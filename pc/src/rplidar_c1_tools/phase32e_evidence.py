"""Structural validation for future Phase 3.2E manual evidence candidates."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping


EVIDENCE_SCHEMA = "mars_scout_phase32e_hcsr04_evidence_candidate"
EVIDENCE_VERSION = 1
EXPECTED_BRANCH = "feature/c-hcsr04-validation-readiness"
EXPECTED_KEIL_PROJECT = "firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx"
EXPECTED_KEIL_TARGET = "OpenRF1_HCSR04_Bringup"
EXPECTED_HEX_FILENAME = "OpenRF1_HCSR04_Bringup.hex"
PHYSICAL_STATUS = "PHYSICAL_VERIFICATION_REQUIRED"
TEMPLATE_RELATIVE_PATH = Path("evidence/phase3.2e/hcsr04_manual_evidence_template.md")

_FULL_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9A-Fa-f]{64}")
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_COM_RE = re.compile(r"\bCOM\d{1,3}\b", re.IGNORECASE)
_WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:[\\/]")
_PRIVATE_MARKERS = ("C:\\Users", "AppData", "Desktop", "unique id", "proxy=", "api_key")
_PLACEHOLDERS = ("<fill", "<user", "todo", "replace_me", "template only")


class Phase32eEvidenceError(ValueError):
    """Raised when a future A evidence candidate is not review-ready."""


@dataclass(frozen=True, slots=True)
class Phase32eEvidenceSummary:
    branch: str
    commit: str
    test_date: str
    sensor_id: str
    software_pass: bool
    candidate_structurally_valid: bool = True
    physical_status: str = PHYSICAL_STATUS


def validate_phase32e_evidence_candidate(path: Path | str) -> Phase32eEvidenceSummary:
    """Validate structure/sanitization only; never certify physical hardware."""
    candidate_path = Path(path)
    if candidate_path.name == TEMPLATE_RELATIVE_PATH.name or candidate_path.suffix.lower() != ".json":
        raise Phase32eEvidenceError("evidence template/non-JSON file is not a candidate")
    raw = candidate_path.read_text(encoding="utf-8")
    _require_sanitized(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise Phase32eEvidenceError(f"candidate is invalid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise Phase32eEvidenceError("candidate must be a JSON object")
    _require_exact_fields(
        data,
        {
            "schema",
            "version",
            "candidate_status",
            "branch",
            "commit",
            "test_date",
            "keil",
            "hex",
            "sensor_id",
            "wiring_and_measurements",
            "behavior",
            "capture_summary",
            "artifacts",
            "manual_conclusion",
            "physical_status",
        },
        "candidate",
    )
    _equal(data, "schema", EVIDENCE_SCHEMA)
    _equal(data, "version", EVIDENCE_VERSION)
    _equal(data, "candidate_status", "MANUAL_REVIEW_REQUIRED")
    _equal(data, "branch", EXPECTED_BRANCH)
    commit = _string(data, "commit")
    if _FULL_COMMIT_RE.fullmatch(commit) is None:
        raise Phase32eEvidenceError("commit must be a full 40-character lowercase Git hash")
    test_date = _string(data, "test_date")
    if _DATE_RE.fullmatch(test_date) is None:
        raise Phase32eEvidenceError("test_date must use YYYY-MM-DD")
    sensor_id = _string(data, "sensor_id")
    if sensor_id not in {"ultrasonic_1", "ultrasonic_2", "ultrasonic_3"}:
        raise Phase32eEvidenceError("sensor_id must be a neutral ultrasonic ID")
    _equal(data, "physical_status", PHYSICAL_STATUS)
    _require_non_placeholder_string(data, "manual_conclusion")

    keil = _object(data, "keil")
    _require_exact_fields(keil, {"project", "target", "build_date", "build_result", "errors", "warnings"}, "keil")
    _equal(keil, "project", EXPECTED_KEIL_PROJECT)
    _equal(keil, "target", EXPECTED_KEIL_TARGET)
    if _DATE_RE.fullmatch(_string(keil, "build_date")) is None:
        raise Phase32eEvidenceError("keil.build_date must use YYYY-MM-DD")
    _equal(keil, "build_result", "PASS")
    _equal(keil, "errors", 0)
    _equal(keil, "warnings", 0)

    hex_data = _object(data, "hex")
    _require_exact_fields(hex_data, {"filename", "sha256"}, "hex")
    _equal(hex_data, "filename", EXPECTED_HEX_FILENAME)
    if _SHA256_RE.fullmatch(_string(hex_data, "sha256")) is None:
        raise Phase32eEvidenceError("hex.sha256 must be 64 hexadecimal characters")

    wiring = _object(data, "wiring_and_measurements")
    _require_exact_fields(
        wiring,
        {
            "actual_connector_orientation",
            "common_ground_check",
            "actual_vcc_v",
            "installed_series_resistor_ohm",
            "installed_resistor_to_ground_ohm",
            "echo_before_divider_v",
            "echo_after_divider_v",
            "trig_pulse_us",
            "echo_pulse_us",
            "timer_tick_hz",
        },
        "wiring_and_measurements",
    )
    for key, value in wiring.items():
        if value is None or value == "":
            raise Phase32eEvidenceError(f"wiring_and_measurements.{key} must be recorded or UNVERIFIED")
    if wiring["common_ground_check"] is not True:
        raise Phase32eEvidenceError("common_ground_check must be true for a candidate")
    _require_non_placeholder_string(wiring, "actual_connector_orientation")
    for key in (
        "actual_vcc_v",
        "installed_series_resistor_ohm",
        "installed_resistor_to_ground_ohm",
        "echo_before_divider_v",
        "echo_after_divider_v",
    ):
        value = wiring[key]
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)) or value <= 0:
            raise Phase32eEvidenceError(f"wiring_and_measurements.{key} must be a positive measured number")
    for key in ("trig_pulse_us", "echo_pulse_us", "timer_tick_hz"):
        value = wiring[key]
        if value == "UNVERIFIED":
            continue
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)) or value <= 0:
            raise Phase32eEvidenceError(f"wiring_and_measurements.{key} must be positive or UNVERIFIED")

    behavior = _object(data, "behavior")
    _require_exact_fields(behavior, {"near", "far", "timeout", "recovery"}, "behavior")
    for key in behavior:
        _require_non_placeholder_string(behavior, key)

    capture = _object(data, "capture_summary")
    required_capture = {
        "total_lines",
        "valid_identity_count",
        "valid_success_count",
        "timeout_error_count",
        "malformed_count",
        "oversized_count",
        "invalid_utf8_count",
        "wrong_sensor_count",
        "sequence_gap_count",
        "duplicate_sequence_count",
        "timestamp_rollback_count",
        "success_after_timeout_recovery",
        "software_pass",
        "manual_review_required",
        "physical_status",
    }
    if not required_capture.issubset(capture):
        raise Phase32eEvidenceError("capture_summary is missing required validation statistics")
    if capture.get("software_pass") is not True or capture.get("manual_review_required") is not True:
        raise Phase32eEvidenceError("capture summary must pass software checks and require manual review")
    if capture.get("physical_status") != PHYSICAL_STATUS:
        raise Phase32eEvidenceError("capture summary must retain PHYSICAL_VERIFICATION_REQUIRED")

    artifacts = _object(data, "artifacts")
    _require_exact_fields(artifacts, {"sanitized_jsonl_path", "sanitized_summary_path"}, "artifacts")
    for key in artifacts:
        _require_sanitized_relative_path(_string(artifacts, key), f"artifacts.{key}")

    return Phase32eEvidenceSummary(
        branch=EXPECTED_BRANCH,
        commit=commit,
        test_date=test_date,
        sensor_id=sensor_id,
        software_pass=True,
    )


def _require_sanitized(raw: str) -> None:
    lowered = raw.lower()
    if _COM_RE.search(raw) or _WINDOWS_PATH_RE.search(raw):
        raise Phase32eEvidenceError("candidate contains a COM port or absolute local path")
    if any(marker.lower() in lowered for marker in _PRIVATE_MARKERS):
        raise Phase32eEvidenceError("candidate contains private local information")
    if any(marker in lowered for marker in _PLACEHOLDERS):
        raise Phase32eEvidenceError("candidate contains template placeholders")


def _require_sanitized_relative_path(value: str, label: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value:
        raise Phase32eEvidenceError(f"{label} must be a sanitized repository-relative path")


def _object(mapping: Mapping[str, Any], key: str) -> dict[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, dict):
        raise Phase32eEvidenceError(f"{key} must be an object")
    return value


def _string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise Phase32eEvidenceError(f"{key} must be a non-empty string")
    return value


def _require_non_placeholder_string(mapping: Mapping[str, Any], key: str) -> None:
    value = _string(mapping, key)
    if value.upper() in {"UNVERIFIED", "MANUAL_ACTION_REQUIRED"}:
        raise Phase32eEvidenceError(f"{key} must contain an observed manual result")


def _equal(mapping: Mapping[str, Any], key: str, expected: object) -> None:
    if mapping.get(key) != expected or (isinstance(expected, int) and isinstance(mapping.get(key), bool)):
        raise Phase32eEvidenceError(f"{key} must be {expected!r}")


def _require_exact_fields(mapping: Mapping[str, Any], expected: set[str], label: str) -> None:
    unknown = sorted(set(mapping) - expected)
    missing = sorted(expected - set(mapping))
    if unknown or missing:
        raise Phase32eEvidenceError(f"{label} fields mismatch; missing={missing}, unknown={unknown}")
