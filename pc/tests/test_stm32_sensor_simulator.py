from __future__ import annotations

from rplidar_c1_tools.stm32_sensor_protocol import parse_stm32_telemetry_line
from rplidar_c1_tools.stm32_sensor_simulator import (
    generate_synthetic_stm32_lines,
    generate_synthetic_stm32_session,
)


def test_simulator_output_is_deterministic_and_covers_all_phase31_sensors():
    first = generate_synthetic_stm32_lines(cycles=2, scenario="nominal")
    second = generate_synthetic_stm32_lines(cycles=2, scenario="nominal")

    assert first == second
    messages = [parse_stm32_telemetry_line(line) for line in first]
    assert [message.sequence for message in messages] == list(range(16))
    assert [message.timestamp_ms for message in messages[:8]] == [0] * 8
    assert [message.timestamp_ms for message in messages[8:]] == [100] * 8
    assert {message.sensor_id for message in messages} == {
        "ultrasonic_1",
        "ultrasonic_2",
        "ultrasonic_3",
        "tcrt5000_1",
        "tcrt5000_2",
        "hall_1",
        "bh1750_1",
        "bmp280_1",
    }


def test_simulator_fault_scenarios_are_stable_and_explicit():
    timeout_messages = generate_synthetic_stm32_session(
        cycles=1,
        scenario="ultrasonic_timeout",
    )
    timeout = [message for message in timeout_messages if message.status == "timeout"]
    assert len(timeout) == 1
    assert timeout[0].sensor_id == "ultrasonic_2"
    assert "distance_mm" not in timeout[0].payload

    mixed = generate_synthetic_stm32_session(cycles=1, scenario="mixed_faults")
    ground = [message for message in mixed if message.message_type == "ground_edge"]
    hall = [message for message in mixed if message.message_type == "hall_landmark"][0]
    assert all(message.payload["polarity_verified"] is False for message in ground)
    assert hall.payload["polarity_verified"] is False
    assert any(message.status == "not_initialized" for message in mixed)


def test_environment_change_scenario_changes_environment_values():
    messages = generate_synthetic_stm32_session(cycles=2, scenario="environment_change")
    lux_values = [
        message.payload["illuminance_lux"]
        for message in messages
        if message.message_type == "illuminance"
    ]
    pressure_values = [
        message.payload["pressure_pa"]
        for message in messages
        if message.message_type == "barometer"
    ]

    assert lux_values == [320.0, 335.0]
    assert pressure_values == [101_325.0, 101_300.0]

