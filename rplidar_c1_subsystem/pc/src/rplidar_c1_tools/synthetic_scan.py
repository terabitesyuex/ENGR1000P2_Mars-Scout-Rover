"""Deterministic synthetic scan source used before live hardware integration."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import random
from typing import Iterator

from .coordinate_transform import (
    native_clockwise_to_robot_angle_deg,
    polar_to_cartesian_m,
)
from .data_models import LidarSample, LidarScan


@dataclass(frozen=True, slots=True)
class SyntheticRoomConfig:
    scan_count: int = 1
    scan_frequency_hz: float = 10.0
    angle_step_deg: float = 1.0
    noise_std_mm: float = 5.0
    random_seed: int = 7
    minimum_distance_mm: int = 50
    maximum_distance_mm: int = 12000
    front_wall_x_m: float = 4.0
    rear_wall_x_m: float = -2.0
    left_wall_y_m: float = 3.0
    right_wall_y_m: float = -3.0
    doorway_center_y_m: float = 0.0
    doorway_width_m: float = 1.0
    circle_center_x_m: float = 1.8
    circle_center_y_m: float = 1.0
    circle_radius_m: float = 0.35
    box_min_x_m: float = 0.6
    box_max_x_m: float = 1.4
    box_min_y_m: float = -1.9
    box_max_y_m: float = -1.1
    missing_sector_start_clockwise_deg: float = 205.0
    missing_sector_width_deg: float = 25.0
    zero_distance_angles_deg: tuple[float, ...] = (18.0, 122.0)
    out_of_range_angles_deg: tuple[float, ...] = (315.0,)
    spike_angles_deg: tuple[float, ...] = (72.0,)


class SyntheticScanSource:
    """Produce C1-style native clockwise scans without opening serial ports."""

    def __init__(self, config: SyntheticRoomConfig | None = None) -> None:
        self._config = config or SyntheticRoomConfig()
        if self._config.scan_frequency_hz <= 0.0:
            raise ValueError("scan_frequency_hz must be positive")
        if self._config.angle_step_deg <= 0.0:
            raise ValueError("angle_step_deg must be positive")

    def scans(self) -> Iterator[LidarScan]:
        for scan_id in range(self._config.scan_count):
            yield self.build_scan(scan_id)

    def build_scan(self, scan_id: int = 0) -> LidarScan:
        rng = random.Random(self._config.random_seed + scan_id)
        period_us = int(1_000_000 / self._config.scan_frequency_hz)
        start_timestamp_us = scan_id * period_us
        samples: list[LidarSample] = []
        angles = _angle_values(self._config.angle_step_deg)

        for index, native_angle_deg in enumerate(angles):
            if _in_missing_sector(
                native_angle_deg,
                self._config.missing_sector_start_clockwise_deg,
                self._config.missing_sector_width_deg,
            ):
                continue

            timestamp_us = start_timestamp_us + int(period_us * (index / len(angles)))
            distance_mm = self._distance_for_angle_mm(native_angle_deg, rng)
            protocol_valid = True
            range_valid = (
                self._config.minimum_distance_mm
                <= distance_mm
                <= self._config.maximum_distance_mm
            )
            reflectivity_raw = 80 if range_valid else 0
            quality_valid = reflectivity_raw > 0
            x_m, y_m = polar_to_cartesian_m(native_angle_deg, distance_mm)

            samples.append(
                LidarSample(
                    timestamp_us=timestamp_us,
                    scan_id=scan_id,
                    angle_clockwise_deg=native_angle_deg,
                    angle_robot_deg=native_clockwise_to_robot_angle_deg(
                        native_angle_deg
                    ),
                    distance_mm=distance_mm,
                    reflectivity_raw=reflectivity_raw,
                    scan_start=not samples,
                    protocol_valid=protocol_valid,
                    range_valid=range_valid,
                    quality_valid=quality_valid,
                    filter_valid=protocol_valid and range_valid and quality_valid,
                    x_m=x_m,
                    y_m=y_m,
                )
            )

        valid_count = sum(1 for sample in samples if sample.filter_valid)
        return LidarScan(
            scan_id=scan_id,
            start_timestamp_us=start_timestamp_us,
            end_timestamp_us=start_timestamp_us + period_us,
            samples=tuple(samples),
            received_point_count=len(samples),
            valid_point_count=valid_count,
            rejected_point_count=len(samples) - valid_count,
            estimated_scan_frequency_hz=self._config.scan_frequency_hz,
            complete=True,
        )

    def _distance_for_angle_mm(
        self,
        native_angle_deg: float,
        rng: random.Random,
    ) -> int:
        if _near_any_angle(native_angle_deg, self._config.zero_distance_angles_deg):
            return 0
        if _near_any_angle(native_angle_deg, self._config.out_of_range_angles_deg):
            return self._config.maximum_distance_mm + 2000
        if _near_any_angle(native_angle_deg, self._config.spike_angles_deg):
            return 150

        robot_angle_rad = math.radians(
            native_clockwise_to_robot_angle_deg(native_angle_deg)
        )
        direction = (math.cos(robot_angle_rad), math.sin(robot_angle_rad))
        hit_distance_m = self._raycast_room(direction)
        noisy_mm = hit_distance_m * 1000.0 + rng.gauss(0.0, self._config.noise_std_mm)
        return max(0, int(round(noisy_mm)))

    def _raycast_room(self, direction: tuple[float, float]) -> float:
        distances: list[float] = []
        dx, dy = direction

        _append_wall_hits(distances, dx, dy, self._config)
        circle_hit = _ray_circle_distance(
            dx,
            dy,
            self._config.circle_center_x_m,
            self._config.circle_center_y_m,
            self._config.circle_radius_m,
        )
        if circle_hit is not None:
            distances.append(circle_hit)

        distances.extend(
            _ray_rectangle_distances(
                dx,
                dy,
                self._config.box_min_x_m,
                self._config.box_max_x_m,
                self._config.box_min_y_m,
                self._config.box_max_y_m,
            )
        )
        if not distances:
            return self._config.maximum_distance_mm / 1000.0
        return min(distance for distance in distances if distance > 0.0)


def scan_to_json(scan: LidarScan) -> str:
    """Serialize a scan for inspection without defining a recording format."""
    payload = {
        "scan_id": scan.scan_id,
        "start_timestamp_us": scan.start_timestamp_us,
        "end_timestamp_us": scan.end_timestamp_us,
        "received_point_count": scan.received_point_count,
        "valid_point_count": scan.valid_point_count,
        "rejected_point_count": scan.rejected_point_count,
        "samples": [
            {
                "timestamp_us": sample.timestamp_us,
                "angle_clockwise_deg": sample.angle_clockwise_deg,
                "angle_robot_deg": sample.angle_robot_deg,
                "distance_mm": sample.distance_mm,
                "filter_valid": sample.filter_valid,
                "x_m": sample.x_m,
                "y_m": sample.y_m,
            }
            for sample in scan.samples
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _angle_values(angle_step_deg: float) -> list[float]:
    count = int(math.ceil(360.0 / angle_step_deg))
    return [min(index * angle_step_deg, 360.0 - 1e-9) for index in range(count)]


def _in_missing_sector(angle_deg: float, start_deg: float, width_deg: float) -> bool:
    if width_deg <= 0.0:
        return False
    offset = (angle_deg - start_deg) % 360.0
    return offset < width_deg


def _near_any_angle(angle_deg: float, targets_deg: tuple[float, ...]) -> bool:
    return any(abs(((angle_deg - target + 180.0) % 360.0) - 180.0) < 0.5 for target in targets_deg)


def _append_wall_hits(
    distances: list[float],
    dx: float,
    dy: float,
    config: SyntheticRoomConfig,
) -> None:
    front = _ray_vertical_segment_distance(
        dx,
        dy,
        config.front_wall_x_m,
        config.right_wall_y_m,
        config.left_wall_y_m,
    )
    if front is not None and not _inside_doorway(front, dy, config):
        distances.append(front)

    rear = _ray_vertical_segment_distance(
        dx,
        dy,
        config.rear_wall_x_m,
        config.right_wall_y_m,
        config.left_wall_y_m,
    )
    if rear is not None:
        distances.append(rear)

    left = _ray_horizontal_segment_distance(
        dx,
        dy,
        config.left_wall_y_m,
        config.rear_wall_x_m,
        config.front_wall_x_m,
    )
    if left is not None:
        distances.append(left)

    right = _ray_horizontal_segment_distance(
        dx,
        dy,
        config.right_wall_y_m,
        config.rear_wall_x_m,
        config.front_wall_x_m,
    )
    if right is not None:
        distances.append(right)


def _inside_doorway(
    distance_m: float,
    dy: float,
    config: SyntheticRoomConfig,
) -> bool:
    hit_y_m = distance_m * dy
    half_width = config.doorway_width_m / 2.0
    return abs(hit_y_m - config.doorway_center_y_m) <= half_width


def _ray_vertical_segment_distance(
    dx: float,
    dy: float,
    x_m: float,
    y_min_m: float,
    y_max_m: float,
) -> float | None:
    if math.isclose(dx, 0.0, abs_tol=1e-12):
        return None
    distance_m = x_m / dx
    if distance_m <= 0.0:
        return None
    y_m = distance_m * dy
    if y_min_m <= y_m <= y_max_m:
        return distance_m
    return None


def _ray_horizontal_segment_distance(
    dx: float,
    dy: float,
    y_m: float,
    x_min_m: float,
    x_max_m: float,
) -> float | None:
    if math.isclose(dy, 0.0, abs_tol=1e-12):
        return None
    distance_m = y_m / dy
    if distance_m <= 0.0:
        return None
    x_m = distance_m * dx
    if x_min_m <= x_m <= x_max_m:
        return distance_m
    return None


def _ray_circle_distance(
    dx: float,
    dy: float,
    center_x_m: float,
    center_y_m: float,
    radius_m: float,
) -> float | None:
    projection_m = center_x_m * dx + center_y_m * dy
    center_distance_sq_m = center_x_m * center_x_m + center_y_m * center_y_m
    closest_sq_m = center_distance_sq_m - projection_m * projection_m
    radius_sq_m = radius_m * radius_m
    if projection_m <= 0.0 or closest_sq_m > radius_sq_m:
        return None
    offset_m = math.sqrt(max(0.0, radius_sq_m - closest_sq_m))
    distance_m = projection_m - offset_m
    return distance_m if distance_m > 0.0 else None


def _ray_rectangle_distances(
    dx: float,
    dy: float,
    x_min_m: float,
    x_max_m: float,
    y_min_m: float,
    y_max_m: float,
) -> list[float]:
    distances: list[float] = []
    for x_m in (x_min_m, x_max_m):
        hit = _ray_vertical_segment_distance(dx, dy, x_m, y_min_m, y_max_m)
        if hit is not None:
            distances.append(hit)
    for y_m in (y_min_m, y_max_m):
        hit = _ray_horizontal_segment_distance(dx, dy, y_m, x_min_m, x_max_m)
        if hit is not None:
            distances.append(hit)
    return distances
