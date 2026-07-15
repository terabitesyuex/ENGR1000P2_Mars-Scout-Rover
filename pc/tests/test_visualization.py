from __future__ import annotations

import importlib
import math
import os
from pathlib import Path
import subprocess
import sys

import matplotlib

if os.name == "nt":
    os.environ.setdefault("WINDIR", r"C:\Windows")

matplotlib.use("Agg", force=True)

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.projections.polar import PolarAxes
import pytest

from rplidar_c1_tools import point_cloud_view, polar_view
from rplidar_c1_tools.data_models import CartesianPoint, ScanFrame, ScanPoint
from rplidar_c1_tools.polar_view import create_polar_figure, save_polar_view
from rplidar_c1_tools.point_cloud_view import (
    create_point_cloud_figure,
    save_point_cloud_view,
)
from rplidar_c1_tools.synthetic_scan import generate_circle_scan, generate_room_scan


def close_figure(figure: Figure) -> None:
    plt.close(figure)


def png_signature(path: Path) -> bytes:
    return path.read_bytes()[:8]


def cardinal_frame() -> ScanFrame:
    return ScanFrame(
        timestamp_us=0,
        points=[
            ScanPoint(angle_deg=0.0, distance_mm=1000),
            ScanPoint(angle_deg=90.0, distance_mm=1000),
            ScanPoint(angle_deg=180.0, distance_mm=1000),
            ScanPoint(angle_deg=270.0, distance_mm=1000),
        ],
        source="unit_test",
    )


def invalid_frame() -> ScanFrame:
    return ScanFrame(
        timestamp_us=0,
        points=[
            ScanPoint(angle_deg=0.0, distance_mm=1000),
            ScanPoint(angle_deg=90.0, distance_mm=-1),
        ],
    )


def test_visualization_module_import_does_not_open_windows() -> None:
    before = set(plt.get_fignums())

    importlib.reload(polar_view)
    importlib.reload(point_cloud_view)

    assert set(plt.get_fignums()) == before


def test_polar_figure_creation_uses_rover_angle_convention() -> None:
    frame = cardinal_frame()
    original_points = list(frame.points)

    figure, axes = create_polar_figure(frame, max_range_m=2.0, title="cardinal")
    try:
        assert isinstance(figure, Figure)
        assert isinstance(axes, PolarAxes)
        assert axes.get_theta_direction() == 1
        assert math.isclose(axes.get_theta_offset(), math.pi / 2.0, abs_tol=1e-9)
        line = axes.lines[0]
        assert len(line.get_xdata()) == 4
        assert list(line.get_ydata()) == [1.0, 1.0, 1.0, 1.0]
        assert math.isclose(line.get_xdata()[1], math.pi / 2.0, abs_tol=1e-9)
        assert frame.points == original_points
    finally:
        close_figure(figure)


def test_polar_invalid_points_are_excluded_by_default_and_explicitly_retained() -> None:
    frame = invalid_frame()

    default_figure, default_axes = create_polar_figure(frame)
    include_figure, include_axes = create_polar_figure(frame, include_invalid=True)
    try:
        assert len(default_axes.lines[0].get_xdata()) == 1
        assert len(include_axes.lines[0].get_xdata()) == 2
        assert math.isnan(include_axes.lines[0].get_ydata()[1])
    finally:
        close_figure(default_figure)
        close_figure(include_figure)


@pytest.mark.parametrize("max_range_m", [0.0, -1.0, math.inf, math.nan])
def test_polar_rejects_invalid_max_range(max_range_m: float) -> None:
    with pytest.raises(ValueError, match="max_range_m"):
        create_polar_figure(cardinal_frame(), max_range_m=max_range_m)


def test_point_cloud_figure_creation_uses_rover_centric_display() -> None:
    frame = cardinal_frame()
    original_points = list(frame.points)

    figure, axes = create_point_cloud_figure(frame, max_range_m=2.0)
    try:
        assert isinstance(figure, Figure)
        assert isinstance(axes, Axes)
        assert axes.name == "rectilinear"
        assert axes.get_aspect() == 1.0
        assert axes.xaxis_inverted()
        line = axes.lines[0]
        assert len(line.get_xdata()) == 4
        assert list(line.get_xdata()) == pytest.approx([0.0, 1.0, 0.0, -1.0])
        assert list(line.get_ydata()) == pytest.approx([1.0, 0.0, -1.0, 0.0])
        assert frame.points == original_points
    finally:
        close_figure(figure)


