from __future__ import annotations

from rplidar_c1_tools.replay import inspect_recording, iter_recording_entries
from rplidar_c1_tools.stm32_recording_bridge import (
    record_stm32_telemetry_stream,
    stm32_message_to_recording_sample,
)
from rplidar_c1_tools.stm32_sensor_models import Stm32TelemetryMessage
from rplidar_c1_tools.stm32_sensor_protocol import encode_stm32_telemetry_message
from rplidar_c1_tools.stm32_sensor_simulator import generate_synthetic_stm32_lines


def test_bridge_maps_each_message_type_with_units_and_source_sequence():
    cases = [
        (
            _message("ultrasonic", "ultrasonic_1", {"distance_mm": 500, "valid": True}),
            "ultrasonic",
            "distance_mm",
            500,
        ),
        (
            _message(
                "ground_edge",
                "tcrt5000_1",
                {"raw_state": 1, "polarity_verified": True, "interpreted_edge_detected": True},
            ),
            "ground_edge",
            "edge_detected",
            True,
        ),
        (
            _message(
                "hall_landmark",
                "hall_1",
                {"raw_state": 1, "polarity_verified": True, "interpreted_landmark_detected": True},
            ),
            "hall_landmark",
            "detected",
            True,
        ),
        (
            _message("illuminance", "bh1750_1", {"illuminance_lux": 320.0}),
            "illuminance",
            "illuminance_lux",
            320.0,
        ),
        (
            _message("barometer", "bmp280_1", {"temperature_c": 24.0, "pressure_pa": 101_325.0}),
            "barometer",
            "pressure_pa",
            101_325.0,
        ),
        (
            _message(
                "imu_raw",
                "mpu6050_1",
                {
                    "accel_x_raw": 0,
                    "accel_y_raw": 0,
                    "accel_z_raw": 16384,
                    "gyro_x_raw": 0,
                    "gyro_y_raw": 0,
                    "gyro_z_raw": 131,
                    "temperature_raw": 0,
                    "accel_range_g": 2,
                    "gyro_range_dps": 250,
                    "calibration_state": "uncalibrated",
                },
            ),
            "imu",
            "sensor_id",
            "mpu6050_1",
        ),
    ]

    for message, record_type, field_name, expected in cases:
        converted_record_type, sample = stm32_message_to_recording_sample(message)
        assert converted_record_type == record_type
        assert getattr(sample, field_name) == expected
        assert sample.timestamp_us == 42_000
        if hasattr(sample, "source_sequence"):
            assert sample.source_sequence == 7


def test_bridge_preserves_timeout_and_unverified_polarity_without_false_detection(tmp_path):
    lines = [
        encode_stm32_telemetry_message(
            _message(
                "ultrasonic",
                "ultrasonic_1",
                {"raw_echo_us": None, "valid": False},
                status="timeout",
            )
        ),
        encode_stm32_telemetry_message(
            _message(
                "ground_edge",
                "tcrt5000_1",
                {"raw_state": 1, "polarity_verified": False, "interpreted_edge_detected": None},
                sequence=8,
            )
        ),
        encode_stm32_telemetry_message(
            _message(
                "hall_landmark",
                "hall_1",
                {"raw_state": 1, "polarity_verified": False, "interpreted_landmark_detected": None},
                sequence=9,
            )
        ),
    ]
    output = tmp_path / "converted.jsonl"

    record_stm32_telemetry_stream(lines, output)
    entries = [entry.payload for entry in iter_recording_entries(output) if entry.payload["record_type"] != "header"]

    ultrasonic = entries[0]
    assert ultrasonic["record_type"] == "ultrasonic"
    assert ultrasonic["valid"] is False
    assert ultrasonic["distance_mm"] is None
    assert ultrasonic["status"] == "timeout"

    ground = entries[1]
    assert ground["edge_detected"] is None
    assert ground["raw_state"] == 1
    assert ground["polarity_verified"] is False

    hall = entries[2]
    assert hall["detected"] is None
    assert hall["raw_state"] == 1
    assert hall["polarity_verified"] is False


def test_recorded_stm32_session_passes_existing_recording_validation_and_inspection(tmp_path):
    output = tmp_path / "recording.jsonl"
    record_stm32_telemetry_stream(
        generate_synthetic_stm32_lines(cycles=2, scenario="nominal"),
        output,
    )

    summary = inspect_recording(output)

    assert summary.record_counts == {
        "ultrasonic": 6,
        "ground_edge": 4,
        "hall_landmark": 2,
        "illuminance": 2,
        "barometer": 2,
    }
    assert summary.first_timestamp_us == 0
    assert summary.last_timestamp_us == 100_000
    entries = [entry.payload for entry in iter_recording_entries(output)]
    assert [entry["sequence"] for entry in entries[1:]] == list(range(1, 17))


def test_recorded_phase32b_session_preserves_status_contracts(tmp_path):
    output = tmp_path / "phase32b_recording.jsonl"
    record_stm32_telemetry_stream(
        generate_synthetic_stm32_lines(cycles=1, scenario="phase32b_full_foundation"),
        output,
    )

    summary = inspect_recording(output)
    assert summary.record_counts["imu"] == 1
    assert summary.record_counts["subsystem_status"] == 1
    assert summary.record_counts["link_status"] == 1
    assert summary.record_counts["lidar_transport_stats"] == 1

    entries = [entry.payload for entry in iter_recording_entries(output)]
    status_record = next(entry for entry in entries if entry["record_type"] == "link_status")
    assert status_record["sensor_id"] == "esp32_link"
    assert status_record["crc_errors"] == 0
    lidar_record = next(entry for entry in entries if entry["record_type"] == "lidar_transport_stats")
    assert lidar_record["sensor_id"] == "c1_1"
    assert lidar_record["overflow_count"] == 0


def _message(
    message_type: str,
    sensor_id: str,
    payload: dict[str, object],
    *,
    sequence: int = 7,
    status: str = "simulated",
) -> Stm32TelemetryMessage:
    return Stm32TelemetryMessage(
        sequence=sequence,
        timestamp_ms=42,
        message_type=message_type,
        sensor_id=sensor_id,
        payload=payload,
        status=status,
    )

