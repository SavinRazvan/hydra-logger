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

import pytest

from hydra_logger.config.models import LogDestination, LogLayer, LoggingConfig
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


class AsyncLogComponent:
    def __init__(self) -> None:
        self.calls = []
        self.closed = False

    async def log(self, level, message, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append((level, message, kwargs))

    async def aclose(self) -> None:
        self.closed = True


class InitFailComponent:
    def __init__(self, name: str = "init-fail") -> None:
        self.name = name

    def initialize(self) -> None:
        raise RuntimeError("init failed")


class CloseAsyncComponent:
    def __init__(self, name: str = "close-async") -> None:
        self.name = name
        self.closed = False

    async def close_async(self) -> None:
        self.closed = True


class EmitAsyncComponent:
    def __init__(self) -> None:
        self.count = 0
        self.closed = False

    async def emit_async(self, _record):  # type: ignore[no-untyped-def]
        self.count += 1

    async def aclose(self) -> None:
        self.closed = True


class FailingHealthComponent:
    name = "broken-health"

    def get_health_status(self):
        raise RuntimeError("health failure")


class RaiseOnCloseComponent:
    def __init__(self, name: str = "raise-close") -> None:
        self.name = name

    def close(self) -> None:
        raise RuntimeError("close failed")


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


def test_composite_logger_health_without_component_method_is_unknown() -> None:
    class BareComponent:
        name = "bare"

    logger = CompositeLogger(components=[BareComponent()])  # type: ignore[list-item]
    health = logger.get_health_status()
    assert health["components"][0]["health"] == "unknown"
    logger.close()


def test_composite_logger_close_tolerates_component_close_failures() -> None:
    logger = CompositeLogger(components=[RaiseOnCloseComponent()])
    logger.close()
    assert logger._closed is True


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


def test_composite_async_logger_flush_direct_io_without_explicit_destination_no_file_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    logger._direct_io_buffer = ["line one\n"]

    def fail_open(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("open() should not be called without explicit destination")

    monkeypatch.setattr("builtins.open", fail_open)
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


def test_composite_async_logger_set_level_accepts_numeric_levels() -> None:
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    logger.set_level(40)
    assert logger.get_level() == "ERROR"
    logger.close()


def test_composite_async_logger_async_context_manager_closes_cleanly() -> None:
    async def _run() -> bool:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True)
        async with logger:
            await logger.log("INFO", "ctx")
        return logger._closed

    assert asyncio.run(_run()) is True


def test_composite_async_logger_formatter_and_layer_management() -> None:
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    formatter = object()
    logger.add_formatter("f1", formatter)
    assert logger.get_formatter("f1") is formatter
    assert logger.get_formatters()["f1"] is formatter
    logger.set_default_formatter("default-fmt")
    assert logger.get_formatter() == "default-fmt"
    logger.remove_formatter("f1")
    assert logger.get_formatter("f1") == "default-fmt"

    logger.add_layer("api", {"level": "INFO"})
    assert logger.get_layer("api") == {"level": "INFO"}
    assert "api" in logger.get_layers()
    logger.set_default_layer("api")
    logger.remove_layer("api")
    assert logger.get_layer("api") is None
    logger.close()


def test_composite_async_logger_direct_io_formatter_branch_and_stats() -> None:
    class Formatter:
        def format(self, _record):  # type: ignore[no-untyped-def]
            return "formatted-line"

    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True)
        logger._buffer_size = 10_000
        logger.add_formatter("structured", Formatter())
        await logger.log("INFO", "payload", formatter="structured")
        assert any("formatted-line" in line for line in logger._direct_io_buffer)
        stats = logger.get_stats()
        assert stats["log_count"] >= 1
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_logger_log_bulk_component_path() -> None:
    async def _run() -> None:
        component = EmitAsyncComponent()
        logger = CompositeAsyncLogger(components=[component], use_direct_io=False)
        await logger.log_bulk("INFO", ["a", "b", "c"])
        assert component.count == 3
        await logger.aclose()
        assert component.closed is True

    asyncio.run(_run())


