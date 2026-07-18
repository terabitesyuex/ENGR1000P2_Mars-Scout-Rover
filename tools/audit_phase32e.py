"""Audit Phase 3.2E HC-SR04 bring-up repository evidence."""

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
    "docs/openrf1_hcsr04_bringup.md",
    "firmware/openrf1/hcsr04_bringup/board_config.h",
    "firmware/openrf1/hcsr04_bringup/hcsr04.c",
    "firmware/openrf1/hcsr04_bringup/hcsr04.h",
    "firmware/openrf1/hcsr04_bringup/main_hcsr04_bringup.c",
    "firmware/openrf1/hcsr04_bringup/platform_hcsr04_bringup.c",
    "firmware/openrf1/hcsr04_bringup/platform_hcsr04_bringup.h",
    "firmware/openrf1/hcsr04_bringup/telemetry_hcsr04_bringup.c",
    "firmware/openrf1/hcsr04_bringup/telemetry_hcsr04_bringup.h",
    "firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx",
    "firmware/openrf1/keil/RTE/_OpenRF1_HCSR04_Bringup/RTE_Components.h",
    "pc/src/rplidar_c1_tools/openrf1_hcsr04_bringup.py",
    "pc/tests/test_openrf1_hcsr04_bringup.py",
    "tools/audit_phase32e.py",
)

GENERATED_PATTERNS = (
    "firmware/openrf1/keil/Objects/",
    "firmware/openrf1/keil/Objects_FullHardware/",
    "firmware/openrf1/keil/Objects_BMP280_Bringup/",
    "firmware/openrf1/keil/Objects_MPU6050_Bringup/",
    "firmware/openrf1/keil/Objects_HCSR04_Bringup/",
    "firmware/openrf1/keil/Listings/",
    "firmware/openrf1/keil/DebugConfig/",
)

WINDOWS_USER_PATH_RE = re.compile(r"[A-Za-z]:\\(?:Users|Documents and Settings)\\")
DESKTOP_PATH_RE = re.compile(r"(?:[A-Za-z]:\\|\\\\)[^\r\n]*\\" + "Desk" + "top" + r"\\")
COM_PORT_RE = re.compile(r"\bCOM[0-9]{1,3}\b")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--manual-output", type=Path, required=True)
    args = parser.parse_args()

    failures: list[str] = []
    lines = ["Phase 3.2E HC-SR04 bring-up audit"]
    _check_required_files(lines, failures)
    _check_hardware_lock(lines, failures)
    _check_source_contract(lines, failures)
    _check_keil_project(lines, failures)
    _check_documentation(lines, failures)
    _check_git_hygiene(lines, failures)
    _check_previous_evidence_hashes(lines, failures)
    _check_no_phase32e_physical_evidence(lines, failures)
    _check_private_information(lines, failures)
    _check_build_evidence(lines)
    lines.append("software_status: SOFTWARE_READY")
    lines.append("physical_status: PHYSICAL_VERIFICATION_REQUIRED")
    lines.append("physical_evidence_verified: false")
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


