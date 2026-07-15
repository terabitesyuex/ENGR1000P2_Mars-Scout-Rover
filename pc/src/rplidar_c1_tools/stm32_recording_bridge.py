"""Bridge validated STM32 sensor telemetry into Phase 2.4 recordings."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .recorder import MultiSensorRecorder
from .recording_models import (
    BarometerSample,
    GroundEdgeSample,
    HallLandmarkSample,
    IlluminanceSample,
    UltrasonicSample,
    default_sensor_inventory,
)
from .stm32_sensor_models import Stm32TelemetryMessage
from .stm32_sensor_protocol import iter_stm32_telemetry, validate_stm32_telemetry_message


def stm32_message_to_recording_sample(message: Stm32TelemetryMessage) -> tuple[str, object]:
    """Convert one validated STM32 telemetry message to a recording sample."""
    validate_stm32_telemetry_message(message)
    timestamp_us = message.timestamp_ms * 1000
    payload = dict(message.payload)
    source_sequence = message.sequence

    if message.message_type == "ultrasonic":
        valid = message.status in {"ok", "simulated"} and payload.get("valid", True) is True
        sample = UltrasonicSample(
            timestamp_us=timestamp_us,
            sensor_id=message.sensor_id,
            distance_mm=payload.get("distance_mm") if valid else None,
            valid=valid,
            status=message.status,
            raw_echo_us=payload.get("raw_echo_us"),
            source_sequence=source_sequence,
        )
        return ("ultrasonic", sample)

    if message.message_type == "ground_edge":
        polarity_verified = bool(payload["polarity_verified"])
        sample = GroundEdgeSample(
            timestamp_us=timestamp_us,
            sensor_id=message.sensor_id,
            edge_detected=payload.get("interpreted_edge_detected") if polarity_verified else None,
            raw_state=payload["raw_state"],
            polarity_verified=polarity_verified,
            status=message.status,
            source_sequence=source_sequence,
        )
        return ("ground_edge", sample)

    if message.message_type == "hall_landmark":
        polarity_verified = bool(payload["polarity_verified"])
        raw_state = payload["raw_state"]
        sample = HallLandmarkSample(
            timestamp_us=timestamp_us,
            sensor_id=message.sensor_id,
            detected=payload.get("interpreted_landmark_detected") if polarity_verified else None,
            raw_state=raw_state,
            raw_value=raw_state,
            polarity_verified=polarity_verified,
            status=message.status,
            source_sequence=source_sequence,
        )
        return ("hall_landmark", sample)

    if message.message_type == "illuminance":
        sample = IlluminanceSample(
            timestamp_us=timestamp_us,
            sensor_id=message.sensor_id,
            illuminance_lux=payload.get("illuminance_lux"),
            status=message.status,
            source_sequence=source_sequence,
        )
        return ("illuminance", sample)

    if message.message_type == "barometer":
        sample = BarometerSample(
            timestamp_us=timestamp_us,
            sensor_id=message.sensor_id,
            temperature_c=payload.get("temperature_c"),
            pressure_pa=payload.get("pressure_pa"),
            status=message.status,
            source_sequence=source_sequence,
        )
        return ("barometer", sample)

    raise ValueError(f"unsupported message_type: {message.message_type}")


def bridge_stm32_message_to_recording(
    recorder: MultiSensorRecorder,
    message: Stm32TelemetryMessage,
) -> int:
    """Write one validated STM32 telemetry message to an open recorder."""
    record_type, sample = stm32_message_to_recording_sample(message)
    if record_type == "ultrasonic":
        return recorder.write_ultrasonic_sample(sample)  # type: ignore[arg-type]
    if record_type == "ground_edge":
        return recorder.write_ground_edge_sample(sample)  # type: ignore[arg-type]
    if record_type == "hall_landmark":
        return recorder.write_hall_landmark_sample(sample)  # type: ignore[arg-type]
    if record_type == "illuminance":
        return recorder.write_illuminance_sample(sample)  # type: ignore[arg-type]
    if record_type == "barometer":
        return recorder.write_barometer_sample(sample)  # type: ignore[arg-type]
    raise ValueError(f"unsupported record_type: {record_type}")


def record_stm32_telemetry_stream(
    lines: Iterable[str],
    output_path: Path | str,
    *,
    overwrite: bool = False,
) -> Path:
    """Record a validated STM32 telemetry stream as Phase 2.4 JSONL."""
    output = Path(output_path)
    with MultiSensorRecorder(
        output,
        sensor_inventory=default_sensor_inventory(lidar_count=2, include_auxiliary=True),
        metadata={
            "generator": "rplidar_c1_tools.cli record-stm32-telemetry",
            "source": "stm32_sensor_telemetry_simulated_or_forwarded",
            "hardware_access": "none",
            "physical_test_required": True,
        },
        overwrite=overwrite,
    ) as recorder:
        for message in iter_stm32_telemetry(lines):
            bridge_stm32_message_to_recording(recorder, message)
    return output

