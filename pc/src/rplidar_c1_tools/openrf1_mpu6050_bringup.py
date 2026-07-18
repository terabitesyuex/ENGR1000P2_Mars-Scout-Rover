"""Host-testable OpenRF1 MPU6050 bring-up helpers for Phase 3.2D."""

from __future__ import annotations

from dataclasses import dataclass
import json
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
) -> str:
    converted = convert_sample(sample)
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
            "gyro_dps": converted.gyro_dps,
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


def _s16_be(raw: bytes) -> int:
    if len(raw) != 2:
        raise Mpu6050BringupError("signed 16-bit value must contain exactly 2 bytes")
    return int.from_bytes(raw, byteorder="big", signed=True)
