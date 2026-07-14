"""Validate Phase 1 hardware-lock and documentation consistency.

The validator uses only the Python standard library and does not open serial
ports or communicate with LiDAR hardware.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import sys


SUBSYSTEM_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class RequiredText:
    relative_path: str
    text: str
    description: str


REQUIRED_TEXTS: tuple[RequiredText, ...] = (
    RequiredText("HARDWARE_LOCK.md", "RPLIDAR C1M1-R2", "exact LiDAR model"),
    RequiredText("HARDWARE_LOCK.md", "XH2.54-5P", "connector type"),
    RequiredText("HARDWARE_LOCK.md", "Red | VCC", "red wire VCC function"),
    RequiredText("HARDWARE_LOCK.md", "Yellow | LiDAR TX", "yellow wire TX function"),
    RequiredText("HARDWARE_LOCK.md", "Green | LiDAR RX", "green wire RX function"),
    RequiredText("HARDWARE_LOCK.md", "Black | GND", "black wire ground function"),
    RequiredText("HARDWARE_LOCK.md", "4.8 V to 5.2 V", "supply voltage range"),
    RequiredText("HARDWARE_LOCK.md", "5.0 V", "nominal supply voltage"),
    RequiredText("HARDWARE_LOCK.md", "800 mA", "startup current"),
    RequiredText("HARDWARE_LOCK.md", "230 mA", "typical operating current"),
    RequiredText("HARDWARE_LOCK.md", "260 mA", "maximum operating current"),
    RequiredText("HARDWARE_LOCK.md", "150 mV", "supply ripple limit"),
    RequiredText("HARDWARE_LOCK.md", "3.3 V TTL", "UART voltage"),
    RequiredText("HARDWARE_LOCK.md", "460800", "UART baud rate"),
    RequiredText("HARDWARE_LOCK.md", "8 data bits, no parity, 1 stop bit", "UART format"),
    RequiredText("HARDWARE_LOCK.md", "Selected ESP32 RX pin: UNSET", "unverified RX pin"),
    RequiredText("HARDWARE_LOCK.md", "Selected ESP32 TX pin: UNSET", "unverified TX pin"),
    RequiredText("HARDWARE_LOCK.md", "External motor PWM pin: VERIFIED not present", "motor PWM absence"),
    RequiredText("HARDWARE_LOCK.md", "Power-supply model: UNVERIFIED", "unverified supply model"),
    RequiredText("HARDWARE_LOCK.md", "Physical wiring verification date: UNVERIFIED", "unverified wiring date"),
    RequiredText("HARDWARE_LOCK.md", "Device firmware version: UNVERIFIED", "unverified firmware version"),
    RequiredText("HARDWARE_LOCK.md", "Redacted device serial number: UNVERIFIED", "redacted serial status"),
    RequiredText("docs/phase1_hardware_audit.md", "Documentation Conflicts", "conflict log"),
    RequiredText("docs/phase1_hardware_audit.md", "UNVERIFIED Values", "unverified value log"),
    RequiredText("docs/phase1_interface_inventory.md", "LidarInterface", "firmware interface inventory"),
    RequiredText("docs/phase1_interface_inventory.md", "ScanSource", "PC scan-source interface inventory"),
    RequiredText("firmware/include/hardware_profile.h", "kLidarBaudRate = 460800", "firmware baud lock"),
    RequiredText("firmware/include/hardware_profile.h", "kLidarSerialConfig = SERIAL_8N1", "firmware UART format"),
    RequiredText("firmware/include/hardware_profile.h", "#ifndef RPLIDAR_C1_LIDAR_RX_PIN", "RX compile-time guard"),
    RequiredText("firmware/include/hardware_profile.h", "#ifndef RPLIDAR_C1_LIDAR_TX_PIN", "TX compile-time guard"),
    RequiredText("firmware/include/hardware_profile.h", "kHasExternalMotorPwm = false", "no external motor PWM"),
)


FIRMWARE_FORBIDDEN_TEXTS: tuple[str, ...] = (
    "MOTOR_PWM_GPIO",
    "SoftwareSerial",
    "constexpr int kLidarRxPin = 20",
    "constexpr int kLidarTxPin = 21",
)


def validate_repo(repo_root: Path = SUBSYSTEM_ROOT) -> list[str]:
    """Return validation errors for the subsystem root."""
    root = repo_root.resolve()
    errors: list[str] = []
    contents = _collect_text_contents(root, errors)
    firmware_sources = _collect_firmware_sources(root, errors)
    errors.extend(validate_text_contents(contents, firmware_sources))
    return errors


def validate_text_contents(
    contents: Mapping[str, str],
    firmware_sources: Mapping[str, str],
) -> list[str]:
    """Validate already-loaded repository text content."""
    errors: list[str] = []
    for required in REQUIRED_TEXTS:
        content = contents.get(required.relative_path)
        if content is None:
            errors.append(f"{required.relative_path}: file is missing")
        elif required.text not in content:
            errors.append(
                f"{required.relative_path}: missing {required.description}: {required.text!r}"
            )

    _validate_phase_scope(contents, errors)
    _validate_firmware_sources(firmware_sources, errors)
    return errors


def _validate_phase_scope(contents: Mapping[str, str], errors: list[str]) -> None:
    readme = contents.get("README.md")
    project_spec = contents.get("PROJECT_SPEC.md")
    test_plan = contents.get("docs/test_plan.md")
    if readme is not None and "Current Phase 1 is repository audit" not in readme:
        errors.append("README.md: current audit-only Phase 1 scope is not stated")
    if project_spec is not None and "No live LiDAR communication is implemented." not in project_spec:
        errors.append("PROJECT_SPEC.md: Phase 1 live-communication exclusion is missing")
    if test_plan is not None and "python tools\\\\validate_hardware_lock.py" not in test_plan:
        errors.append("docs/test_plan.md: Phase 1 validation command is missing")


def _validate_firmware_sources(
    firmware_sources: Mapping[str, str],
    errors: list[str],
) -> None:
    for relative, content in firmware_sources.items():
        for forbidden in FIRMWARE_FORBIDDEN_TEXTS:
            if forbidden in content:
                errors.append(f"{relative}: forbidden firmware text found: {forbidden!r}")


def _collect_text_contents(root: Path, errors: list[str]) -> dict[str, str]:
    paths = {required.relative_path for required in REQUIRED_TEXTS}
    paths.update({"README.md", "PROJECT_SPEC.md", "docs/test_plan.md"})
    contents: dict[str, str] = {}
    for relative_path in sorted(paths):
        content = _read_text(root, relative_path, errors)
        if content is not None:
            contents[relative_path] = content
    return contents


def _collect_firmware_sources(root: Path, errors: list[str]) -> dict[str, str]:
    firmware_root = root / "firmware"
    if not firmware_root.exists():
        errors.append("firmware: directory is missing")
        return {}
    sources: dict[str, str] = {}
    for path in firmware_root.rglob("*"):
        if path.is_file() and path.suffix in {".h", ".hpp", ".cpp", ".ino"}:
            relative = path.relative_to(root).as_posix()
            content = _read_text(root, relative, errors)
            if content is not None:
                sources[relative] = content
    return sources


def _read_text(root: Path, relative_path: str, errors: list[str]) -> str | None:
    path = root / relative_path
    if not path.exists():
        errors.append(f"{relative_path}: file is missing")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{relative_path}: expected UTF-8 text: {exc}")
        return None


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else SUBSYSTEM_ROOT
    errors = validate_repo(root)
    if errors:
        print("Hardware lock validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Hardware lock validation passed.")
    print(f"Checked subsystem root: {root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
