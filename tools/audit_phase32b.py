"""Audit Phase 3.2B software-only foundation evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


REQUIRED_FILES = (
    "docs/phase3_2b_full_hardware_foundation.md",
    "docs/openrf1_phase32b_protocol.md",
    "firmware/openrf1/full_hardware/board_config.h",
    "firmware/openrf1/full_hardware/memory_budget.h",
    "firmware/openrf1/full_hardware/scheduler.c",
    "firmware/openrf1/full_hardware/uart_ring_buffer.c",
    "firmware/openrf1/full_hardware/i2c_bus.c",
    "firmware/openrf1/full_hardware/bmp280.c",
    "firmware/openrf1/full_hardware/mpu6050.c",
    "firmware/openrf1/full_hardware/hcsr04.c",
    "firmware/openrf1/full_hardware/rplidar_c1_transport.c",
    "firmware/openrf1/full_hardware/esp32_link.c",
    "firmware/openrf1/full_hardware/main_full_hardware.c",
    "firmware/openrf1/keil/OpenRF1_BH1750.uvprojx",
    "firmware/openrf1/keil/OpenRF1_FullHardware.uvprojx",
    "pc/src/rplidar_c1_tools/openrf1_phase32b.py",
    "pc/src/rplidar_c1_tools/esp32_link_codec.py",
    "pc/tests/test_phase32b_foundation.py",
    "pc/tests/test_esp32_link_codec.py",
    "pc/tests/test_openrf1_phase32b_firmware_foundation.py",
)

GENERATED_PATTERNS = (
    "firmware/openrf1/keil/Objects/",
    "firmware/openrf1/keil/Objects_FullHardware/",
    "firmware/openrf1/keil/Listings/",
    "firmware/openrf1/keil/DebugConfig/",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--manual-output", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    lines = ["Phase 3.2B software foundation audit"]
    _check_required_files(repo_root, lines, failures)
    _check_keil_project(repo_root, lines, failures)
    _check_git_hygiene(repo_root, lines, failures)
    _check_build_evidence(repo_root, lines, failures)
    lines.append("hardware_access: none")
    lines.append("flash_attempted: no")
    lines.append("serial_port_opened: no")
    if failures:
        lines.append("audit_status: FAIL")
        lines.append("failures:")
        lines.extend(f"  - {item}" for item in failures)
    else:
        lines.append("audit_status: PASS")

    _write(args.audit_output, "\n".join(lines) + "\n")
    _write(args.manual_output, manual_status_text())
    print(args.audit_output)
    print(args.manual_output)
    return 1 if failures else 0


def _check_required_files(repo_root: Path, lines: list[str], failures: list[str]) -> None:
    missing = [relative for relative in REQUIRED_FILES if not (repo_root / relative).exists()]
    lines.append(f"required_files_present: {not missing}")
    if missing:
        failures.append("missing required files: " + ", ".join(missing))


def _check_keil_project(repo_root: Path, lines: list[str], failures: list[str]) -> None:
    project = repo_root / "firmware/openrf1/keil/OpenRF1_FullHardware.uvprojx"
    text = project.read_text(encoding="utf-8")
    checks = {
        "full_output_directory_isolated": ".\\Objects_FullHardware\\" in text,
        "full_output_name_isolated": "<OutputName>OpenRF1_FullHardware</OutputName>" in text,
        "full_includes_are_relative": "..\\full_hardware;..\\app" in text,
        "no_user_absolute_paths": "C:\\Users" not in text,
        "no_bh1750_output_reference": "OpenRF1_BH1750.hex" not in text,
    }
    for label, passed in checks.items():
        lines.append(f"{label}: {passed}")
        if not passed:
            failures.append(label)


def _check_git_hygiene(repo_root: Path, lines: list[str], failures: list[str]) -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        failures.append("git ls-files failed")
        lines.append("generated_artifacts_tracked: unknown")
        return
    tracked = result.stdout.splitlines()
    generated = [
        path
        for path in tracked
        if any(path.startswith(pattern) for pattern in GENERATED_PATTERNS)
        or path.endswith(".uvoptx")
        or ".uvguix." in path
        or ".dbgconf" in path
        or ".base@" in path
    ]
    lines.append(f"generated_artifacts_tracked: {bool(generated)}")
    if generated:
        failures.append("tracked generated artifacts: " + ", ".join(generated[:8]))


def _check_build_evidence(repo_root: Path, lines: list[str], failures: list[str]) -> None:
    baseline_hex = repo_root / "firmware/openrf1/keil/Objects/OpenRF1_BH1750.hex"
    full_hex = repo_root / "firmware/openrf1/keil/Objects_FullHardware/OpenRF1_FullHardware.hex"
    baseline_log = repo_root / "firmware/openrf1/keil/Objects/OpenRF1_BH1750.build_log.htm"
    full_log = repo_root / "firmware/openrf1/keil/Objects_FullHardware/OpenRF1_FullHardware.build_log.htm"
    build_checks = {
        "baseline_hex_present": baseline_hex.exists() and baseline_hex.stat().st_size > 0,
        "full_hardware_hex_present": full_hex.exists() and full_hex.stat().st_size > 0,
        "baseline_keil_zero_errors_warnings": _log_has_zero_errors_warnings(baseline_log),
        "full_keil_zero_errors_warnings": _log_has_zero_errors_warnings(full_log),
    }
    for label, passed in build_checks.items():
        lines.append(f"{label}: {passed}")
        if not passed:
            failures.append(label)


def _log_has_zero_errors_warnings(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "0 Error(s), 0 Warning(s)" in text


def manual_status_text() -> str:
    return "\n".join(
        [
            "Phase 3.2B manual hardware status",
            "software_foundation: SOFTWARE_VERIFIED when tests and Keil builds pass",
            "phase3_2a_bh1750_flash: MANUAL_EVIDENCE_VERIFIED",
            "phase3_2a_ch340_usart1_telemetry: MANUAL_EVIDENCE_VERIFIED",
            "phase3_2a_bh1750_address_0x23: MANUAL_EVIDENCE_VERIFIED",
            "phase3_2a_500_ms_period: MANUAL_EVIDENCE_VERIFIED",
            "phase3_2a_physical_light_response: MANUAL_EVIDENCE_VERIFIED",
            "phase3_2a_absolute_lux_calibration: UNVERIFIED",
            "hardware_access_by_automation: none",
            "phase3_2b_multisensor_firmware_flash: MANUAL_ACTION_REQUIRED",
            "phase3_2b_physical_wiring: UNVERIFIED",
            "phase3_2b_power_integrity: UNVERIFIED",
            "phase3_2b_voltage_levels: UNVERIFIED",
            "USART2_RPLIDAR_operation: UNVERIFIED",
            "USART3_ESP32_operation: UNVERIFIED",
            "BMP280_MPU6050_I2C_ACKs: UNVERIFIED",
            "sensor_polarity: UNVERIFIED",
            "HC_SR04_echo_voh_and_timing: UNVERIFIED",
            "Hall_output_voltage: UNVERIFIED",
            "real_full_system_sensor_data: UNVERIFIED",
        ]
    ) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
