"""Host-testable OpenRF1 HC-SR04 bring-up helpers for Phase 3.2E."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


HCSR04_SENSOR_ID = "ultrasonic_1"
HCSR04_SENSOR_NAME = "hc-sr04"
HCSR04_CONNECTOR = "CN6"
HCSR04_CONNECTOR_PART = "B4B-PH-K-S(LF)(SN)"
HCSR04_CONNECTOR_PIN_ORDER = (
    (1, "VCC_5V"),
    (2, "GND"),
    (3, "PA5_TRIG"),
    (4, "PA4_ECHO"),
)
HCSR04_TRIGGER_MCU_PIN = "PA5"
HCSR04_TRIGGER_GPIO_PORT = "GPIOA"
HCSR04_TRIGGER_GPIO_PIN = "GPIO_Pin_5"
HCSR04_TRIGGER_MODE = "push_pull_output"
HCSR04_ECHO_MCU_PIN = "PA4"
HCSR04_ECHO_GPIO_PORT = "GPIOA"
HCSR04_ECHO_GPIO_PIN = "GPIO_Pin_4"
HCSR04_ECHO_MODE = "floating_input"
HCSR04_TIMER = "TIM6"
HCSR04_TIMER_PRESCALER = 71
HCSR04_TIMER_PERIOD = 30000
HCSR04_TIMER_TICK_HZ = 1_000_000
HCSR04_TRIGGER_PULSE_US = 10
HCSR04_ECHO_TIMEOUT_US = 30_000
HCSR04_MEASUREMENT_PERIOD_MS = 100
HCSR04_DISTANCE_MODEL = "nominal_343_m_per_s_uncalibrated"
HCSR04_DISTANCE_UNIT = "mm"
HCSR04_ECHO_SERIES_RESISTOR_OHM = 10_000
HCSR04_ECHO_PULLDOWN_RESISTOR_OHM = 15_000
HCSR04_ECHO_DIVIDER_TOLERANCE_PERCENT = 5
HCSR04_BRINGUP_PROTOCOL = "mars_scout_stm32_sensor_telemetry"
HCSR04_BRINGUP_VERSION = 1

HCSR04_ERROR_ECHO_NOT_LOW_BEFORE_TRIGGER = "echo_not_low_before_trigger"
HCSR04_ERROR_ECHO_RISE_TIMEOUT = "echo_rise_timeout"
HCSR04_ERROR_ECHO_FALL_TIMEOUT = "echo_fall_timeout"
HCSR04_ERROR_TIMER_CONFIGURATION_FAILURE = "timer_configuration_failure"
HCSR04_ERROR_TIMER_MEASUREMENT_FAILURE = "timer_measurement_failure"
HCSR04_ERROR_PULSE_WIDTH_OUT_OF_BOUNDS = "pulse_width_out_of_bounds"
HCSR04_ERROR_INTERNAL_STATE_ERROR = "internal_state_error"
HCSR04_ERROR_CODES = (
    HCSR04_ERROR_ECHO_NOT_LOW_BEFORE_TRIGGER,
    HCSR04_ERROR_ECHO_RISE_TIMEOUT,
    HCSR04_ERROR_ECHO_FALL_TIMEOUT,
    HCSR04_ERROR_TIMER_CONFIGURATION_FAILURE,
    HCSR04_ERROR_TIMER_MEASUREMENT_FAILURE,
    HCSR04_ERROR_PULSE_WIDTH_OUT_OF_BOUNDS,
    HCSR04_ERROR_INTERNAL_STATE_ERROR,
)


class Hcsr04BringupError(ValueError):
    """Raised for invalid HC-SR04 bring-up inputs."""


@dataclass(frozen=True, slots=True)
class Hcsr04Measurement:
    echo_pulse_us: int

    @property
    def distance_mm(self) -> int:
        return echo_pulse_us_to_distance_mm(self.echo_pulse_us)


@dataclass(frozen=True, slots=True)
class Hcsr04ErrorRecord:
    code: str
    operation: str
    timeout_us: int | None = None


def connector_pin_map() -> dict[int, str]:
    return dict(HCSR04_CONNECTOR_PIN_ORDER)


def echo_divider_output_mv(echo_input_mv: int) -> int:
    """Return nominal external divider output using nearest-integer millivolts."""
    if echo_input_mv < 0:
        raise Hcsr04BringupError("echo_input_mv must be non-negative")
    numerator = echo_input_mv * HCSR04_ECHO_PULLDOWN_RESISTOR_OHM
    denominator = HCSR04_ECHO_SERIES_RESISTOR_OHM + HCSR04_ECHO_PULLDOWN_RESISTOR_OHM
    return (numerator + denominator // 2) // denominator


def echo_pulse_us_to_distance_mm(echo_pulse_us: int) -> int:
    if echo_pulse_us <= 0:
        raise Hcsr04BringupError("echo pulse must be positive for a valid measurement")
    if echo_pulse_us >= HCSR04_ECHO_TIMEOUT_US:
        raise Hcsr04BringupError("echo pulse width is at or beyond the timeout boundary")
    return (echo_pulse_us * 343 + 1000) // 2000


def pulse_width_us(rising_edge_us: int, falling_edge_us: int, *, timer_modulus_us: int = 65_536) -> int:
    if timer_modulus_us <= 0:
        raise Hcsr04BringupError("timer_modulus_us must be positive")
    return (falling_edge_us - rising_edge_us) % timer_modulus_us


def validate_pulse_width_us(echo_pulse_us: int) -> None:
    if echo_pulse_us <= 0:
        raise Hcsr04BringupError("pulse 0 us is invalid and must not become a normal measurement")
    if echo_pulse_us >= HCSR04_ECHO_TIMEOUT_US:
        raise Hcsr04BringupError("pulse width reaches the timeout boundary")


def format_identity_telemetry(*, sequence: int, timestamp_ms: int) -> str:
    payload: dict[str, Any] = {
        "sensor": HCSR04_SENSOR_NAME,
        "connector": HCSR04_CONNECTOR,
        "connector_part": HCSR04_CONNECTOR_PART,
        "connector_pin_order": [
            {"pin": pin, "signal": signal} for pin, signal in HCSR04_CONNECTOR_PIN_ORDER
        ],
        "trigger_pin": HCSR04_TRIGGER_MCU_PIN,
        "trigger_mode": HCSR04_TRIGGER_MODE,
        "echo_pin": HCSR04_ECHO_MCU_PIN,
        "echo_mode": HCSR04_ECHO_MODE,
        "timer": HCSR04_TIMER,
        "timer_prescaler": HCSR04_TIMER_PRESCALER,
        "timer_period": HCSR04_TIMER_PERIOD,
        "timer_tick_hz": HCSR04_TIMER_TICK_HZ,
        "trigger_pulse_us": HCSR04_TRIGGER_PULSE_US,
        "echo_timeout_us": HCSR04_ECHO_TIMEOUT_US,
        "measurement_period_ms": HCSR04_MEASUREMENT_PERIOD_MS,
        "distance_unit": HCSR04_DISTANCE_UNIT,
        "distance_model": HCSR04_DISTANCE_MODEL,
        "echo_protection": {
            "direct_echo_to_cn6_pin4": "prohibited",
            "series_resistor_ohm": HCSR04_ECHO_SERIES_RESISTOR_OHM,
            "pulldown_resistor_ohm": HCSR04_ECHO_PULLDOWN_RESISTOR_OHM,
            "tolerance_percent_or_better": HCSR04_ECHO_DIVIDER_TOLERANCE_PERCENT,
        },
    }
    return _json_line(sequence, timestamp_ms, "sensor_identity", "ok", payload)


def format_measurement_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    measurement: Hcsr04Measurement,
) -> str:
    validate_pulse_width_us(measurement.echo_pulse_us)
    return _json_line(
        sequence,
        timestamp_ms,
        "ultrasonic",
        "ok",
        {
            "echo_pulse_us": measurement.echo_pulse_us,
            "distance_mm": measurement.distance_mm,
            "distance_model": HCSR04_DISTANCE_MODEL,
        },
    )


def format_error_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    error: Hcsr04ErrorRecord,
) -> str:
    if error.code not in HCSR04_ERROR_CODES:
        raise Hcsr04BringupError(f"unknown HC-SR04 error code: {error.code}")
    payload: dict[str, Any] = {
        "echo_pulse_us": None,
        "distance_mm": None,
        "distance_model": HCSR04_DISTANCE_MODEL,
    }
    error_payload: dict[str, Any] = {
        "code": error.code,
        "operation": error.operation,
    }
    if error.timeout_us is not None:
        error_payload["timeout_us"] = error.timeout_us
    return _json_line(
        sequence,
        timestamp_ms,
        "ultrasonic",
        "error",
        payload,
        error=error_payload,
    )


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
        raise Hcsr04BringupError("sequence and timestamp_ms must be non-negative")
    record: dict[str, Any] = {
        "protocol": HCSR04_BRINGUP_PROTOCOL,
        "version": HCSR04_BRINGUP_VERSION,
        "sequence": sequence,
        "timestamp_ms": timestamp_ms,
        "message_type": message_type,
        "sensor_id": HCSR04_SENSOR_ID,
        "status": status,
        "payload": payload,
    }
    if error is not None:
        record["error"] = error
    return json.dumps(record, allow_nan=False, separators=(",", ":"), sort_keys=True) + "\n"
