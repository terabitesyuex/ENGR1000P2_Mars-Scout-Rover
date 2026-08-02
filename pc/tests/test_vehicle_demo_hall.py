from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import rplidar_c1_tools.vehicle_demo_hall as vehicle_demo_hall_module
from rplidar_c1_tools.replay import inspect_recording, iter_recording_entries
from rplidar_c1_tools.vehicle_demo_hall import (
    COURSE_LANDMARK_COUNT,
    COURSE_LANDMARKS_MM,
    HALL_SENSING_POINT_HEIGHT_ABOVE_FLOOR_MM,
    HALL_TO_BASE_LINK_PLANAR_OFFSET_MM,
    HALL_TO_BASE_LINK_Z_MM,
    VehicleDemoHallEvent,
    VehicleDemoTelemetryError,
    analyze_vehicle_demo_hall_stream,
    iter_vehicle_demo_hall_events,
    iter_vehicle_demo_hall_status,
    parse_vehicle_demo_hall_line,
    parse_vehicle_demo_hall_event_line,
    record_vehicle_demo_hall_stream,
    vehicle_demo_hall_to_recording_sample,
    vehicle_demo_hall_event_to_recording_sample,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def _line(
    sequence: int,
    timestamp_ms: int,
    *,
    raw_level: object = 1,
    debounced_level: object = 1,
    message_type: str = "vehicle_demo_status",
    status: str = "ok",
    event_status_fields: bool = False,
    landmark_count: int = 0,
) -> str:
    payload: dict[str, object] = {
        "control_state": "ready",
        "motion": "stop",
        "armed": True,
        "hall_raw_level": raw_level,
        "hall_debounced_level": debounced_level,
    }
    if event_status_fields:
        payload.update(
            {
                "hall_baseline_ready": True,
                "hall_baseline_level": 1,
                "hall_landmark_active": debounced_level == 0,
                "hall_landmark_count": landmark_count,
            }
        )
    if message_type != "vehicle_demo_status":
        payload = {"software": "configuration_only"}
    return json.dumps(
        {
            "sequence": sequence,
            "timestamp_ms": timestamp_ms,
            "message_type": message_type,
            "status": status,
            "payload": payload,
        },
        separators=(",", ":"),
    ) + "\r\n"


def _event_line(
    sequence: int,
    timestamp_ms: int,
    landmark_index: int,
    *,
    baseline_level: object = 1,
    trigger_level: object = 0,
    baseline_inferred: object = True,
) -> str:
    return json.dumps(
        {
            "sequence": sequence,
            "timestamp_ms": timestamp_ms,
            "message_type": "vehicle_demo_hall_event",
            "status": "ok",
            "payload": {
                "landmark_index": landmark_index,
                "baseline_level": baseline_level,
                "trigger_level": trigger_level,
                "baseline_inferred": baseline_inferred,
            },
        },
        separators=(",", ":"),
    ) + "\r\n"


def test_vehicle_status_parses_and_preserves_unverified_hall_levels() -> None:
    status = parse_vehicle_demo_hall_line(_line(7, 250, raw_level=0, debounced_level=1))

    assert status is not None
    assert status.sequence == 7
    assert status.timestamp_ms == 250
    assert status.raw_level == 0
    assert status.debounced_level == 1
    sample = vehicle_demo_hall_to_recording_sample(status)
    assert sample.timestamp_us == 250_000
    assert sample.raw_state == 0
    assert sample.debounced_state == 1
    assert sample.detected is None
    assert sample.polarity_verified is False
    assert sample.source_sequence == 7


def test_extended_status_preserves_baseline_and_latched_count() -> None:
    status = parse_vehicle_demo_hall_line(
        _line(
            7,
            250,
            raw_level=0,
            debounced_level=0,
            event_status_fields=True,
            landmark_count=1,
        )
    )

    assert status is not None
    assert status.baseline_ready is True
    assert status.baseline_level == 1
    assert status.landmark_active is True
    assert status.landmark_count == 1


def test_hall_event_uses_detection_timestamp_and_course_landmark() -> None:
    event = parse_vehicle_demo_hall_event_line(_event_line(8, 113, 1))

    assert event == VehicleDemoHallEvent(
        sequence=8,
        timestamp_ms=113,
        landmark_index=1,
        baseline_level=1,
        trigger_level=0,
        baseline_inferred=True,
    )
    sample = vehicle_demo_hall_event_to_recording_sample(event)
    assert COURSE_LANDMARKS_MM == {1: (600, 400), 2: (1800, 400), 3: (2200, 400)}
    assert COURSE_LANDMARK_COUNT == 3
    assert HALL_TO_BASE_LINK_PLANAR_OFFSET_MM == (0, 0)
    assert HALL_SENSING_POINT_HEIGHT_ABOVE_FLOOR_MM == 65.0
    assert HALL_TO_BASE_LINK_Z_MM == 25.5
    assert HALL_TO_BASE_LINK_Z_MM == HALL_SENSING_POINT_HEIGHT_ABOVE_FLOOR_MM - 79.0 / 2.0
    assert sample.timestamp_us == 113_000
    assert sample.landmark_index == 1
    assert (sample.known_x_mm, sample.known_y_mm) == (600, 400)
    assert (sample.known_base_link_x_mm, sample.known_base_link_y_mm) == (600, 400)
    assert sample.base_link_planar_offset_applied is True
    assert sample.detected is None
    assert sample.polarity_verified is False
    assert sample.baseline_inferred is True


def test_hall_event_outside_known_course_does_not_invent_base_link_fix() -> None:
    event = parse_vehicle_demo_hall_event_line(_event_line(9, 250, 4))

    sample = vehicle_demo_hall_event_to_recording_sample(event)

    assert (sample.known_x_mm, sample.known_y_mm) == (None, None)
    assert (sample.known_base_link_x_mm, sample.known_base_link_y_mm) == (None, None)
    assert sample.base_link_planar_offset_applied is False


def test_nonzero_hall_offset_is_refused_without_yaw_aware_transform(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = parse_vehicle_demo_hall_event_line(_event_line(9, 250, 1))
    monkeypatch.setattr(
        vehicle_demo_hall_module,
        "HALL_TO_BASE_LINK_PLANAR_OFFSET_MM",
        (1, 0),
    )

    with pytest.raises(VehicleDemoTelemetryError, match="yaw-aware transform"):
        vehicle_demo_hall_module.vehicle_demo_hall_event_to_recording_sample(event)


def test_identity_and_motor_diagnostics_are_ignored_without_losing_order() -> None:
    lines = [
        _line(0, 0, message_type="vehicle_demo_identity", status="software_ready"),
        _line(1, 250, raw_level=1, debounced_level=1),
        _line(2, 300, message_type="vehicle_demo_motor_diag"),
        _line(3, 500, raw_level=0, debounced_level=1, status="error"),
    ]

    statuses = list(iter_vehicle_demo_hall_status(lines))

    assert [status.sequence for status in statuses] == [1, 3]
    assert [(status.raw_level, status.debounced_level) for status in statuses] == [(1, 1), (0, 1)]


def test_vehicle_hall_stream_records_and_replays_with_existing_format(tmp_path) -> None:
    output = tmp_path / "vehicle_hall.jsonl"
    lines = [
        _line(10, 1000, raw_level=1, debounced_level=1),
        _line(11, 1250, raw_level=0, debounced_level=0),
    ]

    record_vehicle_demo_hall_stream(lines, output)

    summary = inspect_recording(output)
    assert summary.record_counts == {"hall_landmark": 2}
    records = [
        entry.payload
        for entry in iter_recording_entries(output)
        if entry.payload["record_type"] == "hall_landmark"
    ]
    assert records[0]["raw_state"] == 1
    assert records[0]["debounced_state"] == 1
    assert records[1]["raw_state"] == 0
    assert records[1]["debounced_state"] == 0
    assert all(record["detected"] is None for record in records)
    assert all(record["polarity_verified"] is False for record in records)
    assert [record["source_sequence"] for record in records] == [10, 11]


def test_latched_events_are_recorded_once_instead_of_periodic_statuses(tmp_path) -> None:
    output = tmp_path / "vehicle_hall_events.jsonl"
    lines = [
        _line(1, 100, event_status_fields=True),
        _event_line(2, 125, 1),
        _line(
            3,
            250,
            raw_level=0,
            debounced_level=0,
            event_status_fields=True,
            landmark_count=1,
        ),
        _line(4, 500, event_status_fields=True, landmark_count=1),
        _event_line(5, 625, 2),
    ]

    assert [event.landmark_index for event in iter_vehicle_demo_hall_events(lines)] == [1, 2]
    record_vehicle_demo_hall_stream(lines, output)
    records = [
        entry.payload
        for entry in iter_recording_entries(output)
        if entry.payload["record_type"] == "hall_landmark"
    ]
    assert [record["landmark_index"] for record in records] == [1, 2]
    assert [(record["known_x_mm"], record["known_y_mm"]) for record in records] == [
        (600, 400),
        (1800, 400),
    ]
    assert [
        (record["known_base_link_x_mm"], record["known_base_link_y_mm"])
        for record in records
    ] == [(600, 400), (1800, 400)]
    assert all(record["base_link_planar_offset_applied"] is True for record in records)
    assert [record["timestamp_us"] for record in records] == [125_000, 625_000]


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("not-json\n", "invalid JSON"),
        (_line(1, 0, raw_level=True), "hall_raw_level"),
        (_line(1, 0, raw_level=2), "hall_raw_level"),
        (_line(1, 0, debounced_level=-1), "hall_debounced_level"),
        (_line(1, 0, message_type="unknown"), "unsupported message_type"),
    ],
)
def test_invalid_vehicle_hall_data_is_rejected(line: str, message: str) -> None:
    with pytest.raises(VehicleDemoTelemetryError, match=message):
        parse_vehicle_demo_hall_line(line)


