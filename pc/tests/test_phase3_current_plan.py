from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_phase31_current_plan_documents_core_boundaries():
    required = {
        "AGENTS.md": [
            "Phase 3.1 software work is complete",
            "Phase 3.2A software work is complete",
            "Phase 3.2B software work is complete",
            "Phase 3.2B physical sensor integration has not started",
            "No hardware result may be claimed without evidence",
        ],
        "README.md": [
            "mars_scout_stm32_sensor_telemetry",
            "simulate-stm32-sensors",
            "record-stm32-telemetry",
        ],
        "HARDWARE_LOCK.md": [
            "USER-CONFIRMED PLANNED CONNECTION",
            "HC-SR04 ECHO voltage compatibility",
            "TCRT5000 and Hall output polarity remains UNVERIFIED",
        ],
        "docs/stm32_sensor_protocol.md": [
            "mars_scout_stm32_sensor_telemetry",
            "timeout must not be represented as a valid zero-distance obstacle",
            "Hall sensor is for magnetic landmark/checkpoint detection",
        ],
        "docs/phase3_hardware_checklist.md": [
            "Do not mark checklist items complete automatically",
            "HC-SR04",
            "Evidence table",
        ],
    }

    missing: list[str] = []
    for relative, snippets in required.items():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{relative}: {snippet}")

    assert missing == []


def test_phase32a_current_plan_documents_openrf1_bh1750_boundaries():
    required = {
        "README.md": [
            "OpenRF1 STM32F103RCT6",
            "simulate-bh1750-telemetry",
            "capture-stm32-serial",
            "MANUAL_ACTION_REQUIRED",
        ],
        "HARDWARE_LOCK.md": [
            "OpenRF1 robot controller",
            "STM32F103RCT6",
            "PB1",
            "PC3",
            "NOT YET ACK-VERIFIED",
        ],
        "docs/openrf1_bh1750_bringup.md": [
            "GY-302 VCC",
            "OpenRF1 PB1/SCL",
            "OpenRF1 PC3/SDA",
            "Do not invent a COM port",
        ],
        "docs/test_plan.md": [
            "phase3.2a",
            "Phase 3.2A automated tests do not open real COM ports",
        ],
    }

    missing: list[str] = []
    for relative, snippets in required.items():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{relative}: {snippet}")

    assert missing == []


def test_phase32b_current_plan_documents_software_foundation_boundaries():
    required = {
        "README.md": [
            "Phase 3.2B",
            "OpenRF1_FullHardware.uvprojx",
            "live sensor/link behavior remain UNVERIFIED",
        ],
        "HARDWARE_LOCK.md": [
            "Phase 3.2B proposed full-hardware connection plan",
            "firmware/openrf1/full_hardware/",
            "Physical wiring, voltage levels",
        ],
        "docs/phase3_2b_full_hardware_foundation.md": [
            "Software foundation and Keil builds are VERIFIED",
            "Module supply compatibility is MANUAL_ACTION_REQUIRED",
            "Validate C1-to-ESP32 data transport",
        ],
        "docs/openrf1_phase32b_protocol.md": [
            "payload_length",
            "CRC-16/CCITT-FALSE",
            "a55a0101000034120403020102004f4b94fd",
        ],
        "docs/wiring.md": [
            "Phase 3.2B Proposed Full-Hardware Wiring",
            "Software cannot make Echo electrically safe",
        ],
    }

    missing: list[str] = []
    for relative, snippets in required.items():
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                missing.append(f"{relative}: {snippet}")

    assert missing == []

