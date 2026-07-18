from __future__ import annotations

import math

import pytest

from rplidar_c1_tools.mecanum_odometry import (
    BodyTwist2D,
    EncoderConfiguration,
    MecanumGeometry,
    Pose2D,
    WheelAngularVelocities,
    WheelCountDeltas,
    apply_encoder_direction_multipliers,
    count_delta_to_wheel_angular_displacement_rad,
    count_delta_to_wheel_angular_velocity_rad_s,
    encoder_counter_delta,
    forward_mecanum_kinematics,
    integrate_constant_body_twist,
    inverse_mecanum_kinematics,
    normalize_yaw_rad,
    wheel_count_deltas_to_angular_velocities,
)


SYNTHETIC_GEOMETRY = MecanumGeometry(
    wheel_radius_m=0.05,
    half_length_m=0.20,
    half_width_m=0.15,
)
SYNTHETIC_ENCODERS = EncoderConfiguration(
    counts_per_wheel_revolution=2048.0,
    front_left_direction=1,
    front_right_direction=1,
    rear_left_direction=1,
    rear_right_direction=1,
)


@pytest.mark.parametrize(
    ("twist", "expected"),
    [
        (BodyTwist2D(0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.0)),
        (BodyTwist2D(0.5, 0.0, 0.0), (10.0, 10.0, 10.0, 10.0)),
        (BodyTwist2D(0.0, 0.5, 0.0), (-10.0, 10.0, 10.0, -10.0)),
        (BodyTwist2D(0.0, 0.0, 1.0), (-7.0, 7.0, -7.0, 7.0)),
    ],
)
def test_inverse_kinematics_canonical_motions(
    twist: BodyTwist2D,
    expected: tuple[float, float, float, float],
):
    wheels = inverse_mecanum_kinematics(twist, SYNTHETIC_GEOMETRY)
    assert _wheel_tuple(wheels) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("wheels", "expected"),
    [
        (WheelAngularVelocities(0.0, 0.0, 0.0, 0.0), BodyTwist2D(0.0, 0.0, 0.0)),
        (WheelAngularVelocities(10.0, 10.0, 10.0, 10.0), BodyTwist2D(0.5, 0.0, 0.0)),
        (WheelAngularVelocities(-10.0, 10.0, 10.0, -10.0), BodyTwist2D(0.0, 0.5, 0.0)),
        (WheelAngularVelocities(-7.0, 7.0, -7.0, 7.0), BodyTwist2D(0.0, 0.0, 1.0)),
    ],
)
def test_forward_kinematics_canonical_motions(
    wheels: WheelAngularVelocities,
    expected: BodyTwist2D,
):
    twist = forward_mecanum_kinematics(wheels, SYNTHETIC_GEOMETRY)
    assert _twist_tuple(twist) == pytest.approx(_twist_tuple(expected))


@pytest.mark.parametrize(
    "twist",
    [
        BodyTwist2D(0.0, 0.0, 0.0),
        BodyTwist2D(0.4, -0.2, 0.7),
        BodyTwist2D(-0.3, 0.5, -1.1),
    ],
)
def test_forward_inverse_round_trip(twist: BodyTwist2D):
    reconstructed = forward_mecanum_kinematics(
        inverse_mecanum_kinematics(twist, SYNTHETIC_GEOMETRY),
        SYNTHETIC_GEOMETRY,
    )
    assert _twist_tuple(reconstructed) == pytest.approx(_twist_tuple(twist), abs=1.0e-12)


def test_encoder_count_conversion_uses_wheel_side_counts_per_revolution():
    displacement = count_delta_to_wheel_angular_displacement_rad(
        512,
        counts_per_wheel_revolution=2048.0,
        direction_multiplier=1,
    )
    velocity = count_delta_to_wheel_angular_velocity_rad_s(
        512,
        dt_s=0.5,
        counts_per_wheel_revolution=2048.0,
        direction_multiplier=-1,
    )
    assert displacement == pytest.approx(math.pi / 2.0)
    assert velocity == pytest.approx(-math.pi)


def test_explicit_direction_multipliers_apply_independently():
    configuration = EncoderConfiguration(2048.0, 1, -1, -1, 1)
    raw = WheelCountDeltas(1, 2, -3, -4)
    signed = apply_encoder_direction_multipliers(raw, configuration)
    velocities = wheel_count_deltas_to_angular_velocities(raw, configuration, dt_s=0.25)
    assert signed == WheelCountDeltas(1, -2, 3, -4)
    scale = math.tau / 2048.0 / 0.25
    assert _wheel_tuple(velocities) == pytest.approx((scale, -2 * scale, 3 * scale, -4 * scale))


def test_counter_wrap_is_applied_only_with_explicit_width():
    assert encoder_counter_delta(65_534, 1) == -65_533
    assert encoder_counter_delta(65_534, 1, counter_width_bits=16) == 3
    assert encoder_counter_delta(1, 65_534, counter_width_bits=16) == -3


