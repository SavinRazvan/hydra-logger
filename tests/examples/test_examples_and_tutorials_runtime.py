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
TUTORIALS_DIR = EXAMPLES_DIR / "tutorials"

EXAMPLE_SCRIPTS = [
    "01_format_control.py",
    "02_destination_control.py",
    "03_extension_control.py",
    "04_runtime_control.py",
    "05_custom_configurations.py",
    "06_basic_colored_logging.py",
    "07_multi_layer_colored_logging.py",
    "08_mixed_console_file_output.py",
    "09_all_logger_types_colors.py",
    "10_disable_colors.py",
    "11_quick_start_basic.py",
    "12_quick_start_async.py",
    "13_extension_system_example.py",
    "14_class_based_logging.py",
    "15_eda_microservices_patterns.py",
    "16_multi_layer_web_app.py",
]

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
]


@pytest.mark.parametrize("script_name", EXAMPLE_SCRIPTS)
def test_examples_execute_without_runtime_errors(script_name: str, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    runpy.run_path(str(EXAMPLES_DIR / script_name), run_name="__main__")


@pytest.mark.parametrize("script_name", TUTORIAL_SCRIPTS)
def test_tutorials_execute_without_runtime_errors(script_name: str, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    runpy.run_path(str(TUTORIALS_DIR / script_name), run_name="__main__")
