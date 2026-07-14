from __future__ import annotations

from rplidar_c1_tools.data_models import ScanFrame
from rplidar_c1_tools.synthetic_scan import (
    SyntheticRoomConfig,
    SyntheticScanSource,
    generate_circle_scan,
    generate_room_scan,
)


def test_circle_scan_generation_returns_scan_frame() -> None:
    scan = generate_circle_scan(point_count=8, radius_mm=1500)

    assert isinstance(scan, ScanFrame)
    assert scan.source == "synthetic_circle"
    assert scan.point_count == 8
    assert [point.distance_mm for point in scan.points] == [1500] * 8
    assert scan.points[0].angle_deg == 0.0
    assert scan.points[-1].angle_deg == 315.0


def test_room_scan_cardinal_distances_are_reasonable() -> None:
    scan = generate_room_scan(
        point_count=4,
        room_length_mm=6000,
        room_width_mm=4000,
    )

    assert isinstance(scan, ScanFrame)
    assert scan.source == "synthetic_room"
    assert [point.angle_deg for point in scan.points] == [0.0, 90.0, 180.0, 270.0]
    assert [point.distance_mm for point in scan.points] == [3000, 2000, 3000, 2000]


def test_synthetic_room_scan_is_deterministic() -> None:
    first = generate_room_scan(point_count=16)
    second = generate_room_scan(point_count=16)

    assert first.points == second.points
    assert first.metadata == second.metadata


def test_synthetic_scan_source_yields_configured_frames() -> None:
    source = SyntheticScanSource(
        SyntheticRoomConfig(scan_count=2, angle_step_deg=90.0)
    )
    scans = list(source.scans())

    assert len(scans) == 2
    assert all(isinstance(scan, ScanFrame) for scan in scans)
    assert [scan.frame_id for scan in scans] == [0, 1]
    assert all(scan.point_count == 4 for scan in scans)