@pytest.mark.parametrize(
    "kwargs",
    [
        {"wheel_radius_m": 0.0, "half_length_m": 0.2, "half_width_m": 0.15},
        {"wheel_radius_m": 0.05, "half_length_m": -0.2, "half_width_m": 0.15},
        {"wheel_radius_m": 0.05, "half_length_m": 0.2, "half_width_m": math.inf},
        {"wheel_radius_m": math.nan, "half_length_m": 0.2, "half_width_m": 0.15},
    ],
)
def test_invalid_geometry_is_rejected(kwargs: dict[str, float]):
    with pytest.raises(ValueError):
        MecanumGeometry(**kwargs)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: EncoderConfiguration(0.0, 1, 1, 1, 1),
        lambda: EncoderConfiguration(math.nan, 1, 1, 1, 1),
        lambda: EncoderConfiguration(2048.0, 0, 1, 1, 1),
        lambda: EncoderConfiguration(2048.0, True, 1, 1, 1),
        lambda: EncoderConfiguration(2048.0, 1, 1, 1, 1, counter_width_bits=0),
    ],
)
def test_invalid_encoder_configuration_is_rejected(factory):
    with pytest.raises(ValueError):
        factory()


@pytest.mark.parametrize("dt_s", [0.0, -0.1, math.nan, math.inf])
def test_invalid_time_intervals_are_rejected(dt_s: float):
    with pytest.raises(ValueError, match="dt_s"):
        count_delta_to_wheel_angular_velocity_rad_s(
            1,
            dt_s=dt_s,
            counts_per_wheel_revolution=2048.0,
            direction_multiplier=1,
        )
    with pytest.raises(ValueError, match="dt_s"):
        integrate_constant_body_twist(
            Pose2D(0.0, 0.0, 0.0),
            BodyTwist2D(0.0, 0.0, 0.0),
            dt_s=dt_s,
        )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_kinematic_inputs_are_rejected(value: float):
    with pytest.raises(ValueError):
        BodyTwist2D(value, 0.0, 0.0)
    with pytest.raises(ValueError):
        WheelAngularVelocities(0.0, value, 0.0, 0.0)
    with pytest.raises(ValueError):
        Pose2D(0.0, 0.0, value)


def test_stationary_twist_preserves_pose():
    pose = Pose2D(1.0, -2.0, 0.25)
    assert integrate_constant_body_twist(
        pose,
        BodyTwist2D(0.0, 0.0, 0.0),
        dt_s=0.5,
    ) == pose


def test_forward_motion_follows_nonzero_initial_heading():
    updated = integrate_constant_body_twist(
        Pose2D(1.0, 2.0, math.pi / 2.0),
        BodyTwist2D(1.0, 0.0, 0.0),
        dt_s=2.0,
    )
    assert (updated.x_m, updated.y_m, updated.yaw_rad) == pytest.approx(
        (1.0, 4.0, math.pi / 2.0)
    )


def test_left_strafe_follows_rover_positive_body_y():
    updated = integrate_constant_body_twist(
        Pose2D(0.0, 0.0, 0.0),
        BodyTwist2D(0.0, 0.5, 0.0),
        dt_s=2.0,
    )
    assert (updated.x_m, updated.y_m, updated.yaw_rad) == pytest.approx((0.0, 1.0, 0.0))


def test_counterclockwise_rotation_increases_yaw():
    updated = integrate_constant_body_twist(
        Pose2D(0.0, 0.0, 0.0),
        BodyTwist2D(0.0, 0.0, 0.5),
        dt_s=2.0,
    )
    assert updated == Pose2D(0.0, 0.0, 1.0)


def test_combined_motion_uses_exact_constant_twist_exponential():
    updated = integrate_constant_body_twist(
        Pose2D(0.0, 0.0, 0.0),
        BodyTwist2D(1.0, 0.0, 1.0),
        dt_s=math.pi / 2.0,
    )
    assert (updated.x_m, updated.y_m, updated.yaw_rad) == pytest.approx(
        (1.0, 1.0, math.pi / 2.0),
        abs=1.0e-12,
    )


def test_near_zero_yaw_rate_branch_is_numerically_stable():
    updated = integrate_constant_body_twist(
        Pose2D(0.0, 0.0, 0.0),
        BodyTwist2D(1.0, 2.0, 1.0e-12),
        dt_s=1.0,
    )
    assert (updated.x_m, updated.y_m, updated.yaw_rad) == pytest.approx(
        (1.0, 2.0, 1.0e-12),
        abs=2.0e-12,
    )


def test_yaw_normalization_is_half_open_and_used_by_integration():
    assert normalize_yaw_rad(math.pi) == pytest.approx(-math.pi)
    assert normalize_yaw_rad(-math.pi) == -math.pi
    updated = integrate_constant_body_twist(
        Pose2D(0.0, 0.0, 3.0),
        BodyTwist2D(0.0, 0.0, 1.0),
        dt_s=1.0,
    )
    assert -math.pi <= updated.yaw_rad < math.pi
    assert updated.yaw_rad == pytest.approx(4.0 - math.tau)


def test_invalid_counter_samples_and_width_are_rejected():
    with pytest.raises(ValueError):
        encoder_counter_delta(0, 1, counter_width_bits=0)
    with pytest.raises(ValueError, match="outside"):
        encoder_counter_delta(256, 0, counter_width_bits=8)
    with pytest.raises(ValueError, match="integer"):
        encoder_counter_delta(0, True)


def _wheel_tuple(wheels: WheelAngularVelocities) -> tuple[float, float, float, float]:
    return (
        wheels.front_left_rad_s,
        wheels.front_right_rad_s,
        wheels.rear_left_rad_s,
        wheels.rear_right_rad_s,
    )


def _twist_tuple(twist: BodyTwist2D) -> tuple[float, float, float]:
    return (twist.vx_m_s, twist.vy_m_s, twist.yaw_rate_rad_s)
