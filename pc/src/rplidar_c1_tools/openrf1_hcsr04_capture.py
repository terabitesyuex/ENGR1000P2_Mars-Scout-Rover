"""Recoverable raw JSONL capture for isolated OpenRF1 HC-SR04 diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import statistics
import time

from .openrf1_hcsr04_bringup import (
    HCSR04_SENSOR_ID,
    HCSR04_TELEMETRY_MAX_LINE_BYTES,
    Hcsr04WrongSensorError,
    parse_hcsr04_bringup_line,
)
from .stm32_sensor_protocol import Stm32TelemetryError
from .stm32_serial_capture import (
    DEFAULT_MAX_CONSECUTIVE_MALFORMED_LINES,
    DEFAULT_STARTUP_GRACE_S,
    FileChunkSerialReader,
    PySerialLineReader,
    SerialByteReader,
)


PHYSICAL_VERIFICATION_REQUIRED = "PHYSICAL_VERIFICATION_REQUIRED"
TIMEOUT_ERROR_CODES = {
    "echo_not_low_before_trigger",
    "echo_rise_timeout",
    "echo_fall_timeout",
}


class Hcsr04CaptureError(ValueError):
    """Raised for invalid or incomplete HC-SR04 capture operations."""


class Hcsr04CaptureInterrupted(Hcsr04CaptureError):
    """Raised after a user interrupt has safely closed capture resources."""


@dataclass(frozen=True, slots=True)
class Hcsr04CaptureSummary:
    """Sanitized statistics; intentionally excludes COM ports and local paths."""

    total_lines: int
    valid_identity_count: int
    valid_success_count: int
    timeout_error_count: int
    other_error_count: int
    malformed_count: int
    oversized_count: int
    invalid_utf8_count: int
    wrong_sensor_count: int
    sequence_gap_count: int
    duplicate_sequence_count: int
    timestamp_rollback_count: int
    first_valid_frame_wait_s: float | None
    capture_duration_s: float
    sample_interval_median_ms: float | None
    sample_interval_max_ms: int | None
    echo_pulse_min_us: int | None
    echo_pulse_max_us: int | None
    distance_min_mm: int | None
    distance_max_mm: int | None
    success_after_timeout_recovery: bool
    stopped_after_malformed_limit: bool
    software_pass: bool
    manual_review_required: bool = True
    physical_status: str = PHYSICAL_VERIFICATION_REQUIRED

    def to_json(self) -> dict[str, object]:
        return asdict(self)


def capture_hcsr04_telemetry(
    *,
    reader: SerialByteReader,
    raw_output: Path | str,
    summary_output: Path | str,
    sensor_id: str = HCSR04_SENSOR_ID,
    duration_s: float | None = None,
    max_lines: int | None = None,
    read_chunk_size: int = 64,
    max_empty_reads: int = 10,
    startup_grace_s: float = DEFAULT_STARTUP_GRACE_S,
    max_consecutive_malformed_lines: int = DEFAULT_MAX_CONSECUTIVE_MALFORMED_LINES,
    line_length_limit_bytes: int = HCSR04_TELEMETRY_MAX_LINE_BYTES,
    overwrite: bool = False,
    clock: Callable[[], float] = time.monotonic,
) -> Hcsr04CaptureSummary:
    """Capture every raw byte while independently validating complete JSONL lines."""
    raw_path = Path(raw_output)
    summary_path = Path(summary_output)
    try:
        _validate_options(
            raw_path=raw_path,
            summary_path=summary_path,
            duration_s=duration_s,
            max_lines=max_lines,
            read_chunk_size=read_chunk_size,
            max_empty_reads=max_empty_reads,
            startup_grace_s=startup_grace_s,
            max_consecutive_malformed_lines=max_consecutive_malformed_lines,
            line_length_limit_bytes=line_length_limit_bytes,
            overwrite=overwrite,
        )
    except Exception:
        reader.close()
        raise

    start_s = clock()
    total_lines = 0
    identities = 0
    successes = 0
    timeout_errors = 0
    other_errors = 0
    malformed = 0
    oversized = 0
    invalid_utf8 = 0
    wrong_sensor = 0
    sequence_gaps = 0
    duplicates = 0
    timestamp_rollbacks = 0
    consecutive_malformed = 0
    stopped_after_limit = False
    first_valid_s: float | None = None
    previous_sequence: int | None = None
    previous_timestamp_ms: int | None = None
    previous_sample_timestamp_ms: int | None = None
    sample_intervals_ms: list[int] = []
    echo_values_us: list[int] = []
    distance_values_mm: list[int] = []
    timeout_seen = False
    recovered = False
    empty_reads = 0
    buffer = bytearray()
    discarding_oversized = False
    raw_stream = None

    try:
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_stream = raw_path.open("wb" if overwrite else "xb")
        while True:
            if duration_s is not None and clock() - start_s >= duration_s and not buffer:
                break
            chunk = reader.read(read_chunk_size)
            if chunk == b"":
                if getattr(reader, "eof", False):
                    if buffer or discarding_oversized:
                        total_lines += 1
                        malformed += 1
                        if discarding_oversized or len(buffer) > line_length_limit_bytes:
                            oversized += 1
                    break
                empty_reads += 1
                if first_valid_s is None and clock() - start_s < startup_grace_s:
                    continue
                if empty_reads >= max_empty_reads:
                    break
                continue
            empty_reads = 0
            raw_stream.write(chunk)
            raw_stream.flush()
            buffer.extend(chunk)
            while True:
                newline_index = buffer.find(b"\n")
                if newline_index < 0:
                    if len(buffer) > line_length_limit_bytes:
                        discarding_oversized = True
                    break
                raw_line = bytes(buffer[:newline_index]).rstrip(b"\r")
                encoded_line_bytes = newline_index + 1
                del buffer[: newline_index + 1]
                total_lines += 1
                line_malformed = False
                if discarding_oversized or encoded_line_bytes > line_length_limit_bytes:
                    oversized += 1
                    malformed += 1
                    line_malformed = True
                    discarding_oversized = False
                else:
                    try:
                        text_line = raw_line.decode("utf-8")
                    except UnicodeDecodeError:
                        invalid_utf8 += 1
                        malformed += 1
                        line_malformed = True
                    else:
                        try:
                            message = parse_hcsr04_bringup_line(
                                text_line,
                                allowed_sensor_ids=(sensor_id,),
                                line_number=total_lines,
                            )
                        except Hcsr04WrongSensorError:
                            wrong_sensor += 1
                            malformed += 1
                            line_malformed = True
                        except Stm32TelemetryError:
                            malformed += 1
                            line_malformed = True
                        else:
                            consecutive_malformed = 0
                            if first_valid_s is None:
                                first_valid_s = clock()
                            if previous_sequence is not None:
                                if message.sequence <= previous_sequence:
                                    duplicates += 1
                                elif message.sequence > previous_sequence + 1:
                                    sequence_gaps += message.sequence - previous_sequence - 1
                            if (
                                previous_timestamp_ms is not None
                                and message.timestamp_ms < previous_timestamp_ms
                            ):
                                timestamp_rollbacks += 1
                            previous_sequence = message.sequence
                            previous_timestamp_ms = message.timestamp_ms
                            if message.message_type == "sensor_identity":
                                identities += 1
                            else:
                                if previous_sample_timestamp_ms is not None:
                                    sample_intervals_ms.append(
                                        message.timestamp_ms - previous_sample_timestamp_ms
                                    )
                                previous_sample_timestamp_ms = message.timestamp_ms
                                if message.status == "ok":
                                    successes += 1
                                    pulse = message.payload["echo_pulse_us"]
                                    distance = message.payload["distance_mm"]
                                    echo_values_us.append(int(pulse))
                                    distance_values_mm.append(int(distance))
                                    if timeout_seen:
                                        recovered = True
                                else:
                                    code = str(message.error["code"]) if message.error else ""
                                    if code in TIMEOUT_ERROR_CODES:
                                        timeout_errors += 1
                                        timeout_seen = True
                                    else:
                                        other_errors += 1
                if line_malformed:
                    consecutive_malformed += 1
                    if consecutive_malformed >= max_consecutive_malformed_lines:
                        stopped_after_limit = True
                        break
                if max_lines is not None and total_lines >= max_lines:
                    break
            if stopped_after_limit or (max_lines is not None and total_lines >= max_lines):
                break
    except KeyboardInterrupt as exc:
        raise Hcsr04CaptureInterrupted("capture interrupted; output files were closed") from exc
    finally:
        if raw_stream is not None:
            raw_stream.close()
        reader.close()

    capture_duration_s = max(0.0, clock() - start_s)
    software_pass = all(
        (
            identities >= 1,
            successes >= 1,
            timeout_errors >= 1,
            recovered,
            malformed == 0,
            sequence_gaps == 0,
            duplicates == 0,
            timestamp_rollbacks == 0,
            not stopped_after_limit,
        )
    )
    summary = Hcsr04CaptureSummary(
        total_lines=total_lines,
        valid_identity_count=identities,
        valid_success_count=successes,
        timeout_error_count=timeout_errors,
        other_error_count=other_errors,
        malformed_count=malformed,
        oversized_count=oversized,
        invalid_utf8_count=invalid_utf8,
        wrong_sensor_count=wrong_sensor,
        sequence_gap_count=sequence_gaps,
        duplicate_sequence_count=duplicates,
        timestamp_rollback_count=timestamp_rollbacks,
        first_valid_frame_wait_s=(None if first_valid_s is None else first_valid_s - start_s),
        capture_duration_s=capture_duration_s,
        sample_interval_median_ms=(
            statistics.median(sample_intervals_ms) if sample_intervals_ms else None
        ),
        sample_interval_max_ms=max(sample_intervals_ms) if sample_intervals_ms else None,
        echo_pulse_min_us=min(echo_values_us) if echo_values_us else None,
        echo_pulse_max_us=max(echo_values_us) if echo_values_us else None,
        distance_min_mm=min(distance_values_mm) if distance_values_mm else None,
        distance_max_mm=max(distance_values_mm) if distance_values_mm else None,
        success_after_timeout_recovery=recovered,
        stopped_after_malformed_limit=stopped_after_limit,
        software_pass=software_pass,
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary.to_json(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return summary


def _validate_options(
    *,
    raw_path: Path,
    summary_path: Path,
    duration_s: float | None,
    max_lines: int | None,
    read_chunk_size: int,
    max_empty_reads: int,
    startup_grace_s: float,
    max_consecutive_malformed_lines: int,
    line_length_limit_bytes: int,
    overwrite: bool,
) -> None:
    if raw_path.resolve() == summary_path.resolve():
        raise Hcsr04CaptureError("raw_output and summary_output must differ")
    if duration_s is not None and duration_s <= 0:
        raise Hcsr04CaptureError("duration_s must be positive")
    if max_lines is not None and max_lines <= 0:
        raise Hcsr04CaptureError("max_lines must be positive")
    if read_chunk_size <= 0 or max_empty_reads <= 0:
        raise Hcsr04CaptureError("read sizes/counts must be positive")
    if startup_grace_s < 0:
        raise Hcsr04CaptureError("startup_grace_s must be non-negative")
    if max_consecutive_malformed_lines <= 0:
        raise Hcsr04CaptureError("max_consecutive_malformed_lines must be positive")
    if line_length_limit_bytes <= 0:
        raise Hcsr04CaptureError("line_length_limit_bytes must be positive")
    for path in (raw_path, summary_path):
        if path.exists() and not overwrite:
            raise Hcsr04CaptureError(f"output already exists: {path.name}")


__all__ = [
    "FileChunkSerialReader",
    "Hcsr04CaptureError",
    "Hcsr04CaptureInterrupted",
    "Hcsr04CaptureSummary",
    "PySerialLineReader",
    "capture_hcsr04_telemetry",
]
