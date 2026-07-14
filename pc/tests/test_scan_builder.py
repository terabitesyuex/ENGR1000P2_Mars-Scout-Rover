from __future__ import annotations

import math

import pytest

from rplidar_c1_tools.data_models import ScanFrame, ScanPoint
from rplidar_c1_tools.scan_builder import (
    ScanValidationError,
    build_scan_frame,
    create_scan_point,
)


def test_valid_scan_points_create_scan_frame() -> None:
    points = [
        create_scan_point(angle_deg=0.0, distance_mm=1000, quality=10),
        create_scan_point(angle_deg=90.0, distance_mm=1500),
    ]

    frame = build_scan_frame(
        points,
        timestamp_us=123,
        frame_id=7,
        source="unit_test",
        metadata={"mode": "synthetic"},
    )

    assert isinstance(frame, ScanFrame)
    assert frame.timestamp_us == 123
    assert frame.frame_id == 7
    assert frame.source == "unit_test"
    assert frame.point_count == 2
    assert frame.metadata["mode"] == "synthetic"


def test_negative_distance_is_rejected_clearly() -> None:
    with pytest.raises(ScanValidationError, match="distance_mm"):
        create_scan_point(angle_deg=0.0, distance_mm=-1)


def test_nonfinite_angle_is_rejected_clearly() -> None:
    with pytest.raises(ScanValidationError, match="angle_deg"):
        create_scan_point(angle_deg=math.inf, distance_mm=1000)


def test_angle_outside_unified_range_is_rejected_clearly() -> None:
    with pytest.raises(ScanValidationError, match=r"\[0, 360\)"):
        create_scan_point(angle_deg=360.0, distance_mm=1000)


def test_invalid_quality_is_rejected_clearly() -> None:
    with pytest.raises(ScanValidationError, match="quality"):
        create_scan_point(angle_deg=0.0, distance_mm=1000, quality=-1)


def test_empty_frame_is_rejected_clearly() -> None:
    with pytest.raises(ScanValidationError, match="at least one point"):
        build_scan_frame([], timestamp_us=0)


def test_builder_rejects_non_scan_point() -> None:
    with pytest.raises(ScanValidationError, match="ScanPoint"):
        build_scan_frame([object()], timestamp_us=0)  # type: ignore[list-item]


def test_builder_accepts_existing_scan_point_instances() -> None:
    frame = build_scan_frame(
        [ScanPoint(angle_deg=45.0, distance_mm=2000)],
        timestamp_us=10,
    )

    assert frame.points[0].angle_deg == 45.0
    assert frame.points[0].distance_mm == 2000
