"""
Role: Pytest coverage for examples run-all runner behavior.
Used By:
 - Pytest discovery and CI quality gates.
Depends On:
 - importlib.util
 - pathlib
Notes:
 - Validates runner diagnostics and failure handling for onboarding reliability.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_runner_module():
    root = Path(__file__).resolve().parents[2]
    script_path = root / "examples" / "run_all_examples.py"
    spec = importlib.util.spec_from_file_location("examples_run_all", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_example_surfaces_missing_module_error(tmp_path: Path) -> None:
    module = _load_runner_module()
    broken_example = tmp_path / "broken_example.py"
    broken_example.write_text("import module_that_does_not_exist\n", encoding="utf-8")

    success, _stdout, stderr, _duration, metadata = module.run_example(broken_example)

    assert success is False
    assert "ModuleNotFoundError" in stderr
    assert metadata["has_errors"] is True


def test_print_example_result_shows_error_hint(capsys) -> None:
    module = _load_runner_module()
    module.print_example_result(
        "dummy.py",
        False,
        "",
        "ModuleNotFoundError: No module named 'hydra_logger'",
        0.02,
        {},
        [],
    )
    output = capsys.readouterr().out
    assert "ERROR:" in output
    assert ".hydra_env/bin/python examples/run_all_examples.py" in output


def test_verify_log_files_returns_empty_without_logs(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_runner_module()
    monkeypatch.chdir(tmp_path)
    found, patterns = module.verify_log_files("t01_production_quick_start.py")
    assert found == []
    assert patterns == []
