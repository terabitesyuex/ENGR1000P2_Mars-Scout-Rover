from __future__ import annotations

from decimal import Decimal
import hashlib
from pathlib import Path

import pytest

from rplidar_c1_tools.phase32c_evidence import (
    EVIDENCE_RELATIVE_PATH,
    EVIDENCE_SHA256,
    FORMAL_KEIL_HEX_SHA256,
    Phase32cEvidenceError,
    validate_phase32c_bmp280_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = REPO_ROOT / EVIDENCE_RELATIVE_PATH
REPORT_PATH = REPO_ROOT / "evidence" / "phase3.2c" / "bmp280_physical_evidence.md"


def test_phase32c_bmp280_physical_evidence_hash_and_raw_shape():
    raw_bytes = EVIDENCE_PATH.read_bytes()

    assert hashlib.sha256(raw_bytes).hexdigest().upper() == EVIDENCE_SHA256
    assert raw_bytes.decode("utf-8")
    assert raw_bytes.count(b"\n") == 61


def test_phase32c_bmp280_physical_evidence_matches_formal_capture():
    summary = validate_phase32c_bmp280_evidence(EVIDENCE_PATH)

    assert summary.sha256 == EVIDENCE_SHA256
    assert summary.record_count == 61
    assert summary.sensor_identity_count == 1
    assert summary.environmental_count == 60
    assert (summary.sequence_start, summary.sequence_end) == (0, 60)
    assert summary.first_timestamp_ms == 6
    assert summary.first_environmental_timestamp_ms == 506
    assert summary.last_timestamp_ms == 30006
    assert summary.capture_duration_ms == 30000
    assert summary.environmental_span_ms == 29500
    assert summary.environmental_interval_ms == 500
    assert summary.configured_address == "0x76"
    assert summary.expected_chip_id == "0x58"
    assert summary.chip_id == "0x58"
    assert summary.ctrl_meas == "0x27"
    assert summary.config == "0x80"
    assert summary.temperature_min_c == Decimal("26.18")
    assert summary.temperature_max_c == Decimal("26.23")
    assert summary.pressure_min_pa == Decimal("99867")
    assert summary.pressure_max_pa == Decimal("99882")


def test_phase32c_bmp280_evidence_validator_rejects_changed_file(tmp_path):
    changed = tmp_path / "changed.jsonl"
    changed.write_bytes(EVIDENCE_PATH.read_bytes().replace(b'"sequence":3', b'"sequence":9', 1))
    changed_hash = hashlib.sha256(changed.read_bytes()).hexdigest().upper()

    with pytest.raises(Phase32cEvidenceError, match="sequence"):
        validate_phase32c_bmp280_evidence(changed, expected_sha256=changed_hash)


def test_phase32c_bmp280_evidence_report_is_sanitized_and_truthful():
    report = REPORT_PATH.read_text(encoding="utf-8")

    required = [
        "Source firmware commit | `adef636`",
        FORMAL_KEIL_HEX_SHA256,
        EVIDENCE_SHA256,
        "PHYSICAL_EVIDENCE_VERIFIED",
        "Absolute temperature accuracy",
        "Absolute pressure accuracy",
        "UNVERIFIED",
    ]
    forbidden = [
        "C:" + "\\Users",
        "Desk" + "top",
        "COM" + "5",
        "zig" + "xi",
        "unique 96-" + "bit",
    ]

    for snippet in required:
        assert snippet in report
    for snippet in forbidden:
        assert snippet not in report
