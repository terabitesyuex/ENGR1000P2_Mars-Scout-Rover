"""Audit Phase 3.2F ground-sensor bring-up repository evidence."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pc/src"))

from rplidar_c1_tools.phase32f_evidence import (  # noqa: E402
    CAPTURE_SPECS,
    FORMAL_KEIL_HEX_SHA256,
    Phase32fEvidenceError,
    validate_all_phase32f_captures,
)

PHASE32A_EVIDENCE = (
    "evidence/phase3.2a/bh1750_physical_ba2024b_20260716_234217.jsonl",
    "6B9A2AE724C6473D6D8F18533CDC7B7081BCC782709862E914CE6B20B1690317",
)
PHASE32C_EVIDENCE = (
    "evidence/phase3.2c/bmp280_physical_adef636_20260718_002346.jsonl",
    "1BB0C5BE149DC7C49A3C63432D1CAE4AACAE3D5A80265FE879CA06D1E1A74805",
)

REQUIRED_FILES = (
    "docs/openrf1_ground_sensors_bringup.md",
    "firmware/openrf1/ground_sensors_bringup/board_config.h",
    "firmware/openrf1/ground_sensors_bringup/ground_sensors.c",
    "firmware/openrf1/ground_sensors_bringup/ground_sensors.h",
    "firmware/openrf1/ground_sensors_bringup/main_ground_sensors_bringup.c",
    "firmware/openrf1/ground_sensors_bringup/platform_ground_sensors_bringup.c",
    "firmware/openrf1/ground_sensors_bringup/platform_ground_sensors_bringup.h",
    "firmware/openrf1/ground_sensors_bringup/telemetry_ground_sensors_bringup.c",
    "firmware/openrf1/ground_sensors_bringup/telemetry_ground_sensors_bringup.h",
    "firmware/openrf1/keil/OpenRF1_GroundSensors_Bringup.uvprojx",
    "firmware/openrf1/keil/RTE/_OpenRF1_GroundSensors_Bringup/RTE_Components.h",
    "pc/src/rplidar_c1_tools/openrf1_ground_sensors_bringup.py",
    "pc/tests/test_openrf1_ground_sensors_bringup.py",
    "pc/src/rplidar_c1_tools/phase32f_evidence.py",
    "pc/tests/test_phase32f_physical_evidence.py",
    "tools/audit_phase32f.py",
    "evidence/phase3.2f/tcrt5000_physical_evidence.md",
)

GENERATED_PATTERNS = (
    "firmware/openrf1/keil/Objects/",
    "firmware/openrf1/keil/Objects_FullHardware/",
    "firmware/openrf1/keil/Objects_BMP280_Bringup/",
    "firmware/openrf1/keil/Objects_MPU6050_Bringup/",
    "firmware/openrf1/keil/Objects_HCSR04_Bringup/",
    "firmware/openrf1/keil/Objects_GroundSensors_Bringup/",
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
    lines = ["Phase 3.2F ground-sensor bring-up audit"]
    _check_required_files(lines, failures)
    _check_source_contract(lines, failures)
    _check_keil_project(lines, failures)
    _check_documentation(lines, failures)
    _check_git_hygiene(lines, failures)
    _check_previous_evidence_hashes(lines, failures)
    _check_phase32f_physical_evidence(lines, failures)
    _check_private_information(lines, failures)
    _check_build_evidence(lines)
    lines.append("software_status: SOFTWARE_READY")
    lines.append("physical_status: ISOLATED_TCRT_EVIDENCE_RECORDED")
    lines.append("physical_evidence_verified: isolated_tcrt_only")
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


def _check_source_contract(lines: list[str], failures: list[str]) -> None:
    bringup_root = REPO_ROOT / "firmware/openrf1/ground_sensors_bringup"
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in bringup_root.glob("*.[ch]"))
    host_text = (REPO_ROOT / "pc/src/rplidar_c1_tools/openrf1_ground_sensors_bringup.py").read_text(encoding="utf-8")
    combined = source_text + "\n" + host_text
    required = (
        "OPENRF1_GROUND_LEFT_PIN_TEXT \"PC4\"",
        "OPENRF1_GROUND_RIGHT_PIN_TEXT \"PC5\"",
        "OPENRF1_GROUND_HALL_PIN_TEXT \"PB0\"",
        "OPENRF1_GROUND_GPIO_MODE_TEXT \"floating_input\"",
        "OPENRF1_GROUND_SAMPLE_PERIOD_MS ((uint32_t)5u)",
        "OPENRF1_GROUND_DEBOUNCE_SAMPLES ((uint8_t)4u)",
        "OPENRF1_GROUND_EFFECTIVE_DEBOUNCE_MS ((uint32_t)20u)",
        "OPENRF1_GROUND_TELEMETRY_PERIOD_MS ((uint32_t)50u)",
        "OPENRF1_GROUND_SIGNAL4_USED ((uint8_t)0u)",
        "OPENRF1_GROUND_SIGNAL4_MAPPING_CONFLICT \"schematic_PC14_vendor_example_PB1\"",
        "OPENRF1_GROUND_LEFT_SUPPLY_TEXT \"3.3V\"",
        "OPENRF1_GROUND_RIGHT_SUPPLY_TEXT \"3.3V\"",
        "OPENRF1_GROUND_HALL_MODULE_SUPPLY_TEXT \"5V\"",
        "OPENRF1_GROUND_HALL_INPUT_PROTECTION_TEXT \"external_10k_15k_divider_required\"",
        "OPENRF1_GROUND_HALL_DIVIDER_SERIES_RESISTOR_OHM ((uint16_t)10000u)",
        "OPENRF1_GROUND_HALL_DIVIDER_PULLDOWN_RESISTOR_OHM ((uint16_t)15000u)",
        "ground_sensors_update_sample",
        "next_sample_ms += OPENRF1_GROUND_SAMPLE_PERIOD_MS",
        "next_telemetry_ms += OPENRF1_GROUND_TELEMETRY_PERIOD_MS",
        "openrf1_ground_read_levels",
        "\\\"raw_level\\\":%u",
        "\\\"debounced_level\\\":%u",
        "\\\"semantic_polarity\\\":\\\"unverified\\\"",
    )
    missing = [snippet for snippet in required if snippet not in combined]
    lines.append(f"ground_source_required_snippets_present: {not missing}")
    if missing:
        failures.append("missing ground-sensor source snippets: " + ", ".join(missing))

    platform_text = (bringup_root / "platform_ground_sensors_bringup.c").read_text(encoding="utf-8")
    platform_checks = {
        "pc4_pc5_pb0_floating_inputs": "GPIO_Mode_IN_FLOATING" in platform_text
        and "OPENRF1_GROUND_LEFT_PIN | OPENRF1_GROUND_RIGHT_PIN" in platform_text
        and "OPENRF1_GROUND_HALL_PIN" in platform_text,
        "pb1_not_touched": "GPIO_Pin_1" not in platform_text and "PB1" not in platform_text,
        "pc14_not_initialized": "GPIO_Pin_14" not in platform_text and "PC14" not in platform_text,
    }
    for label, passed in platform_checks.items():
        lines.append(f"{label}: {passed}")
        if not passed:
            failures.append(label)

    forbidden_runtime = (
        "black_detected",
        "white_detected",
        "line_detected",
        "drop_detected",
        "edge_detected",
        "safe_ground",
        "magnet_present",
        "landmark_detected",
        "sensor_missing",
        "disconnected_sensor",
        "chip_id_mismatch",
        "communication_error",
    )
    found = [term for term in forbidden_runtime if term in combined]
    lines.append(f"runtime_semantic_or_fake_presence_claims_present: {bool(found)}")
    if found:
        failures.append("forbidden runtime claims: " + ", ".join(found))

    cross_scope = (
        "BH1750",
        "BMP280",
        "MPU6050",
        "HCSR04",
        "RPLIDAR",
        "ESP32",
        "USART2",
        "USART3",
        "motor",
        "encoder",
        "servo",
    )
    found_cross_scope = [term for term in cross_scope if term in source_text]
    lines.append(f"ground_bringup_source_isolated: {not found_cross_scope}")
    if found_cross_scope:
        failures.append("forbidden cross-scope source terms: " + ", ".join(found_cross_scope))


def _check_keil_project(lines: list[str], failures: list[str]) -> None:
    project = REPO_ROOT / "firmware/openrf1/keil/OpenRF1_GroundSensors_Bringup.uvprojx"
    rte = REPO_ROOT / "firmware/openrf1/keil/RTE/_OpenRF1_GroundSensors_Bringup/RTE_Components.h"
    raw = project.read_bytes()
    text = raw.decode("utf-8")
    rte_text = rte.read_text(encoding="utf-8")
    checks = {
        "ground_uvprojx_has_no_utf8_bom": not raw.startswith(b"\xef\xbb\xbf"),
        "ground_target_name": "<TargetName>OpenRF1_GroundSensors_Bringup</TargetName>" in text,
        "ground_output_directory_isolated": ".\\Objects_GroundSensors_Bringup\\" in text,
        "ground_output_name_isolated": "<OutputName>OpenRF1_GroundSensors_Bringup</OutputName>" in text,
        "ground_includes_are_relative": "..\\ground_sensors_bringup;..\\full_hardware;..\\app" in text,
        "gpio_rcc_usart_components_present": "RTE_DEVICE_STDPERIPH_GPIO" in rte_text
        and "RTE_DEVICE_STDPERIPH_RCC" in rte_text
        and "RTE_DEVICE_STDPERIPH_USART" in rte_text,
        "no_user_absolute_paths": "C:\\Users" not in text,
        "no_desktop_paths": ("Desk" + "top") not in text,
        "no_com_ports": COM_PORT_RE.search(text) is None,
        "only_required_sensor_source": all(
            forbidden not in text
            for forbidden in (
                "bh1750.c",
                "bmp280.c",
                "mpu6050.c",
                "hcsr04.c",
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
    source_text = "\n".join(
        (REPO_ROOT / relative).read_text(encoding="utf-8", errors="replace")
        for relative in (
            "README.md",
            "PROJECT_SPEC.md",
            "HARDWARE_LOCK.md",
            "docs/wiring.md",
            "docs/stm32_sensor_bringup.md",
            "docs/phase3_hardware_checklist.md",
            "docs/openrf1_ground_sensors_bringup.md",
            "docs/test_plan.md",
        )
        if (REPO_ROOT / relative).exists()
    )
    required = (
        "IMPLEMENTED / SOFTWARE_READY",
        "AUTHORITATIVE_VENDOR_DOCUMENTED",
        "DESIGN_LOCKED",
        "UNVERIFIED",
        "PHYSICAL_VERIFICATION_REQUIRED",
        "OpenRF1 vendor control-board package",
        "OpenRF1 four-channel tracking example",
        "OpenRF1 schematic revision dated 2024-07-01",
        "signal 1 / X1 / PC4",
        "signal 2 / X2 / PC5",
        "signal 3 / X3 / PB0",
        "pin 1: GND",
        "pin 2: X4 / schematic PC14",
        "pin 3: X3 / PB0",
        "pin 4: X2 / PC5",
        "pin 5: X1 / PC4",
        "pin 6: VCC_5V",
        "signal 4 / X4 is unused",
        "schematic says PC14",
        "old example maps X4 to PB1",
        "do not power the TCRT modules from the connector's 5 V pin",
        "Do not connect Hall S directly to PB0.",
        "10 kOhm",
        "15 kOhm",
        "do not share one VCC rail",
        "floating input",
        "raw GPIO values are not semantic detection states",
        "semantic polarity remains unverified",
        "phase3.2f",
        "OpenRF1_GroundSensors_Bringup.uvprojx",
        "Objects_GroundSensors_Bringup",
    )
    missing = [snippet for snippet in required if snippet not in source_text]
    lines.append(f"ground_documentation_required_snippets_present: {not missing}")
    if missing:
        failures.append("missing ground-sensor documentation snippets: " + ", ".join(missing))

    ground_doc = REPO_ROOT / "docs/openrf1_ground_sensors_bringup.md"
    text = ground_doc.read_text(encoding="utf-8", errors="replace") if ground_doc.exists() else ""
    false_claims = (
        "left TCRT active polarity is verified",
        "right TCRT active polarity is verified",
        "Hall active polarity is verified",
        "magnetic detection has been physically verified",
        "black/white/drop behavior has been physically verified",
    )
    found_claims = [claim for claim in false_claims if claim in text]
    lines.append(f"ground_false_physical_claims_present: {bool(found_claims)}")
    if found_claims:
        failures.append("false physical claims: " + ", ".join(found_claims))


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


def _check_phase32f_physical_evidence(lines: list[str], failures: list[str]) -> None:
    try:
        summaries = validate_all_phase32f_captures(REPO_ROOT)
    except (OSError, UnicodeError, Phase32fEvidenceError) as exc:
        lines.append("phase3_2f_tcrt_evidence_valid: False")
        failures.append(f"invalid Phase 3.2F TCRT evidence: {exc}")
        return

    lines.append("phase3_2f_tcrt_evidence_valid: True")
    lines.append(f"phase3_2f_tcrt_capture_count: {len(summaries)}")
    lines.append(f"phase3_2f_tcrt_capture_frames_each: {summaries[0].record_count}")
    lines.append(f"phase3_2f_tcrt_steady_interval_ms: {summaries[0].interval_ms}")
    lines.append(f"phase3_2f_tcrt_formal_hex_sha256: {FORMAL_KEIL_HEX_SHA256}")
    evidence_root = REPO_ROOT / "evidence/phase3.2f"
    tracked_names = {path.name for path in evidence_root.glob("*.jsonl")}
    expected_names = {spec["path"].name for spec in CAPTURE_SPECS.values()}
    unexpected = sorted(tracked_names - expected_names)
    if unexpected:
        failures.append("unexpected Phase 3.2F evidence files: " + ", ".join(unexpected))
    lines.append(f"phase3_2f_unexpected_evidence_files: {bool(unexpected)}")


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
    hex_path = REPO_ROOT / "firmware/openrf1/keil/Objects_GroundSensors_Bringup/OpenRF1_GroundSensors_Bringup.hex"
    log_path = REPO_ROOT / "firmware/openrf1/keil/Objects_GroundSensors_Bringup/OpenRF1_GroundSensors_Bringup.build_log.htm"
    hex_present = hex_path.exists() and hex_path.stat().st_size > 0
    lines.append(f"ground_sensors_bringup_local_hex_present: {hex_present}")
    if hex_present:
        lines.append(f"ground_sensors_bringup_hex_sha256: {hashlib.sha256(hex_path.read_bytes()).hexdigest().upper()}")
    lines.append(f"ground_sensors_bringup_local_keil_zero_errors_warnings: {_log_has_zero_errors_warnings(log_path)}")


def _log_has_zero_errors_warnings(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return "0 Error(s), 0 Warning(s)" in text


def manual_status_text() -> str:
    return "\n".join(
        [
            "Phase 3.2F ground-sensor manual hardware status",
            "software_foundation: SOFTWARE_READY by committed tests and verifier when this audit passes",
            "connector_signal_1_pc4: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "connector_signal_2_pc5: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "connector_signal_3_pb0: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "connector_pin_order: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "vendor_input_mode_floating: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "schematic_x4_pc14: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "vendor_example_x4_pb1_conflict: AUTHORITATIVE_VENDOR_DOCUMENTED",
            "tcrt_modules_powered_from_3v3: DESIGN_LOCKED",
            "hall_module_powered_from_5v: DESIGN_LOCKED",
            "hall_s_external_10k_15k_divider: DESIGN_LOCKED",
            "hall_s_direct_to_pb0: PROHIBITED",
            "signal_4: unused",
            "physical_connector_orientation: UNVERIFIED",
            "cable_orientation: UNVERIFIED",
            "actual_3v3_rail: UNVERIFIED",
            "actual_5v_rail: UNVERIFIED",
            "actual_tcrt_output_voltage: UNVERIFIED",
            "tcrt_output_topology: UNVERIFIED",
            "left_tcrt_active_polarity: UNVERIFIED",
            "right_tcrt_active_polarity: UNVERIFIED",
            "hall_module_output_voltage: UNVERIFIED",
            "hall_active_polarity: UNVERIFIED",
            "hall_triggering_magnetic_pole: UNVERIFIED",
            "tcrt_signal_connections_pc4_pc5: MANUAL_EVIDENCE_VERIFIED",
            "tcrt_live_raw_and_debounced_response: MANUAL_EVIDENCE_VERIFIED",
            "four_100_frame_captures_no_sequence_gaps: MANUAL_EVIDENCE_VERIFIED",
            "actual_50_ms_serial_periodicity_steady_state: MANUAL_EVIDENCE_VERIFIED",
            "white_surface_response_at_tested_geometry: MANUAL_EVIDENCE_VERIFIED",
            "open_space_response_at_tested_geometry: MANUAL_EVIDENCE_VERIFIED",
            "tcrt_semantic_polarity: UNVERIFIED",
            "black_white_classification: UNVERIFIED",
            "edge_or_open_space_safety_behavior: UNVERIFIED",
            "magnetic_activation: UNVERIFIED",
            "magnetic_release: UNVERIFIED",
            "real_debounce_suitability: UNVERIFIED",
            "full_hardware_operation: UNVERIFIED",
            "hardware_access_by_automation: none",
        ]
    ) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
