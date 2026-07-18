from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from rplidar_c1_tools.mecanum_odometry import EncoderConfiguration, MecanumGeometry
from rplidar_c1_tools.mecanum_odometry_simulator import (
    MECANUM_ODOMETRY_SCENARIOS,
    generate_mecanum_odometry_samples,
    generate_mecanum_odometry_telemetry_lines,
)
from rplidar_c1_tools.replay import inspect_recording, iter_recording_entries
from rplidar_c1_tools.stm32_recording_bridge import record_stm32_telemetry_stream
from rplidar_c1_tools.stm32_sensor_protocol import (
    Stm32TelemetryFormatError,
    iter_stm32_telemetry,
    parse_stm32_telemetry_line,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_GEOMETRY = MecanumGeometry(0.05, 0.18, 0.16)
SYNTHETIC_ENCODERS = EncoderConfiguration(2048.0, 1, 1, 1, 1)


@pytest.mark.parametrize("scenario", MECANUM_ODOMETRY_SCENARIOS)
def test_every_required_scenario_generates_deterministic_samples(scenario: str):
    kwargs = {
        "geometry": SYNTHETIC_GEOMETRY,
        "encoder_configuration": SYNTHETIC_ENCODERS,
        "scenario": scenario,
        "step_count": 4,
        "interval_ms": 100,
    }
    first = generate_mecanum_odometry_samples(**kwargs)
    second = generate_mecanum_odometry_samples(**kwargs)
    assert first == second
    assert len(first) == 4
    assert [sample.timestamp_ms for sample in first] == [100, 200, 300, 400]
    assert all(sample.interval_ms == 100 for sample in first)


def test_stationary_scenario_preserves_zero_pose_and_counts():
    samples = generate_mecanum_odometry_samples(
        geometry=SYNTHETIC_GEOMETRY,
        encoder_configuration=SYNTHETIC_ENCODERS,
        scenario="stationary",
        step_count=3,
        interval_ms=100,
    )
    for sample in samples:
        assert sample.raw_count_deltas.front_left_count_delta == 0
        assert sample.body_twist.vx_m_s == 0.0
        assert sample.body_twist.vy_m_s == 0.0
        assert sample.body_twist.yaw_rate_rad_s == 0.0
        assert (sample.pose.x_m, sample.pose.y_m, sample.pose.yaw_rad) == (0.0, 0.0, 0.0)


def test_canonical_scenarios_follow_rover_coordinate_convention():
    forward = _final_sample("forward")
    left = _final_sample("left_strafe")
    rotation = _final_sample("counterclockwise_rotation")
    combined = _final_sample("combined_curved_motion")
    assert forward.pose.x_m > 0.0
    assert abs(forward.pose.y_m) < 1.0e-12
    assert left.pose.y_m > 0.0
    assert abs(left.pose.x_m) < 1.0e-12
    assert rotation.pose.yaw_rad > 0.0
    assert combined.pose.x_m > 0.0
    assert combined.pose.y_m > 0.0
    assert combined.pose.yaw_rad > 0.0


def test_explicit_negative_direction_multipliers_preserve_math_wheel_signs():
    encoders = EncoderConfiguration(2048.0, -1, 1, -1, 1)
    [sample] = generate_mecanum_odometry_samples(
        geometry=SYNTHETIC_GEOMETRY,
        encoder_configuration=encoders,
        scenario="forward",
        step_count=1,
        interval_ms=100,
    )
    assert sample.raw_count_deltas.front_left_count_delta < 0
    assert sample.raw_count_deltas.rear_left_count_delta < 0
    assert sample.signed_count_deltas.front_left_count_delta > 0
    assert sample.signed_count_deltas.rear_left_count_delta > 0
    assert sample.body_twist.vx_m_s > 0.0


def test_jsonl_output_is_deterministic_strict_version_one_telemetry():
    kwargs = {
        "geometry": SYNTHETIC_GEOMETRY,
        "encoder_configuration": SYNTHETIC_ENCODERS,
        "scenario": "combined_curved_motion",
        "step_count": 2,
        "interval_ms": 100,
    }
    lines = generate_mecanum_odometry_telemetry_lines(**kwargs)
    assert lines == generate_mecanum_odometry_telemetry_lines(**kwargs)
    messages = list(iter_stm32_telemetry(lines))
    assert len(messages) == 8
    assert [message.sequence for message in messages] == list(range(8))
    assert [message.message_type for message in messages[:4]] == [
        "wheel_encoder_delta",
        "wheel_angular_velocity",
        "body_twist",
        "odometry_pose",
    ]
    assert messages[0].status == "simulated"
    assert all(message.status == "software_derived" for message in messages[1:4])
    assert all(json.loads(line)["version"] == 1 for line in lines)


def test_phase4a_telemetry_parser_rejects_unknown_fields_and_nonfinite_values():
    [line, *_] = generate_mecanum_odometry_telemetry_lines(
        geometry=SYNTHETIC_GEOMETRY,
        encoder_configuration=SYNTHETIC_ENCODERS,
        scenario="forward",
        step_count=1,
        interval_ms=100,
    )
    payload = json.loads(line)
    payload["payload"]["guessed_encoder_resolution"] = 123
    with pytest.raises(Stm32TelemetryFormatError, match="unknown payload field"):
        parse_stm32_telemetry_line(json.dumps(payload))

    payload = json.loads(line)
    payload["payload"]["interval_ms"] = 0
    with pytest.raises(Stm32TelemetryFormatError, match="positive integer"):
        parse_stm32_telemetry_line(json.dumps(payload))

    derived_line = generate_mecanum_odometry_telemetry_lines(
        geometry=SYNTHETIC_GEOMETRY,
        encoder_configuration=SYNTHETIC_ENCODERS,
        scenario="forward",
        step_count=1,
        interval_ms=100,
    )[1]
    payload = json.loads(derived_line)
    payload["status"] = "simulated"
    with pytest.raises(Stm32TelemetryFormatError, match="software_derived"):
        parse_stm32_telemetry_line(json.dumps(payload))


def test_recording_bridge_preserves_phase4a_records_and_status(tmp_path):
    lines = generate_mecanum_odometry_telemetry_lines(
        geometry=SYNTHETIC_GEOMETRY,
        encoder_configuration=SYNTHETIC_ENCODERS,
        scenario="combined_curved_motion",
        step_count=2,
        interval_ms=100,
    )
    output = tmp_path / "phase4a_recording.jsonl"
    record_stm32_telemetry_stream(lines, output)
    summary = inspect_recording(output)
    assert summary.record_counts == {
        "wheel_encoder_delta": 2,
        "wheel_angular_velocity": 2,
        "body_twist": 2,
        "odometry_pose": 2,
    }
    entries = [entry.payload for entry in iter_recording_entries(output)]
    header = entries[0]
    assert header["schema_name"] == "mars_scout_multisensor_recording"
    assert header["schema_version"] == 1
    assert "rover_odometry" in {
        sensor["sensor_id"] for sensor in header["sensor_inventory"]
    }
    encoder_record = entries[1]
    assert encoder_record["status"] == "simulated"
    assert "front_left_raw_count_delta" in encoder_record
    assert "front_left_signed_count_delta" in encoder_record
    odometry_record = entries[4]
    assert odometry_record["status"] == "software_derived"
    assert odometry_record["integration_method"] == "se2_constant_twist_exponential"


def test_geometry_encoder_signs_and_resolution_have_no_defaults():
    geometry_signature = inspect.signature(MecanumGeometry)
    encoder_signature = inspect.signature(EncoderConfiguration)
    for name in ("wheel_radius_m", "half_length_m", "half_width_m"):
        assert geometry_signature.parameters[name].default is inspect.Parameter.empty
    for name in (
        "counts_per_wheel_revolution",
        "front_left_direction",
        "front_right_direction",
        "rear_left_direction",
        "rear_right_direction",
    ):
        assert encoder_signature.parameters[name].default is inspect.Parameter.empty


def test_phase4a_modules_have_no_hardware_access_imports():
    combined = "\n".join(
        (REPO_ROOT / "pc" / "src" / "rplidar_c1_tools" / name).read_text(encoding="utf-8")
        for name in ("mecanum_odometry.py", "mecanum_odometry_simulator.py")
    ).lower()
    for forbidden in (
        "import serial",
        "from serial",
        "import usb",
        "import socket",
        "gpio",
        "i2c",
        "flymcu",
        "keil",
    ):
        assert forbidden not in combined


@pytest.mark.parametrize(
    "kwargs",
    [
        {"step_count": 0, "interval_ms": 100},
        {"step_count": 1, "interval_ms": 0},
        {"step_count": 1, "interval_ms": 100, "start_timestamp_ms": -1},
    ],
)
def test_simulator_rejects_invalid_intervals_counts_and_timestamps(kwargs: dict[str, int]):
    arguments = {
        "geometry": SYNTHETIC_GEOMETRY,
        "encoder_configuration": SYNTHETIC_ENCODERS,
        "scenario": "forward",
        "step_count": 1,
        "interval_ms": 100,
        **kwargs,
    }
    with pytest.raises(ValueError):
        generate_mecanum_odometry_samples(**arguments)


def _final_sample(scenario: str):
    return generate_mecanum_odometry_samples(
        geometry=SYNTHETIC_GEOMETRY,
        encoder_configuration=SYNTHETIC_ENCODERS,
        scenario=scenario,
        step_count=5,
        interval_ms=100,
    )[-1]
