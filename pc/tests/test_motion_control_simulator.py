from __future__ import annotations

import json

import pytest

from rplidar_c1_tools.mecanum_odometry import MecanumGeometry
from rplidar_c1_tools.motion_control import (
    FourWheelPIDConfiguration,
    MotionControlConfiguration,
    MotionSafetyPolicy,
    MotionStopReason,
    PIDGains,
    PIDLimits,
    WheelAccelerationLimits,
    WheelSpeedLimits,
)
from rplidar_c1_tools.motion_control_simulator import (
    MOTION_CONTROL_SCENARIOS,
    SYNTHETIC_CONTROL_ORIGIN,
    SyntheticWheelPlantParameters,
    SyntheticWheelPlantWheelParameters,
    generate_motion_control_samples,
    generate_motion_control_telemetry_lines,
)
from rplidar_c1_tools.replay import inspect_recording, iter_recording_entries
from rplidar_c1_tools.stm32_recording_bridge import record_stm32_telemetry_stream
from rplidar_c1_tools.stm32_sensor_protocol import iter_stm32_telemetry


def test_stationary_simulator_remains_stationary():
    samples = _samples("stationary")
    assert all(_values(sample.synthetic_measured_wheel_speeds) == (0.0,) * 4 for sample in samples)
    assert samples[-1].synthetic_pose.x_m == 0.0
    assert samples[-1].synthetic_pose.y_m == 0.0
    assert samples[-1].synthetic_pose.yaw_rad == 0.0


def test_forward_closed_loop_simulator_has_forward_wheels_and_twist():
    final = _samples("forward", steps=30)[-1]
    assert all(value > 0.0 for value in _values(final.synthetic_measured_wheel_speeds))
    assert final.estimated_body_twist.vx_m_s > 0.0
    assert abs(final.estimated_body_twist.vy_m_s) < 1e-12


def test_left_strafe_closed_loop_simulator_preserves_sign_pattern():
    final = _samples("left_strafe", steps=30)[-1]
    fl, fr, rl, rr = _values(final.synthetic_measured_wheel_speeds)
    assert (fl < 0.0, fr > 0.0, rl > 0.0, rr < 0.0) == (True,) * 4
    assert final.estimated_body_twist.vy_m_s > 0.0


def test_rotation_closed_loop_simulator_preserves_sign_pattern():
    final = _samples("counterclockwise_rotation", steps=30)[-1]
    fl, fr, rl, rr = _values(final.synthetic_measured_wheel_speeds)
    assert (fl < 0.0, fr > 0.0, rl < 0.0, rr > 0.0) == (True,) * 4
    assert final.estimated_body_twist.yaw_rate_rad_s > 0.0


def test_combined_motion_simulator_generates_pose_and_mixed_wheels():
    final = _samples("combined_curved_motion", steps=30)[-1]
    assert len({round(value, 6) for value in _values(final.synthetic_measured_wheel_speeds)}) > 2
    assert final.synthetic_pose.x_m > 0.0
    assert final.synthetic_pose.yaw_rad > 0.0


def test_desaturation_scenario_exposes_proportional_scaling():
    samples = _samples("command_desaturation", steps=3)
    assert all(sample.snapshot.desaturation.desaturated for sample in samples)
    assert all(sample.snapshot.desaturation.scale_factor < 1.0 for sample in samples)


def test_acceleration_limited_transition_exposes_rate_limit_flags():
    samples = _samples("acceleration_limited_transition", steps=9)
    assert any(sample.snapshot.acceleration_limit.limited.any_limited for sample in samples)


@pytest.mark.parametrize(
    ("scenario", "reason"),
    [
        ("stale_command_watchdog_stop", MotionStopReason.STALE_COMMAND),
        ("emergency_stop", MotionStopReason.EMERGENCY_STOP),
        ("ground_edge_forced_stop", MotionStopReason.GROUND_EDGE),
        ("ultrasonic_forced_stop", MotionStopReason.ULTRASONIC_OBSTACLE),
    ],
)
def test_safety_stop_scenarios_force_zero_targets_and_efforts(scenario, reason):
    samples = _samples(scenario, steps=8)
    stopped = [sample for sample in samples if sample.snapshot.safety_decision.forced_stop]
    assert stopped
    assert stopped[-1].snapshot.safety_decision.stop_reason is reason
    assert _values(stopped[-1].snapshot.applied_wheel_setpoints) == (0.0,) * 4
    assert tuple(value for _, value in stopped[-1].snapshot.control_efforts.items) == (0.0,) * 4


