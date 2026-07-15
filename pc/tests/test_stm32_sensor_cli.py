from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "pc" / "src"


def test_stm32_cli_help_generation_inspection_and_recording(tmp_path):
    telemetry = tmp_path / "stm32_telemetry.jsonl"
    inspection = tmp_path / "telemetry_inspection.txt"
    recording = tmp_path / "multisensor_recording.jsonl"
    recording_inspection = tmp_path / "recording_inspection.txt"

    help_result = _run_cli(tmp_path, "simulate-stm32-sensors", "--help")
    assert help_result.returncode == 0
    assert "STM32 sensor telemetry" in help_result.stdout

    generate_result = _run_cli(
        tmp_path,
        "simulate-stm32-sensors",
        "--cycles",
        "2",
        "--scenario",
        "nominal",
        "--output",
        str(telemetry),
    )
    assert generate_result.returncode == 0, generate_result.stderr
    assert telemetry.stat().st_size > 0

    overwrite_result = _run_cli(
        tmp_path,
        "simulate-stm32-sensors",
        "--cycles",
        "1",
        "--output",
        str(telemetry),
    )
    assert overwrite_result.returncode != 0
    assert "already exists" in overwrite_result.stderr

    inspect_result = _run_cli(
        tmp_path,
        "inspect-stm32-telemetry",
        "--input",
        str(telemetry),
        "--output",
        str(inspection),
    )
    assert inspect_result.returncode == 0, inspect_result.stderr
    assert "messages: 16" in inspection.read_text(encoding="utf-8")

    record_result = _run_cli(
        tmp_path,
        "record-stm32-telemetry",
        "--input",
        str(telemetry),
        "--output",
        str(recording),
    )
    assert record_result.returncode == 0, record_result.stderr
    assert recording.stat().st_size > 0

    recording_inspect = _run_cli(
        tmp_path,
        "inspect-recording",
        str(recording),
        "--output",
        str(recording_inspection),
    )
    assert recording_inspect.returncode == 0, recording_inspect.stderr
    assert "ultrasonic: 6" in recording_inspection.read_text(encoding="utf-8")


def test_stm32_cli_invalid_input_exits_nonzero(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("not-json\n", encoding="utf-8")
    result = _run_cli(tmp_path, "inspect-stm32-telemetry", "--input", str(bad))

    assert result.returncode != 0
    assert "invalid JSON" in result.stderr


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

