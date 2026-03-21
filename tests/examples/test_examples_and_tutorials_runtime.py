"""
Role: Pytest runtime coverage for example and tutorial scripts.
Used By:
 - Pytest discovery and CI quality gates.
Depends On:
 - pathlib
 - runpy
Notes:
 - Executes each onboarding script under `__main__` to validate runtime behavior.
"""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = ROOT / "examples"
TUTORIALS_DIR = EXAMPLES_DIR / "tutorials" / "cli_tutorials"

TUTORIAL_SCRIPTS = [
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
    "t15_enterprise_network_hardening_playbook.py",
    "t16_enterprise_config_templates_at_scale.py",
    "t17_enterprise_benchmark_comparison_workflow.py",
    "t18_enterprise_bring_your_own_config_benchmark.py",
    "t19_enterprise_nightly_drift_snapshot.py",
    "t20_notebook_hydra_config_onboarding.py",
]


@pytest.mark.parametrize("script_name", TUTORIAL_SCRIPTS)
def test_tutorials_execute_without_runtime_errors(
    script_name: str, monkeypatch
) -> None:
    monkeypatch.chdir(ROOT)
    runpy.run_path(str(TUTORIALS_DIR / script_name), run_name="__main__")
