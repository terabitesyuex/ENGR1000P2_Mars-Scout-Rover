"""Write one deterministic synthetic scan to data/synthetic for inspection."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
PC_SRC = REPO_ROOT / "pc" / "src"
if str(PC_SRC) not in sys.path:
    sys.path.insert(0, str(PC_SRC))

from rplidar_c1_tools.synthetic_scan import (  # noqa: E402
    generate_room_scan,
    scan_to_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "synthetic" / "synthetic_scan.json",
    )
    args = parser.parse_args()

    scan = generate_room_scan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(scan_to_json(scan), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
