"""Audit committed Phase 2.5 physical C1 evidence without hardware access."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PC_SRC = REPO_ROOT / "pc" / "src"
if str(PC_SRC) not in sys.path:
    sys.path.insert(0, str(PC_SRC))

from rplidar_c1_tools.phase25_evidence import (  # noqa: E402
    CAPTURE_SPECS,
    SOURCE_ARCHIVE_SHA256,
    Phase25EvidenceError,
    validate_all_phase25_captures,
    validate_phase25_rviz_evidence,
)


REQUIRED_FILES = (
    "evidence/phase2.5/c1_1_physical_evidence.md",
    "evidence/phase2.5/c1_1_ros2_rviz_laserscan.png",
    "pc/src/rplidar_c1_tools/phase25_evidence.py",
    "pc/tests/test_phase25_physical_evidence.py",
    "tools/audit_phase25.py",
    *(str(spec["path"]) for spec in CAPTURE_SPECS.values()),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-output", type=Path, required=True)
    args = parser.parse_args()

    failures: list[str] = []
    lines = ["Phase 2.5 physical c1_1 evidence audit"]
    missing = [relative for relative in REQUIRED_FILES if not (REPO_ROOT / relative).is_file()]
    lines.append(f"required_files_present: {not missing}")
    if missing:
        failures.append("missing required files: " + ", ".join(missing))

    try:
        summaries = validate_all_phase25_captures(REPO_ROOT)
        rviz = validate_phase25_rviz_evidence(REPO_ROOT)
    except (OSError, Phase25EvidenceError) as exc:
        lines.append("physical_c1_evidence_valid: False")
        failures.append(str(exc))
    else:
        lines.extend(
            [
                "physical_c1_evidence_valid: True",
                f"source_archive_sha256: {SOURCE_ARCHIVE_SHA256}",
                f"capture_files: {len(summaries)}",
                f"scan_records: {sum(item.scan_count for item in summaries)}",
                f"scan_points: {sum(item.point_count for item in summaries)}",
                f"zero_quality_points: {sum(item.zero_quality_count for item in summaries)}",
                "over_12000_mm_points: "
                + str(sum(item.over_profile_range_count for item in summaries)),
                f"rviz_png_sha256: {rviz.sha256}",
                f"rviz_png_dimensions: {rviz.width_px}x{rviz.height_px}",
                "pc_direct_capture_and_replay_path: MANUAL_EVIDENCE_VERIFIED",
                "absolute_accuracy_and_wall_clock_scan_timing: UNVERIFIED",
            ]
        )

    lines.extend(
        [
            "hardware_access_by_audit: none",
            "serial_port_opened_by_audit: no",
            "flash_attempted_by_audit: no",
            "audit_status: " + ("FAIL" if failures else "PASS"),
        ]
    )
    if failures:
        lines.append("failures:")
        lines.extend(f"  - {failure}" for failure in failures)

    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.audit_output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
