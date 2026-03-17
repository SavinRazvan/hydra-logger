"""
Role: Shared benchmark metric calculation helpers.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - asyncio
 - time
 - typing
Notes:
 - Keeps throughput calculations centralized for consistency.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
import math
import statistics
from typing import Any

from benchmark.dev_logging import get_logger


_logger = get_logger(__name__)


def summarize_samples(values: list[float]) -> dict[str, float]:
    """Return median/p95/cv summary for numeric sample lists."""
    cleaned = [float(value) for value in values if math.isfinite(float(value))]
    if not cleaned:
        return {"median": 0.0, "p95": 0.0, "cv": 0.0, "min": 0.0, "max": 0.0}
    ordered = sorted(cleaned)
    median = statistics.median(ordered)
    p95_index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * 0.95) - 1))
    p95 = ordered[p95_index]
    mean = statistics.mean(ordered)
    stdev = statistics.pstdev(ordered) if len(ordered) > 1 else 0.0
    cv = (stdev / mean) * 100.0 if mean > 0 else 0.0
    return {
        "median": median,
        "p95": p95,
        "cv": cv,
        "min": ordered[0],
        "max": ordered[-1],
    }


def validate_sample_duration(
    *, section: str, duration: float, min_duration_seconds: float
) -> str | None:
    """Validate duration has enough sample time for meaningful comparison."""
    if min_duration_seconds <= 0:
        return None
    if duration < min_duration_seconds:
        return (
            f"{section}.duration: sample too short ({duration:.6f}s), "
            f"requires >= {min_duration_seconds:.6f}s"
        )
    return None


def messages_per_second(total_messages: int, duration: float) -> float:
    """Safely compute throughput from message count and elapsed duration."""
    if total_messages < 0:
        _logger.error("Negative total_messages provided: %s", total_messages)
        raise ValueError("total_messages must be >= 0")
    if duration <= 0:
        return 0.0
    return total_messages / duration


def measure_sync_batch_throughput(
    *,
    logger: Any,
    messages: list[tuple[str, str, dict[str, Any]]],
    flush_sync: Callable[[Any], None],
    min_duration_seconds: float = 0.25,
    min_iterations: int = 5,
) -> tuple[int, float, float]:
    """Measure sync batch throughput over multiple iterations for stable results."""
    total_messages = 0
    iterations = 0
    start_time = time.perf_counter()

    try:
        while iterations < min_iterations or (
            time.perf_counter() - start_time < min_duration_seconds
        ):
            logger.log_batch(messages)
            total_messages += len(messages)
            iterations += 1

        flush_sync(logger)
        end_time = time.perf_counter()
        duration = end_time - start_time
        return total_messages, duration, messages_per_second(total_messages, duration)
    except Exception:
        _logger.exception(
            "Sync batch throughput measurement failed (min_iterations=%s)",
            min_iterations,
        )
        raise


async def measure_async_batch_throughput(
    *,
    logger: Any,
    messages: list[tuple[str, str, dict[str, Any]]],
    flush_async: Callable[[Any], Awaitable[None]],
    min_duration_seconds: float = 0.25,
    min_iterations: int = 5,
) -> tuple[int, float, float]:
    """Measure async batch throughput over multiple iterations for stable results."""
    total_messages = 0
    iterations = 0
    start_time = time.perf_counter()

    try:
        while iterations < min_iterations or (
            time.perf_counter() - start_time < min_duration_seconds
        ):
            await logger.log_batch(messages)
            total_messages += len(messages)
            iterations += 1

        await flush_async(logger)
        end_time = time.perf_counter()
        duration = end_time - start_time
        return total_messages, duration, messages_per_second(total_messages, duration)
    except Exception:
        _logger.exception(
            "Async batch throughput measurement failed (min_iterations=%s)",
            min_iterations,
        )
        raise


def _validate_rate(
    *,
    numerator: float,
    duration: float,
    reported_rate: float,
    label: str,
    violations: list[str],
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-9,
) -> None:
    expected = messages_per_second(int(numerator), duration) if numerator >= 0 else 0.0
    if not math.isfinite(reported_rate):
        violations.append(f"{label}: reported rate is not finite ({reported_rate!r})")
        return
    if not math.isclose(reported_rate, expected, rel_tol=rel_tol, abs_tol=abs_tol):
        violations.append(
            f"{label}: expected {expected:.12f} but found {reported_rate:.12f}"
        )


def validate_result_invariants(results: dict[str, Any]) -> list[str]:
    """Validate benchmark math and counting invariants."""
    violations: list[str] = []

    def _validate_counting_and_timing(section: dict[str, Any], label_prefix: str) -> None:
        expected = section.get("expected_emitted")
        actual = section.get("actual_emitted")
        written = section.get("written_lines")
        written_observed = bool(section.get("written_lines_observed", True))
        if expected is not None and actual is not None and int(expected) != int(actual):
            violations.append(
                f"{label_prefix}.actual_emitted: expected {int(expected)} but found {int(actual)}"
            )
        strict_file_evidence = bool(section.get("strict_file_evidence", True))
        if strict_file_evidence and not written_observed:
            violations.append(f"{label_prefix}.written_lines_observed: expected True")
        if (
            written_observed
            and written is not None
            and actual is not None
            and int(written) != int(actual)
        ):
            violations.append(
                f"{label_prefix}.written_lines: expected {int(actual)} but found {int(written)}"
            )
        warmup = section.get("warmup_duration")
        flush = section.get("flush_duration")
        measured = section.get("measured_duration")
        duration = section.get("duration")
        if warmup is not None and float(warmup) < 0:
            violations.append(f"{label_prefix}.warmup_duration: negative value {float(warmup)}")
        if flush is not None and float(flush) < 0:
            violations.append(f"{label_prefix}.flush_duration: negative value {float(flush)}")
        if measured is not None and duration is not None and not math.isclose(
            float(measured),
            float(duration),
            rel_tol=1e-6,
            abs_tol=1e-9,
        ):
            violations.append(
                f"{label_prefix}.measured_duration: expected {float(duration):.12f} "
                f"but found {float(measured):.12f}"
            )

    for key in ("sync_logger", "async_logger"):
        section = results.get(key, {})
        if not isinstance(section, dict):
            continue
        total = float(section.get("total_messages", 0))
        duration = float(section.get("individual_duration", 0))
        rate = float(section.get("individual_messages_per_second", 0))
        _validate_rate(
            numerator=total,
            duration=duration,
            reported_rate=rate,
            label=f"{key}.individual_messages_per_second",
            violations=violations,
        )

    composite = results.get("composite_logger", {})
    if isinstance(composite, dict):
        _validate_rate(
            numerator=float(composite.get("total_messages", 0)),
            duration=float(composite.get("individual_duration", 0)),
            reported_rate=float(composite.get("individual_messages_per_second", 0)),
            label="composite_logger.individual_messages_per_second",
            violations=violations,
        )
        _validate_rate(
            numerator=float(composite.get("small_batch_total_messages", 0)),
            duration=float(composite.get("small_batch_duration", 0)),
            reported_rate=float(composite.get("small_batch_messages_per_second", 0)),
            label="composite_logger.small_batch_messages_per_second",
            violations=violations,
        )
        _validate_rate(
            numerator=float(composite.get("batch_total_messages", 0)),
            duration=float(composite.get("batch_duration", 0)),
            reported_rate=float(composite.get("batch_messages_per_second", 0)),
            label="composite_logger.batch_messages_per_second",
            violations=violations,
        )

    composite_async = results.get("composite_async_logger", {})
    if isinstance(composite_async, dict):
        _validate_rate(
            numerator=float(composite_async.get("total_messages", 0)),
            duration=float(composite_async.get("individual_duration", 0)),
            reported_rate=float(composite_async.get("individual_messages_per_second", 0)),
            label="composite_async_logger.individual_messages_per_second",
            violations=violations,
        )
        _validate_rate(
            numerator=float(composite_async.get("batch_total_messages", 0)),
            duration=float(composite_async.get("batch_duration", 0)),
            reported_rate=float(composite_async.get("batch_messages_per_second", 0)),
            label="composite_async_logger.batch_messages_per_second",
            violations=violations,
        )

    configurations = results.get("configurations", {})
    if isinstance(configurations, dict):
        for config_name, config_result in configurations.items():
            if not isinstance(config_result, dict):
                continue
            if not isinstance(config_result.get("messages_per_second"), (int, float)):
                continue
            _validate_rate(
                numerator=float(config_result.get("total_messages", 0)),
                duration=float(config_result.get("duration", 0)),
                reported_rate=float(config_result.get("messages_per_second", 0)),
                label=f"configurations.{config_name}.messages_per_second",
                violations=violations,
            )

    for key in ("file_writing", "async_file_writing"):
        section = results.get(key, {})
        if not isinstance(section, dict):
            continue
        _validate_counting_and_timing(section, key)
        total = float(section.get("total_messages", 0))
        duration = float(section.get("duration", 0))
        msg_rate = float(section.get("messages_per_second", 0))
        bytes_written = float(section.get("bytes_written", 0))
        byte_rate = float(section.get("bytes_per_second", 0))
        _validate_rate(
            numerator=total,
            duration=duration,
            reported_rate=msg_rate,
            label=f"{key}.messages_per_second",
            violations=violations,
        )
        _validate_rate(
            numerator=bytes_written,
            duration=duration,
            reported_rate=byte_rate,
            label=f"{key}.bytes_per_second",
            violations=violations,
        )

    concurrent = results.get("concurrent", {})
    if isinstance(concurrent, dict):
        _validate_rate(
            numerator=float(concurrent.get("total_messages", 0)),
            duration=float(concurrent.get("total_duration", 0)),
            reported_rate=float(concurrent.get("total_messages_per_second", 0)),
            label="concurrent.total_messages_per_second",
            violations=violations,
        )

    async_concurrent = results.get("async_concurrent", {})
    if isinstance(async_concurrent, dict):
        scaling = async_concurrent.get("scaling", {})
        if isinstance(scaling, dict):
            for key, row in scaling.items():
                if not isinstance(row, dict):
                    continue
                _validate_rate(
                    numerator=float(row.get("total_messages", 0)),
                    duration=float(row.get("total_duration", 0)),
                    reported_rate=float(row.get("total_messages_per_second", 0)),
                    label=f"async_concurrent.scaling.{key}.total_messages_per_second",
                    violations=violations,
                )

    parallel_workers = results.get("parallel_workers", {})
    if isinstance(parallel_workers, dict):
        scaling = parallel_workers.get("scaling", {})
        if isinstance(scaling, dict):
            for key, row in scaling.items():
                if not isinstance(row, dict):
                    continue
                _validate_rate(
                    numerator=float(row.get("total_messages", 0)),
                    duration=float(row.get("total_duration", 0)),
                    reported_rate=float(row.get("total_messages_per_second", 0)),
                    label=f"parallel_workers.scaling.{key}.total_messages_per_second",
                    violations=violations,
                )

    return violations
