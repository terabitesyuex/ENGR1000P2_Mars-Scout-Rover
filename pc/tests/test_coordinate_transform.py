from __future__ import annotations

import math

from rplidar_c1_tools.coordinate_transform import (
    native_clockwise_to_robot_angle_deg,
    normalize_angle_deg,
    polar_to_cartesian_m,
)


def assert_close(actual: float, expected: float) -> None:
    assert math.isclose(actual, expected, abs_tol=1e-9)


def test_cardinal_native_angles_convert_to_rover_frame() -> None:
    assert_close(native_clockwise_to_robot_angle_deg(0.0), 0.0)
    assert_close(native_clockwise_to_robot_angle_deg(90.0), 270.0)
    assert_close(native_clockwise_to_robot_angle_deg(180.0), 180.0)
    assert_close(native_clockwise_to_robot_angle_deg(270.0), 90.0)


def test_polar_to_cartesian_uses_metres_and_rover_axes() -> None:
    x_m, y_m = polar_to_cartesian_m(0.0, 1000.0)
    assert_close(x_m, 1.0)
    assert_close(y_m, 0.0)

    x_m, y_m = polar_to_cartesian_m(90.0, 1000.0)
    assert abs(x_m) < 1e-9
    assert_close(y_m, -1.0)

    x_m, y_m = polar_to_cartesian_m(270.0, 1000.0)
    assert abs(x_m) < 1e-9
    assert_close(y_m, 1.0)


def test_angle_normalization() -> None:
    assert_close(normalize_angle_deg(-45.0), 315.0)
    assert_close(normalize_angle_deg(405.0), 45.0)
    assert_close(normalize_angle_deg(720.0), 0.0)
