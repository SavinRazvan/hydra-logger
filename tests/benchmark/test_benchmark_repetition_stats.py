"""
Role: Unit tests for benchmark repetition/statistics helpers.
Used By:
 - Pytest benchmark reliability validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Validates median/p95/cv and minimum sample-duration guard behavior.
"""

from __future__ import annotations

from benchmark.metrics import summarize_samples, validate_sample_duration


def test_summarize_samples_returns_expected_statistics() -> None:
    summary = summarize_samples([10.0, 20.0, 30.0, 40.0, 50.0])
    assert summary["median"] == 30.0
    assert summary["p95"] == 50.0
    assert summary["min"] == 10.0
    assert summary["max"] == 50.0
    assert summary["cv"] > 0.0


def test_summarize_samples_handles_single_and_empty_inputs() -> None:
    single = summarize_samples([7.0])
    assert single["median"] == 7.0
    assert single["p95"] == 7.0
    assert single["cv"] == 0.0

    empty = summarize_samples([])
    assert empty["median"] == 0.0
    assert empty["p95"] == 0.0
    assert empty["cv"] == 0.0


def test_validate_sample_duration_reports_short_samples() -> None:
    violation = validate_sample_duration(
        section="sync_logger",
        duration=0.0001,
        min_duration_seconds=0.001,
    )
    assert violation is not None
    assert "sample too short" in violation

    no_violation = validate_sample_duration(
        section="sync_logger",
        duration=0.1,
        min_duration_seconds=0.001,
    )
    assert no_violation is None
