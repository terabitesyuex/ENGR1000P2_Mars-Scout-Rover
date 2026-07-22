from __future__ import annotations

import json
from pathlib import Path

import pytest

from rplidar_c1_tools.openrf1_hcsr04_bringup import format_identity_telemetry
from rplidar_c1_tools.openrf1_hcsr04_capture import (
    FileChunkSerialReader,
    Hcsr04CaptureError,
    Hcsr04CaptureInterrupted,
    capture_hcsr04_telemetry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
VALID_FIXTURE = REPO_ROOT / "data" / "test_vectors" / "phase3.2e" / "hcsr04_valid_session.jsonl"
INVALID_UTF8_FIXTURE = REPO_ROOT / "data/test_vectors/phase3.2e/hcsr04_invalid_utf8_bytes.txt"
OVERSIZED_FIXTURE = REPO_ROOT / "data/test_vectors/phase3.2e/hcsr04_oversized_line.txt"


def test_valid_fixture_captures_raw_bytes_and_passes_software_gate(tmp_path: Path):
    raw = tmp_path / "raw.jsonl"
    summary_path = tmp_path / "summary.json"
    reader = FileChunkSerialReader(VALID_FIXTURE, chunk_size=13)

    summary = capture_hcsr04_telemetry(
        reader=reader,
        raw_output=raw,
        summary_output=summary_path,
        duration_s=30.0,
    )

    assert reader.closed
    assert raw.read_bytes() == VALID_FIXTURE.read_bytes()
    assert summary.valid_identity_count == 1
    assert summary.valid_success_count == 6
    assert summary.timeout_error_count == 1
    assert summary.success_after_timeout_recovery
    assert summary.sample_interval_median_ms == 100
    assert summary.sample_interval_max_ms == 100
    assert (summary.echo_pulse_min_us, summary.echo_pulse_max_us) == (1, 29_999)
    assert (summary.distance_min_mm, summary.distance_max_mm) == (0, 5_145)
    assert summary.software_pass
    stored = json.loads(summary_path.read_text(encoding="utf-8"))
    assert stored["physical_status"] == "PHYSICAL_VERIFICATION_REQUIRED"
    assert stored["manual_review_required"] is True
    assert "path" not in summary_path.read_text(encoding="utf-8").lower()
    assert "com" not in summary_path.read_text(encoding="utf-8").lower()


def test_capture_counts_malformed_utf8_oversized_wrong_sensor_and_preserves_raw(tmp_path: Path):
    wrong = json.loads(format_identity_telemetry(sequence=0, timestamp_ms=0))
    wrong["sensor_id"] = "ultrasonic_2"
    invalid_utf8_bytes = bytes.fromhex(INVALID_UTF8_FIXTURE.read_text(encoding="ascii"))
    oversized_bytes = OVERSIZED_FIXTURE.read_bytes()
    assert len(oversized_bytes) > 512
    input_bytes = (
        b"not-json\n"
        + invalid_utf8_bytes
        + oversized_bytes
        + (json.dumps(wrong, separators=(",", ":")).encode("ascii") + b"\n")
        + VALID_FIXTURE.read_bytes()
    )
    source = tmp_path / "source.bin"
    source.write_bytes(input_bytes)
    raw = tmp_path / "raw.bin"
    summary_path = tmp_path / "summary.json"

    summary = capture_hcsr04_telemetry(
        reader=FileChunkSerialReader(source, chunk_size=7),
        raw_output=raw,
        summary_output=summary_path,
        max_consecutive_malformed_lines=10,
        duration_s=30.0,
    )

    assert raw.read_bytes() == input_bytes
    assert summary.malformed_count == 4
    assert summary.invalid_utf8_count == 1
    assert summary.oversized_count == 1
    assert summary.wrong_sensor_count == 1
    assert not summary.software_pass


def test_capture_reports_gap_duplicate_rollback_and_malformed_limit(tmp_path: Path):
    records = [json.loads(line) for line in VALID_FIXTURE.read_text(encoding="utf-8").splitlines()]
    records[1]["sequence"] = 2
    records[2]["sequence"] = 2
    records[3]["sequence"] = 3
    records[3]["timestamp_ms"] = 50
    source = tmp_path / "ordering.jsonl"
    source.write_text(
        "\n".join(json.dumps(record, separators=(",", ":")) for record in records) + "\n",
        encoding="utf-8",
    )
    summary = capture_hcsr04_telemetry(
        reader=FileChunkSerialReader(source),
        raw_output=tmp_path / "ordering-raw.jsonl",
        summary_output=tmp_path / "ordering-summary.json",
        duration_s=30.0,
    )
    assert summary.sequence_gap_count == 1
    assert summary.duplicate_sequence_count == 1
    assert summary.timestamp_rollback_count == 1
    assert not summary.software_pass

    malformed_source = tmp_path / "malformed.jsonl"
    malformed_source.write_bytes(b"bad\nstill-bad\n" + VALID_FIXTURE.read_bytes())
    limited = capture_hcsr04_telemetry(
        reader=FileChunkSerialReader(malformed_source),
        raw_output=tmp_path / "limited-raw.jsonl",
        summary_output=tmp_path / "limited-summary.json",
        max_consecutive_malformed_lines=2,
        duration_s=30.0,
    )
    assert limited.stopped_after_malformed_limit
    assert limited.total_lines == 2
    assert not limited.software_pass


def test_capture_closes_reader_on_option_error_and_ctrl_c(tmp_path: Path):
    existing = tmp_path / "existing.jsonl"
    existing.write_text("occupied", encoding="utf-8")
    reader = FileChunkSerialReader(VALID_FIXTURE)
    with pytest.raises(Hcsr04CaptureError, match="already exists"):
        capture_hcsr04_telemetry(
            reader=reader,
            raw_output=existing,
            summary_output=tmp_path / "summary.json",
        )
    assert reader.closed

    class InterruptingReader:
        closed = False

        def read(self, size: int) -> bytes:
            raise KeyboardInterrupt

        def close(self) -> None:
            self.closed = True

    interrupting = InterruptingReader()
    with pytest.raises(Hcsr04CaptureInterrupted, match="closed"):
        capture_hcsr04_telemetry(
            reader=interrupting,
            raw_output=tmp_path / "interrupt-raw.jsonl",
            summary_output=tmp_path / "interrupt-summary.json",
        )
    assert interrupting.closed
