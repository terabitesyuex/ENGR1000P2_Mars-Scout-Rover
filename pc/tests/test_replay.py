from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import matplotlib
import pytest

matplotlib.use("Agg", force=True)

from rplidar_c1_tools.cli import record_synthetic_session
from rplidar_c1_tools.recorder import MultiSensorRecorder
from rplidar_c1_tools.replay import (
    RecordingFormatError,
    iter_lidar_scans,
    iter_recording_entries,
    last_lidar_scan_by_sensor,
    replay_lidar_scans,
)
from rplidar_c1_tools.synthetic_scan import generate_circle_scan
from rplidar_c1_tools.point_cloud_view import save_point_cloud_view
from rplidar_c1_tools.polar_view import save_polar_view


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def test_lazy_reader_preserves_two_c1_streams_and_point_order(tmp_path):
    path = tmp_path / "session.jsonl"
    record_synthetic_session(
        output_path=path,
        scene="room",
        frames=2,
        lidar_count=2,
        point_count=12,
        include_auxiliary=True,
        overwrite=False,
    )

    iterator = iter_lidar_scans(path)
    first = next(iterator)
    second = next(iterator)

    assert first.sensor_id == "c1_1"
    assert second.sensor_id == "c1_2"
    assert first.scan_frame.point_count == 12
    assert [point.angle_deg for point in first.scan_frame.points] == [
        index * 30.0 for index in range(12)
    ]
    assert first.rover_pose is not None
    assert first.rover_pose.x_m == 0.0


def test_replay_is_immediate_by_default_and_filterable_by_sensor(tmp_path):
    path = tmp_path / "session.jsonl"
    record_synthetic_session(
        output_path=path,
        scene="circle",
        frames=3,
        lidar_count=2,
        point_count=8,
        include_auxiliary=False,
        overwrite=False,
    )

    all_records = list(replay_lidar_scans(path))
    c1_2_records = list(replay_lidar_scans(path, sensor_id="c1_2"))

    assert len(all_records) == 6
    assert [record.sensor_id for record in c1_2_records] == ["c1_2", "c1_2", "c1_2"]
    assert [record.scan_frame.timestamp_us for record in c1_2_records] == [
        0,
        100_000,
        200_000,
    ]


def test_timed_replay_is_testable_without_real_sleep(tmp_path):
    path = tmp_path / "session.jsonl"
    record_synthetic_session(
        output_path=path,
        scene="circle",
        frames=3,
        lidar_count=1,
        point_count=4,
        include_auxiliary=False,
        overwrite=False,
    )
    sleeps: list[float] = []

    records = list(
        replay_lidar_scans(
            path,
            sensor_id="c1_1",
            timed=True,
            speed=2.0,
            sleep=sleeps.append,
        )
    )

    assert len(records) == 3
    assert sleeps == [0.05, 0.05]


def test_replayed_lidar_can_be_rendered_by_phase23_visualizers(tmp_path):
    path = tmp_path / "session.jsonl"
    output_dir = tmp_path / "visuals"
    record_synthetic_session(
        output_path=path,
        scene="room",
        frames=1,
        lidar_count=2,
        point_count=36,
        include_auxiliary=False,
        overwrite=False,
    )

    records = last_lidar_scan_by_sensor(path)
    generated = [
        save_polar_view(records["c1_1"].scan_frame, output_dir / "c1_1_polar.png"),
        save_point_cloud_view(records["c1_1"].scan_frame, output_dir / "c1_1_point_cloud.png"),
        save_polar_view(records["c1_2"].scan_frame, output_dir / "c1_2_polar.png"),
        save_point_cloud_view(records["c1_2"].scan_frame, output_dir / "c1_2_point_cloud.png"),
    ]

    for path in generated:
        assert path.read_bytes().startswith(b"\x89PNG")
        assert path.stat().st_size > 0


@pytest.mark.parametrize(
        ("contents", "message"),
        [
            ("", "missing header"),
            ("{}\n", "record_type must be a non-empty string"),
        (
            '{"record_type":"lidar_scan","schema_name":"mars_scout_multisensor_recording","schema_version":1}\n',
            "first record must be header",
        ),
        ("not-json\n", "line 1: invalid JSON"),
    ],
)
def test_malformed_recordings_report_line_numbers(tmp_path, contents, message):
    path = tmp_path / "bad.jsonl"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(RecordingFormatError, match=message):
        list(iter_recording_entries(path))


