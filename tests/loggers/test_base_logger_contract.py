"""
Role: Pytest coverage for base logger shared contracts.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates common base logger helpers and fallback paths.
"""

from __future__ import annotations

import asyncio

from hydra_logger.loggers.base import BaseLogger


class DummyBaseLogger(BaseLogger):
    def log(self, level, message, **kwargs):
        self._last = (level, message, kwargs)

    def debug(self, message, **kwargs):
        self.log("DEBUG", message, **kwargs)

    def info(self, message, **kwargs):
        self.log("INFO", message, **kwargs)

    def warning(self, message, **kwargs):
        self.log("WARNING", message, **kwargs)

    def error(self, message, **kwargs):
        self.log("ERROR", message, **kwargs)

    def critical(self, message, **kwargs):
        self.log("CRITICAL", message, **kwargs)

    def close(self):
        self._closed = True

    def get_health_status(self):
        return {"initialized": self._initialized, "closed": self._closed}


def test_base_logger_config_helpers_and_flags() -> None:
    logger = DummyBaseLogger(
        config=None,
        name="core",
        enable_security=True,
        enable_sanitization=True,
        enable_plugins=True,
        enable_monitoring=True,
    )
    assert logger.name == "core"
    assert logger.is_security_enabled() is True
    assert logger.is_sanitization_enabled() is True
    assert logger.is_plugins_enabled() is True
    assert logger.is_monitoring_enabled() is True

    logger.name = "renamed"
    assert logger.name == "renamed"
    assert logger.file_path is None


def test_base_logger_record_creation_and_level_mappers() -> None:
    logger = DummyBaseLogger(config=None, name="base")
    record = logger.create_log_record("INFO", "hello", layer="default")
    assert record.message == "hello"
    assert record.level_name == "INFO"
    assert record.logger_name == "base"
    assert logger._get_level_name(50) == "CRITICAL"
    assert logger._get_level_int("debug") == 10
    assert logger._get_level_int("unknown") == 20


def test_base_logger_batch_and_async_context_cleanup() -> None:
    logger = DummyBaseLogger(config=None)
    records = [
        logger.create_log_record("INFO", "m1"),
        logger.create_log_record("ERROR", "m2"),
    ]
    logger.log_batch(records)
    assert logger._last[1] == "m2"

    async def _run():
        async with logger:
            await logger.emit_async(logger.create_log_record("INFO", "m3"))
        return logger.is_closed

    assert asyncio.run(_run()) is True


def test_base_logger_performance_profile_stats_and_context_manager() -> None:
    logger = DummyBaseLogger(config=None)
    logger.set_performance_profile("minimal")
    assert logger.get_performance_profile() == "minimal"
    stats = logger.get_record_creation_stats()
    assert stats["performance_profile"] == "minimal"

    with logger as ctx:
        assert ctx is logger
    assert logger.is_closed is True
