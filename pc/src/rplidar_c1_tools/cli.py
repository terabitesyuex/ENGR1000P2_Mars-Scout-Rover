"""Command-line entry points for PC-side tools."""

from __future__ import annotations

import argparse
from pathlib import Path

from .point_cloud_view import save_point_cloud_view
from .polar_view import save_polar_view
from .synthetic_scan import SyntheticRoomConfig, SyntheticScanSource, scan_to_json
from .synthetic_scan import generate_circle_scan, generate_room_scan


def main() -> int:
    parser = argparse.ArgumentParser(prog="rplidar-c1")
    subparsers = parser.add_subparsers(dest="command", required=True)

    synthetic = subparsers.add_parser(
        "synthetic-room",
        help="Generate deterministic synthetic scans without LiDAR hardware.",
    )
    synthetic.add_argument("--scans", type=int, default=1)
    synthetic.add_argument("--angle-step-deg", type=float, default=1.0)
    synthetic.add_argument("--room-length-mm", type=int, default=6000)
    synthetic.add_argument("--room-width-mm", type=int, default=4000)

    render = subparsers.add_parser(
        "render-synthetic",
        help="Render deterministic synthetic scan visualizations as PNG files.",
    )
    render.add_argument(
        "--scene",
        choices=("circle", "room", "both"),
        default="both",
        help="Synthetic scene to render.",
    )
    render.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".verification") / "phase2.3_visuals",
    )
    show_group = render.add_mutually_exclusive_group()
    show_group.add_argument(
        "--show",
        action="store_true",
        help="Display figures interactively after export.",
    )
    show_group.add_argument(
        "--no-show",
        action="store_false",
        dest="show",
        help="Do not display figures after export.",
    )
    render.set_defaults(show=False)

    args = parser.parse_args()
    if args.command == "synthetic-room":
        config = SyntheticRoomConfig(
            scan_count=args.scans,
            angle_step_deg=args.angle_step_deg,
            room_length_mm=args.room_length_mm,
            room_width_mm=args.room_width_mm,
        )
        for scan in SyntheticScanSource(config).scans():
            print(scan_to_json(scan))
        return 0
    if args.command == "render-synthetic":
        paths = render_synthetic(
            scene=args.scene,
            output_dir=args.output_dir,
            show=args.show,
        )
        for path in paths:
            print(path)
        return 0
    parser.error(f"unsupported command: {args.command}")
    return 2


def render_synthetic(scene: str, output_dir: Path, show: bool = False) -> list[Path]:
    """Render deterministic synthetic visualizations and return output paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes = _selected_scenes(scene)
    paths: list[Path] = []
    for scene_name in scenes:
        scan = _scan_for_scene(scene_name)
        paths.append(
            save_polar_view(
                scan,
                output_dir / f"{scene_name}_polar.png",
                title=f"Synthetic {scene_name} polar scan",
            )
        )
        paths.append(
            save_point_cloud_view(
                scan,
                output_dir / f"{scene_name}_point_cloud.png",
                title=f"Synthetic {scene_name} Cartesian point cloud",
            )
        )
    if show:
        from matplotlib import pyplot as plt

        for scene_name in scenes:
            scan = _scan_for_scene(scene_name)
            from .point_cloud_view import create_point_cloud_figure
            from .polar_view import create_polar_figure

            create_polar_figure(scan, title=f"Synthetic {scene_name} polar scan")
            create_point_cloud_figure(
                scan,
                title=f"Synthetic {scene_name} Cartesian point cloud",
            )
        plt.show()
    return paths


def _selected_scenes(scene: str) -> tuple[str, ...]:
    if scene == "both":
        return ("circle", "room")
    if scene in {"circle", "room"}:
        return (scene,)
    raise ValueError("scene must be one of: circle, room, both")


def _scan_for_scene(scene: str):
    if scene == "circle":
        return generate_circle_scan(point_count=360, radius_mm=2000)
    if scene == "room":
        return generate_room_scan(point_count=360, room_length_mm=6000, room_width_mm=4000)
    raise ValueError("scene must be one of: circle, room, both")


if __name__ == "__main__":
    raise SystemExit(main())
