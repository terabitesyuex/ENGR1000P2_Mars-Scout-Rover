"""Deterministic software-only Phase 4B closed-loop wheel simulation."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .mecanum_odometry import (
    BodyTwist2D,
    MecanumGeometry,
    Pose2D,
    WheelAngularVelocities,
    forward_mecanum_kinematics,
    integrate_constant_body_twist,
)
from .motion_control import (
    BodyMotionCommand,
    MotionControlConfiguration,
    MotionControlSnapshot,
    MotionControlState,
    MotionSafetyInputs,
    WheelControlEfforts,
    motion_control_step,
    zero_wheel_speeds,
)
from .stm32_sensor_models import Stm32TelemetryMessage
from .stm32_sensor_protocol import encode_stm32_telemetry_message


MOTION_CONTROL_SCENARIOS = (
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
)

SYNTHETIC_CONTROL_ORIGIN = "synthetic_phase4b_motion_control"


@dataclass(frozen=True, slots=True)
class SyntheticWheelPlantWheelParameters:
    """Explicit SYNTHETIC first-order wheel parameters, never rover data."""

    gain_rad_s_per_normalized_effort: float
    time_constant_s: float

    def __post_init__(self) -> None:
        _require_positive_finite(
            self.gain_rad_s_per_normalized_effort,
            "gain_rad_s_per_normalized_effort",
        )
        _require_positive_finite(self.time_constant_s, "time_constant_s")


@dataclass(frozen=True, slots=True)
class SyntheticWheelPlantParameters:
    front_left: SyntheticWheelPlantWheelParameters
    front_right: SyntheticWheelPlantWheelParameters
    rear_left: SyntheticWheelPlantWheelParameters
    rear_right: SyntheticWheelPlantWheelParameters

    def __post_init__(self) -> None:
        for name, value in self.items:
            if not isinstance(value, SyntheticWheelPlantWheelParameters):
                raise ValueError(
                    f"{name} must be SyntheticWheelPlantWheelParameters"
                )

    @property
    def items(
        self,
    ) -> tuple[tuple[str, SyntheticWheelPlantWheelParameters], ...]:
        return (
            ("front_left", self.front_left),
            ("front_right", self.front_right),
            ("rear_left", self.rear_left),
            ("rear_right", self.rear_right),
        )

    @classmethod
    def shared(
        cls,
        *,
        gain_rad_s_per_normalized_effort: float,
        time_constant_s: float,
    ) -> "SyntheticWheelPlantParameters":
        wheel = SyntheticWheelPlantWheelParameters(
            gain_rad_s_per_normalized_effort=gain_rad_s_per_normalized_effort,
            time_constant_s=time_constant_s,
        )
        return cls(wheel, wheel, wheel, wheel)


@dataclass(frozen=True, slots=True)
class MotionControlSimulationSample:
    """One synthetic plant update and its complete software control snapshot."""

    snapshot: MotionControlSnapshot
    synthetic_measured_wheel_speeds: WheelAngularVelocities
    estimated_body_twist: BodyTwist2D
    synthetic_pose: Pose2D

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, MotionControlSnapshot):
            raise ValueError("snapshot must be MotionControlSnapshot")
        if not isinstance(
            self.synthetic_measured_wheel_speeds,
            WheelAngularVelocities,
        ):
            raise ValueError(
                "synthetic_measured_wheel_speeds must be WheelAngularVelocities"
            )
        if not isinstance(self.estimated_body_twist, BodyTwist2D):
            raise ValueError("estimated_body_twist must be BodyTwist2D")
        if not isinstance(self.synthetic_pose, Pose2D):
            raise ValueError("synthetic_pose must be Pose2D")


def update_synthetic_wheel_plant(
    *,
    prior_speeds: WheelAngularVelocities,
    efforts: WheelControlEfforts,
    parameters: SyntheticWheelPlantParameters,
    dt_s: float,
) -> WheelAngularVelocities:
    """Apply an exact discrete update of a synthetic first-order wheel model."""
    if not isinstance(prior_speeds, WheelAngularVelocities):
        raise ValueError("prior_speeds must be WheelAngularVelocities")
    if not isinstance(efforts, WheelControlEfforts):
        raise ValueError("efforts must be WheelControlEfforts")
    if not isinstance(parameters, SyntheticWheelPlantParameters):
        raise ValueError("parameters must be SyntheticWheelPlantParameters")
    _require_positive_finite(dt_s, "dt_s")
    speeds = _wheel_values(prior_speeds)
    effort_values = tuple(value for _, value in efforts.items)
    wheel_parameters = tuple(value for _, value in parameters.items)
    next_speeds: list[float] = []
    for speed, effort, wheel in zip(
        speeds,
        effort_values,
        wheel_parameters,
        strict=True,
    ):
        alpha = 1.0 - math.exp(-dt_s / wheel.time_constant_s)
        steady_speed = wheel.gain_rad_s_per_normalized_effort * effort
        next_speeds.append(speed + alpha * (steady_speed - speed))
    return WheelAngularVelocities(*next_speeds)


def synthetic_body_command_for_scenario(
    scenario: str,
    *,
    step_index: int,
    step_count: int,
    timestamp_ms: int,
    interval_ms: int,
) -> BodyMotionCommand:
    """Return explicitly synthetic scenario input values, not rover limits."""
    _validate_scenario_step(
        scenario,
        step_index=step_index,
        step_count=step_count,
        timestamp_ms=timestamp_ms,
        interval_ms=interval_ms,
    )
    # These fixed values are deterministic SYNTHETIC test inputs.  They are not
    # motor, wheel, chassis, controller, or safe-operating specifications.
    command_values = {
        "stationary": (0.0, 0.0, 0.0),
        "forward": (0.40, 0.0, 0.0),
        "left_strafe": (0.0, 0.30, 0.0),
        "counterclockwise_rotation": (0.0, 0.0, 0.50),
        "combined_curved_motion": (0.35, 0.12, 0.40),
        "command_desaturation": (1.50, 0.70, 1.20),
        "stale_command_watchdog_stop": (0.40, 0.0, 0.0),
        "emergency_stop": (0.40, 0.0, 0.0),
        "ground_edge_forced_stop": (0.40, 0.0, 0.0),
        "ultrasonic_forced_stop": (0.40, 0.0, 0.0),
        "slow_front_left_wheel": (0.40, 0.0, 0.0),
    }
    if scenario == "acceleration_limited_transition":
        values = (0.0, 0.0, 0.0) if step_index < step_count // 3 else (0.40, 0.0, 0.0)
    else:
        values = command_values[scenario]
    command_timestamp_ms = timestamp_ms
    if scenario == "stale_command_watchdog_stop" and step_index >= step_count // 2:
        command_timestamp_ms = timestamp_ms - (
            step_index - step_count // 2 + 1
        ) * interval_ms
    return BodyMotionCommand(
        vx_m_s=values[0],
        vy_m_s=values[1],
        yaw_rate_rad_s=values[2],
        command_timestamp_ms=command_timestamp_ms,
        command_id=f"{scenario}-{step_index}",
        source=SYNTHETIC_CONTROL_ORIGIN,
    )


def generate_motion_control_samples(
    *,
    configuration: MotionControlConfiguration,
    plant_parameters: SyntheticWheelPlantParameters,
    scenario: str,
    step_count: int,
    interval_ms: int,
    start_timestamp_ms: int = 0,
    initial_pose: Pose2D | None = None,
) -> tuple[MotionControlSimulationSample, ...]:
    """Run the full Phase 4B software pipeline without hardware access."""
    if not isinstance(configuration, MotionControlConfiguration):
        raise ValueError("configuration must be MotionControlConfiguration")
    if not isinstance(plant_parameters, SyntheticWheelPlantParameters):
        raise ValueError("plant_parameters must be SyntheticWheelPlantParameters")
    if scenario not in MOTION_CONTROL_SCENARIOS:
        raise ValueError(
            f"scenario must be one of: {', '.join(MOTION_CONTROL_SCENARIOS)}"
        )
    if scenario == "slow_front_left_wheel":
        other_time_constants = (
            plant_parameters.front_right.time_constant_s,
            plant_parameters.rear_left.time_constant_s,
            plant_parameters.rear_right.time_constant_s,
        )
        if not all(
            plant_parameters.front_left.time_constant_s > value
            for value in other_time_constants
        ):
            raise ValueError(
                "slow_front_left_wheel requires an explicitly larger synthetic "
                "front-left time constant"
            )
    _require_positive_int(step_count, "step_count")
    _require_positive_int(interval_ms, "interval_ms")
    _require_non_negative_int(start_timestamp_ms, "start_timestamp_ms")
    pose = initial_pose if initial_pose is not None else Pose2D(0.0, 0.0, 0.0)
    if not isinstance(pose, Pose2D):
        raise ValueError("initial_pose must be Pose2D or None")
    dt_s = interval_ms / 1000.0
    measurements = zero_wheel_speeds()
    control_state = MotionControlState()
    samples: list[MotionControlSimulationSample] = []

    for step_index in range(step_count):
        timestamp_ms = start_timestamp_ms + (step_index + 1) * interval_ms
        command = synthetic_body_command_for_scenario(
            scenario,
            step_index=step_index,
            step_count=step_count,
            timestamp_ms=timestamp_ms,
            interval_ms=interval_ms,
        )
        safety_inputs = _synthetic_safety_inputs(
            scenario,
            step_index=step_index,
            step_count=step_count,
            command_age_ms=timestamp_ms - command.command_timestamp_ms,
        )
        snapshot, control_state = motion_control_step(
            command=command,
            measurements=measurements,
            safety_inputs=safety_inputs,
            dt_s=dt_s,
            configuration=configuration,
            prior_state=control_state,
        )
        measurements = update_synthetic_wheel_plant(
            prior_speeds=measurements,
            efforts=snapshot.control_efforts,
            parameters=plant_parameters,
            dt_s=dt_s,
        )
        estimated_twist = forward_mecanum_kinematics(
            measurements,
            configuration.geometry,
        )
        pose = integrate_constant_body_twist(pose, estimated_twist, dt_s=dt_s)
        samples.append(
            MotionControlSimulationSample(
                snapshot=snapshot,
                synthetic_measured_wheel_speeds=measurements,
                estimated_body_twist=estimated_twist,
                synthetic_pose=pose,
            )
        )
    return tuple(samples)


def motion_control_sample_to_telemetry_messages(
    sample: MotionControlSimulationSample,
    *,
    sequence_start: int,
) -> tuple[Stm32TelemetryMessage, ...]:
    """Encode one sample with additive version-1 software-derived records."""
    if not isinstance(sample, MotionControlSimulationSample):
        raise ValueError("sample must be MotionControlSimulationSample")
    _require_non_negative_int(sequence_start, "sequence_start")
    snapshot = sample.snapshot
    command = snapshot.command
    requested = snapshot.requested_wheel_speeds
    desaturated = snapshot.desaturation.setpoints
    limited = snapshot.acceleration_limit.setpoints
    applied = snapshot.applied_wheel_setpoints
    measured = sample.synthetic_measured_wheel_speeds
    efforts = snapshot.control_efforts
    safety = snapshot.safety_decision
    twist = sample.estimated_body_twist
    pose = sample.synthetic_pose
    timestamp_ms = snapshot.timestamp_ms
    flags = snapshot.acceleration_limit.limited
    common = {"origin": SYNTHETIC_CONTROL_ORIGIN}
    return (
        Stm32TelemetryMessage(
            sequence=sequence_start,
            timestamp_ms=timestamp_ms,
            message_type="body_motion_command",
            sensor_id="motion_command",
            status="software_derived",
            payload={
                **common,
                "vx_m_s": command.vx_m_s,
                "vy_m_s": command.vy_m_s,
                "yaw_rate_rad_s": command.yaw_rate_rad_s,
                "command_timestamp_ms": command.command_timestamp_ms,
                "command_id": command.command_id,
                "source": command.source,
                "motion_requested": command.motion_requested,
            },
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 1,
            timestamp_ms=timestamp_ms,
            message_type="wheel_speed_setpoint",
            sensor_id="mecanum_wheel_setpoints",
            status="software_derived",
            payload={
                **common,
                **_prefixed_wheels("requested", requested),
                **_prefixed_wheels("desaturated", desaturated),
                **_prefixed_wheels("acceleration_limited", limited),
                **_prefixed_wheels("applied", applied),
                "desaturation_applied": snapshot.desaturation.desaturated,
                "desaturation_scale_factor": snapshot.desaturation.scale_factor,
                "front_left_rate_limited": flags.front_left,
                "front_right_rate_limited": flags.front_right,
                "rear_left_rate_limited": flags.rear_left,
                "rear_right_rate_limited": flags.rear_right,
            },
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 2,
            timestamp_ms=timestamp_ms,
            message_type="wheel_speed_measurement",
            sensor_id="mecanum_wheel_measurements",
            status="software_derived",
            payload={**common, **_plain_wheels(measured)},
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 3,
            timestamp_ms=timestamp_ms,
            message_type="wheel_control_effort",
            sensor_id="mecanum_wheel_control",
            status="software_derived",
            payload={
                **common,
                "front_left_normalized": efforts.front_left_normalized,
                "front_right_normalized": efforts.front_right_normalized,
                "rear_left_normalized": efforts.rear_left_normalized,
                "rear_right_normalized": efforts.rear_right_normalized,
                "output_meaning": "dimensionless_mathematical_not_pwm",
            },
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 4,
            timestamp_ms=timestamp_ms,
            message_type="motion_safety_state",
            sensor_id="motion_safety",
            status="software_derived",
            payload={
                **common,
                "permit_motion": safety.permit_motion,
                "forced_stop": safety.forced_stop,
                "stop_reason": safety.stop_reason.value,
                "command_age_ms": safety.command_age_ms,
                "command_stale": safety.command_stale,
                "latched_fault": safety.latched_fault,
                "targets_replaced_with_zero": safety.targets_replaced_with_zero,
            },
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 5,
            timestamp_ms=timestamp_ms,
            message_type="motion_control_snapshot",
            sensor_id="motion_control",
            status="software_derived",
            payload={
                **common,
                "requested_vx_m_s": command.vx_m_s,
                "requested_vy_m_s": command.vy_m_s,
                "requested_yaw_rate_rad_s": command.yaw_rate_rad_s,
                **_prefixed_wheels("requested", requested),
                **_prefixed_wheels("desaturated", desaturated),
                **_prefixed_wheels("acceleration_limited", limited),
                **_prefixed_wheels("measured", measured),
                "front_left_effort_normalized": efforts.front_left_normalized,
                "front_right_effort_normalized": efforts.front_right_normalized,
                "rear_left_effort_normalized": efforts.rear_left_normalized,
                "rear_right_effort_normalized": efforts.rear_right_normalized,
                "estimated_vx_m_s": twist.vx_m_s,
                "estimated_vy_m_s": twist.vy_m_s,
                "estimated_yaw_rate_rad_s": twist.yaw_rate_rad_s,
                "synthetic_pose_x_m": pose.x_m,
                "synthetic_pose_y_m": pose.y_m,
                "synthetic_pose_yaw_rad": pose.yaw_rad,
                "permit_motion": safety.permit_motion,
                "stop_reason": safety.stop_reason.value,
            },
        ),
    )


def generate_motion_control_telemetry_lines(
    *,
    configuration: MotionControlConfiguration,
    plant_parameters: SyntheticWheelPlantParameters,
    scenario: str,
    step_count: int,
    interval_ms: int,
    start_timestamp_ms: int = 0,
) -> tuple[str, ...]:
    """Return deterministic UTF-8-compatible JSON lines for a full session."""
    lines: list[str] = []
    samples = generate_motion_control_samples(
        configuration=configuration,
        plant_parameters=plant_parameters,
        scenario=scenario,
        step_count=step_count,
        interval_ms=interval_ms,
        start_timestamp_ms=start_timestamp_ms,
    )
    for index, sample in enumerate(samples):
        lines.extend(
            encode_stm32_telemetry_message(message)
            for message in motion_control_sample_to_telemetry_messages(
                sample,
                sequence_start=index * 6,
            )
        )
    return tuple(lines)


def _synthetic_safety_inputs(
    scenario: str,
    *,
    step_index: int,
    step_count: int,
    command_age_ms: int,
) -> MotionSafetyInputs:
    hazard_active = step_index >= step_count // 2
    return MotionSafetyInputs(
        control_enabled=True,
        emergency_stop=scenario == "emergency_stop" and hazard_active,
        command_age_ms=command_age_ms,
        communication_ok=True,
        ground_edge_hazard=(
            scenario == "ground_edge_forced_stop" and hazard_active
        ),
        ultrasonic_hazard=(
            scenario == "ultrasonic_forced_stop" and hazard_active
        ),
        critical_sensor_valid=True,
        controller_fault=False,
    )


def _plain_wheels(wheels: WheelAngularVelocities) -> dict[str, float]:
    return {
        "front_left_rad_s": wheels.front_left_rad_s,
        "front_right_rad_s": wheels.front_right_rad_s,
        "rear_left_rad_s": wheels.rear_left_rad_s,
        "rear_right_rad_s": wheels.rear_right_rad_s,
    }


def _prefixed_wheels(
    prefix: str,
    wheels: WheelAngularVelocities,
) -> dict[str, float]:
    return {
        f"{prefix}_front_left_rad_s": wheels.front_left_rad_s,
        f"{prefix}_front_right_rad_s": wheels.front_right_rad_s,
        f"{prefix}_rear_left_rad_s": wheels.rear_left_rad_s,
        f"{prefix}_rear_right_rad_s": wheels.rear_right_rad_s,
    }


def _wheel_values(
    wheels: WheelAngularVelocities,
) -> tuple[float, float, float, float]:
    return (
        wheels.front_left_rad_s,
        wheels.front_right_rad_s,
        wheels.rear_left_rad_s,
        wheels.rear_right_rad_s,
    )


def _validate_scenario_step(
    scenario: str,
    *,
    step_index: int,
    step_count: int,
    timestamp_ms: int,
    interval_ms: int,
) -> None:
    if scenario not in MOTION_CONTROL_SCENARIOS:
        raise ValueError(
            f"scenario must be one of: {', '.join(MOTION_CONTROL_SCENARIOS)}"
        )
    _require_non_negative_int(step_index, "step_index")
    _require_positive_int(step_count, "step_count")
    if step_index >= step_count:
        raise ValueError("step_index must be less than step_count")
    _require_non_negative_int(timestamp_ms, "timestamp_ms")
    _require_positive_int(interval_ms, "interval_ms")


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
