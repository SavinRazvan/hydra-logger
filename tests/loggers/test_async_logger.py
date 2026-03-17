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
import builtins
import sys
import types

import pytest

from hydra_logger.config.models import LogDestination, LogLayer, LoggingConfig
from hydra_logger.core.exceptions import HydraLoggerError
from hydra_logger.loggers.async_logger import AsyncLogger
from hydra_logger.types.levels import LogLevel


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


def test_async_logger_optimal_concurrency_importerror_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "psutil":
            raise ImportError("forced")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    assert logger._get_optimal_concurrency() == 100
    logger.close()


def test_async_logger_optimal_concurrency_thresholds(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = AsyncLogger()

    def _set_available_mb(available_mb: int) -> None:
        fake = types.SimpleNamespace(
            virtual_memory=lambda: types.SimpleNamespace(
                available=available_mb * 1024 * 1024
            )
        )
        monkeypatch.setitem(sys.modules, "psutil", fake)

    _set_available_mb(9000)
    assert logger._get_optimal_concurrency() == 500
    _set_available_mb(5000)
    assert logger._get_optimal_concurrency() == 250
    _set_available_mb(3000)
    assert logger._get_optimal_concurrency() == 100
    _set_available_mb(1000)
    assert logger._get_optimal_concurrency() == 50
    logger.close()


def test_async_logger_log_async_raises_hydra_error_and_uses_fallback_handler() -> None:
    class Fallback:
        def __init__(self) -> None:
            self.called = False

        def handle(self, _record) -> None:  # type: ignore[no-untyped-def]
            self.called = True

    async def _run() -> None:
        logger = AsyncLogger()
        fallback = Fallback()
        logger._fallback_handler = fallback

        async def _fail_emit(_record) -> None:  # type: ignore[no-untyped-def]
            raise RuntimeError("emit fail")

        logger._emit_to_handlers = _fail_emit  # type: ignore[assignment]

        with pytest.raises(HydraLoggerError, match="Failed to log message"):
            await logger._log_async("INFO", "will fail")
        assert fallback.called is True
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_get_concurrency_info_importerror_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    logger._optimal_concurrency = 7
    logger._concurrency_semaphore = asyncio.Semaphore(3)
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "psutil":
            raise ImportError("forced")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    info = logger.get_concurrency_info()
    assert info["status"] == "active_no_psutil"
    logger.close()


def test_async_logger_overflow_worker_processes_and_exits() -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        logger._closed = False
        logger._concurrency_semaphore = None
        record = logger.create_log_record("INFO", "ovf-msg")
        await logger._overflow_queue.put(record)

        async def _emit(_record):  # type: ignore[no-untyped-def]
            logger._closed = True

        logger._emit_to_handlers = _emit  # type: ignore[assignment]
        await asyncio.wait_for(logger._overflow_worker(), timeout=1.0)
        assert logger.get_health_status()["log_count"] >= 1
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_runtime_updates_without_config_are_noop() -> None:
    logger = AsyncLogger()
    logger._config = None
    logger.update_security_level("high")
    logger.update_monitoring_config("basic", 5, True)
    logger.toggle_feature("plugins", True)
    assert logger.get_configuration_summary()["status"] == "no_configuration"
    logger.close()


def test_async_logger_close_async_alias() -> None:
    logger = AsyncLogger()
    asyncio.run(logger.close_async())
    assert logger.is_closed is True


def test_async_logger_create_formatter_cache_and_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    destination = LogDestination(type="console", format="plain-text")
    calls = []

    class SentinelFormatter:
        pass

    sentinel = SentinelFormatter()

    def fake_get_formatter(fmt, **_kwargs):  # type: ignore[no-untyped-def]
        calls.append(fmt)
        return sentinel

    monkeypatch.setattr("hydra_logger.formatters.get_formatter", fake_get_formatter)
    first = logger._create_formatter_for_destination(
        destination, is_console=False, use_colors=False
    )
    second = logger._create_formatter_for_destination(
        destination, is_console=False, use_colors=False
    )
    assert first is sentinel and second is sentinel
    assert calls == ["plain-text"]

    state = {"n": 0}

    def flaky_get_formatter(_fmt, **_kwargs):  # type: ignore[no-untyped-def]
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("formatter-broken")
        return sentinel

    monkeypatch.setattr("hydra_logger.formatters.get_formatter", flaky_get_formatter)
    fallback = logger._create_formatter_for_destination(
        LogDestination(type="file", path="a.log", format="plain-text"),
        is_console=False,
        use_colors=False,
    )
    assert fallback is sentinel
    logger.close()


def test_async_logger_create_handler_variants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeConsoleHandler:
        def __init__(self, **_kwargs):  # type: ignore[no-untyped-def]
            self.formatter = None

        def setFormatter(self, formatter) -> None:  # type: ignore[no-untyped-def]
            self.formatter = formatter

    class FakeFileHandler:
        def __init__(self, filename: str, **_kwargs):
            self.filename = filename
            self.formatter = None
            self.started = False

        def setFormatter(self, formatter) -> None:  # type: ignore[no-untyped-def]
            self.formatter = formatter

        def _start_worker(self) -> None:
            self.started = True

    monkeypatch.setattr(
        "hydra_logger.handlers.console_handler.AsyncConsoleHandler", FakeConsoleHandler
    )
    monkeypatch.setattr("hydra_logger.handlers.file_handler.AsyncFileHandler", FakeFileHandler)

    logger = AsyncLogger(
        config=LoggingConfig(
            layers={"default": LogLayer(destinations=[LogDestination(type="null")])}
        )
    )
    monkeypatch.setattr(
        LoggingConfig, "resolve_log_path", lambda self, path, fmt=None: f"/tmp/{path}"
    )

    console_handler = logger._create_handler_from_destination(
        LogDestination(type="console", format="plain-text")
    )
    file_handler = logger._create_handler_from_destination(
        LogDestination(type="file", path="logs.log", format="plain-text")
    )
    null_handler = logger._create_handler_from_destination(LogDestination(type="null"))
    fallback_handler = logger._create_handler_from_destination(
        LogDestination(type="async_cloud", service_type="s3")
    )

    assert getattr(console_handler, "formatter", None) is not None
    assert getattr(file_handler, "filename", "") == "/tmp/logs.log"
    assert getattr(file_handler, "started", False) is True
    assert null_handler.__class__.__name__ == "NullHandler"
    assert fallback_handler.__class__.__name__ == "NullHandler"
    logger.close()


def test_async_logger_log_batch_wraps_chunk_processing_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()

        async def explode(_chunk, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("chunk fail")

        monkeypatch.setattr(logger, "_process_chunk_optimized", explode)
        with pytest.raises(HydraLoggerError, match="Failed to log batch"):
            await logger.log_batch([("INFO", "m1", {})])
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_setup_data_protection_importerror_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    logger._enable_data_protection = True
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name.endswith("extensions.extension_base"):
            raise ImportError("forced")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    logger._setup_data_protection()
    assert logger._data_protection is None
    logger.close()


def test_async_logger_setup_data_protection_uses_configured_patterns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = {}

    class FakeSecurityExtension:
        def __init__(self, enabled: bool, patterns):  # type: ignore[no-untyped-def]
            seen["enabled"] = enabled
            seen["patterns"] = patterns

    monkeypatch.setattr(
        "hydra_logger.extensions.extension_base.SecurityExtension",
        FakeSecurityExtension,
    )
    logger = AsyncLogger(
        config=LoggingConfig(
            extensions={"data_protection": {"patterns": ["token", "secret"]}}
        )
    )
    logger._enable_data_protection = True
    logger._setup_data_protection()
    assert seen["enabled"] is True
    assert seen["patterns"] == ["token", "secret"]
    logger.close()


def test_async_logger_ensure_concurrency_semaphore_starts_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    task_marker = object()

    def fake_create_task(_coro):  # type: ignore[no-untyped-def]
        _coro.close()
        return task_marker

    monkeypatch.setattr(asyncio, "create_task", fake_create_task)
    logger._ensure_concurrency_semaphore()
    assert logger._concurrency_semaphore is not None
    assert logger._optimal_concurrency is not None
    assert logger._overflow_worker_task is task_marker
    logger.close()


def test_async_logger_overflow_worker_queuefull_path_logs_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        logger._closed = False
        logger._concurrency_semaphore = asyncio.Semaphore(0)  # locked() -> True
        record = logger.create_log_record("INFO", "ovf")
        await logger._overflow_queue.put(record)
        warnings = []

        def full_nowait(_rec):  # type: ignore[no-untyped-def]
            logger._closed = True
            raise asyncio.QueueFull()

        monkeypatch.setattr(logger._overflow_queue, "put_nowait", full_nowait)
        monkeypatch.setattr(
            "hydra_logger.loggers.async_logger.diagnostics.warning",
            lambda msg: warnings.append(msg),
        )
        await asyncio.wait_for(logger._overflow_worker(), timeout=1.0)
        assert warnings and "Overflow queue full" in warnings[0]
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_process_chunk_small_path_handles_item_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        warnings = []

        async def flaky_log(level, message, **kwargs):  # type: ignore[no-untyped-def]
            if message == "bad":
                raise RuntimeError("chunk-item-failed")

        monkeypatch.setattr(logger, "log", flaky_log)
        monkeypatch.setattr(
            "hydra_logger.loggers.async_logger.diagnostics.warning",
            lambda msg, err: warnings.append((msg, str(err))),
        )

        await logger._process_chunk_optimized(
            [("INFO", "bad", {}), ("INFO", "good", {})]
        )
        assert warnings and "chunk-item-failed" in warnings[0][1]
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_process_chunk_large_path_logs_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        infos = []

        async def ok_log(_level, _message, **_kwargs):  # type: ignore[no-untyped-def]
            return None

        monkeypatch.setattr(logger, "log", ok_log)
        monkeypatch.setattr(
            "hydra_logger.loggers.async_logger.diagnostics.info",
            lambda *args: infos.append(args),
        )

        chunk = [("INFO", f"m{i}", {}) for i in range(1001)]
        await logger._process_chunk_optimized(chunk)
        assert infos, "Expected progress info for large chunk"
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_log_concurrent_wraps_gather_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()

        async def explode(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("gather failed")

        monkeypatch.setattr(asyncio, "gather", explode)
        with pytest.raises(HydraLoggerError, match="Failed to log concurrent"):
            await logger.log_concurrent([("INFO", "x", {})], max_concurrent=1)
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_monitoring_toggle_and_concurrency_reasoning_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StubConfig:
        def __init__(self) -> None:
            self.calls = []
            self.features = {}

        def update_monitoring_config(self, detail, sample, background):  # type: ignore[no-untyped-def]
            self.calls.append((detail, sample, background))

        def toggle_feature(self, feature: str, enabled: bool) -> None:
            self.features[feature] = enabled

        def get_configuration_summary(self):
            return {"status": "ok"}

    logger = AsyncLogger()
    logger._config = StubConfig()  # type: ignore[assignment]
    logger.toggle_feature("sanitization", True)
    logger.toggle_feature("plugins", True)
    assert logger._enable_sanitization is True
    assert logger._enable_plugins is True

    logger.update_monitoring_config(detail_level=None, sample_rate=5, background=False)
    assert logger.get_configuration_summary()["status"] == "ok"

    logger._optimal_concurrency = 250
    logger._concurrency_semaphore = asyncio.Semaphore(2)
    fake_psutil = types.SimpleNamespace(
        virtual_memory=lambda: types.SimpleNamespace(available=5000 * 1024 * 1024, percent=42)
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    info = logger.get_concurrency_info()
    assert info["status"] == "active"
    assert "MB available" in logger._get_concurrency_reasoning()

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "psutil":
            raise ImportError("forced")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    assert "psutil not available" in logger._get_concurrency_reasoning()
    logger.close()


def test_async_logger_security_processing_and_plugin_noops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        record = logger.create_log_record("INFO", "secure")

        # Disabled security should return original record.
        logger._enable_security = False
        same = await logger._apply_security_processing(record)
        assert same is record

        # Enabled security should process and update stats.
        logger._enable_security = True
        logger._security_stats = {}

        class Engine:
            def process_log_record(self, rec):  # type: ignore[no-untyped-def]
                return rec

        logger._security_engine = Engine()
        processed = await logger._apply_security_processing(record)
        assert processed is record
        assert logger._security_stats["processed_records"] == 1

        # Processing failures should be non-fatal and return original record.
        warnings = []

        class BadEngine:
            def process_log_record(self, _rec):  # type: ignore[no-untyped-def]
                raise RuntimeError("security-fail")

        logger._security_engine = BadEngine()
        monkeypatch.setattr(
            "hydra_logger.loggers.async_logger.diagnostics.warning",
            lambda *_args: warnings.append("warn"),
        )
        fallback = await logger._apply_security_processing(record)
        assert fallback is record
        assert warnings

        # Plugin lifecycle is intentionally no-op.
        assert await logger._execute_pre_log_plugins(record) is record
        await logger._execute_post_log_plugins(record)
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_sync_convenience_methods_return_coroutines_without_loop() -> None:
    logger = AsyncLogger()

    async def fake_coro():  # type: ignore[no-untyped-def]
        return None

    logger.log = lambda *_args, **_kwargs: fake_coro()  # type: ignore[assignment]
    coros = [logger.debug("d"), logger.info("i"), logger.warning("w"), logger.error("e"), logger.critical("c")]
    for coro in coros:
        assert asyncio.iscoroutine(coro)
        coro.close()
    logger.close()


def test_async_logger_sync_convenience_methods_schedule_tasks_with_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        created = []

        class FakeLoop:
            def create_task(self, coro):  # type: ignore[no-untyped-def]
                created.append("task")
                coro.close()
                return object()

        monkeypatch.setattr(asyncio, "get_running_loop", lambda: FakeLoop())
        logger.debug("d")
        logger.info("i")
        logger.warning("w")
        logger.error("e")
        logger.critical("c")
        assert len(created) == 5
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_async_convenience_methods_delegate_to_log_async() -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        seen = []

        async def fake_log_async(level, message, **_kwargs):  # type: ignore[no-untyped-def]
            seen.append((level, message))

        logger.log_async = fake_log_async  # type: ignore[assignment]
        await logger.debug_async("d")
        await logger.info_async("i")
        await logger.warning_async("w")
        await logger.error_async("e")
        await logger.critical_async("c")
        assert seen == [
            (LogLevel.DEBUG, "d"),
            (LogLevel.INFO, "i"),
            (LogLevel.WARNING, "w"),
            (LogLevel.ERROR, "e"),
            (LogLevel.CRITICAL, "c"),
        ]
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_log_and_log_async_swallow_internal_failures() -> None:
    logger = AsyncLogger()

    async def fail_async(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("boom")

    # log() path: force sync fallback and then failure in _log_sync, which must be swallowed.
    logger._log_sync = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("sync-boom"))  # type: ignore[assignment]
    original_get_running_loop = asyncio.get_running_loop
    asyncio.get_running_loop = lambda: (_ for _ in ()).throw(RuntimeError("no-loop"))  # type: ignore[assignment]
    try:
        assert logger.log("INFO", "x") is None
    finally:
        asyncio.get_running_loop = original_get_running_loop  # type: ignore[assignment]

    # log_async() path: internal failures should be swallowed.
    logger._log_async = fail_async  # type: ignore[assignment]
    asyncio.run(logger.log_async("INFO", "x"))
    logger.close()


def test_async_logger_background_work_empty_and_failure_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        assert await logger.log_background_work([]) == []

        errors = []

        async def explode(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("gather-fail")

        monkeypatch.setattr(asyncio, "gather", explode)
        monkeypatch.setattr(
            "hydra_logger.loggers.async_logger.diagnostics.error",
            lambda *_args: errors.append("error"),
        )
        assert await logger.log_background_work([lambda: "x"], max_concurrent=1) == []
        assert errors
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_close_and_aclose_cleanup_branches() -> None:
    async def _run() -> None:
        logger = AsyncLogger()

        class CloseRaises:
            def close(self) -> None:
                raise RuntimeError("close-fail")

        class AsyncClose:
            async def close_async(self) -> None:
                return None

        class AsyncAclose:
            async def aclose(self) -> None:
                return None

        logger._handlers = {
            "raise": CloseRaises(),
            "async-close": AsyncClose(),
            "aclose": AsyncAclose(),
        }
        logger._console_handler = CloseRaises()

        # Sync close should tolerate handler/console close failures.
        logger.close()
        assert logger.is_closed is True

        # Re-open state to exercise async close cancellation branch.
        logger._closed = False
        logger._overflow_worker_task = asyncio.create_task(asyncio.sleep(10))
        await logger.aclose()
        assert logger.is_closed is True

    asyncio.run(_run())


def test_async_logger_setup_from_dict_and_not_initialized_early_returns() -> None:
    logger = AsyncLogger(config={"layers": {"default": {"destinations": [{"type": "null"}]}}})
    logger._initialized = False
    assert logger.log("INFO", "skip") is None
    asyncio.run(logger.log_async("INFO", "skip"))
    logger.close()


def test_async_logger_sync_and_async_internal_exception_swallow_paths() -> None:
    logger = AsyncLogger()
    logger._record_builder.normalize_level = lambda _level: (_ for _ in ()).throw(RuntimeError("norm-fail"))  # type: ignore[assignment]
    logger._log_sync("INFO", "x")

    async def _run() -> None:
        class Fallback:
            def handle(self, _record):  # type: ignore[no-untyped-def]
                raise RuntimeError("fallback-fail")

        logger2 = AsyncLogger()
        logger2._fallback_handler = Fallback()

        async def _fail_emit(_record):  # type: ignore[no-untyped-def]
            raise RuntimeError("emit-fail")

        logger2._emit_to_handlers = _fail_emit  # type: ignore[assignment]
        with pytest.raises(HydraLoggerError):
            await logger2._log_async("INFO", "x")
        await logger2.aclose()

    asyncio.run(_run())
    logger.close()


def test_async_logger_overflow_worker_timeout_and_exception_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        logger._closed = False
        logger._concurrency_semaphore = asyncio.Semaphore(1)
        record = logger.create_log_record("INFO", "ovf-timeout")
        await logger._overflow_queue.put(record)

        state = {"calls": 0}
        original_wait_for = asyncio.wait_for

        async def fake_wait_for(awaitable, *args, **kwargs):  # type: ignore[no-untyped-def]
            state["calls"] += 1
            if state["calls"] == 1:
                awaitable.close()
                raise asyncio.TimeoutError()
            if state["calls"] == 2:
                return await original_wait_for(awaitable, *args, **kwargs)
            awaitable.close()
            raise RuntimeError("queue-broken")

        async def _emit(_record):  # type: ignore[no-untyped-def]
            logger._closed = True

        monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)
        logger._emit_to_handlers = _emit  # type: ignore[assignment]
        await original_wait_for(logger._overflow_worker(), timeout=1.0)

        # Outer exception sleep branch.
        logger._closed = False
        logger._overflow_queue = asyncio.Queue()
        await logger._overflow_queue.put(logger.create_log_record("INFO", "ovf-outer"))
        logger._concurrency_semaphore = object()  # type: ignore[assignment]
        monkeypatch.setattr(asyncio, "wait_for", original_wait_for)
        sleeps = []

        async def fake_sleep(seconds: float):  # type: ignore[no-untyped-def]
            sleeps.append(seconds)
            logger._closed = True

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        await original_wait_for(logger._overflow_worker(), timeout=1.0)
        assert sleeps
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_large_batch_and_concurrency_dynamic_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        info_calls = []
        monkeypatch.setattr(
            "hydra_logger.loggers.async_logger.diagnostics.info",
            lambda *args: info_calls.append(args),
        )

        async def ok_log(_level, _message, **_kwargs):  # type: ignore[no-untyped-def]
            return None

        logger.log = ok_log  # type: ignore[assignment]
        messages = [("INFO", f"m{i}", {}) for i in range(10001)]
        await logger.log_batch(messages)
        await logger.log_concurrent(messages, max_concurrent=None)
        assert info_calls
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_empty_collection_early_returns_and_default_concurrency() -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        await logger.log_batch([])
        await logger.log_concurrent([])
        results = await logger.log_background_work([lambda: "ok"], max_concurrent=None)
        assert results == ["ok"]
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_convenience_non_coroutine_returns_and_context_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    logger.log = lambda *_args, **_kwargs: "done"  # type: ignore[assignment]
    assert logger.debug("d") == "done"
    assert logger.error("e") == "done"
    assert logger.critical("c") == "done"

    with AsyncLogger() as ctx:
        assert ctx is not None
    assert ctx.is_closed is True

    # __exit__ path with pre-closed logger branch in close().
    ctx.close()
    monkeypatch.setattr(ctx, "close", lambda: None)
    ctx.__exit__(None, None, None)


def test_async_logger_aclose_console_close_async_and_outer_exception() -> None:
    async def _run() -> None:
        logger = AsyncLogger()

        class ConsoleCloseAsync:
            async def close_async(self) -> None:
                return None

        logger._console_handler = ConsoleCloseAsync()
        await logger.aclose()

        # Outer exception branch in aclose.
        logger2 = AsyncLogger()
        logger2._closed = False
        logger2._handlers = None  # type: ignore[assignment]
        await logger2.aclose()

    asyncio.run(_run())


def test_async_logger_health_and_reasoning_remaining_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    logger._optimal_concurrency = 500
    logger._concurrency_semaphore = asyncio.Semaphore(4)
    health = logger.get_health_status()
    assert health["concurrency_available"] == 4

    fake_psutil = types.SimpleNamespace(
        virtual_memory=lambda: types.SimpleNamespace(available=9000 * 1024 * 1024, percent=10)
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    assert "High concurrency" in logger._get_concurrency_reasoning()

    fake_psutil_mid = types.SimpleNamespace(
        virtual_memory=lambda: types.SimpleNamespace(available=3000 * 1024 * 1024, percent=30)
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil_mid)
    assert "Low concurrency" in logger._get_concurrency_reasoning()

    fake_psutil_low = types.SimpleNamespace(
        virtual_memory=lambda: types.SimpleNamespace(available=1000 * 1024 * 1024, percent=70)
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil_low)
    assert "Conservative concurrency" in logger._get_concurrency_reasoning()
    logger.close()


def test_async_logger_formatter_colored_console_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = AsyncLogger()
    destination = LogDestination(type="console", format="plain-text")
    calls = []

    def fake_get_formatter(fmt, **kwargs):  # type: ignore[no-untyped-def]
        calls.append((fmt, kwargs.get("use_colors")))
        return object()

    monkeypatch.setattr("hydra_logger.formatters.get_formatter", fake_get_formatter)
    logger._create_formatter_for_destination(destination, is_console=True, use_colors=True)
    assert calls and calls[0][0] == "colored"
    logger.close()


def test_async_logger_process_chunk_large_branch_item_failure_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        warnings = []

        async def flaky_log(_level, message, **_kwargs):  # type: ignore[no-untyped-def]
            if message == "bad":
                raise RuntimeError("large-item-fail")

        monkeypatch.setattr(logger, "log", flaky_log)
        monkeypatch.setattr(
            "hydra_logger.loggers.async_logger.diagnostics.warning",
            lambda msg, err: warnings.append((msg, str(err))),
        )
        big_chunk = [("INFO", "bad", {})] + [("INFO", f"ok-{i}", {}) for i in range(1001)]
        await logger._process_chunk_optimized(big_chunk)
        assert warnings and "large-item-fail" in warnings[0][1]
        await logger.aclose()

    asyncio.run(_run())


def test_async_logger_close_cancels_overflow_worker_task_branch() -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        logger._overflow_worker_task = asyncio.create_task(asyncio.sleep(10))
        logger.close()
        assert logger.is_closed is True

    asyncio.run(_run())


def test_async_logger_overflow_worker_breaks_on_queue_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = AsyncLogger()
        logger._closed = False

        async def broken_wait_for(_awaitable, *args, **kwargs):  # type: ignore[no-untyped-def]
            _awaitable.close()
            raise RuntimeError("queue-broken")

        monkeypatch.setattr(asyncio, "wait_for", broken_wait_for)
        await logger._overflow_worker()
        await logger.aclose()

    asyncio.run(_run())
