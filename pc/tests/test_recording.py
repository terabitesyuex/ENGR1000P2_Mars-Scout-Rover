from __future__ import annotations

import json
import math

import pytest

from rplidar_c1_tools import (
    BarometerSample,
    GroundEdgeSample,
    HallLandmarkSample,
    IlluminanceSample,
    ImuSample,
    MultiSensorRecorder,
    RecordingError,
    RoverPose,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    UltrasonicSample,
    default_sensor_inventory,
    generate_circle_scan,
    read_recording_header,
)
from rplidar_c1_tools.replay import inspect_recording, iter_lidar_scans, iter_recording_entries


def test_writer_defaults_to_the_single_physical_c1_inventory(tmp_path):
    path = tmp_path / "single_c1_session.jsonl"
    with MultiSensorRecorder(path, created_unix_us=123):
        pass

    header = read_recording_header(path)
    lidar_sensors = [
        sensor for sensor in header["sensor_inventory"] if sensor["sensor_type"] == "rplidar_c1"
    ]
    assert [sensor["sensor_id"] for sensor in lidar_sensors] == ["c1_1"]


def test_writer_supports_explicit_c1_2_software_compatibility_inventory(tmp_path):
    path = tmp_path / "session.jsonl"
    with MultiSensorRecorder(
        path,
        sensor_inventory=default_sensor_inventory(lidar_count=2),
        created_unix_us=123,
    ) as recorder:
        recorder.write_lidar_scan("c1_1", generate_circle_scan(point_count=4))
        recorder.write_lidar_scan("c1_2", generate_circle_scan(point_count=4))

    header = read_recording_header(path)
    assert header["schema_name"] == SCHEMA_NAME
    assert header["schema_version"] == SCHEMA_VERSION
    assert header["created_unix_us"] == 123
    assert header["coordinate_convention"]["angle_zero"] == "forward"
    assert header["coordinate_convention"]["positive_angle"] == "counterclockwise"
    sensor_ids = {sensor["sensor_id"] for sensor in header["sensor_inventory"]}
    assert {"c1_1", "c1_2"}.issubset(sensor_ids)


def test_lidar_recording_preserves_scan_frame_point_order_units_and_pose(tmp_path):
    path = tmp_path / "session.jsonl"
    pose = RoverPose(timestamp_us=0, x_m=1.0, y_m=2.0, yaw_rad=0.25)
    scan = generate_circle_scan(point_count=8, radius_mm=1500, timestamp_us=10, frame_id=7)

    with MultiSensorRecorder(path) as recorder:
        recorder.write_lidar_scan("c1_1", scan, pose=pose)

    [record] = list(iter_lidar_scans(path))
    assert record.sensor_id == "c1_1"
    assert record.scan_frame.frame_id == 7
    assert record.scan_frame.timestamp_us == 10
    assert [point.angle_deg for point in record.scan_frame.points] == [
        point.angle_deg for point in scan.points
    ]
    assert [point.distance_mm for point in record.scan_frame.points] == [1500] * 8
    assert record.rover_pose == pose


def test_writer_supports_all_phase24_auxiliary_record_types(tmp_path):
    path = tmp_path / "session.jsonl"
    with MultiSensorRecorder(path) as recorder:
        recorder.write_rover_pose(RoverPose(timestamp_us=0, x_m=0.0, y_m=0.0, yaw_rad=0.0))
        recorder.write_imu_sample(
            ImuSample(
                timestamp_us=0,
                accel_x_mps2=0.0,
                accel_y_mps2=0.0,
                accel_z_mps2=9.80665,
                gyro_x_radps=0.0,
                gyro_y_radps=0.0,
                gyro_z_radps=0.1,
                temperature_c=24.0,
            )
        )
        recorder.write_ultrasonic_sample(
            UltrasonicSample(timestamp_us=0, sensor_id="ultrasonic_1", distance_mm=500)
        )
        recorder.write_ground_edge_sample(
            GroundEdgeSample(timestamp_us=0, sensor_id="tcrt5000_1", edge_detected=False)
        )
        recorder.write_hall_landmark_sample(
            HallLandmarkSample(timestamp_us=0, detected=True, raw_value=1)
        )
        recorder.write_illuminance_sample(
            IlluminanceSample(timestamp_us=0, illuminance_lux=320.0)
        )
        recorder.write_barometer_sample(
            BarometerSample(timestamp_us=0, temperature_c=24.5, pressure_pa=101_325.0)
        )

    record_types = [entry.payload["record_type"] for entry in iter_recording_entries(path)]
    assert record_types == [
        "header",
        "rover_pose",
        "imu",
        "ultrasonic",
        "ground_edge",
        "hall_landmark",
        "illuminance",
        "barometer",
    ]


