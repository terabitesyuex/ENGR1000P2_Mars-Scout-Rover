"""Typed models for Phase 3.1 STM32 low-rate sensor telemetry."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


STM32_TELEMETRY_PROTOCOL = "mars_scout_stm32_sensor_telemetry"
STM32_TELEMETRY_VERSION = 1

TELEMETRY_STATUSES = (
    "ok",
    "timeout",
    "out_of_range",
    "invalid_reading",
    "not_initialized",
    "stale",
    "hardware_fault",
    "simulated",
)

MESSAGE_TYPES = (
    "ultrasonic",
    "ground_edge",
    "hall_landmark",
    "illuminance",
    "barometer",
)

ULTRASONIC_SENSOR_IDS = ("ultrasonic_1", "ultrasonic_2", "ultrasonic_3")
GROUND_EDGE_SENSOR_IDS = ("tcrt5000_1", "tcrt5000_2")
HALL_SENSOR_IDS = ("hall_1",)
ILLUMINANCE_SENSOR_IDS = ("bh1750_1",)
BAROMETER_SENSOR_IDS = ("bmp280_1",)

SENSOR_IDS_BY_MESSAGE_TYPE = {
    "ultrasonic": ULTRASONIC_SENSOR_IDS,
    "ground_edge": GROUND_EDGE_SENSOR_IDS,
    "hall_landmark": HALL_SENSOR_IDS,
    "illuminance": ILLUMINANCE_SENSOR_IDS,
    "barometer": BAROMETER_SENSOR_IDS,
}


@dataclass(frozen=True, slots=True)
class Stm32TelemetryMessage:
    """One validated transport-facing STM32 sensor telemetry message."""

    sequence: int
    timestamp_ms: int
    message_type: str
    sensor_id: str
    payload: Mapping[str, Any]
    status: str = "ok"
    protocol: str = STM32_TELEMETRY_PROTOCOL
    version: int = STM32_TELEMETRY_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_json(self) -> dict[str, Any]:
        """Return the canonical JSON object for this message."""
        return {
            "protocol": self.protocol,
            "version": self.version,
            "sequence": self.sequence,
            "timestamp_ms": self.timestamp_ms,
            "message_type": self.message_type,
            "sensor_id": self.sensor_id,
            "payload": dict(self.payload),
            "status": self.status,
        }