def test_synthetic_slow_wheel_parameter_creates_mismatch():
    shared = SyntheticWheelPlantWheelParameters(20.0, 0.1)
    plant = SyntheticWheelPlantParameters(
        front_left=SyntheticWheelPlantWheelParameters(20.0, 1.0),
        front_right=shared,
        rear_left=shared,
        rear_right=shared,
    )
    final = generate_motion_control_samples(
        configuration=_configuration(),
        plant_parameters=plant,
        scenario="slow_front_left_wheel",
        step_count=8,
        interval_ms=100,
    )[-1]
    fl, fr, rl, rr = _values(final.synthetic_measured_wheel_speeds)
    assert fl < min(fr, rl, rr)


def test_slow_wheel_scenario_requires_explicitly_slower_front_left_plant():
    with pytest.raises(ValueError, match="explicitly larger synthetic"):
        generate_motion_control_samples(
            configuration=_configuration(),
            plant_parameters=_plant(),
            scenario="slow_front_left_wheel",
            step_count=2,
            interval_ms=100,
        )


def test_simulator_is_reproducible():
    first = _samples("combined_curved_motion", steps=10)
    second = _samples("combined_curved_motion", steps=10)
    assert first == second


def test_all_required_scenarios_are_available():
    assert set(MOTION_CONTROL_SCENARIOS) == {
        "stationary",
        "forward",
        "left_strafe",
        "counterclockwise_rotation",
        "combined_curved_motion",
        "command_desaturation",
        "acceleration_limited_transition",
        "stale_command_watchdog_stop",
        "emergency_stop",
        "ground_edge_forced_stop",
        "ultrasonic_forced_stop",
        "slow_front_left_wheel",
    }


def test_jsonl_round_trip_has_six_backward_compatible_v1_messages_per_step():
    lines = generate_motion_control_telemetry_lines(
        configuration=_configuration(),
        plant_parameters=_plant(),
        scenario="forward",
        step_count=3,
        interval_ms=100,
    )
    messages = list(iter_stm32_telemetry(line + "\n" for line in lines))
    assert len(messages) == 18
    assert {message.message_type for message in messages} == {
        "body_motion_command",
        "wheel_speed_setpoint",
        "wheel_speed_measurement",
        "wheel_control_effort",
        "motion_safety_state",
        "motion_control_snapshot",
    }
    assert all(message.version == 1 for message in messages)
    assert all(message.status == "software_derived" for message in messages)
    assert all(message.payload["origin"] == SYNTHETIC_CONTROL_ORIGIN for message in messages)
    assert all(json.loads(line)["version"] == 1 for line in lines)


def test_recording_conversion_and_inspection_preserve_phase4b_records(tmp_path):
    telemetry_lines = generate_motion_control_telemetry_lines(
        configuration=_configuration(),
        plant_parameters=_plant(),
        scenario="left_strafe",
        step_count=2,
        interval_ms=100,
    )
    output = tmp_path / "motion_recording.jsonl"
    record_stm32_telemetry_stream(
        (line + "\n" for line in telemetry_lines),
        output,
    )
    entries = list(iter_recording_entries(output))
    record_types = [entry.payload["record_type"] for entry in entries[1:]]
    assert record_types == [
        "body_motion_command",
        "wheel_speed_setpoint",
        "wheel_speed_measurement",
        "wheel_control_effort",
        "motion_safety_state",
        "motion_control_snapshot",
    ] * 2
    assert entries[1].payload["origin"] == SYNTHETIC_CONTROL_ORIGIN
    assert "motion_control_snapshot: 2" in inspect_recording(output).to_text()


def _configuration() -> MotionControlConfiguration:
    # All values are explicit synthetic fixtures, not physical rover values.
    return MotionControlConfiguration(
        geometry=MecanumGeometry(0.05, 0.18, 0.16),
        wheel_speed_limits=WheelSpeedLimits(20.0),
        wheel_acceleration_limits=WheelAccelerationLimits.shared(10.0),
        wheel_pid=FourWheelPIDConfiguration.shared(
            PIDGains(0.05, 0.02, 0.0),
            PIDLimits(-1.0, 1.0, -2.0, 2.0),
        ),
        safety_policy=MotionSafetyPolicy(command_timeout_ms=250),
    )


def _plant() -> SyntheticWheelPlantParameters:
    return SyntheticWheelPlantParameters.shared(
        gain_rad_s_per_normalized_effort=20.0,
        time_constant_s=0.2,
    )


def _samples(scenario: str, *, steps: int = 12):
    return generate_motion_control_samples(
        configuration=_configuration(),
        plant_parameters=_plant(),
        scenario=scenario,
        step_count=steps,
        interval_ms=100,
    )


def _values(wheels) -> tuple[float, float, float, float]:
    return (
        wheels.front_left_rad_s,
        wheels.front_right_rad_s,
        wheels.rear_left_rad_s,
        wheels.rear_right_rad_s,
    )