@pytest.mark.parametrize(
    ("line", "message"),
    [
        (_event_line(1, 0, 1, baseline_level=1, trigger_level=1), "differ from baseline"),
        (_event_line(1, 0, 1, baseline_inferred=False), "baseline must be inferred"),
    ],
)
def test_invalid_vehicle_hall_event_is_rejected(line: str, message: str) -> None:
    with pytest.raises(VehicleDemoTelemetryError, match=message):
        parse_vehicle_demo_hall_event_line(line)


def test_stream_rejects_sequence_and_timestamp_regression() -> None:
    with pytest.raises(VehicleDemoTelemetryError, match="sequence must increase"):
        list(iter_vehicle_demo_hall_status([_line(2, 10), _line(2, 20)]))
    with pytest.raises(VehicleDemoTelemetryError, match="timestamp_ms must be nondecreasing"):
        list(iter_vehicle_demo_hall_status([_line(2, 20), _line(3, 10)]))
    with pytest.raises(VehicleDemoTelemetryError, match="without gaps"):
        list(iter_vehicle_demo_hall_events([_event_line(1, 10, 2)]))
    with pytest.raises(VehicleDemoTelemetryError, match="missing latched Hall event"):
        list(
            iter_vehicle_demo_hall_events(
                [_line(1, 10, event_status_fields=True, landmark_count=1)]
            )
        )


