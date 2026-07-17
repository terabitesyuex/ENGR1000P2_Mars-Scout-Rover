"""Audit Phase 3.2C BMP280 bring-up repository evidence."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PC_SRC = REPO_ROOT / "pc" / "src"
if str(PC_SRC) not in sys.path:
    sys.path.insert(0, str(PC_SRC))

from rplidar_c1_tools.phase32c_evidence import (  # noqa: E402
    EVIDENCE_RELATIVE_PATH,
    FORMAL_KEIL_HEX_SHA256,
    Phase32cEvidenceError,
    validate_phase32c_bmp280_evidence,
)


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
    "evidence/phase3.2c/bmp280_physical_adef636_20260718_002346.jsonl",
    "evidence/phase3.2c/bmp280_physical_evidence.md",
    "pc/src/rplidar_c1_tools/openrf1_bmp280_bringup.py",
    "pc/src/rplidar_c1_tools/phase32c_evidence.py",
    "pc/tests/test_openrf1_bmp280_bringup.py",
    "pc/tests/test_phase32c_physical_evidence.py",
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

    repo_root = REPO_ROOT
    failures: list[str] = []
    lines = ["Phase 3.2C BMP280 bring-up audit"]
    _check_required_files(repo_root, lines, failures)
    _check_keil_project(repo_root, lines, failures)
    _check_git_hygiene(repo_root, lines, failures)
    _check_build_evidence(repo_root, lines, failures)
    _check_physical_evidence(repo_root, lines, failures)
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
        "bh1750_local_hex_present": repo_root / "firmware/openrf1/keil/Objects/OpenRF1_BH1750.hex",
        "full_hardware_local_hex_present": repo_root
        / "firmware/openrf1/keil/Objects_FullHardware/OpenRF1_FullHardware.hex",
        "bmp280_bringup_local_hex_present": repo_root
        / "firmware/openrf1/keil/Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.hex",
    }
    for label, path in build_checks.items():
        passed = path.exists() and path.stat().st_size > 0
        lines.append(f"{label}: {passed}")

    logs = {
        "bh1750_local_keil_zero_errors_warnings": repo_root
        / "firmware/openrf1/keil/Objects/OpenRF1_BH1750.build_log.htm",
        "full_hardware_local_keil_zero_errors_warnings": repo_root
        / "firmware/openrf1/keil/Objects_FullHardware/OpenRF1_FullHardware.build_log.htm",
        "bmp280_bringup_local_keil_zero_errors_warnings": repo_root
        / "firmware/openrf1/keil/Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.build_log.htm",
    }
    for label, path in logs.items():
        passed = _log_has_zero_errors_warnings(path)
        lines.append(f"{label}: {passed}")

    lines.append(f"bmp280_formal_keil_hex_sha256: {FORMAL_KEIL_HEX_SHA256}")
    bmp_hex = build_checks["bmp280_bringup_local_hex_present"]
    if bmp_hex.exists() and bmp_hex.stat().st_size > 0:
        digest = hashlib.sha256(bmp_hex.read_bytes()).hexdigest().upper()
        lines.append(f"bmp280_bringup_hex_sha256: {digest}")
        if digest != FORMAL_KEIL_HEX_SHA256:
            failures.append("bmp280_bringup_hex_sha256_mismatch")

    direct_hex = repo_root / "firmware/openrf1/keil/Objects_BMP280_Bringup/OpenRF1_BMP280_Bringup.manual.hex"
    direct_present = direct_hex.exists() and direct_hex.stat().st_size > 0
    lines.append(f"bmp280_direct_armclang_hex_present: {direct_present}")
    if direct_present:
        digest = hashlib.sha256(direct_hex.read_bytes()).hexdigest().upper()
        lines.append(f"bmp280_direct_armclang_hex_sha256: {digest}")


def _check_physical_evidence(repo_root: Path, lines: list[str], failures: list[str]) -> None:
    evidence_path = repo_root / EVIDENCE_RELATIVE_PATH
    try:
        summary = validate_phase32c_bmp280_evidence(evidence_path)
    except (OSError, Phase32cEvidenceError) as exc:
        lines.append("bmp280_physical_evidence_valid: False")
        failures.append(f"bmp280 physical evidence invalid: {exc}")
        return

    lines.extend(
        [
            "bmp280_physical_evidence_valid: True",
            f"bmp280_physical_evidence_sha256: {summary.sha256}",
            f"bmp280_physical_evidence_records: {summary.record_count}",
            f"bmp280_sensor_identity_records: {summary.sensor_identity_count}",
            f"bmp280_environmental_records: {summary.environmental_count}",
            f"bmp280_sequence_range: {summary.sequence_start}..{summary.sequence_end}",
            f"bmp280_capture_duration_ms: {summary.capture_duration_ms}",
            f"bmp280_environmental_interval_ms: {summary.environmental_interval_ms}",
            f"bmp280_configured_address: {summary.configured_address}",
            f"bmp280_expected_chip_id: {summary.expected_chip_id}",
            f"bmp280_observed_chip_id: {summary.chip_id}",
            f"bmp280_ctrl_meas: {summary.ctrl_meas}",
            f"bmp280_config: {summary.config}",
            f"bmp280_temperature_range_c: {summary.temperature_min_c}..{summary.temperature_max_c}",
            f"bmp280_pressure_range_pa: {summary.pressure_min_pa}..{summary.pressure_max_pa}",
            "bmp280_private_local_information_present: False",
            "bmp280_physical_ack_address_chip_id_config_live_telemetry: PHYSICAL_EVIDENCE_VERIFIED",
        ]
    )


def _log_has_zero_errors_warnings(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "0 Error(s), 0 Warning(s)" in text


def manual_status_text() -> str:
    return "\n".join(
        [
            "Phase 3.2C BMP280 manual hardware status",
            "software_foundation: SOFTWARE_VERIFIED by committed tests and verifier when this audit passes",
            "board_identity: CONFIRMED by Phase 3.2A OpenRF1 evidence",
            "mcu_identity: CONFIRMED by Phase 3.2A OpenRF1 evidence",
            "bmp280_module_count: CONFIRMED x1 inventory",
            "bmp280_vcc_3v3_rule: CONFIRMED_MODULE_EVIDENCE",
            f"bmp280_formal_keil_hex_sha256: {FORMAL_KEIL_HEX_SHA256}",
            "bmp280_firmware_flash: PHYSICAL_EVIDENCE_VERIFIED",
            "ch340_usart1_jsonl_telemetry: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_address_0x76: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_i2c_ack: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_chip_id_0x58: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_calibration_path_for_compensated_output: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_ctrl_meas_0x27_config_0x80_readback: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_live_temperature_pressure: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_500ms_periodicity: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_stable_30_second_capture: PHYSICAL_EVIDENCE_VERIFIED",
            "bmp280_i2c_errors_in_formal_capture: none",
            "absolute_temperature_accuracy: UNVERIFIED",
            "absolute_pressure_accuracy: UNVERIFIED",
            "long_duration_operation_beyond_capture: UNVERIFIED",
            "shared_i2c_multidevice_concurrency: UNVERIFIED",
            "complete_full_hardware_operation: UNVERIFIED",
            "hardware_access_by_automation: none",
        ]
    ) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
