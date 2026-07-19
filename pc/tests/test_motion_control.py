from __future__ import annotations

import math

import pytest

from rplidar_c1_tools.mecanum_odometry import (
    BodyTwist2D,
    MecanumGeometry,
    WheelAngularVelocities,
    inverse_mecanum_kinematics,
)
from rplidar_c1_tools.motion_control import (
    BodyMotionCommand,
    FourWheelPIDConfiguration,
    MotionCommandLimits,
    MotionControlConfiguration,
    MotionControlState,
    MotionSafetyInputs,
    MotionSafetyPolicy,
    MotionStopReason,
    PIDGains,
    PIDLimits,
    PIDState,
    WheelAccelerationLimits,
    WheelControllerState,
    WheelPIDConfiguration,
    WheelSpeedLimits,
    check_command_watchdog,
    control_four_wheels,
    desaturate_wheel_setpoints,
    evaluate_motion_safety,
    limit_wheel_setpoint_acceleration,
    motion_control_step,
    update_wheel_speed_pid,
    validate_body_motion_command,
    zero_wheel_speeds,
)


def test_body_command_validation_and_explicit_limits():
    command = BodyMotionCommand(0.4, -0.2, 0.3, 10, command_id="one")
    twist = validate_body_motion_command(
        command,
        MotionCommandLimits(0.5, 0.3, 0.4),
    )
    assert twist == BodyTwist2D(0.4, -0.2, 0.3)
    with pytest.raises(ValueError, match="vx_m_s exceeds"):
        validate_body_motion_command(command, MotionCommandLimits(0.3, 0.3, 0.4))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"vx_m_s": math.nan},
        {"vy_m_s": math.inf},
        {"yaw_rate_rad_s": -math.inf},
        {"command_timestamp_ms": -1},
        {"command_id": ""},
        {"source": ""},
        {"motion_requested": 1},
    ],
)
def test_body_command_rejects_invalid_fields(kwargs):
    values = dict(
        vx_m_s=0.0,
        vy_m_s=0.0,
        yaw_rate_rad_s=0.0,
        command_timestamp_ms=0,
    )
    values.update(kwargs)
    with pytest.raises(ValueError):
        BodyMotionCommand(**values)


def test_motion_requested_false_yields_zero_twist():
    command = BodyMotionCommand(1.0, 2.0, 3.0, 0, motion_requested=False)
    assert validate_body_motion_command(command) == BodyTwist2D(0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    ("twist", "expected"),
    [
        (BodyTwist2D(0.4, 0.0, 0.0), (8.0, 8.0, 8.0, 8.0)),
        (BodyTwist2D(0.0, 0.3, 0.0), (-6.0, 6.0, 6.0, -6.0)),
        (BodyTwist2D(0.0, 0.0, 0.5), (-3.4, 3.4, -3.4, 3.4)),
        (BodyTwist2D(0.35, 0.12, 0.4), (1.88, 12.12, 6.68, 7.32)),
    ],
)
def test_phase4a_inverse_kinematics_generates_canonical_targets(twist, expected):
    wheels = inverse_mecanum_kinematics(twist, _geometry())
    assert _values(wheels) == pytest.approx(expected)


def test_desaturation_is_identity_below_limit():
    requested = WheelAngularVelocities(1.0, -2.0, 3.0, -4.0)
    result = desaturate_wheel_setpoints(requested, WheelSpeedLimits(5.0))
    assert result.setpoints is requested
    assert result.desaturated is False
    assert result.scale_factor == 1.0


def test_desaturation_scales_proportionally_and_preserves_signs_and_ratios():
    requested = WheelAngularVelocities(2.0, -4.0, 8.0, -1.0)
    result = desaturate_wheel_setpoints(requested, WheelSpeedLimits(4.0))
    assert result.desaturated is True
    assert result.scale_factor == 0.5
    assert _values(result.setpoints) == pytest.approx((1.0, -2.0, 4.0, -0.5))
    for original, scaled in zip(_values(requested), _values(result.setpoints), strict=True):
        assert scaled / original == pytest.approx(0.5)


@pytest.mark.parametrize("limit", [0.0, -1.0, math.nan, math.inf])
def test_invalid_wheel_speed_limit_is_rejected(limit):
    with pytest.raises(ValueError):
        WheelSpeedLimits(limit)


def test_acceleration_limit_from_rest_and_flags():
    result = limit_wheel_setpoint_acceleration(
        zero_wheel_speeds(),
        WheelAngularVelocities(5.0, -5.0, 0.5, -0.5),
        WheelAccelerationLimits.shared(2.0),
        dt_s=0.5,
    )
    assert _values(result.setpoints) == pytest.approx((1.0, -1.0, 0.5, -0.5))
    assert tuple(value for _, value in result.limited.items) == (True, True, False, False)


