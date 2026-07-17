"""Audit Phase 3.2C BMP280 bring-up repository evidence."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess


REQUIRED_FILES = (
    "docs/openrf1_bmp280_bringup.md",
    "firmware/openrf1/bmp280_bringup/board_config.h",
    "firmware/openrf1/bmp280_bringup/main_bmp280_bringup.c",
    "firmware/openrf1/bmp280_bringup/platform_bmp280_bringup.c",
    "firmware/openrf1/bmp280_bringup/telemetry_bmp280_bringup.c",
    "firmware/openrf1/full_hardware/bmp280.c",
    "firmware/openrf1/full_hardware/bmp280.h",
    "firmware/openrf1/keil/OpenRF1_BMP280_Bringup.uvprojx",
    "firmware/openrf1/keil/RTE/_OpenRF1_BMP280_Bringup/RTE_Components.h",
    "pc/src/rplidar_c1_tools/openrf1_bmp280_bringup.py",
    "pc/tests/test_openrf1_bmp280_bringup.py",
    "tools/audit_phase32c.py",
)

GENERATED_PATTERNS = (
    "firmware/openrf1/keil/Objects/",
    "firmware/openrf1/keil/Objects_FullHardware/",
    "firmware/openrf1/keil/Objects_BMP280_Bringup/",
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
    lines = ["Phase 3.2C BMP280 bring-up audit"]
    _check_required_files(repo_root, lines, failures)
    _check_keil_project(repo_root, lines, failures)
    _check_git_hygiene(repo_root, lines, failures)
    _check_build_evidence(repo_root, lines, failures)
    lines.append("hardware_access_by_automation: none")
    lines.append("flash_attempted_by_automation: no")
    lines.append("serial_port_opened_by_automation: no")
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
    project = repo_root / "firmware/openrf1/keil/OpenRF1_BMP280_Bringup.uvprojx"
    text = project.read_text(encoding="utf-8")
    checks = {
        "bmp280_target_name": "<TargetName>OpenRF1_BMP280_Bringup</TargetName>" in text,
        "bmp280_output_directory_isolated": ".\\Objects_BMP280_Bringup\\" in text,
        "bmp280_output_name_isolated": "<OutputName>OpenRF1_BMP280_Bringup</OutputName>" in text,
        "bmp280_includes_are_relative": "..\\bmp280_bringup;..\\full_hardware;..\\app" in text,
        "no_user_absolute_paths": "C:\\Users" not in text,
        "no_bh1750_or_full_output_reference": "OpenRF1_BH1750.hex" not in text
        and "OpenRF1_FullHardware.hex" not in text,
        "no_unverified_usart_targets": "USART2" not in text and "USART3" not in text,
        "no_other_sensor_sources": all(
            forbidden not in text
            for forbidden in (
                "bh1750.c",
                "mpu6050.c",
                "hcsr04.c",
                "ground_sensors.c",
                "hall_sensor.c",
                "rplidar_c1_transport.c",
                "esp32_link.c",
                "main_full_hardware.c",
            )
        ),
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
        or (path.startswith("firmware/openrf1/keil/") and path.endswith(".lst"))
        or path.endswith(".uvoptx")
        or ".uvguix." in path
        or ".dbgconf" in path
        or ".base@" in path
    ]
    lines.append(f"generated_artifacts_tracked: {bool(generated)}")
    if generated:
        failures.append("tracked generated artifacts: " + ", ".join(generated[:8]))


def _check_build_evidence(repo_root: Path, lines: list[str], failures: list[str]) -> None:
    build_checks = {
        "bh1750_hex_present": repo_root / "firmware/openrf1/keil/Objects/OpenRF1_BH1750.hex",
        "full_hardware_hex_present": repo_root / "firmware/openrf1/keil/Objects_FullHardware/OpenRF1_FullHardware.hex",
        "bmp280_bringup_hex_present": repo_root / "firmware/openrf1/keil/Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.hex",
    }
    for label, path in build_checks.items():
        passed = path.exists() and path.stat().st_size > 0
        lines.append(f"{label}: {passed}")
        if not passed:
            failures.append(label)

    logs = {
        "bh1750_keil_zero_errors_warnings": repo_root / "firmware/openrf1/keil/Objects/OpenRF1_BH1750.build_log.htm",
        "full_hardware_keil_zero_errors_warnings": repo_root
        / "firmware/openrf1/keil/Objects_FullHardware/OpenRF1_FullHardware.build_log.htm",
        "bmp280_bringup_keil_zero_errors_warnings": repo_root
        / "firmware/openrf1/keil/Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.build_log.htm",
    }
    for label, path in logs.items():
        passed = _log_has_zero_errors_warnings(path)
        lines.append(f"{label}: {passed}")
        if not passed:
            failures.append(label)

    bmp_hex = build_checks["bmp280_bringup_hex_present"]
    if bmp_hex.exists() and bmp_hex.stat().st_size > 0:
        digest = hashlib.sha256(bmp_hex.read_bytes()).hexdigest().upper()
        lines.append(f"bmp280_bringup_hex_sha256: {digest}")

    direct_hex = repo_root / "firmware/openrf1/keil/Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.manual.hex"
    direct_present = direct_hex.exists() and direct_hex.stat().st_size > 0
    lines.append(f"bmp280_direct_armclang_hex_present: {direct_present}")
    if direct_present:
        digest = hashlib.sha256(direct_hex.read_bytes()).hexdigest().upper()
        lines.append(f"bmp280_direct_armclang_hex_sha256: {digest}")


def _log_has_zero_errors_warnings(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "0 Error(s), 0 Warning(s)" in text


def manual_status_text() -> str:
    return "\n".join(
        [
            "Phase 3.2C BMP280 manual hardware status",
            "software_foundation: SOFTWARE_VERIFIED only when tests, Keil builds, and verifier pass",
            "board_identity: CONFIRMED by Phase 3.2A OpenRF1 evidence",
            "mcu_identity: CONFIRMED by Phase 3.2A OpenRF1 evidence",
            "bmp280_module_count: CONFIRMED x1 inventory",
            "bmp280_vcc_3v3_rule: CONFIRMED_MODULE_EVIDENCE",
            "bmp280_expected_address_0x76: PLANNED from SDO grounded; real ACK remains UNVERIFIED",
            "bmp280_expected_chip_id_0x58: PLANNED manufacturer register value; physical read remains UNVERIFIED",
            "bmp280_firmware_flash: MANUAL_ACTION_REQUIRED",
            "bmp280_i2c_ack: MANUAL_ACTION_REQUIRED",
            "bmp280_chip_id_read: MANUAL_ACTION_REQUIRED",
            "bmp280_live_temperature_pressure: MANUAL_ACTION_REQUIRED",
            "hardware_access_by_automation: none",
        ]
    ) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
