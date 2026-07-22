from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SUBSYSTEM_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SUBSYSTEM_ROOT / "tools" / "validate_hardware_lock.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_hardware_lock", VALIDATOR_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def loaded_repository_texts():
    validator = load_validator()
    read_errors: list[str] = []
    contents = validator._collect_text_contents(SUBSYSTEM_ROOT, read_errors)
    firmware_sources = validator._collect_firmware_sources(SUBSYSTEM_ROOT, read_errors)
    assert read_errors == []
    return validator, contents, firmware_sources


def test_current_repository_hardware_lock_validation_passes() -> None:
    validator = load_validator()

    assert validator.validate_repo(SUBSYSTEM_ROOT) == []


def test_validation_reports_missing_required_hardware_fact() -> None:
    validator, contents, firmware_sources = loaded_repository_texts()
    contents["HARDWARE_LOCK.md"] = contents["HARDWARE_LOCK.md"].replace(
        "RPLIDAR C1M1-R2",
        "RPLIDAR UNKNOWN",
    )

    errors = validator.validate_text_contents(contents, firmware_sources)

    assert any("exact LiDAR model" in error for error in errors)


def test_validation_rejects_invented_uart_gpio() -> None:
    validator, contents, firmware_sources = loaded_repository_texts()
    contents["HARDWARE_LOCK.md"] = contents["HARDWARE_LOCK.md"].replace(
        "USART2 user-UART MCU pins: AUTHORITATIVE_VENDOR_DOCUMENTED as PA2/TX2 and PA3/RX2",
        "USART2 user-UART MCU pins: PA8/TX2 and PA9/RX2 invented",
    )

    errors = validator.validate_text_contents(contents, firmware_sources)

    assert any("documented OpenRF1 USART2 assignment" in error for error in errors)


def test_validation_rejects_lost_battery_safety_boundary() -> None:
    validator, contents, firmware_sources = loaded_repository_texts()
    contents["HARDWARE_LOCK.md"] = contents["HARDWARE_LOCK.md"].replace(
        "39 A is not a confirmed BMS continuous/peak rating",
        "39 A is confirmed for all wiring and protection",
    )

    errors = validator.validate_text_contents(contents, firmware_sources)

    assert any("battery advertised-rate safety boundary" in error for error in errors)


def test_validation_rejects_lost_chinese_assembly_stop_rule() -> None:
    validator, contents, firmware_sources = loaded_repository_texts()
    contents["docs/openrf1_rover_wiring_plan_zh.md"] = contents[
        "docs/openrf1_rover_wiring_plan_zh.md"
    ].replace("禁止未知极性直接插电池", "允许未知极性直接插电池")

    errors = validator.validate_text_contents(contents, firmware_sources)

    assert any("Chinese assembly battery stop rule" in error for error in errors)
