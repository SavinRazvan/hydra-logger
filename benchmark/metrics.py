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
from typing import Any


def messages_per_second(total_messages: int, duration: float) -> float:
    """Safely compute throughput from message count and elapsed duration."""
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

    while iterations < min_iterations or (time.perf_counter() - start_time < min_duration_seconds):
        logger.log_batch(messages)
        total_messages += len(messages)
        iterations += 1

    flush_sync(logger)
    end_time = time.perf_counter()
    duration = end_time - start_time
    return total_messages, duration, messages_per_second(total_messages, duration)


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

    while iterations < min_iterations or (time.perf_counter() - start_time < min_duration_seconds):
        await logger.log_batch(messages)
        total_messages += len(messages)
        iterations += 1

    await flush_async(logger)
    end_time = time.perf_counter()
    duration = end_time - start_time
    return total_messages, duration, messages_per_second(total_messages, duration)
