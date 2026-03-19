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
import builtins

import pytest

from hydra_logger.config.models import LoggingConfig
from hydra_logger.core.exceptions import HydraLoggerError
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


def test_base_logger_coerce_config_paths() -> None:
    logger_from_dict = DummyBaseLogger(config={"default_level": "INFO"})
    assert isinstance(logger_from_dict.get_config(), LoggingConfig)

    cfg = LoggingConfig(default_level="DEBUG")
    logger_from_model = DummyBaseLogger(config=cfg)
    assert logger_from_model.get_config() == cfg

    logger_from_invalid = DummyBaseLogger(config="bad-type")  # type: ignore[arg-type]
    assert logger_from_invalid.get_config() is None


def test_base_logger_magic_config_helpers_and_custom_selector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hydra_logger.config.configuration_templates import configuration_templates

    template = LoggingConfig(default_level="WARNING")
    monkeypatch.setattr(configuration_templates, "has_template", lambda name: True)
    monkeypatch.setattr(configuration_templates, "get_template", lambda name: template)

    logger = DummyBaseLogger(config=None)
    methods = [
        logger.for_production,
        logger.for_development,
        logger.for_testing,
        logger.for_microservice,
        logger.for_web_app,
        logger.for_api_service,
        logger.for_background_worker,
        logger.for_high_performance,
        logger.for_minimal,
        logger.for_debug,
    ]
    for method in methods:
        assert method() is logger
        assert logger.get_config() == template

    assert logger.with_magic_config("custom") is logger
    assert logger.get_config() == template

    monkeypatch.setattr(configuration_templates, "has_template", lambda name: False)
    with pytest.raises(ValueError, match="Unknown magic config"):
        logger.with_magic_config("missing")


def test_base_logger_initialize_from_config_wraps_setup_errors() -> None:
    class BrokenInitLogger(DummyBaseLogger):
        def _setup_handlers(self) -> None:
            raise RuntimeError("boom")

    logger = BrokenInitLogger(config=None)
    with pytest.raises(HydraLoggerError, match="Failed to initialize logger"):
        logger._initialize_from_config(LoggingConfig())


def test_base_logger_record_fallback_and_stats_fallback() -> None:
    logger = DummyBaseLogger(config=None, name="fallback")
    logger._record_creation_strategy = None

    rec_num = logger.create_log_record(40, "n", layer="ops")
    assert rec_num.level_name == "ERROR"
    rec_str = logger.create_log_record("custom", "s")
    assert rec_str.level_name == "custom"

    stats = logger.get_record_creation_stats()
    assert stats["strategy"] == "fallback"


def test_base_logger_setup_record_creation_strategy_import_error_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = DummyBaseLogger(config=None)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name.endswith("types.records"):
            raise ImportError("forced")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    logger._setup_record_creation_strategy()
    assert logger._record_creation_strategy is None


def test_base_logger_aexit_paths_and_initialize_no_config() -> None:
    class AcloseLogger(DummyBaseLogger):
        async def aclose(self) -> None:
            self._aclose_called = True

    class CloseCoroutineLogger(DummyBaseLogger):
        async def close(self) -> None:  # type: ignore[override]
            self._closed = True

    class SyncCloseLogger(DummyBaseLogger):
        pass

    async def run() -> tuple[bool, bool, bool]:
        aclose_logger = AcloseLogger(config=None)
        aclose_logger.close_async = lambda: None  # type: ignore[assignment]
        await aclose_logger.__aexit__(None, None, None)

        close_coro_logger = CloseCoroutineLogger(config=None)
        close_coro_logger.close_async = lambda: None  # type: ignore[assignment]
        close_coro_logger.aclose = lambda: None  # type: ignore[assignment]
        await close_coro_logger.__aexit__(None, None, None)

        sync_logger = SyncCloseLogger(config=None)
        sync_logger.close_async = lambda: None  # type: ignore[assignment]
        sync_logger.aclose = lambda: None  # type: ignore[assignment]
        await sync_logger.__aexit__(None, None, None)

        no_cfg = DummyBaseLogger(config=None)
        no_cfg.initialize()
        return (
            getattr(aclose_logger, "_aclose_called", False),
            close_coro_logger.is_closed,
            sync_logger.is_closed,
        )

    assert asyncio.run(run()) == (True, True, True)


def test_base_logger_abstract_pass_bodies_and_init_alias_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = DummyBaseLogger(config=None)

    # Call abstract body implementations directly to cover pass statements.
    BaseLogger.log(logger, "INFO", "x")
    BaseLogger.debug(logger, "x")
    BaseLogger.info(logger, "x")
    BaseLogger.warning(logger, "x")
    BaseLogger.error(logger, "x")
    BaseLogger.critical(logger, "x")
    BaseLogger.close(logger)
    BaseLogger.get_health_status(logger)

    # initialize() branch when config is present.
    cfg = LoggingConfig()
    logger._config = cfg
    called = {"n": 0}
    monkeypatch.setattr(
        logger,
        "_initialize_from_config",
        lambda _cfg: called.__setitem__("n", called["n"] + 1),
    )
    logger.initialize()
    assert called["n"] == 1

    # aclose alias delegates to close_async
    async def _run() -> None:
        marker = {"n": 0}

        async def _close_async() -> None:
            marker["n"] += 1

        logger.close_async = _close_async  # type: ignore[assignment]
        await logger.aclose()
        assert marker["n"] == 1

    asyncio.run(_run())
    logger._initialized = True
    assert logger.is_initialized is True


def test_base_logger_destructor_async_and_exception_paths() -> None:
    class AsyncCloseLogger(DummyBaseLogger):
        async def close(self) -> None:  # type: ignore[override]
            return None

    class BrokenCloseLogger(DummyBaseLogger):
        def close(self):
            raise BaseException("boom")

    async_logger = AsyncCloseLogger(config=None)
    async_logger._closed = False
    async_logger.__del__()
    assert async_logger.is_closed is True

    broken = BrokenCloseLogger(config=None)
    broken._closed = False
    broken.__del__()  # swallow BaseException path
