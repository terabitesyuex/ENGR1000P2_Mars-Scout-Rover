"""Mockable STM32 telemetry serial capture for Phase 3.2A."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Protocol

from .openrf1_bh1750 import OPENRF1_BH1750_SENSOR_ID
from .recorder import MultiSensorRecorder
from .recording_models import default_sensor_inventory
from .stm32_recording_bridge import bridge_stm32_message_to_recording
from .stm32_sensor_models import Stm32TelemetryMessage
from .stm32_sensor_protocol import (
    Stm32TelemetryError,
    encode_stm32_telemetry_message,
    parse_stm32_telemetry_line,
)


DEFAULT_STM32_SERIAL_BAUD = 115200
DEFAULT_STM32_SERIAL_TIMEOUT_S = 1.0
DEFAULT_LINE_LENGTH_LIMIT_BYTES = 512


class SerialByteReader(Protocol):
    """Minimal serial-like byte reader used for dependency injection."""

    def read(self, size: int) -> bytes:
        """Return up to size bytes, or b'' on timeout/no data."""

    def close(self) -> None:
        """Release the underlying resource."""


class Stm32SerialCaptureError(ValueError):
    """Raised for STM32 serial-capture failures."""


class Stm32SerialCaptureInterrupted(Stm32SerialCaptureError):
    """Raised when capture is interrupted after the reader is closed."""


@dataclass(frozen=True, slots=True)
class Stm32SerialCaptureSummary:
    """Compact capture statistics for CLI and tests."""

    messages: int
    malformed_lines: int
    status_counts: dict[str, int]
    first_timestamp_ms: int | None
    last_timestamp_ms: int | None
    lux_min: float | None
    lux_max: float | None
    lux_mean: float | None
    telemetry_output: Path | None
    recording_output: Path | None

    def to_text(self) -> str:
        lines = [
            f"messages: {self.messages}",
            f"malformed_lines: {self.malformed_lines}",
            "status_counts:",
        ]
        for status, count in sorted(self.status_counts.items()):
            lines.append(f"  {status}: {count}")
        lines.extend(
            [
                f"first_timestamp_ms: {self.first_timestamp_ms}",
                f"last_timestamp_ms: {self.last_timestamp_ms}",
                f"lux_min: {self.lux_min}",
                f"lux_max: {self.lux_max}",
                f"lux_mean: {self.lux_mean}",
                f"telemetry_output: {self.telemetry_output}",
                f"recording_output: {self.recording_output}",
            ]
        )
        return "\n".join(lines) + "\n"


class FileChunkSerialReader:
    """File-backed byte reader for automated tests and verifier smoke runs."""

    def __init__(self, path: Path | str, *, chunk_size: int = 17) -> None:
        if chunk_size <= 0:
            raise Stm32SerialCaptureError("chunk_size must be positive")
        self.path = Path(path)
        self.chunk_size = chunk_size
        self._stream = self.path.open("rb")
        self.eof = False
        self.closed = False

    def read(self, size: int) -> bytes:
        if self.closed:
            return b""
        chunk = self._stream.read(min(size, self.chunk_size))
        if chunk == b"":
            self.eof = True
        return chunk

    def close(self) -> None:
        if not self.closed:
            self._stream.close()
            self.closed = True


class PySerialLineReader:
    """PySerial-backed reader for manual, user-selected COM ports only."""

    def __init__(
        self,
        *,
        port: str,
        baud: int = DEFAULT_STM32_SERIAL_BAUD,
        timeout_s: float = DEFAULT_STM32_SERIAL_TIMEOUT_S,
    ) -> None:
        if not port:
            raise Stm32SerialCaptureError("port must be provided explicitly")
        if baud <= 0:
            raise Stm32SerialCaptureError("baud must be positive")
        if timeout_s <= 0.0:
            raise Stm32SerialCaptureError("timeout_s must be positive")
        try:
            import serial  # type: ignore[import-not-found]
        except ImportError as exc:
            raise Stm32SerialCaptureError(
                "pyserial is required for live STM32 serial capture; "
                "install it in the repository venv with: "
                "pc\\.venv\\Scripts\\python.exe -m pip install pyserial"
            ) from exc
        self._serial = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=timeout_s,
        )

    def read(self, size: int) -> bytes:
        return bytes(self._serial.read(size))

    def close(self) -> None:
        self._serial.close()


def capture_stm32_serial_telemetry(
    *,
    reader: SerialByteReader,
    telemetry_output: Path | str | None,
    recording_output: Path | str | None,
    duration_s: float | None = None,
    max_messages: int | None = None,
    read_chunk_size: int = 64,
    max_empty_reads: int = 10,
    line_length_limit_bytes: int = DEFAULT_LINE_LENGTH_LIMIT_BYTES,
    overwrite: bool = False,
    clock: Callable[[], float] = time.monotonic,
) -> Stm32SerialCaptureSummary:
    """Capture validated BH1750 telemetry and optionally write recording JSONL."""
    try:
        if telemetry_output is None and recording_output is None:
            raise Stm32SerialCaptureError("at least one output path is required")
        if duration_s is not None and duration_s <= 0.0:
            raise Stm32SerialCaptureError("duration_s must be positive")
        if max_messages is not None and max_messages <= 0:
            raise Stm32SerialCaptureError("max_messages must be positive")
        if read_chunk_size <= 0:
            raise Stm32SerialCaptureError("read_chunk_size must be positive")
        if max_empty_reads <= 0:
            raise Stm32SerialCaptureError("max_empty_reads must be positive")
        if line_length_limit_bytes <= 0:
            raise Stm32SerialCaptureError("line_length_limit_bytes must be positive")

        telemetry_path = Path(telemetry_output) if telemetry_output is not None else None
        recording_path = Path(recording_output) if recording_output is not None else None
        _check_output_path(telemetry_path, overwrite)
        _check_output_path(recording_path, overwrite)
    except Exception:
        reader.close()
        raise

    status_counts: Counter[str] = Counter()
    lux_values: list[float] = []
    first_timestamp_ms: int | None = None
    last_timestamp_ms: int | None = None
    messages = 0
    malformed_lines = 0
    start_s = clock()

    telemetry_stream = None
    recorder = None
    try:
        if telemetry_path is not None:
            telemetry_path.parent.mkdir(parents=True, exist_ok=True)
            telemetry_stream = telemetry_path.open(
                "w" if overwrite else "x",
                encoding="utf-8",
                newline="\n",
            )
        if recording_path is not None:
            recorder = MultiSensorRecorder(
                recording_path,
                sensor_inventory=default_sensor_inventory(lidar_count=1, include_auxiliary=True),
                metadata={
                    "source": "stm32_serial_capture",
                    "sensor_id": OPENRF1_BH1750_SENSOR_ID,
                    "hardware_access": "manual_user_selected_port_or_mock_reader",
                    "physical_test_required": True,
                },
                overwrite=overwrite,
            )
            recorder.open()

        for line in _iter_serial_lines(
            reader=reader,
            read_chunk_size=read_chunk_size,
            max_empty_reads=max_empty_reads,
            line_length_limit_bytes=line_length_limit_bytes,
            duration_s=duration_s,
            start_s=start_s,
            clock=clock,
        ):
            try:
                message = parse_stm32_telemetry_line(line, line_number=messages + malformed_lines + 1)
                _require_phase32a_bh1750_message(message)
            except (Stm32TelemetryError, Stm32SerialCaptureError) as exc:
                malformed_lines += 1
                raise Stm32SerialCaptureError(str(exc)) from exc

            if telemetry_stream is not None:
                telemetry_stream.write(encode_stm32_telemetry_message(message))
                telemetry_stream.write("\n")
                telemetry_stream.flush()
            if recorder is not None:
                bridge_stm32_message_to_recording(recorder, message)

            messages += 1
            status_counts[message.status] += 1
            first_timestamp_ms = message.timestamp_ms if first_timestamp_ms is None else first_timestamp_ms
            last_timestamp_ms = message.timestamp_ms
            lux = message.payload.get("illuminance_lux")
            if isinstance(lux, int | float):
                lux_values.append(float(lux))
            if max_messages is not None and messages >= max_messages:
                break
            if duration_s is not None and clock() - start_s >= duration_s:
                break
    except KeyboardInterrupt as exc:
        raise Stm32SerialCaptureInterrupted("capture interrupted") from exc
    finally:
        if recorder is not None:
            recorder.close()
        if telemetry_stream is not None:
            telemetry_stream.close()
        reader.close()

    return Stm32SerialCaptureSummary(
        messages=messages,
        malformed_lines=malformed_lines,
        status_counts=dict(status_counts),
        first_timestamp_ms=first_timestamp_ms,
        last_timestamp_ms=last_timestamp_ms,
        lux_min=min(lux_values) if lux_values else None,
        lux_max=max(lux_values) if lux_values else None,
        lux_mean=(sum(lux_values) / len(lux_values)) if lux_values else None,
        telemetry_output=telemetry_path,
        recording_output=recording_path,
    )


def _iter_serial_lines(
    *,
    reader: SerialByteReader,
    read_chunk_size: int,
    max_empty_reads: int,
    line_length_limit_bytes: int,
    duration_s: float | None,
    start_s: float,
    clock: Callable[[], float],
):
    buffer = bytearray()
    empty_reads = 0
    while True:
        if duration_s is not None and clock() - start_s >= duration_s and not buffer:
            return
        chunk = reader.read(read_chunk_size)
        if chunk == b"":
            if getattr(reader, "eof", False):
                if buffer:
                    raise Stm32SerialCaptureError("unterminated telemetry line at EOF")
                return
            empty_reads += 1
            if empty_reads >= max_empty_reads:
                raise Stm32SerialCaptureError("serial read timeout")
            continue
        empty_reads = 0
        buffer.extend(chunk)
        while True:
            newline_index = buffer.find(b"\n")
            if newline_index < 0:
                break
            if newline_index > line_length_limit_bytes:
                raise Stm32SerialCaptureError("telemetry line exceeds length limit")
            raw_line = bytes(buffer[:newline_index]).rstrip(b"\r")
            del buffer[: newline_index + 1]
            try:
                yield raw_line.decode("ascii")
            except UnicodeDecodeError as exc:
                raise Stm32SerialCaptureError("telemetry line is not ASCII/UTF-8 JSON") from exc
        if len(buffer) > line_length_limit_bytes:
            raise Stm32SerialCaptureError("telemetry line exceeds length limit")


def _require_phase32a_bh1750_message(message: Stm32TelemetryMessage) -> None:
    if message.message_type != "illuminance":
        raise Stm32SerialCaptureError("Phase 3.2A capture accepts only illuminance messages")
    if message.sensor_id != OPENRF1_BH1750_SENSOR_ID:
        raise Stm32SerialCaptureError("Phase 3.2A capture accepts only sensor_id bh1750_1")
    lux = message.payload.get("illuminance_lux")
    if message.status in {"ok", "simulated"} and lux is None:
        raise Stm32SerialCaptureError("valid BH1750 messages require illuminance_lux")


def _check_output_path(path: Path | None, overwrite: bool) -> None:
    if path is not None and path.exists() and not overwrite:
        raise Stm32SerialCaptureError(f"output already exists: {path}")
