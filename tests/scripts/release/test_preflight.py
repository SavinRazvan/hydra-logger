"""
Role: Pytest coverage for release preflight orchestration.
Used By:
 - Pytest discovery and release governance validation.
Depends On:
 - importlib
 - pathlib
 - sys
Notes:
 - Exercises pass/fail control flow and optional step selection.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_preflight_module():
    repo_root = Path(__file__).resolve().parents[3]
    script_path = repo_root / "scripts" / "release" / "preflight.py"
    spec = importlib.util.spec_from_file_location("release_preflight", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_steps_include_build_and_benchmark() -> None:
    module = _load_preflight_module()
    steps = module._default_steps(skip_benchmark=False, skip_build=False)
    step_ids = [item.step_id for item in steps]

    assert "version_consistency" in step_ids
    assert "benchmark_pr_gate" in step_ids
    assert "build_dist" in step_ids
    assert "verify_dist_contents" in step_ids


def test_default_steps_can_skip_optional_segments() -> None:
    module = _load_preflight_module()
    steps = module._default_steps(skip_benchmark=True, skip_build=True)
    step_ids = [item.step_id for item in steps]

    assert "benchmark_pr_gate" not in step_ids
    assert "build_dist" not in step_ids
    assert "twine_check" not in step_ids
    assert "verify_dist_contents" not in step_ids


def test_default_steps_include_pypi_parity_when_enabled() -> None:
    module = _load_preflight_module()
    steps = module._default_steps(
        skip_benchmark=True, skip_build=True, pypi_parity=True
    )
    step_ids = [item.step_id for item in steps]
    assert "pypi_parity" in step_ids
    assert step_ids.index("pypi_parity") > step_ids.index("version_consistency")


def test_run_preflight_stops_on_first_failure(monkeypatch) -> None:
    module = _load_preflight_module()
    first = module.PreflightStep("a", "first", ["echo", "1"])
    second = module.PreflightStep("b", "second", ["echo", "2"])
    calls: list[str] = []

    def _fake_run(step, cwd):
        calls.append(step.step_id)
        if step.step_id == "a":
            return module.PreflightResult(step, 1, 0.1, "failed")
        return module.PreflightResult(step, 0, 0.1, "")

    monkeypatch.setattr(module, "_run_step", _fake_run)
    code = module.run_preflight(
        steps=[first, second],
        cwd=Path("."),
        continue_on_failure=False,
    )

    assert code == 1
    assert calls == ["a"]


def test_run_preflight_continue_on_failure_runs_all(monkeypatch) -> None:
    module = _load_preflight_module()
    first = module.PreflightStep("a", "first", ["echo", "1"])
    second = module.PreflightStep("b", "second", ["echo", "2"])
    calls: list[str] = []

    def _fake_run(step, cwd):
        calls.append(step.step_id)
        if step.step_id == "a":
            return module.PreflightResult(step, 1, 0.1, "failed")
        return module.PreflightResult(step, 0, 0.1, "")

    monkeypatch.setattr(module, "_run_step", _fake_run)
    code = module.run_preflight(
        steps=[first, second],
        cwd=Path("."),
        continue_on_failure=True,
    )

    assert code == 1
    assert calls == ["a", "b"]
