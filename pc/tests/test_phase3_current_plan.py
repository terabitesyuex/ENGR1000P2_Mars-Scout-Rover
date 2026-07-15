from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_phase31_current_plan_documents_core_boundaries():
    required = {
        "AGENTS.md": [
            "Phase 3.1 software work is complete",
            "Phase 3.2 and later physical sensor integration have not started",
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

