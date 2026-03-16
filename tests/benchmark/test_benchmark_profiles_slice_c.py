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
