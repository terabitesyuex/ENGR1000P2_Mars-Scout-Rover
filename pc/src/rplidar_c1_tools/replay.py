"""Lazy reading and deterministic replay for Phase 2.4 recordings."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

from .data_models import ScanFrame, ScanPoint
from .recording_models import RoverPose, SCHEMA_NAME, SCHEMA_VERSION
from .scan_builder import ScanValidationError, build_scan_frame


class RecordingFormatError(ValueError):
    """Raised for malformed, unsupported, or inconsistent recording lines."""

    def __init__(self, message: str, *, line_number: int | None = None) -> None:
        self.line_number = line_number
        prefix = f"line {line_number}: " if line_number is not None else ""
        super().__init__(f"{prefix}{message}")


@dataclass(frozen=True, slots=True)
class RecordingEntry:
    line_number: int
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LidarScanRecord:
    sensor_id: str
    sequence: int
    line_number: int
    scan_frame: ScanFrame
    rover_pose: RoverPose | None = None


@dataclass(frozen=True, slots=True)
class RecordingSummary:
    path: Path
    schema_name: str
    schema_version: int
    sensor_ids: tuple[str, ...]
    record_counts: dict[str, int]
    lidar_scan_counts: dict[str, int]
    first_timestamp_us: int | None
    last_timestamp_us: int | None

    def to_text(self) -> str:
        lines = [
            f"path: {self.path}",
            f"schema: {self.schema_name} v{self.schema_version}",
            f"sensors: {', '.join(self.sensor_ids)}",
            "record_counts:",
        ]
        for record_type, count in sorted(self.record_counts.items()):
            lines.append(f"  {record_type}: {count}")
        lines.append("lidar_scan_counts:")
        for sensor_id, count in sorted(self.lidar_scan_counts.items()):
            lines.append(f"  {sensor_id}: {count}")
        lines.append(f"first_timestamp_us: {self.first_timestamp_us}")
        lines.append(f"last_timestamp_us: {self.last_timestamp_us}")
        return "\n".join(lines) + "\n"


def read_recording_header(path: Path | str) -> dict[str, Any]:
    """Read and validate only the required header line."""
    iterator = iter_recording_entries(path)
    try:
        return next(iterator).payload
    except StopIteration as exc:
        raise RecordingFormatError("recording is empty") from exc


def iter_recording_entries(path: Path | str) -> Iterator[RecordingEntry]:
    """Yield validated JSONL entries lazily in file order."""
    recording_path = Path(path)
    known_sensor_ids: set[str] | None = None
    last_sequence = 0
    last_timestamp_us = 0
    saw_header = False

    with recording_path.open("r", encoding="utf-8") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            if raw_line.strip() == "":
                raise RecordingFormatError("blank lines are not valid records", line_number=line_number)
            payload = _parse_json_object(raw_line, line_number)
            record_type = _require_string(payload, "record_type", line_number)
            _validate_schema(payload, line_number)

            if line_number == 1:
                if record_type != "header":
                    raise RecordingFormatError("first record must be header", line_number=line_number)
                known_sensor_ids = _validate_header(payload, line_number)
                saw_header = True
            elif not saw_header:
                raise RecordingFormatError("missing header", line_number=line_number)
            else:
                if record_type == "header":
                    raise RecordingFormatError("duplicate header", line_number=line_number)
                if known_sensor_ids is None:
                    raise RecordingFormatError("missing sensor inventory", line_number=line_number)
                _validate_known_sensor(payload, known_sensor_ids, line_number)
                sequence = _require_int(payload, "sequence", line_number)
                if sequence <= last_sequence:
                    raise RecordingFormatError("sequence must increase", line_number=line_number)
                last_sequence = sequence
                timestamp_us = _require_int(payload, "timestamp_us", line_number)
                if timestamp_us < last_timestamp_us:
                    raise RecordingFormatError("timestamp_us must be nondecreasing", line_number=line_number)
                last_timestamp_us = timestamp_us

            yield RecordingEntry(line_number=line_number, payload=payload)

    if not saw_header:
        raise RecordingFormatError("missing header")


def iter_lidar_scans(
    path: Path | str,
    *,
    sensor_id: str | None = None,
) -> Iterator[LidarScanRecord]:
    """Yield LiDAR scans lazily as existing `ScanFrame` objects."""
    for entry in iter_recording_entries(path):
        payload = entry.payload
        if payload["record_type"] != "lidar_scan":
            continue
        if sensor_id is not None and payload["sensor_id"] != sensor_id:
            continue
        yield _payload_to_lidar_record(payload, entry.line_number)


def replay_lidar_scans(
    path: Path | str,
    *,
    sensor_id: str | None = None,
    timed: bool = False,
    speed: float = 1.0,
    sleep: Callable[[float], None] | None = None,
) -> Iterator[LidarScanRecord]:
    """Replay LiDAR scans deterministically in file order.

    With `timed=False`, records are yielded immediately. With `timed=True`,
    timestamp deltas are passed to `sleep`, which can be a fake function in
    tests so no real waiting is required.
    """
    if speed <= 0.0:
        raise ValueError("speed must be positive")
    sleeper = sleep or time.sleep
    previous_timestamp_us: int | None = None
    for record in iter_lidar_scans(path, sensor_id=sensor_id):
        if timed and previous_timestamp_us is not None:
            delta_us = record.scan_frame.timestamp_us - previous_timestamp_us
            if delta_us > 0:
                sleeper((delta_us / 1_000_000.0) / speed)
        previous_timestamp_us = record.scan_frame.timestamp_us
        yield record


def last_lidar_scan_by_sensor(
    path: Path | str,
    *,
    sensor_ids: Iterable[str] | None = None,
) -> dict[str, LidarScanRecord]:
    """Return the final LiDAR scan for each requested sensor."""
    wanted = set(sensor_ids or ())
    records: dict[str, LidarScanRecord] = {}
    for record in iter_lidar_scans(path):
        if wanted and record.sensor_id not in wanted:
            continue
        records[record.sensor_id] = record
    return records


def inspect_recording(path: Path | str) -> RecordingSummary:
    """Return a compact summary without loading scan points into memory."""
    recording_path = Path(path)
    schema_name = ""
    schema_version = 0
    sensor_ids: tuple[str, ...] = ()
    record_counts: Counter[str] = Counter()
    lidar_scan_counts: Counter[str] = Counter()
    first_timestamp_us: int | None = None
    last_timestamp_us: int | None = None

    for entry in iter_recording_entries(recording_path):
        payload = entry.payload
        record_type = str(payload["record_type"])
        if record_type == "header":
            schema_name = str(payload["schema_name"])
            schema_version = int(payload["schema_version"])
            sensor_ids = tuple(
                str(sensor["sensor_id"])
                for sensor in payload.get("sensor_inventory", [])
            )
            continue
        record_counts[record_type] += 1
        timestamp_us = int(payload["timestamp_us"])
        first_timestamp_us = timestamp_us if first_timestamp_us is None else first_timestamp_us
        last_timestamp_us = timestamp_us
        if record_type == "lidar_scan":
            lidar_scan_counts[str(payload["sensor_id"])] += 1

    return RecordingSummary(
        path=recording_path,
        schema_name=schema_name,
        schema_version=schema_version,
        sensor_ids=sensor_ids,
        record_counts=dict(record_counts),
        lidar_scan_counts=dict(lidar_scan_counts),
        first_timestamp_us=first_timestamp_us,
        last_timestamp_us=last_timestamp_us,
    )


def _payload_to_lidar_record(payload: dict[str, Any], line_number: int) -> LidarScanRecord:
    points_payload = payload.get("points")
    if not isinstance(points_payload, list):
        raise RecordingFormatError("lidar_scan points must be a list", line_number=line_number)
    points: list[ScanPoint] = []
    for point_index, point_payload in enumerate(points_payload):
        if not isinstance(point_payload, dict):
            raise RecordingFormatError(
                f"points[{point_index}] must be an object",
                line_number=line_number,
            )
        points.append(
            ScanPoint(
                angle_deg=float(point_payload.get("angle_deg")),
                distance_mm=int(point_payload.get("distance_mm")),
                quality=_optional_int(point_payload.get("quality")),
            )
        )
    try:
        scan_frame = build_scan_frame(
            points,
            timestamp_us=int(payload["timestamp_us"]),
            frame_id=_optional_int(payload.get("frame_id")),
            source=str(payload.get("source", "recording")),
            metadata=_metadata_dict(payload.get("metadata")),
        )
    except (ScanValidationError, TypeError, ValueError) as exc:
        raise RecordingFormatError(str(exc), line_number=line_number) from exc
    pose = _payload_to_pose(payload.get("rover_pose"), line_number)
    return LidarScanRecord(
        sensor_id=str(payload["sensor_id"]),
        sequence=int(payload["sequence"]),
        line_number=line_number,
        scan_frame=scan_frame,
        rover_pose=pose,
    )


def _parse_json_object(raw_line: str, line_number: int) -> dict[str, Any]:
    try:
        payload = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        raise RecordingFormatError(f"invalid JSON: {exc.msg}", line_number=line_number) from exc
    if not isinstance(payload, dict):
        raise RecordingFormatError("record must be a JSON object", line_number=line_number)
    return payload


def _validate_schema(payload: dict[str, Any], line_number: int) -> None:
    if payload.get("schema_name") != SCHEMA_NAME:
        raise RecordingFormatError("unsupported schema_name", line_number=line_number)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise RecordingFormatError("unsupported schema_version", line_number=line_number)


def _validate_header(payload: dict[str, Any], line_number: int) -> set[str]:
    inventory = payload.get("sensor_inventory")
    if not isinstance(inventory, list) or not inventory:
        raise RecordingFormatError("header sensor_inventory must be a non-empty list", line_number=line_number)
    sensor_ids: list[str] = []
    for index, sensor in enumerate(inventory):
        if not isinstance(sensor, dict):
            raise RecordingFormatError(f"sensor_inventory[{index}] must be an object", line_number=line_number)
        sensor_id = sensor.get("sensor_id")
        if not isinstance(sensor_id, str) or not sensor_id:
            raise RecordingFormatError(f"sensor_inventory[{index}].sensor_id is invalid", line_number=line_number)
        sensor_ids.append(sensor_id)
    duplicates = sorted({sensor_id for sensor_id in sensor_ids if sensor_ids.count(sensor_id) > 1})
    if duplicates:
        raise RecordingFormatError(
            f"duplicate sensor_id in header: {', '.join(duplicates)}",
            line_number=line_number,
        )
    return set(sensor_ids)


def _validate_known_sensor(
    payload: dict[str, Any],
    known_sensor_ids: set[str],
    line_number: int,
) -> None:
    sensor_id = _require_string(payload, "sensor_id", line_number)
    if sensor_id not in known_sensor_ids:
        raise RecordingFormatError(f"unknown sensor_id: {sensor_id}", line_number=line_number)


def _payload_to_pose(payload: object, line_number: int) -> RoverPose | None:
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise RecordingFormatError("rover_pose must be an object or null", line_number=line_number)
    try:
        return RoverPose(
            timestamp_us=int(payload["timestamp_us"]),
            x_m=float(payload["x_m"]),
            y_m=float(payload["y_m"]),
            yaw_rad=float(payload["yaw_rad"]),
            source=str(payload.get("source", "recording")),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RecordingFormatError("invalid rover_pose", line_number=line_number) from exc


def _require_string(payload: dict[str, Any], key: str, line_number: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise RecordingFormatError(f"{key} must be a non-empty string", line_number=line_number)
    return value


def _require_int(payload: dict[str, Any], key: str, line_number: int) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or value < 0:
        raise RecordingFormatError(f"{key} must be a non-negative integer", line_number=line_number)
    return value


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _metadata_dict(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("metadata must be an object")
    return value
