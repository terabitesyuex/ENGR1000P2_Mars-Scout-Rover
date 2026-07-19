"""Typed models for Phase 2.4 multi-sensor JSONL recordings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any


SCHEMA_NAME = "mars_scout_multisensor_recording"
SCHEMA_VERSION = 1
LIDAR_SENSOR_IDS = ("c1_1", "c1_2")


@dataclass(frozen=True, slots=True)
class SensorDefinition:
    sensor_id: str
    sensor_type: str
    description: str
    units: tuple[str, ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "description": self.description,
            "units": list(self.units),
        }


@dataclass(frozen=True, slots=True)
class RoverPose:
    timestamp_us: int
    x_m: float
    y_m: float
    yaw_rad: float
    source: str = "synthetic"


@dataclass(frozen=True, slots=True)
class ImuSample:
    timestamp_us: int
    accel_x_mps2: float
    accel_y_mps2: float
    accel_z_mps2: float
    gyro_x_radps: float
    gyro_y_radps: float
    gyro_z_radps: float
    sensor_id: str = "mpu6050_1"
    temperature_c: float | None = None


@dataclass(frozen=True, slots=True)
class UltrasonicSample:
    timestamp_us: int
    distance_mm: int | None
    sensor_id: str
    valid: bool = True
    status: str = "ok"
    raw_echo_us: int | None = None
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class GroundEdgeSample:
    timestamp_us: int
    edge_detected: bool | None
    sensor_id: str
    raw_state: int | None = None
    polarity_verified: bool = False
    status: str = "ok"
    reflectance_raw: int | None = None
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class HallLandmarkSample:
    timestamp_us: int
    detected: bool | None
    sensor_id: str = "hall_1"
    raw_state: int | None = None
    polarity_verified: bool = False
    status: str = "ok"
    raw_value: int | None = None
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class IlluminanceSample:
    timestamp_us: int
    illuminance_lux: float | None
    sensor_id: str = "bh1750_1"
    status: str = "ok"
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class BarometerSample:
    timestamp_us: int
    temperature_c: float | None
    pressure_pa: float | None
    sensor_id: str = "bmp280_1"
    status: str = "ok"
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class SubsystemStatusSample:
    timestamp_us: int
    subsystem: str
    health: str
    error_count: int
    sensor_id: str = "stm32_subsystem"
    status: str = "ok"
    detail: str | None = None
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class LinkStatusSample:
    timestamp_us: int
    link_name: str
    healthy: bool
    rx_bytes: int
    tx_bytes: int
    malformed_frames: int
    crc_errors: int
    sequence_gaps: int
    sensor_id: str = "esp32_link"
    status: str = "ok"
    last_rx_ms: int | None = None
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class LidarTransportStatsSample:
    timestamp_us: int
    sensor_id: str
    rx_bytes: int
    bytes_read: int
    overflow_count: int
    framing_error_count: int
    chunks_forwarded: int
    last_rx_tick_ms: int
    status: str = "ok"
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class WheelEncoderDeltaSample:
    timestamp_us: int
    interval_ms: int
    front_left_raw_count_delta: int
    front_right_raw_count_delta: int
    rear_left_raw_count_delta: int
    rear_right_raw_count_delta: int
    front_left_signed_count_delta: int
    front_right_signed_count_delta: int
    rear_left_signed_count_delta: int
    rear_right_signed_count_delta: int
    sensor_id: str = "wheel_encoders"
    status: str = "simulated"
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class WheelAngularVelocitySample:
    timestamp_us: int
    front_left_rad_s: float
    front_right_rad_s: float
    rear_left_rad_s: float
    rear_right_rad_s: float
    sensor_id: str = "mecanum_wheels"
    status: str = "software_derived"
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class BodyTwistSample:
    timestamp_us: int
    vx_m_s: float
    vy_m_s: float
    yaw_rate_rad_s: float
    sensor_id: str = "rover_body"
    status: str = "software_derived"
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class OdometryPoseSample:
    timestamp_us: int
    x_m: float
    y_m: float
    yaw_rad: float
    integration_method: str = "se2_constant_twist_exponential"
    sensor_id: str = "rover_odometry"
    status: str = "software_derived"
    source_sequence: int | None = None


@dataclass(frozen=True, slots=True)
class MotionControlRecordSample:
    """Preserved validated Phase 4B payload for an additive v1 record type."""

    timestamp_us: int
    sensor_id: str
    origin: str
    control_data: dict[str, Any]
    status: str = "software_derived"
    source_sequence: int | None = None


def default_sensor_inventory(
    *,
    lidar_count: int = 2,
    include_auxiliary: bool = True,
) -> tuple[SensorDefinition, ...]:
    """Return the neutral planned inventory used by synthetic recordings."""
    if lidar_count not in (1, 2):
        raise ValueError("lidar_count must be 1 or 2")

    sensors: list[SensorDefinition] = [
        SensorDefinition(
            sensor_id=sensor_id,
            sensor_type="rplidar_c1",
            description="Planned SLAMTEC RPLIDAR C1 unit; operation unverified",
            units=("angle_deg", "distance_mm", "quality"),
        )
        for sensor_id in LIDAR_SENSOR_IDS[:lidar_count]
    ]
    if include_auxiliary:
        sensors.extend(
            [
                SensorDefinition(
                    "ultrasonic_1",
                    "hc_sr04",
                    "Planned short-range ultrasonic ranging sensor",
                    ("distance_mm",),
                ),
                SensorDefinition(
                    "ultrasonic_2",
                    "hc_sr04",
                    "Planned short-range ultrasonic ranging sensor",
                    ("distance_mm",),
                ),
                SensorDefinition(
                    "ultrasonic_3",
                    "hc_sr04",
                    "Planned short-range ultrasonic ranging sensor",
                    ("distance_mm",),
                ),
                SensorDefinition(
                    "tcrt5000_1",
                    "tcrt5000",
                    "Planned reflective edge/drop sensor",
                    ("edge_detected", "reflectance_raw"),
                ),
                SensorDefinition(
                    "tcrt5000_2",
                    "tcrt5000",
                    "Planned reflective edge/drop sensor",
                    ("edge_detected", "reflectance_raw"),
                ),
                SensorDefinition(
                    "hall_1",
                    "hall_landmark",
                    "Planned magnetic landmark/checkpoint sensor",
                    ("detected", "raw_value"),
                ),
                SensorDefinition(
                    "bh1750_1",
                    "bh1750",
                    "Planned illuminance sensor",
                    ("illuminance_lux",),
                ),
                SensorDefinition(
                    "bmp280_1",
                    "bmp280",
                    "Planned temperature and atmospheric pressure sensor",
                    ("temperature_c", "pressure_pa"),
                ),
                SensorDefinition(
                    "mpu6050_1",
                    "mpu6050",
                    "Planned inertial measurement unit",
                    ("accel_mps2", "gyro_radps", "temperature_c"),
                ),
                SensorDefinition(
                    "rover_pose",
                    "synthetic_rover_pose",
                    "Optional replay pose estimate; not hardware odometry",
                    ("x_m", "y_m", "yaw_rad"),
                ),
                SensorDefinition(
                    "stm32_subsystem",
                    "subsystem_status",
                    "Software status for STM32 scheduler and sensor subsystems",
                    ("health", "error_count"),
                ),
                SensorDefinition(
                    "esp32_link",
                    "esp32_link_status",
                    "Software status for the planned STM32-to-ESP32 link",
                    ("rx_bytes", "tx_bytes", "crc_errors"),
                ),
                SensorDefinition(
                    "wheel_encoders",
                    "wheel_encoder_delta",
                    "Raw and explicitly sign-corrected wheel counts; hardware values unverified",
                    ("count_delta", "interval_ms"),
                ),
                SensorDefinition(
                    "mecanum_wheels",
                    "software_derived_wheel_velocity",
                    "Wheel rates derived from explicit encoder configuration",
                    ("rad_s",),
                ),
                SensorDefinition(
                    "rover_body",
                    "software_derived_body_twist",
                    "Body twist derived by Phase 4A forward kinematics",
                    ("m_s", "rad_s"),
                ),
                SensorDefinition(
                    "rover_odometry",
                    "software_derived_odometry_pose",
                    "SE(2)-integrated software odometry; not physical accuracy evidence",
                    ("x_m", "y_m", "yaw_rad"),
                ),
                SensorDefinition(
                    "motion_command",
                    "software_derived_body_motion_command",
                    "Validated Phase 4B command; not physical motion evidence",
                    ("m_s", "rad_s", "timestamp_ms"),
                ),
                SensorDefinition(
                    "mecanum_wheel_setpoints",
                    "software_derived_wheel_speed_setpoint",
                    "Requested, shaped, and safety-applied mathematical wheel targets",
                    ("rad_s",),
                ),
                SensorDefinition(
                    "mecanum_wheel_measurements",
                    "synthetic_wheel_speed_measurement",
                    "Synthetic first-order plant wheel speeds; not encoder evidence",
                    ("rad_s",),
                ),
                SensorDefinition(
                    "mecanum_wheel_control",
                    "software_derived_normalized_control_effort",
                    "Dimensionless mathematical effort; not PWM or motor voltage",
                    ("normalized",),
                ),
                SensorDefinition(
                    "motion_safety",
                    "software_derived_motion_safety_state",
                    "Pure Phase 4B permit-or-stop arbitration result",
                    ("boolean", "milliseconds"),
                ),
                SensorDefinition(
                    "motion_control",
                    "software_derived_motion_control_snapshot",
                    "Complete synthetic Phase 4B pipeline snapshot",
                    ("m_s", "rad_s", "normalized", "m", "rad"),
                ),
            ]
        )
    return tuple(sensors)


def pose_to_json(pose: RoverPose | None) -> dict[str, Any] | None:
    if pose is None:
        return None
    _validate_timestamp_us(pose.timestamp_us)
    _require_finite(pose.x_m, "pose.x_m")
    _require_finite(pose.y_m, "pose.y_m")
    _require_finite(pose.yaw_rad, "pose.yaw_rad")
    return asdict(pose)


def sample_to_json(sample: object) -> dict[str, Any]:
    if not hasattr(sample, "__dataclass_fields__"):
        raise ValueError("sample must be a recording dataclass")
    data = asdict(sample)
    _validate_timestamp_us(data.get("timestamp_us"))
    sensor_id = data.get("sensor_id")
    if sensor_id is not None and not isinstance(sensor_id, str):
        raise ValueError("sensor_id must be a string")
    for key, value in data.items():
        if isinstance(value, float):
            _require_finite(value, key)
    return data


def _validate_timestamp_us(value: object) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError("timestamp_us must be a non-negative integer")


def _require_finite(value: float, name: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
