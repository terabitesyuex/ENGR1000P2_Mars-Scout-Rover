"""Headless-safe polar scan visualization for synthetic `ScanFrame` data."""

from __future__ import annotations

import math
import os
from pathlib import Path

if os.name == "nt":
    os.environ.setdefault("WINDIR", r"C:\Windows")

from matplotlib.figure import Figure
from matplotlib.projections.polar import PolarAxes

from .coordinate_transform import scan_point_to_cartesian
from .data_models import ScanFrame, ScanPoint


def create_polar_figure(
    scan_frame: ScanFrame,
    *,
    include_invalid: bool = False,
    max_range_m: float | None = None,
    title: str | None = None,
) -> tuple[Figure, PolarAxes]:
    """Create a polar figure with rover-frame angles.

    Invalid points are excluded by default. With `include_invalid=True`,
    invalid source points are retained in the plotted data arrays as NaN
    radius placeholders, so their positions are explicit without clamping.
    """
    _validate_scan_frame(scan_frame)
    _validate_max_range_m(max_range_m)

    theta_rad, radius_m = _polar_plot_data(scan_frame, include_invalid)
    figure = Figure(figsize=(6.0, 6.0), layout="constrained")
    axes = figure.add_subplot(111, projection="polar")
    axes.set_theta_zero_location("N")
    axes.set_theta_direction(1)
    axes.plot(theta_rad, radius_m, linestyle="", marker=".", label="scan_points")
    axes.set_ylabel("range_m")
    axes.set_rlabel_position(135)
    if max_range_m is not None:
        axes.set_ylim(0.0, max_range_m)
    if title:
        axes.set_title(title)
    return figure, axes


def save_polar_view(
    scan_frame: ScanFrame,
    output_path: Path | str,
    *,
    include_invalid: bool = False,
    max_range_m: float | None = None,
    title: str | None = None,
    dpi: int = 150,
) -> Path:
    """Save a deterministic PNG polar view and close the created figure."""
    path = _prepare_output_path(output_path)
    figure, _axes = create_polar_figure(
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


def _polar_plot_data(
    scan_frame: ScanFrame,
    include_invalid: bool,
) -> tuple[list[float], list[float]]:
    theta_rad: list[float] = []
    radius_m: list[float] = []
    for point in scan_frame.points:
        try:
            scan_point_to_cartesian(point)
            theta_rad.append(math.radians(point.angle_deg))
            radius_m.append(point.distance_mm / 1000.0)
        except ValueError:
            if include_invalid:
                theta_rad.append(_safe_radians(point))
                radius_m.append(math.nan)
    return theta_rad, radius_m


def _safe_radians(point: ScanPoint) -> float:
    try:
        angle_deg = float(point.angle_deg)
    except (TypeError, ValueError):
        return math.nan
    if not math.isfinite(angle_deg):
        return math.nan
    return math.radians(angle_deg)


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
