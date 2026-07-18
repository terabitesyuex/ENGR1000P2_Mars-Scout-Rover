"""Deterministic, hardware-free Phase 4A mecanum odometry simulation."""

from __future__ import annotations

import math

from .mecanum_odometry import (
    BodyTwist2D,
    EncoderConfiguration,
    MecanumGeometry,
    OdometrySample,
    Pose2D,
    WheelAngularVelocities,
    WheelCountDeltas,
    apply_encoder_direction_multipliers,
    forward_mecanum_kinematics,
    integrate_constant_body_twist,
    inverse_mecanum_kinematics,
    wheel_count_deltas_to_angular_velocities,
)
from .stm32_sensor_models import Stm32TelemetryMessage
from .stm32_sensor_protocol import encode_stm32_telemetry_message


MECANUM_ODOMETRY_SCENARIOS = (
    "stationary",
    "forward",
    "left_strafe",
    "counterclockwise_rotation",
    "combined_curved_motion",
)


def synthetic_body_twist_for_scenario(scenario: str) -> BodyTwist2D:
    """Return a documented synthetic twist, never a measured rover value."""
    scenarios = {
        "stationary": BodyTwist2D(0.0, 0.0, 0.0),
        "forward": BodyTwist2D(0.40, 0.0, 0.0),
        "left_strafe": BodyTwist2D(0.0, 0.30, 0.0),
        "counterclockwise_rotation": BodyTwist2D(0.0, 0.0, 0.50),
        "combined_curved_motion": BodyTwist2D(0.35, 0.12, 0.40),
    }
    try:
        return scenarios[scenario]
    except KeyError as exc:
        raise ValueError(
            f"scenario must be one of: {', '.join(MECANUM_ODOMETRY_SCENARIOS)}"
        ) from exc


def generate_mecanum_odometry_samples(
    *,
    geometry: MecanumGeometry,
    encoder_configuration: EncoderConfiguration,
    scenario: str,
    step_count: int,
    interval_ms: int,
    start_timestamp_ms: int = 0,
    initial_pose: Pose2D | None = None,
) -> tuple[OdometrySample, ...]:
    """Generate quantized encoder samples and derived odometry deterministically."""
    if not isinstance(geometry, MecanumGeometry):
        raise ValueError("geometry must be MecanumGeometry")
    if not isinstance(encoder_configuration, EncoderConfiguration):
        raise ValueError("encoder_configuration must be EncoderConfiguration")
    _require_positive_int(step_count, "step_count")
    _require_positive_int(interval_ms, "interval_ms")
    _require_non_negative_int(start_timestamp_ms, "start_timestamp_ms")
    pose = initial_pose if initial_pose is not None else Pose2D(0.0, 0.0, 0.0)
    if not isinstance(pose, Pose2D):
        raise ValueError("initial_pose must be Pose2D or None")

    target_twist = synthetic_body_twist_for_scenario(scenario)
    target_wheels = inverse_mecanum_kinematics(target_twist, geometry)
    dt_s = interval_ms / 1000.0
    previous_cumulative_raw = (0, 0, 0, 0)
    samples: list[OdometrySample] = []

    for step_index in range(1, step_count + 1):
        cumulative_raw = _cumulative_raw_counts(
            target_wheels,
            encoder_configuration,
            elapsed_s=step_index * dt_s,
        )
        raw_count_deltas = WheelCountDeltas(
            front_left_count_delta=cumulative_raw[0] - previous_cumulative_raw[0],
            front_right_count_delta=cumulative_raw[1] - previous_cumulative_raw[1],
            rear_left_count_delta=cumulative_raw[2] - previous_cumulative_raw[2],
            rear_right_count_delta=cumulative_raw[3] - previous_cumulative_raw[3],
        )
        previous_cumulative_raw = cumulative_raw
        signed_count_deltas = apply_encoder_direction_multipliers(
            raw_count_deltas,
            encoder_configuration,
        )
        wheel_velocities = wheel_count_deltas_to_angular_velocities(
            raw_count_deltas,
            encoder_configuration,
            dt_s=dt_s,
        )
        body_twist = forward_mecanum_kinematics(wheel_velocities, geometry)
        pose = integrate_constant_body_twist(pose, body_twist, dt_s=dt_s)
        samples.append(
            OdometrySample(
                timestamp_ms=start_timestamp_ms + step_index * interval_ms,
                interval_ms=interval_ms,
                raw_count_deltas=raw_count_deltas,
                signed_count_deltas=signed_count_deltas,
                wheel_angular_velocities=wheel_velocities,
                body_twist=body_twist,
                pose=pose,
            )
        )
    return tuple(samples)


