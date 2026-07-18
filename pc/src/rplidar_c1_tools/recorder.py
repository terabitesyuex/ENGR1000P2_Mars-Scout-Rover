"""Stream multi-sensor records to the Phase 2.4 JSON Lines format."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any, TextIO

from .data_models import MetadataValue, ScanFrame
from .recording_models import (
    BarometerSample,
    BodyTwistSample,
    GroundEdgeSample,
    HallLandmarkSample,
    IlluminanceSample,
    ImuSample,
    LidarTransportStatsSample,
    LinkStatusSample,
    RoverPose,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SensorDefinition,
    SubsystemStatusSample,
    UltrasonicSample,
    OdometryPoseSample,
    WheelAngularVelocitySample,
    WheelEncoderDeltaSample,
    default_sensor_inventory,
    pose_to_json,
    sample_to_json,
)


class RecordingError(ValueError):
    """Raised when a recording cannot be written safely."""


class MultiSensorRecorder:
    """Incrementally write one versioned multi-sensor JSONL recording."""

    def __init__(
        self,
        output_path: Path | str,
        *,
        sensor_inventory: Iterable[SensorDefinition] | None = None,
        metadata: Mapping[str, MetadataValue] | None = None,
        created_unix_us: int = 0,
        overwrite: bool = False,
    ) -> None:
        self.output_path = Path(output_path)
        self.sensor_inventory = tuple(sensor_inventory or default_sensor_inventory())
        self.metadata = dict(metadata or {})
        self.created_unix_us = created_unix_us
        self.overwrite = overwrite
        self._known_sensor_ids = _sensor_id_set(self.sensor_inventory)
        self._stream: TextIO | None = None
        self._sequence = 0
        _validate_header_inputs(self.sensor_inventory, self.created_unix_us)

    def __enter__(self) -> "MultiSensorRecorder":
        self.open()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def open(self) -> None:
        """Open the output file and write the required header line."""
        if self._stream is not None:
            raise RecordingError("recording is already open")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w" if self.overwrite else "x"
        try:
            self._stream = self.output_path.open(mode, encoding="utf-8", newline="\n")
        except FileExistsError as exc:
            raise RecordingError(f"recording already exists: {self.output_path}") from exc
        self._write_payload(self._header_payload())

    def close(self) -> None:
        if self._stream is not None:
            self._stream.close()
            self._stream = None

    def write_lidar_scan(
        self,
        sensor_id: str,
        scan_frame: ScanFrame,
        *,
        pose: RoverPose | None = None,
    ) -> int:
        """Write one complete LiDAR `ScanFrame` while preserving point order."""
        self._require_known_sensor(sensor_id)
        if not isinstance(scan_frame, ScanFrame):
            raise RecordingError("scan_frame must be a ScanFrame")
        payload = self._base_record(
            "lidar_scan",
            sensor_id=sensor_id,
            timestamp_us=scan_frame.timestamp_us,
        )
        payload.update(
            {
                "frame_id": scan_frame.frame_id,
                "source": scan_frame.source,
                "metadata": scan_frame.metadata,
                "points": [
                    {
                        "angle_deg": point.angle_deg,
                        "distance_mm": point.distance_mm,
                        "quality": point.quality,
                    }
                    for point in scan_frame.points
                ],
                "rover_pose": pose_to_json(pose),
            }
        )
        return self._write_payload(payload)

    def write_rover_pose(self, pose: RoverPose) -> int:
        payload = self._base_record(
            "rover_pose",
            sensor_id="rover_pose",
            timestamp_us=pose.timestamp_us,
        )
        payload.update(sample_to_json(pose))
        return self._write_payload(payload)

    def write_imu_sample(self, sample: ImuSample) -> int:
        return self._write_sample_record("imu", sample)

    def write_ultrasonic_sample(self, sample: UltrasonicSample) -> int:
        return self._write_sample_record("ultrasonic", sample)

    def write_ground_edge_sample(self, sample: GroundEdgeSample) -> int:
        return self._write_sample_record("ground_edge", sample)

    def write_hall_landmark_sample(self, sample: HallLandmarkSample) -> int:
        return self._write_sample_record("hall_landmark", sample)

    def write_illuminance_sample(self, sample: IlluminanceSample) -> int:
        return self._write_sample_record("illuminance", sample)

    def write_barometer_sample(self, sample: BarometerSample) -> int:
        return self._write_sample_record("barometer", sample)

    def write_subsystem_status_sample(self, sample: SubsystemStatusSample) -> int:
        return self._write_sample_record("subsystem_status", sample)

    def write_link_status_sample(self, sample: LinkStatusSample) -> int:
        return self._write_sample_record("link_status", sample)

    def write_lidar_transport_stats_sample(self, sample: LidarTransportStatsSample) -> int:
        return self._write_sample_record("lidar_transport_stats", sample)

    def write_wheel_encoder_delta_sample(self, sample: WheelEncoderDeltaSample) -> int:
        return self._write_sample_record("wheel_encoder_delta", sample)

    def write_wheel_angular_velocity_sample(self, sample: WheelAngularVelocitySample) -> int:
        return self._write_sample_record("wheel_angular_velocity", sample)

    def write_body_twist_sample(self, sample: BodyTwistSample) -> int:
        return self._write_sample_record("body_twist", sample)

    def write_odometry_pose_sample(self, sample: OdometryPoseSample) -> int:
        return self._write_sample_record("odometry_pose", sample)

    def _write_sample_record(self, record_type: str, sample: object) -> int:
        try:
            data = sample_to_json(sample)
        except ValueError as exc:
            raise RecordingError(str(exc)) from exc
        sensor_id = str(data["sensor_id"])
        self._require_known_sensor(sensor_id)
        payload = self._base_record(
            record_type,
            sensor_id=sensor_id,
            timestamp_us=int(data["timestamp_us"]),
        )
        payload.update(data)
        return self._write_payload(payload)

    def _header_payload(self) -> dict[str, Any]:
        return {
            "record_type": "header",
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "created_unix_us": self.created_unix_us,
            "sensor_inventory": [sensor.to_json() for sensor in self.sensor_inventory],
            "coordinate_convention": {
                "frame": "rover",
                "angle_unit": "deg",
                "angle_zero": "forward",
                "positive_angle": "counterclockwise",
                "distance_unit": "mm",
                "cartesian_unit": "m",
                "x_axis": "forward",
                "y_axis": "left",
            },
            "metadata": self.metadata,
        }

    def _base_record(
        self,
        record_type: str,
        *,
        sensor_id: str,
        timestamp_us: int,
    ) -> dict[str, Any]:
        if not isinstance(timestamp_us, int) or timestamp_us < 0:
            raise RecordingError("timestamp_us must be a non-negative integer")
        self._sequence += 1
        return {
            "record_type": record_type,
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "sequence": self._sequence,
            "timestamp_us": timestamp_us,
            "sensor_id": sensor_id,
        }

    def _write_payload(self, payload: Mapping[str, Any]) -> int:
        if self._stream is None:
            raise RecordingError("recording is not open")
        try:
            line = json.dumps(
                dict(payload),
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            )
        except (TypeError, ValueError) as exc:
            raise RecordingError(f"record payload is not JSON-serializable: {exc}") from exc
        self._stream.write(line)
        self._stream.write("\n")
        self._stream.flush()
        return self._sequence

    def _require_known_sensor(self, sensor_id: str) -> None:
        if sensor_id not in self._known_sensor_ids:
            raise RecordingError(f"unknown sensor_id: {sensor_id}")


def _sensor_id_set(sensor_inventory: Iterable[SensorDefinition]) -> set[str]:
    sensor_ids = [sensor.sensor_id for sensor in sensor_inventory]
    duplicates = sorted({sensor_id for sensor_id in sensor_ids if sensor_ids.count(sensor_id) > 1})
    if duplicates:
        raise RecordingError(f"duplicate sensor_id in inventory: {', '.join(duplicates)}")
    return set(sensor_ids)


def _validate_header_inputs(
    sensor_inventory: tuple[SensorDefinition, ...],
    created_unix_us: int,
) -> None:
    if not sensor_inventory:
        raise RecordingError("sensor_inventory must not be empty")
    if not isinstance(created_unix_us, int) or created_unix_us < 0:
        raise RecordingError("created_unix_us must be a non-negative integer")
