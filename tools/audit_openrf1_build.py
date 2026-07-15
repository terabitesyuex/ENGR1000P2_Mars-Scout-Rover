"""Audit OpenRF1 Phase 3.2A build prerequisites without building or flashing."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


REQUIRED_APP_FILES = (
    "firmware/openrf1/README.md",
    "firmware/openrf1/app/board_config.h",
    "firmware/openrf1/app/soft_i2c.h",
    "firmware/openrf1/app/soft_i2c.c",
    "firmware/openrf1/app/bh1750.h",
    "firmware/openrf1/app/bh1750.c",
    "firmware/openrf1/app/telemetry.h",
    "firmware/openrf1/app/telemetry.c",
    "firmware/openrf1/app/main.h",
    "firmware/openrf1/app/main.c",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-output", type=Path, required=True)
    parser.add_argument("--manual-output", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    build_text = build_audit_text(repo_root)
    manual_text = manual_status_text()
    _write(args.build_output, build_text)
    _write(args.manual_output, manual_text)
    print(f"wrote {args.build_output}")
    print(f"wrote {args.manual_output}")
    return 0


def build_audit_text(repo_root: Path) -> str:
    missing = [relative for relative in REQUIRED_APP_FILES if not (repo_root / relative).exists()]
    keil_projects = _find(repo_root / "firmware", ("*.uvproj", "*.uvprojx"))
    startup_files = _find(repo_root / "firmware", ("startup_stm32f10x_hd.s",))
    spl_headers = _find(repo_root / "firmware", ("stm32f10x.h",))
    uv4 = shutil.which("UV4.exe") or shutil.which("UV4")

    lines = [
        "OpenRF1 Phase 3.2A build audit",
        "build_status: MANUAL_ACTION_REQUIRED",
        "hardware_access: none",
        "flash_attempted: no",
        "serial_port_opened: no",
        f"required_app_files_present: {not missing}",
    ]
    if missing:
        lines.append("missing_app_files:")
        lines.extend(f"  - {item}" for item in missing)
    lines.extend(
        [
            f"keil_project_found: {bool(keil_projects)}",
            f"startup_stm32f10x_hd_found: {bool(startup_files)}",
            f"stm32f10x_header_found: {bool(spl_headers)}",
            f"uv4_on_path: {bool(uv4)}",
            "note: repository does not contain a complete licensed Keil/SPL build tree.",
            "manual_action: add app files to the vendor OpenRF1 STM32F103RC Keil project and build without flashing.",
        ]
    )
    return "\n".join(lines) + "\n"


def manual_status_text() -> str:
    return "\n".join(
        [
            "OpenRF1 Phase 3.2A manual hardware status",
            "board_identity: CONFIRMED by user request",
            "mcu_identity: CONFIRMED by user request",
            "planned_wiring: USER-CONFIRMED, NOT ELECTRICALLY TESTED",
            "bh1750_address_0x23: CONFIGURED BY ADDR-TO-GND PLAN, NOT ACK-VERIFIED",
            "keil_build: UNVERIFIED",
            "firmware_flash: UNVERIFIED",
            "serial_com_port: UNVERIFIED",
            "real_lux_readings: UNVERIFIED",
            "hardware_access_by_automation: none",
        ]
    ) + "\n"


def _find(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    if not root.exists():
        return []
    found: list[Path] = []
    for pattern in patterns:
        found.extend(root.rglob(pattern))
    return found


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())
