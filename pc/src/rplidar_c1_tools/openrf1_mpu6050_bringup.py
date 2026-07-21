"""Host-testable OpenRF1 MPU6050 bring-up helpers for Phase 3.2D."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
import json
import math
from typing import Any


MPU6050_SENSOR_ID = "mpu6050_1"
MPU6050_ADDRESS_7BIT = 0x68
MPU6050_EXPECTED_WHO_AM_I = 0x68
MPU6050_REG_SMPLRT_DIV = 0x19
MPU6050_REG_CONFIG = 0x1A
MPU6050_REG_GYRO_CONFIG = 0x1B
MPU6050_REG_ACCEL_CONFIG = 0x1C
MPU6050_REG_ACCEL_XOUT_H = 0x3B
MPU6050_REG_PWR_MGMT_1 = 0x6B
MPU6050_REG_WHO_AM_I = 0x75
MPU6050_PWR_MGMT_1_X_GYRO_PLL = 0x01
MPU6050_SMPLRT_DIV_100HZ_DLPF = 0x09
MPU6050_CONFIG_DLPF_44HZ = 0x03
MPU6050_GYRO_CONFIG_250DPS = 0x00
MPU6050_ACCEL_CONFIG_2G = 0x00
MPU6050_ACCEL_RANGE_G = 2
MPU6050_GYRO_RANGE_DPS = 250
MPU6050_ACCEL_LSB_PER_G = 16384
MPU6050_GYRO_LSB_PER_DPS = 131
MPU6050_SAMPLE_PERIOD_MS = 100
MPU6050_BURST_SAMPLE_BYTES = 14
MPU6050_BRINGUP_PROTOCOL = "mars_scout_stm32_sensor_telemetry"
MPU6050_BRINGUP_VERSION = 1
MPU6050_BRINGUP_MESSAGE_TYPES = ("sensor_identity", "imu")
MPU6050_BRINGUP_STATUSES = (
    "ok",
    "nack",
    "timeout",
    "invalid_reading",
    "not_initialized",
    "stale",
    "hardware_fault",
)


class Mpu6050BringupError(ValueError):
    """Raised for invalid MPU6050 bring-up inputs."""


@dataclass(frozen=True, slots=True)
class Mpu6050RegisterConfig:
    pwr_mgmt_1: int = MPU6050_PWR_MGMT_1_X_GYRO_PLL
    smplrt_div: int = MPU6050_SMPLRT_DIV_100HZ_DLPF
    config: int = MPU6050_CONFIG_DLPF_44HZ
    gyro_config: int = MPU6050_GYRO_CONFIG_250DPS
    accel_config: int = MPU6050_ACCEL_CONFIG_2G


@dataclass(frozen=True, slots=True)
class Mpu6050RawSample:
    accel_x_raw: int
    accel_y_raw: int
    accel_z_raw: int
    temperature_raw: int
    gyro_x_raw: int
    gyro_y_raw: int
    gyro_z_raw: int


@dataclass(frozen=True, slots=True)
class Mpu6050ConvertedSample:
    accel_g: dict[str, float]
    gyro_dps: dict[str, float]
    temperature_c: float


def validate_who_am_i(who_am_i: int) -> None:
    if who_am_i != MPU6050_EXPECTED_WHO_AM_I:
        raise Mpu6050BringupError(f"expected MPU6050 WHO_AM_I 0x68, got 0x{who_am_i:02X}")


def expected_register_config() -> Mpu6050RegisterConfig:
    return Mpu6050RegisterConfig()


def initialization_write_sequence() -> tuple[tuple[int, int], ...]:
    return (
        (MPU6050_REG_PWR_MGMT_1, MPU6050_PWR_MGMT_1_X_GYRO_PLL),
        (MPU6050_REG_SMPLRT_DIV, MPU6050_SMPLRT_DIV_100HZ_DLPF),
        (MPU6050_REG_CONFIG, MPU6050_CONFIG_DLPF_44HZ),
        (MPU6050_REG_GYRO_CONFIG, MPU6050_GYRO_CONFIG_250DPS),
        (MPU6050_REG_ACCEL_CONFIG, MPU6050_ACCEL_CONFIG_2G),
    )


def decode_burst_sample(raw: bytes) -> Mpu6050RawSample:
    if len(raw) != MPU6050_BURST_SAMPLE_BYTES:
        raise Mpu6050BringupError("MPU6050 burst sample must be exactly 14 bytes")
    values = [_s16_be(raw[index : index + 2]) for index in range(0, MPU6050_BURST_SAMPLE_BYTES, 2)]
    return Mpu6050RawSample(
        accel_x_raw=values[0],
        accel_y_raw=values[1],
        accel_z_raw=values[2],
        temperature_raw=values[3],
        gyro_x_raw=values[4],
        gyro_y_raw=values[5],
        gyro_z_raw=values[6],
    )


def convert_sample(sample: Mpu6050RawSample) -> Mpu6050ConvertedSample:
    return Mpu6050ConvertedSample(
        accel_g={
            "x": accel_raw_to_g(sample.accel_x_raw),
            "y": accel_raw_to_g(sample.accel_y_raw),
            "z": accel_raw_to_g(sample.accel_z_raw),
        },
        gyro_dps={
            "x": gyro_raw_to_dps(sample.gyro_x_raw),
            "y": gyro_raw_to_dps(sample.gyro_y_raw),
            "z": gyro_raw_to_dps(sample.gyro_z_raw),
        },
        temperature_c=temperature_raw_to_c(sample.temperature_raw),
    )


def accel_raw_to_g(raw: int) -> float:
    return round(raw / MPU6050_ACCEL_LSB_PER_G, 3)


def gyro_raw_to_dps(raw: int) -> float:
    return round(raw / MPU6050_GYRO_LSB_PER_DPS, 3)


def temperature_raw_to_c(raw: int) -> float:
    return round(raw / 340.0 + 36.53, 2)


def format_identity_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    who_am_i: int,
    register_config: Mpu6050RegisterConfig | None = None,
) -> str:
    validate_who_am_i(who_am_i)
    config = register_config or expected_register_config()
    payload: dict[str, Any] = {
        "sensor": "mpu6050",
        "configured_address": f"0x{MPU6050_ADDRESS_7BIT:02X}",
        "expected_who_am_i": f"0x{MPU6050_EXPECTED_WHO_AM_I:02X}",
        "who_am_i": f"0x{who_am_i:02X}",
        "initialization_stage": "running",
        "error_code": None,
        "pwr_mgmt_1": f"0x{config.pwr_mgmt_1:02X}",
        "smplrt_div": f"0x{config.smplrt_div:02X}",
        "config": f"0x{config.config:02X}",
        "gyro_config": f"0x{config.gyro_config:02X}",
        "accel_config": f"0x{config.accel_config:02X}",
        "accel_range_g": MPU6050_ACCEL_RANGE_G,
        "gyro_range_dps": MPU6050_GYRO_RANGE_DPS,
        "telemetry_period_ms": MPU6050_SAMPLE_PERIOD_MS,
    }
    return _json_line(sequence, timestamp_ms, "sensor_identity", "ok", payload)


def format_imu_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    sample: Mpu6050RawSample,
    gyro_bias_dps: Mapping[str, float] | None = None,
) -> str:
    converted = convert_sample(sample)
    gyro_dps = dict(converted.gyro_dps)
    if gyro_bias_dps is not None:
        gyro_dps = {
            axis: round(gyro_dps[axis] - _require_finite_bias(gyro_bias_dps, axis), 3)
            for axis in ("x", "y", "z")
        }
    return _json_line(
        sequence,
        timestamp_ms,
        "imu",
        "ok",
        {
            "accel_raw": {
                "x": sample.accel_x_raw,
                "y": sample.accel_y_raw,
                "z": sample.accel_z_raw,
            },
            "gyro_raw": {
                "x": sample.gyro_x_raw,
                "y": sample.gyro_y_raw,
                "z": sample.gyro_z_raw,
            },
            "temperature_raw": sample.temperature_raw,
            "accel_g": converted.accel_g,
            "gyro_dps": gyro_dps,
            "temperature_c": converted.temperature_c,
        },
    )


def format_error_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    status: str,
    initialization_stage: str,
    operation: str,
    register: int | None,
) -> str:
    if status == "ok":
        raise Mpu6050BringupError("error telemetry status must not be ok")
    payload: dict[str, Any] = {
        "accel_raw": None,
        "gyro_raw": None,
        "temperature_raw": None,
        "accel_g": None,
        "gyro_dps": None,
        "temperature_c": None,
        "initialization_stage": initialization_stage,
        "operation": operation,
        "register": None if register is None else f"0x{register:02X}",
        "error_code": status,
    }
    return _json_line(sequence, timestamp_ms, "imu", status, payload)


def parse_mpu6050_bringup_line(
    line: str,
    *,
    line_number: int | None = None,
) -> dict[str, Any]:
    """Parse and validate one isolated Phase 3.2D MPU6050 JSONL line."""
    if line.strip() == "":
        raise Mpu6050BringupError(_with_line("blank telemetry line", line_number))
    try:
        message = json.loads(line)
    except json.JSONDecodeError as exc:
        raise Mpu6050BringupError(_with_line(f"invalid JSON: {exc.msg}", line_number)) from exc
    if not isinstance(message, dict):
        raise Mpu6050BringupError(_with_line("telemetry line must be a JSON object", line_number))
    required = {
        "protocol",
        "version",
        "sequence",
        "timestamp_ms",
        "message_type",
        "sensor_id",
        "status",
        "payload",
    }
    unknown = sorted(set(message) - required)
    if unknown:
        raise Mpu6050BringupError(_with_line("unknown top-level field: " + ", ".join(unknown), line_number))
    missing = sorted(required - set(message))
    if missing:
        raise Mpu6050BringupError(_with_line("missing required field: " + ", ".join(missing), line_number))
    if message["protocol"] != MPU6050_BRINGUP_PROTOCOL:
        raise Mpu6050BringupError(_with_line("unsupported protocol", line_number))
    if message["version"] != MPU6050_BRINGUP_VERSION:
        raise Mpu6050BringupError(_with_line("unsupported version", line_number))
    _require_non_negative_int(message["sequence"], "sequence")
    _require_non_negative_int(message["timestamp_ms"], "timestamp_ms")
    if message["message_type"] not in MPU6050_BRINGUP_MESSAGE_TYPES:
        raise Mpu6050BringupError(_with_line("unsupported message_type", line_number))
    if message["sensor_id"] != MPU6050_SENSOR_ID:
        raise Mpu6050BringupError(_with_line("sensor_id must be mpu6050_1", line_number))
    if message["status"] not in MPU6050_BRINGUP_STATUSES:
        raise Mpu6050BringupError(_with_line("unsupported status", line_number))
    if not isinstance(message["payload"], dict):
        raise Mpu6050BringupError(_with_line("payload must be an object", line_number))
    if message["message_type"] == "sensor_identity":
        _validate_identity_payload(message["payload"], message["status"], line_number)
    else:
        _validate_imu_payload(message["payload"], message["status"], line_number)
    return message


def iter_mpu6050_bringup_telemetry(lines: Iterable[str]) -> Iterator[dict[str, Any]]:
    """Yield validated MPU6050 bring-up messages with contiguous sequencing."""
    previous_sequence: int | None = None
    previous_timestamp_ms = 0
    for line_number, line in enumerate(lines, start=1):
        message = parse_mpu6050_bringup_line(line, line_number=line_number)
        sequence = int(message["sequence"])
        timestamp_ms = int(message["timestamp_ms"])
        if previous_sequence is not None and sequence != previous_sequence + 1:
            raise Mpu6050BringupError(_with_line("sequence must increase by exactly 1", line_number))
        if timestamp_ms < previous_timestamp_ms:
            raise Mpu6050BringupError(_with_line("timestamp_ms must be nondecreasing", line_number))
        previous_sequence = sequence
        previous_timestamp_ms = timestamp_ms
        yield message


def _json_line(
    sequence: int,
    timestamp_ms: int,
    message_type: str,
    status: str,
    payload: dict[str, Any],
) -> str:
    if sequence < 0 or timestamp_ms < 0:
        raise Mpu6050BringupError("sequence and timestamp_ms must be non-negative")
    return (
        json.dumps(
            {
                "protocol": MPU6050_BRINGUP_PROTOCOL,
                "version": MPU6050_BRINGUP_VERSION,
                "sequence": sequence,
                "timestamp_ms": timestamp_ms,
                "message_type": message_type,
                "sensor_id": MPU6050_SENSOR_ID,
                "status": status,
                "payload": payload,
            },
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def _validate_identity_payload(
    payload: dict[str, Any],
    status: str,
    line_number: int | None,
) -> None:
    if status != "ok":
        raise Mpu6050BringupError(_with_line("sensor_identity status must be ok", line_number))
    required = {
        "sensor",
        "configured_address",
        "expected_who_am_i",
        "who_am_i",
        "initialization_stage",
        "error_code",
        "pwr_mgmt_1",
        "smplrt_div",
        "config",
        "gyro_config",
        "accel_config",
        "accel_range_g",
        "gyro_range_dps",
        "telemetry_period_ms",
    }
    _require_exact_payload_fields(payload, required, line_number)
    expected_values = {
        "sensor": "mpu6050",
        "configured_address": "0x68",
        "expected_who_am_i": "0x68",
        "who_am_i": "0x68",
        "pwr_mgmt_1": "0x01",
        "smplrt_div": "0x09",
        "config": "0x03",
        "gyro_config": "0x00",
        "accel_config": "0x00",
        "accel_range_g": MPU6050_ACCEL_RANGE_G,
        "gyro_range_dps": MPU6050_GYRO_RANGE_DPS,
        "telemetry_period_ms": MPU6050_SAMPLE_PERIOD_MS,
    }
    for key, value in expected_values.items():
        if payload.get(key) != value:
            raise Mpu6050BringupError(_with_line(f"payload.{key} is invalid", line_number))
    if payload.get("error_code") is not None:
        raise Mpu6050BringupError(_with_line("payload.error_code must be null for identity ok", line_number))
    if not isinstance(payload.get("initialization_stage"), str) or not payload["initialization_stage"]:
        raise Mpu6050BringupError(_with_line("payload.initialization_stage must be a non-empty string", line_number))


def _validate_imu_payload(
    payload: dict[str, Any],
    status: str,
    line_number: int | None,
) -> None:
    measurement_fields = {
        "accel_raw",
        "gyro_raw",
        "temperature_raw",
        "accel_g",
        "gyro_dps",
        "temperature_c",
    }
    if status == "ok":
        _require_exact_payload_fields(payload, measurement_fields, line_number)
        _validate_axis_object(payload["accel_raw"], "payload.accel_raw", int, line_number)
        _validate_axis_object(payload["gyro_raw"], "payload.gyro_raw", int, line_number)
        _require_int(payload["temperature_raw"], "payload.temperature_raw")
        _validate_axis_object(payload["accel_g"], "payload.accel_g", float, line_number)
        _validate_axis_object(payload["gyro_dps"], "payload.gyro_dps", float, line_number)
        _require_finite_number(payload["temperature_c"], "payload.temperature_c")
        return

    required = {
        *measurement_fields,
        "initialization_stage",
        "operation",
        "register",
        "error_code",
    }
    _require_exact_payload_fields(payload, required, line_number)
    for key in measurement_fields:
        if payload.get(key) is not None:
            raise Mpu6050BringupError(_with_line(f"payload.{key} must be null for error telemetry", line_number))
    for key in ("initialization_stage", "operation", "error_code"):
        if not isinstance(payload.get(key), str) or not payload[key]:
            raise Mpu6050BringupError(_with_line(f"payload.{key} must be a non-empty string", line_number))
    register = payload.get("register")
    if register is not None and (not isinstance(register, str) or not register.startswith("0x")):
        raise Mpu6050BringupError(_with_line("payload.register must be null or a hex string", line_number))


def _require_exact_payload_fields(
    payload: dict[str, Any],
    required: set[str],
    line_number: int | None,
) -> None:
    unknown = sorted(set(payload) - required)
    if unknown:
        raise Mpu6050BringupError(_with_line("unknown payload field: " + ", ".join(unknown), line_number))
    missing = sorted(required - set(payload))
    if missing:
        raise Mpu6050BringupError(_with_line("missing payload field: " + ", ".join(missing), line_number))


def _validate_axis_object(
    value: object,
    name: str,
    numeric_type: type,
    line_number: int | None,
) -> None:
    if not isinstance(value, dict):
        raise Mpu6050BringupError(_with_line(f"{name} must be an object", line_number))
    _require_exact_payload_fields(value, {"x", "y", "z"}, line_number)
    for axis in ("x", "y", "z"):
        if numeric_type is int:
            _require_int(value[axis], f"{name}.{axis}")
        else:
            _require_finite_number(value[axis], f"{name}.{axis}")


def _require_finite_bias(values: Mapping[str, float], axis: str) -> float:
    if axis not in values:
        raise Mpu6050BringupError(f"gyro_bias_dps.{axis} is required")
    value = values[axis]
    _require_finite_number(value, f"gyro_bias_dps.{axis}")
    return float(value)


def _require_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise Mpu6050BringupError(f"{name} must be an integer")


def _require_non_negative_int(value: object, name: str) -> None:
    _require_int(value, name)
    if int(value) < 0:
        raise Mpu6050BringupError(f"{name} must be non-negative")


def _require_finite_number(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)):
        raise Mpu6050BringupError(f"{name} must be finite")


def _with_line(message: str, line_number: int | None) -> str:
    return f"line {line_number}: {message}" if line_number is not None else message


def _s16_be(raw: bytes) -> int:
    if len(raw) != 2:
        raise Mpu6050BringupError("signed 16-bit value must contain exactly 2 bytes")
    return int.from_bytes(raw, byteorder="big", signed=True)