def test_composite_async_logger_log_batch_direct_io_level_filtering() -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True, level="ERROR")
        seen = []

        def _capture(level, message, layer, kwargs):  # type: ignore[no-untyped-def]
            seen.append((level, message, layer))

        logger._direct_string_format = _capture  # type: ignore[assignment]
        await logger.log_batch(
            [
                ("INFO", "ignored", {}),
                ("ERROR", "kept", {"layer": "api"}),
            ]
        )
        assert seen == [("ERROR", "kept", "api")]
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_logger_log_batch_component_mode_chunks() -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=False, level="INFO")
        logger._batch_size = 2
        seen = []

        def _capture(level, message, layer, kwargs):  # type: ignore[no-untyped-def]
            seen.append((level, message, layer))

        logger._direct_string_format = _capture  # type: ignore[assignment]
        await logger.log_batch(
            [
                ("INFO", "m1", {}),
                ("DEBUG", "skip", {}),
                ("ERROR", "m2", {"layer": "default"}),
            ]
        )
        assert seen == [("INFO", "m1", "default"), ("ERROR", "m2", "default")]
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_logger_log_bulk_direct_io_coercion() -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True)
        calls = []

        def _emit(level, message, *args, **kwargs):  # type: ignore[no-untyped-def]
            calls.append((level, message))

        logger._direct_io_emit = _emit  # type: ignore[assignment]
        await logger.log_bulk("INFO", ["a", 2, None])
        assert calls == [("INFO", "a"), ("INFO", "2")]
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_logger_log_bulk_component_async_log_path() -> None:
    async def _run() -> None:
        component = AsyncLogComponent()
        logger = CompositeAsyncLogger(components=[component], use_direct_io=False)
        await logger.log_bulk("INFO", ["x"])
        assert component.calls and component.calls[0][1] == "x"
        await logger.aclose()
        assert component.closed is True

    asyncio.run(_run())


def test_composite_async_logger_add_component_init_failure_is_tolerated() -> None:
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    component = InitFailComponent()
    logger.add_component(component)
    assert logger.get_component("init-fail") is component
    logger.close()


def test_composite_async_logger_remove_component_with_async_close_callable() -> None:
    class AsyncCloseComp:
        def __init__(self) -> None:
            self.name = "async-close"

        async def close(self) -> None:
            return None

    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    comp = AsyncCloseComp()
    logger.add_component(comp)
    logger.remove_component(comp)
    assert logger.get_component("async-close") is None
    logger.close()


def test_composite_async_logger_component_mode_with_no_components_is_noop() -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=False)
        await logger.log("INFO", "message")
        assert logger.get_stats()["log_count"] >= 1
        assert len(logger.components) >= 1
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_logger_async_close_uses_close_async_branch() -> None:
    async def _run() -> None:
        component = CloseAsyncComponent()
        logger = CompositeAsyncLogger(components=[component], use_direct_io=False)
        await logger.aclose()
        assert component.closed is True
        assert logger._closed is True

    asyncio.run(_run())


def test_composite_logger_setup_from_config_adds_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = []

    class FakeSyncLogger:
        def __init__(self, config=None):  # type: ignore[no-untyped-def]
            self.name = "fake-sync"
            created.append(config)

        def initialize(self) -> None:
            pass

        def close(self) -> None:
            pass

    monkeypatch.setattr("hydra_logger.loggers.sync_logger.SyncLogger", FakeSyncLogger)
    cfg = LoggingConfig(
        layers={
            "default": LogLayer(destinations=[LogDestination(type="console", format="plain-text")])
        }
    )
    logger = CompositeLogger(config=cfg)
    assert created, "Expected layer setup to instantiate sub-loggers"
    assert logger.get_component("fake-sync") is not None
    logger.close()