def test_point_cloud_uses_existing_scan_frame_to_cartesian(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []

    def fake_convert(frame: ScanFrame, *, include_invalid: bool = True):
        calls.append(include_invalid)
        return (
            CartesianPoint(
                x_m=1.0,
                y_m=2.0,
                source_angle_deg=0.0,
                source_distance_mm=1000.0,
            ),
        )

    monkeypatch.setattr(point_cloud_view.coordinate_transform, "scan_frame_to_cartesian", fake_convert)
    figure, axes = create_point_cloud_figure(cardinal_frame(), include_invalid=False)
    try:
        assert calls == [False]
        assert list(axes.lines[0].get_xdata()) == [2.0]
        assert list(axes.lines[0].get_ydata()) == [1.0]
    finally:
        close_figure(figure)


def test_point_cloud_invalid_point_policy_and_max_range_validation() -> None:
    frame = invalid_frame()

    default_figure, default_axes = create_point_cloud_figure(frame)
    include_figure, include_axes = create_point_cloud_figure(frame, include_invalid=True)
    try:
        assert len(default_axes.lines[0].get_xdata()) == 1
        assert len(include_axes.lines[0].get_xdata()) == 2
        assert math.isnan(include_axes.lines[0].get_xdata()[1])
        assert math.isnan(include_axes.lines[0].get_ydata()[1])
    finally:
        close_figure(default_figure)
        close_figure(include_figure)

    with pytest.raises(ValueError, match="max_range_m"):
        create_point_cloud_figure(frame, max_range_m=math.nan)


def test_known_cardinal_points_display_in_expected_directions() -> None:
    figure, axes = create_point_cloud_figure(cardinal_frame(), max_range_m=2.0)
    try:
        line = axes.lines[0]
        by_angle = {
            angle: (display_y_m, display_x_m)
            for angle, display_y_m, display_x_m in zip(
                [0.0, 90.0, 180.0, 270.0],
                line.get_xdata(),
                line.get_ydata(),
            )
        }
        assert by_angle[0.0][1] > 0.0
        assert by_angle[90.0][0] > 0.0
        assert by_angle[180.0][1] < 0.0
        assert by_angle[270.0][0] < 0.0
        assert axes.xaxis_inverted()
    finally:
        close_figure(figure)


def test_png_exports_create_parent_directories_and_preserve_source(tmp_path: Path) -> None:
    frame = cardinal_frame()
    original_points = list(frame.points)
    polar_path = tmp_path / "nested" / "polar.png"
    point_cloud_path = tmp_path / "nested" / "point_cloud.png"

    returned_polar = save_polar_view(frame, polar_path)
    returned_point_cloud = save_point_cloud_view(frame, point_cloud_path)
    save_polar_view(frame, polar_path)

    assert returned_polar == polar_path
    assert returned_point_cloud == point_cloud_path
    for path in (polar_path, point_cloud_path):
        assert path.exists()
        assert path.stat().st_size > 0
        assert png_signature(path) == b"\x89PNG\r\n\x1a\n"
    assert frame.points == original_points


def test_save_rejects_directory_output_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="file path"):
        save_polar_view(cardinal_frame(), tmp_path)
    with pytest.raises(ValueError, match="file path"):
        save_point_cloud_view(cardinal_frame(), tmp_path)


def test_synthetic_circle_and_room_render_semantics_are_finite() -> None:
    circle = generate_circle_scan(point_count=16, radius_mm=1500)
    room = generate_room_scan(point_count=8, room_length_mm=6000, room_width_mm=4000)

    circle_figure, circle_axes = create_point_cloud_figure(circle)
    room_figure, room_axes = create_point_cloud_figure(room)
    try:
        circle_x = list(circle_axes.lines[0].get_xdata())
        circle_y = list(circle_axes.lines[0].get_ydata())
        for display_y_m, display_x_m in zip(circle_x, circle_y):
            assert math.isfinite(display_y_m)
            assert math.isfinite(display_x_m)
            assert math.isclose(math.hypot(display_y_m, display_x_m), 1.5, abs_tol=1e-9)

        room_x = list(room_axes.lines[0].get_xdata())
        room_y = list(room_axes.lines[0].get_ydata())
        assert room_x[1] > 0.0 and room_y[1] > 0.0
        assert room_x[3] > 0.0 and room_y[3] < 0.0
        assert room_x[5] < 0.0 and room_y[5] < 0.0
        assert room_x[7] < 0.0 and room_y[7] > 0.0
    finally:
        close_figure(circle_figure)
        close_figure(room_figure)


def run_cli(tmp_path: Path, scene: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_root = Path(__file__).resolve().parents[1] / "src"
    env["PYTHONPATH"] = str(src_root)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "rplidar_c1_tools.cli",
            "render-synthetic",
            "--scene",
            scene,
            "--output-dir",
            str(tmp_path),
            "--no-show",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_render_synthetic_outputs_expected_files(tmp_path: Path) -> None:
    result = run_cli(tmp_path, "both")

    assert result.returncode == 0, result.stderr
    expected = {
        "circle_polar.png",
        "circle_point_cloud.png",
        "room_polar.png",
        "room_point_cloud.png",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    for file_name in expected:
        path = tmp_path / file_name
        assert path.stat().st_size > 0
        assert str(path) in result.stdout


def test_cli_render_synthetic_scene_selection_and_invalid_scene(tmp_path: Path) -> None:
    circle_dir = tmp_path / "circle"
    room_dir = tmp_path / "room"

    circle = run_cli(circle_dir, "circle")
    room = run_cli(room_dir, "room")
    invalid = run_cli(tmp_path / "bad", "bad")

    assert circle.returncode == 0
    assert {path.name for path in circle_dir.iterdir()} == {
        "circle_polar.png",
        "circle_point_cloud.png",
    }
    assert room.returncode == 0
    assert {path.name for path in room_dir.iterdir()} == {
        "room_polar.png",
        "room_point_cloud.png",
    }
    assert invalid.returncode != 0
