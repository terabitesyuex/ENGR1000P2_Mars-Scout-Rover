"""Command-line entry points for PC-side tools."""

from __future__ import annotations

import argparse

from .synthetic_scan import SyntheticRoomConfig, SyntheticScanSource, scan_to_json


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
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
