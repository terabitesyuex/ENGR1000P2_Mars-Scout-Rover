"""Host-testable OpenRF1 HC-SR04 bring-up helpers for Phase 3.2E."""

from __future__ import annotations

from dataclasses import dataclass
import json
from collections.abc import Iterable, Iterator
from typing import Any

from .stm32_sensor_models import Stm32TelemetryMessage, ULTRASONIC_SENSOR_IDS
from .stm32_sensor_protocol import Stm32TelemetryFormatError, parse_stm32_telemetry_line


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
HCSR04_TELEMETRY_MAX_LINE_BYTES = 512
HCSR04_FIRMWARE_BUFFER_BYTES = HCSR04_TELEMETRY_MAX_LINE_BYTES + 1

HCSR04_ERROR_ECHO_NOT_LOW_BEFORE_TRIGGER = "echo_not_low_before_trigger"
HCSR04_ERROR_ECHO_RISE_TIMEOUT = "echo_rise_timeout"
HCSR04_ERROR_ECHO_FALL_TIMEOUT = "echo_fall_timeout"
HCSR04_ERROR_TIMER_CONFIGURATION_FAILURE = "timer_configuration_failure"
HCSR04_ERROR_TIMER_MEASUREMENT_FAILURE = "timer_measurement_failure"
HCSR04_ERROR_PULSE_WIDTH_OUT_OF_BOUNDS = "pulse_width_out_of_bounds"
HCSR04_ERROR_TELEMETRY_FORMAT_FAILURE = "telemetry_format_failure"
HCSR04_ERROR_INTERNAL_STATE_ERROR = "internal_state_error"
HCSR04_ERROR_CODES = (
    HCSR04_ERROR_ECHO_NOT_LOW_BEFORE_TRIGGER,
    HCSR04_ERROR_ECHO_RISE_TIMEOUT,
    HCSR04_ERROR_ECHO_FALL_TIMEOUT,
    HCSR04_ERROR_TIMER_CONFIGURATION_FAILURE,
    HCSR04_ERROR_TIMER_MEASUREMENT_FAILURE,
    HCSR04_ERROR_PULSE_WIDTH_OUT_OF_BOUNDS,
    HCSR04_ERROR_TELEMETRY_FORMAT_FAILURE,
    HCSR04_ERROR_INTERNAL_STATE_ERROR,
)


class Hcsr04BringupError(ValueError):
    """Raised for invalid HC-SR04 bring-up inputs."""


class Hcsr04WrongSensorError(Stm32TelemetryFormatError):
    """Raised when a valid HC-SR04 frame uses a sensor ID outside the capture scope."""


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
        "trigger_pin": HCSR04_TRIGGER_MCU_PIN,
        "echo_pin": HCSR04_ECHO_MCU_PIN,
        "timer": HCSR04_TIMER,
        "timer_tick_hz": HCSR04_TIMER_TICK_HZ,
        "trigger_pulse_us": HCSR04_TRIGGER_PULSE_US,
        "echo_timeout_us": HCSR04_ECHO_TIMEOUT_US,
        "measurement_period_ms": HCSR04_MEASUREMENT_PERIOD_MS,
        "distance_unit": HCSR04_DISTANCE_UNIT,
        "distance_model": HCSR04_DISTANCE_MODEL,
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
    if not error.operation:
        raise Hcsr04BringupError("error operation must be non-empty")
    if error.timeout_us not in (None, HCSR04_ECHO_TIMEOUT_US):
        raise Hcsr04BringupError("error timeout_us must match the 30000 us contract")
    payload: dict[str, Any] = {
        "echo_pulse_us": None,
        "distance_mm": None,
        "distance_model": HCSR04_DISTANCE_MODEL,
    }
    error_payload: dict[str, Any] = {
        "code": error.code,
        "operation": error.operation,
        "timeout_us": HCSR04_ECHO_TIMEOUT_US if error.timeout_us is None else error.timeout_us,
    }
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


def telemetry_line_bytes(line: str) -> int:
    """Return the encoded line size including newline but excluding C string NUL."""
    try:
        encoded = line.encode("ascii")
    except UnicodeEncodeError as exc:
        raise Hcsr04BringupError("telemetry must be ASCII JSONL") from exc
    if not encoded.endswith(b"\n"):
        raise Hcsr04BringupError("telemetry line must end with newline")
    return len(encoded)


def validate_telemetry_buffer_capacity(line: str, buffer_bytes: int) -> None:
    """Model snprintf exact-fit semantics, including newline and trailing NUL."""
    if buffer_bytes <= 0:
        raise Hcsr04BringupError("buffer_bytes must be positive")
    required = telemetry_line_bytes(line) + 1
    if buffer_bytes < required:
        raise Hcsr04BringupError(
            f"telemetry buffer requires {required} bytes including NUL"
        )


def parse_hcsr04_bringup_line(
    line: str,
    *,
    allowed_sensor_ids: tuple[str, ...] = (HCSR04_SENSOR_ID,),
    line_number: int | None = None,
) -> Stm32TelemetryMessage:
    """Parse a strict HC-SR04 identity, measurement, or error JSONL record."""
    invalid_allowed = sorted(set(allowed_sensor_ids) - set(ULTRASONIC_SENSOR_IDS))
    if not allowed_sensor_ids or invalid_allowed:
        raise Hcsr04BringupError("allowed_sensor_ids must contain only neutral ultrasonic IDs")
    message = parse_stm32_telemetry_line(line, line_number=line_number)
    if message.message_type not in {"sensor_identity", "ultrasonic"}:
        raise Stm32TelemetryFormatError(
            "HC-SR04 stream supports only sensor_identity and ultrasonic messages",
            line_number=line_number,
        )
    if message.sensor_id not in allowed_sensor_ids:
        raise Hcsr04WrongSensorError(
            "sensor_id is outside the selected HC-SR04 capture scope",
            line_number=line_number,
        )
    return message


def iter_hcsr04_bringup_telemetry(
    lines: Iterable[str],
    *,
    allowed_sensor_ids: tuple[str, ...] = (HCSR04_SENSOR_ID,),
) -> Iterator[Stm32TelemetryMessage]:
    """Yield strict HC-SR04 records with increasing sequence and time."""
    previous_sequence = -1
    previous_timestamp_ms = 0
    for line_number, line in enumerate(lines, start=1):
        message = parse_hcsr04_bringup_line(
            line,
            allowed_sensor_ids=allowed_sensor_ids,
            line_number=line_number,
        )
        if message.sequence <= previous_sequence:
            raise Stm32TelemetryFormatError("sequence must increase", line_number=line_number)
        if message.timestamp_ms < previous_timestamp_ms:
            raise Stm32TelemetryFormatError(
                "timestamp_ms must be nondecreasing",
                line_number=line_number,
            )
        previous_sequence = message.sequence
        previous_timestamp_ms = message.timestamp_ms
        yield message
