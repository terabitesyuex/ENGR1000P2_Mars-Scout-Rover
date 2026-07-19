from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from rplidar_c1_tools.stm32_sensor_protocol import iter_stm32_telemetry


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def test_motion_control_cli_success_and_overwrite_protection(tmp_path):
    output = tmp_path / "motion_control.jsonl"
    result = _run_cli(tmp_path, *_valid_args(output))
    assert result.returncode == 0, result.stderr
    assert "Phase 4B synthetic motion-control telemetry" in result.stdout
    assert str(output) in result.stdout
    with output.open("r", encoding="utf-8") as stream:
        messages = list(iter_stm32_telemetry(stream))
    assert len(messages) == 12
    assert messages[-1].message_type == "motion_control_snapshot"

    refused = _run_cli(tmp_path, *_valid_args(output))
    assert refused.returncode != 0
    assert "already exists" in refused.stderr

    overwritten = _run_cli(tmp_path, *_valid_args(output), "--overwrite")
    assert overwritten.returncode == 0, overwritten.stderr


def test_motion_control_cli_invalid_argument_has_visible_nonzero_failure(tmp_path):
    args = _valid_args(tmp_path / "invalid.jsonl")
    args[args.index("--pid-output-min") + 1] = "1"
    result = _run_cli(tmp_path, *args)
    assert result.returncode != 0
    assert "output_min must be less than output_max" in result.stderr


def test_motion_control_cli_requires_all_explicit_parameters(tmp_path):
    result = _run_cli(
        tmp_path,
        "simulate-motion-control",
        "--scenario",
        "forward",
        "--steps",
        "1",
        "--interval-ms",
        "100",
        "--output",
        str(tmp_path / "missing.jsonl"),
    )
    assert result.returncode != 0
    assert "--wheel-radius-m" in result.stderr
    assert "--pid-kp" in result.stderr
    assert "--plant-time-constant-s" in result.stderr


def test_slow_wheel_cli_requires_explicit_mismatch_parameter(tmp_path):
    args = _valid_args(tmp_path / "slow.jsonl")
    args[args.index("--scenario") + 1] = "slow_front_left_wheel"
    result = _run_cli(tmp_path, *args)
    assert result.returncode != 0
    assert "requires --slow-front-left-time-constant-s" in result.stderr


def test_motion_control_cli_help_states_synthetic_hardware_free_scope(tmp_path):
    result = _run_cli(tmp_path, "simulate-motion-control", "--help")
    assert result.returncode == 0
    assert "hardware-free Phase 4B" in result.stdout
    assert "SYNTHETIC" in result.stdout
    assert "--command-timeout-ms" in result.stdout
    assert "--overwrite" in result.stdout


def _valid_args(output: Path) -> list[str]:
    # Explicit synthetic fixtures; none are claimed as rover constants or tuning.
    return [
        "simulate-motion-control",
        "--wheel-radius-m",
        "0.05",
        "--half-length-m",
        "0.18",
        "--half-width-m",
        "0.16",
        "--max-wheel-speed-rad-s",
        "20",
        "--wheel-acceleration-rad-s2",
        "10",
        "--pid-kp",
        "0.05",
        "--pid-ki",
        "0.02",
        "--pid-kd",
        "0",
        "--pid-output-min",
        "-1",
        "--pid-output-max",
        "1",
        "--pid-integral-min",
        "-2",
        "--pid-integral-max",
        "2",
        "--plant-gain-rad-s-per-effort",
        "20",
        "--plant-time-constant-s",
        "0.2",
        "--command-timeout-ms",
        "250",
        "--scenario",
        "combined_curved_motion",
        "--steps",
        "2",
        "--interval-ms",
        "100",
        "--output",
        str(output),
    ]


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "rplidar_c1_tools.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
