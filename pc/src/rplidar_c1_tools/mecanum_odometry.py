"""Pure Phase 4A mecanum kinematics, encoder conversion, and odometry."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class MecanumGeometry:
    """Explicit X-layout geometry; values are not physical rover defaults."""

    wheel_radius_m: float
    half_length_m: float
    half_width_m: float

    def __post_init__(self) -> None:
        _require_positive_finite(self.wheel_radius_m, "wheel_radius_m")
        _require_positive_finite(self.half_length_m, "half_length_m")
        _require_positive_finite(self.half_width_m, "half_width_m")

    @property
    def rotation_lever_arm_m(self) -> float:
        """Return ``half_length_m + half_width_m``."""
        return self.half_length_m + self.half_width_m


@dataclass(frozen=True, slots=True)
class EncoderConfiguration:
    """Wheel-side encoder resolution and explicit raw-to-mathematical signs."""

    counts_per_wheel_revolution: float
    front_left_direction: int
    front_right_direction: int
    rear_left_direction: int
    rear_right_direction: int
    counter_width_bits: int | None = None

    def __post_init__(self) -> None:
        _require_positive_finite(
            self.counts_per_wheel_revolution,
            "counts_per_wheel_revolution",
        )
        for name, value in self.direction_multipliers:
            _require_direction_multiplier(value, name)
        if self.counter_width_bits is not None:
            _require_positive_int(self.counter_width_bits, "counter_width_bits")

    @property
    def direction_multipliers(self) -> tuple[tuple[str, int], ...]:
        return (
            ("front_left_direction", self.front_left_direction),
            ("front_right_direction", self.front_right_direction),
            ("rear_left_direction", self.rear_left_direction),
            ("rear_right_direction", self.rear_right_direction),
        )


@dataclass(frozen=True, slots=True)
class WheelAngularVelocities:
    """Mathematical wheel angular velocities in rad/s."""

    front_left_rad_s: float
    front_right_rad_s: float
    rear_left_rad_s: float
    rear_right_rad_s: float

    def __post_init__(self) -> None:
        _validate_finite_fields(
            (
                ("front_left_rad_s", self.front_left_rad_s),
                ("front_right_rad_s", self.front_right_rad_s),
                ("rear_left_rad_s", self.rear_left_rad_s),
                ("rear_right_rad_s", self.rear_right_rad_s),
            )
        )


@dataclass(frozen=True, slots=True)
class WheelCountDeltas:
    """Four signed encoder-count deltas in neutral wheel order."""

    front_left_count_delta: int
    front_right_count_delta: int
    rear_left_count_delta: int
    rear_right_count_delta: int

    def __post_init__(self) -> None:
        for name, value in self.items:
            _require_int(value, name)

    @property
    def items(self) -> tuple[tuple[str, int], ...]:
        return (
            ("front_left_count_delta", self.front_left_count_delta),
            ("front_right_count_delta", self.front_right_count_delta),
            ("rear_left_count_delta", self.rear_left_count_delta),
            ("rear_right_count_delta", self.rear_right_count_delta),
        )


@dataclass(frozen=True, slots=True)
class BodyTwist2D:
    """Body-frame velocity: +x forward, +y left, +yaw counterclockwise."""

    vx_m_s: float
    vy_m_s: float
    yaw_rate_rad_s: float

    def __post_init__(self) -> None:
        _validate_finite_fields(
            (
                ("vx_m_s", self.vx_m_s),
                ("vy_m_s", self.vy_m_s),
                ("yaw_rate_rad_s", self.yaw_rate_rad_s),
            )
        )


@dataclass(frozen=True, slots=True)
class Pose2D:
    """World-frame 2D pose in metres and radians."""

    x_m: float
    y_m: float
    yaw_rad: float

    def __post_init__(self) -> None:
        _validate_finite_fields(
            (("x_m", self.x_m), ("y_m", self.y_m), ("yaw_rad", self.yaw_rad))
        )


@dataclass(frozen=True, slots=True)
class OdometrySample:
    """One software-derived encoder/kinematics/pose integration result."""

    timestamp_ms: int
    interval_ms: int
    raw_count_deltas: WheelCountDeltas
    signed_count_deltas: WheelCountDeltas
    wheel_angular_velocities: WheelAngularVelocities
    body_twist: BodyTwist2D
    pose: Pose2D

    def __post_init__(self) -> None:
        _require_non_negative_int(self.timestamp_ms, "timestamp_ms")
        _require_positive_int(self.interval_ms, "interval_ms")
        for name, value, expected_type in (
            ("raw_count_deltas", self.raw_count_deltas, WheelCountDeltas),
            ("signed_count_deltas", self.signed_count_deltas, WheelCountDeltas),
            ("wheel_angular_velocities", self.wheel_angular_velocities, WheelAngularVelocities),
            ("body_twist", self.body_twist, BodyTwist2D),
            ("pose", self.pose, Pose2D),
        ):
            if not isinstance(value, expected_type):
                raise ValueError(f"{name} must be {expected_type.__name__}")


def inverse_mecanum_kinematics(
    body_twist: BodyTwist2D,
    geometry: MecanumGeometry,
) -> WheelAngularVelocities:
    """Map a rover body twist to standard X-layout wheel angular rates."""
    if not isinstance(body_twist, BodyTwist2D):
        raise ValueError("body_twist must be BodyTwist2D")
    if not isinstance(geometry, MecanumGeometry):
        raise ValueError("geometry must be MecanumGeometry")
    radius = geometry.wheel_radius_m
    lever_arm = geometry.rotation_lever_arm_m
    vx = body_twist.vx_m_s
    vy = body_twist.vy_m_s
    yaw_component = lever_arm * body_twist.yaw_rate_rad_s
    return WheelAngularVelocities(
        front_left_rad_s=(vx - vy - yaw_component) / radius,
        front_right_rad_s=(vx + vy + yaw_component) / radius,
        rear_left_rad_s=(vx + vy - yaw_component) / radius,
        rear_right_rad_s=(vx - vy + yaw_component) / radius,
    )


def forward_mecanum_kinematics(
    wheel_velocities: WheelAngularVelocities,
    geometry: MecanumGeometry,
) -> BodyTwist2D:
    """Map standard X-layout wheel angular rates to a rover body twist."""
    if not isinstance(wheel_velocities, WheelAngularVelocities):
        raise ValueError("wheel_velocities must be WheelAngularVelocities")
    if not isinstance(geometry, MecanumGeometry):
        raise ValueError("geometry must be MecanumGeometry")
    fl = wheel_velocities.front_left_rad_s
    fr = wheel_velocities.front_right_rad_s
    rl = wheel_velocities.rear_left_rad_s
    rr = wheel_velocities.rear_right_rad_s
    radius_quarter = geometry.wheel_radius_m / 4.0
    return BodyTwist2D(
        vx_m_s=radius_quarter * (fl + fr + rl + rr),
        vy_m_s=radius_quarter * (-fl + fr + rl - rr),
        yaw_rate_rad_s=(
            radius_quarter
            / geometry.rotation_lever_arm_m
            * (-fl + fr - rl + rr)
        ),
    )


def count_delta_to_wheel_angular_displacement_rad(
    count_delta: int,
    *,
    counts_per_wheel_revolution: float,
    direction_multiplier: int,
) -> float:
    """Convert a raw count delta to mathematical wheel displacement in radians."""
    _require_int(count_delta, "count_delta")
    _require_positive_finite(counts_per_wheel_revolution, "counts_per_wheel_revolution")
    _require_direction_multiplier(direction_multiplier, "direction_multiplier")
    return math.tau * count_delta * direction_multiplier / counts_per_wheel_revolution


def count_delta_to_wheel_angular_velocity_rad_s(
    count_delta: int,
    *,
    dt_s: float,
    counts_per_wheel_revolution: float,
    direction_multiplier: int,
) -> float:
    """Convert a raw count delta over positive ``dt_s`` to rad/s."""
    _require_positive_finite(dt_s, "dt_s")
    return count_delta_to_wheel_angular_displacement_rad(
        count_delta,
        counts_per_wheel_revolution=counts_per_wheel_revolution,
        direction_multiplier=direction_multiplier,
    ) / dt_s


def apply_encoder_direction_multipliers(
    raw_count_deltas: WheelCountDeltas,
    configuration: EncoderConfiguration,
) -> WheelCountDeltas:
    """Apply explicit raw-encoder signs to obtain mathematical wheel signs."""
    if not isinstance(raw_count_deltas, WheelCountDeltas):
        raise ValueError("raw_count_deltas must be WheelCountDeltas")
    if not isinstance(configuration, EncoderConfiguration):
        raise ValueError("configuration must be EncoderConfiguration")
    return WheelCountDeltas(
        front_left_count_delta=(
            raw_count_deltas.front_left_count_delta * configuration.front_left_direction
        ),
        front_right_count_delta=(
            raw_count_deltas.front_right_count_delta * configuration.front_right_direction
        ),
        rear_left_count_delta=(
            raw_count_deltas.rear_left_count_delta * configuration.rear_left_direction
        ),
        rear_right_count_delta=(
            raw_count_deltas.rear_right_count_delta * configuration.rear_right_direction
        ),
    )


def wheel_count_deltas_to_angular_velocities(
    raw_count_deltas: WheelCountDeltas,
    configuration: EncoderConfiguration,
    *,
    dt_s: float,
) -> WheelAngularVelocities:
    """Convert four raw encoder deltas to mathematical wheel rates."""
    _require_positive_finite(dt_s, "dt_s")
    signed = apply_encoder_direction_multipliers(raw_count_deltas, configuration)
    scale = math.tau / configuration.counts_per_wheel_revolution / dt_s
    return WheelAngularVelocities(
        front_left_rad_s=signed.front_left_count_delta * scale,
        front_right_rad_s=signed.front_right_count_delta * scale,
        rear_left_rad_s=signed.rear_left_count_delta * scale,
        rear_right_rad_s=signed.rear_right_count_delta * scale,
    )


def encoder_counter_delta(
    previous_count: int,
    current_count: int,
    *,
    counter_width_bits: int | None = None,
) -> int:
    """Return a signed counter delta, applying wrap only for an explicit width."""
    _require_int(previous_count, "previous_count")
    _require_int(current_count, "current_count")
    if counter_width_bits is None:
        return current_count - previous_count
    _require_positive_int(counter_width_bits, "counter_width_bits")
    modulus = 1 << counter_width_bits
    if not 0 <= previous_count < modulus:
        raise ValueError("previous_count is outside the explicit counter width")
    if not 0 <= current_count < modulus:
        raise ValueError("current_count is outside the explicit counter width")
    half_range = modulus // 2
    return (current_count - previous_count + half_range) % modulus - half_range


def integrate_constant_body_twist(
    pose: Pose2D,
    body_twist: BodyTwist2D,
    *,
    dt_s: float,
) -> Pose2D:
    """Integrate a constant body-frame twist with the exact SE(2) exponential."""
    if not isinstance(pose, Pose2D):
        raise ValueError("pose must be Pose2D")
    if not isinstance(body_twist, BodyTwist2D):
        raise ValueError("body_twist must be BodyTwist2D")
    _require_positive_finite(dt_s, "dt_s")

    theta = body_twist.yaw_rate_rad_s * dt_s
    if abs(theta) < 1.0e-8:
        theta2 = theta * theta
        sinc_theta = 1.0 - theta2 / 6.0 + theta2 * theta2 / 120.0
        cosc_theta = theta / 2.0 - theta * theta2 / 24.0 + theta * theta2 * theta2 / 720.0
    else:
        sinc_theta = math.sin(theta) / theta
        cosc_theta = (1.0 - math.cos(theta)) / theta

    forward_delta_m = dt_s * (
        sinc_theta * body_twist.vx_m_s - cosc_theta * body_twist.vy_m_s
    )
    left_delta_m = dt_s * (
        cosc_theta * body_twist.vx_m_s + sinc_theta * body_twist.vy_m_s
    )
    cos_yaw = math.cos(pose.yaw_rad)
    sin_yaw = math.sin(pose.yaw_rad)
    return Pose2D(
        x_m=pose.x_m + cos_yaw * forward_delta_m - sin_yaw * left_delta_m,
        y_m=pose.y_m + sin_yaw * forward_delta_m + cos_yaw * left_delta_m,
        yaw_rad=normalize_yaw_rad(pose.yaw_rad + theta),
    )


def normalize_yaw_rad(yaw_rad: float) -> float:
    """Normalize a finite angle to the half-open interval ``[-pi, pi)``."""
    _require_finite(yaw_rad, "yaw_rad")
    if -math.pi <= float(yaw_rad) < math.pi:
        return float(yaw_rad)
    return (yaw_rad + math.pi) % math.tau - math.pi


def _validate_finite_fields(fields: tuple[tuple[str, float], ...]) -> None:
    for name, value in fields:
        _require_finite(value, name)


def _require_finite(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be finite")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def _require_positive_finite(value: object, name: str) -> None:
    _require_finite(value, name)
    if float(value) <= 0.0:
        raise ValueError(f"{name} must be positive")


def _require_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")


def _require_non_negative_int(value: object, name: str) -> None:
    _require_int(value, name)
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _require_positive_int(value: object, name: str) -> None:
    _require_int(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _require_direction_multiplier(value: object, name: str) -> None:
    _require_int(value, name)
    if value not in (-1, 1):
        raise ValueError(f"{name} must be +1 or -1")