def test_analysis_reports_observed_transitions_without_hall_semantics() -> None:
    summary = analyze_vehicle_demo_hall_stream(
        [
            _line(1, 100, raw_level=1, debounced_level=1),
            _line(2, 150, raw_level=0, debounced_level=1),
            _line(3, 200, raw_level=0, debounced_level=0),
            _line(4, 250, raw_level=1, debounced_level=0),
            _line(5, 300, raw_level=1, debounced_level=1),
            _event_line(6, 325, 1),
        ]
    )

    assert summary.status_count == 5
    assert summary.duration_ms == 200
    assert (summary.raw_zero_count, summary.raw_one_count) == (2, 3)
    assert (summary.debounced_zero_count, summary.debounced_one_count) == (2, 3)
    assert summary.raw_debounced_mismatch_count == 2
    assert [transition.sequence for transition in summary.raw_transitions] == [2, 4]
    assert [transition.timestamp_ms for transition in summary.debounced_transitions] == [200, 300]
    assert [event.landmark_index for event in summary.landmark_events] == [1]
    assert summary.known_landmark_event_count == 1
    assert summary.unexpected_landmark_event_count == 0
    assert summary.course_checkpoint_sequence_complete is False
    assert summary.next_expected_landmark_index == 2
    text = summary.to_text()
    assert "hall_semantics: unverified_numeric_levels_only" in text
    assert "raw_transition: sequence=2, timestamp_ms=150, level=1->0" in text
    assert "course_checkpoint_sequence_complete: false" in text
    assert "next_expected_landmark_index: 2" in text
    assert "magnet_present" not in text
    assert "landmark_event: index=1, timestamp_ms=325, known_x_mm=600, known_y_mm=400" in text


