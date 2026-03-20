"""
Role: Tests for `examples/tutorials/utility` (notebook bootstrap helpers).
Used By:
 - Pytest discovery / CI.
Depends On:
 - pathlib
 - sys
Notes:
 - Imports utility via the same path layout notebooks use.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TUTORIALS = ROOT / "examples" / "tutorials"


def _import_utility():
    s = str(TUTORIALS)
    if s not in sys.path:
        sys.path.insert(0, s)
    import utility  # noqa: WPS433 — intentional dynamic path

    return utility


def test_utility_find_repo_root_matches_tests_layout() -> None:
    utility = _import_utility()
    assert utility.find_repo_root(ROOT) == ROOT


def test_utility_tutorial_paths() -> None:
    utility = _import_utility()
    cfg = utility.tutorial_config_path("base_default.yaml", repo_root=ROOT)
    logs = utility.tutorial_logs_dir(repo_root=ROOT)
    assert cfg == ROOT / "examples" / "config" / "base_default.yaml"
    assert logs == ROOT / "examples" / "logs" / "tutorials"