def test_acceleration_limit_during_reversal():
    result = limit_wheel_setpoint_acceleration(
        WheelAngularVelocities(2.0, 2.0, 2.0, 2.0),
        WheelAngularVelocities(-2.0, -2.0, -2.0, -2.0),
        WheelAccelerationLimits.shared(5.0),
        dt_s=0.2,
    )
    assert _values(result.setpoints) == pytest.approx((1.0, 1.0, 1.0, 1.0))
    assert result.limited.any_limited


@pytest.mark.parametrize("dt_s", [0.0, -0.1, math.nan, math.inf])
def test_acceleration_limit_rejects_invalid_dt(dt_s):
    with pytest.raises(ValueError):
        limit_wheel_setpoint_acceleration(
            zero_wheel_speeds(),
            zero_wheel_speeds(),
            WheelAccelerationLimits.shared(1.0),
            dt_s=dt_s,
        )


@pytest.mark.parametrize("limit", [0.0, -1.0, math.nan, math.inf])
def test_acceleration_limit_rejects_invalid_magnitude(limit):
    with pytest.raises(ValueError):
        WheelAccelerationLimits.shared(limit)


def test_pid_proportional_only_behavior():
    result = _pid(target=2.0, measured=0.5, gains=PIDGains(0.2, 0.0, 0.0))
    assert result.normalized_effort == pytest.approx(0.3)
    assert result.proportional_term == pytest.approx(0.3)


def test_pid_integral_accumulation():
    state = PIDState()
    first = _pid(target=1.0, measured=0.0, gains=PIDGains(0.0, 0.2, 0.0), state=state)
    second = _pid(target=1.0, measured=0.0, gains=PIDGains(0.0, 0.2, 0.0), state=first.state)
    assert first.state.integral_error_rad == pytest.approx(0.1)
    assert second.state.integral_error_rad == pytest.approx(0.2)
    assert second.normalized_effort == pytest.approx(0.04)


def test_pid_derivative_is_on_measurement():
    result = _pid(
        target=10.0,
        measured=3.0,
        gains=PIDGains(0.0, 0.0, 0.5),
        state=PIDState(previous_measurement_rad_s=1.0),
    )
    assert result.derivative_term == pytest.approx(-10.0)
    assert result.normalized_effort == -1.0


def test_pid_first_sample_derivative_is_deterministically_zero():
    result = _pid(target=1.0, measured=5.0, gains=PIDGains(0.0, 0.0, 1.0))
    assert result.derivative_term == 0.0
    assert result.normalized_effort == 0.0


@pytest.mark.parametrize(
    ("target", "expected"),
    [(100.0, 1.0), (-100.0, -1.0)],
)
def test_pid_output_saturation(target, expected):
    result = _pid(target=target, measured=0.0, gains=PIDGains(1.0, 0.0, 0.0))
    assert result.normalized_effort == expected
    assert result.saturated


@pytest.mark.parametrize("target", [100.0, -100.0])
def test_pid_conditional_anti_windup_bounds_unreachable_demand(target):
    state = PIDState()
    gains = PIDGains(1.0, 1.0, 0.0)
    for _ in range(100):
        result = _pid(target=target, measured=0.0, gains=gains, state=state)
        state = result.state
    assert state.integral_error_rad == 0.0
    assert result.integration_blocked


def test_pid_recovers_after_saturation():
    saturated = _pid(
        target=100.0,
        measured=0.0,
        gains=PIDGains(1.0, 1.0, 0.0),
    )
    recovered = _pid(
        target=0.0,
        measured=0.0,
        gains=PIDGains(1.0, 1.0, 0.0),
        state=saturated.state,
    )
    assert recovered.normalized_effort == 0.0
    assert recovered.state.integral_error_rad == 0.0


def test_pid_disable_resets_state_and_returns_zero():
    result = _pid(
        target=10.0,
        measured=2.0,
        gains=PIDGains(1.0, 1.0, 1.0),
        state=PIDState(3.0, 4.0),
        enabled=False,
    )
    assert result.normalized_effort == 0.0
    assert result.state == PIDState()


def test_pid_reset_is_explicit_fresh_state():
    prior = _pid(target=1.0, measured=0.0, gains=PIDGains(0.0, 1.0, 0.0)).state
    reset = PIDState()
    after_reset = _pid(
        target=0.0,
        measured=0.0,
        gains=PIDGains(0.0, 1.0, 0.0),
        state=reset,
    )
    assert prior != reset
    assert after_reset.state.integral_error_rad == 0.0


