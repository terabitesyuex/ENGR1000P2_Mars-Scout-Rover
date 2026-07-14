from __future__ import annotations

from rplidar_c1_tools.synthetic_scan import SyntheticRoomConfig, SyntheticScanSource


def test_synthetic_source_yields_completed_scan_without_hardware() -> None:
    source = SyntheticScanSource(SyntheticRoomConfig(scan_count=1, noise_std_mm=0.0))
    scan = next(source.scans())

    assert scan.complete
    assert scan.scan_id == 0
    assert scan.received_point_count > 300
    assert scan.valid_point_count > 250
    assert scan.rejected_point_count >= 3
    assert scan.samples[0].scan_start
    assert all(not sample.scan_start for sample in scan.samples[1:])


def test_synthetic_source_is_deterministic() -> None:
    config = SyntheticRoomConfig(scan_count=1, noise_std_mm=2.0, random_seed=123)
    first = next(SyntheticScanSource(config).scans())
    second = next(SyntheticScanSource(config).scans())

    first_distances = [sample.distance_mm for sample in first.samples]
    second_distances = [sample.distance_mm for sample in second.samples]
    assert first_distances == second_distances


def test_synthetic_scan_contains_missing_and_invalid_data() -> None:
    scan = next(SyntheticScanSource(SyntheticRoomConfig(noise_std_mm=0.0)).scans())
    angles = {round(sample.angle_clockwise_deg) for sample in scan.samples}
    distances = [sample.distance_mm for sample in scan.samples]

    assert 210 not in angles
    assert 0 in distances
    assert 14000 in distances
    assert any(not sample.filter_valid for sample in scan.samples)
