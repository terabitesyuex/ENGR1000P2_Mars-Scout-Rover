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


def test_validation_rejects_concrete_unverified_gpio() -> None:
    validator, contents, firmware_sources = loaded_repository_texts()
    contents["HARDWARE_LOCK.md"] = contents["HARDWARE_LOCK.md"].replace(
        "Selected ESP32 RX pin: UNSET",
        "Selected ESP32 RX pin: GPIO20",
    )

    errors = validator.validate_text_contents(contents, firmware_sources)

    assert any("unverified RX pin" in error for error in errors)
