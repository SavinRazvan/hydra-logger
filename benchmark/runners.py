"""
Role: Reusable benchmark execution runners.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - asyncio
 - concurrent.futures
 - pathlib
 - time
 - typing
Notes:
 - Keeps suite execution logic out of the CLI/orchestrator module.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import time
from typing import Any, Callable

from benchmark.dev_logging import get_logger
from hydra_logger import getLogger
from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer


_logger = get_logger(__name__)


def parallel_sync_worker(
    bench_logs_dir: str,
    worker_count: int,
    worker_id: int,
    messages_per_worker: int,
) -> int:
    """Process worker for real parallel benchmark throughput."""
    log_path = (
        Path(bench_logs_dir)
        / f"parallel_worker_{worker_count}_{worker_id}_{time.time_ns()}.jsonl"
    )
    config = LoggingConfig(
        default_level="INFO",
        layers={
            "default": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(type="file", path=str(log_path), format="json-lines"),
                ],
            )
        },
    )
    logger_name = f"parallel_worker_{worker_count}_{worker_id}_{time.time_ns()}"
    logger = getLogger(logger_name, logger_type="sync", config=config)
    try:
        for i in range(messages_per_worker):
            logger.info(f"Parallel worker {worker_id} message {i}")
    except Exception:
        _logger.exception(
            "Parallel sync worker failed (workers=%s, worker_id=%s, messages=%s)",
            worker_count,
            worker_id,
            messages_per_worker,
        )
        raise
    finally:
        try:
            if hasattr(logger, "close"):
                logger.close()
        except Exception:
            _logger.exception(
                "Parallel sync worker logger close failed (worker_id=%s)",
                worker_id,
            )
    return messages_per_worker


async def run_async_concurrent_suite(
    *,
    matrix: list[int],
    messages_per_task: int,
    create_logger: Callable[[int], Any],
    flush_async: Callable[[Any], Any],
    close_async: Callable[[Any], Any],
    messages_per_second: Callable[[int, float], float],
) -> dict[str, Any]:
    """Run async-concurrent suite using event-loop task interleaving."""
    scaling: dict[str, Any] = {}

    for task_count in matrix:
        if task_count <= 0:
            _logger.error("Invalid task_count in async suite: %s", task_count)
            raise ValueError("task_count must be >= 1")
        logger = create_logger(task_count)

        async def _task(task_id: int) -> None:
            messages = [
                ("INFO", f"AsyncSuite task={task_id} msg={i}", {})
                for i in range(messages_per_task)
            ]
            await logger.log_batch(messages)

        try:
            start = time.perf_counter()
            await asyncio.gather(*[_task(i) for i in range(task_count)])
            duration = time.perf_counter() - start
            await flush_async(logger)
            total_messages = task_count * messages_per_task
            total_messages_per_second = messages_per_second(total_messages, duration)
        except Exception:
            _logger.exception(
                "Async concurrent suite failed for task_count=%s messages_per_task=%s",
                task_count,
                messages_per_task,
            )
            raise

        scaling[str(task_count)] = {
            "total_messages": total_messages,
            "total_duration": duration,
            "total_messages_per_second": total_messages_per_second,
            "tasks": task_count,
            "messages_per_task": messages_per_task,
        }
        try:
            await close_async(logger)
        except Exception:
            _logger.exception(
                "Async concurrent suite close failed for task_count=%s",
                task_count,
            )
            raise

    return {
        "suite": "async_concurrent",
        "workers_tasks": matrix,
        "messages_per_worker": messages_per_task,
        "scaling": scaling,
        "status": "COMPLETED",
    }


def run_parallel_workers_suite(
    *,
    matrix: list[int],
    messages_per_worker: int,
    bench_logs_dir: Path,
    messages_per_second: Callable[[int, float], float],
) -> dict[str, Any]:
    """Run real process-parallel suite using ProcessPoolExecutor."""
    scaling: dict[str, Any] = {}

    for worker_count in matrix:
        if worker_count <= 0:
            _logger.error("Invalid worker_count in parallel suite: %s", worker_count)
            raise ValueError("worker_count must be >= 1")

        try:
            start = time.perf_counter()
            with ProcessPoolExecutor(max_workers=worker_count) as executor:
                futures = [
                    executor.submit(
                        parallel_sync_worker,
                        str(bench_logs_dir),
                        worker_count,
                        worker_id,
                        messages_per_worker,
                    )
                    for worker_id in range(worker_count)
                ]
                completed_messages = sum(f.result() for f in futures)
            duration = time.perf_counter() - start
            total_messages_per_second = messages_per_second(completed_messages, duration)
        except Exception:
            _logger.exception(
                "Parallel workers suite failed for worker_count=%s",
                worker_count,
            )
            raise

        scaling[str(worker_count)] = {
            "total_messages": completed_messages,
            "total_duration": duration,
            "total_messages_per_second": total_messages_per_second,
            "workers": worker_count,
            "messages_per_worker": messages_per_worker,
        }

    return {
        "suite": "parallel_workers",
        "workers_tasks": matrix,
        "messages_per_worker": messages_per_worker,
        "scaling": scaling,
        "status": "COMPLETED",
    }