def test_pid_rejects_invalid_dt_and_limits():
    with pytest.raises(ValueError, match="dt_s"):
        _pid(target=0.0, measured=0.0, dt_s=0.0)
    with pytest.raises(ValueError, match="output_min"):
        PIDLimits(1.0, 1.0, -1.0, 1.0)
    with pytest.raises(ValueError, match="integral_min"):
        PIDLimits(-1.0, 1.0, 2.0, 1.0)


def test_four_wheel_controller_states_are_independent():
    configuration = FourWheelPIDConfiguration.shared(
        PIDGains(0.0, 1.0, 0.0),
        _pid_limits(),
    )
    result = control_four_wheels(
        targets=WheelAngularVelocities(1.0, 0.0, 0.0, 0.0),
        measurements=zero_wheel_speeds(),
        dt_s=0.1,
        configuration=configuration,
        prior_state=WheelControllerState(),
        enabled=True,
    )
    assert result.state.front_left.integral_error_rad == pytest.approx(0.1)
    assert result.state.front_right.integral_error_rad == 0.0
    assert result.state.rear_left.integral_error_rad == 0.0
    assert result.state.rear_right.integral_error_rad == 0.0


def test_four_wheel_controller_supports_distinct_gains_without_coupling():
    low = WheelPIDConfiguration(PIDGains(0.1, 0.0, 0.0), _pid_limits())
    high = WheelPIDConfiguration(PIDGains(0.2, 0.0, 0.0), _pid_limits())
    configuration = FourWheelPIDConfiguration(low, high, low, high)
    result = control_four_wheels(
        targets=WheelAngularVelocities(1.0, 1.0, 1.0, 1.0),
        measurements=zero_wheel_speeds(),
        dt_s=0.1,
        configuration=configuration,
        prior_state=WheelControllerState(),
        enabled=True,
    )
    assert tuple(value for _, value in result.efforts.items) == pytest.approx(
        (0.1, 0.2, 0.1, 0.2)
    )


def test_watchdog_is_fresh_before_stale_at_and_after_threshold():
    before = check_command_watchdog(
        current_timestamp_ms=1099,
        command_timestamp_ms=1000,
        timeout_ms=100,
    )
    at = check_command_watchdog(
        current_timestamp_ms=1100,
        command_timestamp_ms=1000,
        timeout_ms=100,
    )
    after = check_command_watchdog(
        current_timestamp_ms=1101,
        command_timestamp_ms=1000,
        timeout_ms=100,
    )
    assert (before.stale, at.stale, after.stale) == (False, True, True)


def test_watchdog_rejects_nonmonotonic_timestamps():
    with pytest.raises(ValueError, match="must not precede"):
        check_command_watchdog(
            current_timestamp_ms=9,
            command_timestamp_ms=10,
            timeout_ms=1,
        )


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"ground_edge_hazard": True}, MotionStopReason.GROUND_EDGE),
        ({"ultrasonic_hazard": True}, MotionStopReason.ULTRASONIC_OBSTACLE),
        ({"controller_fault": True}, MotionStopReason.CONTROLLER_FAULT),
        ({"communication_ok": False}, MotionStopReason.COMMUNICATION_FAULT),
        ({"external_stop": True}, MotionStopReason.EXTERNAL_STOP),
        ({"critical_sensor_valid": False}, MotionStopReason.CRITICAL_SENSOR_INVALID),
    ],
)
def test_safety_stop_conditions(changes, reason):
    inputs = _safety_inputs(**changes)
    decision = evaluate_motion_safety(inputs, MotionSafetyPolicy(100))
    assert decision.stop_reason is reason
    assert decision.forced_stop
    assert decision.targets_replaced_with_zero


def test_emergency_stop_has_precedence_over_every_other_condition():
    decision = evaluate_motion_safety(
        _safety_inputs(
            emergency_stop=True,
            command_age_ms=1000,
            communication_ok=False,
            ground_edge_hazard=True,
            ultrasonic_hazard=True,
            controller_fault=True,
        ),
        MotionSafetyPolicy(100),
    )
    assert decision.stop_reason is MotionStopReason.EMERGENCY_STOP


