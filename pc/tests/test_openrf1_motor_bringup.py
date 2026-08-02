from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "firmware" / "openrf1" / "motor_bringup"
PROJECT = ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_Motor_Bringup.uvprojx"


def _read(name: str) -> str:
    return (SOURCE_DIR / name).read_text(encoding="utf-8")


def test_control_starts_unconfigured_and_has_no_default_physical_values() -> None:
    config = _read("board_config.h")
    control = _read("motor_control.c")
    main = _read("main_motor_bringup.c")

    assert "MOTOR_BRINGUP_UNCONFIGURED" in control
    assert "control->config.connector = 0u;" in control
    assert "control->config.motor_sign = 0;" in control
    assert "control->config.encoder_sign = 0;" in control
    assert "control->config.max_duty_permille = 0u;" in control
    assert "control->config.watchdog_ms = 0u;" in control
    assert "vendor_connector_mapping_physical_wheels_unverified" in config
    assert r'\"user_duty_limit_required\":true' in main
    assert r'\"user_direction_signs_required\":true' in main


def test_configuration_run_and_watchdog_are_fail_disabled() -> None:
    control = _read("motor_control.c")

    assert "connector < 1u || connector > 4u" in control
    assert "sign_valid(motor_sign) == 0u" in control
    assert "sign_valid(encoder_sign) == 0u" in control
    assert "max_duty_permille == 0u" in control
    assert "watchdog_ms == 0u" in control
    assert "control->state != MOTOR_BRINGUP_DISARMED" in control
    assert "duty_permille > control->config.max_duty_permille" in control
    assert "requested_direction * control->config.motor_sign" in control
    assert "now_ms - control->last_heartbeat_ms" in control
    assert "clear_output(control);" in control
    assert "control->state = MOTOR_BRINGUP_FAULT;" in control


def test_platform_has_hardware_double_disable_and_one_channel_enable() -> None:
    platform = _read("platform_motor_bringup.c")

    assert "TIM8->CCER = 0u;" in platform
    assert "TIM8->BDTR = 0u;" in platform
    for compare in ("TIM8->CCR1 = 0u;", "TIM8->CCR2 = 0u;",
                    "TIM8->CCR3 = 0u;", "TIM8->CCR4 = 0u;"):
        assert compare in platform
    assert "motor_direction_outputs_low();" in platform
    assert "TIM8->CCER = channel_enable;" in platform
    assert "TIM8->BDTR = TIM_BDTR_MOE;" in platform
    assert "openrf1_motor_stop_all();" in platform
    assert "channel_enable = TIM_CCER_CC1E;" in platform
    assert "channel_enable = TIM_CCER_CC4E;" in platform
    assert "TIM_CCER_CC1E | TIM_CCER_CC2E" not in platform


def test_command_fault_and_transmit_failure_force_safe_stop() -> None:
    main = _read("main_motor_bringup.c")

    assert "CONFIG %u %d %d %u %lu %c" in main
    assert "RUN %d %u %c" in main
    for command in ("ARM", "HEARTBEAT", "STOP", "DISARM", "RESET"):
        assert f'"{command}"' in main
    assert "if (handle_command(g_command, now_ms) == 0u ||" in main
    assert "force_safe_stop();" in main
    assert "openrf1_motor_stop_all();" in main
    assert "emit_status(now_ms) == 0u" in main


def test_encoder_observation_stays_connector_labelled() -> None:
    platform = _read("platform_motor_bringup.c")
    main = _read("main_motor_bringup.c")

    assert "raw_counts[0] = (uint16_t)TIM5->CNT;" in platform
    assert "raw_counts[1] = (uint16_t)TIM3->CNT;" in platform
    assert "raw_counts[2] = (uint16_t)TIM2->CNT;" in platform
    assert "raw_counts[3] = (uint16_t)TIM4->CNT;" in platform
    assert "tim2_full_remap" in platform
    assert "swj_jtag_disabled_swd_enabled" in platform
    assert "selected_signed_delta_count" in main
    assert "front_left" not in main


def test_keil_target_is_dedicated_and_generated_output_is_ignored() -> None:
    project = PROJECT.read_text(encoding="utf-8")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_Motor_Bringup</TargetName>" in project
    assert ".\\Objects_Motor_Bringup\\" in project
    assert "..\\motor_bringup;..\\vehicle_demo" in project
    for source in (
        "main_motor_bringup.c",
        "motor_control.c",
        "platform_motor_bringup.c",
        "encoder_input.c",
    ):
        assert source in project
    for forbidden in (
        "main_vehicle_demo.c",
        "obstacle_control.c",
        "ultrasonic_array.c",
        "hall_input.c",
    ):
        assert forbidden not in project
    assert "Objects_Motor_Bringup/" in ignore