def test_composite_async_logger_async_close_gather_exception_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        class BadAclose:
            name = "bad-aclose"

            async def aclose(self) -> None:
                raise RuntimeError("boom")

        logger = CompositeAsyncLogger(components=[BadAclose()], use_direct_io=False)

        async def failing_gather(*awaitables, **_kwargs):  # type: ignore[no-untyped-def]
            for awaitable in awaitables:
                if hasattr(awaitable, "close"):
                    awaitable.close()
            raise RuntimeError("gather fail")

        monkeypatch.setattr(asyncio, "gather", failing_gather)
        await logger.aclose()
        assert logger._closed is True

    asyncio.run(_run())


def test_composite_logger_config_dict_path_and_level_methods() -> None:
    logger = CompositeLogger(
        config={
            "layers": {
                "default": {
                    "destinations": [{"type": "console", "format": "plain-text"}]
                }
            }
        }
    )
    assert logger._config is not None

    class MethodsComponent:
        name = "methods"

        def __init__(self) -> None:
            self.calls = []

        def debug(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            self.calls.append("debug")

        def warning(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            self.calls.append("warning")

        def error(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            self.calls.append("error")

        def critical(self, *_args, **_kwargs):  # type: ignore[no-untyped-def]
            self.calls.append("critical")

    comp = MethodsComponent()
    logger.add_component(comp)  # type: ignore[arg-type]
    logger.debug("d")
    logger.warning("w")
    logger.error("e")
    logger.critical("c")
    assert comp.calls == ["debug", "warning", "error", "critical"]
    logger.close()


def test_composite_async_logger_log_formatter_fallback_and_detailed_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True)
        logger._buffer_size = 100

        class NoFormat:
            pass

        logger.add_formatter("nofmt", NoFormat())
        await logger.log(
            "INFO",
            "message",
            formatter="nofmt",
            file_name="app.py",
            function_name="run",
        )
        assert logger._direct_io_buffer
        assert "message" in logger._direct_io_buffer[-1]

        # No formatter.format() method falls back to raw message + newline.
        assert logger._direct_io_buffer[-1] == "message\n"

        # Without formatter override, detailed direct format path includes file/function.
        await logger.log("INFO", "detailed", file_name="app.py", function_name="run")
        assert "[app.py]" in logger._direct_io_buffer[-1]
        assert "[run]" in logger._direct_io_buffer[-1]

        # Exercise _direct_io_emit non-preformatted path with explicit layer.
        logger._direct_io_emit("INFO", "raw", layer="api", pre_formatted=False)
        assert "[api]" in logger._direct_io_buffer[-1]

        # Exercise flush path where file path comes from component.file_path.
        class FilePathComponent:
            file_path = "/tmp/composite-from-component.log"

        logger.components = [FilePathComponent()]  # type: ignore[list-item]
        logger._direct_io_buffer.append("line\n")

        writes = []

        class FakeFile:
            def __enter__(self):
                return self

            def __exit__(self, *_args):  # type: ignore[no-untyped-def]
                return False

            def write(self, payload: str) -> None:
                writes.append(payload)

        monkeypatch.setattr("builtins.open", lambda *_args, **_kwargs: FakeFile())
        logger._flush_direct_io()
        assert writes
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_logger_log_bulk_and_close_residual_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True)
        await logger.log_bulk("INFO", [])
        logger._closed = True
        await logger.log_bulk("INFO", ["x"])
        logger._closed = False

        # Force component-mode with no components.
        logger._use_direct_io = False
        logger.components = []
        await logger.log_bulk("INFO", ["x"])

        class RaiseComponent:
            async def emit_async(self, _record):  # type: ignore[no-untyped-def]
                raise RuntimeError("emit-fail")

        logger.components = [RaiseComponent()]  # type: ignore[list-item]
        await logger.log_bulk("INFO", ["x"])

        # Exercise async close outer exception path.
        class BadIterable:
            def __iter__(self):
                raise RuntimeError("iter-fail")

        logger.components = BadIterable()  # type: ignore[assignment]
        await logger.aclose()
        assert logger._closed is True

    asyncio.run(_run())


def test_composite_async_logger_exit_coroutine_close_branch() -> None:
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)

    async def async_close():
        return None

    logger.close = async_close  # type: ignore[assignment]
    logger.__exit__(None, None, None)
    assert logger._closed is True


