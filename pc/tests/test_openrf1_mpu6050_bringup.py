from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from rplidar_c1_tools.openrf1_mpu6050_bringup import (
    MPU6050_ACCEL_CONFIG_2G,
    MPU6050_ADDRESS_7BIT,
    MPU6050_CONFIG_DLPF_44HZ,
    MPU6050_EXPECTED_WHO_AM_I,
    MPU6050_GYRO_CONFIG_250DPS,
    MPU6050_PWR_MGMT_1_X_GYRO_PLL,
    MPU6050_REG_ACCEL_CONFIG,
    MPU6050_REG_ACCEL_XOUT_H,
    MPU6050_REG_CONFIG,
    MPU6050_REG_GYRO_CONFIG,
    MPU6050_REG_PWR_MGMT_1,
    MPU6050_REG_SMPLRT_DIV,
    MPU6050_REG_WHO_AM_I,
    MPU6050_SAMPLE_PERIOD_MS,
    MPU6050_SMPLRT_DIV_100HZ_DLPF,
    Mpu6050BringupError,
    Mpu6050RawSample,
    accel_raw_to_g,
    convert_sample,
    decode_burst_sample,
    expected_register_config,
    format_error_telemetry,
    format_identity_telemetry,
    format_imu_telemetry,
    gyro_raw_to_dps,
    initialization_write_sequence,
    iter_mpu6050_bringup_telemetry,
    parse_mpu6050_bringup_line,
    temperature_raw_to_c,
    validate_who_am_i,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BRINGUP_ROOT = REPO_ROOT / "firmware" / "openrf1" / "mpu6050_bringup"
FULL_ROOT = REPO_ROOT / "firmware" / "openrf1" / "full_hardware"
KEIL_PROJECT = REPO_ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_MPU6050_Bringup.uvprojx"
FIXTURE_ROOT = REPO_ROOT / "data" / "test_vectors" / "phase3.2d"


def test_mpu6050_registers_configuration_and_address_are_locked():
    validate_who_am_i(MPU6050_EXPECTED_WHO_AM_I)
    with pytest.raises(Mpu6050BringupError, match="WHO_AM_I"):
        validate_who_am_i(0x69)

    assert MPU6050_ADDRESS_7BIT == 0x68
    assert MPU6050_REG_SMPLRT_DIV == 0x19
    assert MPU6050_REG_CONFIG == 0x1A
    assert MPU6050_REG_GYRO_CONFIG == 0x1B
    assert MPU6050_REG_ACCEL_CONFIG == 0x1C
    assert MPU6050_REG_ACCEL_XOUT_H == 0x3B
    assert MPU6050_REG_PWR_MGMT_1 == 0x6B
    assert MPU6050_REG_WHO_AM_I == 0x75
    assert expected_register_config().pwr_mgmt_1 == 0x01
    assert expected_register_config().smplrt_div == 0x09
    assert expected_register_config().config == 0x03
    assert expected_register_config().gyro_config == 0x00
    assert expected_register_config().accel_config == 0x00
    assert initialization_write_sequence() == (
        (MPU6050_REG_PWR_MGMT_1, MPU6050_PWR_MGMT_1_X_GYRO_PLL),
        (MPU6050_REG_SMPLRT_DIV, MPU6050_SMPLRT_DIV_100HZ_DLPF),
        (MPU6050_REG_CONFIG, MPU6050_CONFIG_DLPF_44HZ),
        (MPU6050_REG_GYRO_CONFIG, MPU6050_GYRO_CONFIG_250DPS),
        (MPU6050_REG_ACCEL_CONFIG, MPU6050_ACCEL_CONFIG_2G),
    )
    assert MPU6050_SAMPLE_PERIOD_MS == 100


def test_signed_big_endian_burst_decode_and_conversions():
    burst = bytes(
        [
            0x40,
            0x00,
            0xC0,
            0x00,
            0x00,
            0x00,
            0x01,
            0x54,
            0x00,
            0x83,
            0xFF,
            0x7D,
            0x80,
            0x00,
        ]
    )
    sample = decode_burst_sample(burst)

    assert sample == Mpu6050RawSample(
        accel_x_raw=16384,
        accel_y_raw=-16384,
        accel_z_raw=0,
        temperature_raw=340,
        gyro_x_raw=131,
        gyro_y_raw=-131,
        gyro_z_raw=-32768,
    )
    assert accel_raw_to_g(16384) == 1.0
    assert accel_raw_to_g(-16384) == -1.0
    assert gyro_raw_to_dps(131) == 1.0
    assert gyro_raw_to_dps(-131) == -1.0
    assert temperature_raw_to_c(0) == 36.53
    assert temperature_raw_to_c(340) == 37.53
    assert temperature_raw_to_c(-340) == 35.53

    converted = convert_sample(sample)
    assert converted.accel_g == {"x": 1.0, "y": -1.0, "z": 0.0}
    assert converted.gyro_dps["x"] == 1.0
    assert converted.gyro_dps["y"] == -1.0
    assert converted.temperature_c == 37.53


def test_burst_decode_rejects_incomplete_transactions():
    with pytest.raises(Mpu6050BringupError, match="14 bytes"):
        decode_burst_sample(bytes(13))


def test_mpu6050_telemetry_formats_identity_measurement_and_errors():
    identity = json.loads(format_identity_telemetry(sequence=0, timestamp_ms=10, who_am_i=0x68))
    sample = Mpu6050RawSample(
        accel_x_raw=16384,
        accel_y_raw=-16384,
        accel_z_raw=0,
        temperature_raw=-340,
        gyro_x_raw=131,
        gyro_y_raw=-131,
        gyro_z_raw=0,
    )
    measurement = json.loads(format_imu_telemetry(sequence=1, timestamp_ms=110, sample=sample))
    error = json.loads(
        format_error_telemetry(
            sequence=2,
            timestamp_ms=210,
            status="nack",
            initialization_stage="read_who_am_i",
            operation="read_who_am_i",
            register=0x75,
        )
    )

    assert identity["message_type"] == "sensor_identity"
    assert identity["sensor_id"] == "mpu6050_1"
    assert identity["status"] == "ok"
    assert identity["payload"]["sensor"] == "mpu6050"
    assert identity["payload"]["configured_address"] == "0x68"
    assert identity["payload"]["expected_who_am_i"] == "0x68"
    assert identity["payload"]["who_am_i"] == "0x68"
    assert identity["payload"]["pwr_mgmt_1"] == "0x01"
    assert identity["payload"]["smplrt_div"] == "0x09"
    assert identity["payload"]["config"] == "0x03"
    assert identity["payload"]["gyro_config"] == "0x00"
    assert identity["payload"]["accel_config"] == "0x00"
    assert identity["payload"]["accel_range_g"] == 2
    assert identity["payload"]["gyro_range_dps"] == 250
    assert identity["payload"]["telemetry_period_ms"] == 100

    assert measurement["message_type"] == "imu"
    assert measurement["status"] == "ok"
    assert measurement["payload"]["accel_raw"] == {"x": 16384, "y": -16384, "z": 0}
    assert measurement["payload"]["gyro_raw"] == {"x": 131, "y": -131, "z": 0}
    assert measurement["payload"]["temperature_raw"] == -340
    assert measurement["payload"]["accel_g"] == {"x": 1.0, "y": -1.0, "z": 0.0}
    assert measurement["payload"]["gyro_dps"] == {"x": 1.0, "y": -1.0, "z": 0.0}
    assert measurement["payload"]["temperature_c"] == 35.53

    assert error["message_type"] == "imu"
    assert error["status"] == "nack"
    assert error["payload"]["accel_raw"] is None
    assert error["payload"]["gyro_raw"] is None
    assert error["payload"]["temperature_raw"] is None
    assert error["payload"]["accel_g"] is None
    assert error["payload"]["gyro_dps"] is None
    assert error["payload"]["temperature_c"] is None
    assert error["payload"]["operation"] == "read_who_am_i"
    assert error["payload"]["register"] == "0x75"
    assert error["payload"]["error_code"] == "nack"


def test_gyro_bias_changes_only_scaled_gyro_dps():
    sample = Mpu6050RawSample(
        accel_x_raw=0,
        accel_y_raw=0,
        accel_z_raw=16384,
        temperature_raw=0,
        gyro_x_raw=262,
        gyro_y_raw=-262,
        gyro_z_raw=131,
    )

    measurement = json.loads(
        format_imu_telemetry(
            sequence=1,
            timestamp_ms=10100,
            sample=sample,
            gyro_bias_dps={"x": 0.5, "y": -0.25, "z": 0.125},
        )
    )

    assert measurement["payload"]["gyro_raw"] == {"x": 262, "y": -262, "z": 131}
    assert measurement["payload"]["gyro_dps"] == {"x": 1.5, "y": -1.75, "z": 0.875}
    assert measurement["payload"]["accel_raw"] == {"x": 0, "y": 0, "z": 16384}
    assert measurement["payload"]["accel_g"] == {"x": 0.0, "y": 0.0, "z": 1.0}


def test_mpu6050_fixture_stream_covers_startup_grace_and_100ms_period():
    lines = (FIXTURE_ROOT / "mpu6050_startup_grace_session.jsonl").read_text(encoding="utf-8").splitlines()
    messages = list(iter_mpu6050_bringup_telemetry(lines))

    assert [message["message_type"] for message in messages] == ["sensor_identity", "imu", "imu"]
    assert messages[0]["sensor_id"] == "mpu6050_1"
    assert messages[0]["timestamp_ms"] == 10_000
    assert [messages[index + 1]["timestamp_ms"] - messages[index]["timestamp_ms"] for index in (0, 1)] == [100, 100]
    assert messages[1]["payload"]["accel_raw"] == {"x": 0, "y": 0, "z": 16384}
    assert messages[1]["payload"]["accel_g"] == {"x": 0.0, "y": 0.0, "z": 1.0}
    assert messages[1]["payload"]["gyro_raw"] == {"x": 262, "y": -262, "z": 131}
    assert messages[1]["payload"]["gyro_dps"] == {"x": 1.5, "y": -1.75, "z": 0.875}
    assert messages[1]["payload"]["temperature_raw"] == 0
    assert messages[1]["payload"]["temperature_c"] == 36.53


def test_mpu6050_error_fixture_preserves_null_measurements():
    [message] = list(
        iter_mpu6050_bringup_telemetry(
            (FIXTURE_ROOT / "mpu6050_error_session.jsonl").read_text(encoding="utf-8").splitlines()
        )
    )

    assert message["message_type"] == "imu"
    assert message["status"] == "nack"
    assert message["payload"]["operation"] == "read_who_am_i"
    for key in ("accel_raw", "accel_g", "gyro_raw", "gyro_dps", "temperature_raw", "temperature_c"):
        assert message["payload"][key] is None


def test_mpu6050_parser_rejects_malformed_wrong_sensor_gap_and_backwards_time():
    valid = format_identity_telemetry(sequence=0, timestamp_ms=0, who_am_i=0x68)
    with pytest.raises(Mpu6050BringupError, match="invalid JSON"):
        parse_mpu6050_bringup_line("not-json")
    with pytest.raises(Mpu6050BringupError, match="sensor_id"):
        parse_mpu6050_bringup_line(valid.replace('"mpu6050_1"', '"bh1750_1"'))
    with pytest.raises(Mpu6050BringupError, match="sequence"):
        list(
            iter_mpu6050_bringup_telemetry(
                [
                    valid,
                    format_imu_telemetry(
                        sequence=2,
                        timestamp_ms=100,
                        sample=Mpu6050RawSample(0, 0, 16384, 0, 0, 0, 0),
                    ),
                ]
            )
        )
    with pytest.raises(Mpu6050BringupError, match="timestamp_ms"):
        list(
            iter_mpu6050_bringup_telemetry(
                [
                    valid.replace('"timestamp_ms":0', '"timestamp_ms":100'),
                    format_imu_telemetry(
                        sequence=1,
                        timestamp_ms=99,
                        sample=Mpu6050RawSample(0, 0, 16384, 0, 0, 0, 0),
                    ),
                ]
            )
        )


def test_mpu6050_parser_resets_ordering_for_new_session():
    first = list(
        iter_mpu6050_bringup_telemetry(
            [
                format_identity_telemetry(sequence=7, timestamp_ms=10_000, who_am_i=0x68),
            ]
        )
    )
    second = list(
        iter_mpu6050_bringup_telemetry(
            [
                format_identity_telemetry(sequence=0, timestamp_ms=0, who_am_i=0x68),
            ]
        )
    )

    assert first[0]["sequence"] == 7
    assert second[0]["sequence"] == 0


def test_mpu6050_jsonl_output_has_no_nonfinite_or_startup_prose():
    line = format_imu_telemetry(
        sequence=3,
        timestamp_ms=300,
        sample=Mpu6050RawSample(1, -1, 0, 0, 1, -1, 0),
    )

    assert line.endswith("\n")
    assert "NaN" not in line
    assert "Infinity" not in line
    assert line.startswith("{")
    assert json.loads(line)["sequence"] == 3


def test_firmware_source_tree_is_isolated_to_mpu6050_bringup():
    required = {
        "board_config.h",
        "main_mpu6050_bringup.c",
        "platform_mpu6050_bringup.c",
        "platform_mpu6050_bringup.h",
        "telemetry_mpu6050_bringup.c",
        "telemetry_mpu6050_bringup.h",
    }
    assert required.issubset({path.name for path in BRINGUP_ROOT.iterdir()})

    combined = "\n".join(path.read_text(encoding="utf-8") for path in BRINGUP_ROOT.glob("*.[ch]"))
    for required_snippet in (
        "OPENRF1_MPU6050_ADDRESS_7BIT ((uint8_t)0x68u)",
        "OPENRF1_MPU6050_SENSOR_ID \"mpu6050_1\"",
        "OPENRF1_MPU6050_SAMPLE_PERIOD_MS ((uint32_t)100u)",
        "MPU6050_BRINGUP_STAGE_READ_WHO_AM_I",
        "mpu6050_read_who_am_i",
        "mpu6050_wake_for_bringup",
        "mpu6050_write_register_readback",
        "mpu6050_read_raw_sample",
        'message_type\\":\\"imu',
    ):
        assert required_snippet in combined

    forbidden = (
        "BMP280",
        "BH1750",
        "HCSR04",
        "TCRT5000",
        "Hall",
        "RPLIDAR",
        "ESP32",
        "USART2",
        "USART3",
        "motor",
        "encoder",
        "servo",
    )
    for term in forbidden:
        assert term not in combined


def test_shared_mpu6050_driver_supports_required_bringup_contracts():
    header = (FULL_ROOT / "mpu6050.h").read_text(encoding="utf-8")
    source = (FULL_ROOT / "mpu6050.c").read_text(encoding="utf-8")

    for snippet in (
        "MPU6050_ADDRESS_7BIT ((uint8_t)0x68u)",
        "MPU6050_REG_SMPLRT_DIV ((uint8_t)0x19u)",
        "MPU6050_REG_CONFIG ((uint8_t)0x1Au)",
        "MPU6050_REG_GYRO_CONFIG ((uint8_t)0x1Bu)",
        "MPU6050_REG_ACCEL_CONFIG ((uint8_t)0x1Cu)",
        "MPU6050_REG_ACCEL_XOUT_H ((uint8_t)0x3Bu)",
        "MPU6050_REG_PWR_MGMT_1 ((uint8_t)0x6Bu)",
        "MPU6050_REG_WHO_AM_I ((uint8_t)0x75u)",
        "MPU6050_BURST_SAMPLE_BYTES ((uint8_t)14u)",
        "mpu6050_write_register_readback",
        "mpu6050_wake_for_bringup",
        "mpu6050_configure_for_bringup",
        "mpu6050_read_configuration",
    ):
        assert snippet in header

    assert "openrf1_i2c_write_read(address_7bit, &reg, 1u, buffer, (uint8_t)sizeof(buffer))" in source
    assert "s16_be(buffer[12], buffer[13])" in source
    assert "0xD0" not in source
    assert "0xD1" not in source


def test_mpu6050_bringup_keil_target_is_isolated_and_has_no_absolute_paths():
    text = KEIL_PROJECT.read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_MPU6050_Bringup</TargetName>" in text
    assert r"<OutputDirectory>.\Objects_MPU6050_Bringup\</OutputDirectory>" in text
    assert "<OutputName>OpenRF1_MPU6050_Bringup</OutputName>" in text
    assert "<CreateHexFile>1</CreateHexFile>" in text
    assert "<uAC6>1</uAC6>" in text
    assert "STM32F10X_HD,USE_STDPERIPH_DRIVER" in text
    assert "..\\mpu6050_bringup;..\\full_hardware;..\\app" in text
    assert "C:\\Users" not in text
    assert "Desktop" not in text
    assert "OpenRF1_BH1750.hex" not in text
    assert "OpenRF1_BMP280_Bringup.hex" not in text
    assert "OpenRF1_FullHardware.hex" not in text

    included_sources = set(re.findall(r"<FileName>([^<]+)</FileName>", text))
    assert included_sources == {
        "i2c_bus.c",
        "main_mpu6050_bringup.c",
        "mpu6050.c",
        "openrf1_status.c",
        "platform_mpu6050_bringup.c",
        "soft_i2c.c",
        "telemetry_mpu6050_bringup.c",
    }
