"""
Role: Drift policy evaluation for benchmark throughput regressions.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - json
 - pathlib
 - statistics
 - typing
Notes:
 - Compares current run throughput against same-profile historical baselines.
"""

from __future__ import annotations

import json
from pathlib import Path
import statistics
from typing import Any


DEFAULT_DRIFT_POLICY: dict[str, Any] = {
    "enabled": False,
    "history_window": 20,
    "min_baseline_runs": 5,
    "max_negative_drift_pct_median": 15.0,
    "max_negative_drift_pct_p95": 25.0,
    "metrics": [
        "sync_logger.individual_messages_per_second",
        "async_logger.individual_messages_per_second",
        "file_writing.messages_per_second",
        "async_file_writing.messages_per_second",
        "concurrent.total_messages_per_second",
    ],
}


def _percentile(values: list[float], percentile: float) -> float:
    """Compute percentile using linear interpolation on sorted values."""
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    if percentile <= 0:
        return min(values)
    if percentile >= 100:
        return max(values)

    ordered = sorted(values)
    position = (len(ordered) - 1) * (percentile / 100.0)
    lower_idx = int(position)
    upper_idx = min(lower_idx + 1, len(ordered) - 1)
    fraction = position - lower_idx
    return ordered[lower_idx] + (ordered[upper_idx] - ordered[lower_idx]) * fraction


def _merge_policy(overrides: dict[str, Any] | None) -> dict[str, Any]:
    policy = dict(DEFAULT_DRIFT_POLICY)
    if isinstance(overrides, dict):
        policy.update(overrides)
    return policy


def _extract_metric(result_payload: dict[str, Any], metric_path: str) -> float | None:
    node: Any = result_payload
    for part in metric_path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    if isinstance(node, (int, float)):
        return float(node)
    return None


def _load_history_payloads(
    *,
    results_dir: Path,
    profile_name: str,
    history_window: int,
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    files = sorted(results_dir.glob("benchmark_*.json"), reverse=True)
    for file_path in files:
        # Exclude convenience copy and malformed artifacts.
        if file_path.name == "benchmark_latest.json":
            continue
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        if metadata.get("profile", "legacy_default") != profile_name:
            continue
        payloads.append(payload)
        if len(payloads) >= max(history_window, 0):
            break
    return payloads


def evaluate_drift_policy(
    *,
    current_results: dict[str, Any],
    results_dir: Path,
    profile_name: str | None,
    policy_overrides: dict[str, Any] | None,
) -> tuple[list[str], dict[str, Any]]:
    """
    Evaluate throughput drift against historical artifacts for the same profile.

    Returns (violations, report). If policy is disabled, violations are empty and
    report contains status=disabled.
    """
    policy = _merge_policy(policy_overrides)
    normalized_profile = profile_name or "legacy_default"

    report: dict[str, Any] = {
        "enabled": bool(policy["enabled"]),
        "profile": normalized_profile,
        "status": "disabled",
        "history_window": int(policy["history_window"]),
        "min_baseline_runs": int(policy["min_baseline_runs"]),
        "max_negative_drift_pct_median": float(policy["max_negative_drift_pct_median"]),
        "max_negative_drift_pct_p95": float(policy["max_negative_drift_pct_p95"]),
        "metrics": {},
    }
    if not policy["enabled"]:
        return [], report

    history = _load_history_payloads(
        results_dir=results_dir,
        profile_name=normalized_profile,
        history_window=int(policy["history_window"]),
    )
    report["history_files_considered"] = len(history)

    violations: list[str] = []
    min_runs = int(policy["min_baseline_runs"])
    median_limit = float(policy["max_negative_drift_pct_median"])
    p95_limit = float(policy["max_negative_drift_pct_p95"])
    metric_paths = policy.get("metrics", [])
    if not isinstance(metric_paths, list):
        metric_paths = []

    for metric_path in metric_paths:
        if not isinstance(metric_path, str):
            continue
        current_value = _extract_metric(current_results, metric_path)
        baseline_values: list[float] = []
        for payload in history:
            result_node = payload.get("results", {})
            if not isinstance(result_node, dict):
                continue
            historical = _extract_metric(result_node, metric_path)
            if historical is not None:
                baseline_values.append(historical)

        metric_report: dict[str, Any] = {
            "current": current_value,
            "baseline_count": len(baseline_values),
            "status": "skipped_no_current_metric" if current_value is None else "ok",
        }

        if current_value is None:
            report["metrics"][metric_path] = metric_report
            continue
        if len(baseline_values) < min_runs:
            metric_report["status"] = "skipped_insufficient_baseline"
            report["metrics"][metric_path] = metric_report
            continue

        baseline_median = statistics.median(baseline_values)
        baseline_p95 = _percentile(baseline_values, 95.0)
        drift_vs_median_pct = (
            ((current_value - baseline_median) / baseline_median) * 100.0
            if baseline_median > 0
            else 0.0
        )
        drift_vs_p95_pct = (
            ((current_value - baseline_p95) / baseline_p95) * 100.0
            if baseline_p95 > 0
            else 0.0
        )

        metric_report.update(
            {
                "baseline_median": baseline_median,
                "baseline_p95": baseline_p95,
                "drift_vs_median_pct": drift_vs_median_pct,
                "drift_vs_p95_pct": drift_vs_p95_pct,
            }
        )

        if drift_vs_median_pct < -median_limit:
            violations.append(
                f"{metric_path}: median drift {drift_vs_median_pct:.2f}% "
                f"exceeds {-median_limit:.2f}% limit"
            )
            metric_report["status"] = "violation_median"
        if drift_vs_p95_pct < -p95_limit:
            violations.append(
                f"{metric_path}: p95 drift {drift_vs_p95_pct:.2f}% "
                f"exceeds {-p95_limit:.2f}% limit"
            )
            metric_report["status"] = "violation_p95"

        report["metrics"][metric_path] = metric_report

    report["status"] = "failed" if violations else "passed"
    return violations, report
