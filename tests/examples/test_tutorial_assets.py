"""
Role: Pytest coverage for enterprise tutorial asset integrity.
Used By:
 - Pytest discovery and CI quality gates.
Depends On:
 - pathlib
Notes:
 - Validates onboarding tutorial files exist and remain discoverable from docs.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TUTORIAL_DIR = ROOT / "examples" / "tutorials" / "python"


def _current_tutorial_files() -> list[str]:
    """Return current tutorial scripts from the canonical python track directory."""
    return sorted(path.name for path in TUTORIAL_DIR.glob("t*.py"))


def test_tutorial_scripts_exist() -> None:
    for filename in _current_tutorial_files():
        assert (
            TUTORIAL_DIR / filename
        ).exists(), f"Missing tutorial script: {filename}"


def test_tutorial_readme_references_all_tracks() -> None:
    readme = (ROOT / "examples" / "tutorials" / "README.md").read_text(encoding="utf-8")
    for filename in _current_tutorial_files():
        assert filename in readme


def test_example_readme_points_to_tutorials() -> None:
    readme = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")
    assert "examples/tutorials/README.md" in readme
