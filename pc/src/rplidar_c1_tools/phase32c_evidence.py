"""Validation for the Phase 3.2C BMP280 physical evidence capture."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


EVIDENCE_RELATIVE_PATH = Path("evidence/phase3.2c/bmp280_physical_adef636_20260718_002346.jsonl")
EVIDENCE_SHA256 = "1BB0C5BE149DC7C49A3C63432D1CAE4AACAE3D5A80265FE879CA06D1E1A74805"
SOURCE_FIRMWARE_COMMIT = "adef636"
FORMAL_KEIL_HEX_SHA256 = "85101B9F76C27FDFA019E382FC7285F239F78FA78FB0722B0400F8DDFF67E27E"

EXPECTED_PROTOCOL = "mars_scout_stm32_sensor_telemetry"
EXPECTED_VERSION = 1
EXPECTED_SENSOR_ID = "bmp280_1"
EXPECTED_ADDRESS = "0x76"
EXPECTED_CHIP_ID = "0x58"
EXPECTED_CTRL_MEAS = "0x27"
EXPECTED_CONFIG = "0x80"
EXPECTED_RECORD_COUNT = 61
EXPECTED_ENVIRONMENTAL_COUNT = 60
EXPECTED_SEQUENCE_START = 0
EXPECTED_SEQUENCE_END = 60
EXPECTED_INTERVAL_MS = 500
EXPECTED_TEMPERATURE_MIN_C = Decimal("26.18")
EXPECTED_TEMPERATURE_MAX_C = Decimal("26.23")
EXPECTED_PRESSURE_MIN_PA = Decimal("99867")
EXPECTED_PRESSURE_MAX_PA = Decimal("99882")

_PRIVATE_MARKERS = (
    "C:" + "\\Users",
    "Desk" + "top",
    "App" + "Data",
    "Documents" + "\\GitHub",
    "zig" + "xi",
    "unique 96-" + "bit",
)
_COM_PORT_PATTERN = re.compile(r"\bCOM[0-9]+\b", re.IGNORECASE)


class Phase32cEvidenceError(ValueError):
    """Raised when the Phase 3.2C evidence file does not match the locked facts."""


@dataclass(frozen=True, slots=True)
class Phase32cEvidenceSummary:
    sha256: str
    record_count: int
    sensor_identity_count: int
    environmental_count: int
    sequence_start: int
    sequence_end: int
    first_timestamp_ms: int
    first_environmental_timestamp_ms: int
    last_timestamp_ms: int
    capture_duration_ms: int
    environmental_span_ms: int
    environmental_interval_ms: int
    temperature_min_c: Decimal
    temperature_max_c: Decimal
    pressure_min_pa: Decimal
    pressure_max_pa: Decimal
    configured_address: str
    expected_chip_id: str
    chip_id: str
    ctrl_meas: str
    config: str


def validate_phase32c_bmp280_evidence(
    path: Path,
    *,
    expected_sha256: str = EVIDENCE_SHA256,
) -> Phase32cEvidenceSummary:
    raw_bytes = path.read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest().upper()
    if actual_sha256 != expected_sha256:
        raise Phase32cEvidenceError(
            f"expected evidence sha256 {expected_sha256}, got {actual_sha256}"
        )

    raw_text = raw_bytes.decode("utf-8")
    _validate_no_private_local_information(raw_text)
    records = _parse_jsonl(raw_text)
    return _validate_records(records, actual_sha256)


def _validate_no_private_local_information(raw_text: str) -> None:
    for marker in _PRIVATE_MARKERS:
        if marker in raw_text:
            raise Phase32cEvidenceError("evidence contains private local information")
    if _COM_PORT_PATTERN.search(raw_text):
        raise Phase32cEvidenceError("evidence contains a concrete COM port")


def _parse_jsonl(raw_text: str) -> list[Mapping[str, Any]]:
    lines = raw_text.splitlines()
    if len(lines) != EXPECTED_RECORD_COUNT:
        raise Phase32cEvidenceError(f"expected {EXPECTED_RECORD_COUNT} JSONL records")

    records: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line:
            raise Phase32cEvidenceError(f"blank JSONL line at {line_number}")
        try:
            record = json.loads(line, parse_float=Decimal)
        except json.JSONDecodeError as exc:
            raise Phase32cEvidenceError(f"invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise Phase32cEvidenceError(f"record {line_number} is not a JSON object")
        records.append(record)
    return records


def _validate_records(records: Sequence[Mapping[str, Any]], sha256: str) -> Phase32cEvidenceSummary:
    if len(records) != EXPECTED_RECORD_COUNT:
        raise Phase32cEvidenceError(f"expected {EXPECTED_RECORD_COUNT} records")

    _require_sequences(records)
    _require_timestamps(records)
    _require_common_fields(records)

    identity_records = [record for record in records if record["message_type"] == "sensor_identity"]
    environmental_records = [record for record in records if record["message_type"] == "environmental"]
    if len(identity_records) != 1:
        raise Phase32cEvidenceError("expected exactly one sensor_identity record")
    if len(environmental_records) != EXPECTED_ENVIRONMENTAL_COUNT:
        raise Phase32cEvidenceError(f"expected {EXPECTED_ENVIRONMENTAL_COUNT} environmental records")
    if len(identity_records) + len(environmental_records) != len(records):
        raise Phase32cEvidenceError("unexpected message_type in evidence")

    payload = _payload(identity_records[0])
    _require_equal(payload, "configured_address", EXPECTED_ADDRESS)
    _require_equal(payload, "expected_chip_id", EXPECTED_CHIP_ID)
    _require_equal(payload, "chip_id", EXPECTED_CHIP_ID)
    _require_equal(payload, "ctrl_meas", EXPECTED_CTRL_MEAS)
    _require_equal(payload, "config", EXPECTED_CONFIG)
    if payload.get("error_code") is not None:
        raise Phase32cEvidenceError("identity error_code must be null")

    intervals = [
        int(next_record["timestamp_ms"]) - int(record["timestamp_ms"])
        for record, next_record in zip(environmental_records, environmental_records[1:])
    ]
    if intervals != [EXPECTED_INTERVAL_MS] * (EXPECTED_ENVIRONMENTAL_COUNT - 1):
        raise Phase32cEvidenceError("environmental intervals are not exactly 500 ms")

    all_intervals = [
        int(next_record["timestamp_ms"]) - int(record["timestamp_ms"])
        for record, next_record in zip(records, records[1:])
    ]
    if all_intervals != [EXPECTED_INTERVAL_MS] * (EXPECTED_RECORD_COUNT - 1):
        raise Phase32cEvidenceError("record intervals are not exactly 500 ms")

    temperatures = [_numeric_decimal(_payload(record).get("temperature_c"), "temperature_c") for record in environmental_records]
    pressures = [_numeric_decimal(_payload(record).get("pressure_pa"), "pressure_pa") for record in environmental_records]
    if min(temperatures) != EXPECTED_TEMPERATURE_MIN_C or max(temperatures) != EXPECTED_TEMPERATURE_MAX_C:
        raise Phase32cEvidenceError("temperature range does not match formal capture")
    if min(pressures) != EXPECTED_PRESSURE_MIN_PA or max(pressures) != EXPECTED_PRESSURE_MAX_PA:
        raise Phase32cEvidenceError("pressure range does not match formal capture")

    return Phase32cEvidenceSummary(
        sha256=sha256,
        record_count=len(records),
        sensor_identity_count=len(identity_records),
        environmental_count=len(environmental_records),
        sequence_start=int(records[0]["sequence"]),
        sequence_end=int(records[-1]["sequence"]),
        first_timestamp_ms=int(records[0]["timestamp_ms"]),
        first_environmental_timestamp_ms=int(environmental_records[0]["timestamp_ms"]),
        last_timestamp_ms=int(records[-1]["timestamp_ms"]),
        capture_duration_ms=int(records[-1]["timestamp_ms"]) - int(records[0]["timestamp_ms"]),
        environmental_span_ms=int(environmental_records[-1]["timestamp_ms"])
        - int(environmental_records[0]["timestamp_ms"]),
        environmental_interval_ms=EXPECTED_INTERVAL_MS,
        temperature_min_c=min(temperatures),
        temperature_max_c=max(temperatures),
        pressure_min_pa=min(pressures),
        pressure_max_pa=max(pressures),
        configured_address=str(payload["configured_address"]),
        expected_chip_id=str(payload["expected_chip_id"]),
        chip_id=str(payload["chip_id"]),
        ctrl_meas=str(payload["ctrl_meas"]),
        config=str(payload["config"]),
    )


def _require_sequences(records: Sequence[Mapping[str, Any]]) -> None:
    expected = list(range(EXPECTED_SEQUENCE_START, EXPECTED_SEQUENCE_END + 1))
    observed = [record.get("sequence") for record in records]
    if observed != expected:
        raise Phase32cEvidenceError("sequence values must run from 0 through 60 with no gaps")


def _require_timestamps(records: Sequence[Mapping[str, Any]]) -> None:
    for index, record in enumerate(records):
        timestamp_ms = record.get("timestamp_ms")
        if not isinstance(timestamp_ms, int) or isinstance(timestamp_ms, bool):
            raise Phase32cEvidenceError(f"record {index} timestamp_ms must be an integer")


def _require_common_fields(records: Sequence[Mapping[str, Any]]) -> None:
    for index, record in enumerate(records):
        _require_equal(record, "protocol", EXPECTED_PROTOCOL)
        _require_equal(record, "version", EXPECTED_VERSION)
        _require_equal(record, "sensor_id", EXPECTED_SENSOR_ID)
        _require_equal(record, "status", "ok")
        if _payload(record).get("error_code") not in (None, ""):
            raise Phase32cEvidenceError(f"record {index} contains an error_code")


def _payload(record: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise Phase32cEvidenceError("record payload must be a JSON object")
    return payload


def _require_equal(mapping: Mapping[str, Any], key: str, expected: object) -> None:
    if mapping.get(key) != expected:
        raise Phase32cEvidenceError(f"{key} must be {expected!r}")


def _numeric_decimal(value: object, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise Phase32cEvidenceError(f"{label} must be numeric")
    return Decimal(value)
