from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from rplidar_c1_tools.openrf1_bh1750 import generate_bh1750_telemetry_lines
from rplidar_c1_tools.replay import inspect_recording, iter_recording_entries
from rplidar_c1_tools.stm32_sensor_models import Stm32TelemetryMessage
from rplidar_c1_tools.stm32_sensor_protocol import encode_stm32_telemetry_message
from rplidar_c1_tools.stm32_sensor_simulator import generate_synthetic_stm32_lines
from rplidar_c1_tools.stm32_serial_capture import (
    FileChunkSerialReader,
    Stm32SerialCaptureError,
    Stm32SerialCaptureInterrupted,
    capture_stm32_serial_telemetry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def test_mocked_serial_capture_writes_raw_telemetry_and_recording(tmp_path):
    source = _write_lines(tmp_path / "source.jsonl", generate_bh1750_telemetry_lines(samples=4))
    telemetry = tmp_path / "captured_telemetry.jsonl"
    recording = tmp_path / "captured_recording.jsonl"

    summary = capture_stm32_serial_telemetry(
        reader=FileChunkSerialReader(source, chunk_size=5),
        telemetry_output=telemetry,
        recording_output=recording,
        max_messages=4,
    )

    assert summary.messages == 4
    assert summary.malformed_lines == 0
    assert summary.status_counts == {"simulated": 4}
    assert summary.first_timestamp_ms == 0
    assert summary.last_timestamp_ms == 1500
    assert summary.lux_min == 120.0
    assert summary.lux_max == 141.75
    assert summary.lux_mean == pytest.approx(130.875)
    assert telemetry.read_text(encoding="utf-8").count("\n") == 4
    assert inspect_recording(recording).record_counts == {"illuminance": 4}


def test_capture_preserves_hardware_fault_without_zero_lux(tmp_path):
    message = Stm32TelemetryMessage(
        sequence=0,
        timestamp_ms=10,
        message_type="illuminance",
        sensor_id="bh1750_1",
        status="hardware_fault",
        payload={"illuminance_lux": None},
    )
    source = _write_lines(tmp_path / "fault.jsonl", [encode_stm32_telemetry_message(message)])
    recording = tmp_path / "fault_recording.jsonl"

    summary = capture_stm32_serial_telemetry(
        reader=FileChunkSerialReader(source),
        telemetry_output=tmp_path / "fault_telemetry.jsonl",
        recording_output=recording,
    )

    assert summary.messages == 1
    assert summary.lux_min is None
    [entry] = [
        item.payload
        for item in iter_recording_entries(recording)
        if item.payload["record_type"] == "illuminance"
    ]
    assert entry["status"] == "hardware_fault"
    assert entry["illuminance_lux"] is None


def test_capture_rejects_malformed_json_invalid_utf8_oversized_and_timeout(tmp_path):
    bad_json = _write_bytes(tmp_path / "bad.jsonl", b"not-json\n")
    with pytest.raises(Stm32SerialCaptureError, match="invalid JSON"):
        capture_stm32_serial_telemetry(
            reader=FileChunkSerialReader(bad_json),
            telemetry_output=tmp_path / "bad_out.jsonl",
            recording_output=None,
        )

    invalid_utf8 = _write_bytes(tmp_path / "utf8.jsonl", b"\xff\n")
    with pytest.raises(Stm32SerialCaptureError, match="ASCII/UTF-8"):
        capture_stm32_serial_telemetry(
            reader=FileChunkSerialReader(invalid_utf8),
            telemetry_output=tmp_path / "utf8_out.jsonl",
            recording_output=None,
        )

    oversized = _write_bytes(tmp_path / "oversized.jsonl", b"{" + (b'"x":1,' * 20) + b"}\n")
    with pytest.raises(Stm32SerialCaptureError, match="length limit"):
        capture_stm32_serial_telemetry(
            reader=FileChunkSerialReader(oversized, chunk_size=200),
            telemetry_output=tmp_path / "oversized_out.jsonl",
            recording_output=None,
            line_length_limit_bytes=20,
        )

    with pytest.raises(Stm32SerialCaptureError, match="serial read timeout"):
        capture_stm32_serial_telemetry(
            reader=TimeoutReader(),
            telemetry_output=tmp_path / "timeout_out.jsonl",
            recording_output=None,
            max_empty_reads=2,
        )


def test_capture_rejects_wrong_message_type_sensor_and_invalid_lux(tmp_path):
    wrong_type = _write_lines(tmp_path / "wrong_type.jsonl", [generate_synthetic_stm32_lines(cycles=1)[0]])
    with pytest.raises(Stm32SerialCaptureError, match="illuminance"):
        capture_stm32_serial_telemetry(
            reader=FileChunkSerialReader(wrong_type),
            telemetry_output=tmp_path / "wrong_type_out.jsonl",
            recording_output=None,
        )

    wrong_sensor = _write_lines(
        tmp_path / "wrong_sensor.jsonl",
        [
            encode_stm32_telemetry_message(
                Stm32TelemetryMessage(
                    sequence=0,
                    timestamp_ms=0,
                    message_type="illuminance",
                    sensor_id="bh1750_1",
                    payload={"illuminance_lux": 10.0},
                    status="simulated",
                )
            ).replace('"bh1750_1"', '"bmp280_1"')
        ],
    )
    with pytest.raises(Stm32SerialCaptureError, match="sensor_id"):
        capture_stm32_serial_telemetry(
            reader=FileChunkSerialReader(wrong_sensor),
            telemetry_output=tmp_path / "wrong_sensor_out.jsonl",
            recording_output=None,
        )

    invalid_lux = _write_lines(
        tmp_path / "invalid_lux.jsonl",
        [
            encode_stm32_telemetry_message(
                Stm32TelemetryMessage(
                    sequence=0,
                    timestamp_ms=0,
                    message_type="illuminance",
                    sensor_id="bh1750_1",
                    payload={"illuminance_lux": 10.0},
                    status="simulated",
                )
            ).replace("10.0", "-1.0")
        ],
    )
    with pytest.raises(Stm32SerialCaptureError, match="non-negative"):
        capture_stm32_serial_telemetry(
            reader=FileChunkSerialReader(invalid_lux),
            telemetry_output=tmp_path / "invalid_lux_out.jsonl",
            recording_output=None,
        )


def test_capture_refuses_overwrite_and_closes_on_interrupt(tmp_path):
    source = _write_lines(tmp_path / "source.jsonl", generate_bh1750_telemetry_lines(samples=1))
    output = tmp_path / "exists.jsonl"
    output.write_text("existing\n", encoding="utf-8")

    with pytest.raises(Stm32SerialCaptureError, match="already exists"):
        capture_stm32_serial_telemetry(
            reader=FileChunkSerialReader(source),
            telemetry_output=output,
            recording_output=None,
        )

    interrupting = InterruptingReader()
    with pytest.raises(Stm32SerialCaptureInterrupted):
        capture_stm32_serial_telemetry(
            reader=interrupting,
            telemetry_output=tmp_path / "interrupted.jsonl",
            recording_output=None,
        )
    assert interrupting.closed is True


def test_capture_closes_reader_when_argument_validation_fails(tmp_path):
    reader = TimeoutReader()

    with pytest.raises(Stm32SerialCaptureError, match="duration_s must be positive"):
        capture_stm32_serial_telemetry(
            reader=reader,
            telemetry_output=tmp_path / "unused.jsonl",
            recording_output=None,
            duration_s=0.0,
        )

    assert reader.closed is True

def test_capture_cli_uses_mock_input_and_python_module_entrypoint(tmp_path):
    source = tmp_path / "mocked_source.jsonl"
    telemetry = tmp_path / "mocked_bh1750_telemetry.jsonl"
    recording = tmp_path / "mocked_bh1750_recording.jsonl"
    _run_cli(
        tmp_path,
        "simulate-bh1750-telemetry",
        "--samples",
        "3",
        "--output",
        str(source),
    )

    result = _run_cli(
        tmp_path,
        "capture-stm32-serial",
        "--mock-input",
        str(source),
        "--max-messages",
        "3",
        "--telemetry-output",
        str(telemetry),
        "--recording-output",
        str(recording),
    )

    assert result.returncode == 0, result.stderr
    assert "messages: 3" in result.stdout
    assert "lux_mean:" in result.stdout
    assert telemetry.exists()
    assert recording.exists()


class TimeoutReader:
    def __init__(self) -> None:
        self.closed = False

    def read(self, _size: int) -> bytes:
        return b""

    def close(self) -> None:
        self.closed = True


class InterruptingReader:
    def __init__(self) -> None:
        self.closed = False

    def read(self, _size: int) -> bytes:
        raise KeyboardInterrupt

    def close(self) -> None:
        self.closed = True


def _write_lines(path: Path, lines) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def _write_bytes(path: Path, payload: bytes) -> Path:
    path.write_bytes(payload)
    return path


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "rplidar_c1_tools", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
