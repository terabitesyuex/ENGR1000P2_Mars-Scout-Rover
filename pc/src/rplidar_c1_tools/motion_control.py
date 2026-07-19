"""Pure Phase 4B wheel-speed control, command shaping, and motion safety."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math

from .mecanum_odometry import (
    BodyTwist2D,
    MecanumGeometry,
    WheelAngularVelocities,
    inverse_mecanum_kinematics,
)


# Phase 4A owns the mathematical four-wheel velocity structure.  These aliases
# add Phase 4B semantics without creating a second wheel-order representation.
WheelSpeedSetpoints = WheelAngularVelocities
WheelSpeedMeasurements = WheelAngularVelocities


@dataclass(frozen=True, slots=True)
class BodyMotionCommand:
    """Validated rover body command using Phase 4A coordinates and units."""

    vx_m_s: float
    vy_m_s: float
    yaw_rate_rad_s: float
    command_timestamp_ms: int
    command_id: str | None = None
    source: str = "software_request"
    motion_requested: bool = True

    def __post_init__(self) -> None:
        _validate_finite_fields(
            (
                ("vx_m_s", self.vx_m_s),
                ("vy_m_s", self.vy_m_s),
                ("yaw_rate_rad_s", self.yaw_rate_rad_s),
            )
        )
        _require_non_negative_int(self.command_timestamp_ms, "command_timestamp_ms")
        if self.command_id is not None and (
            not isinstance(self.command_id, str) or not self.command_id
        ):
            raise ValueError("command_id must be a non-empty string or None")
        _require_non_empty_string(self.source, "source")
        _require_bool(self.motion_requested, "motion_requested")

    @property
    def body_twist(self) -> BodyTwist2D:
        if not self.motion_requested:
            return BodyTwist2D(0.0, 0.0, 0.0)
        return BodyTwist2D(self.vx_m_s, self.vy_m_s, self.yaw_rate_rad_s)


@dataclass(frozen=True, slots=True)
class MotionCommandLimits:
    """Explicit absolute body-command limits; never rover defaults."""

    max_abs_vx_m_s: float
    max_abs_vy_m_s: float
    max_abs_yaw_rate_rad_s: float

    def __post_init__(self) -> None:
        _validate_positive_finite_fields(
            (
                ("max_abs_vx_m_s", self.max_abs_vx_m_s),
                ("max_abs_vy_m_s", self.max_abs_vy_m_s),
                ("max_abs_yaw_rate_rad_s", self.max_abs_yaw_rate_rad_s),
            )
        )


@dataclass(frozen=True, slots=True)
class WheelSpeedLimits:
    """Explicit positive wheel-speed magnitude limit."""

    max_wheel_speed_rad_s: float

    def __post_init__(self) -> None:
        _require_positive_finite(
            self.max_wheel_speed_rad_s,
            "max_wheel_speed_rad_s",
        )


@dataclass(frozen=True, slots=True)
class WheelAccelerationLimits:
    """Independent positive wheel angular-acceleration limits."""

    front_left_rad_s2: float
    front_right_rad_s2: float
    rear_left_rad_s2: float
    rear_right_rad_s2: float

    def __post_init__(self) -> None:
        _validate_positive_finite_fields(self.items)

    @property
    def items(self) -> tuple[tuple[str, float], ...]:
        return (
            ("front_left_rad_s2", self.front_left_rad_s2),
            ("front_right_rad_s2", self.front_right_rad_s2),
            ("rear_left_rad_s2", self.rear_left_rad_s2),
            ("rear_right_rad_s2", self.rear_right_rad_s2),
        )

    @classmethod
    def shared(cls, max_acceleration_rad_s2: float) -> "WheelAccelerationLimits":
        """Build four explicit fields from one deliberately shared limit."""
        _require_positive_finite(max_acceleration_rad_s2, "max_acceleration_rad_s2")
        return cls(*(float(max_acceleration_rad_s2),) * 4)


@dataclass(frozen=True, slots=True)
class WheelRateLimitFlags:
    front_left: bool
    front_right: bool
    rear_left: bool
    rear_right: bool

    def __post_init__(self) -> None:
        for name, value in self.items:
            _require_bool(value, name)

    @property
    def items(self) -> tuple[tuple[str, bool], ...]:
        return (
            ("front_left", self.front_left),
            ("front_right", self.front_right),
            ("rear_left", self.rear_left),
            ("rear_right", self.rear_right),
        )

    @property
    def any_limited(self) -> bool:
        return any(value for _, value in self.items)


@dataclass(frozen=True, slots=True)
class WheelDesaturationResult:
    requested_setpoints: WheelSpeedSetpoints
    setpoints: WheelSpeedSetpoints
    desaturated: bool
    scale_factor: float

    def __post_init__(self) -> None:
        _require_wheels(self.requested_setpoints, "requested_setpoints")
        _require_wheels(self.setpoints, "setpoints")
        _require_bool(self.desaturated, "desaturated")
        _require_positive_finite(self.scale_factor, "scale_factor")
        if self.scale_factor > 1.0:
            raise ValueError("scale_factor must not exceed 1")


@dataclass(frozen=True, slots=True)
class WheelAccelerationLimitResult:
    previous_setpoints: WheelSpeedSetpoints
    requested_setpoints: WheelSpeedSetpoints
    setpoints: WheelSpeedSetpoints
    limited: WheelRateLimitFlags

    def __post_init__(self) -> None:
        _require_wheels(self.previous_setpoints, "previous_setpoints")
        _require_wheels(self.requested_setpoints, "requested_setpoints")
        _require_wheels(self.setpoints, "setpoints")
        if not isinstance(self.limited, WheelRateLimitFlags):
            raise ValueError("limited must be WheelRateLimitFlags")


@dataclass(frozen=True, slots=True)
class PIDGains:
    """Explicit discrete PID gains; no tuning values are defaulted."""

    kp: float
    ki: float
    kd: float

    def __post_init__(self) -> None:
        for name, value in (("kp", self.kp), ("ki", self.ki), ("kd", self.kd)):
            _require_non_negative_finite(value, name)


@dataclass(frozen=True, slots=True)
class PIDLimits:
    """Normalized output bounds and integral-state bounds."""

    output_min: float
    output_max: float
    integral_min: float
    integral_max: float

    def __post_init__(self) -> None:
        _validate_finite_fields(
            (
                ("output_min", self.output_min),
                ("output_max", self.output_max),
                ("integral_min", self.integral_min),
                ("integral_max", self.integral_max),
            )
        )
        if self.output_min >= self.output_max:
            raise ValueError("output_min must be less than output_max")
        if self.integral_min > self.integral_max:
            raise ValueError("integral_min must not exceed integral_max")


@dataclass(frozen=True, slots=True)
class PIDState:
    """All state required by one pure discrete wheel controller."""

    integral_error_rad: float = 0.0
    previous_measurement_rad_s: float | None = None

    def __post_init__(self) -> None:
        _require_finite(self.integral_error_rad, "integral_error_rad")
        if self.previous_measurement_rad_s is not None:
            _require_finite(
                self.previous_measurement_rad_s,
                "previous_measurement_rad_s",
            )


@dataclass(frozen=True, slots=True)
class PIDStepResult:
    normalized_effort: float
    state: PIDState
    error_rad_s: float
    proportional_term: float
    integral_term: float
    derivative_term: float
    saturated: bool
    integration_blocked: bool

    def __post_init__(self) -> None:
        _validate_finite_fields(
            (
                ("normalized_effort", self.normalized_effort),
                ("error_rad_s", self.error_rad_s),
                ("proportional_term", self.proportional_term),
                ("integral_term", self.integral_term),
                ("derivative_term", self.derivative_term),
            )
        )
        if not isinstance(self.state, PIDState):
            raise ValueError("state must be PIDState")
        _require_bool(self.saturated, "saturated")
        _require_bool(self.integration_blocked, "integration_blocked")


@dataclass(frozen=True, slots=True)
class WheelControlEfforts:
    """Dimensionless mathematical efforts; these are not PWM values."""

    front_left_normalized: float
    front_right_normalized: float
    rear_left_normalized: float
    rear_right_normalized: float

    def __post_init__(self) -> None:
        _validate_finite_fields(self.items)

    @property
    def items(self) -> tuple[tuple[str, float], ...]:
        return (
            ("front_left_normalized", self.front_left_normalized),
            ("front_right_normalized", self.front_right_normalized),
            ("rear_left_normalized", self.rear_left_normalized),
            ("rear_right_normalized", self.rear_right_normalized),
        )


@dataclass(frozen=True, slots=True)
class WheelPIDConfiguration:
    gains: PIDGains
    limits: PIDLimits

    def __post_init__(self) -> None:
        if not isinstance(self.gains, PIDGains):
            raise ValueError("gains must be PIDGains")
        if not isinstance(self.limits, PIDLimits):
            raise ValueError("limits must be PIDLimits")


@dataclass(frozen=True, slots=True)
class FourWheelPIDConfiguration:
    front_left: WheelPIDConfiguration
    front_right: WheelPIDConfiguration
    rear_left: WheelPIDConfiguration
    rear_right: WheelPIDConfiguration

    def __post_init__(self) -> None:
        for name, value in self.items:
            if not isinstance(value, WheelPIDConfiguration):
                raise ValueError(f"{name} must be WheelPIDConfiguration")

    @property
    def items(self) -> tuple[tuple[str, WheelPIDConfiguration], ...]:
        return (
            ("front_left", self.front_left),
            ("front_right", self.front_right),
            ("rear_left", self.rear_left),
            ("rear_right", self.rear_right),
        )

    @classmethod
    def shared(
        cls,
        gains: PIDGains,
        limits: PIDLimits,
    ) -> "FourWheelPIDConfiguration":
        """Deliberately apply one immutable configuration to four controllers."""
        shared = WheelPIDConfiguration(gains=gains, limits=limits)
        return cls(shared, shared, shared, shared)


@dataclass(frozen=True, slots=True)
class WheelControllerState:
    front_left: PIDState = field(default_factory=PIDState)
    front_right: PIDState = field(default_factory=PIDState)
    rear_left: PIDState = field(default_factory=PIDState)
    rear_right: PIDState = field(default_factory=PIDState)

    def __post_init__(self) -> None:
        for name, value in self.items:
            if not isinstance(value, PIDState):
                raise ValueError(f"{name} must be PIDState")

    @property
    def items(self) -> tuple[tuple[str, PIDState], ...]:
        return (
            ("front_left", self.front_left),
            ("front_right", self.front_right),
            ("rear_left", self.rear_left),
            ("rear_right", self.rear_right),
        )


@dataclass(frozen=True, slots=True)
class FourWheelPIDResult:
    efforts: WheelControlEfforts
    state: WheelControllerState
    wheel_results: tuple[PIDStepResult, PIDStepResult, PIDStepResult, PIDStepResult]

    def __post_init__(self) -> None:
        if not isinstance(self.efforts, WheelControlEfforts):
            raise ValueError("efforts must be WheelControlEfforts")
        if not isinstance(self.state, WheelControllerState):
            raise ValueError("state must be WheelControllerState")
        if len(self.wheel_results) != 4 or not all(
            isinstance(result, PIDStepResult) for result in self.wheel_results
        ):
            raise ValueError("wheel_results must contain four PIDStepResult values")


class MotionStopReason(str, Enum):
    NONE = "none"
    DISABLED = "disabled"
    EMERGENCY_STOP = "emergency_stop"
    STALE_COMMAND = "stale_command"
    COMMUNICATION_FAULT = "communication_fault"
    GROUND_EDGE = "ground_edge"
    ULTRASONIC_OBSTACLE = "ultrasonic_obstacle"
    CRITICAL_SENSOR_INVALID = "critical_sensor_invalid"
    CONTROLLER_FAULT = "controller_fault"
    EXTERNAL_STOP = "external_stop"


@dataclass(frozen=True, slots=True)
class CommandWatchdogResult:
    command_age_ms: int
    timeout_ms: int
    stale: bool

    def __post_init__(self) -> None:
        _require_non_negative_int(self.command_age_ms, "command_age_ms")
        _require_positive_int(self.timeout_ms, "timeout_ms")
        _require_bool(self.stale, "stale")


@dataclass(frozen=True, slots=True)
class MotionSafetyInputs:
    control_enabled: bool
    emergency_stop: bool
    command_age_ms: int
    communication_ok: bool
    ground_edge_hazard: bool
    ultrasonic_hazard: bool
    critical_sensor_valid: bool
    controller_fault: bool
    external_stop: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("control_enabled", self.control_enabled),
            ("emergency_stop", self.emergency_stop),
            ("communication_ok", self.communication_ok),
            ("ground_edge_hazard", self.ground_edge_hazard),
            ("ultrasonic_hazard", self.ultrasonic_hazard),
            ("critical_sensor_valid", self.critical_sensor_valid),
            ("controller_fault", self.controller_fault),
            ("external_stop", self.external_stop),
        ):
            _require_bool(value, name)
        _require_non_negative_int(self.command_age_ms, "command_age_ms")


@dataclass(frozen=True, slots=True)
class MotionSafetyPolicy:
    """Explicit conservative stop policy; no sensor availability is inferred."""

    command_timeout_ms: int
    watchdog_enabled: bool = True
    stop_on_communication_fault: bool = True
    stop_on_ground_edge: bool = True
    stop_on_ultrasonic_hazard: bool = True
    stop_on_critical_sensor_invalid: bool = True
    stop_on_external_stop: bool = True

    def __post_init__(self) -> None:
        _require_positive_int(self.command_timeout_ms, "command_timeout_ms")
        for name, value in (
            ("watchdog_enabled", self.watchdog_enabled),
            ("stop_on_communication_fault", self.stop_on_communication_fault),
            ("stop_on_ground_edge", self.stop_on_ground_edge),
            ("stop_on_ultrasonic_hazard", self.stop_on_ultrasonic_hazard),
            ("stop_on_critical_sensor_invalid", self.stop_on_critical_sensor_invalid),
            ("stop_on_external_stop", self.stop_on_external_stop),
        ):
            _require_bool(value, name)


@dataclass(frozen=True, slots=True)
class MotionSafetyDecision:
    permit_motion: bool
    forced_stop: bool
    stop_reason: MotionStopReason
    command_stale: bool
    command_age_ms: int
    latched_fault: bool
    targets_replaced_with_zero: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("permit_motion", self.permit_motion),
            ("forced_stop", self.forced_stop),
            ("command_stale", self.command_stale),
            ("latched_fault", self.latched_fault),
            ("targets_replaced_with_zero", self.targets_replaced_with_zero),
        ):
            _require_bool(value, name)
        if not isinstance(self.stop_reason, MotionStopReason):
            raise ValueError("stop_reason must be MotionStopReason")
        _require_non_negative_int(self.command_age_ms, "command_age_ms")
        if self.forced_stop == self.permit_motion:
            raise ValueError("forced_stop must be the opposite of permit_motion")
        if self.targets_replaced_with_zero != self.forced_stop:
            raise ValueError("target replacement must match forced_stop")
        if self.permit_motion != (self.stop_reason is MotionStopReason.NONE):
            raise ValueError("stop_reason must agree with permit_motion")


@dataclass(frozen=True, slots=True)
class MotionControlConfiguration:
    geometry: MecanumGeometry
    wheel_speed_limits: WheelSpeedLimits
    wheel_acceleration_limits: WheelAccelerationLimits
    wheel_pid: FourWheelPIDConfiguration
    safety_policy: MotionSafetyPolicy
    command_limits: MotionCommandLimits | None = None

    def __post_init__(self) -> None:
        expected = (
            ("geometry", self.geometry, MecanumGeometry),
            ("wheel_speed_limits", self.wheel_speed_limits, WheelSpeedLimits),
            (
                "wheel_acceleration_limits",
                self.wheel_acceleration_limits,
                WheelAccelerationLimits,
            ),
            ("wheel_pid", self.wheel_pid, FourWheelPIDConfiguration),
            ("safety_policy", self.safety_policy, MotionSafetyPolicy),
        )
        for name, value, expected_type in expected:
            if not isinstance(value, expected_type):
                raise ValueError(f"{name} must be {expected_type.__name__}")
        if self.command_limits is not None and not isinstance(
            self.command_limits,
            MotionCommandLimits,
        ):
            raise ValueError("command_limits must be MotionCommandLimits or None")


@dataclass(frozen=True, slots=True)
class MotionControlState:
    previous_setpoints: WheelSpeedSetpoints = field(
        default_factory=lambda: WheelAngularVelocities(0.0, 0.0, 0.0, 0.0)
    )
    wheel_controllers: WheelControllerState = field(default_factory=WheelControllerState)

    def __post_init__(self) -> None:
        _require_wheels(self.previous_setpoints, "previous_setpoints")
        if not isinstance(self.wheel_controllers, WheelControllerState):
            raise ValueError("wheel_controllers must be WheelControllerState")


@dataclass(frozen=True, slots=True)
class MotionControlSnapshot:
    """Complete result from one deterministic Phase 4B control update."""

    timestamp_ms: int
    command: BodyMotionCommand
    requested_wheel_speeds: WheelSpeedSetpoints
    desaturation: WheelDesaturationResult
    acceleration_limit: WheelAccelerationLimitResult
    applied_wheel_setpoints: WheelSpeedSetpoints
    measured_wheel_speeds: WheelSpeedMeasurements
    control_efforts: WheelControlEfforts
    safety_decision: MotionSafetyDecision
    controller_state: WheelControllerState

    def __post_init__(self) -> None:
        _require_non_negative_int(self.timestamp_ms, "timestamp_ms")
        expected = (
            ("command", self.command, BodyMotionCommand),
            (
                "requested_wheel_speeds",
                self.requested_wheel_speeds,
                WheelAngularVelocities,
            ),
            ("desaturation", self.desaturation, WheelDesaturationResult),
            (
                "acceleration_limit",
                self.acceleration_limit,
                WheelAccelerationLimitResult,
            ),
            (
                "applied_wheel_setpoints",
                self.applied_wheel_setpoints,
                WheelAngularVelocities,
            ),
            (
                "measured_wheel_speeds",
                self.measured_wheel_speeds,
                WheelAngularVelocities,
            ),
            ("control_efforts", self.control_efforts, WheelControlEfforts),
            ("safety_decision", self.safety_decision, MotionSafetyDecision),
            ("controller_state", self.controller_state, WheelControllerState),
        )
        for name, value, expected_type in expected:
            if not isinstance(value, expected_type):
                raise ValueError(f"{name} must be {expected_type.__name__}")


def validate_body_motion_command(
    command: BodyMotionCommand,
    limits: MotionCommandLimits | None = None,
) -> BodyTwist2D:
    """Validate an immutable command and optional explicit magnitude limits."""
    if not isinstance(command, BodyMotionCommand):
        raise ValueError("command must be BodyMotionCommand")
    if limits is not None and not isinstance(limits, MotionCommandLimits):
        raise ValueError("limits must be MotionCommandLimits or None")
    twist = command.body_twist
    if limits is None:
        return twist
    checks = (
        (abs(twist.vx_m_s), limits.max_abs_vx_m_s, "vx_m_s"),
        (abs(twist.vy_m_s), limits.max_abs_vy_m_s, "vy_m_s"),
        (
            abs(twist.yaw_rate_rad_s),
            limits.max_abs_yaw_rate_rad_s,
            "yaw_rate_rad_s",
        ),
    )
    for magnitude, maximum, name in checks:
        if magnitude > maximum:
            raise ValueError(f"{name} exceeds the explicit command limit")
    return twist


def desaturate_wheel_setpoints(
    requested_setpoints: WheelSpeedSetpoints,
    limits: WheelSpeedLimits,
) -> WheelDesaturationResult:
    """Proportionally scale all wheels when the explicit peak limit is exceeded."""
    values = _wheel_tuple(requested_setpoints, "requested_setpoints")
    if not isinstance(limits, WheelSpeedLimits):
        raise ValueError("limits must be WheelSpeedLimits")
    peak = max(abs(value) for value in values)
    if peak <= limits.max_wheel_speed_rad_s:
        return WheelDesaturationResult(
            requested_setpoints=requested_setpoints,
            setpoints=requested_setpoints,
            desaturated=False,
            scale_factor=1.0,
        )
    scale = limits.max_wheel_speed_rad_s / peak
    return WheelDesaturationResult(
        requested_setpoints=requested_setpoints,
        setpoints=_wheels_from_tuple(tuple(value * scale for value in values)),
        desaturated=True,
        scale_factor=scale,
    )


def limit_wheel_setpoint_acceleration(
    previous_setpoints: WheelSpeedSetpoints,
    requested_setpoints: WheelSpeedSetpoints,
    limits: WheelAccelerationLimits,
    *,
    dt_s: float,
) -> WheelAccelerationLimitResult:
    """Limit each setpoint change to its explicit acceleration times ``dt_s``."""
    previous = _wheel_tuple(previous_setpoints, "previous_setpoints")
    requested = _wheel_tuple(requested_setpoints, "requested_setpoints")
    if not isinstance(limits, WheelAccelerationLimits):
        raise ValueError("limits must be WheelAccelerationLimits")
    _require_positive_finite(dt_s, "dt_s")
    accelerations = tuple(value for _, value in limits.items)
    output: list[float] = []
    flags: list[bool] = []
    for prior, wanted, acceleration in zip(
        previous,
        requested,
        accelerations,
        strict=True,
    ):
        maximum_change = acceleration * dt_s
        change = wanted - prior
        limited_change = _clamp(change, -maximum_change, maximum_change)
        output.append(prior + limited_change)
        flags.append(not math.isclose(change, limited_change, rel_tol=0.0, abs_tol=1e-15))
    return WheelAccelerationLimitResult(
        previous_setpoints=previous_setpoints,
        requested_setpoints=requested_setpoints,
        setpoints=_wheels_from_tuple(tuple(output)),
        limited=WheelRateLimitFlags(*flags),
    )


def update_wheel_speed_pid(
    *,
    target_rad_s: float,
    measured_rad_s: float,
    dt_s: float,
    gains: PIDGains,
    limits: PIDLimits,
    prior_state: PIDState,
    enabled: bool,
) -> PIDStepResult:
    """Run PID with derivative on measurement and conditional anti-windup.

    ``integral_error_rad`` stores ``sum(error_rad_s * dt_s)``.  A candidate is
    first clamped to the explicit state limits.  If that candidate would drive
    an already saturated output farther in the same direction as the error,
    the prior integral is retained instead.  Disabled updates return zero and
    reset all controller state.
    """
    _require_finite(target_rad_s, "target_rad_s")
    _require_finite(measured_rad_s, "measured_rad_s")
    _require_positive_finite(dt_s, "dt_s")
    if not isinstance(gains, PIDGains):
        raise ValueError("gains must be PIDGains")
    if not isinstance(limits, PIDLimits):
        raise ValueError("limits must be PIDLimits")
    if not isinstance(prior_state, PIDState):
        raise ValueError("prior_state must be PIDState")
    _require_bool(enabled, "enabled")
    if not enabled:
        return PIDStepResult(
            normalized_effort=0.0,
            state=PIDState(),
            error_rad_s=target_rad_s - measured_rad_s,
            proportional_term=0.0,
            integral_term=0.0,
            derivative_term=0.0,
            saturated=False,
            integration_blocked=False,
        )

    error = target_rad_s - measured_rad_s
    proportional = gains.kp * error
    measurement_derivative = (
        0.0
        if prior_state.previous_measurement_rad_s is None
        else (measured_rad_s - prior_state.previous_measurement_rad_s) / dt_s
    )
    derivative = -gains.kd * measurement_derivative
    integral_candidate = _clamp(
        prior_state.integral_error_rad + error * dt_s,
        limits.integral_min,
        limits.integral_max,
    )
    candidate_raw = proportional + gains.ki * integral_candidate + derivative
    integration_blocked = (
        candidate_raw > limits.output_max and error > 0.0
    ) or (
        candidate_raw < limits.output_min and error < 0.0
    )
    integral_state = (
        _clamp(
            prior_state.integral_error_rad,
            limits.integral_min,
            limits.integral_max,
        )
        if integration_blocked
        else integral_candidate
    )
    integral = gains.ki * integral_state
    raw_output = proportional + integral + derivative
    output = _clamp(raw_output, limits.output_min, limits.output_max)
    return PIDStepResult(
        normalized_effort=output,
        state=PIDState(
            integral_error_rad=integral_state,
            previous_measurement_rad_s=measured_rad_s,
        ),
        error_rad_s=error,
        proportional_term=proportional,
        integral_term=integral,
        derivative_term=derivative,
        saturated=not math.isclose(output, raw_output, rel_tol=0.0, abs_tol=1e-15),
        integration_blocked=integration_blocked,
    )


def control_four_wheels(
    *,
    targets: WheelSpeedSetpoints,
    measurements: WheelSpeedMeasurements,
    dt_s: float,
    configuration: FourWheelPIDConfiguration,
    prior_state: WheelControllerState,
    enabled: bool,
) -> FourWheelPIDResult:
    """Apply four independent PID configurations and states in stable order."""
    target_values = _wheel_tuple(targets, "targets")
    measured_values = _wheel_tuple(measurements, "measurements")
    _require_positive_finite(dt_s, "dt_s")
    if not isinstance(configuration, FourWheelPIDConfiguration):
        raise ValueError("configuration must be FourWheelPIDConfiguration")
    if not isinstance(prior_state, WheelControllerState):
        raise ValueError("prior_state must be WheelControllerState")
    _require_bool(enabled, "enabled")
    configs = tuple(value for _, value in configuration.items)
    states = tuple(value for _, value in prior_state.items)
    results = tuple(
        update_wheel_speed_pid(
            target_rad_s=target,
            measured_rad_s=measurement,
            dt_s=dt_s,
            gains=config.gains,
            limits=config.limits,
            prior_state=state,
            enabled=enabled,
        )
        for target, measurement, config, state in zip(
            target_values,
            measured_values,
            configs,
            states,
            strict=True,
        )
    )
    return FourWheelPIDResult(
        efforts=WheelControlEfforts(
            *(result.normalized_effort for result in results)
        ),
        state=WheelControllerState(*(result.state for result in results)),
        wheel_results=results,  # type: ignore[arg-type]
    )


def check_command_watchdog(
    *,
    current_timestamp_ms: int,
    command_timestamp_ms: int,
    timeout_ms: int,
) -> CommandWatchdogResult:
    """Evaluate staleness at ``age >= timeout`` using supplied monotonic time."""
    _require_non_negative_int(current_timestamp_ms, "current_timestamp_ms")
    _require_non_negative_int(command_timestamp_ms, "command_timestamp_ms")
    _require_positive_int(timeout_ms, "timeout_ms")
    if current_timestamp_ms < command_timestamp_ms:
        raise ValueError("current_timestamp_ms must not precede command_timestamp_ms")
    age = current_timestamp_ms - command_timestamp_ms
    return CommandWatchdogResult(
        command_age_ms=age,
        timeout_ms=timeout_ms,
        stale=age >= timeout_ms,
    )


def evaluate_motion_safety(
    inputs: MotionSafetyInputs,
    policy: MotionSafetyPolicy,
) -> MotionSafetyDecision:
    """Return the first applicable stop condition in documented precedence."""
    if not isinstance(inputs, MotionSafetyInputs):
        raise ValueError("inputs must be MotionSafetyInputs")
    if not isinstance(policy, MotionSafetyPolicy):
        raise ValueError("policy must be MotionSafetyPolicy")
    command_stale = (
        policy.watchdog_enabled
        and inputs.command_age_ms >= policy.command_timeout_ms
    )
    reason = MotionStopReason.NONE
    if inputs.emergency_stop:
        reason = MotionStopReason.EMERGENCY_STOP
    elif inputs.controller_fault:
        reason = MotionStopReason.CONTROLLER_FAULT
    elif not inputs.control_enabled:
        reason = MotionStopReason.DISABLED
    elif policy.stop_on_external_stop and inputs.external_stop:
        reason = MotionStopReason.EXTERNAL_STOP
    elif command_stale:
        reason = MotionStopReason.STALE_COMMAND
    elif policy.stop_on_communication_fault and not inputs.communication_ok:
        reason = MotionStopReason.COMMUNICATION_FAULT
    elif policy.stop_on_ground_edge and inputs.ground_edge_hazard:
        reason = MotionStopReason.GROUND_EDGE
    elif policy.stop_on_ultrasonic_hazard and inputs.ultrasonic_hazard:
        reason = MotionStopReason.ULTRASONIC_OBSTACLE
    elif policy.stop_on_critical_sensor_invalid and not inputs.critical_sensor_valid:
        reason = MotionStopReason.CRITICAL_SENSOR_INVALID
    permit = reason is MotionStopReason.NONE
    return MotionSafetyDecision(
        permit_motion=permit,
        forced_stop=not permit,
        stop_reason=reason,
        command_stale=command_stale,
        command_age_ms=inputs.command_age_ms,
        latched_fault=False,
        targets_replaced_with_zero=not permit,
    )


def motion_control_step(
    *,
    command: BodyMotionCommand,
    measurements: WheelSpeedMeasurements,
    safety_inputs: MotionSafetyInputs,
    dt_s: float,
    configuration: MotionControlConfiguration,
    prior_state: MotionControlState,
) -> tuple[MotionControlSnapshot, MotionControlState]:
    """Coordinate independently testable Phase 4B stages for one pure update."""
    if not isinstance(configuration, MotionControlConfiguration):
        raise ValueError("configuration must be MotionControlConfiguration")
    if not isinstance(prior_state, MotionControlState):
        raise ValueError("prior_state must be MotionControlState")
    if not isinstance(safety_inputs, MotionSafetyInputs):
        raise ValueError("safety_inputs must be MotionSafetyInputs")
    _require_wheels(measurements, "measurements")
    _require_positive_finite(dt_s, "dt_s")
    expected_age = safety_inputs.command_age_ms
    timestamp_ms = command.command_timestamp_ms + expected_age
    _require_non_negative_int(timestamp_ms, "timestamp_ms")

    twist = validate_body_motion_command(command, configuration.command_limits)
    requested = inverse_mecanum_kinematics(twist, configuration.geometry)
    desaturation = desaturate_wheel_setpoints(
        requested,
        configuration.wheel_speed_limits,
    )
    acceleration = limit_wheel_setpoint_acceleration(
        prior_state.previous_setpoints,
        desaturation.setpoints,
        configuration.wheel_acceleration_limits,
        dt_s=dt_s,
    )
    safety = evaluate_motion_safety(safety_inputs, configuration.safety_policy)
    applied = acceleration.setpoints if safety.permit_motion else zero_wheel_speeds()
    controller = control_four_wheels(
        targets=applied,
        measurements=measurements,
        dt_s=dt_s,
        configuration=configuration.wheel_pid,
        prior_state=prior_state.wheel_controllers,
        enabled=safety.permit_motion,
    )
    next_state = MotionControlState(
        previous_setpoints=applied,
        wheel_controllers=controller.state,
    )
    return (
        MotionControlSnapshot(
            timestamp_ms=timestamp_ms,
            command=command,
            requested_wheel_speeds=requested,
            desaturation=desaturation,
            acceleration_limit=acceleration,
            applied_wheel_setpoints=applied,
            measured_wheel_speeds=measurements,
            control_efforts=controller.efforts,
            safety_decision=safety,
            controller_state=controller.state,
        ),
        next_state,
    )


def zero_wheel_speeds() -> WheelAngularVelocities:
    return WheelAngularVelocities(0.0, 0.0, 0.0, 0.0)


def _wheel_tuple(
    wheels: WheelAngularVelocities,
    name: str,
) -> tuple[float, float, float, float]:
    _require_wheels(wheels, name)
    return (
        wheels.front_left_rad_s,
        wheels.front_right_rad_s,
        wheels.rear_left_rad_s,
        wheels.rear_right_rad_s,
    )


def _wheels_from_tuple(values: tuple[float, ...]) -> WheelAngularVelocities:
    if len(values) != 4:
        raise ValueError("wheel values must contain exactly four entries")
    return WheelAngularVelocities(*values)


def _require_wheels(value: object, name: str) -> None:
    if not isinstance(value, WheelAngularVelocities):
        raise ValueError(f"{name} must be WheelAngularVelocities")


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _validate_finite_fields(fields: tuple[tuple[str, float], ...]) -> None:
    for name, value in fields:
        _require_finite(value, name)


def _validate_positive_finite_fields(
    fields: tuple[tuple[str, float], ...],
) -> None:
    for name, value in fields:
        _require_positive_finite(value, name)


def _require_finite(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{name} must be finite")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")


def _require_positive_finite(value: object, name: str) -> None:
    _require_finite(value, name)
    if float(value) <= 0.0:
        raise ValueError(f"{name} must be positive")


def _require_non_negative_finite(value: object, name: str) -> None:
    _require_finite(value, name)
    if float(value) < 0.0:
        raise ValueError(f"{name} must be non-negative")


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


def _require_bool(value: object, name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be a boolean")


def _require_non_empty_string(value: object, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
