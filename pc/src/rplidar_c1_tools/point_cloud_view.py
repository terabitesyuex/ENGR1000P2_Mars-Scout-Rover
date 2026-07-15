"""Headless-safe rover-centric Cartesian point-cloud visualization."""

from __future__ import annotations

import math
import os
from pathlib import Path

if os.name == "nt":
    os.environ.setdefault("WINDIR", r"C:\Windows")

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from . import coordinate_transform
from .data_models import CartesianPoint, ScanFrame


def create_point_cloud_figure(
    scan_frame: ScanFrame,
    *,
    include_invalid: bool = False,
    max_range_m: float | None = None,
    title: str | None = None,
    show_orientation_guides: bool = True,
) -> tuple[Figure, Axes]:
    """Create a rover-centric point-cloud figure.

    Display orientation is from above the rover: image top is rover forward
    and image left is rover left. The stored coordinates are not changed.
    Invalid points are excluded by default; with `include_invalid=True`, they
    are retained as NaN placeholders in the plotted data arrays.
    """
    _validate_scan_frame(scan_frame)
    _validate_max_range_m(max_range_m)
    points = coordinate_transform.scan_frame_to_cartesian(
        scan_frame,
        include_invalid=include_invalid,
    )
    display_y_m = [point.y_m for point in points]
    display_x_m = [point.x_m for point in points]

    figure = Figure(figsize=(6.0, 6.0), layout="constrained")
    axes = figure.add_subplot(111)
    axes.plot(display_y_m, display_x_m, linestyle="", marker=".", label="scan_points")
    axes.plot([0.0], [0.0], marker="+", color="black", label="rover_origin")
    axes.set_xlabel("rover y_m (left positive)")
    axes.set_ylabel("rover x_m (forward positive)")
    axes.set_aspect("equal", adjustable="box")
    axes.invert_xaxis()
    _set_axis_limits(axes, points, max_range_m)
    if show_orientation_guides:
        _add_orientation_guides(axes)
    if title:
        axes.set_title(title)
    return figure, axes


def save_point_cloud_view(
    scan_frame: ScanFrame,
    output_path: Path | str,
    *,
    include_invalid: bool = False,
    max_range_m: float | None = None,
    title: str | None = None,
    dpi: int = 150,
) -> Path:
    """Save a deterministic PNG point-cloud view and close the created figure."""
    path = _prepare_output_path(output_path)
    figure, _axes = create_point_cloud_figure(
        scan_frame,
        include_invalid=include_invalid,
        max_range_m=max_range_m,
        title=title,
    )
    try:
        figure.savefig(path, dpi=dpi, format="png")
    finally:
        from matplotlib import pyplot as plt

        plt.close(figure)
    return path


def _add_orientation_guides(axes: Axes) -> None:
    axes.axhline(0.0, color="0.80", linewidth=0.8)
    axes.axvline(0.0, color="0.80", linewidth=0.8)
    axes.text(0.5, 0.98, "Forward", transform=axes.transAxes, ha="center", va="top")
    axes.text(0.5, 0.02, "Backward", transform=axes.transAxes, ha="center", va="bottom")
    axes.text(0.02, 0.5, "Left", transform=axes.transAxes, ha="left", va="center")
    axes.text(0.98, 0.5, "Right", transform=axes.transAxes, ha="right", va="center")


def _set_axis_limits(
    axes: Axes,
    points: tuple[CartesianPoint, ...],
    max_range_m: float | None,
) -> None:
    if max_range_m is None:
        finite_values = [
            abs(value)
            for point in points
            for value in (point.x_m, point.y_m)
            if math.isfinite(value)
        ]
        max_range_m = max(finite_values, default=1.0)
        max_range_m = max(max_range_m * 1.05, 1.0)
    axes.set_xlim(max_range_m, -max_range_m)
    axes.set_ylim(-max_range_m, max_range_m)


def _validate_scan_frame(scan_frame: ScanFrame) -> None:
    if not isinstance(scan_frame, ScanFrame):
        raise ValueError("scan_frame must be a ScanFrame")


def _validate_max_range_m(max_range_m: float | None) -> None:
    if max_range_m is None:
        return
    if not math.isfinite(max_range_m) or max_range_m <= 0.0:
        raise ValueError("max_range_m must be a positive finite value")


def _prepare_output_path(output_path: Path | str) -> Path:
    path = Path(output_path)
    if path.exists() and path.is_dir():
        raise ValueError("output_path must be a file path, not a directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
