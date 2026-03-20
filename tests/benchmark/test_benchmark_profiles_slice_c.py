"""
Role: Unit tests for benchmark profile tier loading.
Used By:
 - Pytest benchmark profile validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Verifies ci_smoke/pr_gate/nightly profile integration.
"""

from __future__ import annotations

import pytest

from benchmark.performance_benchmark import HydraLoggerBenchmark
from benchmark.profiles import load_profile


def test_load_profile_known_profiles() -> None:
    ci = load_profile("ci_smoke")
    pr = load_profile("pr_gate")
    nightly = load_profile("nightly_truth")

    assert ci["name"] == "ci_smoke"
    assert pr["name"] == "pr_gate"
    assert nightly["name"] == "nightly_truth"
    assert ci["drift_policy"]["enabled"] is False
    assert pr["drift_policy"]["enabled"] is True
    assert nightly["drift_policy"]["enabled"] is True
    assert ci["strict_reliability_guards"] is False
    assert pr["strict_reliability_guards"] is False
    assert nightly["strict_reliability_guards"] is True
    assert ci["write_markdown_reports"] is False
    assert pr["write_markdown_reports"] is False
    assert nightly["write_markdown_reports"] is True


def test_load_profile_unknown_raises() -> None:
    with pytest.raises(ValueError):
        load_profile("missing_profile")


def test_benchmark_init_applies_profile_overrides(tmp_path) -> None:
    bench = HydraLoggerBenchmark(
        save_results=False,
        results_dir=str(tmp_path / "results"),
        profile="ci_smoke",
    )
    assert bench.profile_name == "ci_smoke"
    assert bench.test_config["typical_single_messages"] == 10000
    assert bench.test_config["suite_matrix_workers_tasks"] == [1, 2, 4, 8, 16, 32]
    assert bench.test_config["suite_matrix_messages_per_worker"] == 1000
    assert bench.drift_policy.get("enabled") is False
    assert bench.strict_reliability_guards is False
    assert bench.write_markdown_reports is False
    assert bench.output_matrix_overrides["include_extensions"] is False


def test_benchmark_profile_enabled_sections_applied_when_cli_absent(
    tmp_path, monkeypatch
) -> None:
    def fake_profile(_name):  # type: ignore[no-untyped-def]
        return {
            "enabled_sections": ["sync_logger", "memory"],
            "test_config_overrides": {},
        }

    monkeypatch.setattr("benchmark.performance_benchmark.load_profile", fake_profile)
    bench = HydraLoggerBenchmark(
        save_results=False,
        results_dir=str(tmp_path / "results"),
        profile="custom",
    )
    assert bench.enabled_sections == ["sync_logger", "memory"]


def test_benchmark_cli_sections_override_profile_sections(
    tmp_path, monkeypatch
) -> None:
    def fake_profile(_name):  # type: ignore[no-untyped-def]
        return {
            "enabled_sections": ["sync_logger", "memory"],
            "test_config_overrides": {},
        }

    monkeypatch.setattr("benchmark.performance_benchmark.load_profile", fake_profile)
    bench = HydraLoggerBenchmark(
        save_results=False,
        results_dir=str(tmp_path / "results"),
        profile="custom",
        enabled_sections=["async_logger"],
    )
    assert bench.enabled_sections == ["async_logger"]
