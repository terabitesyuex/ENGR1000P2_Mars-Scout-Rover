from __future__ import annotations

import json

import pytest

from rplidar_c1_tools.stm32_sensor_models import Stm32TelemetryMessage
from rplidar_c1_tools.stm32_sensor_protocol import (
    Stm32TelemetryFormatError,
    encode_stm32_telemetry_message,
    iter_stm32_telemetry,
    parse_stm32_telemetry_line,
)


def _message(
    message_type: str,
    sensor_id: str,
    payload: dict[str, object],
    *,
    status: str = "simulated",
) -> Stm32TelemetryMessage:
    return Stm32TelemetryMessage(
        sequence=0,
        timestamp_ms=0,
        message_type=message_type,
        sensor_id=sensor_id,
        payload=payload,
        status=status,
    )


def _base_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "protocol": "mars_scout_stm32_sensor_telemetry",
        "version": 1,
        "sequence": 0,
        "timestamp_ms": 0,
        "message_type": "ultrasonic",
        "sensor_id": "ultrasonic_1",
        "payload": {"distance_mm": 500, "valid": True},
        "status": "simulated",
    }
    payload.update(overrides)
    return payload


def _line_with(**overrides: object) -> str:
    return json.dumps(_base_payload(**overrides), allow_nan=False)


def _line_without(key: str) -> str:
    payload = _base_payload()
    payload.pop(key)
    return json.dumps(payload, allow_nan=False)


def _line_raw_payload(raw_payload: str) -> str:
    return (
        '{"protocol":"mars_scout_stm32_sensor_telemetry","version":1,'
        '"sequence":0,"timestamp_ms":0,"message_type":"illuminance",'
        '"sensor_id":"bh1750_1","payload":'
        + raw_payload
        + ',"status":"simulated"}'
    )


def test_valid_round_trip_for_every_phase31_message_type():
    messages = [
        _message("ultrasonic", "ultrasonic_1", {"distance_mm": 500, "raw_echo_us": 1234, "valid": True}),
        _message(
            "ground_edge",
            "tcrt5000_1",
            {"raw_state": 1, "polarity_verified": True, "interpreted_edge_detected": True},
        ),
        _message(
            "hall_landmark",
            "hall_1",
            {"raw_state": 0, "polarity_verified": True, "interpreted_landmark_detected": False},
        ),
        _message("illuminance", "bh1750_1", {"illuminance_lux": 320.5}),
        _message("barometer", "bmp280_1", {"temperature_c": 24.0, "pressure_pa": 101_325.0}),
    ]

    for message in messages:
        parsed = parse_stm32_telemetry_line(encode_stm32_telemetry_message(message))
        assert parsed == message


@pytest.mark.parametrize(
    ("line", "match"),
    [
        ("not-json", "invalid JSON"),
        ("[]", "JSON object"),
        (_line_without("protocol"), "missing required field"),
        (_line_with(version=2), "unsupported version"),
        (_line_with(message_type="bad"), "unknown message_type"),
        (_line_with(sensor_id="front_ultrasonic"), "sensor_id"),
        (_line_with(message_type="barometer", sensor_id="ultrasonic_1"), "sensor_id"),
        (_line_with(sequence=-1), "sequence"),
        (_line_with(timestamp_ms=-1), "timestamp_ms"),
        (_line_with(sequence=True), "sequence"),
        (_line_with(status="made_up"), "invalid status"),
        (_line_with(payload=[]), "payload must be an object"),
        (_line_with(extra=1), "unknown top-level field"),
    ],
)
def test_top_level_protocol_errors_are_rejected(line: str, match: str):
    with pytest.raises(Stm32TelemetryFormatError, match=match):
        parse_stm32_telemetry_line(line, line_number=3)


def test_stream_validation_reports_line_number_for_ordering_errors():
    first = _line_with(sequence=1, timestamp_ms=10)
    duplicate = _line_with(sequence=1, timestamp_ms=11)
    with pytest.raises(Stm32TelemetryFormatError, match="line 2: sequence"):
        list(iter_stm32_telemetry([first, duplicate]))

    second_backwards = _line_with(sequence=2, timestamp_ms=9)
    with pytest.raises(Stm32TelemetryFormatError, match="line 2: timestamp_ms"):
        list(iter_stm32_telemetry([first, second_backwards]))


def test_nan_and_infinity_are_rejected():
    for value in ("NaN", "Infinity"):
        line = _line_raw_payload(f'{{"illuminance_lux":{value}}}')
        with pytest.raises(Stm32TelemetryFormatError, match="finite"):
            parse_stm32_telemetry_line(line)


def test_ultrasonic_payload_semantics():
    parse_stm32_telemetry_line(
        _line_with(payload={"distance_mm": 0, "raw_echo_us": 0, "valid": True})
    )
    timeout = _line_with(status="timeout", payload={"raw_echo_us": None, "valid": False})
    assert parse_stm32_telemetry_line(timeout).status == "timeout"

    with pytest.raises(Stm32TelemetryFormatError, match="distance_mm"):
        parse_stm32_telemetry_line(_line_with(payload={"distance_mm": -1, "valid": True}))
    with pytest.raises(Stm32TelemetryFormatError, match="must not include"):
        parse_stm32_telemetry_line(
            _line_with(status="timeout", payload={"distance_mm": 0, "valid": False})
        )
    with pytest.raises(Stm32TelemetryFormatError, match="raw_echo_us"):
        parse_stm32_telemetry_line(_line_with(payload={"distance_mm": 1, "raw_echo_us": True, "valid": True}))


def test_digital_payload_preserves_unverified_polarity_and_rejects_bool_raw_state():
    ground = parse_stm32_telemetry_line(
        _line_with(
            message_type="ground_edge",
            sensor_id="tcrt5000_1",
            payload={
                "raw_state": 1,
                "polarity_verified": False,
                "interpreted_edge_detected": None,
            },
        )
    )
    assert ground.payload["interpreted_edge_detected"] is None

    with pytest.raises(Stm32TelemetryFormatError, match="raw_state"):
        parse_stm32_telemetry_line(
            _line_with(
                message_type="ground_edge",
                sensor_id="tcrt5000_1",
                payload={
                    "raw_state": True,
                    "polarity_verified": False,
                    "interpreted_edge_detected": None,
                },
            )
        )
    with pytest.raises(Stm32TelemetryFormatError, match="until polarity"):
        parse_stm32_telemetry_line(
            _line_with(
                message_type="hall_landmark",
                sensor_id="hall_1",
                payload={
                    "raw_state": 1,
                    "polarity_verified": False,
                    "interpreted_landmark_detected": True,
                },
            )
        )


def test_environment_payload_rules_and_no_altitude_field():
    parse_stm32_telemetry_line(
        _line_with(message_type="illuminance", sensor_id="bh1750_1", payload={"illuminance_lux": 0.0})
    )
    parse_stm32_telemetry_line(
        _line_with(
            message_type="illuminance",
            sensor_id="bh1750_1",
            status="invalid_reading",
            payload={"illuminance_lux": None},
        )
    )
    with pytest.raises(Stm32TelemetryFormatError, match="non-negative"):
        parse_stm32_telemetry_line(
            _line_with(message_type="illuminance", sensor_id="bh1750_1", payload={"illuminance_lux": -0.1})
        )
    with pytest.raises(Stm32TelemetryFormatError, match="unknown payload field"):
        parse_stm32_telemetry_line(
            _line_with(
                message_type="barometer",
                sensor_id="bmp280_1",
                payload={"temperature_c": 20.0, "pressure_pa": 101_000.0, "altitude_m": 5.0},
            )
        )


