"""Pure coordinate and frame transforms for the rover convention.

Project convention:
- +x points forward from the rover;
- +y points left;
- positive yaw is counterclockwise;
- angles are degrees unless a name ends in `_rad`;
- Cartesian distances are metres;
- LiDAR input distances are millimetres.
"""

from __future__ import annotations

import math

from .data_models import CartesianPoint, ScanFrame, ScanPoint, Transform2D


def normalize_angle_deg(angle_deg: float) -> float:
    """Return an angle in the half-open range [0, 360)."""
    _require_finite(angle_deg, "angle_deg")
    normalized = math.fmod(angle_deg, 360.0)
    if normalized < 0.0:
        normalized += 360.0
    if math.isclose(normalized, 360.0, abs_tol=1e-12):
        return 0.0
    return normalized


def normalize_angle_rad(angle_rad: float) -> float:
    """Return an angle in the half-open range [-pi, pi)."""
    _require_finite(angle_rad, "angle_rad")
    two_pi = 2.0 * math.pi
    normalized = math.fmod(angle_rad + math.pi, two_pi)
    if normalized < 0.0:
        normalized += two_pi
    return normalized - math.pi


def native_c1_angle_to_rover_deg(native_angle_deg: float) -> float:
    """Convert C1 clockwise-native angle to rover counterclockwise angle."""
    return normalize_angle_deg(-native_angle_deg)


def native_clockwise_to_robot_angle_deg(native_clockwise_angle_deg: float) -> float:
    """Backward-compatible alias for `native_c1_angle_to_rover_deg`."""
    return native_c1_angle_to_rover_deg(native_clockwise_angle_deg)


def polar_to_cartesian(
    angle_deg: float,
    distance_mm: float,
) -> tuple[float, float]:
    """Convert rover-frame polar coordinates to Cartesian metres.

    `angle_deg` is already in the project rover convention. This function does
    not apply native C1 clockwise-angle conversion.
    """
    _require_finite(angle_deg, "angle_deg")
    _require_finite(distance_mm, "distance_mm")
    if distance_mm < 0.0:
        raise ValueError("distance_mm must not be negative")
    angle_rad = math.radians(angle_deg)
    distance_m = distance_mm / 1000.0
    return distance_m * math.cos(angle_rad), distance_m * math.sin(angle_rad)


def polar_to_cartesian_m(angle_deg: float, distance_mm: float) -> tuple[float, float]:
    """Backward-compatible alias for rover-frame `polar_to_cartesian`."""
    return polar_to_cartesian(angle_deg, distance_mm)


def scan_point_to_cartesian(point: ScanPoint) -> CartesianPoint:
    """Convert one valid `ScanPoint` to one immutable Cartesian point."""
    if not isinstance(point, ScanPoint):
        raise ValueError("point must be a ScanPoint")
    x_m, y_m = polar_to_cartesian(point.angle_deg, point.distance_mm)
    return CartesianPoint(
        x_m=x_m,
        y_m=y_m,
        source_angle_deg=point.angle_deg,
        source_distance_mm=float(point.distance_mm),
        signal_quality=point.quality,
        valid=True,
    )


def scan_frame_to_cartesian(
    frame: ScanFrame,
    *,
    include_invalid: bool = True,
) -> tuple[CartesianPoint, ...]:
    """Convert a `ScanFrame` while preserving point order.

    By default invalid points are included as `CartesianPoint(valid=False)`
    placeholders so callers can detect data loss. Set `include_invalid=False`
    to omit invalid points explicitly.
    """
    if not isinstance(frame, ScanFrame):
        raise ValueError("frame must be a ScanFrame")

    converted: list[CartesianPoint] = []
    for point in frame.points:
        try:
            converted.append(scan_point_to_cartesian(point))
        except ValueError:
            if include_invalid:
                converted.append(_invalid_cartesian_point(point))
    return tuple(converted)


def transform_point_2d(
    point: CartesianPoint,
    transform: Transform2D,
) -> CartesianPoint:
    """Apply a finite 2D rigid transform to one Cartesian point."""
    if not isinstance(point, CartesianPoint):
        raise ValueError("point must be a CartesianPoint")
    if not isinstance(transform, Transform2D):
        raise ValueError("transform must be a Transform2D")
    _require_finite(point.x_m, "point.x_m")
    _require_finite(point.y_m, "point.y_m")
    _require_finite(transform.translation_x_m, "transform.translation_x_m")
    _require_finite(transform.translation_y_m, "transform.translation_y_m")
    _require_finite(transform.yaw_rad, "transform.yaw_rad")

    cos_yaw = math.cos(transform.yaw_rad)
    sin_yaw = math.sin(transform.yaw_rad)
    x_m = (
        cos_yaw * point.x_m
        - sin_yaw * point.y_m
        + transform.translation_x_m
    )
    y_m = (
        sin_yaw * point.x_m
        + cos_yaw * point.y_m
        + transform.translation_y_m
    )
    return CartesianPoint(
        x_m=x_m,
        y_m=y_m,
        source_angle_deg=point.source_angle_deg,
        source_distance_mm=point.source_distance_mm,
        signal_quality=point.signal_quality,
        valid=point.valid,
    )


def _invalid_cartesian_point(point: ScanPoint) -> CartesianPoint:
    if not isinstance(point, ScanPoint):
        raise ValueError("point must be a ScanPoint")
    return CartesianPoint(
        x_m=math.nan,
        y_m=math.nan,
        source_angle_deg=point.angle_deg,
        source_distance_mm=_safe_float(point.distance_mm),
        signal_quality=point.quality,
        valid=False,
    )


def _require_finite(value: float, name: str) -> None:
    try:
        finite = math.isfinite(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not finite:
        raise ValueError(f"{name} must be finite")


def _safe_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
