"""Validation for the Phase 3.2F isolated TCRT5000 evidence captures."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


EXPECTED_PROTOCOL = "mars_scout_stm32_sensor_telemetry"
EXPECTED_VERSION = 1
EXPECTED_SENSOR_ID = "ground_sensors"
EXPECTED_RECORD_COUNT = 100
EXPECTED_INTERVAL_MS = 50
FORMAL_KEIL_HEX_SHA256 = "999B678986655A2F913EEA643CA1A21EEC0C5CE0C883E4E9A55F5BF9C605FCB5"

CAPTURE_SPECS = {
    "tcrt5000_1_open_space": {
        "path": Path("evidence/phase3.2f/tcrt5000_1_open_space.jsonl"),
        "sha256": "3A51BE6E0D66F5089C7A05BF77E188706484967462552D814B2C0F4C04E3D23E",
        "sequence_start": 20923,
        "timestamp_start_ms": 1046150,
        "states": {"left_tcrt5000": (0, 0)},
    },
    "tcrt5000_1_white_surface": {
        "path": Path("evidence/phase3.2f/tcrt5000_1_white_surface.jsonl"),
        "sha256": "8EEBC9DA5ACC887F496DEE6C279B31A5B3309422AFF303E53AF74CE3CF12255C",
        "sequence_start": 25448,
        "timestamp_start_ms": 1272400,
        "states": {"left_tcrt5000": (1, 1)},
    },
    "tcrt5000_2_open_space": {
        "path": Path("evidence/phase3.2f/tcrt5000_2_open_space.jsonl"),
        "sha256": "402AD39E824B9CBC5FD97D770FD72E81C8577CB27278EC22F628832C336F6D87",
        "sequence_start": 2559,
        "timestamp_start_ms": 127950,
        "states": {"left_tcrt5000": (1, 1), "right_tcrt5000": (0, 0)},
    },
    "tcrt5000_2_white_surface": {
        "path": Path("evidence/phase3.2f/tcrt5000_2_white_surface.jsonl"),
        "sha256": "DBB584BB886EBF647182D419D8C931E87363EC58CE8EF2DF0B920D13FC5710AA",
        "sequence_start": 6205,
        "timestamp_start_ms": 310250,
        "states": {"left_tcrt5000": (1, 1), "right_tcrt5000": (1, 1)},
    },
}

_CHANNELS = ("left_tcrt5000", "right_tcrt5000", "hall_sensor")
_PRIVATE_MARKERS = (
    "C:" + "\\Users",
    "Desk" + "top",
    "App" + "Data",
    "Documents" + "\\GitHub",
    "zig" + "xi",
)
_COM_PORT_PATTERN = re.compile(r"\bCOM[0-9]+\b", re.IGNORECASE)


class Phase32fEvidenceError(ValueError):
    """Raised when a Phase 3.2F capture differs from its locked evidence."""


@dataclass(frozen=True, slots=True)
class Phase32fCaptureSummary:
    name: str
    sha256: str
    record_count: int
    sequence_start: int
    sequence_end: int
    timestamp_start_ms: int
    timestamp_end_ms: int
    capture_span_ms: int
    interval_ms: int


def validate_phase32f_capture(
    repo_root: Path,
    name: str,
    *,
    evidence_path: Path | None = None,
) -> Phase32fCaptureSummary:
    try:
        spec = CAPTURE_SPECS[name]
    except KeyError as exc:
        raise Phase32fEvidenceError(f"unknown capture {name!r}") from exc

    path = evidence_path if evidence_path is not None else repo_root / spec["path"]
    raw_bytes = path.read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest().upper()
    if actual_sha256 != spec["sha256"]:
        raise Phase32fEvidenceError(
            f"expected evidence sha256 {spec['sha256']}, got {actual_sha256}"
        )

    raw_text = raw_bytes.decode("ascii")
    _validate_no_private_local_information(raw_text)
    records = _parse_jsonl(raw_text)
    _validate_records(records, spec)

    return Phase32fCaptureSummary(
        name=name,
        sha256=actual_sha256,
        record_count=len(records),
        sequence_start=int(records[0]["sequence"]),
        sequence_end=int(records[-1]["sequence"]),
        timestamp_start_ms=int(records[0]["timestamp_ms"]),
        timestamp_end_ms=int(records[-1]["timestamp_ms"]),
        capture_span_ms=int(records[-1]["timestamp_ms"]) - int(records[0]["timestamp_ms"]),
        interval_ms=EXPECTED_INTERVAL_MS,
    )


def validate_all_phase32f_captures(repo_root: Path) -> list[Phase32fCaptureSummary]:
    return [validate_phase32f_capture(repo_root, name) for name in CAPTURE_SPECS]


def _validate_no_private_local_information(raw_text: str) -> None:
    if any(marker in raw_text for marker in _PRIVATE_MARKERS) or _COM_PORT_PATTERN.search(raw_text):
        raise Phase32fEvidenceError("evidence contains private local information")


def _parse_jsonl(raw_text: str) -> list[Mapping[str, Any]]:
    lines = raw_text.splitlines()
    if len(lines) != EXPECTED_RECORD_COUNT:
        raise Phase32fEvidenceError(f"expected {EXPECTED_RECORD_COUNT} JSONL records")
    records: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise Phase32fEvidenceError(f"invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise Phase32fEvidenceError(f"record {line_number} is not a JSON object")
        records.append(record)
    return records


def _validate_records(records: Sequence[Mapping[str, Any]], spec: Mapping[str, Any]) -> None:
    sequence_start = int(spec["sequence_start"])
    expected_sequences = list(range(sequence_start, sequence_start + EXPECTED_RECORD_COUNT))
    if [record.get("sequence") for record in records] != expected_sequences:
        raise Phase32fEvidenceError("sequence values are not contiguous")

    timestamp_start_ms = int(spec["timestamp_start_ms"])
    expected_timestamps = [
        timestamp_start_ms + index * EXPECTED_INTERVAL_MS for index in range(EXPECTED_RECORD_COUNT)
    ]
    if [record.get("timestamp_ms") for record in records] != expected_timestamps:
        raise Phase32fEvidenceError("timestamps are not exactly 50 ms apart")

    expected_states = spec["states"]
    for index, record in enumerate(records):
        if record.get("protocol") != EXPECTED_PROTOCOL:
            raise Phase32fEvidenceError(f"record {index} has an unexpected protocol")
        if record.get("version") != EXPECTED_VERSION:
            raise Phase32fEvidenceError(f"record {index} has an unexpected version")
        if record.get("message_type") != "ground_sensors":
            raise Phase32fEvidenceError(f"record {index} has an unexpected message_type")
        if record.get("sensor_id") != EXPECTED_SENSOR_ID or record.get("status") != "ok":
            raise Phase32fEvidenceError(f"record {index} has an unexpected identity or status")
        payload = record.get("payload")
        if not isinstance(payload, dict) or set(payload) != set(_CHANNELS):
            raise Phase32fEvidenceError(f"record {index} has an unexpected payload")
        for channel in _CHANNELS:
            channel_data = payload.get(channel)
            if not isinstance(channel_data, dict) or set(channel_data) != {"raw_level", "debounced_level"}:
                raise Phase32fEvidenceError(f"record {index} has an invalid {channel} object")
            values = (channel_data.get("raw_level"), channel_data.get("debounced_level"))
            if any(type(value) is not int or value not in (0, 1) for value in values):
                raise Phase32fEvidenceError(f"record {index} has a non-binary {channel} level")
        for channel, expected in expected_states.items():
            channel_data = payload[channel]
            observed = (channel_data["raw_level"], channel_data["debounced_level"])
            if observed != tuple(expected):
                raise Phase32fEvidenceError(f"record {index} has an unexpected {channel} state")
