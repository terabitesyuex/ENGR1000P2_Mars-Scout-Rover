from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
FULL_ROOT = REPO_ROOT / "firmware" / "openrf1" / "full_hardware"
KEIL_PROJECT = REPO_ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_FullHardware.uvprojx"


def test_phase32b_full_hardware_source_tree_and_feature_flags_exist():
    required = {
        "board_config.h",
        "memory_budget.h",
        "scheduler.c",
        "uart_ring_buffer.c",
        "i2c_bus.c",
        "bmp280.c",
        "mpu6050.c",
        "digital_filter.c",
        "ground_sensors.c",
        "hall_sensor.c",
        "hcsr04.c",
        "rplidar_c1_transport.c",
        "esp32_link.c",
        "telemetry_full.c",
        "platform_full_hardware.c",
        "main_full_hardware.c",
    }

    assert required.issubset({path.name for path in FULL_ROOT.iterdir()})
    config = (FULL_ROOT / "board_config.h").read_text(encoding="utf-8")
    for flag in (
        "OPENRF1_ENABLE_BH1750",
        "OPENRF1_ENABLE_BMP280",
        "OPENRF1_ENABLE_MPU6050",
        "OPENRF1_ENABLE_ULTRASONIC",
        "OPENRF1_ENABLE_GROUND_SENSORS",
        "OPENRF1_ENABLE_HALL",
        "OPENRF1_ENABLE_RPLIDAR_C1",
        "OPENRF1_ENABLE_ESP32_LINK",
    ):
        assert f"#define {flag} 1" in config
    assert 'OPENRF1_RPLIDAR_USART_NAME "USART2"' in config
    assert 'OPENRF1_ESP32_USART_NAME "USART3"' in config
    assert "OPENRF1_RPLIDAR_USART_PINS_CONFIRMED 0" in config
    assert "OPENRF1_ESP32_USART_PINS_CONFIRMED 0" in config


def test_phase32b_keil_project_has_isolated_output_and_no_absolute_paths():
    text = KEIL_PROJECT.read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_FullHardware</TargetName>" in text
    assert r"<OutputDirectory>.\Objects_FullHardware\</OutputDirectory>" in text
    assert "<OutputName>OpenRF1_FullHardware</OutputName>" in text
    assert "..\\full_hardware;..\\app" in text
    assert "C:\\Users" not in text
    assert "OpenRF1_BH1750.hex" not in text
    assert "..\\app\\main.c" not in text
    assert "..\\app\\platform.c" not in text


def test_phase32b_firmware_uses_bounded_buffers_and_no_dynamic_allocation():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in FULL_ROOT.glob("*.[ch]"))

    assert "malloc" not in combined
    assert re.search(r"(^|[^A-Za-z0-9_])free\s*\(", combined) is None
    assert "OPENRF1_STATIC_ASSERT" in combined
    assert "OPENRF1_RPLIDAR_RX_BUFFER_BYTES" in combined
    assert "OPENRF1_ESP32_RX_BUFFER_BYTES" in combined
    assert "printf(" not in combined.replace("snprintf(", "")


def test_phase32b_main_loop_uses_scheduler_and_ultrasonic_state_machine():
    text = (FULL_ROOT / "main_full_hardware.c").read_text(encoding="utf-8")

    assert "openrf1_scheduler_service" in text
    assert "hcsr04_start" in text
    assert "hcsr04_poll" in text
    assert re.search(r"while\s*\(\s*1\s*\)", text)
    assert "USART2_IRQHandler" not in text
    assert "USART3_IRQHandler" not in text
