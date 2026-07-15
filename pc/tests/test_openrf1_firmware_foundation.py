from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "firmware" / "openrf1" / "app"


def test_board_config_locks_openrf1_bh1750_pin_address_and_uart_constants():
    text = (APP_ROOT / "board_config.h").read_text(encoding="utf-8")

    assert 'OPENRF1_BOARD_NAME "OpenRF1"' in text
    assert 'OPENRF1_MCU_PART "STM32F103RCT6"' in text
    assert "OPENRF1_SOFT_I2C_SCL_PORT GPIOB" in text
    assert "OPENRF1_SOFT_I2C_SCL_PIN GPIO_Pin_1" in text
    assert "OPENRF1_SOFT_I2C_SDA_PORT GPIOC" in text
    assert "OPENRF1_SOFT_I2C_SDA_PIN GPIO_Pin_3" in text
    assert "OPENRF1_BH1750_ADDRESS_7BIT ((uint8_t)0x23u)" in text
    assert "OPENRF1_TELEMETRY_USART USART1" in text
    assert "OPENRF1_TELEMETRY_USART_TX_PIN GPIO_Pin_9" in text
    assert "OPENRF1_TELEMETRY_USART_RX_PIN GPIO_Pin_10" in text
    assert "OPENRF1_TELEMETRY_BAUD ((uint32_t)115200u)" in text


def test_telemetry_buffer_can_hold_worst_case_jsonl():
    text = (APP_ROOT / "board_config.h").read_text(encoding="utf-8")
    match = re.search(
        r"OPENRF1_TELEMETRY_BUFFER_BYTES\s+\(\(uint16_t\)(\d+)u\)",
        text,
    )

    assert match is not None
    assert int(match.group(1)) >= 223


def test_software_i2c_uses_open_drain_bounded_ack_and_recovery():
    text = (APP_ROOT / "soft_i2c.c").read_text(encoding="utf-8")

    assert "GPIO_Mode_Out_OD" in text
    assert "GPIO_Speed_50MHz" in text
    assert "openrf1_soft_i2c_wait_ack(uint16_t timeout_ticks)" in text
    assert "OPENRF1_I2C_ACK_TIMEOUT" in text
    assert "openrf1_soft_i2c_stop();" in text
    assert "openrf1_soft_i2c_recover_bus" in text
    assert "while (1)" not in text


def test_bh1750_firmware_uses_7bit_address_internally_derived_bytes_and_no_sentinel_zero():
    text = (APP_ROOT / "bh1750.c").read_text(encoding="utf-8")

    assert "bh1750_write_address_from_7bit" in text
    assert "bh1750_read_address_from_7bit" in text
    assert "BH1750_CMD_ONE_TIME_HIGH_RESOLUTION" in text
    assert "bh1750_raw_to_centilux" in text
    assert "sample->has_illuminance = 0u" in text
    assert "sample->status = status" in text


def test_bh1750_state_machine_is_rollover_safe_and_prevents_period_underflow():
    text = (APP_ROOT / "bh1750.c").read_text(encoding="utf-8")

    assert "(int32_t)(now_ms - context->next_action_ms)" in text
    assert "publish_period_ms > context->measurement_time_ms" in text


def test_bh1750_i2c_failures_attempt_bus_recovery():
    text = (APP_ROOT / "bh1750.c").read_text(encoding="utf-8")

    assert "openrf1_soft_i2c_recover_bus(OPENRF1_SOFT_I2C_RECOVERY_PULSES)" in text


def test_software_i2c_ack_timeout_has_a_bounded_delay_per_poll():
    text = (APP_ROOT / "soft_i2c.c").read_text(encoding="utf-8")
    start = text.index("OpenRf1I2cStatus openrf1_soft_i2c_wait_ack")
    end = text.index("void openrf1_soft_i2c_ack", start)
    function_text = text[start:end]

    assert "while (sda_read()) {\n        i2c_delay();" in function_text


def test_telemetry_formatter_is_bounded_jsonl_and_does_not_use_sprintf():
    text = (APP_ROOT / "telemetry.c").read_text(encoding="utf-8")

    assert "snprintf" in text
    assert "sprintf" not in text.replace("snprintf", "")
    assert '\\"mars_scout_stm32_sensor_telemetry\\"' in text
    assert '\\"message_type\\":\\"illuminance\\"' in text
    assert '\\"sensor_id\\":\\"%s\\"' in text
    assert '\\"illuminance_lux\\":null' in text
    assert "\\n" in text


def test_phase32a_firmware_scope_excludes_later_sensors_and_rover_control():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in APP_ROOT.glob("*.[ch]"))
    forbidden = (
        "BMP280",
        "HC-SR04",
        "TCRT5000",
        "MPU6050",
        "motor",
        "encoder",
        "mecanum",
        "SLAM",
        "navigation",
    )

    for term in forbidden:
        assert term not in combined
