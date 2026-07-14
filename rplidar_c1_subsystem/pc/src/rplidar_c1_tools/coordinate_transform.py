"""Pure coordinate conversion helpers for C1-native and rover frames."""

from __future__ import annotations

import math


def normalize_angle_deg(angle_deg: float) -> float:
    """Return an angle in the half-open range [0, 360)."""
    normalized = math.fmod(angle_deg, 360.0)
    if normalized < 0.0:
        normalized += 360.0
    if math.isclose(normalized, 360.0, abs_tol=1e-12):
        return 0.0
    return normalized


def native_clockwise_to_robot_angle_deg(native_clockwise_angle_deg: float) -> float:
    """Convert C1 clockwise-native angle to rover counterclockwise angle."""
    return normalize_angle_deg(-native_clockwise_angle_deg)


def polar_to_cartesian_m(
    native_clockwise_angle_deg: float,
    distance_mm: float,
) -> tuple[float, float]:
    """Convert native clockwise polar coordinates to rover-frame metres."""
    robot_angle_deg = native_clockwise_to_robot_angle_deg(native_clockwise_angle_deg)
    angle_rad = math.radians(robot_angle_deg)
    distance_m = distance_mm / 1000.0
    return distance_m * math.cos(angle_rad), distance_m * math.sin(angle_rad)
