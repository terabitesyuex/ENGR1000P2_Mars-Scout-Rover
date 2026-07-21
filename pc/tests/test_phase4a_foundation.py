from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_phase4a_current_plan_documents_software_and_physical_boundaries():
    required = {
        "AGENTS.md": [
            "Phase 4A software work is complete",
            "counts per revolution",
            "physical odometry accuracy remain UNVERIFIED",
        ],
        "README.md": [
            "Phase 4A Mecanum Kinematics and Odometry",
            "simulate-mecanum-odometry",
            "No physical geometry, encoder resolution, gear ratio, counter width, or sign is defaulted",
        ],
        "docs/phase4a_mecanum_kinematics_odometry_foundation.md": [
            "SOFTWARE_VERIFIED software-only foundation",
            "Phase 4 is not physically complete",
            "counts_per_wheel_revolution",
            "se2_constant_twist_exponential",
            "synthetic test values, not rover measurements",
            "UNVERIFIED physical facts",
        ],
        "docs/stm32_sensor_protocol.md": [
            "wheel_encoder_delta",
            "software_derived",
            "odometry_pose",
        ],
        "docs/recording_format.md": [
            "wheel_angular_velocity",
            "body_twist",
            "physical odometry accuracy evidence",
        ],
        "docs/test_plan.md": [
            "phase4a",
            "Phase 4A automated tests do not open COM ports",
        ],
    }
    missing: list[str] = []
    for relative, snippets in required.items():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{relative}: {snippet}")
    assert missing == []


def test_phase4a_manifest_is_hardware_free_and_runs_all_software_layers():
    manifest = json.loads(
        (REPO_ROOT / "tools/verification/phase_manifest.json").read_text(encoding="utf-8")
    )
    assert "phase4a" in manifest["supported_phases"]
    phase = manifest["phases"]["phase4a"]
    assert set(phase["targeted"]) == {
        "pc/tests/test_mecanum_kinematics_odometry.py",
        "pc/tests/test_mecanum_odometry_simulator.py",
        "pc/tests/test_mecanum_odometry_cli.py",
        "pc/tests/test_phase4a_foundation.py",
    }
    assert phase["full"] == ["pc/tests"]
    command_text = json.dumps(phase["python_commands"]).lower()
    for forbidden in ("--port", "serial", "usb", "keil", "flymcu", "flash"):
        assert forbidden not in command_text
    assert "simulate-mecanum-odometry" in command_text
    assert "audit_phase4a.py" in command_text

    verifier = (REPO_ROOT / "tools/verify_phase.ps1").read_text(encoding="utf-8")
    assert 'Join-Path $RepoRoot "pc\\src"' in verifier
    assert "$env:PYTHONPATH = $sourceRoot" in verifier


def test_phase4a_audit_reports_privacy_artifact_and_hardware_boundaries(tmp_path):
    audit_output = tmp_path / "software_audit.txt"
    status_output = tmp_path / "hardware_status.txt"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools/audit_phase4a.py"),
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
    assert "physical_odometry_accuracy: UNVERIFIED" in status
    assert "manual_action_performed_by_verifier: none" in status


def test_phase4a_firmware_diff_audit_is_scoped_and_still_rejects_phase_firmware_changes(monkeypatch):
    audit_module = _load_audit_module("audit_phase4a_scoped", REPO_ROOT / "tools/audit_phase4a.py")

    def fake_run_git(*args: str) -> subprocess.CompletedProcess[str]:
        if args[:2] == ("log", "--format=%H"):
            assert "--" in args
            assert "tools/audit_phase4a.py" in args
            return subprocess.CompletedProcess(["git", *args], 0, stdout="phasecommit\n", stderr="")
        if args[:4] == ("diff-tree", "--no-commit-id", "--name-only", "-r"):
            return subprocess.CompletedProcess(
                ["git", *args],
                0,
                stdout="docs/phase4a_mecanum_kinematics_odometry_foundation.md\nfirmware/openrf1/app/unexpected.c\n",
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


def test_phase4a_firmware_diff_audit_ignores_later_unrelated_firmware_commits(monkeypatch):
    audit_module = _load_audit_module("audit_phase4a_unrelated", REPO_ROOT / "tools/audit_phase4a.py")

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
