"""Host-testable OpenRF1 BMP280 bring-up helpers for Phase 3.2C."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from .openrf1_phase32b import Bmp280Calibration, Bmp280CompensatedSample, Bmp280RawSample


BMP280_SENSOR_ID = "bmp280_1"
BMP280_ADDRESS_7BIT = 0x76
BMP280_EXPECTED_CHIP_ID = 0x58
BMP280_REG_CHIP_ID = 0xD0
BMP280_REG_CTRL_MEAS = 0xF4
BMP280_REG_CONFIG = 0xF5
BMP280_CTRL_MEAS_TEMP_X1_PRESS_X1_NORMAL = 0x27
BMP280_CONFIG_STANDBY_500_MS_FILTER_OFF = 0x80
BMP280_SAMPLE_PERIOD_MS = 500
BMP280_BRINGUP_PROTOCOL = "mars_scout_stm32_sensor_telemetry"
BMP280_BRINGUP_VERSION = 1


class Bmp280BringupError(ValueError):
    """Raised for invalid BMP280 bring-up inputs."""


@dataclass(frozen=True, slots=True)
class Bmp280RegisterConfig:
    ctrl_meas: int = BMP280_CTRL_MEAS_TEMP_X1_PRESS_X1_NORMAL
    config: int = BMP280_CONFIG_STANDBY_500_MS_FILTER_OFF


def validate_chip_id(chip_id: int) -> None:
    if chip_id != BMP280_EXPECTED_CHIP_ID:
        raise Bmp280BringupError(f"expected BMP280 chip id 0x58, got 0x{chip_id:02X}")


def parse_calibration_registers(raw: bytes) -> Bmp280Calibration:
    if len(raw) != 24:
        raise Bmp280BringupError("BMP280 calibration block must be 24 bytes")
    return Bmp280Calibration(
        dig_t1=_u16_le(raw, 0),
        dig_t2=_s16_le(raw, 2),
        dig_t3=_s16_le(raw, 4),
        dig_p1=_u16_le(raw, 6),
        dig_p2=_s16_le(raw, 8),
        dig_p3=_s16_le(raw, 10),
        dig_p4=_s16_le(raw, 12),
        dig_p5=_s16_le(raw, 14),
        dig_p6=_s16_le(raw, 16),
        dig_p7=_s16_le(raw, 18),
        dig_p8=_s16_le(raw, 20),
        dig_p9=_s16_le(raw, 22),
    )


def decode_raw_sample_registers(raw: bytes) -> Bmp280RawSample:
    if len(raw) != 6:
        raise Bmp280BringupError("BMP280 raw sample block must be 6 bytes")
    adc_pressure = (raw[0] << 12) | (raw[1] << 4) | (raw[2] >> 4)
    adc_temperature = (raw[3] << 12) | (raw[4] << 4) | (raw[5] >> 4)
    return Bmp280RawSample(adc_temperature=adc_temperature, adc_pressure=adc_pressure)


def expected_register_config() -> Bmp280RegisterConfig:
    return Bmp280RegisterConfig()


def format_identity_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    status: str,
    initialization_stage: str,
    chip_id: int | None,
    register_config: Bmp280RegisterConfig | None = None,
) -> str:
    config = register_config or expected_register_config()
    payload: dict[str, Any] = {
        "configured_address": f"0x{BMP280_ADDRESS_7BIT:02X}",
        "expected_chip_id": f"0x{BMP280_EXPECTED_CHIP_ID:02X}",
        "chip_id": None if chip_id is None else f"0x{chip_id:02X}",
        "initialization_stage": initialization_stage,
        "error_code": None if status == "ok" else "sensor_init_failed",
        "ctrl_meas": f"0x{config.ctrl_meas:02X}",
        "config": f"0x{config.config:02X}",
    }
    return _json_line(sequence, timestamp_ms, "sensor_identity", status, payload)


def format_environmental_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    sample: Bmp280CompensatedSample,
) -> str:
    return _json_line(
        sequence,
        timestamp_ms,
        "environmental",
        "ok",
        {
            "temperature_c": sample.temperature_c,
            "pressure_pa": sample.pressure_pa,
        },
    )


def format_error_telemetry(
    *,
    sequence: int,
    timestamp_ms: int,
    status: str,
    initialization_stage: str,
) -> str:
    if status == "ok":
        raise Bmp280BringupError("error telemetry status must not be ok")
    return _json_line(
        sequence,
        timestamp_ms,
        "environmental",
        status,
        {
            "temperature_c": None,
            "pressure_pa": None,
            "initialization_stage": initialization_stage,
            "error_code": status,
        },
    )


def _json_line(
    sequence: int,
    timestamp_ms: int,
    message_type: str,
    status: str,
    payload: dict[str, Any],
) -> str:
    if sequence < 0 or timestamp_ms < 0:
        raise Bmp280BringupError("sequence and timestamp_ms must be non-negative")
    return (
        json.dumps(
            {
                "protocol": BMP280_BRINGUP_PROTOCOL,
                "version": BMP280_BRINGUP_VERSION,
                "sequence": sequence,
                "timestamp_ms": timestamp_ms,
                "message_type": message_type,
                "sensor_id": BMP280_SENSOR_ID,
                "status": status,
                "payload": payload,
            },
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def _u16_le(raw: bytes, offset: int) -> int:
    return raw[offset] | (raw[offset + 1] << 8)


def _s16_le(raw: bytes, offset: int) -> int:
    value = _u16_le(raw, offset)
    return value - 0x10000 if value & 0x8000 else value
