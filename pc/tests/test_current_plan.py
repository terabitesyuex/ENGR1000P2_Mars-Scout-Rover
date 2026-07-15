from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from validate_current_plan import validate_current_plan


def test_current_plan_authoritative_anchors_are_present():
    assert validate_current_plan(REPO_ROOT) == []
