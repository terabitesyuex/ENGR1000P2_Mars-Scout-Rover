from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from rplidar_c1_tools.openrf1_ground_sensors_bringup import (
    ERROR_INVALID_LEVEL,
    GROUND_CHANNELS,
    GROUND_CONNECTOR,
    GROUND_CONNECTOR_PART,
    GROUND_DEBOUNCE_SAMPLES,
    GROUND_EFFECTIVE_DEBOUNCE_MS,
    GROUND_GPIO_MODE,
    GROUND_SAMPLE_PERIOD_MS,
    GROUND_SEMANTIC_POLARITY,
    GROUND_SIGNAL4,
    GROUND_TELEMETRY_PERIOD_MS,
    HALL_DIRECT_TO_PB0_ALLOWED,
    HALL_DIVIDER_PULLDOWN_RESISTOR_OHM,
    HALL_DIVIDER_SERIES_RESISTOR_OHM,
    HALL_DIVIDER_TOLERANCE_PERCENT,
    HALL_MODULE_SUPPLY_MV,
    HALL_SENSOR,
    LEFT_TCRT5000,
    RIGHT_TCRT5000,
    SHARED_MODULE_VCC_ALLOWED,
    TCRT_SUPPLY_MV,
    DebouncedDigitalInput,
    GroundSensorsBringupError,
    GroundSensorsState,
    active_signal_map,
    connector_pin_map,
    format_error_telemetry,
    format_ground_sensors_telemetry,
    format_identity_telemetry,
    hall_divider_output_mv,
    scheduled_deadlines,
    validate_static_configuration,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BRINGUP_ROOT = REPO_ROOT / "firmware" / "openrf1" / "ground_sensors_bringup"
KEIL_PROJECT = REPO_ROOT / "firmware" / "openrf1" / "keil" / "OpenRF1_GroundSensors_Bringup.uvprojx"
RTE_COMPONENTS = REPO_ROOT / "firmware" / "openrf1" / "keil" / "RTE" / "_OpenRF1_GroundSensors_Bringup" / "RTE_Components.h"
DOC_PATH = REPO_ROOT / "docs" / "openrf1_ground_sensors_bringup.md"
WIRING_DOC = REPO_ROOT / "docs" / "wiring.md"
HARDWARE_LOCK = REPO_ROOT / "HARDWARE_LOCK.md"
GITIGNORE = REPO_ROOT / ".gitignore"


def _record(line: str) -> dict:
    assert line.endswith("\n")
    assert line.startswith("{")
    assert "NaN" not in line
    assert "Infinity" not in line
    assert "\x1b" not in line
    return json.loads(line)


def test_vendor_documented_ground_sensor_mapping_and_x4_conflict_are_locked():
    assert GROUND_CONNECTOR == "OpenRF1_four_channel_tracking"
    assert GROUND_CONNECTOR_PART == "HDGC2001WV-6P"
    assert connector_pin_map() == {
        1: "GND",
        2: "X4_schematic_PC14_unused",
        3: "X3_PB0",
        4: "X2_PC5",
        5: "X1_PC4",
        6: "VCC_5V",
    }
    assert active_signal_map() == {
        1: "PC4",
        2: "PC5",
        3: "PB0",
    }
    assert GROUND_CHANNELS[LEFT_TCRT5000]["connector_label"] == "X1"
    assert GROUND_CHANNELS[LEFT_TCRT5000]["mcu_pin"] == "PC4"
    assert GROUND_CHANNELS[RIGHT_TCRT5000]["connector_label"] == "X2"
    assert GROUND_CHANNELS[RIGHT_TCRT5000]["mcu_pin"] == "PC5"
    assert GROUND_CHANNELS[HALL_SENSOR]["connector_label"] == "X3"
    assert GROUND_CHANNELS[HALL_SENSOR]["mcu_pin"] == "PB0"
    assert GROUND_SIGNAL4["status"] == "unused"
    assert GROUND_SIGNAL4["schematic_mcu_pin"] == "PC14"
    assert GROUND_SIGNAL4["vendor_example_mcu_pin"] == "PB1"
    assert GROUND_SIGNAL4["mapping_conflict"] == "schematic_PC14_vendor_example_PB1"
    validate_static_configuration()


def test_power_contracts_and_divider_are_explicit():
    assert TCRT_SUPPLY_MV == 3300
    assert GROUND_CHANNELS[LEFT_TCRT5000]["supply"] == "3.3V"
    assert GROUND_CHANNELS[RIGHT_TCRT5000]["supply"] == "3.3V"
    assert HALL_MODULE_SUPPLY_MV == 5000
    assert GROUND_CHANNELS[HALL_SENSOR]["module_supply"] == "5V"
    assert HALL_DIRECT_TO_PB0_ALLOWED is False
    assert SHARED_MODULE_VCC_ALLOWED is False
    assert HALL_DIVIDER_SERIES_RESISTOR_OHM == 10_000
    assert HALL_DIVIDER_PULLDOWN_RESISTOR_OHM == 15_000
    assert HALL_DIVIDER_TOLERANCE_PERCENT == 5
    assert hall_divider_output_mv(5_000) == 3_000
    assert hall_divider_output_mv(5_500) == 3_300


def test_sampling_debounce_and_telemetry_period_contracts():
    assert GROUND_GPIO_MODE == "floating_input"
    assert GROUND_SAMPLE_PERIOD_MS == 5
    assert GROUND_DEBOUNCE_SAMPLES == 4
    assert GROUND_EFFECTIVE_DEBOUNCE_MS == 20
    assert GROUND_TELEMETRY_PERIOD_MS == 50
    assert scheduled_deadlines(start_ms=100, period_ms=5, count=4) == (105, 110, 115, 120)
    assert scheduled_deadlines(start_ms=100, period_ms=50, count=3) == (150, 200, 250)


def test_initial_state_comes_from_observed_levels():
    state = GroundSensorsState.from_initial_levels(
        left_tcrt5000=1,
        right_tcrt5000=0,
        hall_sensor=1,
    )
    assert state.left_tcrt5000.raw_level == 1
    assert state.left_tcrt5000.debounced_level == 1
    assert state.left_tcrt5000.candidate_count == 0
    assert state.right_tcrt5000.raw_level == 0
    assert state.right_tcrt5000.debounced_level == 0
    assert state.hall_sensor.raw_level == 1
    assert state.hall_sensor.debounced_level == 1


def _debounced_trace(initial: int, samples: list[int]) -> list[int]:
    channel = DebouncedDigitalInput.from_initial_level(initial)
    trace: list[int] = []
    for sample in samples:
        channel.update(sample)
        trace.append(channel.debounced_level)
    return trace


def test_required_low_to_high_debounce_vectors():
    assert _debounced_trace(0, [1, 0, 1, 1, 1]) == [0, 0, 0, 0, 0]
    assert _debounced_trace(0, [1, 1, 1, 1]) == [0, 0, 0, 1]


def test_required_high_to_low_debounce_vectors():
    assert _debounced_trace(1, [0, 0, 1, 0, 0, 0]) == [1, 1, 1, 1, 1, 1]
    assert _debounced_trace(1, [0, 0, 0, 0]) == [1, 1, 1, 0]


def test_raw_level_is_immediate_while_debounced_level_waits_for_threshold():
    channel = DebouncedDigitalInput.from_initial_level(0)
    channel.update(1)
    assert channel.raw_level == 1
    assert channel.debounced_level == 0
    channel.update(1)
    channel.update(1)
    assert channel.raw_level == 1
    assert channel.debounced_level == 0
    channel.update(1)
    assert channel.debounced_level == 1


def test_independent_debounce_one_noisy_channel_does_not_affect_others():
    state = GroundSensorsState.from_initial_levels(
        left_tcrt5000=0,
        right_tcrt5000=1,
        hall_sensor=0,
    )
    noisy_left = [1, 0, 1, 0, 1, 0, 1]
    for value in noisy_left:
        state.update_sample(left_tcrt5000=value, right_tcrt5000=1, hall_sensor=1)
    assert state.left_tcrt5000.debounced_level == 0
    assert state.right_tcrt5000.debounced_level == 1
    assert state.hall_sensor.debounced_level == 1


def test_invalid_levels_are_rejected_and_rapid_toggling_is_not_an_error():
    channel = DebouncedDigitalInput.from_initial_level(0)
    for value in [1, 0, 1, 0, 1, 0]:
        channel.update(value)
    assert channel.debounced_level == 0
    with pytest.raises(GroundSensorsBringupError, match=ERROR_INVALID_LEVEL):
        channel.update(2)


def test_identity_and_periodic_jsonl_schema_are_strict_and_numeric():
    state = GroundSensorsState.from_initial_levels(
        left_tcrt5000=0,
        right_tcrt5000=1,
        hall_sensor=1,
    )
    identity = _record(format_identity_telemetry(sequence=0, timestamp_ms=5))
    periodic = _record(format_ground_sensors_telemetry(sequence=1, timestamp_ms=55, state=state))

    assert identity["protocol"] == "mars_scout_stm32_sensor_telemetry"
    assert identity["version"] == 1
    assert identity["sequence"] == 0
    assert identity["message_type"] == "sensor_identity"
    assert identity["sensor_id"] == "ground_sensors"
    assert identity["status"] == "ok"
    assert identity["payload"]["sensor_group"] == "ground_sensors"
    assert identity["payload"]["sample_period_ms"] == 5
    assert identity["payload"]["telemetry_period_ms"] == 50
    assert identity["payload"]["debounce_samples"] == 4
    assert identity["payload"]["semantic_polarity"] == GROUND_SEMANTIC_POLARITY
    assert identity["payload"]["channels"][LEFT_TCRT5000]["mcu_pin"] == "PC4"
    assert identity["payload"]["channels"][RIGHT_TCRT5000]["mcu_pin"] == "PC5"
    assert identity["payload"]["channels"][HALL_SENSOR]["mcu_pin"] == "PB0"
    assert identity["payload"]["signal_4"]["status"] == "unused"

    assert periodic["sequence"] == 1
    assert periodic["timestamp_ms"] == 55
    assert periodic["message_type"] == "ground_sensors"
    assert periodic["status"] == "ok"
    assert periodic["payload"][LEFT_TCRT5000] == {"raw_level": 0, "debounced_level": 0}
    assert periodic["payload"][RIGHT_TCRT5000] == {"raw_level": 1, "debounced_level": 1}
    assert periodic["payload"][HALL_SENSOR] == {"raw_level": 1, "debounced_level": 1}
    for payload in periodic["payload"].values():
        assert type(payload["raw_level"]) is int
        assert type(payload["debounced_level"]) is int
        assert payload["raw_level"] in (0, 1)
        assert payload["debounced_level"] in (0, 1)


def test_error_model_is_internal_only_and_does_not_fabricate_sensor_presence():
    error = _record(
        format_error_telemetry(
            sequence=2,
            timestamp_ms=60,
            code="scheduler_invariant",
            operation="sample",
        )
    )
    assert error["status"] == "error"
    assert error["error"]["code"] == "scheduler_invariant"
    assert error["payload"] == {"sensor_group": "ground_sensors"}
    text = json.dumps(error)
    for forbidden in ("sensor_missing", "disconnected_sensor", "NACK", "chip_id_mismatch", "communication_error"):
        assert forbidden not in text


def test_no_semantic_detection_claims_are_present_in_runtime_records():
    state = GroundSensorsState.from_initial_levels(
        left_tcrt5000=1,
        right_tcrt5000=1,
        hall_sensor=0,
    )
    combined = format_identity_telemetry(sequence=0, timestamp_ms=0) + format_ground_sensors_telemetry(
        sequence=1,
        timestamp_ms=50,
        state=state,
    )
    for forbidden in (
        "black_detected",
        "white_detected",
        "line_detected",
        "drop_detected",
        "edge_detected",
        "safe_ground",
        "magnet_present",
        "landmark_detected",
    ):
        assert forbidden not in combined


def test_firmware_source_tree_is_isolated_to_ground_sensors_bringup():
    required = {
        "board_config.h",
        "ground_sensors.c",
        "ground_sensors.h",
        "main_ground_sensors_bringup.c",
        "platform_ground_sensors_bringup.c",
        "platform_ground_sensors_bringup.h",
        "telemetry_ground_sensors_bringup.c",
        "telemetry_ground_sensors_bringup.h",
    }
    assert required.issubset({path.name for path in BRINGUP_ROOT.iterdir()})

    combined = "\n".join(path.read_text(encoding="utf-8") for path in BRINGUP_ROOT.glob("*.[ch]"))
    for required_snippet in (
        'OPENRF1_GROUND_LEFT_PIN_TEXT "PC4"',
        'OPENRF1_GROUND_RIGHT_PIN_TEXT "PC5"',
        'OPENRF1_GROUND_HALL_PIN_TEXT "PB0"',
        'OPENRF1_GROUND_GPIO_MODE_TEXT "floating_input"',
        "OPENRF1_GROUND_SAMPLE_PERIOD_MS ((uint32_t)5u)",
        "OPENRF1_GROUND_DEBOUNCE_SAMPLES ((uint8_t)4u)",
        "OPENRF1_GROUND_EFFECTIVE_DEBOUNCE_MS ((uint32_t)20u)",
        "OPENRF1_GROUND_TELEMETRY_PERIOD_MS ((uint32_t)50u)",
        "OPENRF1_GROUND_SIGNAL4_USED ((uint8_t)0u)",
        'OPENRF1_GROUND_SIGNAL4_MAPPING_CONFLICT "schematic_PC14_vendor_example_PB1"',
        "ground_sensors_update_sample",
        "next_sample_ms += OPENRF1_GROUND_SAMPLE_PERIOD_MS",
        "next_telemetry_ms += OPENRF1_GROUND_TELEMETRY_PERIOD_MS",
        "openrf1_ground_read_levels",
        '\\"raw_level\\":%u',
        '\\"debounced_level\\":%u',
    ):
        assert required_snippet in combined

    platform_text = (BRINGUP_ROOT / "platform_ground_sensors_bringup.c").read_text(encoding="utf-8")
    assert "GPIO_Mode_IN_FLOATING" in platform_text
    assert "OPENRF1_GROUND_LEFT_PIN | OPENRF1_GROUND_RIGHT_PIN" in platform_text
    assert "OPENRF1_GROUND_HALL_PIN" in platform_text
    assert "GPIO_Pin_1" not in platform_text
    assert "GPIO_Pin_14" not in platform_text
    assert "PC14" not in platform_text
    assert "PB1" not in platform_text

    for forbidden in ("BH1750", "BMP280", "MPU6050", "HCSR04", "RPLIDAR", "ESP32", "USART2", "USART3", "motor", "encoder", "servo"):
        assert forbidden not in combined


def test_ground_sensors_keil_target_is_isolated_relative_and_has_no_bom():
    raw_bytes = KEIL_PROJECT.read_bytes()
    assert not raw_bytes.startswith(b"\xef\xbb\xbf")
    text = raw_bytes.decode("utf-8")
    rte_text = RTE_COMPONENTS.read_text(encoding="utf-8")

    assert "<TargetName>OpenRF1_GroundSensors_Bringup</TargetName>" in text
    assert r"<OutputDirectory>.\Objects_GroundSensors_Bringup\</OutputDirectory>" in text
    assert "<OutputName>OpenRF1_GroundSensors_Bringup</OutputName>" in text
    assert "<CreateHexFile>1</CreateHexFile>" in text
    assert "<uAC6>1</uAC6>" in text
    assert "STM32F10X_HD,USE_STDPERIPH_DRIVER" in text
    assert "..\\ground_sensors_bringup;..\\full_hardware;..\\app" in text
    assert "C:\\Users" not in text
    assert ("Desk" + "top") not in text
    assert "COM" not in text
    assert "RTE_DEVICE_STDPERIPH_GPIO" in rte_text
    assert "RTE_DEVICE_STDPERIPH_RCC" in rte_text
    assert "RTE_DEVICE_STDPERIPH_USART" in rte_text

    included_sources = set(re.findall(r"<FileName>([^<]+)</FileName>", text))
    assert included_sources == {
        "ground_sensors.c",
        "main_ground_sensors_bringup.c",
        "openrf1_status.c",
        "platform_ground_sensors_bringup.c",
        "telemetry_ground_sensors_bringup.c",
    }
    for forbidden in ("bh1750.c", "bmp280.c", "mpu6050.c", "hcsr04.c", "soft_i2c.c", "main_full_hardware.c", "rplidar_c1_transport.c", "esp32_link.c"):
        assert forbidden not in text


def test_documentation_locks_ground_sensor_contract_without_physical_claims():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (DOC_PATH, WIRING_DOC, HARDWARE_LOCK)
    )
    for snippet in (
        "AUTHORITATIVE_VENDOR_DOCUMENTED",
        "signal 1 / X1 / PC4",
        "signal 2 / X2 / PC5",
        "signal 3 / X3 / PB0",
        "signal 4 / X4 is unused",
        "schematic says PC14",
        "old example maps X4 to PB1",
        "do not power the TCRT modules from the connector's 5 V pin",
        "Do not connect Hall S directly to PB0.",
        "10 kOhm",
        "15 kOhm",
        "do not share one VCC rail",
        "floating input",
        "PHYSICAL_VERIFICATION_REQUIRED",
        "SOFTWARE_READY",
        "raw GPIO values are not semantic detection states",
    ):
        assert snippet in combined

    for forbidden_claim in (
        "PHYSICAL_EVIDENCE_VERIFIED",
        "left TCRT active polarity is verified",
        "right TCRT active polarity is verified",
        "Hall active polarity is verified",
    ):
        assert forbidden_claim not in DOC_PATH.read_text(encoding="utf-8")


def test_generated_artifact_exclusions_and_privacy_rules():
    ignore = GITIGNORE.read_text(encoding="utf-8")
    assert "firmware/openrf1/keil/Objects_GroundSensors_Bringup/" in ignore
    assert "firmware/openrf1/keil/Objects_HCSR04_Bringup/" in ignore

    tracked_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (
            DOC_PATH,
            KEIL_PROJECT,
            RTE_COMPONENTS,
            BRINGUP_ROOT / "board_config.h",
            BRINGUP_ROOT / "platform_ground_sensors_bringup.c",
            REPO_ROOT / "tools" / "audit_phase32f.py",
        )
        if path.exists()
    )
    assert "C:\\Users" not in tracked_text
    assert ("Desk" + "top") not in tracked_text
    assert re.search(r"\bCOM[0-9]{1,3}\b", tracked_text) is None
