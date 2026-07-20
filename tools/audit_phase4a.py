"""Audit the software-only Phase 4A repository boundary and hygiene."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "e14d1d2392fc17115b684691f7b4ae92e7a4a4bc"
REQUIRED_FILES = (
    "docs/phase4a_mecanum_kinematics_odometry_foundation.md",
    "pc/src/rplidar_c1_tools/mecanum_odometry.py",
    "pc/src/rplidar_c1_tools/mecanum_odometry_simulator.py",
    "pc/tests/test_mecanum_kinematics_odometry.py",
    "pc/tests/test_mecanum_odometry_simulator.py",
    "pc/tests/test_mecanum_odometry_cli.py",
    "pc/tests/test_phase4a_foundation.py",
    "tools/audit_phase4a.py",
)
PHASE4A_SCOPE_FILES = REQUIRED_FILES
WINDOWS_USER_PATH_RE = re.compile(r"[A-Za-z]:\\(?:Users|Documents and Settings)\\")
POSIX_USER_PATH_RE = re.compile(r"/(?:home|Users)/[^/\s]+/")
COM_PORT_RE = re.compile(r"\bCOM[0-9]{1,3}\b")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--status-output", type=Path, required=True)
    args = parser.parse_args()

    failures: list[str] = []
    lines = ["Phase 4A mecanum kinematics and odometry software audit"]
    _check_required_files(lines, failures)
    _check_source_contract(lines, failures)
    _check_documentation(lines, failures)
    _check_software_only_diff(lines, failures)
    _check_privacy(lines, failures)
    _check_generated_artifacts(lines, failures)
    lines.extend(
        (
            "software_status: SOFTWARE_VERIFIED",
            "physical_status: UNVERIFIED",
            "hardware_access_by_automation: none",
            "serial_or_usb_access_by_automation: none",
            "keil_or_flymcu_invocation_by_automation: none",
            "flash_attempted_by_automation: no",
        )
    )
    lines.append(f"audit_status: {'FAIL' if failures else 'PASS'}")
    for failure in failures:
        lines.append(f"failure: {failure}")

    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_status(args.status_output)
    for line in lines:
        print(line)
    return 1 if failures else 0


def _check_required_files(lines: list[str], failures: list[str]) -> None:
    missing = [relative for relative in REQUIRED_FILES if not (REPO_ROOT / relative).is_file()]
    lines.append(f"required_files_present: {not missing}")
    if missing:
        failures.append("missing required files: " + ", ".join(missing))


def _check_source_contract(lines: list[str], failures: list[str]) -> None:
    paths = [
        REPO_ROOT / "pc/src/rplidar_c1_tools/mecanum_odometry.py",
        REPO_ROOT / "pc/src/rplidar_c1_tools/mecanum_odometry_simulator.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
    required = (
        "class MecanumGeometry",
        "class EncoderConfiguration",
        "class WheelAngularVelocities",
        "class WheelCountDeltas",
        "class BodyTwist2D",
        "class Pose2D",
        "class OdometrySample",
        "def inverse_mecanum_kinematics",
        "def forward_mecanum_kinematics",
        "def encoder_counter_delta",
        "def integrate_constant_body_twist",
        "MECANUM_ODOMETRY_SCENARIOS",
    )
    missing = [snippet for snippet in required if snippet not in text]
    lines.append(f"source_contract_present: {not missing}")
    if missing:
        failures.append("missing source contract: " + ", ".join(missing))

    lowered = text.lower()
    forbidden = (
        "import serial",
        "from serial",
        "import usb",
        "import socket",
        "gpio",
        "i2c",
        "flymcu",
        "keil",
    )
    found = [snippet for snippet in forbidden if snippet in lowered]
    lines.append(f"hardware_access_imports_present: {bool(found)}")
    if found:
        failures.append("hardware access terms in Phase 4A modules: " + ", ".join(found))


def _check_documentation(lines: list[str], failures: list[str]) -> None:
    path = REPO_ROOT / "docs/phase4a_mecanum_kinematics_odometry_foundation.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required = (
        "SOFTWARE_VERIFIED software-only foundation",
        "+x`: forward",
        "+y`: left",
        "front_left",
        "counts_per_wheel_revolution",
        "se2_constant_twist_exponential",
        "synthetic test values, not rover measurements",
        "UNVERIFIED physical facts",
        "Phase 4 is not physically complete",
    )
    missing = [snippet for snippet in required if snippet not in text]
    lines.append(f"documentation_boundary_present: {not missing}")
    if missing:
        failures.append("missing documentation boundary: " + ", ".join(missing))


def _check_software_only_diff(lines: list[str], failures: list[str]) -> None:
    result = _run_git("log", "--format=%H", f"{BASE_COMMIT}..HEAD", "--", *PHASE4A_SCOPE_FILES)
    if result.returncode != 0:
        lines.append("firmware_files_changed: unknown")
        failures.append("git diff against Phase 4A base failed")
        return
    phase_commits = [line for line in result.stdout.splitlines() if line]
    firmware: set[str] = set()
    for commit in phase_commits:
        changed = _run_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)
        if changed.returncode != 0:
            lines.append("firmware_files_changed: unknown")
            failures.append(f"git diff-tree failed for Phase 4A scoped commit {commit}")
            return
        firmware.update(path for path in changed.stdout.splitlines() if path.startswith("firmware/"))
    lines.append(f"firmware_files_changed: {bool(firmware)}")
    if firmware:
        failures.append("software-only phase-scoped commit changed firmware: " + ", ".join(sorted(firmware)))


def _check_privacy(lines: list[str], failures: list[str]) -> None:
    findings: list[str] = []
    for relative in REQUIRED_FILES:
        path = REPO_ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if WINDOWS_USER_PATH_RE.search(text) or POSIX_USER_PATH_RE.search(text):
            findings.append(f"{relative}: absolute user path")
        if COM_PORT_RE.search(text):
            findings.append(f"{relative}: concrete COM port")
        if EMAIL_RE.search(text):
            findings.append(f"{relative}: email address")
    lines.append(f"privacy_findings_present: {bool(findings)}")
    if findings:
        failures.append("privacy findings: " + ", ".join(findings))


def _check_generated_artifacts(lines: list[str], failures: list[str]) -> None:
    result = _run_git("ls-files")
    if result.returncode != 0:
        lines.append("generated_artifacts_tracked: unknown")
        failures.append("git ls-files failed")
        return
    generated: list[str] = []
    for path in result.stdout.splitlines():
        lowered = path.lower()
        if path.startswith("evidence/"):
            continue
        if (
            lowered.startswith(".verification/")
            or "/__pycache__/" in lowered
            or lowered.startswith("__pycache__/")
            or "/.pytest_cache/" in lowered
            or lowered.endswith((".pyc", ".pyo", ".log", ".tmp", ".hex", ".axf", ".obj"))
            or ("phase4a" in lowered and lowered.endswith((".jsonl", ".png", ".jpg", ".jpeg")))
        ):
            generated.append(path)
    lines.append(f"generated_artifacts_tracked: {bool(generated)}")
    if generated:
        failures.append("tracked generated artifacts: " + ", ".join(generated[:8]))


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _write_status(path: Path) -> None:
    lines = (
        "Phase 4A hardware status",
        "phase_scope: software_only",
        "physical_geometry: UNVERIFIED",
        "encoder_resolution_and_gear_ratio: UNVERIFIED",
        "counter_width_and_acquisition_timing: UNVERIFIED",
        "motor_encoder_wheel_signs: UNVERIFIED",
        "mecanum_roller_orientation: UNVERIFIED",
        "motor_control_and_closed_loop_motion: NOT_IMPLEMENTED",
        "mpu6050_fusion: NOT_IMPLEMENTED",
        "physical_odometry_accuracy: UNVERIFIED",
        "manual_action_performed_by_verifier: none",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