def test_reader_rejects_duplicate_unknown_sequence_and_timestamp_errors(tmp_path):
    duplicate_header = (
        _header_line(["c1_1", "c1_1"])
        + "\n"
    )
    _assert_bad_recording(tmp_path, duplicate_header, "line 1: duplicate sensor_id")

    unknown_sensor = "\n".join(
        [
            _header_line(["c1_1"]),
            _scan_line(sensor_id="c1_2", sequence=1, timestamp_us=0),
        ]
    )
    _assert_bad_recording(tmp_path, unknown_sensor + "\n", "line 2: unknown sensor_id")

    duplicate_sequence = "\n".join(
        [
            _header_line(["c1_1"]),
            _scan_line(sensor_id="c1_1", sequence=1, timestamp_us=0),
            _scan_line(sensor_id="c1_1", sequence=1, timestamp_us=100),
        ]
    )
    _assert_bad_recording(tmp_path, duplicate_sequence + "\n", "line 3: sequence")

    timestamp_backwards = "\n".join(
        [
            _header_line(["c1_1"]),
            _scan_line(sensor_id="c1_1", sequence=1, timestamp_us=100),
            _scan_line(sensor_id="c1_1", sequence=2, timestamp_us=0),
        ]
    )
    _assert_bad_recording(tmp_path, timestamp_backwards + "\n", "line 3: timestamp_us")


def test_cli_records_inspects_replays_and_renders_from_other_cwd(tmp_path):
    recording = tmp_path / "synthetic_multisensor_room.jsonl"
    inspection = tmp_path / "inspection.txt"
    render_dir = tmp_path / "visuals"

    record_result = _run_cli(
        tmp_path,
        "record-synthetic",
        "--scene",
        "room",
        "--frames",
        "2",
        "--lidar-count",
        "2",
        "--point-count",
        "24",
        "--include-aux",
        "--output",
        str(recording),
    )
    assert record_result.returncode == 0, record_result.stderr
    assert recording.stat().st_size > 0

    inspect_result = _run_cli(
        tmp_path,
        "inspect-recording",
        str(recording),
        "--output",
        str(inspection),
    )
    assert inspect_result.returncode == 0, inspect_result.stderr
    assert "c1_1" in inspection.read_text(encoding="utf-8")
    assert "c1_2" in inspect_result.stdout

    replay_result = _run_cli(
        tmp_path,
        "replay-recording",
        str(recording),
        "--sensor-id",
        "c1_1",
        "--limit",
        "2",
    )
    assert replay_result.returncode == 0, replay_result.stderr
    assert "replayed_lidar_scans=2" in replay_result.stdout

    render_result = _run_cli(
        tmp_path,
        "render-recording",
        str(recording),
        "--output-dir",
        str(render_dir),
    )
    assert render_result.returncode == 0, render_result.stderr
    for name in (
        "c1_1_last_polar.png",
        "c1_1_last_point_cloud.png",
        "c1_2_last_polar.png",
        "c1_2_last_point_cloud.png",
    ):
        assert (render_dir / name).stat().st_size > 0


def test_cli_refuses_overwrite_invalid_scene_and_bad_counts(tmp_path):
    recording = tmp_path / "session.jsonl"
    first = _run_cli(tmp_path, "record-synthetic", "--output", str(recording))
    assert first.returncode == 0, first.stderr

    overwrite = _run_cli(tmp_path, "record-synthetic", "--output", str(recording))
    assert overwrite.returncode != 0
    assert "already exists" in overwrite.stderr

    invalid_scene = _run_cli(tmp_path, "record-synthetic", "--scene", "bad", "--output", str(tmp_path / "bad.jsonl"))
    assert invalid_scene.returncode != 0

    invalid_frames = _run_cli(tmp_path, "record-synthetic", "--frames", "0", "--output", str(tmp_path / "bad2.jsonl"))
    assert invalid_frames.returncode != 0

    invalid_lidar_count = _run_cli(
        tmp_path,
        "record-synthetic",
        "--lidar-count",
        "3",
        "--output",
        str(tmp_path / "bad3.jsonl"),
    )
    assert invalid_lidar_count.returncode != 0


def test_replay_reader_keeps_existing_scanframe_contract(tmp_path):
    path = tmp_path / "session.jsonl"
    scan = generate_circle_scan(point_count=6, radius_mm=1234)
    with MultiSensorRecorder(path) as recorder:
        recorder.write_lidar_scan("c1_1", scan)

    [record] = list(iter_lidar_scans(path))

    assert record.scan_frame.source == "synthetic_circle"
    assert record.scan_frame.points[0].distance_mm == 1234
    assert record.scan_frame.points[1].angle_deg == 60.0


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "rplidar_c1_tools.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_bad_recording(tmp_path: Path, contents: str, message: str) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(RecordingFormatError, match=message):
        list(iter_recording_entries(path))


def _header_line(sensor_ids: list[str]) -> str:
    return (
        '{"record_type":"header","schema_name":"mars_scout_multisensor_recording",'
        '"schema_version":1,"sensor_inventory":['
        + ",".join(f'{{"sensor_id":"{sensor_id}"}}' for sensor_id in sensor_ids)
        + "]}"
    )


def _scan_line(*, sensor_id: str, sequence: int, timestamp_us: int) -> str:
    return (
        '{"record_type":"lidar_scan","schema_name":"mars_scout_multisensor_recording",'
        f'"schema_version":1,"sequence":{sequence},"timestamp_us":{timestamp_us},'
        f'"sensor_id":"{sensor_id}","points":[{{"angle_deg":0,"distance_mm":1000}}]}}'
    )