def test_streaming_writer_flushes_incremental_records_before_close(tmp_path):
    path = tmp_path / "session.jsonl"
    recorder = MultiSensorRecorder(path)
    recorder.open()
    recorder.write_lidar_scan("c1_1", generate_circle_scan(point_count=4))

    lines_before_close = path.read_text(encoding="utf-8").splitlines()
    assert len(lines_before_close) == 2

    recorder.close()


def test_writer_refuses_overwrite_unless_explicit(tmp_path):
    path = tmp_path / "session.jsonl"
    with MultiSensorRecorder(path):
        pass

    with pytest.raises(RecordingError, match="already exists"):
        with MultiSensorRecorder(path):
            pass

    with MultiSensorRecorder(path, overwrite=True):
        pass


def test_writer_rejects_unknown_sensor_and_duplicate_sensor_inventory(tmp_path):
    with MultiSensorRecorder(tmp_path / "session.jsonl") as recorder:
        with pytest.raises(RecordingError, match="unknown sensor_id"):
            recorder.write_lidar_scan("front_lidar", generate_circle_scan(point_count=4))

    inventory = default_sensor_inventory(lidar_count=1)
    duplicate_inventory = inventory + (inventory[0],)
    with pytest.raises(RecordingError, match="duplicate sensor_id"):
        MultiSensorRecorder(tmp_path / "bad.jsonl", sensor_inventory=duplicate_inventory)


def test_writer_rejects_non_json_nan_payload(tmp_path):
    with MultiSensorRecorder(tmp_path / "session.jsonl") as recorder:
        with pytest.raises(RecordingError, match="accel_x_mps2 must be finite"):
            recorder.write_imu_sample(
                ImuSample(
                    timestamp_us=0,
                    accel_x_mps2=math.nan,
                    accel_y_mps2=0.0,
                    accel_z_mps2=9.8,
                    gyro_x_radps=0.0,
                    gyro_y_radps=0.0,
                    gyro_z_radps=0.0,
                )
            )


def test_inspection_counts_lidar_and_auxiliary_records(tmp_path):
    path = tmp_path / "session.jsonl"
    with MultiSensorRecorder(
        path,
        sensor_inventory=default_sensor_inventory(lidar_count=2),
    ) as recorder:
        recorder.write_lidar_scan("c1_1", generate_circle_scan(point_count=4))
        recorder.write_lidar_scan("c1_2", generate_circle_scan(point_count=4))
        recorder.write_illuminance_sample(IlluminanceSample(timestamp_us=0, illuminance_lux=10.0))

    summary = inspect_recording(path)

    assert summary.lidar_scan_counts == {"c1_1": 1, "c1_2": 1}
    assert summary.record_counts["lidar_scan"] == 2
    assert summary.record_counts["illuminance"] == 1
    assert "c1_1" in summary.to_text()
    assert "bh1750_1" in summary.sensor_ids


def test_json_lines_are_plain_utf8_json_objects(tmp_path):
    path = tmp_path / "session.jsonl"
    with MultiSensorRecorder(path) as recorder:
        recorder.write_lidar_scan("c1_1", generate_circle_scan(point_count=4))

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        assert isinstance(json.loads(line), dict)
