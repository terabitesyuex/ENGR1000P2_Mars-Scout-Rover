from __future__ import annotations

import hashlib
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


def test_validation_rejects_lost_vehicle_assembly_evidence_boundary() -> None:
    validator, contents, firmware_sources = loaded_repository_texts()
    handoff_path = "docs/near_term_vehicle_bringup_handoff.md"
    contents[handoff_path] = contents[handoff_path].replace(
        "full-rover operation remain `UNVERIFIED`.",
        "full-rover operation is accepted.",
    )

    errors = validator.validate_text_contents(contents, firmware_sources)

    assert any("vehicle assembly evidence boundary" in error for error in errors)


def test_vehicle_assembly_evidence_files_match_recorded_hashes() -> None:
    evidence_root = (
        SUBSYSTEM_ROOT / "evidence" / "hardware" / "vehicle_assembly_2026-07-23"
    )
    expected = {
        "cad_mount_offsets_view1.jpg": "7D12E6D0C27D938F3A5DDF250499E9BFEE242D14B1D2BEA32D7B34858612F9FD",
        "cad_mount_offsets_view2.jpg": "66ECC4CF6906EDBE6620049C7BF69E25A81A3C14AE27B374D54FA4BAB7B5DC73",
        "missing_information_responses.docx": "FD4954180AE16CD45CA0ED9B50642BEF62AD84B1534065FA8E13EA7A34A5AD0C",
        "mpu6050_top_axis.jpg": "721000FC0523687A08D506EAFAE613A3188F0243FFEDECD9F0534FB865FCDFFA",
        "mpu6050_underside_axis.jpg": "C38CBBFD9936B3ECA04E324DF28AEE885A717D8704FE06B5B68BF0B0FA456069",
        "vehicle_front_right.jpg": "78F22F3B9DF5121DD38F8A8C0D446E03FD5C86A49DBA3F346EC11254E0E4D3AA",
        "vehicle_front_ultrasonic.jpg": "86E6C13F0E53F548249B5374517B8E3732FEF8B68879F0AAB7D9B15E9B422142",
        "vehicle_top_front_marked.jpg": "F10157F57A4CE185AA3163A34F64AB51257FDCC95B1D25709218AE52AE57E656",
    }

    for filename, expected_hash in expected.items():
        data = (evidence_root / filename).read_bytes()
        assert hashlib.sha256(data).hexdigest().upper() == expected_hash
