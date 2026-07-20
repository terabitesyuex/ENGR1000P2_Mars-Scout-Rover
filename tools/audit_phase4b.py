"""Audit the software-only Phase 4B repository boundary and hygiene."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "53e1d666092a85728a99e238d7d243f13f93f4da"
REQUIRED_FILES = (
    "docs/phase4b_closed_loop_motion_control_foundation.md",
    "pc/src/rplidar_c1_tools/motion_control.py",
    "pc/src/rplidar_c1_tools/motion_control_simulator.py",
    "pc/tests/test_motion_control.py",
    "pc/tests/test_motion_control_simulator.py",
    "pc/tests/test_motion_control_cli.py",
    "pc/tests/test_phase4b_foundation.py",
    "tools/audit_phase4b.py",
)
PHASE4B_MODULES = (
    "pc/src/rplidar_c1_tools/motion_control.py",
    "pc/src/rplidar_c1_tools/motion_control_simulator.py",
)
PHASE4B_SCOPE_FILES = REQUIRED_FILES
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
    lines = ["Phase 4B closed-loop motion control software audit"]
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
            "gpio_i2c_timer_motor_encoder_sensor_access_by_automation: none",
            "keil_or_flymcu_invocation_by_automation: none",
            "flash_attempted_by_automation: no",
            "physical_defaults_supplied_by_phase4b: none",
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
    text = "\n".join(
        (REPO_ROOT / relative).read_text(encoding="utf-8")
        for relative in PHASE4B_MODULES
        if (REPO_ROOT / relative).is_file()
    )
    required = (
        "class BodyMotionCommand",
        "class WheelAccelerationLimits",
        "class PIDGains",
        "class PIDState",
        "class WheelControllerState",
        "class MotionSafetyPolicy",
        "class MotionControlSnapshot",
        "def desaturate_wheel_setpoints",
        "def limit_wheel_setpoint_acceleration",
        "def update_wheel_speed_pid",
        "def control_four_wheels",
        "def check_command_watchdog",
        "def evaluate_motion_safety",
        "def motion_control_step",
        "class SyntheticWheelPlantParameters",
        "MOTION_CONTROL_SCENARIOS",
    )
    missing = [snippet for snippet in required if snippet not in text]
    lines.append(f"source_contract_present: {not missing}")
    if missing:
        failures.append("missing source contract: " + ", ".join(missing))

    imports: set[str] = set()
    syntax_failures: list[str] = []
    for relative in PHASE4B_MODULES:
        path = REPO_ROOT / relative
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except SyntaxError as exc:
            syntax_failures.append(f"{relative}: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    forbidden_roots = {"serial", "usb", "usb1", "socket", "RPi", "machine", "gpiozero"}
    hardware_imports = sorted(
        name for name in imports if name.split(".", 1)[0] in forbidden_roots
    )
    lines.append(f"source_syntax_valid: {not syntax_failures}")
    lines.append(f"hardware_access_imports_present: {bool(hardware_imports)}")
    if syntax_failures:
        failures.extend(syntax_failures)
    if hardware_imports:
        failures.append("hardware access imports: " + ", ".join(hardware_imports))


def _check_documentation(lines: list[str], failures: list[str]) -> None:
    path = REPO_ROOT / "docs/phase4b_closed_loop_motion_control_foundation.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required = (
        "SOFTWARE_VERIFIED software-only foundation",
        "proportional desaturation",
        "derivative on measurement",
        "conditional integration",
        "stale exactly when",
        "dimensionless normalized control effort",
        "synthetic first-order wheel plant",
        "Safety precedence",
        "Phase 4C",
        "UNVERIFIED physical facts",
        "Phase 4 is not physically complete",
    )
    missing = [snippet for snippet in required if snippet not in text]
    lines.append(f"documentation_boundary_present: {not missing}")
    if missing:
        failures.append("missing documentation boundary: " + ", ".join(missing))


def _check_software_only_diff(lines: list[str], failures: list[str]) -> None:
    result = _run_git("log", "--format=%H", f"{BASE_COMMIT}..HEAD", "--", *PHASE4B_SCOPE_FILES)
    if result.returncode != 0:
        lines.append("firmware_files_changed: unknown")
        failures.append("git diff against Phase 4B base failed")
        return
    phase_commits = [line for line in result.stdout.splitlines() if line]
    firmware: set[str] = set()
    for commit in phase_commits:
        changed = _run_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)
        if changed.returncode != 0:
            lines.append("firmware_files_changed: unknown")
            failures.append(f"git diff-tree failed for Phase 4B scoped commit {commit}")
            return
        firmware.update(path for path in changed.stdout.splitlines() if path.startswith("firmware/"))
    lines.append(f"firmware_files_changed: {bool(firmware)}")
    if firmware:
        failures.append("software-only phase-scoped commit changed firmware: " + ", ".join(sorted(firmware)))


def _check_privacy(lines: list[str], failures: list[str]) -> None:
    result = _run_git("diff", "--name-only", BASE_COMMIT)
    paths = set(result.stdout.splitlines()) if result.returncode == 0 else set()
    paths.update(REQUIRED_FILES)
    untracked = _run_git("ls-files", "--others", "--exclude-standard")
    if untracked.returncode == 0:
        paths.update(untracked.stdout.splitlines())
    findings: list[str] = []
    for relative in sorted(paths):
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
    paths = set(result.stdout.splitlines())
    untracked = _run_git("ls-files", "--others", "--exclude-standard")
    if untracked.returncode == 0:
        paths.update(untracked.stdout.splitlines())
    for path in sorted(paths):
        lowered = path.lower()
        if path.startswith("evidence/"):
            continue
        if (
            lowered.startswith(".verification/")
            or "/__pycache__/" in lowered
            or lowered.startswith("__pycache__/")
            or "/.pytest_cache/" in lowered
            or lowered.endswith((".pyc", ".pyo", ".log", ".tmp", ".hex", ".axf", ".obj"))
            or ("phase4b" in lowered and lowered.endswith((".jsonl", ".png", ".jpg", ".jpeg")))
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
        "Phase 4B hardware status",
        "phase_scope: software_only",
        "motor_rotation: UNVERIFIED",
        "encoder_acquisition: UNVERIFIED",
        "wheel_motor_encoder_directions: UNVERIFIED",
        "pwm_polarity_and_mapping: UNVERIFIED",
        "pid_gain_physical_usability: UNVERIFIED",
        "mecanum_roller_orientation: UNVERIFIED",
        "trajectory_following: UNVERIFIED",
        "physical_stopping_distance: UNVERIFIED",
        "real_closed_loop_performance: UNVERIFIED",
        "manual_action_performed_by_verifier: none",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
