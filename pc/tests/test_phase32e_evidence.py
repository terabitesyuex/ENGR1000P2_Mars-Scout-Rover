from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rplidar_c1_tools.phase32e_evidence import (
    EVIDENCE_SCHEMA,
    EXPECTED_BRANCH,
    EXPECTED_HEX_FILENAME,
    EXPECTED_KEIL_PROJECT,
    EXPECTED_KEIL_TARGET,
    PHYSICAL_STATUS,
    Phase32eEvidenceError,
    validate_phase32e_evidence_candidate,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "evidence" / "phase3.2e" / "hcsr04_manual_evidence_template.md"


def _candidate() -> dict[str, object]:
    return {
        "schema": EVIDENCE_SCHEMA,
        "version": 1,
        "candidate_status": "MANUAL_REVIEW_REQUIRED",
        "branch": EXPECTED_BRANCH,
        "commit": "a" * 40,
        "test_date": "2026-07-21",
        "keil": {
            "project": EXPECTED_KEIL_PROJECT,
            "target": EXPECTED_KEIL_TARGET,
            "build_date": "2026-07-21",
            "build_result": "PASS",
            "errors": 0,
            "warnings": 0,
        },
        "hex": {"filename": EXPECTED_HEX_FILENAME, "sha256": "B" * 64},
        "sensor_id": "ultrasonic_1",
        "wiring_and_measurements": {
            "actual_connector_orientation": "manually checked against printed labels",
            "common_ground_check": True,
            "actual_vcc_v": 5.01,
            "installed_series_resistor_ohm": 10_000,
            "installed_resistor_to_ground_ohm": 15_000,
            "echo_before_divider_v": 4.98,
            "echo_after_divider_v": 2.99,
            "trig_pulse_us": "UNVERIFIED",
            "echo_pulse_us": "UNVERIFIED",
            "timer_tick_hz": "UNVERIFIED",
        },
        "behavior": {
            "near": "reported values changed at the near position",
            "far": "reported values changed at the farther position",
            "timeout": "error status with null pulse and distance",
            "recovery": "a later valid success record was captured",
        },
        "capture_summary": {
            "total_lines": 20,
            "valid_identity_count": 1,
            "valid_success_count": 18,
            "timeout_error_count": 1,
            "malformed_count": 0,
            "oversized_count": 0,
            "invalid_utf8_count": 0,
            "wrong_sensor_count": 0,
            "sequence_gap_count": 0,
            "duplicate_sequence_count": 0,
            "timestamp_rollback_count": 0,
            "success_after_timeout_recovery": True,
            "software_pass": True,
            "manual_review_required": True,
            "physical_status": PHYSICAL_STATUS,
        },
        "artifacts": {
            "sanitized_jsonl_path": "evidence/phase3.2e/candidate_raw.jsonl",
            "sanitized_summary_path": "evidence/phase3.2e/candidate_summary.json",
        },
        "manual_conclusion": "Submitted for independent evidence review",
        "physical_status": PHYSICAL_STATUS,
    }


def _write(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_template_is_explicitly_not_a_candidate():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert text.startswith("# TEMPLATE ONLY — NOT PHYSICAL EVIDENCE")
    with pytest.raises(Phase32eEvidenceError, match="not a candidate"):
        validate_phase32e_evidence_candidate(TEMPLATE)


def test_sanitized_candidate_can_be_structurally_valid_without_physical_certification(tmp_path: Path):
    path = tmp_path / "manual_candidate.json"
    _write(path, _candidate())
    summary = validate_phase32e_evidence_candidate(path)
    assert summary.candidate_structurally_valid
    assert summary.physical_status == PHYSICAL_STATUS


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (("commit", "short"), "commit"),
        (("physical_status", "MANUAL_EVIDENCE_VERIFIED"), "PHYSICAL_VERIFICATION_REQUIRED"),
        (("manual_conclusion", "TODO"), "placeholder"),
    ],
)
def test_candidate_rejects_placeholders_and_fake_physical_status(tmp_path: Path, mutation, match: str):
    candidate = copy.deepcopy(_candidate())
    candidate[mutation[0]] = mutation[1]
    path = tmp_path / "bad_candidate.json"
    _write(path, candidate)
    with pytest.raises(Phase32eEvidenceError, match=match):
        validate_phase32e_evidence_candidate(path)


def test_candidate_rejects_private_ports_paths_and_incomplete_measurements(tmp_path: Path):
    for bad_value in ("CO" + "M7", "C:/" + "Users/example/capture.jsonl"):
        candidate = copy.deepcopy(_candidate())
        candidate["manual_conclusion"] = bad_value
        path = tmp_path / "private_candidate.json"
        _write(path, candidate)
        with pytest.raises(Phase32eEvidenceError):
            validate_phase32e_evidence_candidate(path)

    candidate = copy.deepcopy(_candidate())
    candidate["wiring_and_measurements"]["echo_after_divider_v"] = None
    path = tmp_path / "missing_candidate.json"
    _write(path, candidate)
    with pytest.raises(Phase32eEvidenceError, match="recorded or UNVERIFIED"):
        validate_phase32e_evidence_candidate(path)
