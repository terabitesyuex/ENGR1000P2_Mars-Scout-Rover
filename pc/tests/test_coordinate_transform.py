from __future__ import annotations

import math

import pytest

from rplidar_c1_tools.coordinate_transform import (
    native_c1_angle_to_rover_deg,
    normalize_angle_deg,
    normalize_angle_rad,
    polar_to_cartesian,
    scan_frame_to_cartesian,
    scan_point_to_cartesian,
    transform_point_2d,
)
from rplidar_c1_tools.data_models import CartesianPoint, ScanFrame, ScanPoint, Transform2D
from rplidar_c1_tools.synthetic_scan import generate_circle_scan, generate_room_scan


ABS_TOL = 1e-9


def assert_close(actual: float, expected: float) -> None:
    assert math.isclose(actual, expected, abs_tol=ABS_TOL)


@pytest.mark.parametrize(
    ("angle_deg", "expected_deg"),
    [
        (0.0, 0.0),
        (360.0, 0.0),
        (720.0, 0.0),
        (-90.0, 270.0),
        (450.0, 90.0),
        (-720.0, -0.0),
    ],
)
def test_normalize_angle_deg(angle_deg: float, expected_deg: float) -> None:
    assert_close(normalize_angle_deg(angle_deg), expected_deg)


@pytest.mark.parametrize("angle_deg", [math.nan, math.inf, -math.inf])
def test_normalize_angle_deg_rejects_nonfinite(angle_deg: float) -> None:
    with pytest.raises(ValueError, match="angle_deg"):
        normalize_angle_deg(angle_deg)


def test_normalize_angle_rad_uses_half_open_pi_interval() -> None:
    assert_close(normalize_angle_rad(0.0), 0.0)
    assert_close(normalize_angle_rad(math.pi), -math.pi)
    assert_close(normalize_angle_rad(-math.pi), -math.pi)
    assert_close(normalize_angle_rad(3.0 * math.pi / 2.0), -math.pi / 2.0)


@pytest.mark.parametrize("angle_rad", [math.nan, math.inf, -math.inf])
def test_normalize_angle_rad_rejects_nonfinite(angle_rad: float) -> None:
    with pytest.raises(ValueError, match="angle_rad"):
        normalize_angle_rad(angle_rad)


@pytest.mark.parametrize(
    ("native_angle_deg", "expected_rover_deg"),
    [
        (0.0, 0.0),
        (90.0, 270.0),
        (180.0, 180.0),
        (270.0, 90.0),
        (360.0, 0.0),
        (-90.0, 90.0),
    ],
)
def test_native_c1_angle_to_rover_deg(
    native_angle_deg: float,
    expected_rover_deg: float,
) -> None:
    assert_close(native_c1_angle_to_rover_deg(native_angle_deg), expected_rover_deg)


@pytest.mark.parametrize(
    ("angle_deg", "expected_x_m", "expected_y_m"),
    [
        (0.0, 1.0, 0.0),
        (90.0, 0.0, 1.0),
        (180.0, -1.0, 0.0),
        (270.0, 0.0, -1.0),
        (45.0, math.sqrt(2.0) / 2.0, math.sqrt(2.0) / 2.0),
        (225.0, -math.sqrt(2.0) / 2.0, -math.sqrt(2.0) / 2.0),
    ],
)
def test_polar_to_cartesian_uses_rover_convention(
    angle_deg: float,
    expected_x_m: float,
    expected_y_m: float,
) -> None:
    x_m, y_m = polar_to_cartesian(angle_deg, 1000.0)

    assert_close(x_m, expected_x_m)
    assert_close(y_m, expected_y_m)


def test_polar_to_cartesian_allows_zero_distance() -> None:
    x_m, y_m = polar_to_cartesian(123.0, 0.0)

    assert_close(x_m, 0.0)
    assert_close(y_m, 0.0)


def test_polar_to_cartesian_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="distance_mm"):
        polar_to_cartesian(0.0, -1.0)
    with pytest.raises(ValueError, match="angle_deg"):
        polar_to_cartesian(math.nan, 1000.0)
    with pytest.raises(ValueError, match="distance_mm"):
        polar_to_cartesian(0.0, math.inf)


def test_scan_point_to_cartesian_preserves_source_metadata_without_mutation() -> None:
    point = ScanPoint(angle_deg=90.0, distance_mm=1000, quality=42)

    cartesian = scan_point_to_cartesian(point)

    assert isinstance(cartesian, CartesianPoint)
    assert_close(cartesian.x_m, 0.0)
    assert_close(cartesian.y_m, 1.0)
    assert cartesian.source_angle_deg == point.angle_deg
    assert cartesian.source_distance_mm == point.distance_mm
    assert cartesian.signal_quality == point.quality
    assert cartesian.valid
    assert point == ScanPoint(angle_deg=90.0, distance_mm=1000, quality=42)


def test_scan_point_to_cartesian_rejects_invalid_point() -> None:
    with pytest.raises(ValueError, match="distance_mm"):
        scan_point_to_cartesian(ScanPoint(angle_deg=0.0, distance_mm=-1))


