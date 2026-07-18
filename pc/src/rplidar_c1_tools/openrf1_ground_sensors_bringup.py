"""Host-testable OpenRF1 ground-sensor bring-up helpers for Phase 3.2F."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


GROUND_SENSOR_GROUP_ID = "ground_sensors"
GROUND_CONNECTOR = "OpenRF1_four_channel_tracking"
GROUND_CONNECTOR_PART = "HDGC2001WV-6P"
GROUND_CONNECTOR_PIN_ORDER = (
    (1, "GND"),
    (2, "X4_schematic_PC14_unused"),
    (3, "X3_PB0"),
    (4, "X2_PC5"),
    (5, "X1_PC4"),
    (6, "VCC_5V"),
)
GROUND_SAMPLE_PERIOD_MS = 5
GROUND_TELEMETRY_PERIOD_MS = 50
GROUND_DEBOUNCE_SAMPLES = 4
GROUND_EFFECTIVE_DEBOUNCE_MS = 20
GROUND_GPIO_MODE = "floating_input"
GROUND_SEMANTIC_POLARITY = "unverified"
GROUND_PROTOCOL = "mars_scout_stm32_sensor_telemetry"
GROUND_VERSION = 1

LEFT_TCRT5000 = "left_tcrt5000"
RIGHT_TCRT5000 = "right_tcrt5000"
HALL_SENSOR = "hall_sensor"

GROUND_CHANNELS: dict[str, dict[str, Any]] = {
    LEFT_TCRT5000: {
        "connector_signal": 1,
        "connector_label": "X1",
        "mcu_pin": "PC4",
        "gpio_port": "GPIOC",
        "gpio_pin": "GPIO_Pin_4",
        "supply": "3.3V",
    },
    RIGHT_TCRT5000: {
        "connector_signal": 2,
        "connector_label": "X2",
        "mcu_pin": "PC5",
        "gpio_port": "GPIOC",
        "gpio_pin": "GPIO_Pin_5",
        "supply": "3.3V",
    },
    HALL_SENSOR: {
        "connector_signal": 3,
        "connector_label": "X3",
        "mcu_pin": "PB0",
        "gpio_port": "GPIOB",
        "gpio_pin": "GPIO_Pin_0",
        "module_supply": "5V",
        "input_protection": "external_10k_15k_divider_required",
    },
}
GROUND_SIGNAL4 = {
    "status": "unused",
    "connector_signal": 4,
    "connector_label": "X4",
    "schematic_mcu_pin": "PC14",
    "vendor_example_mcu_pin": "PB1",
    "mapping_conflict": "schematic_PC14_vendor_example_PB1",
}

TCRT_SUPPLY_MV = 3300
HALL_MODULE_SUPPLY_MV = 5000
HALL_DIVIDER_SERIES_RESISTOR_OHM = 10_000
HALL_DIVIDER_PULLDOWN_RESISTOR_OHM = 15_000
HALL_DIVIDER_TOLERANCE_PERCENT = 5
HALL_DIRECT_TO_PB0_ALLOWED = False
SHARED_MODULE_VCC_ALLOWED = False

ERROR_INVALID_LEVEL = "invalid_level"
ERROR_INVALID_DEBOUNCE_THRESHOLD = "invalid_debounce_threshold"
ERROR_DUPLICATE_GPIO_ASSIGNMENT = "duplicate_gpio_assignment"
ERROR_UNSUPPORTED_GPIO_MAPPING = "unsupported_gpio_mapping"
ERROR_SCHEDULER_INVARIANT = "scheduler_invariant"
ERROR_CODES = (
    ERROR_INVALID_LEVEL,
    ERROR_INVALID_DEBOUNCE_THRESHOLD,
    ERROR_DUPLICATE_GPIO_ASSIGNMENT,
    ERROR_UNSUPPORTED_GPIO_MAPPING,
    ERROR_SCHEDULER_INVARIANT,
)


class GroundSensorsBringupError(ValueError):
    """Raised for invalid Phase 3.2F software inputs."""


@dataclass(slots=True)
class DebouncedDigitalInput:
    raw_level: int
    debounced_level: int
    candidate_level: int
    candidate_count: int
    debounce_samples: int = GROUND_DEBOUNCE_SAMPLES

    @classmethod
    def from_initial_level(cls, initial_level: int, *, debounce_samples: int = GROUND_DEBOUNCE_SAMPLES) -> "DebouncedDigitalInput":
        _validate_level(initial_level)
        if debounce_samples <= 0:
            raise GroundSensorsBringupError(ERROR_INVALID_DEBOUNCE_THRESHOLD)
        level = 1 if initial_level else 0
        return cls(
            raw_level=level,
            debounced_level=level,
            candidate_level=level,
            candidate_count=0,
            debounce_samples=debounce_samples,
        )

    def update(self, raw_level: int) -> None:
        _validate_level(raw_level)
        raw = 1 if raw_level else 0
        self.raw_level = raw
        if raw == self.debounced_level:
            self.candidate_level = raw
            self.candidate_count = 0
            return
        if raw != self.candidate_level:
            self.candidate_level = raw
            self.candidate_count = 1
            return
        if self.candidate_count < self.debounce_samples:
            self.candidate_count += 1
        if self.candidate_count >= self.debounce_samples:
            self.debounced_level = raw
            self.candidate_level = raw
            self.candidate_count = 0


@dataclass(slots=True)
class GroundSensorsState:
    left_tcrt5000: DebouncedDigitalInput
    right_tcrt5000: DebouncedDigitalInput
    hall_sensor: DebouncedDigitalInput

    @classmethod
    def from_initial_levels(
        cls,
        *,
        left_tcrt5000: int,
        right_tcrt5000: int,
        hall_sensor: int,
        debounce_samples: int = GROUND_DEBOUNCE_SAMPLES,
    ) -> "GroundSensorsState":
        return cls(
            left_tcrt5000=DebouncedDigitalInput.from_initial_level(
                left_tcrt5000,
                debounce_samples=debounce_samples,
            ),
            right_tcrt5000=DebouncedDigitalInput.from_initial_level(
                right_tcrt5000,
                debounce_samples=debounce_samples,
            ),
            hall_sensor=DebouncedDigitalInput.from_initial_level(
                hall_sensor,
                debounce_samples=debounce_samples,
            ),
        )

    def update_sample(self, *, left_tcrt5000: int, right_tcrt5000: int, hall_sensor: int) -> None:
        self.left_tcrt5000.update(left_tcrt5000)
        self.right_tcrt5000.update(right_tcrt5000)
        self.hall_sensor.update(hall_sensor)


def connector_pin_map() -> dict[int, str]:
    return dict(GROUND_CONNECTOR_PIN_ORDER)


def active_signal_map() -> dict[int, str]:
    return {
        int(config["connector_signal"]): str(config["mcu_pin"])
        for config in GROUND_CHANNELS.values()
    }


def validate_static_configuration() -> None:
    signals = tuple(config["connector_signal"] for config in GROUND_CHANNELS.values())
    if signals != (1, 2, 3):
        raise GroundSensorsBringupError(ERROR_UNSUPPORTED_GPIO_MAPPING)
    pins = tuple(config["mcu_pin"] for config in GROUND_CHANNELS.values())
    if len(set(pins)) != len(pins):
        raise GroundSensorsBringupError(ERROR_DUPLICATE_GPIO_ASSIGNMENT)
    if "PB1" in pins or "PC14" in pins:
        raise GroundSensorsBringupError(ERROR_UNSUPPORTED_GPIO_MAPPING)
    if GROUND_SIGNAL4["status"] != "unused":
        raise GroundSensorsBringupError(ERROR_UNSUPPORTED_GPIO_MAPPING)
    if GROUND_SAMPLE_PERIOD_MS != 5 or GROUND_TELEMETRY_PERIOD_MS != 50:
        raise GroundSensorsBringupError(ERROR_SCHEDULER_INVARIANT)
    if GROUND_DEBOUNCE_SAMPLES != 4 or GROUND_EFFECTIVE_DEBOUNCE_MS != 20:
        raise GroundSensorsBringupError(ERROR_INVALID_DEBOUNCE_THRESHOLD)


def hall_divider_output_mv(input_mv: int) -> int:
    if input_mv < 0:
        raise GroundSensorsBringupError("input_mv must be non-negative")
    denominator = HALL_DIVIDER_SERIES_RESISTOR_OHM + HALL_DIVIDER_PULLDOWN_RESISTOR_OHM
    numerator = input_mv * HALL_DIVIDER_PULLDOWN_RESISTOR_OHM
    return (numerator + denominator // 2) // denominator


def scheduled_deadlines(*, start_ms: int, period_ms: int, count: int) -> tuple[int, ...]:
    if start_ms < 0 or period_ms <= 0 or count < 0:
        raise GroundSensorsBringupError(ERROR_SCHEDULER_INVARIANT)
    return tuple(start_ms + period_ms * index for index in range(1, count + 1))


def format_identity_telemetry(*, sequence: int, timestamp_ms: int) -> str:
    validate_static_configuration()
    payload: dict[str, Any] = {
        "sensor_group": GROUND_SENSOR_GROUP_ID,
        "connector": GROUND_CONNECTOR,
        "connector_part": GROUND_CONNECTOR_PART,
        "connector_pin_order": [
            {"pin": pin, "signal": signal} for pin, signal in GROUND_CONNECTOR_PIN_ORDER
        ],
        "sample_period_ms": GROUND_SAMPLE_PERIOD_MS,
        "telemetry_period_ms": GROUND_TELEMETRY_PERIOD_MS,
        "debounce_samples": GROUND_DEBOUNCE_SAMPLES,
        "effective_debounce_ms": GROUND_EFFECTIVE_DEBOUNCE_MS,
        "semantic_polarity": GROUND_SEMANTIC_POLARITY,
        "gpio_mode": GROUND_GPIO_MODE,
        "channels": {
            LEFT_TCRT5000: {
                "connector_signal": GROUND_CHANNELS[LEFT_TCRT5000]["connector_signal"],
                "connector_label": GROUND_CHANNELS[LEFT_TCRT5000]["connector_label"],
                "mcu_pin": GROUND_CHANNELS[LEFT_TCRT5000]["mcu_pin"],
                "supply": GROUND_CHANNELS[LEFT_TCRT5000]["supply"],
            },
            RIGHT_TCRT5000: {
                "connector_signal": GROUND_CHANNELS[RIGHT_TCRT5000]["connector_signal"],
                "connector_label": GROUND_CHANNELS[RIGHT_TCRT5000]["connector_label"],
                "mcu_pin": GROUND_CHANNELS[RIGHT_TCRT5000]["mcu_pin"],
                "supply": GROUND_CHANNELS[RIGHT_TCRT5000]["supply"],
            },
            HALL_SENSOR: {
                "connector_signal": GROUND_CHANNELS[HALL_SENSOR]["connector_signal"],
                "connector_label": GROUND_CHANNELS[HALL_SENSOR]["connector_label"],
                "mcu_pin": GROUND_CHANNELS[HALL_SENSOR]["mcu_pin"],
                "module_supply": GROUND_CHANNELS[HALL_SENSOR]["module_supply"],
                "input_protection": GROUND_CHANNELS[HALL_SENSOR]["input_protection"],
            },
        },
        "signal_4": {
            "status": GROUND_SIGNAL4["status"],
            "mapping_conflict": GROUND_SIGNAL4["mapping_conflict"],
        },
    }
    return _json_line(sequence, timestamp_ms, "sensor_identity", "ok", payload)


def format_ground_sensors_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    state: GroundSensorsState,
) -> str:
    payload = {
        LEFT_TCRT5000: _channel_payload(state.left_tcrt5000),
        RIGHT_TCRT5000: _channel_payload(state.right_tcrt5000),
        HALL_SENSOR: _channel_payload(state.hall_sensor),
    }
    return _json_line(sequence, timestamp_ms, "ground_sensors", "ok", payload)


def format_error_telemetry(*, sequence: int, timestamp_ms: int, code: str, operation: str) -> str:
    if code not in ERROR_CODES:
        raise GroundSensorsBringupError(f"unknown ground-sensor error code: {code}")
    return _json_line(
        sequence,
        timestamp_ms,
        "ground_sensors",
        "error",
        {"sensor_group": GROUND_SENSOR_GROUP_ID},
        error={"code": code, "operation": operation},
    )


def _channel_payload(channel: DebouncedDigitalInput) -> dict[str, int]:
    _validate_level(channel.raw_level)
    _validate_level(channel.debounced_level)
    return {
        "raw_level": channel.raw_level,
        "debounced_level": channel.debounced_level,
    }


def _validate_level(level: int) -> None:
    if level not in (0, 1):
        raise GroundSensorsBringupError(ERROR_INVALID_LEVEL)


def _json_line(
    sequence: int,
    timestamp_ms: int,
    message_type: str,
    status: str,
    payload: dict[str, Any],
    *,
    error: dict[str, Any] | None = None,
) -> str:
    if sequence < 0 or timestamp_ms < 0:
        raise GroundSensorsBringupError("sequence and timestamp_ms must be non-negative")
    record: dict[str, Any] = {
        "protocol": GROUND_PROTOCOL,
        "version": GROUND_VERSION,
        "sequence": sequence,
        "timestamp_ms": timestamp_ms,
        "message_type": message_type,
        "sensor_id": GROUND_SENSOR_GROUP_ID,
        "status": status,
        "payload": payload,
    }
    if error is not None:
        record["error"] = error
    return json.dumps(record, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n"
