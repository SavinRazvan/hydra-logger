"""
Role: Pytest coverage for composite logger behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates component fan-out, failure isolation, and close lifecycle.
"""

import asyncio

from hydra_logger.core.exceptions import HydraLoggerError
from hydra_logger.loggers.composite_logger import CompositeAsyncLogger, CompositeLogger


class DummyComponent:
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.messages = []
        self.closed = False

    def log(self, level, message, **kwargs):
        if self.should_fail:
            raise RuntimeError("component failure")
        self.messages.append((level, message))

    def info(self, message, **kwargs):
        self.log("INFO", message, **kwargs)

    def close(self):
        self.closed = True

    def get_health_status(self):
        return {"health": "healthy", "closed": self.closed}


class DummyAsyncComponent:
    def __init__(self, name: str):
        self.name = name
        self.messages = []
        self.closed = False

    async def log(self, level, message, **kwargs):
        self.messages.append((level, message))

    async def aclose(self):
        self.closed = True


class FailingHealthComponent:
    name = "broken-health"

    def get_health_status(self):
        raise RuntimeError("health failure")


def test_composite_logger_fan_out_and_failure_isolation() -> None:
    ok = DummyComponent("ok")
    bad = DummyComponent("bad", should_fail=True)
    logger = CompositeLogger(components=[ok, bad])
    logger.info("hello composite")
    assert ok.messages
    logger.close()
    assert ok.closed is True


def test_composite_logger_add_remove_component() -> None:
    logger = CompositeLogger()
    comp = DummyComponent("c1")
    logger.add_component(comp)
    assert logger.get_component("c1") is comp
    logger.remove_component(comp)
    assert logger.get_component("c1") is None


def test_composite_logger_batch_updates_log_count() -> None:
    comp = DummyComponent("batch")
    logger = CompositeLogger(components=[comp])
    logger.log_batch(
        [
            ("INFO", "m1", {}),
            ("ERROR", "m2", {}),
        ]
    )
    health = logger.get_health_status()
    assert health["component_count"] == 1
    logger.close()


def test_composite_async_logger_log_and_close() -> None:
    component = DummyAsyncComponent("async")
    logger = CompositeAsyncLogger(components=[component], use_direct_io=False)
    asyncio.run(logger.log("INFO", "async composite message"))
    asyncio.run(logger.aclose())
    assert component.messages
    assert component.closed is True


def test_composite_logger_rejects_log_when_not_initialized_or_closed() -> None:
    logger = CompositeLogger()
    logger._initialized = False
    try:
        logger.log("INFO", "x")
    except HydraLoggerError as exc:
        assert "not initialized" in str(exc)
    else:
        raise AssertionError("Expected log failure when logger is not initialized")

    logger._initialized = True
    logger._closed = True
    try:
        logger.log("INFO", "x")
    except HydraLoggerError as exc:
        assert "closed" in str(exc)
    else:
        raise AssertionError("Expected log failure when logger is closed")


def test_composite_logger_health_marks_unhealthy_on_component_exception() -> None:
    logger = CompositeLogger(components=[FailingHealthComponent()])
    health = logger.get_health_status()
    assert health["overall_health"] == "unhealthy"
    assert health["components"][0]["health"] == "error"


def test_composite_async_logger_health_for_empty_components() -> None:
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    health = logger.get_health_status()
    assert health["component_count"] == 0
    assert health["overall_health"] == "unknown"
    logger.close()


def test_composite_async_logger_flush_direct_io_clears_buffer_on_write_failure(
    monkeypatch,
) -> None:
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    logger._direct_io_buffer = ["line one\n"]

    def _raise_open(*_args, **_kwargs):
        raise OSError("disk down")

    monkeypatch.setattr("builtins.open", _raise_open)
    logger._flush_direct_io()
    assert logger._direct_io_buffer == []
    logger.close()


def test_composite_logger_level_helpers_and_context_manager_close() -> None:
    comp = DummyComponent("level")
    with CompositeLogger(components=[comp]) as logger:
        logger.debug("d")
        logger.warning("w")
        logger.error("e")
        logger.critical("c")
    assert comp.closed is True


def test_composite_logger_log_batch_noop_when_closed_or_empty() -> None:
    comp = DummyComponent("noop")
    logger = CompositeLogger(components=[comp])
    logger.log_batch([])
    logger.close()
    logger.log_batch([("INFO", "m", {})])
    assert comp.messages == []
