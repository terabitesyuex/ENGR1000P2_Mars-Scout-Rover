from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "firmware" / "openrf1" / "app"
BOARD_CONFIG = APP_ROOT / "config" / "board_config.h"
SENSOR_CONFIG = APP_ROOT / "config" / "sensor_config.h"
MOTOR_HEADER = APP_ROOT / "drivers" / "motor" / "motor.h"
MOTOR_SOURCE = APP_ROOT / "drivers" / "motor" / "motor.c"
ENCODER_HEADER = APP_ROOT / "drivers" / "encoder" / "encoder.h"
ENCODER_SOURCE = APP_ROOT / "drivers" / "encoder" / "encoder.c"
MECANUM_HEADER = APP_ROOT / "control" / "mecanum.h"
MECANUM_SOURCE = APP_ROOT / "control" / "mecanum.c"
FOUNDATION_MAIN = APP_ROOT / "rover_control" / "main_rover_control_foundation.c"
KEIL_PROJECT = (
    REPO_ROOT
    / "firmware"
    / "openrf1"
    / "keil"
    / "OpenRF1_RoverControl_Foundation.uvprojx"
)
TODO_HARDWARE = REPO_ROOT / "TODO_HARDWARE.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _round_divide(numerator: int, denominator: int) -> int:
    if numerator >= 0:
        return (numerator + denominator // 2) // denominator
    return -((-numerator + denominator // 2) // denominator)


def _mecanum_reference(
    *,
    vx_mm_s: int,
    vy_mm_s: int,
    omega_mrad_s: int,
    wheel_radius_mm: int,
    half_wheelbase_mm: int,
    half_track_width_mm: int,
    max_wheel_speed_mrad_s: int,
) -> tuple[int, int, int, int]:
    lever_arm_mm = half_wheelbase_mm + half_track_width_mm
    rotation_mm_s = _round_divide(omega_mrad_s * lever_arm_mm, 1000)
    linear_mm_s = (
        vx_mm_s - vy_mm_s - rotation_mm_s,
        vx_mm_s + vy_mm_s + rotation_mm_s,
        vx_mm_s + vy_mm_s - rotation_mm_s,
        vx_mm_s - vy_mm_s + rotation_mm_s,
    )
    angular_mrad_s = [
        _round_divide(value * 1000, wheel_radius_mm) for value in linear_mm_s
    ]
    peak = max(abs(value) for value in angular_mrad_s)
    if peak > max_wheel_speed_mrad_s:
        angular_mrad_s = [
            _round_divide(value * max_wheel_speed_mrad_s, peak)
            for value in angular_mrad_s
        ]
    return tuple(angular_mrad_s)


def _find_armclang() -> Path | None:
    on_path = shutil.which("armclang")
    if on_path:
        return Path(on_path)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate = (
            Path(local_app_data)
            / "Keil_v5"
            / "ARM"
            / "ARMCLANG"
            / "bin"
            / "armclang.exe"
        )
        if candidate.is_file():
            return candidate
    candidate = Path("C:/Keil_v5/ARM/ARMCLANG/bin/armclang.exe")
    return candidate if candidate.is_file() else None


def test_unified_architecture_files_exist_without_moving_bringups():
    required = (
        APP_ROOT / "README.md",
        BOARD_CONFIG,
        SENSOR_CONFIG,
        MOTOR_HEADER,
        MOTOR_SOURCE,
        ENCODER_HEADER,
        ENCODER_SOURCE,
        MECANUM_HEADER,
        MECANUM_SOURCE,
        FOUNDATION_MAIN,
        KEIL_PROJECT,
        TODO_HARDWARE,
    )
    assert all(path.is_file() for path in required)
    assert not (REPO_ROOT / "rplidar_c1_subsystem").exists()
    assert not (APP_ROOT / "middleware").exists()
    for placeholder in ("distance", "imu", "lidar"):
        assert not (APP_ROOT / "drivers" / placeholder).exists()
    assert (REPO_ROOT / "firmware" / "openrf1" / "mpu6050_bringup").is_dir()
    assert (REPO_ROOT / "firmware" / "openrf1" / "hcsr04_bringup").is_dir()
    assert (REPO_ROOT / "firmware" / "openrf1" / "bmp280_bringup").is_dir()
    assert (REPO_ROOT / "firmware" / "openrf1" / "ground_sensors_bringup").is_dir()


def test_keil_arm_compiler_6_target_is_isolated_from_all_bringups():
    project_bytes = KEIL_PROJECT.read_bytes()
    assert not project_bytes.startswith(b"\xef\xbb\xbf")
    project = project_bytes.decode("utf-8")
    assert "<TargetName>OpenRF1_RoverControl_Foundation</TargetName>" in project
    assert "<Device>STM32F103RC</Device>" in project
    assert "<uAC6>1</uAC6>" in project
    assert "V6.24::ARMCLANG" in project
    assert "<OutputDirectory>.\\Objects_RoverControl_Foundation\\</OutputDirectory>" in project
    for source_path in (
        "..\\app\\rover_control\\main_rover_control_foundation.c",
        "..\\app\\drivers\\motor\\motor.c",
        "..\\app\\drivers\\encoder\\encoder.c",
        "..\\app\\control\\mecanum.c",
    ):
        assert source_path in project
    for forbidden in (
        "ground_sensors_bringup",
        "hcsr04_bringup",
        "mpu6050_bringup",
        "bmp280_bringup",
        "StdPeriph Drivers:GPIO",
        "StdPeriph Drivers:USART",
    ):
        assert forbidden not in project

    main_source = _text(FOUNDATION_MAIN)
    assert "foundation_apply_motor" in main_source
    assert "foundation_read_encoder" in main_source
    assert "stm32f10x" not in main_source
    assert "GPIO" not in main_source
    assert "USART" not in main_source


def test_board_config_keeps_unknown_hardware_centralized_and_disabled():
    config = _text(BOARD_CONFIG)
    assert '#define OPENRF1_HARDWARE_UNKNOWN_TEXT "UNKNOWN"' in config
    assert "#define OPENRF1_MOTOR_HARDWARE_MAPPING_READY ((uint8_t)0u)" in config
    assert "#define OPENRF1_ENCODER_HARDWARE_MAPPING_READY ((uint8_t)0u)" in config
    assert "#define OPENRF1_MECANUM_GEOMETRY_READY ((uint8_t)0u)" in config
    assert "#define OPENRF1_RPLIDAR_C1_UART_MAPPING_READY ((uint8_t)0u)" in config
    assert "#define OPENRF1_ESP32_UART_MAPPING_READY ((uint8_t)0u)" in config
    for suffix in (
        "MOTOR_FRONT_LEFT_PWM_PIN",
        "MOTOR_FRONT_RIGHT_PWM_PIN",
        "MOTOR_REAR_LEFT_PWM_PIN",
        "MOTOR_REAR_RIGHT_PWM_PIN",
        "ENCODER_FRONT_LEFT_A_PIN",
        "ENCODER_FRONT_LEFT_B_PIN",
        "ENCODER_FRONT_RIGHT_A_PIN",
        "ENCODER_FRONT_RIGHT_B_PIN",
        "ENCODER_REAR_LEFT_A_PIN",
        "ENCODER_REAR_LEFT_B_PIN",
        "ENCODER_REAR_RIGHT_A_PIN",
        "ENCODER_REAR_RIGHT_B_PIN",
        "RPLIDAR_C1_UART_TX_PIN",
        "RPLIDAR_C1_UART_RX_PIN",
        "ESP32_UART_TX_PIN",
        "ESP32_UART_RX_PIN",
    ):
        assert f"#define OPENRF1_{suffix} OPENRF1_HARDWARE_UNKNOWN_TEXT" in config


def test_user_provided_motor_and_encoder_numbers_are_recorded_without_geometry_guess():
    config = _text(BOARD_CONFIG)
    assert "OPENRF1_JGB37_520_MIN_SUPPLY_MV ((uint32_t)6000u)" in config
    assert "OPENRF1_JGB37_520_MAX_SUPPLY_MV ((uint32_t)12000u)" in config
    assert "OPENRF1_ENCODER_MOTOR_SHAFT_PPR ((uint32_t)11u)" in config
    assert "OPENRF1_GEAR_RATIO_NUMERATOR ((uint32_t)30u)" in config
    assert "OPENRF1_ENCODER_OUTPUT_SHAFT_PPR ((uint32_t)330u)" in config
    assert "OPENRF1_ENCODER_QUADRATURE_MULTIPLIER ((uint32_t)4u)" in config
    assert "OPENRF1_ENCODER_COUNTS_PER_OUTPUT_REV ((uint32_t)1320u)" in config
    assert "#define OPENRF1_WHEEL_RADIUS_MM OPENRF1_HARDWARE_UNKNOWN_I32" in config
    assert "#define OPENRF1_HALF_WHEELBASE_MM OPENRF1_HARDWARE_UNKNOWN_I32" in config
    assert "#define OPENRF1_HALF_TRACK_WIDTH_MM OPENRF1_HARDWARE_UNKNOWN_I32" in config
    assert "#define OPENRF1_MECANUM_ROLLER_LAYOUT OPENRF1_HARDWARE_UNKNOWN_I32" in config


def test_motor_hal_has_four_logical_channels_and_injected_backend():
    header = _text(MOTOR_HEADER)
    source = _text(MOTOR_SOURCE)
    for wheel in ("FRONT_LEFT", "FRONT_RIGHT", "REAR_LEFT", "REAR_RIGHT"):
        assert f"MOTOR_ID_{wheel}" in header
    assert "MotorApplyOutputFn" in header
    assert "motor_set_speed(" in header
    assert "motor_set_direction(" in header
    assert "motor_stop(" in header
    assert "motor_stop_all(" in header
    assert "MOTOR_COMMAND_MAX_PERMILLE ((int16_t)1000)" in header
    assert "controller->outputs[motor_id] = *output;" in source
    assert source.index("backend_status =") < source.index(
        "controller->outputs[motor_id] = *output;"
    )


def test_encoder_hal_uses_signed_cumulative_counts_and_explicit_speed_units():
    header = _text(ENCODER_HEADER)
    source = _text(ENCODER_SOURCE)
    for wheel in ("FRONT_LEFT", "FRONT_RIGHT", "REAR_LEFT", "REAR_RIGHT"):
        assert f"ENCODER_ID_{wheel}" in header
    assert "EncoderReadCountFn" in header
    assert "encoder_get_count(" in header
    assert "encoder_reset(" in header
    assert "encoder_get_speed(" in header
    assert "speed_counts_per_second" in header
    assert "delta_count * 1000" in source
    assert "timestamp_ms - channel->last_sample_ms" in source
    assert "channel->zero_offset_count = raw_count;" in source
    assert "encoder_wrapped_delta" in source
    assert "(int64_t)UINT32_MAX + 1" in source


@pytest.mark.parametrize(
    ("command", "expected"),
    (
        (
            {"vx_mm_s": 1000, "vy_mm_s": 0, "omega_mrad_s": 0},
            (20000, 20000, 20000, 20000),
        ),
        (
            {"vx_mm_s": 0, "vy_mm_s": 500, "omega_mrad_s": 0},
            (-10000, 10000, 10000, -10000),
        ),
        (
            {"vx_mm_s": 0, "vy_mm_s": 0, "omega_mrad_s": 1000},
            (-4000, 4000, -4000, 4000),
        ),
        (
            {"vx_mm_s": 1000, "vy_mm_s": 500, "omega_mrad_s": 1000},
            (6000, 34000, 26000, 14000),
        ),
    ),
)
def test_mecanum_inverse_kinematics_contract_vectors(command, expected):
    assert _mecanum_reference(
        **command,
        wheel_radius_mm=50,
        half_wheelbase_mm=100,
        half_track_width_mm=100,
        max_wheel_speed_mrad_s=100000,
    ) == expected


def test_mecanum_preserves_ratios_when_limited():
    assert _mecanum_reference(
        vx_mm_s=1000,
        vy_mm_s=500,
        omega_mrad_s=1000,
        wheel_radius_mm=50,
        half_wheelbase_mm=100,
        half_track_width_mm=100,
        max_wheel_speed_mrad_s=17000,
    ) == (3000, 17000, 13000, 7000)


def test_mecanum_requires_explicit_verified_x_roller_contract():
    header = _text(MECANUM_HEADER)
    source = _text(MECANUM_SOURCE)
    assert "MECANUM_ROLLER_LAYOUT_UNVERIFIED = 0" in header
    assert "MECANUM_ROLLER_LAYOUT_X = 1" in header
    assert "MecanumRollerLayout roller_layout;" in header
    assert "geometry->roller_layout != MECANUM_ROLLER_LAYOUT_X" in source


def test_motion_core_has_no_stm32_gpio_timer_uart_or_dynamic_allocation():
    combined = "\n".join(
        _text(path)
        for path in (
            MOTOR_HEADER,
            MOTOR_SOURCE,
            ENCODER_HEADER,
            ENCODER_SOURCE,
            MECANUM_HEADER,
            MECANUM_SOURCE,
        )
    )
    for forbidden in (
        "stm32f10x",
        "GPIOA",
        "GPIOB",
        "GPIOC",
        "TIM1",
        "TIM2",
        "TIM3",
        "TIM4",
        "USART1",
        "USART2",
        "USART3",
        "malloc(",
        "calloc(",
        "realloc(",
        "free(",
    ):
        assert forbidden not in combined


def test_hardware_todo_locks_documented_mappings_and_required_unknowns():
    todo = _text(TODO_HARDWARE)
    for required in (
        "| Motor PWM GPIO | authoritative_vendor_documented | PC6, PC7, PC8, PC9 |",
        "| Encoder A GPIO for all four wheels | authoritative_vendor_documented | CN1 PA0, CN2 PA6, CN3 PA15, CN4 PB6 |",
        "| Encoder B GPIO for all four wheels | authoritative_vendor_documented | CN1 PA1, CN2 PA7, CN3 PB3, CN4 PB7 |",
        "| RPLIDAR C1 STM32 UART and pins | authoritative_vendor_documented | H5 pin 3 PA2/TX2, pin 4 PA3/RX2; physical C1 link still unverified |",
        "| ESP32 STM32 UART and pins | authoritative_vendor_documented | H6 pin 3 PB11/RX3, pin 4 PB10/TX3; physical ESP32 link still unverified |",
        "| Wheel radius | unknown |",
        "| Half wheelbase | unknown |",
        "| Half track width | unknown |",
        "| Battery advertised electrical values | seller_documented | Li-ion, 11.1 V nominal, 7800 mAh, 5C, 12.6 V fully charged; source images and hashes archived |",
        "| Battery BMS current limits | unverified |",
        "| Battery charger | seller_documented; physical validation required |",
        "| Battery voltage/current telemetry ADC path | unknown |",
    ):
        assert required in todo
    assert "No hardware was connected, powered, flashed, or accessed" in todo


def test_motion_sources_compile_with_keil_arm_compiler_6(tmp_path):
    armclang = _find_armclang()
    if armclang is None:
        pytest.skip("Keil ARM Compiler 6 is not installed")

    sources = (MOTOR_SOURCE, ENCODER_SOURCE, MECANUM_SOURCE)
    for source in sources:
        output = tmp_path / f"{source.stem}.o"
        result = subprocess.run(
            [
                str(armclang),
                "--target=arm-arm-none-eabi",
                "-mcpu=cortex-m3",
                "-std=c99",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-ffreestanding",
                "-c",
                str(source),
                "-I",
                str(source.parent),
                "-o",
                str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 and "permission denied" in result.stderr.lower():
            pytest.skip("sandbox does not permit launching Keil ARM Compiler 6")
        assert result.returncode == 0, result.stdout + result.stderr
        assert output.is_file()
