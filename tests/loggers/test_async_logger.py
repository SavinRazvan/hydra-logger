"""
Role: Pytest coverage for async logger behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
 - pytest
Notes:
 - Validates sync fallback path and explicit async log/close lifecycle.
"""

from __future__ import annotations

import asyncio

from hydra_logger.loggers.async_logger import AsyncLogger


def test_async_logger_sync_fallback_log_increments_count() -> None:
    logger = AsyncLogger()
    logger.info("sync fallback message")
    assert logger.get_health_status()["log_count"] >= 1
    logger.close()
    assert logger.is_closed is True


def test_async_logger_explicit_async_log_and_aclose() -> None:
    logger = AsyncLogger()
    asyncio.run(logger.log_async("INFO", "async message"))
    health = logger.get_health_status()
    assert health["log_count"] >= 1
    asyncio.run(logger.aclose())
    assert logger.is_closed is True


def test_async_logger_log_concurrent_and_background_work() -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        await logger.log_concurrent(
            [
                ("INFO", "m1", {}),
                ("WARNING", "m2", {}),
                ("ERROR", "m3", {}),
            ],
            max_concurrent=2,
        )

        async def async_task():
            return "async-ok"

        def sync_task():
            return "sync-ok"

        results = await logger.log_background_work([async_task, sync_task], max_concurrent=2)
        assert "async-ok" in results
        assert "sync-ok" in results
        assert logger.get_health_status()["log_count"] >= 3
        await logger.aclose()

    asyncio.run(_run())
