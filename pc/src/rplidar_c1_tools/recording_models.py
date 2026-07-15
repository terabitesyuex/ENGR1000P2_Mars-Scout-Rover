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
    distance_mm: int
    sensor_id: str
    valid: bool = True


@dataclass(frozen=True, slots=True)
class GroundEdgeSample:
    timestamp_us: int
    edge_detected: bool
    sensor_id: str
    reflectance_raw: int | None = None


@dataclass(frozen=True, slots=True)
class HallLandmarkSample:
    timestamp_us: int
    detected: bool
    sensor_id: str = "hall_1"
    raw_value: int | None = None


@dataclass(frozen=True, slots=True)
class IlluminanceSample:
    timestamp_us: int
    illuminance_lux: float
    sensor_id: str = "bh1750_1"


@dataclass(frozen=True, slots=True)
class BarometerSample:
    timestamp_us: int
    temperature_c: float
    pressure_pa: float
    sensor_id: str = "bmp280_1"


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
