from __future__ import annotations

import json
from pathlib import Path

import pytest

from rplidar_c1_tools.openrf1_hcsr04_bringup import (
    HCSR04_ECHO_TIMEOUT_US,
    HCSR04_ERROR_ECHO_RISE_TIMEOUT,
    Hcsr04ErrorRecord,
    Hcsr04Measurement,
    Hcsr04WrongSensorError,
    format_error_telemetry,
    format_identity_telemetry,
    format_measurement_telemetry,
    iter_hcsr04_bringup_telemetry,
    parse_hcsr04_bringup_line,
)
from rplidar_c1_tools.stm32_sensor_protocol import Stm32TelemetryFormatError


REPO_ROOT = Path(__file__).resolve().parents[2]
INVALID_FIXTURE = REPO_ROOT / "data/test_vectors/phase3.2e/hcsr04_invalid_cases.jsonl"


def _replace(line: str, **updates: object) -> str:
    record = json.loads(line)
    record.update(updates)
    return json.dumps(record, separators=(",", ":")) + "\n"


def test_parser_accepts_identity_success_timeout_and_recovery():
    lines = [
        format_identity_telemetry(sequence=0, timestamp_ms=0),
        format_measurement_telemetry(
            sequence=1,
            timestamp_ms=100,
            measurement=Hcsr04Measurement(echo_pulse_us=2_000),
        ),
        format_error_telemetry(
            sequence=2,
            timestamp_ms=200,
            error=Hcsr04ErrorRecord(
                code=HCSR04_ERROR_ECHO_RISE_TIMEOUT,
                operation="wait_for_echo_rising_edge",
                timeout_us=HCSR04_ECHO_TIMEOUT_US,
            ),
        ),
        format_measurement_telemetry(
            sequence=3,
            timestamp_ms=300,
            measurement=Hcsr04Measurement(echo_pulse_us=1_000),
        ),
    ]
    messages = list(iter_hcsr04_bringup_telemetry(lines))
    assert [message.status for message in messages] == ["ok", "ok", "error", "ok"]
    assert messages[2].error == {
        "code": "echo_rise_timeout",
        "operation": "wait_for_echo_rising_edge",
        "timeout_us": 30_000,
    }


def test_parser_rejects_unknown_missing_and_inconsistent_fields():
    good = format_measurement_telemetry(
        sequence=1,
        timestamp_ms=100,
        measurement=Hcsr04Measurement(echo_pulse_us=2_000),
    )
    record = json.loads(good)
    record["payload"]["distance_mm"] = 344
    inconsistent = json.dumps(record) + "\n"
    record = json.loads(good)
    del record["payload"]["distance_model"]
    missing = json.dumps(record) + "\n"
    record = json.loads(good)
    record["payload"]["surprise"] = 1
    unknown = json.dumps(record) + "\n"

    for line in (inconsistent, missing, unknown, "not-json\n"):
        with pytest.raises(Stm32TelemetryFormatError):
            parse_hcsr04_bringup_line(line)


def test_parser_enforces_neutral_sensor_scope_and_ordering():
    identity = format_identity_telemetry(sequence=0, timestamp_ms=0)
    ultrasonic_2 = _replace(identity, sensor_id="ultrasonic_2")
    front = _replace(identity, sensor_id="front")

    assert parse_hcsr04_bringup_line(
        ultrasonic_2,
        allowed_sensor_ids=("ultrasonic_2",),
    ).sensor_id == "ultrasonic_2"
    with pytest.raises(Hcsr04WrongSensorError):
        parse_hcsr04_bringup_line(ultrasonic_2)
    with pytest.raises(Stm32TelemetryFormatError):
        parse_hcsr04_bringup_line(front, allowed_sensor_ids=("ultrasonic_1",))

    repeated = [identity, _replace(identity, sequence=0, timestamp_ms=100)]
    with pytest.raises(Stm32TelemetryFormatError, match="sequence"):
        list(iter_hcsr04_bringup_telemetry(repeated))
    rollback = [identity, _replace(identity, sequence=1, timestamp_ms=100), _replace(identity, sequence=2)]
    with pytest.raises(Stm32TelemetryFormatError, match="timestamp"):
        list(iter_hcsr04_bringup_telemetry(rollback))


@pytest.mark.parametrize("sensor_id", ["ultrasonic_2", "ultrasonic_3"])
def test_optional_neutral_sensor_ids_are_accepted_only_when_selected(sensor_id: str):
    line = _replace(format_identity_telemetry(sequence=0, timestamp_ms=0), sensor_id=sensor_id)
    assert parse_hcsr04_bringup_line(line, allowed_sensor_ids=(sensor_id,)).sensor_id == sensor_id
    with pytest.raises(Hcsr04WrongSensorError):
        parse_hcsr04_bringup_line(line)


@pytest.mark.parametrize("sensor_id", ["front", "left", "right"])
def test_mounting_semantic_ids_are_rejected(sensor_id: str):
    line = _replace(format_identity_telemetry(sequence=0, timestamp_ms=0), sensor_id=sensor_id)
    with pytest.raises(Stm32TelemetryFormatError):
        parse_hcsr04_bringup_line(line)


def test_invalid_fixture_and_pulse_boundaries_are_rejected():
    for line in INVALID_FIXTURE.read_text(encoding="utf-8").splitlines():
        with pytest.raises(Stm32TelemetryFormatError):
            parse_hcsr04_bringup_line(line)

    good = json.loads(
        format_measurement_telemetry(
            sequence=0,
            timestamp_ms=0,
            measurement=Hcsr04Measurement(echo_pulse_us=1),
        )
    )
    assert good["payload"]["distance_mm"] == 0
    for pulse in (-1, 0, 30_000):
        record = json.loads(json.dumps(good))
        record["payload"]["echo_pulse_us"] = pulse
        record["payload"]["distance_mm"] = 0
        with pytest.raises(Stm32TelemetryFormatError):
            parse_hcsr04_bringup_line(json.dumps(record))


def test_each_iterator_call_starts_an_independent_session():
    first = [format_identity_telemetry(sequence=0, timestamp_ms=0)]
    second = [format_identity_telemetry(sequence=0, timestamp_ms=0)]
    assert len(list(iter_hcsr04_bringup_telemetry(first))) == 1
    assert len(list(iter_hcsr04_bringup_telemetry(second))) == 1
