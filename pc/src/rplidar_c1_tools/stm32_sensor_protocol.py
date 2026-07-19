"""Strict JSONL protocol helpers for Phase 3.1 STM32 sensor telemetry."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
import json
import math
from typing import Any

from .stm32_sensor_models import (
    BAROMETER_SENSOR_IDS,
    BODY_MOTION_COMMAND_SENSOR_IDS,
    BODY_TWIST_SENSOR_IDS,
    GROUND_EDGE_SENSOR_IDS,
    HALL_SENSOR_IDS,
    IMU_RAW_SENSOR_IDS,
    ILLUMINANCE_SENSOR_IDS,
    LIDAR_TRANSPORT_STATS_SENSOR_IDS,
    LINK_STATUS_SENSOR_IDS,
    MOTION_CONTROL_SNAPSHOT_SENSOR_IDS,
    MOTION_SAFETY_STATE_SENSOR_IDS,
    MESSAGE_TYPES,
    SENSOR_IDS_BY_MESSAGE_TYPE,
    STM32_TELEMETRY_PROTOCOL,
    STM32_TELEMETRY_VERSION,
    SUBSYSTEM_STATUS_SENSOR_IDS,
    TELEMETRY_STATUSES,
    ULTRASONIC_SENSOR_IDS,
    ODOMETRY_POSE_SENSOR_IDS,
    WHEEL_ANGULAR_VELOCITY_SENSOR_IDS,
    WHEEL_CONTROL_EFFORT_SENSOR_IDS,
    WHEEL_ENCODER_DELTA_SENSOR_IDS,
    WHEEL_SPEED_MEASUREMENT_SENSOR_IDS,
    WHEEL_SPEED_SETPOINT_SENSOR_IDS,
    Stm32TelemetryMessage,
)


class Stm32TelemetryError(ValueError):
    """Base error for STM32 sensor telemetry failures."""


class Stm32TelemetryFormatError(Stm32TelemetryError):
    """Raised for malformed or semantically invalid telemetry."""

    def __init__(self, message: str, *, line_number: int | None = None) -> None:
        self.line_number = line_number
        prefix = f"line {line_number}: " if line_number is not None else ""
        super().__init__(f"{prefix}{message}")


TOP_LEVEL_FIELDS = {
    "protocol",
    "version",
    "sequence",
    "timestamp_ms",
    "message_type",
    "sensor_id",
    "payload",
    "status",
}


def encode_stm32_telemetry_message(message: Stm32TelemetryMessage) -> str:
    """Encode one validated message as one UTF-8 JSONL-compatible line."""
    validate_stm32_telemetry_message(message)
    return json.dumps(
        message.to_json(),
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def parse_stm32_telemetry_line(
    line: str,
    *,
    line_number: int | None = None,
) -> Stm32TelemetryMessage:
    """Parse and validate one telemetry JSON line."""
    if line.strip() == "":
        raise Stm32TelemetryFormatError("blank telemetry line", line_number=line_number)
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise Stm32TelemetryFormatError(
            f"invalid JSON: {exc.msg}",
            line_number=line_number,
        ) from exc
    if not isinstance(payload, dict):
        raise Stm32TelemetryFormatError("telemetry line must be a JSON object", line_number=line_number)
    unknown = sorted(set(payload) - TOP_LEVEL_FIELDS)
    if unknown:
        raise Stm32TelemetryFormatError(
            f"unknown top-level field: {', '.join(unknown)}",
            line_number=line_number,
        )
    missing = sorted(TOP_LEVEL_FIELDS - set(payload))
    if missing:
        raise Stm32TelemetryFormatError(
            f"missing required field: {', '.join(missing)}",
            line_number=line_number,
        )
    message = Stm32TelemetryMessage(
        protocol=_require_string(payload, "protocol", line_number),
        version=_require_int(payload, "version", line_number),
        sequence=_require_int(payload, "sequence", line_number),
        timestamp_ms=_require_int(payload, "timestamp_ms", line_number),
        message_type=_require_string(payload, "message_type", line_number),
        sensor_id=_require_string(payload, "sensor_id", line_number),
        status=_require_string(payload, "status", line_number),
        payload=_require_object(payload, "payload", line_number),
    )
    validate_stm32_telemetry_message(message, line_number=line_number)
    return message


def iter_stm32_telemetry(lines: Iterable[str]) -> Iterator[Stm32TelemetryMessage]:
    """Yield validated telemetry messages while enforcing stream ordering."""
    previous_sequence = -1
    previous_timestamp_ms = 0
    for line_number, line in enumerate(lines, start=1):
        message = parse_stm32_telemetry_line(line, line_number=line_number)
        if message.sequence <= previous_sequence:
            raise Stm32TelemetryFormatError("sequence must increase", line_number=line_number)
        if message.timestamp_ms < previous_timestamp_ms:
            raise Stm32TelemetryFormatError("timestamp_ms must be nondecreasing", line_number=line_number)
        previous_sequence = message.sequence
        previous_timestamp_ms = message.timestamp_ms
        yield message


def validate_stm32_telemetry_message(
    message: Stm32TelemetryMessage,
    *,
    line_number: int | None = None,
) -> None:
    """Validate schema and per-sensor payload semantics."""
    if not isinstance(message, Stm32TelemetryMessage):
        raise Stm32TelemetryFormatError("message must be Stm32TelemetryMessage", line_number=line_number)
    if message.protocol != STM32_TELEMETRY_PROTOCOL:
        raise Stm32TelemetryFormatError("unsupported protocol", line_number=line_number)
    if message.version != STM32_TELEMETRY_VERSION:
        raise Stm32TelemetryFormatError("unsupported version", line_number=line_number)
    _validate_non_negative_int(message.sequence, "sequence", line_number)
    _validate_non_negative_int(message.timestamp_ms, "timestamp_ms", line_number)
    if message.message_type not in MESSAGE_TYPES:
        raise Stm32TelemetryFormatError("unknown message_type", line_number=line_number)
    if message.status not in TELEMETRY_STATUSES:
        raise Stm32TelemetryFormatError("invalid status", line_number=line_number)
    if message.sensor_id not in SENSOR_IDS_BY_MESSAGE_TYPE[message.message_type]:
        raise Stm32TelemetryFormatError("sensor_id does not match message_type", line_number=line_number)
    if not isinstance(message.payload, Mapping):
        raise Stm32TelemetryFormatError("payload must be an object", line_number=line_number)
    _validate_payload(message, line_number)


def _validate_payload(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    if message.message_type == "ultrasonic":
        _validate_ultrasonic(message, line_number)
    elif message.message_type == "ground_edge":
        _validate_ground_edge(message, line_number)
    elif message.message_type == "hall_landmark":
        _validate_hall_landmark(message, line_number)
    elif message.message_type == "illuminance":
        _validate_illuminance(message, line_number)
    elif message.message_type == "barometer":
        _validate_barometer(message, line_number)
    elif message.message_type == "imu_raw":
        _validate_imu_raw(message, line_number)
    elif message.message_type == "subsystem_status":
        _validate_subsystem_status(message, line_number)
    elif message.message_type == "link_status":
        _validate_link_status(message, line_number)
    elif message.message_type == "lidar_transport_stats":
        _validate_lidar_transport_stats(message, line_number)
    elif message.message_type == "wheel_encoder_delta":
        _validate_wheel_encoder_delta(message, line_number)
    elif message.message_type == "wheel_angular_velocity":
        _validate_wheel_angular_velocity(message, line_number)
    elif message.message_type == "body_twist":
        _validate_body_twist(message, line_number)
    elif message.message_type == "odometry_pose":
        _validate_odometry_pose(message, line_number)
    elif message.message_type == "body_motion_command":
        _validate_body_motion_command(message, line_number)
    elif message.message_type == "wheel_speed_setpoint":
        _validate_wheel_speed_setpoint(message, line_number)
    elif message.message_type == "wheel_speed_measurement":
        _validate_wheel_speed_measurement(message, line_number)
    elif message.message_type == "wheel_control_effort":
        _validate_wheel_control_effort(message, line_number)
    elif message.message_type == "motion_safety_state":
        _validate_motion_safety_state(message, line_number)
    elif message.message_type == "motion_control_snapshot":
        _validate_motion_control_snapshot(message, line_number)
    else:
        raise Stm32TelemetryFormatError("unknown message_type", line_number=line_number)


def _validate_ultrasonic(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, ULTRASONIC_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    _require_allowed_fields(payload, {"distance_mm", "raw_echo_us", "valid"}, line_number)
    if "valid" in payload and not isinstance(payload["valid"], bool):
        raise Stm32TelemetryFormatError("payload.valid must be a boolean", line_number=line_number)
    raw_echo_us = payload.get("raw_echo_us")
    if raw_echo_us is not None:
        _validate_non_negative_int(raw_echo_us, "payload.raw_echo_us", line_number)
    distance_present = payload.get("distance_mm") is not None
    if message.status in {"ok", "simulated"}:
        if not distance_present:
            raise Stm32TelemetryFormatError("payload.distance_mm is required", line_number=line_number)
        _validate_non_negative_int(payload["distance_mm"], "payload.distance_mm", line_number)
        if payload.get("valid", True) is not True:
            raise Stm32TelemetryFormatError("valid ultrasonic status requires payload.valid true", line_number=line_number)
    else:
        if distance_present:
            raise Stm32TelemetryFormatError(
                "invalid ultrasonic status must not include a valid distance_mm",
                line_number=line_number,
            )
        if payload.get("valid", False) is not False:
            raise Stm32TelemetryFormatError("invalid ultrasonic status requires payload.valid false", line_number=line_number)


def _validate_ground_edge(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, GROUND_EDGE_SENSOR_IDS, line_number)
    _validate_digital_payload(
        dict(message.payload),
        interpreted_key="interpreted_edge_detected",
        line_number=line_number,
    )


def _validate_hall_landmark(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, HALL_SENSOR_IDS, line_number)
    _validate_digital_payload(
        dict(message.payload),
        interpreted_key="interpreted_landmark_detected",
        line_number=line_number,
    )


def _validate_digital_payload(
    payload: dict[str, Any],
    *,
    interpreted_key: str,
    line_number: int | None,
) -> None:
    _require_allowed_fields(payload, {"raw_state", "polarity_verified", interpreted_key}, line_number)
    raw_state = payload.get("raw_state")
    _validate_non_negative_int(raw_state, "payload.raw_state", line_number)
    if raw_state not in (0, 1):
        raise Stm32TelemetryFormatError("payload.raw_state must be 0 or 1", line_number=line_number)
    polarity_verified = payload.get("polarity_verified")
    if not isinstance(polarity_verified, bool):
        raise Stm32TelemetryFormatError("payload.polarity_verified must be a boolean", line_number=line_number)
    interpreted = payload.get(interpreted_key)
    if not polarity_verified:
        if interpreted is not None:
            raise Stm32TelemetryFormatError(
                f"payload.{interpreted_key} must be null until polarity is verified",
                line_number=line_number,
            )
        return
    if not isinstance(interpreted, bool):
        raise Stm32TelemetryFormatError(
            f"payload.{interpreted_key} must be a boolean when polarity is verified",
            line_number=line_number,
        )


def _validate_illuminance(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, ILLUMINANCE_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    _require_allowed_fields(payload, {"illuminance_lux"}, line_number)
    value = payload.get("illuminance_lux")
    if message.status in {"ok", "simulated"}:
        _validate_non_negative_finite(value, "payload.illuminance_lux", line_number)
    elif value is not None:
        _validate_non_negative_finite(value, "payload.illuminance_lux", line_number)


def _validate_barometer(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, BAROMETER_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    _require_allowed_fields(payload, {"temperature_c", "pressure_pa"}, line_number)
    if message.status in {"ok", "simulated"}:
        _validate_finite(payload.get("temperature_c"), "payload.temperature_c", line_number)
        _validate_positive_finite(payload.get("pressure_pa"), "payload.pressure_pa", line_number)
    else:
        temperature = payload.get("temperature_c")
        pressure = payload.get("pressure_pa")
        if temperature is not None:
            _validate_finite(temperature, "payload.temperature_c", line_number)
        if pressure is not None:
            _validate_positive_finite(pressure, "payload.pressure_pa", line_number)


def _validate_imu_raw(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, IMU_RAW_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    allowed = {
        "accel_x_raw",
        "accel_y_raw",
        "accel_z_raw",
        "gyro_x_raw",
        "gyro_y_raw",
        "gyro_z_raw",
        "temperature_raw",
        "accel_range_g",
        "gyro_range_dps",
        "calibration_state",
    }
    _require_allowed_fields(payload, allowed, line_number)
    for key in (
        "accel_x_raw",
        "accel_y_raw",
        "accel_z_raw",
        "gyro_x_raw",
        "gyro_y_raw",
        "gyro_z_raw",
        "temperature_raw",
    ):
        _validate_signed_int(payload.get(key), f"payload.{key}", line_number)
    accel_range_g = payload.get("accel_range_g")
    if accel_range_g not in (2, 4, 8, 16):
        raise Stm32TelemetryFormatError("payload.accel_range_g must be 2, 4, 8, or 16", line_number=line_number)
    gyro_range_dps = payload.get("gyro_range_dps")
    if gyro_range_dps not in (250, 500, 1000, 2000):
        raise Stm32TelemetryFormatError(
            "payload.gyro_range_dps must be 250, 500, 1000, or 2000",
            line_number=line_number,
        )
    calibration_state = payload.get("calibration_state")
    if not isinstance(calibration_state, str) or not calibration_state:
        raise Stm32TelemetryFormatError("payload.calibration_state must be a non-empty string", line_number=line_number)


def _validate_subsystem_status(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, SUBSYSTEM_STATUS_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    _require_allowed_fields(payload, {"subsystem", "health", "error_count", "detail"}, line_number)
    for key in ("subsystem", "health"):
        value = payload.get(key)
        if not isinstance(value, str) or not value:
            raise Stm32TelemetryFormatError(f"payload.{key} must be a non-empty string", line_number=line_number)
    _validate_non_negative_int(payload.get("error_count"), "payload.error_count", line_number)
    detail = payload.get("detail")
    if detail is not None and not isinstance(detail, str):
        raise Stm32TelemetryFormatError("payload.detail must be a string or null", line_number=line_number)


def _validate_link_status(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, LINK_STATUS_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    allowed = {
        "link_name",
        "healthy",
        "rx_bytes",
        "tx_bytes",
        "malformed_frames",
        "crc_errors",
        "sequence_gaps",
        "last_rx_ms",
    }
    _require_allowed_fields(payload, allowed, line_number)
    if not isinstance(payload.get("link_name"), str) or not payload.get("link_name"):
        raise Stm32TelemetryFormatError("payload.link_name must be a non-empty string", line_number=line_number)
    if not isinstance(payload.get("healthy"), bool):
        raise Stm32TelemetryFormatError("payload.healthy must be a boolean", line_number=line_number)
    for key in ("rx_bytes", "tx_bytes", "malformed_frames", "crc_errors", "sequence_gaps"):
        _validate_non_negative_int(payload.get(key), f"payload.{key}", line_number)
    last_rx_ms = payload.get("last_rx_ms")
    if last_rx_ms is not None:
        _validate_non_negative_int(last_rx_ms, "payload.last_rx_ms", line_number)


def _validate_lidar_transport_stats(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, LIDAR_TRANSPORT_STATS_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    allowed = {
        "rx_bytes",
        "bytes_read",
        "overflow_count",
        "framing_error_count",
        "chunks_forwarded",
        "last_rx_tick_ms",
    }
    _require_allowed_fields(payload, allowed, line_number)
    for key in allowed:
        _validate_non_negative_int(payload.get(key), f"payload.{key}", line_number)


def _validate_wheel_encoder_delta(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(message.sensor_id, WHEEL_ENCODER_DELTA_SENSOR_IDS, line_number)
    payload = dict(message.payload)
    delta_fields = {
        "front_left_raw_count_delta",
        "front_right_raw_count_delta",
        "rear_left_raw_count_delta",
        "rear_right_raw_count_delta",
        "front_left_signed_count_delta",
        "front_right_signed_count_delta",
        "rear_left_signed_count_delta",
        "rear_right_signed_count_delta",
    }
    _require_allowed_fields(payload, {"interval_ms", *delta_fields}, line_number)
    _validate_positive_int(payload.get("interval_ms"), "payload.interval_ms", line_number)
    for key in delta_fields:
        _validate_signed_int(payload.get(key), f"payload.{key}", line_number)


def _validate_wheel_angular_velocity(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(message.sensor_id, WHEEL_ANGULAR_VELOCITY_SENSOR_IDS, line_number)
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    allowed = {
        "front_left_rad_s",
        "front_right_rad_s",
        "rear_left_rad_s",
        "rear_right_rad_s",
    }
    _require_allowed_fields(payload, allowed, line_number)
    for key in allowed:
        _validate_finite(payload.get(key), f"payload.{key}", line_number)


def _validate_body_twist(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, BODY_TWIST_SENSOR_IDS, line_number)
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    allowed = {"vx_m_s", "vy_m_s", "yaw_rate_rad_s"}
    _require_allowed_fields(payload, allowed, line_number)
    for key in allowed:
        _validate_finite(payload.get(key), f"payload.{key}", line_number)


def _validate_odometry_pose(message: Stm32TelemetryMessage, line_number: int | None) -> None:
    _require_sensor_id(message.sensor_id, ODOMETRY_POSE_SENSOR_IDS, line_number)
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    allowed = {"x_m", "y_m", "yaw_rad", "integration_method"}
    _require_allowed_fields(payload, allowed, line_number)
    for key in ("x_m", "y_m", "yaw_rad"):
        _validate_finite(payload.get(key), f"payload.{key}", line_number)
    if payload.get("integration_method") != "se2_constant_twist_exponential":
        raise Stm32TelemetryFormatError(
            "payload.integration_method must identify the Phase 4A SE(2) integrator",
            line_number=line_number,
        )


def _validate_body_motion_command(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(message.sensor_id, BODY_MOTION_COMMAND_SENSOR_IDS, line_number)
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    allowed = {
        "origin",
        "vx_m_s",
        "vy_m_s",
        "yaw_rate_rad_s",
        "command_timestamp_ms",
        "command_id",
        "source",
        "motion_requested",
    }
    _require_allowed_fields(payload, allowed, line_number)
    _require_phase4b_origin(payload, line_number)
    for key in ("vx_m_s", "vy_m_s", "yaw_rate_rad_s"):
        _validate_finite(payload.get(key), f"payload.{key}", line_number)
    _validate_non_negative_int(
        payload.get("command_timestamp_ms"),
        "payload.command_timestamp_ms",
        line_number,
    )
    command_id = payload.get("command_id")
    if command_id is not None and (not isinstance(command_id, str) or not command_id):
        raise Stm32TelemetryFormatError(
            "payload.command_id must be a non-empty string or null",
            line_number=line_number,
        )
    if not isinstance(payload.get("source"), str) or not payload.get("source"):
        raise Stm32TelemetryFormatError(
            "payload.source must be a non-empty string",
            line_number=line_number,
        )
    _validate_bool(payload.get("motion_requested"), "payload.motion_requested", line_number)


def _validate_wheel_speed_setpoint(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(message.sensor_id, WHEEL_SPEED_SETPOINT_SENSOR_IDS, line_number)
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    wheel_fields = {
        f"{stage}_{wheel}_rad_s"
        for stage in ("requested", "desaturated", "acceleration_limited", "applied")
        for wheel in ("front_left", "front_right", "rear_left", "rear_right")
    }
    flag_fields = {
        f"{wheel}_rate_limited"
        for wheel in ("front_left", "front_right", "rear_left", "rear_right")
    }
    allowed = {
        "origin",
        "desaturation_applied",
        "desaturation_scale_factor",
        *wheel_fields,
        *flag_fields,
    }
    _require_allowed_fields(payload, allowed, line_number)
    _require_phase4b_origin(payload, line_number)
    for key in wheel_fields:
        _validate_finite(payload.get(key), f"payload.{key}", line_number)
    _validate_bool(
        payload.get("desaturation_applied"),
        "payload.desaturation_applied",
        line_number,
    )
    scale = payload.get("desaturation_scale_factor")
    _validate_positive_finite(scale, "payload.desaturation_scale_factor", line_number)
    if float(scale) > 1.0:
        raise Stm32TelemetryFormatError(
            "payload.desaturation_scale_factor must not exceed 1",
            line_number=line_number,
        )
    for key in flag_fields:
        _validate_bool(payload.get(key), f"payload.{key}", line_number)


def _validate_wheel_speed_measurement(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(
        message.sensor_id,
        WHEEL_SPEED_MEASUREMENT_SENSOR_IDS,
        line_number,
    )
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    fields = {
        "front_left_rad_s",
        "front_right_rad_s",
        "rear_left_rad_s",
        "rear_right_rad_s",
    }
    _require_allowed_fields(payload, {"origin", *fields}, line_number)
    _require_phase4b_origin(payload, line_number)
    for key in fields:
        _validate_finite(payload.get(key), f"payload.{key}", line_number)


def _validate_wheel_control_effort(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(message.sensor_id, WHEEL_CONTROL_EFFORT_SENSOR_IDS, line_number)
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    fields = {
        "front_left_normalized",
        "front_right_normalized",
        "rear_left_normalized",
        "rear_right_normalized",
    }
    _require_allowed_fields(payload, {"origin", "output_meaning", *fields}, line_number)
    _require_phase4b_origin(payload, line_number)
    for key in fields:
        _validate_finite(payload.get(key), f"payload.{key}", line_number)
    if payload.get("output_meaning") != "dimensionless_mathematical_not_pwm":
        raise Stm32TelemetryFormatError(
            "payload.output_meaning must distinguish effort from PWM",
            line_number=line_number,
        )


def _validate_motion_safety_state(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(message.sensor_id, MOTION_SAFETY_STATE_SENSOR_IDS, line_number)
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    boolean_fields = {
        "permit_motion",
        "forced_stop",
        "command_stale",
        "latched_fault",
        "targets_replaced_with_zero",
    }
    _require_allowed_fields(
        payload,
        {"origin", "stop_reason", "command_age_ms", *boolean_fields},
        line_number,
    )
    _require_phase4b_origin(payload, line_number)
    for key in boolean_fields:
        _validate_bool(payload.get(key), f"payload.{key}", line_number)
    _validate_non_negative_int(
        payload.get("command_age_ms"),
        "payload.command_age_ms",
        line_number,
    )
    stop_reasons = {
        "none",
        "disabled",
        "emergency_stop",
        "stale_command",
        "communication_fault",
        "ground_edge",
        "ultrasonic_obstacle",
        "critical_sensor_invalid",
        "controller_fault",
        "external_stop",
    }
    if payload.get("stop_reason") not in stop_reasons:
        raise Stm32TelemetryFormatError(
            "payload.stop_reason is unsupported",
            line_number=line_number,
        )
    if bool(payload["permit_motion"]) == bool(payload["forced_stop"]):
        raise Stm32TelemetryFormatError(
            "payload permit_motion and forced_stop must be opposites",
            line_number=line_number,
        )


def _validate_motion_control_snapshot(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    _require_sensor_id(
        message.sensor_id,
        MOTION_CONTROL_SNAPSHOT_SENSOR_IDS,
        line_number,
    )
    _require_software_derived_status(message, line_number)
    payload = dict(message.payload)
    wheel_fields = {
        f"{stage}_{wheel}_rad_s"
        for stage in ("requested", "desaturated", "acceleration_limited", "measured")
        for wheel in ("front_left", "front_right", "rear_left", "rear_right")
    }
    finite_fields = {
        "requested_vx_m_s",
        "requested_vy_m_s",
        "requested_yaw_rate_rad_s",
        "front_left_effort_normalized",
        "front_right_effort_normalized",
        "rear_left_effort_normalized",
        "rear_right_effort_normalized",
        "estimated_vx_m_s",
        "estimated_vy_m_s",
        "estimated_yaw_rate_rad_s",
        "synthetic_pose_x_m",
        "synthetic_pose_y_m",
        "synthetic_pose_yaw_rad",
        *wheel_fields,
    }
    _require_allowed_fields(
        payload,
        {"origin", "permit_motion", "stop_reason", *finite_fields},
        line_number,
    )
    _require_phase4b_origin(payload, line_number)
    for key in finite_fields:
        _validate_finite(payload.get(key), f"payload.{key}", line_number)
    _validate_bool(payload.get("permit_motion"), "payload.permit_motion", line_number)
    if not isinstance(payload.get("stop_reason"), str) or not payload.get("stop_reason"):
        raise Stm32TelemetryFormatError(
            "payload.stop_reason must be a non-empty string",
            line_number=line_number,
        )


def _require_phase4b_origin(
    payload: dict[str, Any],
    line_number: int | None,
) -> None:
    if payload.get("origin") != "synthetic_phase4b_motion_control":
        raise Stm32TelemetryFormatError(
            "Phase 4B control telemetry requires explicit synthetic origin",
            line_number=line_number,
        )


def _validate_bool(value: object, name: str, line_number: int | None) -> None:
    if not isinstance(value, bool):
        raise Stm32TelemetryFormatError(
            f"{name} must be a boolean",
            line_number=line_number,
        )


def _require_software_derived_status(
    message: Stm32TelemetryMessage,
    line_number: int | None,
) -> None:
    if message.status != "software_derived":
        raise Stm32TelemetryFormatError(
            "derived motion telemetry requires status software_derived",
            line_number=line_number,
        )


def _require_allowed_fields(
    payload: dict[str, Any],
    allowed: set[str],
    line_number: int | None,
) -> None:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise Stm32TelemetryFormatError(
            f"unknown payload field: {', '.join(unknown)}",
            line_number=line_number,
        )


def _require_sensor_id(sensor_id: str, allowed: tuple[str, ...], line_number: int | None) -> None:
    if sensor_id not in allowed:
        raise Stm32TelemetryFormatError("sensor_id does not match message_type", line_number=line_number)


def _require_string(payload: dict[str, Any], key: str, line_number: int | None) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise Stm32TelemetryFormatError(f"{key} must be a non-empty string", line_number=line_number)
    return value


def _require_int(payload: dict[str, Any], key: str, line_number: int | None) -> int:
    value = payload.get(key)
    _validate_non_negative_int(value, key, line_number)
    return value


def _require_object(payload: dict[str, Any], key: str, line_number: int | None) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise Stm32TelemetryFormatError(f"{key} must be an object", line_number=line_number)
    return value


def _validate_non_negative_int(value: object, name: str, line_number: int | None) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise Stm32TelemetryFormatError(f"{name} must be a non-negative integer", line_number=line_number)


def _validate_positive_int(value: object, name: str, line_number: int | None) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise Stm32TelemetryFormatError(f"{name} must be a positive integer", line_number=line_number)


def _validate_signed_int(value: object, name: str, line_number: int | None) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise Stm32TelemetryFormatError(f"{name} must be an integer", line_number=line_number)


def _validate_finite(value: object, name: str, line_number: int | None) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)):
        raise Stm32TelemetryFormatError(f"{name} must be finite", line_number=line_number)


def _validate_positive_finite(value: object, name: str, line_number: int | None) -> None:
    _validate_finite(value, name, line_number)
    if float(value) <= 0.0:
        raise Stm32TelemetryFormatError(f"{name} must be positive", line_number=line_number)


def _validate_non_negative_finite(value: object, name: str, line_number: int | None) -> None:
    _validate_finite(value, name, line_number)
    if float(value) < 0.0:
        raise Stm32TelemetryFormatError(f"{name} must be non-negative", line_number=line_number)