def _check_hardware_lock(lines: list[str], failures: list[str]) -> None:
    source_text = "\n".join(
        (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        for relative in ("HARDWARE_LOCK.md", "PROJECT_SPEC.md", "docs/openrf1_hcsr04_bringup.md")
        if (REPO_ROOT / relative).exists()
    )
    required = (
        "AUTHORITATIVE_VENDOR_DOCUMENTED",
        "OpenRF1 vendor control-board package",
        "ultrasonic sensor example",
        "OpenRF1 schematic revision dated 2024-07-01",
        "CN6",
        "B4B-PH-K-S(LF)(SN)",
        "pin 1: VCC_5V",
        "pin 2: GND",
        "pin 3: PA5_TRIG",
        "pin 4: PA4_ECHO",
        "TRIG: PA5",
        "ECHO: PA4",
        "TIM6",
        "10 kOhm",
        "15 kOhm",
        "Do not connect HC-SR04 ECHO directly to CN6 pin 4.",
        "actual board connector orientation: UNVERIFIED",
        "physical trigger pulse: UNVERIFIED",
        "real distance data: UNVERIFIED",
    )
    missing = [snippet for snippet in required if snippet not in source_text]
    lines.append(f"hardware_lock_required_snippets_present: {not missing}")
    if missing:
        failures.append("missing hardware lock snippets: " + ", ".join(missing))
    if "PA4 is 5-V tolerant" in source_text:
        failures.append("PA4 must not be described as 5-V tolerant")


def _check_source_contract(lines: list[str], failures: list[str]) -> None:
    bringup_root = REPO_ROOT / "firmware/openrf1/hcsr04_bringup"
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in bringup_root.glob("*.[ch]"))
    required = (
        "OPENRF1_HCSR04_TRIGGER_PIN_TEXT \"PA5\"",
        "OPENRF1_HCSR04_ECHO_PIN_TEXT \"PA4\"",
        "OPENRF1_HCSR04_TIMER_TEXT \"TIM6\"",
        "OPENRF1_HCSR04_TIMER_PRESCALER ((uint16_t)71u)",
        "OPENRF1_HCSR04_TIMER_PERIOD ((uint16_t)30000u)",
        "OPENRF1_HCSR04_TIMER_TICK_HZ ((uint32_t)1000000u)",
        "OPENRF1_HCSR04_TRIGGER_PULSE_US ((uint16_t)10u)",
        "OPENRF1_HCSR04_ECHO_TIMEOUT_US ((uint32_t)30000u)",
        "OPENRF1_HCSR04_MEASUREMENT_PERIOD_MS ((uint32_t)100u)",
        "OPENRF1_HCSR04_ECHO_SERIES_RESISTOR_OHM ((uint16_t)10000u)",
        "OPENRF1_HCSR04_ECHO_PULLDOWN_RESISTOR_OHM ((uint16_t)15000u)",
        "HCSR04_RESULT_ECHO_NOT_LOW_BEFORE_TRIGGER",
        "HCSR04_RESULT_ECHO_RISE_TIMEOUT",
        "HCSR04_RESULT_ECHO_FALL_TIMEOUT",
        "HCSR04_RESULT_TIMER_MEASUREMENT_FAILURE",
        "HCSR04_RESULT_PULSE_WIDTH_OUT_OF_BOUNDS",
        "hcsr04_elapsed_us",
        "(echo_pulse_us * 343u + 1000u) / 2000u",
        "OPENRF1_HCSR04_WAIT_POLL_LIMIT",
        "next_attempt_ms += OPENRF1_HCSR04_MEASUREMENT_PERIOD_MS",
        "\\\"distance_model\\\":\\\"%s\\\"",
        "\\\"error\\\":{\\\"code\\\":\\\"%s\\\"",
    )
    missing = [snippet for snippet in required if snippet not in source_text]
    lines.append(f"hcsr04_source_required_snippets_present: {not missing}")
    if missing:
        failures.append("missing HC-SR04 source snippets: " + ", ".join(missing))

    forbidden = (
        "BH1750",
        "BMP280",
        "MPU6050",
        "RPLIDAR",
        "ESP32",
        "USART2",
        "USART3",
        "I2C",
        "motor",
        "encoder",
        "servo",
    )
    found = [term for term in forbidden if term in source_text]
    lines.append(f"hcsr04_bringup_source_isolated: {not found}")
    if found:
        failures.append("forbidden cross-scope source terms: " + ", ".join(found))


def _check_keil_project(lines: list[str], failures: list[str]) -> None:
    project = REPO_ROOT / "firmware/openrf1/keil/OpenRF1_HCSR04_Bringup.uvprojx"
    rte = REPO_ROOT / "firmware/openrf1/keil/RTE/_OpenRF1_HCSR04_Bringup/RTE_Components.h"
    text = project.read_text(encoding="utf-8")
    rte_text = rte.read_text(encoding="utf-8")
    checks = {
        "hcsr04_target_name": "<TargetName>OpenRF1_HCSR04_Bringup</TargetName>" in text,
        "hcsr04_output_directory_isolated": ".\\Objects_HCSR04_Bringup\\" in text,
        "hcsr04_output_name_isolated": "<OutputName>OpenRF1_HCSR04_Bringup</OutputName>" in text,
        "hcsr04_includes_are_relative": "..\\hcsr04_bringup;..\\full_hardware;..\\app" in text,
        "tim_component_present": "Csub=\"TIM\"" in text and "RTE_DEVICE_STDPERIPH_TIM" in rte_text,
        "no_user_absolute_paths": "C:\\Users" not in text,
        "no_desktop_paths": ("Desk" + "top") not in text,
        "only_required_sensor_source": all(
            forbidden not in text
            for forbidden in (
                "bh1750.c",
                "bmp280.c",
                "mpu6050.c",
                "soft_i2c.c",
                "main_full_hardware.c",
                "rplidar_c1_transport.c",
                "esp32_link.c",
            )
        ),
    }
    for label, passed in checks.items():
        lines.append(f"{label}: {passed}")
        if not passed:
            failures.append(label)


