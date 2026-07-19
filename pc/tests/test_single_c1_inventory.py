from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from audit_single_c1_inventory import CURRENT_SOURCES, audit_repo
from rplidar_c1_tools.recording_models import SCHEMA_VERSION, default_sensor_inventory


def test_current_inventory_has_one_physical_c1() -> None:
    inventory = default_sensor_inventory(include_auxiliary=False)
    assert [sensor.sensor_id for sensor in inventory] == ["c1_1"]


def test_authoritative_inventory_sections_do_not_declare_c1_2() -> None:
    for relative in ("AGENTS.md", "README.md", "PROJECT_SPEC.md", "HARDWARE_LOCK.md"):
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "RPLIDAR C1 x2" not in text
        assert "- `c1_2`" not in text


def test_recording_schema_version_remains_v1() -> None:
    assert SCHEMA_VERSION == 1


def test_current_sources_pass_single_c1_audit() -> None:
    assert audit_repo(REPO_ROOT) == []


def test_audit_rejects_new_active_two_c1_claim(tmp_path: Path) -> None:
    for relative in CURRENT_SOURCES:
        source = REPO_ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "\nTwo physical C1 units are available.\n", encoding="utf-8")
    assert any("stale active" in error for error in audit_repo(tmp_path))


def test_version_one_compatibility_id_remains_supported() -> None:
    inventory = default_sensor_inventory(lidar_count=2, include_auxiliary=False)
    assert [sensor.sensor_id for sensor in inventory] == ["c1_1", "c1_2"]