def test_analysis_reports_complete_course_and_unexpected_extra_event() -> None:
    summary = analyze_vehicle_demo_hall_stream(
        [
            _line(1, 100, event_status_fields=True),
            _event_line(2, 200, 1),
            _event_line(3, 300, 2),
            _event_line(4, 400, 3),
            _event_line(5, 500, 4),
        ]
    )

    assert summary.known_landmark_event_count == 3
    assert summary.unexpected_landmark_event_count == 1
    assert summary.course_checkpoint_sequence_complete is True
    assert summary.next_expected_landmark_index is None
    text = summary.to_text()
    assert "course_checkpoint_sequence_complete: true" in text
    assert "unexpected_landmark_event_count: 1" in text
    assert "next_expected_landmark_index: null" in text


def test_analysis_requires_at_least_one_vehicle_status() -> None:
    with pytest.raises(VehicleDemoTelemetryError, match="no vehicle_demo_status records"):
        analyze_vehicle_demo_hall_stream(
            [_line(0, 0, message_type="vehicle_demo_identity", status="software_ready")]
        )


def test_offline_cli_records_and_inspects_vehicle_hall_from_other_cwd(tmp_path) -> None:
    source = tmp_path / "vehicle.jsonl"
    recording = tmp_path / "recording.jsonl"
    source.write_text(
        _line(0, 0, message_type="vehicle_demo_identity", status="software_ready")
        + _line(1, 250, raw_level=1, debounced_level=1)
        + _line(2, 500, raw_level=0, debounced_level=0),
        encoding="utf-8",
        newline="",
    )

    result = _run_cli(
        tmp_path,
        "record-vehicle-demo-hall",
        "--input",
        str(source),
        "--output",
        str(recording),
    )
    assert result.returncode == 0, result.stderr

    inspection = _run_cli(tmp_path, "inspect-recording", str(recording))
    assert inspection.returncode == 0, inspection.stderr
    assert "hall_landmark: 2" in inspection.stdout

    hall_report = _run_cli(
        tmp_path,
        "inspect-vehicle-demo-hall",
        "--input",
        str(source),
    )
    assert hall_report.returncode == 0, hall_report.stderr
    assert "status_count: 2" in hall_report.stdout
    assert "raw_transition_count: 1" in hall_report.stdout
    assert "debounced_transition_count: 1" in hall_report.stdout

    overwrite = _run_cli(
        tmp_path,
        "record-vehicle-demo-hall",
        "--input",
        str(source),
        "--output",
        str(recording),
    )
    assert overwrite.returncode != 0
    assert "already exists" in overwrite.stderr


def test_offline_cli_rejects_malformed_vehicle_jsonl(tmp_path) -> None:
    source = tmp_path / "bad.jsonl"
    source.write_text("not-json\n", encoding="utf-8")

    result = _run_cli(
        tmp_path,
        "record-vehicle-demo-hall",
        "--input",
        str(source),
        "--output",
        str(tmp_path / "recording.jsonl"),
    )

    assert result.returncode != 0
    assert "invalid JSON" in result.stderr


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "rplidar_c1_tools.cli", *args],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
