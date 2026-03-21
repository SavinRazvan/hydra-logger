"""
Role: Tests for `shared/run_all_cli_tutorials.py` discovery and dry-run.
Used By:
 - pytest under `tests/examples/`.
Depends On:
 - examples/tutorials/shared/run_all_cli_tutorials.py
Notes:
 - Avoids executing all tutorials in unit tests (slow + env); validates paths only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    import importlib.util

    path = ROOT / "examples" / "tutorials" / "shared" / "run_all_cli_tutorials.py"
    spec = importlib.util.spec_from_file_location("run_all_cli_tutorials", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def runner_mod():
    return _load_runner()


def test_cli_tutorial_list_has_twenty_scripts(runner_mod) -> None:
    assert len(runner_mod.CLI_TUTORIAL_FILENAMES) == 20


def test_all_cli_scripts_exist_on_disk(runner_mod) -> None:
    root = runner_mod.repo_root_from_here()
    for p in runner_mod.iter_cli_script_paths(root):
        assert p.is_file(), f"missing {p}"


def test_dry_run_returns_zero(runner_mod) -> None:
    assert runner_mod.main(["--dry-run"]) == 0
