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
    "docs/test_plan.md",
)


@dataclass(frozen=True, slots=True)
class RequiredSnippet:
    path: str
    snippet: str
    label: str


REQUIRED_SNIPPETS = (
    RequiredSnippet("README.md", "RPLIDAR C1 x2", "two C1 units documented"),
    RequiredSnippet("README.md", "one stable C1", "one-C1 baseline documented"),
    RequiredSnippet("README.md", "simultaneous dual-C1", "dual-C1 optional status documented"),
    RequiredSnippet("README.md", "WiFi", "WiFi baseline documented"),
    RequiredSnippet("README.md", "ROS and a vehicle-mounted Linux computer are not required", "ROS/Linux non-goal documented"),
    RequiredSnippet("PROJECT_SPEC.md", "mandatory requirements", "authoritative requirements section"),
    RequiredSnippet("PROJECT_SPEC.md", "environmental-change indication", "environmental wording documented"),
    RequiredSnippet("PROJECT_SPEC.md", "Reliable real-world dust-storm detection is not claimed", "dust-storm honesty documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "CONFIRMED INVENTORY", "inventory section documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "BH1750 x1", "BH1750 documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "BMP280 x1", "BMP280 documented"),
    RequiredSnippet("HARDWARE_LOCK.md", "exact ESP32 GPIOs: UNVERIFIED", "GPIO remains unverified"),
    RequiredSnippet("docs/architecture.md", "STM32 sensors and rover state", "STM32 data path documented"),
    RequiredSnippet("docs/architecture.md", "ESP32 -> WiFi -> PC", "ESP32 WiFi role documented"),
    RequiredSnippet("docs/architecture.md", "PC visualization/recording", "PC role documented"),
    RequiredSnippet("docs/test_plan.md", "Phase 2.4", "phase order documented"),
    RequiredSnippet("docs/test_plan.md", "Phase 2.5", "next hardware test phase documented"),
    RequiredSnippet("AGENTS.md", "Do not invent GPIO", "future-agent hardware policy documented"),
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
