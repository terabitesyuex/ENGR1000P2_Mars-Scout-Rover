from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_phase4b_current_plan_documents_software_and_physical_boundaries():
    required = {
        "AGENTS.md": [
            "Phase 4B software work is complete",
            "normalized control effort is dimensionless",
            "real closed-loop performance remain UNVERIFIED",
        ],
        "README.md": [
            "Phase 4B Closed-Loop Motion Control",
            "simulate-motion-control",
            "Real motor/encoder behavior",
        ],
        "docs/phase4b_closed_loop_motion_control_foundation.md": [
            "SOFTWARE_VERIFIED software-only foundation",
            "proportional desaturation",
            "derivative on measurement",
            "conditional integration",
            "stale exactly when",
            "Safety precedence",
            "dimensionless normalized control effort",
            "synthetic first-order wheel plant",
            "Phase 4C",
            "UNVERIFIED physical facts",
            "Phase 4 is not physically complete",
        ],
        "docs/stm32_sensor_protocol.md": [
            "body_motion_command",
            "motion_control_snapshot",
            "synthetic_phase4b_motion_control",
        ],
        "docs/recording_format.md": [
            "wheel_control_effort",
            "Existing recordings need none of these record types",
        ],
        "docs/test_plan.md": [
            "phase4b",
            "Phase 4B automated tests do not open COM ports",
        ],
    }
    missing: list[str] = []
    for relative, snippets in required.items():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{relative}: {snippet}")
    assert missing == []


def test_phase4b_manifest_is_hardware_free_and_runs_all_software_layers():
    manifest = json.loads(
        (REPO_ROOT / "tools/verification/phase_manifest.json").read_text(encoding="utf-8")
    )
    assert "phase4b" in manifest["supported_phases"]
    phase = manifest["phases"]["phase4b"]
    assert set(phase["targeted"]) == {
        "pc/tests/test_motion_control.py",
        "pc/tests/test_motion_control_simulator.py",
        "pc/tests/test_motion_control_cli.py",
        "pc/tests/test_phase4b_foundation.py",
    }
    assert phase["full"] == ["pc/tests"]
    command_text = json.dumps(phase["python_commands"]).lower()
    for forbidden in (
        "--port",
        "capture",
        "serial",
        "usb",
        "keil",
        "flymcu",
        "flash",
        "gpio",
    ):
        assert forbidden not in command_text
    assert "simulate-motion-control" in command_text
    assert "audit_phase4b.py" in command_text


def test_phase4b_modules_have_no_hardware_access_imports():
    module_paths = [
        REPO_ROOT / "pc/src/rplidar_c1_tools/motion_control.py",
        REPO_ROOT / "pc/src/rplidar_c1_tools/motion_control_simulator.py",
    ]
    imports: set[str] = set()
    for path in module_paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    forbidden_roots = {"serial", "usb", "usb1", "socket", "RPi", "machine", "gpiozero"}
    assert not {name for name in imports if name.split(".", 1)[0] in forbidden_roots}


def test_phase4b_audit_reports_privacy_artifact_and_hardware_boundaries(tmp_path):
    audit_output = tmp_path / "software_audit.txt"
    status_output = tmp_path / "hardware_status.txt"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools/audit_phase4b.py"),
            "--audit-output",
            str(audit_output),
            "--status-output",
            str(status_output),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    audit = audit_output.read_text(encoding="utf-8")
    status = status_output.read_text(encoding="utf-8")
    assert "audit_status: PASS" in audit
    assert "privacy_findings_present: False" in audit
    assert "generated_artifacts_tracked: False" in audit
    assert "hardware_access_by_automation: none" in audit
    assert "serial_or_usb_access_by_automation: none" in audit
    assert "physical_defaults_supplied_by_phase4b: none" in audit
    assert "pid_gain_physical_usability: UNVERIFIED" in status
    assert "physical_stopping_distance: UNVERIFIED" in status
    assert "manual_action_performed_by_verifier: none" in status


def test_phase4b_firmware_diff_audit_is_scoped_and_still_rejects_phase_firmware_changes(monkeypatch):
    audit_module = _load_audit_module("audit_phase4b_scoped", REPO_ROOT / "tools/audit_phase4b.py")

    def fake_run_git(*args: str) -> subprocess.CompletedProcess[str]:
        if args[:2] == ("log", "--format=%H"):
            assert "--" in args
            assert "tools/audit_phase4b.py" in args
            return subprocess.CompletedProcess(["git", *args], 0, stdout="phasecommit\n", stderr="")
        if args[:4] == ("diff-tree", "--no-commit-id", "--name-only", "-r"):
            return subprocess.CompletedProcess(
                ["git", *args],
                0,
                stdout="pc/src/rplidar_c1_tools/motion_control.py\nfirmware/openrf1/app/unexpected.c\n",
                stderr="",
            )
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr(audit_module, "_run_git", fake_run_git)
    lines: list[str] = []
    failures: list[str] = []

    audit_module._check_software_only_diff(lines, failures)

    assert "firmware_files_changed: True" in lines
    assert failures == [
        "software-only phase-scoped commit changed firmware: firmware/openrf1/app/unexpected.c"
    ]


def test_phase4b_firmware_diff_audit_ignores_later_unrelated_firmware_commits(monkeypatch):
    audit_module = _load_audit_module("audit_phase4b_unrelated", REPO_ROOT / "tools/audit_phase4b.py")

    def fake_run_git(*args: str) -> subprocess.CompletedProcess[str]:
        if args[:2] == ("log", "--format=%H"):
            assert "--" in args
            return subprocess.CompletedProcess(["git", *args], 0, stdout="", stderr="")
        raise AssertionError(f"unexpected git call: {args}")

    monkeypatch.setattr(audit_module, "_run_git", fake_run_git)
    lines: list[str] = []
    failures: list[str] = []

    audit_module._check_software_only_diff(lines, failures)

    assert "firmware_files_changed: False" in lines
    assert failures == []


def _load_audit_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
