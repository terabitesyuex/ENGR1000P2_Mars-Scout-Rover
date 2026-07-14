"""Shared PC-side LiDAR data models with explicit units."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Protocol


MetadataValue = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class ScanPoint:
    """Unified scan point in the rover frame.

    `angle_deg` is measured in degrees, with 0 degrees forward and positive
    rotation counterclockwise. `distance_mm` is measured in millimeters.
    """

    angle_deg: float
    distance_mm: int
    quality: int | None = None


@dataclass(frozen=True, slots=True)
class ScanFrame:
    """Completed scan frame shared by synthetic, replay, and future live input."""

    timestamp_us: int
    points: list[ScanPoint]
    frame_id: int | None = None
    source: str = "unknown"
    metadata: dict[str, MetadataValue] = field(default_factory=dict)

    @property
    def point_count(self) -> int:
        return len(self.points)


@dataclass(frozen=True, slots=True)
class CartesianPoint:
    """Cartesian point in metres derived from one `ScanPoint`."""

    x_m: float
    y_m: float
    source_angle_deg: float
    source_distance_mm: float
    signal_quality: int | None = None
    valid: bool = True


@dataclass(frozen=True, slots=True)
class Transform2D:
    """Planar rigid transform in metres and radians."""

    translation_x_m: float = 0.0
    translation_y_m: float = 0.0
    yaw_rad: float = 0.0


@dataclass(frozen=True, slots=True)
class LidarDeviceInfo:
    model_identifier: str
    firmware_major: int
    firmware_minor: int
    hardware_revision: int
    redacted_serial_identifier: str
    valid: bool


@dataclass(frozen=True, slots=True)
class LidarHealth:
    health_state: str
    device_error_code: int
    timestamp_ms: int
    valid: bool


@dataclass(frozen=True, slots=True)
class RawLidarSample:
    timestamp_us: int
    scan_id: int
    raw_angle_value: float
    raw_distance_value: int
    raw_quality_or_reflectivity: int | None
    scan_start: bool
    protocol_valid: bool


@dataclass(frozen=True, slots=True)
class LidarSample:
    timestamp_us: int
    scan_id: int
    angle_clockwise_deg: float
    angle_robot_deg: float
    distance_mm: int
    reflectivity_raw: int | None
    scan_start: bool
    protocol_valid: bool
    range_valid: bool
    quality_valid: bool
    filter_valid: bool
    x_m: float
    y_m: float


@dataclass(frozen=True, slots=True)
class LidarScan:
    scan_id: int
    start_timestamp_us: int
    end_timestamp_us: int
    samples: tuple[LidarSample, ...]
    received_point_count: int
    valid_point_count: int
    rejected_point_count: int
    estimated_scan_frequency_hz: float
    complete: bool


@dataclass(frozen=True, slots=True)
class LidarStatistics:
    total_bytes: int = 0
    total_samples: int = 0
    valid_samples: int = 0
    rejected_samples: int = 0
    completed_scans: int = 0
    parser_errors: int = 0
    checksum_errors: int = 0
    timeouts: int = 0
    overflow_count: int = 0
    recovery_count: int = 0


class ScanSource(Protocol):
    """Common interface for live, replay, CSV, and synthetic scan sources."""

    def scans(self) -> Iterator[ScanFrame]:
        """Yield completed scans without exposing the source transport."""
        ...