def test_policy_can_deliberately_make_noncritical_unavailability_nonfatal():
    inputs = _safety_inputs(
        communication_ok=False,
        ground_edge_hazard=True,
        ultrasonic_hazard=True,
        critical_sensor_valid=False,
    )
    policy = MotionSafetyPolicy(
        100,
        stop_on_communication_fault=False,
        stop_on_ground_edge=False,
        stop_on_ultrasonic_hazard=False,
        stop_on_critical_sensor_invalid=False,
    )
    assert evaluate_motion_safety(inputs, policy).permit_motion


def test_pipeline_forced_stop_zeros_targets_efforts_and_controller_state():
    active_snapshot, active_state = motion_control_step(
        command=BodyMotionCommand(0.4, 0.0, 0.0, 0),
        measurements=zero_wheel_speeds(),
        safety_inputs=_safety_inputs(),
        dt_s=0.1,
        configuration=_control_configuration(),
        prior_state=MotionControlState(),
    )
    assert any(value != 0.0 for _, value in active_snapshot.control_efforts.items)
    stopped_snapshot, stopped_state = motion_control_step(
        command=BodyMotionCommand(0.4, 0.0, 0.0, 100),
        measurements=zero_wheel_speeds(),
        safety_inputs=_safety_inputs(emergency_stop=True),
        dt_s=0.1,
        configuration=_control_configuration(),
        prior_state=active_state,
    )
    assert stopped_snapshot.applied_wheel_setpoints == zero_wheel_speeds()
    assert tuple(value for _, value in stopped_snapshot.control_efforts.items) == (0.0,) * 4
    assert stopped_state == MotionControlState()


def test_pipeline_restart_after_forced_stop_is_deterministic():
    configuration = _control_configuration()
    command = BodyMotionCommand(0.4, 0.0, 0.0, 0)
    first, first_state = motion_control_step(
        command=command,
        measurements=zero_wheel_speeds(),
        safety_inputs=_safety_inputs(),
        dt_s=0.1,
        configuration=configuration,
        prior_state=MotionControlState(),
    )
    _, stopped_state = motion_control_step(
        command=BodyMotionCommand(0.4, 0.0, 0.0, 100),
        measurements=zero_wheel_speeds(),
        safety_inputs=_safety_inputs(ground_edge_hazard=True),
        dt_s=0.1,
        configuration=configuration,
        prior_state=first_state,
    )
    restarted, _ = motion_control_step(
        command=BodyMotionCommand(0.4, 0.0, 0.0, 200),
        measurements=zero_wheel_speeds(),
        safety_inputs=_safety_inputs(),
        dt_s=0.1,
        configuration=configuration,
        prior_state=stopped_state,
    )
    assert restarted.applied_wheel_setpoints == first.applied_wheel_setpoints
    assert restarted.control_efforts == first.control_efforts


def _geometry() -> MecanumGeometry:
    # Explicit synthetic fixture, not measured rover geometry.
    return MecanumGeometry(0.05, 0.18, 0.16)


def _pid_limits() -> PIDLimits:
    return PIDLimits(-1.0, 1.0, -2.0, 2.0)


def _pid(
    *,
    target: float,
    measured: float,
    gains: PIDGains | None = None,
    state: PIDState | None = None,
    dt_s: float = 0.1,
    enabled: bool = True,
):
    return update_wheel_speed_pid(
        target_rad_s=target,
        measured_rad_s=measured,
        dt_s=dt_s,
        gains=gains or PIDGains(0.0, 0.0, 0.0),
        limits=_pid_limits(),
        prior_state=state or PIDState(),
        enabled=enabled,
    )


def _safety_inputs(**changes) -> MotionSafetyInputs:
    values = dict(
        control_enabled=True,
        emergency_stop=False,
        command_age_ms=0,
        communication_ok=True,
        ground_edge_hazard=False,
        ultrasonic_hazard=False,
        critical_sensor_valid=True,
        controller_fault=False,
        external_stop=False,
    )
    values.update(changes)
    return MotionSafetyInputs(**values)


def _control_configuration() -> MotionControlConfiguration:
    return MotionControlConfiguration(
        geometry=_geometry(),
        wheel_speed_limits=WheelSpeedLimits(20.0),
        wheel_acceleration_limits=WheelAccelerationLimits.shared(10.0),
        wheel_pid=FourWheelPIDConfiguration.shared(
            PIDGains(0.1, 0.05, 0.0),
            _pid_limits(),
        ),
        safety_policy=MotionSafetyPolicy(100),
    )


def _values(wheels: WheelAngularVelocities) -> tuple[float, float, float, float]:
    return (
        wheels.front_left_rad_s,
        wheels.front_right_rad_s,
        wheels.rear_left_rad_s,
        wheels.rear_right_rad_s,
    )