def test_composite_logger_dispatch_path_and_component_method_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class NoisyComponent:
        name = "noisy"

        @staticmethod
        def debug(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("debug-fail")

        @staticmethod
        def warning(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("warn-fail")

        @staticmethod
        def error(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("err-fail")

        @staticmethod
        def critical(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("crit-fail")

    logger = CompositeLogger(components=[NoisyComponent()])  # type: ignore[list-item]
    dispatched = {"count": 0}

    def _dispatch_sync(components, level, message, **kwargs):  # type: ignore[no-untyped-def]
        dispatched["count"] += 1
        assert components
        assert level == "INFO"
        assert message == "x"

    monkeypatch.setattr(logger._component_dispatcher, "dispatch_sync", _dispatch_sync)
    logger.log("INFO", "x")
    logger.debug("d")
    logger.warning("w")
    logger.error("e")
    logger.critical("c")
    assert dispatched["count"] == 1
    logger.close()


def test_composite_async_logger_wrapper_methods_and_level_checks() -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True, level="WARNING")
        assert logger.is_enabled_for("ERROR") is True
        assert logger.is_enabled_for("INFO") is False
        logger.set_level("DEBUG")
        assert logger.get_level() == "DEBUG"

        await logger.debug("d")
        await logger.info("i")
        await logger.warning("w")
        await logger.error("e")
        await logger.critical("c")
        assert logger.get_stats()["log_count"] >= 5
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_logger_flush_direct_io_from_explicit_config_destination(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = LoggingConfig(
        layers={
            "default": LogLayer(
                destinations=[LogDestination(type="file", path="cfg-explicit.log", format="plain-text")]
            )
        }
    )
    logger = CompositeAsyncLogger(config=cfg, components=[], use_direct_io=True)
    logger._direct_io_buffer = ["line\n"]
    logger._flush_direct_io()
    output = tmp_path / "logs" / "cfg-explicit.log"
    assert output.exists()
    assert "line" in output.read_text(encoding="utf-8")
    logger.close()


def test_composite_async_logger_close_paths_and_health_error_branches() -> None:
    class CoroutineCloseComponent:
        name = "coroutine-close"

        async def close(self) -> None:
            raise RuntimeError("async-close-fail")

    class FailingSyncCloseComponent:
        name = "failing-sync-close"

        @staticmethod
        def close() -> None:
            raise RuntimeError("sync-close-fail")

    class BadHealthComponent:
        name = "bad-health"

        @staticmethod
        def get_health_status():
            raise RuntimeError("health-fail")

    async def _run() -> None:
        logger = CompositeAsyncLogger(
            components=[CoroutineCloseComponent(), BadHealthComponent()],
            use_direct_io=False,
        )
        logger.close()
        assert logger._closed is True

        logger2 = CompositeAsyncLogger(components=[FailingSyncCloseComponent()], use_direct_io=True)
        logger2.close()
        assert logger2._closed is True

        logger3 = CompositeAsyncLogger(components=[BadHealthComponent()], use_direct_io=True)
        health = logger3.get_health_status()
        assert health["overall_health"] == "unhealthy"
        logger3._closed = True
        await logger3.aclose()
        logger3.__enter__()
        logger3.__exit__(None, None, None)

    asyncio.run(_run())


def test_composite_logger_additional_lifecycle_error_branches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InitFail:
        name = "init-fail-sync"

        @staticmethod
        def initialize() -> None:
            raise RuntimeError("init-fail")

    class CloseFail:
        name = "close-fail-sync"

        @staticmethod
        def close() -> None:
            raise RuntimeError("close-fail")

    logger = CompositeLogger()
    logger._setup_layers()  # no config branch
    logger.add_component(InitFail())  # init exception branch
    close_fail = CloseFail()
    logger.add_component(close_fail)
    logger.remove_component(close_fail)  # close exception branch
    logger.close()
    logger.close()  # already-closed branch

    class BadList(list):
        def clear(self) -> None:  # type: ignore[override]
            raise RuntimeError("clear-fail")

    logger2 = CompositeLogger()
    logger2.components = BadList()  # type: ignore[assignment]
    logger2.close()  # outer exception path
    assert logger2._closed is False

    logger3 = CompositeLogger()
    health = logger3.get_health_status()
    assert health["overall_health"] == "unknown"

    class Unhealthy:
        name = "unhealthy"

        @staticmethod
        def get_health_status():
            return {"health": "unhealthy"}

    logger4 = CompositeLogger(components=[Unhealthy()])  # type: ignore[list-item]
    assert logger4.get_health_status()["overall_health"] == "unhealthy"
    logger4.close()


def test_composite_logger_log_batch_fallback_and_exception_paths() -> None:
    class LogOnly:
        def __init__(self) -> None:
            self.calls = []

        def log(self, level, message, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append((level, message, kwargs))

    class BadBatch:
        @staticmethod
        def log_batch(_messages):  # type: ignore[no-untyped-def]
            raise RuntimeError("batch-fail")

    component = LogOnly()
    logger = CompositeLogger(components=[component, BadBatch()])  # type: ignore[list-item]
    logger.log_batch([("INFO", "m", {"k": "v"})])
    assert component.calls and component.calls[0][1] == "m"
    logger.close()


def test_composite_async_direct_flush_threshold_and_config_fallback_paths(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    logger = CompositeAsyncLogger(components=[], use_direct_io=True)

    flushes = {"count": 0}
    logger._flush_direct_io = lambda: flushes.__setitem__("count", flushes["count"] + 1)  # type: ignore[assignment]
    logger._buffer_size = 1
    logger._direct_string_format("INFO", "msg", "default", {})
    logger._direct_io_emit("INFO", "msg2", pre_formatted=False)
    assert flushes["count"] >= 2

    logger2 = CompositeAsyncLogger(
        config=LoggingConfig(
            layers={
                "default": LogLayer(
                    destinations=[LogDestination(type="async_file", path="async-target.log")]
                )
            }
        ),
        components=[],
        use_direct_io=True,
    )
    logger2._direct_io_buffer = ["line\n"]
    logger2._flush_direct_io()
    assert (tmp_path / "logs" / "async-target.log").exists()
    logger2.close()


def test_composite_async_flush_fallback_print_and_close_preparation_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FileComp:
        file_path = "/tmp/never-write.log"

    logger = CompositeAsyncLogger(components=[FileComp()], use_direct_io=True)  # type: ignore[list-item]
    logger._direct_io_buffer = ["x\n"]

    def _bad_open(*_args, **_kwargs):
        raise OSError("open-fail")

    monkeypatch.setattr("builtins.open", _bad_open)
    logger._flush_direct_io()
    assert logger._direct_io_buffer == []

    class BrokenAttr:
        name = "broken-attr"

        def __getattribute__(self, name: str):  # type: ignore[override]
            if name == "aclose":
                raise RuntimeError("attr-fail")
            return object.__getattribute__(self, name)

    async def _run() -> None:
        logger2 = CompositeAsyncLogger(components=[BrokenAttr()], use_direct_io=False)  # type: ignore[list-item]
        await logger2.aclose()
        assert logger2._closed is True

    asyncio.run(_run())


def test_composite_async_no_component_log_and_health_paths() -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=False)
        logger.components = []
        await logger.log("INFO", "msg")
        logger._closed = True
        await logger.aclose()  # already closed branch

        class Healthy:
            name = "healthy"

            @staticmethod
            def get_health_status():
                return {"health": "healthy"}

        class Unknown:
            name = "unknown"

        logger2 = CompositeAsyncLogger(components=[Healthy(), Unknown()], use_direct_io=True)  # type: ignore[list-item]
        health = logger2.get_health_status()
        assert health["overall_health"] == "healthy"
        assert len(health["components"]) == 2
        logger2.close()

    asyncio.run(_run())


def test_composite_constructor_init_failure_branches() -> None:
    class InitFail:
        name = "init-fail"

        @staticmethod
        def initialize() -> None:
            raise RuntimeError("init-fail")

    logger = CompositeLogger(components=[InitFail()])  # type: ignore[list-item]
    assert logger._initialized is True
    logger.close()

    logger2 = CompositeAsyncLogger(components=[InitFail()], use_direct_io=True)  # type: ignore[list-item]
    assert logger2._initialized is True
    logger2.close()


def test_composite_async_remove_component_close_exception_branch() -> None:
    class BadClose:
        name = "bad-close"

        @staticmethod
        def close() -> None:
            raise RuntimeError("bad-close")

    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    comp = BadClose()
    logger.add_component(comp)
    logger.remove_component(comp)
    assert logger.get_component("bad-close") is None
    logger.close()


def test_composite_async_int_level_and_early_return_paths() -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True, level="INFO")
        assert logger.is_enabled_for(40) is True
        assert logger.is_enabled_for(10) is False

        logger._initialized = False
        await logger.log(20, "skip")
        logger._initialized = True
        logger._closed = True
        await logger.log(20, "skip")
        logger._closed = False

        logger.set_level("ERROR")
        await logger.log("INFO", "filtered")
        assert logger.get_stats()["log_count"] == 0
        await logger.aclose()

    asyncio.run(_run())


def test_composite_async_time_based_flush_and_component_bulk_non_string_conversion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[], use_direct_io=True)
        flushed = {"count": 0}
        logger._flush_direct_io = lambda: flushed.__setitem__("count", flushed["count"] + 1)  # type: ignore[assignment]
        logger._buffer_size = 999
        logger._last_flush = 0.0
        logger._flush_interval = 0.1
        monkeypatch.setattr("hydra_logger.utils.time_utility.TimeUtility.perf_counter", lambda: 1.0)
        logger._direct_string_format("INFO", "m", "default", {})
        logger._direct_io_emit("INFO", "m2", pre_formatted=False)
        assert flushed["count"] >= 2

        class EmitComponent:
            def __init__(self) -> None:
                self.count = 0

            async def emit_async(self, _record):  # type: ignore[no-untyped-def]
                self.count += 1

        component = EmitComponent()
        logger2 = CompositeAsyncLogger(components=[component], use_direct_io=False)
        await logger2.log_bulk("INFO", [1, "two"])
        assert component.count == 2
        await logger2.aclose()

    asyncio.run(_run())


def test_composite_async_close_coroutine_branch_and_error_count_warning() -> None:
    class CoroutineClose:
        name = "coroutine-close"

        async def close(self) -> None:
            raise RuntimeError("close boom")

    async def _run() -> None:
        logger = CompositeAsyncLogger(components=[CoroutineClose()], use_direct_io=False)
        await logger.aclose()
        assert logger._closed is True

    asyncio.run(_run())


def test_composite_async_sync_close_outer_exception_and_unhealthy_health() -> None:
    class BadIter:
        def __iter__(self):
            raise RuntimeError("iter-fail")

    logger = CompositeAsyncLogger(components=[], use_direct_io=True)
    logger.components = BadIter()  # type: ignore[assignment]
    logger.close()
    assert logger._closed is True

    class Unhealthy:
        name = "u"

        @staticmethod
        def get_health_status():
            return {"health": "unhealthy"}

    logger2 = CompositeAsyncLogger(components=[Unhealthy()], use_direct_io=True)  # type: ignore[list-item]
    assert logger2.get_health_status()["overall_health"] == "unhealthy"
    logger2.close()
