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
    ImuSample,
    LidarTransportStatsSample,
    LinkStatusSample,
    SubsystemStatusSample,
    UltrasonicSample,
    default_sensor_inventory,
)
from .openrf1_phase32b import (
    mpu6050_accel_raw_to_mps2,
    mpu6050_gyro_raw_to_radps,
    mpu6050_temperature_raw_to_c,
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

    if message.message_type == "imu_raw":
        sample = ImuSample(
            timestamp_us=timestamp_us,
            sensor_id=message.sensor_id,
            accel_x_mps2=mpu6050_accel_raw_to_mps2(
                int(payload["accel_x_raw"]),
                accel_range_g=int(payload["accel_range_g"]),
            ),
            accel_y_mps2=mpu6050_accel_raw_to_mps2(
                int(payload["accel_y_raw"]),
                accel_range_g=int(payload["accel_range_g"]),
            ),
            accel_z_mps2=mpu6050_accel_raw_to_mps2(
                int(payload["accel_z_raw"]),
                accel_range_g=int(payload["accel_range_g"]),
            ),
            gyro_x_radps=mpu6050_gyro_raw_to_radps(
                int(payload["gyro_x_raw"]),
                gyro_range_dps=int(payload["gyro_range_dps"]),
            ),
            gyro_y_radps=mpu6050_gyro_raw_to_radps(
                int(payload["gyro_y_raw"]),
                gyro_range_dps=int(payload["gyro_range_dps"]),
            ),
            gyro_z_radps=mpu6050_gyro_raw_to_radps(
                int(payload["gyro_z_raw"]),
                gyro_range_dps=int(payload["gyro_range_dps"]),
            ),
            temperature_c=mpu6050_temperature_raw_to_c(int(payload["temperature_raw"])),
        )
        return ("imu", sample)

    if message.message_type == "subsystem_status":
        sample = SubsystemStatusSample(
            timestamp_us=timestamp_us,
            subsystem=str(payload["subsystem"]),
            health=str(payload["health"]),
            error_count=int(payload["error_count"]),
            status=message.status,
            detail=payload.get("detail") if payload.get("detail") is not None else None,
            source_sequence=source_sequence,
        )
        return ("subsystem_status", sample)

    if message.message_type == "link_status":
        sample = LinkStatusSample(
            timestamp_us=timestamp_us,
            link_name=str(payload["link_name"]),
            healthy=bool(payload["healthy"]),
            rx_bytes=int(payload["rx_bytes"]),
            tx_bytes=int(payload["tx_bytes"]),
            malformed_frames=int(payload["malformed_frames"]),
            crc_errors=int(payload["crc_errors"]),
            sequence_gaps=int(payload["sequence_gaps"]),
            status=message.status,
            last_rx_ms=payload.get("last_rx_ms") if payload.get("last_rx_ms") is not None else None,
            source_sequence=source_sequence,
        )
        return ("link_status", sample)

    if message.message_type == "lidar_transport_stats":
        sample = LidarTransportStatsSample(
            timestamp_us=timestamp_us,
            sensor_id=message.sensor_id,
            rx_bytes=int(payload["rx_bytes"]),
            bytes_read=int(payload["bytes_read"]),
            overflow_count=int(payload["overflow_count"]),
            framing_error_count=int(payload["framing_error_count"]),
            chunks_forwarded=int(payload["chunks_forwarded"]),
            last_rx_tick_ms=int(payload["last_rx_tick_ms"]),
            status=message.status,
            source_sequence=source_sequence,
        )
        return ("lidar_transport_stats", sample)

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
    if record_type == "imu":
        return recorder.write_imu_sample(sample)  # type: ignore[arg-type]
    if record_type == "subsystem_status":
        return recorder.write_subsystem_status_sample(sample)  # type: ignore[arg-type]
    if record_type == "link_status":
        return recorder.write_link_status_sample(sample)  # type: ignore[arg-type]
    if record_type == "lidar_transport_stats":
        return recorder.write_lidar_transport_stats_sample(sample)  # type: ignore[arg-type]
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
        sensor_inventory=default_sensor_inventory(lidar_count=1, include_auxiliary=True),
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