def test_scan_frame_to_cartesian_preserves_order_by_default() -> None:
    frame = ScanFrame(
        timestamp_us=0,
        points=[
            ScanPoint(angle_deg=0.0, distance_mm=1000),
            ScanPoint(angle_deg=90.0, distance_mm=1000),
            ScanPoint(angle_deg=180.0, distance_mm=1000),
        ],
    )

    points = scan_frame_to_cartesian(frame)

    assert [point.source_angle_deg for point in points] == [0.0, 90.0, 180.0]
    assert [point.valid for point in points] == [True, True, True]


def test_scan_frame_to_cartesian_can_include_or_exclude_invalid_points() -> None:
    frame = ScanFrame(
        timestamp_us=0,
        points=[
            ScanPoint(angle_deg=0.0, distance_mm=1000),
            ScanPoint(angle_deg=0.0, distance_mm=-1),
            ScanPoint(angle_deg=90.0, distance_mm=1000),
        ],
    )

    included = scan_frame_to_cartesian(frame)
    excluded = scan_frame_to_cartesian(frame, include_invalid=False)

    assert [point.valid for point in included] == [True, False, True]
    assert len(excluded) == 2
    assert [point.source_angle_deg for point in excluded] == [0.0, 90.0]


def test_transform_point_2d_identity() -> None:
    point = CartesianPoint(1.0, 2.0, source_angle_deg=45.0, source_distance_mm=1000.0)

    transformed = transform_point_2d(point, Transform2D())

    assert_close(transformed.x_m, 1.0)
    assert_close(transformed.y_m, 2.0)
    assert transformed.source_angle_deg == point.source_angle_deg


def test_transform_point_2d_translation_only() -> None:
    point = CartesianPoint(1.0, 2.0, source_angle_deg=0.0, source_distance_mm=1000.0)
    transform = Transform2D(translation_x_m=3.0, translation_y_m=-4.0)

    transformed = transform_point_2d(point, transform)

    assert_close(transformed.x_m, 4.0)
    assert_close(transformed.y_m, -2.0)


@pytest.mark.parametrize(
    ("yaw_rad", "expected_x_m", "expected_y_m"),
    [
        (math.pi / 2.0, 0.0, 1.0),
        (-math.pi / 2.0, 0.0, -1.0),
        (math.pi, -1.0, 0.0),
    ],
)
def test_transform_point_2d_rotation(
    yaw_rad: float,
    expected_x_m: float,
    expected_y_m: float,
) -> None:
    point = CartesianPoint(1.0, 0.0, source_angle_deg=0.0, source_distance_mm=1000.0)

    transformed = transform_point_2d(point, Transform2D(yaw_rad=yaw_rad))

    assert_close(transformed.x_m, expected_x_m)
    assert_close(transformed.y_m, expected_y_m)


def test_transform_point_2d_rotation_plus_translation_and_input_unchanged() -> None:
    point = CartesianPoint(1.0, 0.0, source_angle_deg=0.0, source_distance_mm=1000.0)
    transform = Transform2D(
        translation_x_m=2.0,
        translation_y_m=3.0,
        yaw_rad=math.pi / 2.0,
    )

    transformed = transform_point_2d(point, transform)

    assert_close(transformed.x_m, 2.0)
    assert_close(transformed.y_m, 4.0)
    assert point == CartesianPoint(
        1.0,
        0.0,
        source_angle_deg=0.0,
        source_distance_mm=1000.0,
    )


def test_transform_point_2d_rejects_nonfinite_transform() -> None:
    point = CartesianPoint(1.0, 0.0, source_angle_deg=0.0, source_distance_mm=1000.0)

    with pytest.raises(ValueError, match="yaw_rad"):
        transform_point_2d(point, Transform2D(yaw_rad=math.inf))


def test_synthetic_circle_scan_converts_with_expected_radius() -> None:
    radius_mm = 1500
    frame = generate_circle_scan(point_count=16, radius_mm=radius_mm)

    points = scan_frame_to_cartesian(frame)

    assert len(points) == frame.point_count
    for point in points:
        assert math.isfinite(point.x_m)
        assert math.isfinite(point.y_m)
        assert_close(math.hypot(point.x_m, point.y_m), radius_mm / 1000.0)


def test_synthetic_room_scan_quadrants_are_not_mirrored() -> None:
    frame = generate_room_scan(point_count=8, room_length_mm=6000, room_width_mm=4000)

    points = scan_frame_to_cartesian(frame)
    by_angle = {point.source_angle_deg: point for point in points}

    assert by_angle[45.0].x_m > 0.0
    assert by_angle[45.0].y_m > 0.0
    assert by_angle[135.0].x_m < 0.0
    assert by_angle[135.0].y_m > 0.0
    assert by_angle[225.0].x_m < 0.0
    assert by_angle[225.0].y_m < 0.0
    assert by_angle[315.0].x_m > 0.0
    assert by_angle[315.0].y_m < 0.0
