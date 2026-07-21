from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from rplidar_c1_tools.phase32f_evidence import (
    CAPTURE_SPECS,
    EXPECTED_INTERVAL_MS,
    EXPECTED_RECORD_COUNT,
    FORMAL_KEIL_HEX_SHA256,
    Phase32fEvidenceError,
    validate_all_phase32f_captures,
    validate_phase32f_capture,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "evidence/phase3.2f/tcrt5000_physical_evidence.md"


def test_phase32f_capture_hashes_and_raw_shapes():
    for spec in CAPTURE_SPECS.values():
        raw_bytes = (REPO_ROOT / spec["path"]).read_bytes()
        assert hashlib.sha256(raw_bytes).hexdigest().upper() == spec["sha256"]
        assert len(raw_bytes.decode("ascii").splitlines()) == EXPECTED_RECORD_COUNT


def test_phase32f_captures_match_locked_states_and_timing():
    summaries = validate_all_phase32f_captures(REPO_ROOT)

    assert len(summaries) == 4
    assert all(summary.record_count == EXPECTED_RECORD_COUNT for summary in summaries)
    assert all(summary.sequence_end - summary.sequence_start == 99 for summary in summaries)
    assert all(summary.capture_span_ms == 4950 for summary in summaries)
    assert all(summary.interval_ms == EXPECTED_INTERVAL_MS for summary in summaries)


def test_phase32f_validator_rejects_changed_file(tmp_path):
    name = "tcrt5000_1_open_space"
    original = REPO_ROOT / CAPTURE_SPECS[name]["path"]
    changed = tmp_path / "changed.jsonl"
    changed.write_bytes(original.read_bytes().replace(b'"sequence":20924', b'"sequence":29924', 1))

    with pytest.raises(Phase32fEvidenceError, match="sha256"):
        validate_phase32f_capture(tmp_path, name, evidence_path=changed)


def test_phase32f_report_is_sanitized_and_scope_limited():
    report = REPORT_PATH.read_text(encoding="utf-8")

    required = [
        FORMAL_KEIL_HEX_SHA256,
        "MANUAL_EVIDENCE_VERIFIED",
        "four 100-frame captures",
        "50 ms",
        "Black/white classification",
        "Actual 3.3 V rail voltage",
        "Hall sensor",
        "UNVERIFIED",
        "exactly one physical RPLIDAR C1M1-R2",
    ]
    forbidden = [
        "C:" + "\\Users",
        "Desk" + "top",
        "COM" + "5",
        "zig" + "xi",
        "c1_2 is available",
    ]

    for snippet in required:
        assert snippet in report
    for snippet in forbidden:
        assert snippet not in report
