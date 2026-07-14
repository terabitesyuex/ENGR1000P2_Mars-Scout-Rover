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
    synthetic.add_argument("--noise-std-mm", type=float, default=5.0)

    args = parser.parse_args()
    if args.command == "synthetic-room":
        config = SyntheticRoomConfig(
            scan_count=args.scans,
            angle_step_deg=args.angle_step_deg,
            noise_std_mm=args.noise_std_mm,
        )
        for scan in SyntheticScanSource(config).scans():
            print(scan_to_json(scan))
        return 0
    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
