"""
Role: Regression guard for logger lifecycle memory/task/queue leaks.
Used By:
 - Pytest discovery and release readiness quality gates.
Depends On:
 - asyncio
 - gc
 - os
 - hydra_logger
Notes:
 - Uses configurable thresholds to stay strict but practical across environments.
"""

from __future__ import annotations

import asyncio
import gc
import os
import resource
from typing import Any

from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer
from hydra_logger.loggers.async_logger import AsyncLogger
from hydra_logger.loggers.composite_logger import CompositeAsyncLogger, CompositeLogger
from hydra_logger.loggers.sync_logger import SyncLogger


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name, str(default)).strip()
    try:
        return float(value)
    except ValueError:
        return default


LEAK_CYCLES = max(1, _env_int("HYDRA_LEAK_CYCLES", 25))
TASK_TOLERANCE = max(0, _env_int("HYDRA_LEAK_TASK_TOLERANCE", 0))
QUEUE_TOLERANCE = max(0, _env_int("HYDRA_LEAK_QUEUE_TOLERANCE", 0))
RSS_THRESHOLD_MB = max(1.0, _env_float("HYDRA_LEAK_RSS_THRESHOLD_MB", 64.0))
RSS_THRESHOLD_BYTES = int(RSS_THRESHOLD_MB * 1024 * 1024)


def _quiet_config(*, queue_mode: bool = False) -> LoggingConfig:
    extensions: dict[str, Any] = {}
    if queue_mode:
        extensions["async_runtime"] = {
            "mode": "queue",
            "worker_count": 1,
            "max_queue_size": 256,
            "overflow_policy": "drop_newest",
        }
    return LoggingConfig(
        layers={
            "default": LogLayer(
                level="INFO",
                destinations=[LogDestination(type="null")],
            )
        },
        extensions=extensions,
    )


def _rss_bytes() -> int:
    # ru_maxrss is KB on Linux and bytes on macOS.
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if usage < 1024 * 1024:
        return int(usage)
    return int(usage * 1024)


def _active_non_current_tasks() -> int:
    current = asyncio.current_task()
    return sum(
        1
        for task in asyncio.all_tasks()
        if task is not current and not task.done() and not task.cancelled()
    )


def _extract_queue_sizes(logger: Any) -> dict[str, int]:
    sizes: dict[str, int] = {}
    health = getattr(logger, "get_health_status", lambda: {})()
    if isinstance(health, dict):
        if "async_queue_size" in health:
            sizes["health.async_queue_size"] = int(health["async_queue_size"])
        if "pending_deferred_closes" in health:
            sizes["health.pending_deferred_closes"] = int(
                health["pending_deferred_closes"]
            )

    for attr in ("_async_record_queue", "_overflow_queue", "_message_queue"):
        queue_obj = getattr(logger, attr, None)
        if queue_obj is not None and hasattr(queue_obj, "qsize"):
            sizes[f"{attr}.qsize"] = int(queue_obj.qsize())

    for attr in ("_async_worker_tasks", "_worker_tasks", "_deferred_close_tasks"):
        task_group = getattr(logger, attr, None)
        if task_group is None:
            continue
        try:
            sizes[f"{attr}.len"] = len(task_group)
        except TypeError:
            continue
    return sizes


def _assert_queues_drained(logger: Any, label: str) -> None:
    sizes = _extract_queue_sizes(logger)
    offenders = {key: value for key, value in sizes.items() if value > QUEUE_TOLERANCE}
    assert offenders == {}, f"{label} queues/tasks not drained: {offenders}"


async def _run_sync_logger_cycles(cycles: int) -> None:
    baseline = _active_non_current_tasks()
    for index in range(cycles):
        logger = SyncLogger(config=_quiet_config())
        logger.info(f"sync leak cycle {index}")
        logger.close()
        _assert_queues_drained(logger, "SyncLogger")
        await asyncio.sleep(0)
    await asyncio.sleep(0)
    final = _active_non_current_tasks()
    assert final <= baseline + TASK_TOLERANCE, (
        f"SyncLogger task leak: baseline={baseline}, final={final}, "
        f"tolerance={TASK_TOLERANCE}"
    )


async def _run_async_logger_cycles(cycles: int) -> None:
    baseline = _active_non_current_tasks()
    for index in range(cycles):
        logger = AsyncLogger(config=_quiet_config(queue_mode=True))
        await logger.log_async("INFO", f"async leak cycle {index}")
        await logger.aclose()
        _assert_queues_drained(logger, "AsyncLogger")
        await asyncio.sleep(0)
    await asyncio.sleep(0)
    final = _active_non_current_tasks()
    assert final <= baseline + TASK_TOLERANCE, (
        f"AsyncLogger task leak: baseline={baseline}, final={final}, "
        f"tolerance={TASK_TOLERANCE}"
    )


async def _run_composite_logger_cycles(cycles: int) -> None:
    baseline = _active_non_current_tasks()
    for index in range(cycles):
        logger = CompositeLogger(config=_quiet_config())
        logger.info(f"composite leak cycle {index}")
        logger.close()
        _assert_queues_drained(logger, "CompositeLogger")
        await asyncio.sleep(0)
    await asyncio.sleep(0)
    final = _active_non_current_tasks()
    assert final <= baseline + TASK_TOLERANCE, (
        f"CompositeLogger task leak: baseline={baseline}, final={final}, "
        f"tolerance={TASK_TOLERANCE}"
    )


async def _run_composite_async_logger_cycles(cycles: int) -> None:
    baseline = _active_non_current_tasks()
    for index in range(cycles):
        logger = CompositeAsyncLogger(
            config=_quiet_config(),
            components=[],
            use_direct_io=True,
        )
        await logger.log("INFO", f"composite async leak cycle {index}")
        await logger.aclose()
        _assert_queues_drained(logger, "CompositeAsyncLogger")
        await asyncio.sleep(0)
    await asyncio.sleep(0)
    final = _active_non_current_tasks()
    assert final <= baseline + TASK_TOLERANCE, (
        f"CompositeAsyncLogger task leak: baseline={baseline}, final={final}, "
        f"tolerance={TASK_TOLERANCE}"
    )


def _assert_rss_growth_within_threshold(before: int, after: int, label: str) -> None:
    growth = max(0, after - before)
    assert growth <= RSS_THRESHOLD_BYTES, (
        f"{label} RSS growth exceeded threshold: growth={growth} bytes, "
        f"threshold={RSS_THRESHOLD_BYTES} bytes ({RSS_THRESHOLD_MB:.1f} MB)"
    )


def test_memory_leak_regressions_for_all_logger_types() -> None:
    before = _rss_bytes()

    asyncio.run(_run_sync_logger_cycles(LEAK_CYCLES))
    gc.collect()
    after_sync = _rss_bytes()
    _assert_rss_growth_within_threshold(before, after_sync, "SyncLogger")

    asyncio.run(_run_async_logger_cycles(LEAK_CYCLES))
    gc.collect()
    after_async = _rss_bytes()
    _assert_rss_growth_within_threshold(after_sync, after_async, "AsyncLogger")

    asyncio.run(_run_composite_logger_cycles(LEAK_CYCLES))
    gc.collect()
    after_composite = _rss_bytes()
    _assert_rss_growth_within_threshold(after_async, after_composite, "CompositeLogger")

    asyncio.run(_run_composite_async_logger_cycles(LEAK_CYCLES))
    gc.collect()
    after_composite_async = _rss_bytes()
    _assert_rss_growth_within_threshold(
        after_composite,
        after_composite_async,
        "CompositeAsyncLogger",
    )
