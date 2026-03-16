"""
Role: Unit tests for benchmark drift policy checks.
Used By:
 - Pytest benchmark drift validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Verifies median/p95 drift gates against profile-scoped history artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.drift import evaluate_drift_policy, load_policy_for_profile


def _write_result(
    *,
    results_dir: Path,
    filename: str,
    profile: str,
    sync_rate: float,
    async_rate: float = 200.0,
) -> None:
    payload = {
        "metadata": {"profile": profile},
        "results": {
            "sync_logger": {"individual_messages_per_second": sync_rate},
            "async_logger": {"individual_messages_per_second": async_rate},
            "file_writing": {"messages_per_second": 300.0},
            "async_file_writing": {"messages_per_second": 250.0},
            "concurrent": {"total_messages_per_second": 400.0},
        },
    }
    (results_dir / filename).write_text(json.dumps(payload), encoding="utf-8")


def test_evaluate_drift_policy_returns_disabled_when_not_enabled(tmp_path) -> None:
    violations, report = evaluate_drift_policy(
        current_results={"sync_logger": {"individual_messages_per_second": 100.0}},
        results_dir=tmp_path,
        profile_name="ci_smoke",
        policy_overrides={"enabled": False},
    )
    assert violations == []
    assert report["status"] == "disabled"


def test_evaluate_drift_policy_skips_when_baseline_history_is_too_small(tmp_path) -> None:
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-00-00.json",
        profile="pr_gate",
        sync_rate=100.0,
    )
    violations, report = evaluate_drift_policy(
        current_results={"sync_logger": {"individual_messages_per_second": 95.0}},
        results_dir=tmp_path,
        profile_name="pr_gate",
        policy_overrides={
            "enabled": True,
            "metrics": ["sync_logger.individual_messages_per_second"],
            "min_baseline_runs": 3,
        },
    )
    assert violations == []
    assert report["status"] == "passed"
    assert (
        report["metrics"]["sync_logger.individual_messages_per_second"]["status"]
        == "skipped_insufficient_baseline"
    )


def test_evaluate_drift_policy_detects_median_and_p95_regression(tmp_path) -> None:
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-00-01.json",
        profile="nightly_truth",
        sync_rate=1000.0,
    )
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-00-02.json",
        profile="nightly_truth",
        sync_rate=1100.0,
    )
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-00-03.json",
        profile="nightly_truth",
        sync_rate=1200.0,
    )

    violations, report = evaluate_drift_policy(
        current_results={"sync_logger": {"individual_messages_per_second": 700.0}},
        results_dir=tmp_path,
        profile_name="nightly_truth",
        policy_overrides={
            "enabled": True,
            "metrics": ["sync_logger.individual_messages_per_second"],
            "min_baseline_runs": 3,
            "max_negative_drift_pct_median": 10.0,
            "max_negative_drift_pct_p95": 15.0,
        },
    )

    assert report["status"] == "failed"
    assert len(violations) == 2
    assert "median drift" in violations[0] or "median drift" in violations[1]
    assert "p95 drift" in violations[0] or "p95 drift" in violations[1]


def test_evaluate_drift_policy_passes_when_current_matches_baseline_band(tmp_path) -> None:
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-00-10.json",
        profile="pr_gate",
        sync_rate=1000.0,
    )
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-00-11.json",
        profile="pr_gate",
        sync_rate=1020.0,
    )
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-00-12.json",
        profile="pr_gate",
        sync_rate=980.0,
    )

    violations, report = evaluate_drift_policy(
        current_results={"sync_logger": {"individual_messages_per_second": 995.0}},
        results_dir=tmp_path,
        profile_name="pr_gate",
        policy_overrides={
            "enabled": True,
            "metrics": ["sync_logger.individual_messages_per_second"],
            "min_baseline_runs": 3,
            "max_negative_drift_pct_median": 10.0,
            "max_negative_drift_pct_p95": 20.0,
        },
    )

    assert violations == []
    assert report["status"] == "passed"
    assert (
        report["metrics"]["sync_logger.individual_messages_per_second"]["status"] == "ok"
    )


def test_load_policy_for_profile_reads_canonical_policy_and_overrides() -> None:
    policy = load_policy_for_profile(
        profile_name="pr_gate",
        policy_overrides={"max_negative_drift_pct_median": 18.0},
    )
    assert policy["enabled"] is True
    assert policy["min_baseline_runs"] == 3
    assert policy["max_negative_drift_pct_median"] == 18.0


def test_evaluate_drift_policy_marks_high_variance_inconclusive(tmp_path) -> None:
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-01-01.json",
        profile="pr_gate",
        sync_rate=100.0,
    )
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-01-02.json",
        profile="pr_gate",
        sync_rate=300.0,
    )
    _write_result(
        results_dir=tmp_path,
        filename="benchmark_2026-03-16_00-01-03.json",
        profile="pr_gate",
        sync_rate=500.0,
    )
    violations, report = evaluate_drift_policy(
        current_results={"sync_logger": {"individual_messages_per_second": 200.0}},
        results_dir=tmp_path,
        profile_name="pr_gate",
        policy_overrides={
            "enabled": True,
            "metrics": ["sync_logger.individual_messages_per_second"],
            "min_baseline_runs": 3,
            "max_variation_cv_pct": 5.0,
        },
    )
    assert violations == []
    assert report["status"] == "inconclusive"
    assert (
        report["metrics"]["sync_logger.individual_messages_per_second"]["status"]
        == "inconclusive_high_variance"
    )
