"""
Role: Tests for hydra_logger.utils.slo_metrics SLI helpers.
Used By:
 - Pytest discovery and CI coverage gates.
Depends On:
 - hydra_logger
Notes:
 - Validates counter and percentile helpers used for SLO dashboards.
"""

from hydra_logger.utils import slo_metrics


def test_slo_metrics_counters_and_reset() -> None:
    slo_metrics.reset_metrics()
    slo_metrics.record_dropped_log("t")
    slo_metrics.record_handler_error("h")
    slo_metrics.record_queue_saturation("q")
    snap = slo_metrics.snapshot()
    assert snap["dropped_logs"] == 1
    assert snap["handler_errors"] == 1
    assert snap["queue_saturation_events"] == 1
    slo_metrics.reset_metrics()
    snap2 = slo_metrics.snapshot()
    assert snap2["dropped_logs"] == 0


def test_slo_metrics_flush_latency_percentiles() -> None:
    slo_metrics.reset_metrics()
    for i in range(10):
        slo_metrics.record_flush_latency("t", float(i) * 0.01)
    pct = slo_metrics.flush_latency_percentiles()
    assert pct["count"] == 10.0
    assert pct["p99"] >= pct["p95"]
    assert pct["p95"] > 0


def test_slo_metrics_percentile_edge_cases() -> None:
    assert slo_metrics.percentile([], 50) == 0.0
    assert slo_metrics.percentile([1.0], 50) == 1.0


def test_slo_metrics_trim_and_percentile_boundaries() -> None:
    slo_metrics.reset_metrics()
    for idx in range(10_002):
        slo_metrics.record_flush_latency("trim", float(idx))

    percentiles = slo_metrics.flush_latency_percentiles()
    assert percentiles["count"] == 5001.0
    assert slo_metrics.percentile([1.0, 2.0, 3.0], 0) == 1.0
    assert slo_metrics.percentile([1.0, 2.0, 3.0], 100) == 3.0

    slo_metrics.reset_metrics()
    assert slo_metrics.flush_latency_percentiles() == {
        "p95": 0.0,
        "p99": 0.0,
        "count": 0.0,
    }
