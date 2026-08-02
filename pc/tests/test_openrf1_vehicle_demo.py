from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "firmware" / "openrf1" / "vehicle_demo"
PROJECT = ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_VehicleDemo.uvprojx"


def _read(name: str) -> str:
    return (SOURCE_DIR / name).read_text(encoding="utf-8")


def _constant(source: str, name: str) -> int:
    match = re.search(rf"#define\s+{name}\s+\(\(\w+_t\)(\d+)u\)", source)
    assert match is not None, name
    return int(match.group(1))


def test_user_confirmed_pin_profile_is_centralized() -> None:
    config = _read("demo_config.h")

    assert '"hardware_group_3us_user_confirmed"' in config
    assert 'OPENRF1_DEMO_US_LEFT_TRIGGER_PIN "PB9"' in config
    assert 'OPENRF1_DEMO_US_LEFT_ECHO_PIN "PB8"' in config
    assert 'OPENRF1_DEMO_US_CENTER_TRIGGER_PIN "PB5"' in config
    assert 'OPENRF1_DEMO_US_CENTER_ECHO_PIN "PB4"' in config
    assert 'OPENRF1_DEMO_US_RIGHT_TRIGGER_PIN "PD2"' in config
    assert 'OPENRF1_DEMO_US_RIGHT_ECHO_PIN "PC11"' in config
    assert "User-confirmed current demo mapping" in config
    assert "Electrical ECHO voltage safety remains unverified" in config


def test_safety_and_ultrasonic_timing_constants() -> None:
    config = _read("demo_config.h")

    assert _constant(config, "OPENRF1_DEMO_FRONT_STOP_MM") == 250
    assert _constant(config, "OPENRF1_DEMO_SIDE_STOP_MM") == 200
    assert _constant(config, "OPENRF1_DEMO_HAZARD_CONFIRM_COUNT") == 2
    assert _constant(config, "OPENRF1_DEMO_COMMAND_WATCHDOG_MS") == 2000
    assert _constant(config, "OPENRF1_DEMO_SENSOR_MAX_AGE_MS") == 500
    assert _constant(config, "OPENRF1_DEMO_TRIGGER_PULSE_US") >= 10
    assert _constant(config, "OPENRF1_DEMO_ECHO_TIMEOUT_US") == 30000
    assert _constant(config, "OPENRF1_DEMO_INTER_CHANNEL_GAP_US") == 35000


def test_distance_conversion_vectors_and_timeout_boundary() -> None:
    def distance_mm(pulse_us: int) -> int | None:
        if pulse_us <= 0 or pulse_us >= 30_000:
            return None
        return (pulse_us * 343 + 1000) // 2000

    assert distance_mm(0) is None
    assert distance_mm(1000) == 172
    assert distance_mm(2000) == 343
    assert distance_mm(10_000) == 1715
    assert distance_mm(30_000) is None


def test_sensor_failure_and_stale_data_are_fail_closed() -> None:
    control = _read("obstacle_control.c")

    safety_check = control.index("if (all_samples_current(samples, now_ms) == 0u)")
    state_switch = control.index("switch (controller->state)")
    assert safety_check < state_switch
    assert "enter_sensor_fault(controller, now_ms);" in control
    assert "controller->armed = 0u;" in control
    assert "controller->motion = DEMO_MOTION_STOP;" in control
    assert "DEMO_CONTROL_SENSOR_FAULT" in control
    assert "DEMO_CONTROL_WATCHDOG_FAULT" in control
    assert "format_distance" in _read("main_vehicle_demo.c")
    assert 'snprintf(output, 6u, "null")' in _read("main_vehicle_demo.c")


def test_motion_requires_explicit_arm_start_and_heartbeat() -> None:
    main = _read("main_vehicle_demo.c")
    control = _read("obstacle_control.c")

    assert 'strings_equal(command, "ARM")' in main
    assert 'strings_equal(command, "START")' in main
    assert 'strings_equal(command, "HEARTBEAT")' in main
    assert "DEMO_COMMAND_STOP" in main
    assert "OPENRF1_DEMO_COMMAND_WATCHDOG_MS" in control
    assert "controller->last_heartbeat_ms" in control
    assert "if (any_hazard(samples) != 0u)" in control
    assert "enter_state(controller, DEMO_CONTROL_READY, now_ms);" in control
    assert "DEMO_MOTION_FORWARD" not in main.split("demo_platform_init", maxsplit=1)[0]


def test_ultrasonic_runtime_is_nonblocking_and_staggered() -> None:
    ultrasonic = _read("ultrasonic_array.c")
    platform = _read("platform_vehicle_demo.c")

    assert "while (" not in ultrasonic
    assert "DEMO_ULTRASONIC_WAIT_LOW" in ultrasonic
    assert "DEMO_ULTRASONIC_WAIT_RISE" in ultrasonic
    assert "DEMO_ULTRASONIC_WAIT_FALL" in ultrasonic
    assert "OPENRF1_DEMO_INTER_CHANNEL_GAP_US" in ultrasonic
    assert "DWT" not in platform
    assert "g_timer6_overflows" in platform
    assert "TIM6_IRQHandler" in platform
    assert "USART_CR1_TXEIE" in platform


def test_motor_mapping_preserves_hardware_team_calibration() -> None:
    config = _read("demo_config.h")
    platform = _read("platform_vehicle_demo.c")

    assert _constant(config, "OPENRF1_DEMO_CN1_SPEED_SCALE_PERMILLE") == 1010
    assert _constant(config, "OPENRF1_DEMO_CN2_SPEED_SCALE_PERMILLE") == 1010
    assert _constant(config, "OPENRF1_DEMO_CN3_SPEED_SCALE_PERMILLE") == 750
    assert _constant(config, "OPENRF1_DEMO_CN4_SPEED_SCALE_PERMILLE") == 750
    for pin in ("GPIOA, 8u", "GPIOA, 11u", "GPIOA, 12u", "GPIOC, 10u"):
        assert pin in platform
    for channel in ("TIM8->CCR1", "TIM8->CCR2", "TIM8->CCR3", "TIM8->CCR4"):
        assert channel in platform


def test_keil_target_is_isolated_reproducible_and_relative() -> None:
    project = PROJECT.read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_VehicleDemo</TargetName>" in project
    assert ".\\Objects_VehicleDemo\\" in project
    assert "<OutputName>OpenRF1_VehicleDemo</OutputName>" in project
    assert "<CreateHexFile>1</CreateHexFile>" in project
    assert "..\\vehicle_demo" in project
    for source in (
        "main_vehicle_demo.c",
        "obstacle_control.c",
        "platform_vehicle_demo.c",
        "ultrasonic_array.c",
    ):
        assert source in project
    assert "C:\\Users\\" not in project
    assert ":\\Desktop\\" not in project
    assert "main_motor_identify.c" not in project


def test_telemetry_is_jsonl_only_and_reports_pin_profile() -> None:
    main = _read("main_vehicle_demo.c")

    assert r'\"message_type\":\"vehicle_demo_identity' in main
    assert r'\"message_type\":\"vehicle_demo_status' in main
    assert "OPENRF1_DEMO_PIN_PROFILE" in main
    assert "OpenRF1 3US AUTO OBSTACLE" not in main
    assert r"\r\n" in main
