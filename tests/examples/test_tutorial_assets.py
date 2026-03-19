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
TUTORIAL_DIR = ROOT / "examples" / "tutorials"
TUTORIAL_FILES = [
    "t01_production_quick_start.py",
    "t02_configuration_recipes.py",
    "t03_layers_customization.py",
    "t04_extensions_plugins.py",
    "t05_framework_patterns.py",
    "t06_migration_adoption.py",
    "t07_operational_playbook.py",
    "t08_console_configuration_cookbook.py",
    "t09_levels_columns_date_and_destinations.py",
    "t10_enterprise_profile_config.py",
    "t11_enterprise_policy_layers.py",
    "t12_network_http_typed_destination.py",
    "t13_network_ws_resilient_typed_destination.py",
    "t14_network_local_http_simulation.py",
]


def test_tutorial_scripts_exist() -> None:
    for filename in TUTORIAL_FILES:
        assert (
            TUTORIAL_DIR / filename
        ).exists(), f"Missing tutorial script: {filename}"


def test_tutorial_readme_references_all_tracks() -> None:
    readme = (TUTORIAL_DIR / "README.md").read_text(encoding="utf-8")
    for filename in TUTORIAL_FILES:
        assert filename in readme


def test_example_readme_points_to_tutorials() -> None:
    readme = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")
    assert "examples/tutorials/README.md" in readme
