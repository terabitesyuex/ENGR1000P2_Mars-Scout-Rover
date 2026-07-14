"""Deterministic synthetic scans for Phase 2.1 software-only testing."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from typing import Iterator

from .data_models import ScanFrame
from .scan_builder import build_scan_frame, create_scan_point


@dataclass(frozen=True, slots=True)
class SyntheticRoomConfig:
    scan_count: int = 1
    angle_step_deg: float = 1.0
    room_length_mm: int = 6000
    room_width_mm: int = 4000
    timestamp_step_us: int = 100_000
    quality: int = 100

    @property
    def point_count(self) -> int:
        if self.angle_step_deg <= 0.0:
            raise ValueError("angle_step_deg must be positive")
        return int(round(360.0 / self.angle_step_deg))


class SyntheticScanSource:
    """Produce deterministic room scans without serial ports or hardware."""

    def __init__(self, config: SyntheticRoomConfig | None = None) -> None:
        self._config = config or SyntheticRoomConfig()
        if self._config.scan_count < 0:
            raise ValueError("scan_count must be non-negative")
        if self._config.point_count <= 0:
            raise ValueError("point_count must be positive")

    def scans(self) -> Iterator[ScanFrame]:
        for frame_id in range(self._config.scan_count):
            yield self.build_scan(frame_id)

    def build_scan(self, frame_id: int = 0) -> ScanFrame:
        return generate_room_scan(
            point_count=self._config.point_count,
            room_length_mm=self._config.room_length_mm,
            room_width_mm=self._config.room_width_mm,
            timestamp_us=frame_id * self._config.timestamp_step_us,
            frame_id=frame_id,
            quality=self._config.quality,
        )


def generate_circle_scan(
    *,
    point_count: int = 360,
    radius_mm: int = 1000,
    timestamp_us: int = 0,
    frame_id: int | None = 0,
    quality: int | None = 100,
) -> ScanFrame:
    """Generate a full 360 degree scan with a constant-radius virtual wall."""
    _validate_point_count(point_count)
    points = [
        create_scan_point(angle_deg=angle_deg, distance_mm=radius_mm, quality=quality)
        for angle_deg in _angle_values(point_count)
    ]
    return build_scan_frame(
        points,
        timestamp_us=timestamp_us,
        frame_id=frame_id,
        source="synthetic_circle",
        metadata={"radius_mm": radius_mm},
    )


def generate_room_scan(
    *,
    point_count: int = 360,
    room_length_mm: int = 6000,
    room_width_mm: int = 4000,
    timestamp_us: int = 0,
    frame_id: int | None = 0,
    quality: int | None = 100,
) -> ScanFrame:
    """Generate a rectangular room scan with the LiDAR at the room center."""
    _validate_point_count(point_count)
    if room_length_mm <= 0 or room_width_mm <= 0:
        raise ValueError("room_length_mm and room_width_mm must be positive")

    points = [
        create_scan_point(
            angle_deg=angle_deg,
            distance_mm=_room_distance_mm(angle_deg, room_length_mm, room_width_mm),
            quality=quality,
        )
        for angle_deg in _angle_values(point_count)
    ]
    return build_scan_frame(
        points,
        timestamp_us=timestamp_us,
        frame_id=frame_id,
        source="synthetic_room",
        metadata={
            "room_length_mm": room_length_mm,
            "room_width_mm": room_width_mm,
        },
    )


def scan_to_json(scan: ScanFrame) -> str:
    """Serialize a synthetic scan frame for inspection."""
    payload = {
        "timestamp_us": scan.timestamp_us,
        "frame_id": scan.frame_id,
        "source": scan.source,
        "metadata": scan.metadata,
        "points": [
            {
                "angle_deg": point.angle_deg,
                "distance_mm": point.distance_mm,
                "quality": point.quality,
            }
            for point in scan.points
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _validate_point_count(point_count: int) -> None:
    if not isinstance(point_count, int) or point_count <= 0:
        raise ValueError("point_count must be a positive integer")


def _angle_values(point_count: int) -> list[float]:
    step_deg = 360.0 / point_count
    return [index * step_deg for index in range(point_count)]


def _room_distance_mm(
    angle_deg: float,
    room_length_mm: int,
    room_width_mm: int,
) -> int:
    angle_rad = math.radians(angle_deg)
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    half_length_mm = room_length_mm / 2.0
    half_width_mm = room_width_mm / 2.0
    distances = [
        distance_mm
        for distance_mm in (
            _axis_distance_mm(dx, half_length_mm),
            _axis_distance_mm(-dx, half_length_mm),
            _axis_distance_mm(dy, half_width_mm),
            _axis_distance_mm(-dy, half_width_mm),
        )
        if distance_mm is not None
    ]
    return int(round(min(distances)))


def _axis_distance_mm(direction_component: float, half_extent_mm: float) -> float | None:
    if direction_component <= 0.0:
        return None
    return half_extent_mm / direction_component