def _check_documentation(lines: list[str], failures: list[str]) -> None:
    doc = REPO_ROOT / "docs/openrf1_hcsr04_bringup.md"
    if not doc.exists():
        failures.append("missing HC-SR04 bring-up documentation")
        return
    text = doc.read_text(encoding="utf-8")
    required = (
        "IMPLEMENTED / SOFTWARE_READY",
        "UNVERIFIED",
        "PHYSICAL_VERIFICATION_REQUIRED",
        "disconnect all power before changing wiring",
        "check printed module labels",
        "only HC-SR04 should be connected",
        "raw 5 V must not be applied to an unverified STM32 input",
        "measurements are nominal and uncalibrated",
        "soft materials and angled surfaces",
        "very close objects",
        "No physical verification has yet occurred.",
        "Future Physical Validation Checklist",
        "[ ] Confirm official Keil build success.",
        "[ ] Do not claim calibrated absolute accuracy",
    )
    text_lower = text.lower()
    missing = [snippet for snippet in required if snippet.lower() not in text_lower]
    lines.append(f"hcsr04_documentation_required_snippets_present: {not missing}")
    if missing:
        failures.append("missing HC-SR04 documentation snippets: " + ", ".join(missing))
    if "PHYSICAL_EVIDENCE_VERIFIED" in text:
        failures.append("Phase 3.2E documentation must not claim physical evidence verified")


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
        or path.endswith((".hex", ".axf", ".o", ".obj", ".map", ".dep", ".lnp", ".uvoptx"))
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


def _check_no_phase32e_physical_evidence(lines: list[str], failures: list[str]) -> None:
    evidence_root = REPO_ROOT / "evidence/phase3.2e"
    files = [path for path in evidence_root.rglob("*") if path.is_file()] if evidence_root.exists() else []
    lines.append(f"phase3_2e_physical_evidence_files_present: {bool(files)}")
    if files:
        failures.append("Phase 3.2E physical evidence files are not allowed in this software-only phase")


def _check_private_information(lines: list[str], failures: list[str]) -> None:
    paths = [
        REPO_ROOT / relative
        for relative in REQUIRED_FILES
        if (REPO_ROOT / relative).is_file()
    ]
    findings: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(REPO_ROOT)
        if WINDOWS_USER_PATH_RE.search(text):
            findings.append(f"{relative} contains a Windows user path")
        if DESKTOP_PATH_RE.search(text):
            findings.append(f"{relative} contains a local desktop path")
        if COM_PORT_RE.search(text):
            findings.append(f"{relative} contains a concrete COM port")
    lines.append(f"private_local_information_present: {bool(findings)}")
    if findings:
        failures.append("private local information present: " + "; ".join(findings[:4]))


def _check_build_evidence(lines: list[str]) -> None:
    hex_path = REPO_ROOT / "firmware/openrf1/keil/Objects_HCSR04_Bringup/OpenRF1_HCSR04_Bringup.hex"
    log_path = REPO_ROOT / "firmware/openrf1/keil/Objects_HCSR04_Bringup/OpenRF1_HCSR04_Bringup.build_log.htm"
    hex_present = hex_path.exists() and hex_path.stat().st_size > 0
    lines.append(f"hcsr04_bringup_local_hex_present: {hex_present}")
    if hex_present:
        lines.append(f"hcsr04_bringup_hex_sha256: {hashlib.sha256(hex_path.read_bytes()).hexdigest().upper()}")
    lines.append(f"hcsr04_bringup_local_keil_zero_errors_warnings: {_log_has_zero_errors_warnings(log_path)}")


def _log_has_zero_errors_warnings(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "0 Error(s), 0 Warning(s)" in text


def manual_status_text() -> str:
    return "\n".join(
        [
            "Phase 3.2E HC-SR04 manual hardware status",
            "software_foundation: SOFTWARE_READY by committed tests and verifier when this audit passes",
            "connector_and_pin_lock: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "cn6_pin_order: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "trig_pa5_mapping: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "echo_pa4_mapping: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "tim6_timer_resource: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "external_echo_divider_required: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "direct_echo_to_cn6_pin4: PROHIBITED",
            "actual_board_connector_orientation: UNVERIFIED",
            "actual_cable_orientation: UNVERIFIED",
            "installed_resistor_values: UNVERIFIED",
            "real_echo_voltage_before_division: UNVERIFIED",
            "real_echo_voltage_after_division: UNVERIFIED",
            "physical_trigger_pulse: UNVERIFIED",
            "physical_echo_pulse: UNVERIFIED",
            "real_distance_data: UNVERIFIED",
            "physical_timer_accuracy: UNVERIFIED",
            "physical_timeout_behavior: UNVERIFIED",
            "absolute_distance_accuracy: UNVERIFIED",
            "complete_full_hardware_operation: UNVERIFIED",
            "hardware_access_by_automation: none",
        ]
    ) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
