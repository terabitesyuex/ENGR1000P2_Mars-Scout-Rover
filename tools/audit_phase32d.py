"""Audit Phase 3.2D MPU6050 bring-up repository evidence."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]

PHASE32A_EVIDENCE = (
    "evidence/phase3.2a/bh1750_physical_ba2024b_20260716_234217.jsonl",
    "6B9A2AE724C6473D6D8F18533CDC7B7081BCC782709862E914CE6B20B1690317",
)
PHASE32C_EVIDENCE = (
    "evidence/phase3.2c/bmp280_physical_adef636_20260718_002346.jsonl",
    "1BB0C5BE149DC7C49A3C63432D1CAE4AACAE3D5A80265FE879CA06D1E1A74805",
)

REQUIRED_FILES = (
    "docs/openrf1_mpu6050_bringup.md",
    "firmware/openrf1/mpu6050_bringup/board_config.h",
    "firmware/openrf1/mpu6050_bringup/main_mpu6050_bringup.c",
    "firmware/openrf1/mpu6050_bringup/platform_mpu6050_bringup.c",
    "firmware/openrf1/mpu6050_bringup/platform_mpu6050_bringup.h",
    "firmware/openrf1/mpu6050_bringup/telemetry_mpu6050_bringup.c",
    "firmware/openrf1/mpu6050_bringup/telemetry_mpu6050_bringup.h",
    "firmware/openrf1/full_hardware/mpu6050.c",
    "firmware/openrf1/full_hardware/mpu6050.h",
    "firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx",
    "firmware/openrf1/keil/RTE/_OpenRF1_MPU6050_Bringup/RTE_Components.h",
    "pc/src/rplidar_c1_tools/openrf1_mpu6050_bringup.py",
    "pc/tests/test_openrf1_mpu6050_bringup.py",
    "data/test_vectors/phase3.2d/mpu6050_startup_grace_session.jsonl",
    "data/test_vectors/phase3.2d/mpu6050_error_session.jsonl",
    "evidence/phase3.2d/mpu6050_manual_evidence.md",
    "tools/audit_phase32d.py",
)

GENERATED_PATTERNS = (
    "firmware/openrf1/keil/Objects/",
    "firmware/openrf1/keil/Objects_FullHardware/",
    "firmware/openrf1/keil/Objects_BMP280_Bringup/",
    "firmware/openrf1/keil/Objects_MPU6050_Bringup/",
    "firmware/openrf1/keil/Listings/",
    "firmware/openrf1/keil/DebugConfig/",
)

WINDOWS_USER_PATH_RE = re.compile(r"[A-Za-z]:\\(?:Users|Documents and Settings)\\")
DESKTOP_PATH_RE = re.compile(r"(?:[A-Za-z]:\\|\\\\)[^\r\n]*\\" + "Desktop" + r"\\")
COM_PORT_RE = re.compile(r"\bCOM[0-9]{1,3}\b")

OUT_OF_SCOPE_MANUAL_EVIDENCE_SNIPPETS = (
    "Reported final HEX name",
    "Reported final HEX size",
    "Reported final HEX SHA-256",
    "Reported Keil build result",
    "Formal continuity-test frames",
    "Formal continuity-test wall time",
    "Formal timestamp span",
    "Median / maximum interval",
    "Sequence gaps greater than 1",
    "approximately 4.77 V",
    "approximately 4.78 V",
    "approximately 3.31 V",
    "Continuity checks found",
    "ticks = 24u",
    "ticks = 240u",
    "151 frames",
    "15000 ms",
    "X mean approximately",
    "Y mean approximately",
    "Z mean approximately",
    "std approximately",
)

MANUAL_EVIDENCE_BOUNDARY_FILES = (
    "README.md",
    "PROJECT_SPEC.md",
    "HARDWARE_LOCK.md",
    "docs/openrf1_mpu6050_bringup.md",
    "docs/stm32_sensor_bringup.md",
    "docs/stm32_sensor_protocol.md",
    "evidence/phase3.2d/mpu6050_manual_evidence.md",
    "tools/verification/phase_manifest.json",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--manual-output", type=Path, required=True)
    args = parser.parse_args()

    failures: list[str] = []
    lines = ["Phase 3.2D MPU6050 bring-up audit"]
    _check_required_files(lines, failures)
    _check_keil_project(lines, failures)
    _check_source_boundaries(lines, failures)
    _check_git_hygiene(lines, failures)
    _check_previous_evidence_hashes(lines, failures)
    _check_phase32d_manual_evidence(lines, failures)
    _check_private_information(lines, failures)
    _check_build_evidence(lines)
    lines.append("software_status: SOFTWARE_READY")
    lines.append("isolated_manual_evidence_status: MANUAL_EVIDENCE_VERIFIED")
    lines.append("full_hardware_status: UNVERIFIED")
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


def _check_required_files(lines: list[str], failures: list[str]) -> None:
    missing = [relative for relative in REQUIRED_FILES if not (REPO_ROOT / relative).exists()]
    lines.append(f"required_files_present: {not missing}")
    if missing:
        failures.append("missing required files: " + ", ".join(missing))


def _check_keil_project(lines: list[str], failures: list[str]) -> None:
    project = REPO_ROOT / "firmware/openrf1/keil/OpenRF1_MPU6050_Bringup.uvprojx"
    text = project.read_text(encoding="utf-8")
    checks = {
        "mpu6050_target_name": "<TargetName>OpenRF1_MPU6050_Bringup</TargetName>" in text,
        "mpu6050_output_directory_isolated": ".\\Objects_MPU6050_Bringup\\" in text,
        "mpu6050_output_name_isolated": "<OutputName>OpenRF1_MPU6050_Bringup</OutputName>" in text,
        "mpu6050_includes_are_relative": "..\\mpu6050_bringup;..\\full_hardware;..\\app" in text,
        "no_user_absolute_paths": "C:\\Users" not in text,
        "no_other_target_hex_reference": all(
            item not in text
            for item in (
                "OpenRF1_BH1750.hex",
                "OpenRF1_BMP280_Bringup.hex",
                "OpenRF1_FullHardware.hex",
            )
        ),
        "no_unverified_usart_targets": "USART2" not in text and "USART3" not in text,
        "only_required_sensor_source": all(
            forbidden not in text
            for forbidden in (
                "bh1750.c",
                "bmp280.c",
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


def _check_source_boundaries(lines: list[str], failures: list[str]) -> None:
    bringup_root = REPO_ROOT / "firmware/openrf1/mpu6050_bringup"
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in bringup_root.glob("*.[ch]"))
    required_snippets = (
        "OPENRF1_MPU6050_ADDRESS_7BIT ((uint8_t)0x68u)",
        "OPENRF1_MPU6050_SENSOR_ID \"mpu6050_1\"",
        "OPENRF1_MPU6050_SAMPLE_PERIOD_MS ((uint32_t)100u)",
        "MPU6050_BRINGUP_STAGE_READ_WHO_AM_I",
        "mpu6050_read_who_am_i",
        "mpu6050_write_register_readback",
        "mpu6050_read_raw_sample",
    )
    missing_snippets = [snippet for snippet in required_snippets if snippet not in source_text]
    lines.append(f"mpu6050_source_required_snippets_present: {not missing_snippets}")
    if missing_snippets:
        failures.append("missing MPU6050 source snippets: " + ", ".join(missing_snippets))

    forbidden_terms = (
        "BMP280",
        "BH1750",
        "HCSR04",
        "TCRT5000",
        "Hall",
        "RPLIDAR",
        "ESP32",
        "USART2",
        "USART3",
        "motor",
        "encoder",
        "servo",
    )
    forbidden_found = [term for term in forbidden_terms if term in source_text]
    lines.append(f"mpu6050_bringup_source_isolated: {not forbidden_found}")
    if forbidden_found:
        failures.append("forbidden cross-scope source terms: " + ", ".join(forbidden_found))


def _check_git_hygiene(lines: list[str], failures: list[str]) -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
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


def _check_previous_evidence_hashes(lines: list[str], failures: list[str]) -> None:
    for relative, expected in (PHASE32A_EVIDENCE, PHASE32C_EVIDENCE):
        path = REPO_ROOT / relative
        if not path.exists():
            lines.append(f"{relative}: missing")
            failures.append(f"missing previous evidence: {relative}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        lines.append(f"{relative}: sha256={digest}")
        if digest != expected:
            failures.append(f"previous evidence hash mismatch: {relative}")


def _check_phase32d_manual_evidence(lines: list[str], failures: list[str]) -> None:
    evidence_root = REPO_ROOT / "evidence/phase3.2d"
    allowed = {REPO_ROOT / "evidence/phase3.2d/mpu6050_manual_evidence.md"}
    files = set(path for path in evidence_root.rglob("*") if path.is_file()) if evidence_root.exists() else set()
    unexpected = sorted(path.relative_to(REPO_ROOT).as_posix() for path in files - allowed)
    evidence_path = REPO_ROOT / "evidence/phase3.2d/mpu6050_manual_evidence.md"
    lines.append(f"phase3_2d_manual_evidence_present: {evidence_path in files}")
    lines.append(f"phase3_2d_unexpected_evidence_files_present: {bool(unexpected)}")
    if evidence_path not in files:
        failures.append("missing Phase 3.2D sanitized manual evidence file")
        return
    if unexpected:
        failures.append("unexpected Phase 3.2D evidence files: " + ", ".join(unexpected))

    text = evidence_path.read_text(encoding="utf-8")
    required_snippets = (
        "MANUAL_EVIDENCE_VERIFIED",
        "reported the isolated GY-521/MPU6050 wiring",
        "I2C ACK at address `0x68`",
        "WHO_AM_I register result `0x68`",
        "Isolated configuration readback",
        "Live IMU JSON telemetry",
        "Startup dynamic gyro-bias calibration semantics",
        "`gyro_raw` preserves raw register data",
        "`gyro_dps` subtracts the",
        "approximately 10 Hz telemetry during a 15-second isolated test",
        "with no sequence loss",
        "isolated sensor-axis response",
        "Exact connector orientation",
        "Software-I2C delay-loop tuning",
        "Exact gyro bias or standard-deviation values",
        "Shared-I2C concurrency",
        "Complete multisensor firmware operation",
        "did not build or flash firmware",
        "C did not perform or repeat",
    )
    missing = [snippet for snippet in required_snippets if snippet not in text]
    lines.append(f"phase3_2d_manual_evidence_required_snippets_present: {not missing}")
    if missing:
        failures.append("missing manual evidence snippets: " + ", ".join(missing))

    out_of_scope = [
        f"{relative}: {snippet}"
        for relative in MANUAL_EVIDENCE_BOUNDARY_FILES
        for snippet in OUT_OF_SCOPE_MANUAL_EVIDENCE_SNIPPETS
        if snippet in (REPO_ROOT / relative).read_text(encoding="utf-8")
    ]
    lines.append(f"phase3_2d_out_of_scope_evidence_present: {bool(out_of_scope)}")
    if out_of_scope:
        failures.append(
            "out-of-scope manual evidence snippets present: " + ", ".join(out_of_scope)
        )


def _check_private_information(lines: list[str], failures: list[str]) -> None:
    paths = [
        REPO_ROOT / relative
        for relative in REQUIRED_FILES
        if (REPO_ROOT / relative).is_file()
    ]
    findings: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if WINDOWS_USER_PATH_RE.search(text):
            findings.append(f"{path.relative_to(REPO_ROOT)} contains a Windows user path")
        if DESKTOP_PATH_RE.search(text):
            findings.append(f"{path.relative_to(REPO_ROOT)} contains a Desktop path")
        if COM_PORT_RE.search(text):
            findings.append(f"{path.relative_to(REPO_ROOT)} contains a concrete COM port")
    lines.append(f"private_local_information_present: {bool(findings)}")
    if findings:
        failures.append("private local information present: " + "; ".join(findings[:4]))


def _check_build_evidence(lines: list[str]) -> None:
    hex_path = REPO_ROOT / "firmware/openrf1/keil/Objects_MPU6050_Bringup/OpenRF1_MPU6050_Bringup.hex"
    log_path = REPO_ROOT / "firmware/openrf1/keil/Objects_MPU6050_Bringup/OpenRF1_MPU6050_Bringup.build_log.htm"
    hex_present = hex_path.exists() and hex_path.stat().st_size > 0
    lines.append(f"mpu6050_bringup_local_hex_present: {hex_present}")
    if hex_present:
        lines.append(f"mpu6050_bringup_hex_sha256: {hashlib.sha256(hex_path.read_bytes()).hexdigest().upper()}")
    lines.append(f"mpu6050_bringup_local_keil_zero_errors_warnings: {_log_has_zero_errors_warnings(log_path)}")


def _log_has_zero_errors_warnings(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "0 Error(s), 0 Warning(s)" in text


def manual_status_text() -> str:
    return "\n".join(
        [
            "Phase 3.2D MPU6050 manual hardware status",
            "software_foundation: SOFTWARE_READY by committed tests and verifier when this audit passes",
            "board_identity: CONFIRMED by Phase 3.2A OpenRF1 evidence",
            "mcu_identity: CONFIRMED by Phase 3.2A OpenRF1 evidence",
            "mpu6050_module_count: CONFIRMED x1 inventory",
            "mpu6050_module_vcc_5v_rule: CONFIRMED_MODULE_EVIDENCE for GY-521 style module",
            "mpu6050_isolated_wiring: MANUAL_EVIDENCE_VERIFIED for VCC/GND/SCL/SDA/AD0",
            "mpu6050_address_0x68: MANUAL_EVIDENCE_VERIFIED in isolated bring-up",
            "mpu6050_who_am_i_0x68: MANUAL_EVIDENCE_VERIFIED in isolated bring-up",
            "mpu6050_i2c_ack: MANUAL_EVIDENCE_VERIFIED in isolated bring-up",
            "mpu6050_configuration_readback: MANUAL_EVIDENCE_VERIFIED in isolated bring-up",
            "mpu6050_live_imu_temperature_telemetry: MANUAL_EVIDENCE_VERIFIED in isolated bring-up",
            "mpu6050_startup_gyro_bias_semantics: MANUAL_EVIDENCE_VERIFIED in isolated bring-up",
            "mpu6050_axis_orientation: UNVERIFIED",
            "mpu6050_accelerometer_offset: UNVERIFIED",
            "mpu6050_yaw_drift: UNVERIFIED",
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
