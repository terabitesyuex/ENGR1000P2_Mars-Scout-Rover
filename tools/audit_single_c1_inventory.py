"""Audit current sources for stale active two-C1 assumptions.

This intentionally does not ban ``c1_2`` repository-wide. Historical version-1
recordings, compatibility tests, and explicitly synthetic multi-LiDAR fixtures
remain valid and are documented in ``ALLOWLIST_REASONS``.
"""

from __future__ import annotations

from pathlib import Path
import re


CURRENT_SOURCES = (
    "AGENTS.md",
    "README.md",
    "PROJECT_SPEC.md",
    "HARDWARE_LOCK.md",
    "docs/architecture.md",
    "docs/c1_pc_direct_test.md",
    "docs/communication_protocol.md",
    "docs/calibration.md",
    "docs/coordinate_frames.md",
    "docs/recording_format.md",
    "docs/test_plan.md",
    "docs/troubleshooting.md",
    "docs/wiring.md",
    "pc_direct/README.md",
    "pc/src/rplidar_c1_tools/recording_models.py",
    "pc/src/rplidar_c1_tools/cli.py",
    "pc/src/rplidar_c1_tools/c1_pc_direct.py",
    "pc/src/rplidar_c1_tools/stm32_recording_bridge.py",
    "pc/src/rplidar_c1_tools/stm32_serial_capture.py",
)

ALLOWLIST_REASONS = {
    "c1_2": "historical version-1 compatibility or explicitly synthetic multi-LiDAR coverage",
    "--lidar-count 2": "explicit synthetic multi-LiDAR compatibility option",
}

FORBIDDEN_ACTIVE_PATTERNS = (
    re.compile(r"RPLIDAR C1 x2", re.IGNORECASE),
    re.compile(r"two physical C1", re.IGNORECASE),
    re.compile(r"both C1 units", re.IGNORECASE),
    re.compile(r"test(?:ing)? `?c1_1`? and `?c1_2`? independently", re.IGNORECASE),
    re.compile(r"dual-C1 feasibility evaluation", re.IGNORECASE),
    re.compile(r"default[^\n]*lidar_count\s*[:=]\s*2", re.IGNORECASE),
)


def audit_repo(repo_root: Path) -> list[str]:
    errors: list[str] = []
    for relative in CURRENT_SOURCES:
        path = repo_root / relative
        if not path.exists():
            errors.append(f"{relative}: missing current source")
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in FORBIDDEN_ACTIVE_PATTERNS):
                if ("NOT CURRENT SCOPE" in line or "no current" in line.lower()
                        or "historical" in line.lower() or "synthetic" in line.lower()):
                    continue
                errors.append(f"{relative}:{line_number}: stale active two-C1 assumption")

    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    hardware = (repo_root / "HARDWARE_LOCK.md").read_text(encoding="utf-8")
    if "RPLIDAR C1M1-R2 x1" not in readme:
        errors.append("README.md: current inventory must state RPLIDAR C1M1-R2 x1")
    if "`c1_1`" not in hardware:
        errors.append("HARDWARE_LOCK.md: current physical LiDAR ID c1_1 is missing")
    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    errors = audit_repo(repo_root)
    if errors:
        print("Single-C1 inventory audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Single-C1 inventory audit passed")
    print("Allowlist: " + "; ".join(f"{key} ({value})" for key, value in ALLOWLIST_REASONS.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
