from __future__ import annotations

import pytest

from rplidar_c1_tools.stm32_sensor_models import (
    MESSAGE_TYPES,
    SENSOR_IDS_BY_MESSAGE_TYPE,
    STM32_TELEMETRY_PROTOCOL,
    STM32_TELEMETRY_VERSION,
    TELEMETRY_STATUSES,
    Stm32TelemetryMessage,
)


def test_stm32_message_model_is_canonical_and_payload_is_read_only():
    message = Stm32TelemetryMessage(
        sequence=0,
        timestamp_ms=10,
        message_type="ultrasonic",
        sensor_id="ultrasonic_1",
        payload={"distance_mm": 500, "valid": True},
        status="simulated",
    )

    assert message.to_json() == {
        "protocol": STM32_TELEMETRY_PROTOCOL,
        "version": STM32_TELEMETRY_VERSION,
        "sequence": 0,
        "timestamp_ms": 10,
        "message_type": "ultrasonic",
        "sensor_id": "ultrasonic_1",
        "payload": {"distance_mm": 500, "valid": True},
        "status": "simulated",
    }
    with pytest.raises(TypeError):
        message.payload["distance_mm"] = 0  # type: ignore[index]


def test_phase31_model_constants_cover_required_sensors_and_statuses():
    assert set(MESSAGE_TYPES) == {
        "ultrasonic",
        "ground_edge",
        "hall_landmark",
        "illuminance",
        "barometer",
    }
    assert SENSOR_IDS_BY_MESSAGE_TYPE["ultrasonic"] == (
        "ultrasonic_1",
        "ultrasonic_2",
        "ultrasonic_3",
    )
    assert SENSOR_IDS_BY_MESSAGE_TYPE["ground_edge"] == ("tcrt5000_1", "tcrt5000_2")
    assert SENSOR_IDS_BY_MESSAGE_TYPE["hall_landmark"] == ("hall_1",)
    assert SENSOR_IDS_BY_MESSAGE_TYPE["illuminance"] == ("bh1750_1",)
    assert SENSOR_IDS_BY_MESSAGE_TYPE["barometer"] == ("bmp280_1",)
    assert {"ok", "timeout", "out_of_range", "invalid_reading", "simulated"}.issubset(
        set(TELEMETRY_STATUSES)
    )

