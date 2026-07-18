from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from rplidar_c1_tools.stm32_sensor_protocol import iter_stm32_telemetry


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def test_mecanum_cli_success_and_overwrite_protection(tmp_path):
    output = tmp_path / "mecanum_odometry.jsonl"
    result = _run_cli(tmp_path, *_valid_args(output))
    assert result.returncode == 0, result.stderr
    assert str(output) in result.stdout
    assert output.read_bytes().decode("utf-8").endswith("\n")
    with output.open("r", encoding="utf-8") as stream:
        messages = list(iter_stm32_telemetry(stream))
    assert len(messages) == 12
    assert messages[-1].message_type == "odometry_pose"

    refused = _run_cli(tmp_path, *_valid_args(output))
    assert refused.returncode != 0
    assert "already exists" in refused.stderr

    overwritten = _run_cli(tmp_path, *_valid_args(output), "--overwrite")
    assert overwritten.returncode == 0, overwritten.stderr


def test_mecanum_cli_requires_explicit_geometry_resolution_and_signs(tmp_path):
    output = tmp_path / "missing_configuration.jsonl"
    result = _run_cli(
        tmp_path,
        "simulate-mecanum-odometry",
        "--scenario",
        "forward",
        "--steps",
        "1",
        "--interval-ms",
        "100",
        "--output",
        str(output),
    )
    assert result.returncode != 0
    assert "--wheel-radius-m" in result.stderr
    assert "--counts-per-wheel-revolution" in result.stderr
    assert not output.exists()


def test_mecanum_cli_invalid_inputs_have_visible_nonzero_failures(tmp_path):
    invalid_direction = _valid_args(tmp_path / "direction.jsonl")
    index = invalid_direction.index("--front-left-direction") + 1
    invalid_direction[index] = "0"
    result = _run_cli(tmp_path, *invalid_direction)
    assert result.returncode != 0
    assert "+1 or -1" in result.stderr

    invalid_geometry = _valid_args(tmp_path / "geometry.jsonl")
    index = invalid_geometry.index("--wheel-radius-m") + 1
    invalid_geometry[index] = "nan"
    result = _run_cli(tmp_path, *invalid_geometry)
    assert result.returncode != 0
    assert "wheel_radius_m must be finite" in result.stderr


def test_mecanum_cli_help_labels_wheel_side_counts_and_hardware_free_scope(tmp_path):
    result = _run_cli(tmp_path, "simulate-mecanum-odometry", "--help")
    assert result.returncode == 0
    assert "Wheel-side counts per full wheel revolution" in result.stdout
    assert "hardware-free Phase 4A telemetry" in result.stdout


def _valid_args(output: Path) -> list[str]:
    # These values are synthetic fixtures, not physical rover measurements.
    return [
        "simulate-mecanum-odometry",
        "--wheel-radius-m",
        "0.05",
        "--half-length-m",
        "0.18",
        "--half-width-m",
        "0.16",
        "--counts-per-wheel-revolution",
        "2048",
        "--front-left-direction",
        "1",
        "--front-right-direction",
        "1",
        "--rear-left-direction",
        "1",
        "--rear-right-direction",
        "1",
        "--scenario",
        "combined_curved_motion",
        "--steps",
        "3",
        "--interval-ms",
        "100",
        "--output",
        str(output),
    ]


def _run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "rplidar_c1_tools.cli", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
