from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "firmware" / "openrf1" / "encoder_bringup"
PROJECT = ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_Encoder_Bringup.uvprojx"


def _read(name: str) -> str:
    return (SOURCE_DIR / name).read_text(encoding="utf-8")


def _constant(source: str, name: str) -> int:
    match = re.search(rf"#define\s+{name}\s+\(\(\w+_t\)(\d+)u\)", source)
    assert match is not None, name
    return int(match.group(1))


def test_target_is_encoder_only_and_has_no_motion_path() -> None:
    main = _read("main_encoder_bringup.c")
    platform = _read("platform_encoder_bringup.c")

    assert "vehicle_demo_encoder" in main
    assert r'\"motor_outputs_present\":false' in main
    assert "openrf1_encoder_read_raw" in main
    assert "command" not in main.lower()
    assert "TIM8" not in platform
    assert "motor" not in platform.lower()
    assert "ultrasonic" not in platform.lower()
    assert "hall" not in platform.lower()
    assert "GPIOC" not in platform and "GPIOD" not in platform
    assert "USART_CR1_RE" not in platform
    assert "USART_CR1_RXNEIE" not in platform
    assert "USART_CR1_UE | USART_CR1_TE" in platform


def test_counter_mapping_and_unknown_physical_semantics_are_explicit() -> None:
    config = _read("board_config.h")
    main = _read("main_encoder_bringup.c")
    platform = _read("platform_encoder_bringup.c")

    assert _constant(config, "OPENRF1_ENCODER_BRINGUP_COUNTER_BITS") == 16
    assert _constant(config, "OPENRF1_ENCODER_BRINGUP_SAMPLE_PERIOD_MS") == 100
    assert _constant(config, "OPENRF1_ENCODER_BRINGUP_USART_BAUD") == 115200
    assert "vendor_connector_mapping_physical_wheels_unverified" in config
    assert r'\"direction_signs_verified\":false' in main
    assert "raw_counts[0] = (uint16_t)TIM5->CNT;" in platform
    assert "raw_counts[1] = (uint16_t)TIM3->CNT;" in platform
    assert "raw_counts[2] = (uint16_t)TIM2->CNT;" in platform
    assert "raw_counts[3] = (uint16_t)TIM4->CNT;" in platform
    assert "encoder_timer_configure(TIM5); /* CN1 */" in platform
    assert "encoder_timer_configure(TIM3); /* CN2 */" in platform
    assert "encoder_timer_configure(TIM2); /* CN3, full remap */" in platform
    assert "encoder_timer_configure(TIM4); /* CN4 */" in platform


def test_timer_and_debug_configuration_is_read_only() -> None:
    platform = _read("platform_encoder_bringup.c")

    assert "swj_jtag_disabled_swd_enabled" in platform
    assert "mapr = AFIO->MAPR;" in platform
    assert "timer->SMCR = 3u;" in platform
    assert "timer->CCMR1 = 1u | (1u << 8);" in platform
    assert "timer->CCER = 0u;" in platform
    assert "timer->PSC = 0u;" in platform
    assert "timer->ARR = UINT16_MAX;" in platform
    assert "External 3.3 V pull-ups are required" in platform
    assert "USART_CR1_TXEIE" in platform


def test_keil_target_is_dedicated_relative_and_reproducible() -> None:
    project = PROJECT.read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_Encoder_Bringup</TargetName>" in project
    assert ".\\Objects_Encoder_Bringup\\" in project
    assert "<OutputName>OpenRF1_Encoder_Bringup</OutputName>" in project
    assert "<CreateHexFile>1</CreateHexFile>" in project
    assert "..\\encoder_bringup;..\\vehicle_demo" in project
    for source in (
        "main_encoder_bringup.c",
        "platform_encoder_bringup.c",
        "encoder_input.c",
    ):
        assert source in project
    for forbidden in (
        "main_vehicle_demo.c",
        "obstacle_control.c",
        "ultrasonic_array.c",
        "hall_input.c",
        "platform_vehicle_demo.c",
    ):
        assert forbidden not in project
    assert "C:\\Users\\" not in project
