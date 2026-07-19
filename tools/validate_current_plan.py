"""Validate explicit current-plan facts in authoritative project documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys


AUTHORITATIVE_FILES = (
    "AGENTS.md",
    "README.md",
    "PROJECT_SPEC.md",
    "HARDWARE_LOCK.md",
    "docs/architecture.md",
    "docs/stm32_sensor_protocol.md",
    "docs/phase3_hardware_checklist.md",
    "docs/openrf1_bh1750_bringup.md",
    "docs/phase3_2b_full_hardware_foundation.md",
    "docs/openrf1_phase32b_protocol.md",
    "docs/openrf1_mpu6050_bringup.md",
    "docs/openrf1_hcsr04_bringup.md",
    "docs/openrf1_ground_sensors_bringup.md",
    "docs/phase4a_mecanum_kinematics_odometry_foundation.md",
    "docs/phase4b_closed_loop_motion_control_foundation.md",
    "docs/test_plan.md",
)


@dataclass(frozen=True, slots=True)
class RequiredSnippet:
    path: str
    snippet: str
    label: str


REQUIRED_SNIPPETS = (
    RequiredSnippet("README.md", "RPLIDAR C1M1-R2 x1", "single current C1 inventory documented"),
    RequiredSnippet("README.md", "only active LiDAR integration target", "one-C1 baseline documented"),
    RequiredSnippet("README.md", "no current dual-C1 feasibility evaluation", "dual-C1 out-of-scope status documented"),
    RequiredSnippet("README.md", "WiFi", "WiFi baseline documented"),
    RequiredSnippet("README.md", "ROS and a vehicle-mounted Linux computer are not required", "ROS/Linux non-goal documented"),
    RequiredSnippet("PROJECT_SPEC.md", "mandatory requirements", "authoritative requirements section"),
    RequiredSnippet("PROJECT_SPEC.md", "environmental-change indication", "environmental wording documented"),
    RequiredSnippet("PROJECT_SPEC.md", "Reliable real-world dust-storm detection is not claimed", "dust-storm honesty documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "CONFIRMED INVENTORY", "inventory section documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "BH1750 x1", "BH1750 documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "BMP280 x1", "BMP280 documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "exact ESP32 module UART GPIOs: CONFIRMED_MODULE_EVIDENCE", "ESP32 module GPIO evidence documented"),
    RequiredSnippet("docs/architecture.md", "STM32 sensors and rover state", "STM32 data path documented"),
    RequiredSnippet("docs/architecture.md", "ESP32 -> WiFi -> PC", "ESP32 WiFi role documented"),
    RequiredSnippet("docs/architecture.md", "PC visualization/recording", "PC role documented"),
    RequiredSnippet("docs/test_plan.md", "Phase 2.4", "phase order documented"),
    RequiredSnippet("docs/test_plan.md", "Phase 2.5", "next hardware test phase documented"),
    RequiredSnippet("AGENTS.md", "Do not invent GPIO", "future-agent hardware policy documented"),
    RequiredSnippet("AGENTS.md", "Do not invent COM ports", "future-agent serial-port policy documented"),
    RequiredSnippet("README.md", "capture-c1", "Phase 2.5 capture CLI documented"),
    RequiredSnippet("PROJECT_SPEC.md", "Automated tests use mocked byte streams", "Phase 2.5 automation boundary documented"),
    RequiredSnippet("README.md", "mars_scout_stm32_sensor_telemetry", "Phase 3.1 protocol documented"),
    RequiredSnippet("README.md", "simulate-stm32-sensors", "Phase 3.1 simulation CLI documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "USER-CONFIRMED PLANNED CONNECTION", "planned connector status documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "HC-SR04 ECHO voltage compatibility", "HC-SR04 ECHO status documented"),
    RequiredSnippet("docs/architecture.md", "STM32 telemetry parser / recording bridge", "Phase 3.1 software layer documented"),
    RequiredSnippet("docs/stm32_sensor_protocol.md", "timeout must not be represented as a valid zero-distance obstacle", "ultrasonic timeout semantics documented"),
    RequiredSnippet("docs/phase3_hardware_checklist.md", "Do not mark checklist items complete automatically", "manual checklist honesty documented"),
    RequiredSnippet("README.md", "OpenRF1 STM32F103RCT6", "Phase 3.2A OpenRF1 target documented"),
    RequiredSnippet("README.md", "capture-stm32-serial", "Phase 3.2A capture CLI documented"),
    RequiredSnippet("README.md", "phase3.2a", "Phase 3.2A verifier documented"),
    RequiredSnippet("PROJECT_SPEC.md", "Phase 3.2A Acceptance Philosophy", "Phase 3.2A acceptance documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "OpenRF1 robot controller", "OpenRF1 board documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "STM32F103RCT6", "OpenRF1 MCU documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "PB1", "OpenRF1 SCL documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "PC3", "OpenRF1 SDA documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "BH1750 communication at configured address `0x23`", "BH1750 evidence status documented"),
    RequiredSnippet("docs/openrf1_bh1750_bringup.md", "GY-302 VCC", "BH1750 wiring procedure documented"),
    RequiredSnippet("docs/openrf1_bh1750_bringup.md", "Do not invent a COM port", "COM-port honesty documented"),
    RequiredSnippet("README.md", "phase3.2b", "Phase 3.2B verifier documented"),
    RequiredSnippet("AGENTS.md", "Phase 3.2B software work is complete", "Phase 3.2B software status documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "Phase 3.2B proposed full-hardware connection plan", "Phase 3.2B proposal status documented"),
    RequiredSnippet("docs/phase3_2b_full_hardware_foundation.md", "real multisensor wiring, power integrity", "Phase 3.2B manual warning documented"),
    RequiredSnippet("docs/openrf1_phase32b_protocol.md", "CRC-16/CCITT-FALSE", "Phase 3.2B binary CRC documented"),
    RequiredSnippet("README.md", "Phase 3.2D", "Phase 3.2D status documented"),
    RequiredSnippet("README.md", "OpenRF1_MPU6050_Bringup.uvprojx", "Phase 3.2D Keil target documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "Phase 3.2D MPU6050 Bring-Up Boundary Status", "Phase 3.2D hardware boundary documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "MPU6050 ACK, physical address, WHO_AM_I", "MPU6050 unverified status documented"),
    RequiredSnippet("docs/openrf1_mpu6050_bringup.md", "PHYSICAL_VERIFICATION_REQUIRED", "MPU6050 physical verification status documented"),
    RequiredSnippet("docs/test_plan.md", "phase3.2d", "Phase 3.2D verifier documented"),
    RequiredSnippet("README.md", "Phase 3.2E", "Phase 3.2E status documented"),
    RequiredSnippet("README.md", "OpenRF1_HCSR04_Bringup.uvprojx", "Phase 3.2E Keil target documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "Phase 3.2E HC-SR04 Bring-Up Boundary Status", "Phase 3.2E hardware boundary documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "TRIG: PA5", "HC-SR04 TRIG pin documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "ECHO: PA4", "HC-SR04 ECHO pin documented"),
    RequiredSnippet("docs/openrf1_hcsr04_bringup.md", "Do not connect HC-SR04 ECHO directly to CN6 pin 4", "HC-SR04 direct ECHO prohibition documented"),
    RequiredSnippet("docs/test_plan.md", "phase3.2e", "Phase 3.2E verifier documented"),
    RequiredSnippet("README.md", "Phase 3.2F", "Phase 3.2F status documented"),
    RequiredSnippet("README.md", "OpenRF1_GroundSensors_Bringup.uvprojx", "Phase 3.2F Keil target documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "Phase 3.2F Ground-Sensor Bring-Up Boundary Status", "Phase 3.2F hardware boundary documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "signal 1 / X1 / PC4", "Ground signal 1 pin documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "signal 2 / X2 / PC5", "Ground signal 2 pin documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "signal 3 / X3 / PB0", "Ground signal 3 pin documented"),
    RequiredSnippet("docs/openrf1_ground_sensors_bringup.md", "Do not connect Hall S directly to PB0", "Hall direct connection prohibition documented"),
    RequiredSnippet("docs/openrf1_ground_sensors_bringup.md", "semantic polarity remains unverified", "Ground semantic polarity status documented"),
    RequiredSnippet("docs/test_plan.md", "phase3.2f", "Phase 3.2F verifier documented"),
    RequiredSnippet("README.md", "Phase 4A", "Phase 4A software status documented"),
    RequiredSnippet("README.md", "simulate-mecanum-odometry", "Phase 4A simulator CLI documented"),
    RequiredSnippet("AGENTS.md", "Phase 4A software work is complete", "Phase 4A software boundary documented"),
    RequiredSnippet("docs/phase4a_mecanum_kinematics_odometry_foundation.md", "counts_per_wheel_revolution", "Phase 4A explicit encoder resolution documented"),
    RequiredSnippet("docs/phase4a_mecanum_kinematics_odometry_foundation.md", "UNVERIFIED physical facts", "Phase 4A physical boundary documented"),
    RequiredSnippet("docs/test_plan.md", "phase4a", "Phase 4A verifier documented"),
    RequiredSnippet("README.md", "Phase 4B", "Phase 4B software status documented"),
    RequiredSnippet("README.md", "simulate-motion-control", "Phase 4B simulator CLI documented"),
    RequiredSnippet("AGENTS.md", "Phase 4B software work is complete", "Phase 4B software boundary documented"),
    RequiredSnippet("docs/phase4b_closed_loop_motion_control_foundation.md", "conditional integration", "Phase 4B anti-windup documented"),
    RequiredSnippet("docs/phase4b_closed_loop_motion_control_foundation.md", "UNVERIFIED physical facts", "Phase 4B physical boundary documented"),
    RequiredSnippet("docs/test_plan.md", "phase4b", "Phase 4B verifier documented"),
)


class CurrentPlanValidationError(ValueError):
    """Raised when explicit current-plan anchors are missing."""


def validate_current_plan(repo_root: Path) -> list[str]:
    """Return missing explicit anchors from current authoritative documents."""
    missing: list[str] = []
    for relative in AUTHORITATIVE_FILES:
        path = repo_root / relative
        if not path.exists():
            missing.append(f"{relative}: missing file")
    for requirement in REQUIRED_SNIPPETS:
        path = repo_root / requirement.path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        if requirement.snippet.lower() not in text:
            missing.append(f"{requirement.path}: missing {requirement.label}")
    return missing


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    missing = validate_current_plan(repo_root)
    if missing:
        for item in missing:
            print(f"FAIL {item}")
        return 1
    print("PASS current plan anchors present")
    print("NOTE this validator checks explicit text anchors only; it is not semantic analysis.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