def odometry_sample_to_telemetry_messages(
    sample: OdometrySample,
    *,
    sequence_start: int,
) -> tuple[Stm32TelemetryMessage, ...]:
    """Represent one sample with backward-compatible version-1 message types."""
    if not isinstance(sample, OdometrySample):
        raise ValueError("sample must be OdometrySample")
    _require_non_negative_int(sequence_start, "sequence_start")
    raw = sample.raw_count_deltas
    signed = sample.signed_count_deltas
    wheel = sample.wheel_angular_velocities
    twist = sample.body_twist
    pose = sample.pose
    timestamp_ms = sample.timestamp_ms
    return (
        Stm32TelemetryMessage(
            sequence=sequence_start,
            timestamp_ms=timestamp_ms,
            message_type="wheel_encoder_delta",
            sensor_id="wheel_encoders",
            status="simulated",
            payload={
                "interval_ms": sample.interval_ms,
                "front_left_raw_count_delta": raw.front_left_count_delta,
                "front_right_raw_count_delta": raw.front_right_count_delta,
                "rear_left_raw_count_delta": raw.rear_left_count_delta,
                "rear_right_raw_count_delta": raw.rear_right_count_delta,
                "front_left_signed_count_delta": signed.front_left_count_delta,
                "front_right_signed_count_delta": signed.front_right_count_delta,
                "rear_left_signed_count_delta": signed.rear_left_count_delta,
                "rear_right_signed_count_delta": signed.rear_right_count_delta,
            },
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 1,
            timestamp_ms=timestamp_ms,
            message_type="wheel_angular_velocity",
            sensor_id="mecanum_wheels",
            status="software_derived",
            payload={
                "front_left_rad_s": wheel.front_left_rad_s,
                "front_right_rad_s": wheel.front_right_rad_s,
                "rear_left_rad_s": wheel.rear_left_rad_s,
                "rear_right_rad_s": wheel.rear_right_rad_s,
            },
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 2,
            timestamp_ms=timestamp_ms,
            message_type="body_twist",
            sensor_id="rover_body",
            status="software_derived",
            payload={
                "vx_m_s": twist.vx_m_s,
                "vy_m_s": twist.vy_m_s,
                "yaw_rate_rad_s": twist.yaw_rate_rad_s,
            },
        ),
        Stm32TelemetryMessage(
            sequence=sequence_start + 3,
            timestamp_ms=timestamp_ms,
            message_type="odometry_pose",
            sensor_id="rover_odometry",
            status="software_derived",
            payload={
                "x_m": pose.x_m,
                "y_m": pose.y_m,
                "yaw_rad": pose.yaw_rad,
                "integration_method": "se2_constant_twist_exponential",
            },
        ),
    )


def generate_mecanum_odometry_telemetry_lines(
    *,
    geometry: MecanumGeometry,
    encoder_configuration: EncoderConfiguration,
    scenario: str,
    step_count: int,
    interval_ms: int,
    start_timestamp_ms: int = 0,
    initial_pose: Pose2D | None = None,
) -> tuple[str, ...]:
    """Encode a deterministic Phase 4A session as UTF-8-compatible JSON lines."""
    lines: list[str] = []
    for sample_index, sample in enumerate(
        generate_mecanum_odometry_samples(
            geometry=geometry,
            encoder_configuration=encoder_configuration,
            scenario=scenario,
            step_count=step_count,
            interval_ms=interval_ms,
            start_timestamp_ms=start_timestamp_ms,
            initial_pose=initial_pose,
        )
    ):
        lines.extend(
            encode_stm32_telemetry_message(message)
            for message in odometry_sample_to_telemetry_messages(
                sample,
                sequence_start=sample_index * 4,
            )
        )
    return tuple(lines)


def _cumulative_raw_counts(
    target_wheels: WheelAngularVelocities,
    configuration: EncoderConfiguration,
    *,
    elapsed_s: float,
) -> tuple[int, int, int, int]:
    counts_scale = configuration.counts_per_wheel_revolution / math.tau
    signed_counts = (
        target_wheels.front_left_rad_s * elapsed_s * counts_scale,
        target_wheels.front_right_rad_s * elapsed_s * counts_scale,
        target_wheels.rear_left_rad_s * elapsed_s * counts_scale,
        target_wheels.rear_right_rad_s * elapsed_s * counts_scale,
    )
    directions = (
        configuration.front_left_direction,
        configuration.front_right_direction,
        configuration.rear_left_direction,
        configuration.rear_right_direction,
    )
    return tuple(
        int(round(signed_count * direction))
        for signed_count, direction in zip(signed_counts, directions, strict=True)
    )  # type: ignore[return-value]


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
