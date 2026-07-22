from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from rplidar_c1_tools.openrf1_hcsr04_bringup import (
    HCSR04_CONNECTOR,
    HCSR04_CONNECTOR_PART,
    HCSR04_ECHO_DIVIDER_TOLERANCE_PERCENT,
    HCSR04_ECHO_GPIO_PIN,
    HCSR04_ECHO_GPIO_PORT,
    HCSR04_ECHO_MCU_PIN,
    HCSR04_ECHO_PULLDOWN_RESISTOR_OHM,
    HCSR04_ECHO_SERIES_RESISTOR_OHM,
    HCSR04_ECHO_TIMEOUT_US,
    HCSR04_ERROR_ECHO_FALL_TIMEOUT,
    HCSR04_ERROR_ECHO_NOT_LOW_BEFORE_TRIGGER,
    HCSR04_ERROR_ECHO_RISE_TIMEOUT,
    HCSR04_FIRMWARE_BUFFER_BYTES,
    HCSR04_MEASUREMENT_PERIOD_MS,
    HCSR04_TIMER,
    HCSR04_TIMER_PERIOD,
    HCSR04_TIMER_PRESCALER,
    HCSR04_TIMER_TICK_HZ,
    HCSR04_TRIGGER_GPIO_PIN,
    HCSR04_TRIGGER_GPIO_PORT,
    HCSR04_TRIGGER_MCU_PIN,
    HCSR04_TRIGGER_PULSE_US,
    HCSR04_TELEMETRY_MAX_LINE_BYTES,
    Hcsr04BringupError,
    Hcsr04ErrorRecord,
    Hcsr04Measurement,
    connector_pin_map,
    echo_divider_output_mv,
    echo_pulse_us_to_distance_mm,
    format_error_telemetry,
    format_identity_telemetry,
    format_measurement_telemetry,
    pulse_width_us,
    telemetry_line_bytes,
    validate_telemetry_buffer_capacity,
    validate_pulse_width_us,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BRINGUP_ROOT = REPO_ROOT / "firmware" / "openrf1" / "hcsr04_bringup"
KEIL_PROJECT = REPO_ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_HCSR04_Bringup.uvprojx"
RTE_COMPONENTS = REPO_ROOT / "firmware" / "openrf1" / "keil" / "RTE" / "_OpenRF1_HCSR04_Bringup" / "RTE_Components.h"
DOC_PATH = REPO_ROOT / "docs" / "openrf1_hcsr04_bringup.md"
HARDWARE_LOCK = REPO_ROOT / "HARDWARE_LOCK.md"


def _record(line: str) -> dict:
    assert line.endswith("\n")
    assert "NaN" not in line
    assert "Infinity" not in line
    assert line.startswith("{")
    return json.loads(line)


def test_hcsr04_vendor_documented_connector_pins_timer_and_divider_are_locked():
    assert HCSR04_CONNECTOR == "CN6"
    assert HCSR04_CONNECTOR_PART == "B4B-PH-K-S(LF)(SN)"
    assert connector_pin_map() == {
        1: "VCC_5V",
        2: "GND",
        3: "PA5_TRIG",
        4: "PA4_ECHO",
    }
    assert HCSR04_TRIGGER_MCU_PIN == "PA5"
    assert HCSR04_TRIGGER_GPIO_PORT == "GPIOA"
    assert HCSR04_TRIGGER_GPIO_PIN == "GPIO_Pin_5"
    assert HCSR04_ECHO_MCU_PIN == "PA4"
    assert HCSR04_ECHO_GPIO_PORT == "GPIOA"
    assert HCSR04_ECHO_GPIO_PIN == "GPIO_Pin_4"
    assert HCSR04_TIMER == "TIM6"
    assert HCSR04_TIMER_PRESCALER == 71
    assert HCSR04_TIMER_PERIOD == 30000
    assert HCSR04_TIMER_TICK_HZ == 1_000_000
    assert HCSR04_TRIGGER_PULSE_US == 10
    assert HCSR04_ECHO_TIMEOUT_US == 30_000
    assert HCSR04_MEASUREMENT_PERIOD_MS == 100
    assert HCSR04_ECHO_SERIES_RESISTOR_OHM == 10_000
    assert HCSR04_ECHO_PULLDOWN_RESISTOR_OHM == 15_000
    assert HCSR04_ECHO_DIVIDER_TOLERANCE_PERCENT == 5
    assert echo_divider_output_mv(5_000) == 3_000
    assert echo_divider_output_mv(5_500) == 3_300


def test_distance_conversion_rounding_and_timeout_boundary():
    with pytest.raises(Hcsr04BringupError, match="positive"):
        echo_pulse_us_to_distance_mm(0)

    assert echo_pulse_us_to_distance_mm(1_000) == 172
    assert echo_pulse_us_to_distance_mm(2_000) == 343
    assert echo_pulse_us_to_distance_mm(10_000) == 1715

    validate_pulse_width_us(29_999)
    with pytest.raises(Hcsr04BringupError, match="timeout boundary"):
        validate_pulse_width_us(30_000)
    with pytest.raises(Hcsr04BringupError, match="timeout"):
        echo_pulse_us_to_distance_mm(30_000)


def test_pulse_width_subtraction_handles_wraparound():
    assert pulse_width_us(100, 350, timer_modulus_us=65_536) == 250
    assert pulse_width_us(65_500, 24, timer_modulus_us=65_536) == 60
    with pytest.raises(Hcsr04BringupError):
        pulse_width_us(1, 2, timer_modulus_us=0)


def test_hcsr04_jsonl_identity_measurement_and_error_schema():
    identity = _record(format_identity_telemetry(sequence=0, timestamp_ms=5))
    measurement = _record(
        format_measurement_telemetry(
            sequence=1,
            timestamp_ms=105,
            measurement=Hcsr04Measurement(echo_pulse_us=2_000),
        )
    )
    error = _record(
        format_error_telemetry(
            sequence=2,
            timestamp_ms=205,
            error=Hcsr04ErrorRecord(
                code=HCSR04_ERROR_ECHO_RISE_TIMEOUT,
                operation="wait_for_echo_rising_edge",
                timeout_us=HCSR04_ECHO_TIMEOUT_US,
            ),
        )
    )

    assert identity["message_type"] == "sensor_identity"
    assert identity["sensor_id"] == "ultrasonic_1"
    assert identity["status"] == "ok"
    assert identity["payload"]["sensor"] == "hc-sr04"
    assert identity["payload"]["trigger_pin"] == "PA5"
    assert identity["payload"]["echo_pin"] == "PA4"
    assert identity["payload"]["timer"] == "TIM6"
    assert identity["payload"]["timer_tick_hz"] == 1_000_000
    assert identity["payload"]["trigger_pulse_us"] == 10
    assert identity["payload"]["echo_timeout_us"] == 30_000
    assert identity["payload"]["measurement_period_ms"] == 100
    assert identity["payload"]["distance_model"] == "nominal_343_m_per_s_uncalibrated"
    assert set(identity["payload"]) == {
        "sensor",
        "connector",
        "trigger_pin",
        "echo_pin",
        "timer",
        "timer_tick_hz",
        "trigger_pulse_us",
        "echo_timeout_us",
        "measurement_period_ms",
        "distance_unit",
        "distance_model",
    }

    assert measurement["message_type"] == "ultrasonic"
    assert measurement["status"] == "ok"
    assert measurement["payload"]["echo_pulse_us"] == 2_000
    assert measurement["payload"]["distance_mm"] == 343
    assert measurement["payload"]["distance_model"] == "nominal_343_m_per_s_uncalibrated"
    assert "error" not in measurement

    assert error["message_type"] == "ultrasonic"
    assert error["status"] == "error"
    assert error["payload"]["echo_pulse_us"] is None
    assert error["payload"]["distance_mm"] is None
    assert error["error"]["code"] == "echo_rise_timeout"
    assert error["error"]["timeout_us"] == 30_000


def test_error_telemetry_rejects_unknown_code_and_never_reuses_stale_distance():
    with pytest.raises(Hcsr04BringupError, match="unknown"):
        format_error_telemetry(
            sequence=1,
            timestamp_ms=1,
            error=Hcsr04ErrorRecord(code="timeout", operation="wait"),
        )

    for code in (
        HCSR04_ERROR_ECHO_NOT_LOW_BEFORE_TRIGGER,
        HCSR04_ERROR_ECHO_RISE_TIMEOUT,
        HCSR04_ERROR_ECHO_FALL_TIMEOUT,
    ):
        record = _record(
            format_error_telemetry(
                sequence=1,
                timestamp_ms=1,
                error=Hcsr04ErrorRecord(code=code, operation="echo_operation", timeout_us=30_000),
            )
        )
        assert record["status"] == "error"
        assert record["payload"]["distance_mm"] is None
        assert record["payload"]["echo_pulse_us"] is None


def test_every_firmware_line_shape_fits_the_shared_512_byte_jsonl_contract():
    lines = [
        format_identity_telemetry(sequence=4_294_967_295, timestamp_ms=4_294_967_295),
        format_measurement_telemetry(
            sequence=4_294_967_295,
            timestamp_ms=4_294_967_295,
            measurement=Hcsr04Measurement(echo_pulse_us=29_999),
        ),
    ]
    lines.extend(
        format_error_telemetry(
            sequence=4_294_967_295,
            timestamp_ms=4_294_967_295,
            error=Hcsr04ErrorRecord(
                code=code,
                operation="wait_for_echo_falling_edge",
                timeout_us=HCSR04_ECHO_TIMEOUT_US,
            ),
        )
        for code in (
            HCSR04_ERROR_ECHO_NOT_LOW_BEFORE_TRIGGER,
            HCSR04_ERROR_ECHO_RISE_TIMEOUT,
            HCSR04_ERROR_ECHO_FALL_TIMEOUT,
            "timer_configuration_failure",
            "timer_measurement_failure",
            "pulse_width_out_of_bounds",
            "telemetry_format_failure",
            "internal_state_error",
        )
    )

    for line in lines:
        assert telemetry_line_bytes(line) <= HCSR04_TELEMETRY_MAX_LINE_BYTES
        validate_telemetry_buffer_capacity(line, HCSR04_FIRMWARE_BUFFER_BYTES)
        validate_telemetry_buffer_capacity(line, telemetry_line_bytes(line) + 1)
        with pytest.raises(Hcsr04BringupError, match="including NUL"):
            validate_telemetry_buffer_capacity(line, telemetry_line_bytes(line))

    board = (BRINGUP_ROOT / "board_config.h").read_text(encoding="utf-8")
    main = (BRINGUP_ROOT / "main_hcsr04_bringup.c").read_text(encoding="utf-8")
    assert "OPENRF1_HCSR04_TELEMETRY_MAX_LINE_BYTES ((uint16_t)512u)" in board
    assert "OPENRF1_HCSR04_TELEMETRY_BUFFER_BYTES ((uint16_t)513u)" in board
    assert "HCSR04_TELEMETRY_FORMAT_FAILURE" in main


def test_firmware_source_tree_is_isolated_to_hcsr04_bringup():
    required = {
        "board_config.h",
        "hcsr04.c",
        "hcsr04.h",
        "main_hcsr04_bringup.c",
        "platform_hcsr04_bringup.c",
        "platform_hcsr04_bringup.h",
        "telemetry_hcsr04_bringup.c",
        "telemetry_hcsr04_bringup.h",
    }
    assert required.issubset({path.name for path in BRINGUP_ROOT.iterdir()})

    combined = "\n".join(path.read_text(encoding="utf-8") for path in BRINGUP_ROOT.glob("*.[ch]"))
    for required_snippet in (
        'OPENRF1_HCSR04_TRIGGER_PIN_TEXT "PA5"',
        'OPENRF1_HCSR04_ECHO_PIN_TEXT "PA4"',
        'OPENRF1_HCSR04_TIMER_TEXT "TIM6"',
        "OPENRF1_HCSR04_TIMER_PRESCALER ((uint16_t)71u)",
        "OPENRF1_HCSR04_TIMER_PERIOD ((uint16_t)30000u)",
        "OPENRF1_HCSR04_TRIGGER_PULSE_US ((uint16_t)10u)",
        "OPENRF1_HCSR04_ECHO_TIMEOUT_US ((uint32_t)30000u)",
        "OPENRF1_HCSR04_MEASUREMENT_PERIOD_MS ((uint32_t)100u)",
        "hcsr04_elapsed_us",
        "HCSR04_RESULT_ECHO_NOT_LOW_BEFORE_TRIGGER",
        "HCSR04_RESULT_ECHO_RISE_TIMEOUT",
        "HCSR04_RESULT_ECHO_FALL_TIMEOUT",
        "OPENRF1_HCSR04_WAIT_POLL_LIMIT",
        'message_type\\":\\"ultrasonic',
    ):
        assert required_snippet in combined

    forbidden = (
        "BH1750",
        "BMP280",
        "MPU6050",
        "RPLIDAR",
        "ESP32",
        "USART2",
        "USART3",
        "I2C",
        "motor",
        "encoder",
        "servo",
    )
    for term in forbidden:
        assert term not in combined


def test_hcsr04_bringup_keil_target_is_isolated_relative_and_has_tim_component():
    text = KEIL_PROJECT.read_text(encoding="utf-8")
    rte_text = RTE_COMPONENTS.read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_HCSR04_Bringup</TargetName>" in text
    assert r"<OutputDirectory>.\Objects_HCSR04_Bringup\</OutputDirectory>" in text
    assert "<OutputName>OpenRF1_HCSR04_Bringup</OutputName>" in text
    assert "<CreateHexFile>1</CreateHexFile>" in text
    assert "<uAC6>1</uAC6>" in text
    assert "STM32F10X_HD,USE_STDPERIPH_DRIVER" in text
    assert "..\\hcsr04_bringup;..\\full_hardware;..\\app" in text
    assert "C:\\Users" not in text
    assert ("Desk" + "top") not in text
    assert "COM" not in text
    assert "Csub=\"TIM\"" in text
    assert "RTE_DEVICE_STDPERIPH_TIM" in rte_text

    included_sources = set(re.findall(r"<FileName>([^<]+)</FileName>", text))
    assert included_sources == {
        "hcsr04.c",
        "main_hcsr04_bringup.c",
        "openrf1_status.c",
        "platform_hcsr04_bringup.c",
        "telemetry_hcsr04_bringup.c",
    }
    for forbidden in ("bh1750.c", "bmp280.c", "mpu6050.c", "soft_i2c.c", "main_full_hardware.c"):
        assert forbidden not in text


def test_documentation_locks_vendor_facts_without_claiming_physical_evidence():
    text = DOC_PATH.read_text(encoding="utf-8")
    lock = HARDWARE_LOCK.read_text(encoding="utf-8")
    combined = text + "\n" + lock

    for snippet in (
        "AUTHORITATIVE_VENDOR_DOCUMENTED",
        "CN6",
        "B4B-PH-K-S(LF)(SN)",
        "pin 1: VCC_5V",
        "pin 2: GND",
        "pin 3: PA5_TRIG",
        "pin 4: PA4_ECHO",
        "TRIG: PA5",
        "ECHO: PA4",
        "TIM6",
        "Do not connect HC-SR04 ECHO directly to CN6 pin 4.",
        "10 kOhm",
        "15 kOhm",
        "PHYSICAL_VERIFICATION_REQUIRED",
        "SOFTWARE_READY",
    ):
        assert snippet in combined

    assert "PA4 is 5-V tolerant" not in combined
    assert "PHYSICAL_EVIDENCE_VERIFIED" not in text
