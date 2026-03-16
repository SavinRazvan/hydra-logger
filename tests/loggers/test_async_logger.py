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

from hydra_logger.core.exceptions import HydraLoggerError
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


def test_async_logger_background_work_filters_task_exceptions() -> None:
    async def _run() -> None:
        logger = AsyncLogger()

        async def ok_async():
            return "ok-async"

        def fail_sync():
            raise RuntimeError("boom")

        results = await logger.log_background_work([ok_async, fail_sync], max_concurrent=2)
        assert results == ["ok-async"]
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_close_disables_concurrency_semaphore_in_health_status() -> None:
    logger = AsyncLogger()
    logger.close()
    health = logger.get_health_status()
    assert health["closed"] is True
    assert health["concurrency_semaphore"] == "inactive"


def test_async_logger_batch_and_concurrent_require_initialization() -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        logger._initialized = False
        try:
            await logger.log_batch([("INFO", "x", {})])
        except HydraLoggerError as exc:
            assert "not initialized" in str(exc)
        else:
            raise AssertionError("Expected log_batch to fail when not initialized")

        try:
            await logger.log_concurrent([("INFO", "x", {})])
        except HydraLoggerError as exc:
            assert "not initialized" in str(exc)
        else:
            raise AssertionError("Expected log_concurrent to fail when not initialized")

    asyncio.run(_run())


def test_async_logger_aliases_and_runtime_config_helpers() -> None:
    logger = AsyncLogger()
    logger.warn("warn-msg")
    logger.fatal("fatal-msg")
    assert logger.get_health_status()["log_count"] >= 2

    class StubConfig:
        def __init__(self) -> None:
            self.security_level = None
            self.monitoring = None
            self.features = {}

        def update_security_level(self, level: str) -> None:
            self.security_level = level

        def update_monitoring_config(self, detail_level, sample_rate, background) -> None:
            self.monitoring = (detail_level, sample_rate, background)

        def toggle_feature(self, feature: str, enabled: bool) -> None:
            self.features[feature] = enabled

        def get_configuration_summary(self):
            return {"status": "ok", "security": self.security_level}

    cfg = StubConfig()
    logger._config = cfg  # type: ignore[assignment]
    logger.update_security_level("high")
    logger.update_monitoring_config("full", 10, True)
    logger.toggle_feature("security", True)
    assert logger.get_configuration_summary()["status"] == "ok"
    assert logger._enable_security is True
    assert logger.get_pool_stats()["status"] == "deprecated"
    logger._concurrency_semaphore = None
    assert logger.get_concurrency_info()["status"] == "not_initialized"
    logger.close()
