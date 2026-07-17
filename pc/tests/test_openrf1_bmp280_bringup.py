from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from rplidar_c1_tools.openrf1_bmp280_bringup import (
    BMP280_ADDRESS_7BIT,
    BMP280_CONFIG_STANDBY_500_MS_FILTER_OFF,
    BMP280_CTRL_MEAS_TEMP_X1_PRESS_X1_NORMAL,
    BMP280_EXPECTED_CHIP_ID,
    BMP280_REG_CHIP_ID,
    Bmp280BringupError,
    Bmp280RegisterConfig,
    decode_raw_sample_registers,
    expected_register_config,
    format_environmental_telemetry,
    format_error_telemetry,
    format_identity_telemetry,
    parse_calibration_registers,
    validate_chip_id,
)
from rplidar_c1_tools.openrf1_phase32b import (
    Bmp280CompensatedSample,
    bmp280_compensate,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BRINGUP_ROOT = REPO_ROOT / "firmware" / "openrf1" / "bmp280_bringup"
FULL_ROOT = REPO_ROOT / "firmware" / "openrf1" / "full_hardware"
KEIL_PROJECT = REPO_ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_BMP280_Bringup.uvprojx"


CALIBRATION_BYTES = bytes(
    [
        0x70,
        0x6B,
        0x43,
        0x67,
        0x18,
        0xFC,
        0x7D,
        0x8E,
        0x43,
        0xD6,
        0xD0,
        0x0B,
        0x27,
        0x0B,
        0x8C,
        0x00,
        0xF9,
        0xFF,
        0x8C,
        0x3C,
        0xF8,
        0xC6,
        0x70,
        0x17,
    ]
)


def test_bmp280_chip_id_and_register_config_are_locked():
    validate_chip_id(BMP280_EXPECTED_CHIP_ID)
    with pytest.raises(Bmp280BringupError, match="chip id"):
        validate_chip_id(0x57)

    assert BMP280_ADDRESS_7BIT == 0x76
    assert BMP280_REG_CHIP_ID == 0xD0
    assert expected_register_config() == Bmp280RegisterConfig(ctrl_meas=0x27, config=0x80)
    assert BMP280_CTRL_MEAS_TEMP_X1_PRESS_X1_NORMAL == 0b00100111
    assert BMP280_CONFIG_STANDBY_500_MS_FILTER_OFF == 0b10000000


def test_calibration_and_raw_register_parsing_match_bosch_vector():
    calibration = parse_calibration_registers(CALIBRATION_BYTES)
    raw = decode_raw_sample_registers(bytes([0x65, 0x5A, 0xC0, 0x7E, 0xED, 0x00]))

    assert calibration.dig_t1 == 27504
    assert calibration.dig_t2 == 26435
    assert calibration.dig_t3 == -1000
    assert calibration.dig_p1 == 36477
    assert calibration.dig_p8 == -14600
    assert calibration.dig_p9 == 6000
    assert raw.adc_temperature == 519888
    assert raw.adc_pressure == 415148


def test_compensation_behavior_remains_consistent_for_bmp280_bringup():
    compensated = bmp280_compensate(
        parse_calibration_registers(CALIBRATION_BYTES),
        decode_raw_sample_registers(bytes([0x65, 0x5A, 0xC0, 0x7E, 0xED, 0x00])),
    )

    assert compensated.temperature_c == 25.08
    assert 100650 <= compensated.pressure_pa <= 100656


def test_bringup_telemetry_formats_identity_success_sample_and_errors():
    identity = json.loads(
        format_identity_telemetry(
            sequence=0,
            timestamp_ms=1,
            status="ok",
            initialization_stage="running",
            chip_id=0x58,
        )
    )
    sample = json.loads(
        format_environmental_telemetry(
            sequence=1,
            timestamp_ms=501,
            sample=Bmp280CompensatedSample(temperature_c=25.08, pressure_pa=100653, t_fine=128422),
        )
    )
    error = json.loads(
        format_error_telemetry(
            sequence=2,
            timestamp_ms=1001,
            status="nack",
            initialization_stage="probe_address",
        )
    )

    assert identity["message_type"] == "sensor_identity"
    assert identity["sensor_id"] == "bmp280_1"
    assert identity["payload"]["configured_address"] == "0x76"
    assert identity["payload"]["expected_chip_id"] == "0x58"
    assert identity["payload"]["chip_id"] == "0x58"
    assert identity["payload"]["ctrl_meas"] == "0x27"
    assert identity["payload"]["config"] == "0x80"

    assert sample["message_type"] == "environmental"
    assert sample["status"] == "ok"
    assert sample["payload"]["temperature_c"] == 25.08
    assert sample["payload"]["pressure_pa"] == 100653

    assert error["message_type"] == "environmental"
    assert error["status"] == "nack"
    assert error["payload"]["temperature_c"] is None
    assert error["payload"]["pressure_pa"] is None
    assert error["payload"]["error_code"] == "nack"


def test_firmware_source_tree_is_isolated_to_bmp280_bringup():
    required = {
        "board_config.h",
        "main_bmp280_bringup.c",
        "platform_bmp280_bringup.c",
        "platform_bmp280_bringup.h",
        "telemetry_bmp280_bringup.c",
        "telemetry_bmp280_bringup.h",
    }
    assert required.issubset({path.name for path in BRINGUP_ROOT.iterdir()})

    combined = "\n".join(path.read_text(encoding="utf-8") for path in BRINGUP_ROOT.glob("*.[ch]"))
    for required_snippet in (
        "OPENRF1_BMP280_ADDRESS_7BIT ((uint8_t)0x76u)",
        "OPENRF1_BMP280_SENSOR_ID \"bmp280_1\"",
        "OPENRF1_BMP280_SAMPLE_PERIOD_MS ((uint32_t)500u)",
        "BMP280_BRINGUP_STAGE_PROBE_ADDRESS",
        "bmp280_read_chip_id",
        "bmp280_read_calibration",
        "bmp280_configure_normal_mode",
        "bmp280_compensate",
        'message_type\\":\\"environmental',
    ):
        assert required_snippet in combined

    forbidden = (
        "BH1750",
        "MPU6050",
        "HCSR04",
        "TCRT5000",
        "Hall",
        "RPLIDAR",
        "ESP32",
        "USART2",
        "USART3",
        "motor",
        "encoder",
    )
    for term in forbidden:
        assert term not in combined


def test_shared_bmp280_driver_writes_and_reads_configuration_registers():
    header = (FULL_ROOT / "bmp280.h").read_text(encoding="utf-8")
    source = (FULL_ROOT / "bmp280.c").read_text(encoding="utf-8")

    assert "BMP280_CTRL_MEAS_TEMP_X1_PRESS_X1_NORMAL ((uint8_t)0x27u)" in header
    assert "BMP280_CONFIG_STANDBY_500_MS_FILTER_OFF ((uint8_t)0x80u)" in header
    assert "bmp280_configure_normal_mode" in header
    assert "BMP280_REG_CTRL_MEAS ((uint8_t)0xF4u)" in source
    assert "BMP280_REG_CONFIG ((uint8_t)0xF5u)" in source
    assert "write_register" in source
    assert "bmp280_read_configuration" in source


def test_bmp280_bringup_keil_target_is_isolated_and_has_no_absolute_paths():
    text = KEIL_PROJECT.read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_BMP280_Bringup</TargetName>" in text
    assert r"<OutputDirectory>.\Objects_BMP280_Bringup\</OutputDirectory>" in text
    assert "<OutputName>OpenRF1_BMP280_Bringup</OutputName>" in text
    assert "<CreateHexFile>1</CreateHexFile>" in text
    assert "<uAC6>1</uAC6>" in text
    assert "STM32F10X_HD,USE_STDPERIPH_DRIVER" in text
    assert "..\\bmp280_bringup;..\\full_hardware;..\\app" in text
    assert "C:\\Users" not in text
    assert "OpenRF1_BH1750.hex" not in text
    assert "OpenRF1_FullHardware.hex" not in text

    included_sources = set(re.findall(r"<FileName>([^<]+)</FileName>", text))
    assert included_sources == {
        "bmp280.c",
        "i2c_bus.c",
        "main_bmp280_bringup.c",
        "openrf1_status.c",
        "platform_bmp280_bringup.c",
        "soft_i2c.c",
        "telemetry_bmp280_bringup.c",
    }
