"""Adapt VehicleDemo Hall telemetry into the existing recording pipeline."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .recorder import MultiSensorRecorder
from .recording_models import HallLandmarkSample, default_sensor_inventory


_TOP_LEVEL_FIELDS = {"sequence", "timestamp_ms", "message_type", "status", "payload"}
_IGNORED_MESSAGE_TYPES = {
    "vehicle_demo_identity",
    "vehicle_demo_motor_diag",
    "vehicle_demo_encoder",
}
_STATUS_EVENT_FIELDS = {
    "hall_baseline_ready",
    "hall_baseline_level",
    "hall_landmark_active",
    "hall_landmark_count",
}
COURSE_LANDMARKS_MM = {
    1: (600, 400),
    2: (1800, 400),
    3: (2200, 400),
}
COURSE_LANDMARK_COUNT = len(COURSE_LANDMARKS_MM)
HALL_TO_BASE_LINK_PLANAR_OFFSET_MM = (0, 0)
HALL_SENSING_POINT_HEIGHT_ABOVE_FLOOR_MM = 65.0
_SUPPLIED_LOADED_WHEEL_DIAMETER_MM = 79.0
HALL_TO_BASE_LINK_Z_MM = (
    HALL_SENSING_POINT_HEIGHT_ABOVE_FLOOR_MM
    - _SUPPLIED_LOADED_WHEEL_DIAMETER_MM / 2.0
)


class VehicleDemoTelemetryError(ValueError):
    """Raised when VehicleDemo JSONL cannot be adapted safely."""

    def __init__(self, message: str, *, line_number: int | None = None) -> None:
        self.line_number = line_number
        prefix = f"line {line_number}: " if line_number is not None else ""
        super().__init__(f"{prefix}{message}")


@dataclass(frozen=True, slots=True)
class VehicleDemoHallStatus:
    sequence: int
    timestamp_ms: int
    raw_level: int
    debounced_level: int
    vehicle_status: str
    baseline_ready: bool = False
    baseline_level: int | None = None
    landmark_active: bool = False
    landmark_count: int = 0


@dataclass(frozen=True, slots=True)
class VehicleDemoHallEvent:
    sequence: int
    timestamp_ms: int
    landmark_index: int
    baseline_level: int
    trigger_level: int
    baseline_inferred: bool


@dataclass(frozen=True, slots=True)
class VehicleDemoHallTransition:
    sequence: int
    timestamp_ms: int
    previous_level: int
    current_level: int


@dataclass(frozen=True, slots=True)
class VehicleDemoHallSummary:
    status_count: int
    first_timestamp_ms: int
    last_timestamp_ms: int
    duration_ms: int
    raw_zero_count: int
    raw_one_count: int
    debounced_zero_count: int
    debounced_one_count: int
    raw_debounced_mismatch_count: int
    raw_transitions: tuple[VehicleDemoHallTransition, ...]
    debounced_transitions: tuple[VehicleDemoHallTransition, ...]
    landmark_events: tuple[VehicleDemoHallEvent, ...]
    known_landmark_event_count: int
    unexpected_landmark_event_count: int
    course_checkpoint_sequence_complete: bool
    next_expected_landmark_index: int | None

    def to_text(self) -> str:
        lines = [
            "source: vehicle_demo_jsonl",
            "hall_semantics: unverified_numeric_levels_only",
            f"status_count: {self.status_count}",
            f"first_timestamp_ms: {self.first_timestamp_ms}",
            f"last_timestamp_ms: {self.last_timestamp_ms}",
            f"duration_ms: {self.duration_ms}",
            f"raw_level_counts: 0={self.raw_zero_count}, 1={self.raw_one_count}",
            (
                "debounced_level_counts: "
                f"0={self.debounced_zero_count}, 1={self.debounced_one_count}"
            ),
            f"raw_debounced_mismatch_count: {self.raw_debounced_mismatch_count}",
            f"raw_transition_count: {len(self.raw_transitions)}",
        ]
        lines.extend(_transition_text("raw", transition) for transition in self.raw_transitions)
        lines.append(f"debounced_transition_count: {len(self.debounced_transitions)}")
        lines.extend(
            _transition_text("debounced", transition)
            for transition in self.debounced_transitions
        )
        lines.append(f"landmark_event_count: {len(self.landmark_events)}")
        lines.append(f"known_landmark_event_count: {self.known_landmark_event_count}")
        lines.append(
            f"unexpected_landmark_event_count: {self.unexpected_landmark_event_count}"
        )
        lines.append(
            "course_checkpoint_sequence_complete: "
            f"{str(self.course_checkpoint_sequence_complete).lower()}"
        )
        lines.append(
            "next_expected_landmark_index: "
            + (
                str(self.next_expected_landmark_index)
                if self.next_expected_landmark_index is not None
                else "null"
            )
        )
        lines.extend(_event_text(event) for event in self.landmark_events)
        return "\n".join(lines) + "\n"


def parse_vehicle_demo_hall_line(
    line: str,
    *,
    line_number: int | None = None,
) -> VehicleDemoHallStatus | None:
    """Parse one VehicleDemo line, returning Hall data only for status lines."""
    record = _parse_record(line, line_number)
    return _hall_status_from_record(record, line_number)


def parse_vehicle_demo_hall_event_line(
    line: str,
    *,
    line_number: int | None = None,
) -> VehicleDemoHallEvent | None:
    """Parse one VehicleDemo line, returning only a latched Hall event."""
    record = _parse_record(line, line_number)
    return _hall_event_from_record(record, line_number)


def _hall_status_from_record(
    record: dict[str, Any],
    line_number: int | None,
) -> VehicleDemoHallStatus | None:
    sequence = _non_negative_int(record["sequence"], "sequence", line_number)
    timestamp_ms = _non_negative_int(record["timestamp_ms"], "timestamp_ms", line_number)
    message_type = _string(record["message_type"], "message_type", line_number)
    vehicle_status = _string(record["status"], "status", line_number)
    payload = record["payload"]
    if not isinstance(payload, dict):
        raise VehicleDemoTelemetryError("payload must be an object", line_number=line_number)

    if message_type in _IGNORED_MESSAGE_TYPES:
        return None
    if message_type == "vehicle_demo_hall_event":
        return None
    if message_type != "vehicle_demo_status":
        raise VehicleDemoTelemetryError("unsupported message_type", line_number=line_number)
    if vehicle_status not in {"ok", "error"}:
        raise VehicleDemoTelemetryError("invalid vehicle status", line_number=line_number)

    raw_level = _binary_level(payload.get("hall_raw_level"), "payload.hall_raw_level", line_number)
    debounced_level = _binary_level(
        payload.get("hall_debounced_level"),
        "payload.hall_debounced_level",
        line_number,
    )
    present_event_fields = _STATUS_EVENT_FIELDS.intersection(payload)
    if present_event_fields and present_event_fields != _STATUS_EVENT_FIELDS:
        raise VehicleDemoTelemetryError(
            "incomplete Hall event status fields",
            line_number=line_number,
        )
    if present_event_fields:
        baseline_ready = _bool(
            payload["hall_baseline_ready"],
            "payload.hall_baseline_ready",
            line_number,
        )
        baseline_level = _binary_level(
            payload["hall_baseline_level"],
            "payload.hall_baseline_level",
            line_number,
        )
        landmark_active = _bool(
            payload["hall_landmark_active"],
            "payload.hall_landmark_active",
            line_number,
        )
        landmark_count = _non_negative_int(
            payload["hall_landmark_count"],
            "payload.hall_landmark_count",
            line_number,
        )
    else:
        baseline_ready = False
        baseline_level = None
        landmark_active = False
        landmark_count = 0
    return VehicleDemoHallStatus(
        sequence=sequence,
        timestamp_ms=timestamp_ms,
        raw_level=raw_level,
        debounced_level=debounced_level,
        vehicle_status=vehicle_status,
        baseline_ready=baseline_ready,
        baseline_level=baseline_level,
        landmark_active=landmark_active,
        landmark_count=landmark_count,
    )


def _hall_event_from_record(
    record: dict[str, Any],
    line_number: int | None,
) -> VehicleDemoHallEvent | None:
    message_type = _string(record["message_type"], "message_type", line_number)
    if message_type != "vehicle_demo_hall_event":
        return None
    if _string(record["status"], "status", line_number) != "ok":
        raise VehicleDemoTelemetryError("invalid Hall event status", line_number=line_number)
    payload = record["payload"]
    if not isinstance(payload, dict):
        raise VehicleDemoTelemetryError("payload must be an object", line_number=line_number)
    expected_fields = {"landmark_index", "baseline_level", "trigger_level", "baseline_inferred"}
    if set(payload) != expected_fields:
        raise VehicleDemoTelemetryError("unexpected Hall event fields", line_number=line_number)
    baseline_level = _binary_level(payload["baseline_level"], "payload.baseline_level", line_number)
    trigger_level = _binary_level(payload["trigger_level"], "payload.trigger_level", line_number)
    if trigger_level == baseline_level:
        raise VehicleDemoTelemetryError("Hall event trigger must differ from baseline", line_number=line_number)
    baseline_inferred = _bool(
        payload["baseline_inferred"],
        "payload.baseline_inferred",
        line_number,
    )
    if not baseline_inferred:
        raise VehicleDemoTelemetryError("Hall event baseline must be inferred", line_number=line_number)
    landmark_index = _non_negative_int(
        payload["landmark_index"],
        "payload.landmark_index",
        line_number,
    )
    if landmark_index == 0:
        raise VehicleDemoTelemetryError("landmark_index must be positive", line_number=line_number)
    return VehicleDemoHallEvent(
        sequence=_non_negative_int(record["sequence"], "sequence", line_number),
        timestamp_ms=_non_negative_int(record["timestamp_ms"], "timestamp_ms", line_number),
        landmark_index=landmark_index,
        baseline_level=baseline_level,
        trigger_level=trigger_level,
        baseline_inferred=True,
    )


def _iter_vehicle_demo_hall_messages(
    lines: Iterable[str],
) -> Iterator[VehicleDemoHallStatus | VehicleDemoHallEvent]:
    previous_sequence = -1
    previous_timestamp_ms = 0
    previous_landmark_index = 0
    for line_number, line in enumerate(lines, start=1):
        record = _parse_record(line, line_number)
        sequence = _non_negative_int(record["sequence"], "sequence", line_number)
        timestamp_ms = _non_negative_int(record["timestamp_ms"], "timestamp_ms", line_number)
        if sequence <= previous_sequence:
            raise VehicleDemoTelemetryError("sequence must increase", line_number=line_number)
        if timestamp_ms < previous_timestamp_ms:
            raise VehicleDemoTelemetryError("timestamp_ms must be nondecreasing", line_number=line_number)
        previous_sequence = sequence
        previous_timestamp_ms = timestamp_ms
        event = _hall_event_from_record(record, line_number)
        if event is not None:
            if event.landmark_index != previous_landmark_index + 1:
                raise VehicleDemoTelemetryError(
                    "landmark_index must increase without gaps",
                    line_number=line_number,
                )
            previous_landmark_index = event.landmark_index
            yield event
            continue
        status = _hall_status_from_record(record, line_number)
        if status is not None:
            if status.landmark_count < previous_landmark_index:
                raise VehicleDemoTelemetryError(
                    "hall_landmark_count regressed",
                    line_number=line_number,
                )
            if status.baseline_ready and status.landmark_count > previous_landmark_index:
                raise VehicleDemoTelemetryError(
                    "missing latched Hall event",
                    line_number=line_number,
                )
            yield status


def iter_vehicle_demo_hall_status(lines: Iterable[str]) -> Iterator[VehicleDemoHallStatus]:
    """Yield Hall statuses while enforcing source sequence and timestamp order."""
    for message in _iter_vehicle_demo_hall_messages(lines):
        if isinstance(message, VehicleDemoHallStatus):
            yield message


def iter_vehicle_demo_hall_events(lines: Iterable[str]) -> Iterator[VehicleDemoHallEvent]:
    """Yield gap-free, timestamped Hall landmark events."""
    for message in _iter_vehicle_demo_hall_messages(lines):
        if isinstance(message, VehicleDemoHallEvent):
            yield message


def vehicle_demo_hall_to_recording_sample(status: VehicleDemoHallStatus) -> HallLandmarkSample:
    """Preserve Hall levels without inventing magnetic detection semantics."""
    if not isinstance(status, VehicleDemoHallStatus):
        raise TypeError("status must be VehicleDemoHallStatus")
    return HallLandmarkSample(
        timestamp_us=status.timestamp_ms * 1000,
        detected=None,
        raw_state=status.raw_level,
        debounced_state=status.debounced_level,
        polarity_verified=False,
        status="ok",
        raw_value=status.raw_level,
        source_sequence=status.sequence,
    )


def vehicle_demo_hall_event_to_recording_sample(
    event: VehicleDemoHallEvent,
) -> HallLandmarkSample:
    """Convert one baseline-excursion event without claiming physical polarity."""
    if not isinstance(event, VehicleDemoHallEvent):
        raise TypeError("event must be VehicleDemoHallEvent")
    known_position = COURSE_LANDMARKS_MM.get(event.landmark_index)
    known_x_mm, known_y_mm = known_position if known_position is not None else (None, None)
    if known_position is None:
        known_base_link_x_mm = None
        known_base_link_y_mm = None
        base_link_planar_offset_applied = False
    else:
        offset_x_mm, offset_y_mm = HALL_TO_BASE_LINK_PLANAR_OFFSET_MM
        if offset_x_mm != 0 or offset_y_mm != 0:
            raise VehicleDemoTelemetryError(
                "nonzero Hall planar offset requires a yaw-aware transform"
            )
        known_base_link_x_mm = known_x_mm
        known_base_link_y_mm = known_y_mm
        base_link_planar_offset_applied = True
    return HallLandmarkSample(
        timestamp_us=event.timestamp_ms * 1000,
        detected=None,
        raw_state=event.trigger_level,
        debounced_state=event.trigger_level,
        polarity_verified=False,
        status="ok",
        raw_value=event.trigger_level,
        source_sequence=event.sequence,
        landmark_index=event.landmark_index,
        known_x_mm=known_x_mm,
        known_y_mm=known_y_mm,
        known_base_link_x_mm=known_base_link_x_mm,
        known_base_link_y_mm=known_base_link_y_mm,
        base_link_planar_offset_applied=base_link_planar_offset_applied,
        baseline_level=event.baseline_level,
        baseline_inferred=event.baseline_inferred,
    )


def record_vehicle_demo_hall_stream(
    lines: Iterable[str],
    output_path: Path | str,
    *,
    overwrite: bool = False,
) -> Path:
    """Write VehicleDemo Hall statuses as replay-compatible Hall records."""
    output = Path(output_path)
    with MultiSensorRecorder(
        output,
        sensor_inventory=default_sensor_inventory(lidar_count=1, include_auxiliary=True),
        metadata={
            "generator": "rplidar_c1_tools.vehicle_demo_hall",
            "source": "vehicle_demo_jsonl",
            "hall_polarity": "unverified",
        },
        overwrite=overwrite,
    ) as recorder:
        messages = list(_iter_vehicle_demo_hall_messages(lines))
        events = [message for message in messages if isinstance(message, VehicleDemoHallEvent)]
        if events:
            for event in events:
                recorder.write_hall_landmark_sample(
                    vehicle_demo_hall_event_to_recording_sample(event)
                )
        else:
            for message in messages:
                if isinstance(message, VehicleDemoHallStatus):
                    recorder.write_hall_landmark_sample(
                        vehicle_demo_hall_to_recording_sample(message)
                    )
    return output


def analyze_vehicle_demo_hall_stream(lines: Iterable[str]) -> VehicleDemoHallSummary:
    """Summarize observed numeric levels without assigning Hall polarity."""
    messages = list(_iter_vehicle_demo_hall_messages(lines))
    statuses = [message for message in messages if isinstance(message, VehicleDemoHallStatus)]
    events = [message for message in messages if isinstance(message, VehicleDemoHallEvent)]
    if not statuses:
        raise VehicleDemoTelemetryError("no vehicle_demo_status records")

    raw_transitions = _transitions(statuses, "raw_level")
    debounced_transitions = _transitions(statuses, "debounced_level")
    first_timestamp_ms = statuses[0].timestamp_ms
    last_timestamp_ms = statuses[-1].timestamp_ms
    known_landmark_event_count = min(len(events), COURSE_LANDMARK_COUNT)
    unexpected_landmark_event_count = max(0, len(events) - COURSE_LANDMARK_COUNT)
    course_checkpoint_sequence_complete = len(events) >= COURSE_LANDMARK_COUNT
    next_expected_landmark_index = (
        len(events) + 1 if not course_checkpoint_sequence_complete else None
    )
    return VehicleDemoHallSummary(
        status_count=len(statuses),
        first_timestamp_ms=first_timestamp_ms,
        last_timestamp_ms=last_timestamp_ms,
        duration_ms=last_timestamp_ms - first_timestamp_ms,
        raw_zero_count=sum(status.raw_level == 0 for status in statuses),
        raw_one_count=sum(status.raw_level == 1 for status in statuses),
        debounced_zero_count=sum(status.debounced_level == 0 for status in statuses),
        debounced_one_count=sum(status.debounced_level == 1 for status in statuses),
        raw_debounced_mismatch_count=sum(
            status.raw_level != status.debounced_level for status in statuses
        ),
        raw_transitions=raw_transitions,
        debounced_transitions=debounced_transitions,
        landmark_events=tuple(events),
        known_landmark_event_count=known_landmark_event_count,
        unexpected_landmark_event_count=unexpected_landmark_event_count,
        course_checkpoint_sequence_complete=course_checkpoint_sequence_complete,
        next_expected_landmark_index=next_expected_landmark_index,
    )


def _transitions(
    statuses: list[VehicleDemoHallStatus],
    field_name: str,
) -> tuple[VehicleDemoHallTransition, ...]:
    transitions: list[VehicleDemoHallTransition] = []
    previous_level = getattr(statuses[0], field_name)
    for status in statuses[1:]:
        current_level = getattr(status, field_name)
        if current_level != previous_level:
            transitions.append(
                VehicleDemoHallTransition(
                    sequence=status.sequence,
                    timestamp_ms=status.timestamp_ms,
                    previous_level=previous_level,
                    current_level=current_level,
                )
            )
        previous_level = current_level
    return tuple(transitions)


def _transition_text(label: str, transition: VehicleDemoHallTransition) -> str:
    return (
        f"{label}_transition: sequence={transition.sequence}, "
        f"timestamp_ms={transition.timestamp_ms}, "
        f"level={transition.previous_level}->{transition.current_level}"
    )


def _event_text(event: VehicleDemoHallEvent) -> str:
    known_position = COURSE_LANDMARKS_MM.get(event.landmark_index)
    position_text = (
        f", known_x_mm={known_position[0]}, known_y_mm={known_position[1]}"
        if known_position is not None
        else ""
    )
    return (
        f"landmark_event: index={event.landmark_index}, "
        f"timestamp_ms={event.timestamp_ms}{position_text}"
    )


def _parse_record(line: str, line_number: int | None) -> dict[str, Any]:
    if line.strip() == "":
        raise VehicleDemoTelemetryError("blank telemetry line", line_number=line_number)
    try:
        record = json.loads(line, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        raise VehicleDemoTelemetryError("invalid JSON", line_number=line_number) from exc
    if not isinstance(record, dict):
        raise VehicleDemoTelemetryError("telemetry line must be a JSON object", line_number=line_number)
    if set(record) != _TOP_LEVEL_FIELDS:
        raise VehicleDemoTelemetryError("unexpected top-level fields", line_number=line_number)
    return record


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _non_negative_int(value: Any, name: str, line_number: int | None) -> int:
    if type(value) is not int or value < 0:
        raise VehicleDemoTelemetryError(f"{name} must be a non-negative integer", line_number=line_number)
    return value


def _binary_level(value: Any, name: str, line_number: int | None) -> int:
    level = _non_negative_int(value, name, line_number)
    if level not in (0, 1):
        raise VehicleDemoTelemetryError(f"{name} must be 0 or 1", line_number=line_number)
    return level


def _bool(value: Any, name: str, line_number: int | None) -> bool:
    if type(value) is not bool:
        raise VehicleDemoTelemetryError(f"{name} must be a boolean", line_number=line_number)
    return value


def _string(value: Any, name: str, line_number: int | None) -> str:
    if not isinstance(value, str) or value == "":
        raise VehicleDemoTelemetryError(f"{name} must be a non-empty string", line_number=line_number)
    return value
