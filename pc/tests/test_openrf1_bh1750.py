from __future__ import annotations

import pytest

from rplidar_c1_tools.openrf1_bh1750 import (
    BH1750_ONE_TIME_HIGH_RESOLUTION_MODE,
    OPENRF1_BH1750_ADDRESS_7BIT,
    OPENRF1_BH1750_SENSOR_ID,
    Bh1750Controller,
    OpenRf1Bh1750Error,
    OpenRf1BoardConfig,
    bh1750_raw_count_from_bytes,
    bh1750_raw_count_to_centilux,
    bh1750_raw_count_to_lux,
    bh1750_read_address_byte,
    bh1750_write_address_byte,
    format_bh1750_telemetry_line,
    generate_bh1750_telemetry_lines,
)
from rplidar_c1_tools.stm32_sensor_protocol import iter_stm32_telemetry, parse_stm32_telemetry_line


def test_openrf1_board_config_locks_confirmed_phase32a_facts():
    config = OpenRf1BoardConfig()

    assert config.board_name == "OpenRF1"
    assert config.mcu == "STM32F103RCT6"
    assert config.sensor_id == OPENRF1_BH1750_SENSOR_ID
    assert config.scl_port == "GPIOB"
    assert config.scl_pin == "GPIO_Pin_1"
    assert config.sda_port == "GPIOC"
    assert config.sda_pin == "GPIO_Pin_3"
    assert config.bh1750_address_7bit == 0x23
    assert config.uart == "USART1"
    assert config.uart_tx_pin == "PA9"
    assert config.uart_rx_pin == "PA10"
    assert config.uart_baud == 115200


def test_bh1750_address_derivation_keeps_public_address_7bit():
    assert OPENRF1_BH1750_ADDRESS_7BIT == 0x23
    assert bh1750_write_address_byte() == 0x46
    assert bh1750_read_address_byte() == 0x47
    assert BH1750_ONE_TIME_HIGH_RESOLUTION_MODE == 0x20

    with pytest.raises(OpenRf1Bh1750Error, match="7 bits"):
        bh1750_write_address_byte(0x80)


def test_raw_bytes_and_lux_conversion_are_deterministic():
    assert bh1750_raw_count_from_bytes(0x12, 0x34) == 0x1234
    assert bh1750_raw_count_to_centilux(0) == 0
    assert bh1750_raw_count_to_lux(0) == 0.0
    assert bh1750_raw_count_to_centilux(12) == 1000
    assert bh1750_raw_count_to_lux(12) == 10.0
    assert bh1750_raw_count_to_centilux(0xFFFF) == 5_461_250

    with pytest.raises(OpenRf1Bh1750Error, match="byte"):
        bh1750_raw_count_from_bytes(256, 0)
    with pytest.raises(OpenRf1Bh1750Error, match="16-bit"):
        bh1750_raw_count_to_centilux(0x1_0000)


def test_nonblocking_state_machine_waits_for_measurement_without_busy_delay():
    starts = 0
    reads = 0

    def start_measurement() -> str:
        nonlocal starts
        starts += 1
        return "ok"

    def read_raw_count() -> tuple[str, int | None]:
        nonlocal reads
        reads += 1
        return ("ok", 12)

    controller = Bh1750Controller(measurement_time_ms=180, period_ms=500)

    assert controller.step(0, start_measurement=start_measurement, read_raw_count=read_raw_count) is None
    assert starts == 1
    assert reads == 0
    assert controller.state == "WAIT_MEASUREMENT"
    assert controller.step(100, start_measurement=start_measurement, read_raw_count=read_raw_count) is None

    sample = controller.step(180, start_measurement=start_measurement, read_raw_count=read_raw_count)

    assert sample is not None
    assert sample.status == "ok"
    assert sample.illuminance_centilux == 1000
    assert sample.illuminance_lux == 10.0
    assert controller.next_action_ms == 500


def test_state_machine_errors_do_not_substitute_zero_lux():
    controller = Bh1750Controller(measurement_time_ms=10, period_ms=20, retry_backoff_ms=50)
    sample = controller.step(
        0,
        start_measurement=lambda: "timeout",
        read_raw_count=lambda: ("ok", 0),
    )

    assert sample is not None
    assert sample.status == "timeout"
    assert sample.illuminance_centilux is None
    assert sample.illuminance_lux is None
    assert controller.state == "RETRY_BACKOFF"
    assert controller.next_action_ms == 50


def test_bh1750_telemetry_format_round_trips_with_phase31_parser():
    line = format_bh1750_telemetry_line(
        sequence=3,
        timestamp_ms=1000,
        status="ok",
        illuminance_centilux=12_345,
    )
    message = parse_stm32_telemetry_line(line)

    assert message.sequence == 3
    assert message.timestamp_ms == 1000
    assert message.message_type == "illuminance"
    assert message.sensor_id == "bh1750_1"
    assert message.payload["illuminance_lux"] == 123.45


def test_bh1750_fault_telemetry_uses_null_not_zero_lux():
    line = format_bh1750_telemetry_line(
        sequence=4,
        timestamp_ms=1500,
        status="hardware_fault",
        illuminance_centilux=None,
    )
    message = parse_stm32_telemetry_line(line)

    assert message.status == "hardware_fault"
    assert message.payload["illuminance_lux"] is None


def test_deterministic_bh1750_generator_is_stream_valid():
    first = generate_bh1750_telemetry_lines(samples=3)
    second = generate_bh1750_telemetry_lines(samples=3)

    assert first == second
    messages = list(iter_stm32_telemetry(first))
    assert [message.sequence for message in messages] == [0, 1, 2]
    assert {message.sensor_id for message in messages} == {"bh1750_1"}
