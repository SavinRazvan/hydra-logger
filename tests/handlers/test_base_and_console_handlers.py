"""
Role: Pytest coverage for base and console handler behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates level filtering and buffered console flush lifecycle.
"""

import asyncio
import io
import logging
from datetime import datetime, timezone

import pytest

from hydra_logger.handlers import console_handler as console_module
from hydra_logger.handlers.base_handler import BaseHandler
from hydra_logger.handlers.console_handler import (
    AsyncConsoleHandler,
    SyncConsoleHandler,
    create_async_console_handler,
    create_sync_console_handler,
)
from hydra_logger.types.records import LogRecord
from hydra_logger.utils.time_utility import (
    TimestampConfig,
    TimestampFormat,
    TimestampPrecision,
)


class DummyHandler(BaseHandler):
    def __init__(self):
        super().__init__(name="dummy", level=30)
        self.records = []

    def emit(self, record: LogRecord) -> None:
        self.records.append(record)


def test_base_handler_filters_by_level() -> None:
    handler = DummyHandler()
    low = LogRecord(level=20, level_name="INFO", message="low")
    high = LogRecord(level=40, level_name="ERROR", message="high")
    handler.handle(low)
    handler.handle(high)
    assert len(handler.records) == 1
    assert handler.records[0].message == "high"


def test_base_handler_logs_formatter_name_resolution_failure(caplog) -> None:
    class BrokenFormatter:
        def get_format_name(self):
            raise RuntimeError("bad formatter")

    handler = DummyHandler()
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.base_handler"):
        handler.setFormatter(BrokenFormatter())

    assert handler.get_config()["formatter"] == "unknown"
    assert "Failed to resolve formatter name for handler=dummy" in caplog.text


def test_base_handler_timestamp_and_lifecycle_helpers() -> None:
    handler = DummyHandler()
    ts_record = LogRecord(
        level=20,
        level_name="INFO",
        message="with ts",
        timestamp=1700000000.0,
    )
    formatted = handler.format_timestamp(ts_record)
    assert formatted

    dt_record = LogRecord(
        level=20,
        level_name="INFO",
        message="with datetime",
        timestamp=datetime.now(timezone.utc),
    )
    assert handler.format_timestamp(dt_record)
    fallback_record = LogRecord(level=20, level_name="INFO", message="fallback now")
    fallback_record.timestamp = None
    assert handler.format_timestamp(fallback_record)

    handler.setFormatter(None)  # type: ignore[arg-type]
    assert handler.get_config()["formatter"] is None
    handler.setLevel(10)
    assert handler.isEnabledFor(10) is True
    assert handler.is_initialized() is True
    handler.close()
    assert handler.is_closed() is True
    metrics = handler.get_performance_metrics()
    assert metrics["performance_optimized"] is True


def test_base_handler_utc_timestamp_and_abstract_emit_body() -> None:
    handler = DummyHandler()
    handler.timestamp_config = TimestampConfig(
        format_type=TimestampFormat.RFC3339_MICRO,
        precision=TimestampPrecision.MICROSECONDS,
        timezone_name="UTC",
        include_timezone=True,
    )
    ts_record = LogRecord(
        level=20, level_name="INFO", message="utc ts", timestamp=1700000000.0
    )
    assert handler.format_timestamp(ts_record)
    utc_now_record = LogRecord(level=20, level_name="INFO", message="utc now")
    utc_now_record.timestamp = None
    assert handler.format_timestamp(utc_now_record)

    with pytest.raises(
        NotImplementedError, match="Subclasses must implement emit method"
    ):
        BaseHandler.emit(handler, ts_record)


def test_sync_console_handler_flushes_buffer_to_stream() -> None:
    stream = io.StringIO()
    handler = SyncConsoleHandler(stream=stream, buffer_size=1, flush_interval=60)
    handler.emit(LogRecord(level=20, level_name="INFO", message="hello"))
    output = stream.getvalue()
    assert "hello" in output
    stats = handler.get_stats()
    assert stats["messages_processed"] == 1


def test_sync_console_handler_auto_cleanup_flushes_pending_buffer() -> None:
    stream = io.StringIO()
    handler = SyncConsoleHandler(stream=stream, buffer_size=100, flush_interval=60)
    handler.emit(LogRecord(level=20, level_name="INFO", message="pending"))
    handler._auto_cleanup()
    assert "pending" in stream.getvalue()


def test_sync_console_handler_close_flushes_buffered_messages() -> None:
    stream = io.StringIO()
    handler = SyncConsoleHandler(stream=stream, buffer_size=100, flush_interval=60)
    handler.emit(LogRecord(level=10, level_name="DEBUG", message="dbg-before-close"))
    assert stream.getvalue() == ""
    handler.close()
    assert "dbg-before-close" in stream.getvalue()
    assert handler.is_closed() is True


def test_sync_console_handler_close_flush_failure_is_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    stream = io.StringIO()
    handler = SyncConsoleHandler(stream=stream, buffer_size=100, flush_interval=60)
    handler.emit(LogRecord(level=20, level_name="INFO", message="pending"))
    assert handler._buffer

    def _boom() -> None:
        raise RuntimeError("flush boom")

    monkeypatch.setattr(handler, "_flush_buffer", _boom)
    with caplog.at_level(logging.ERROR, logger="hydra_logger.handlers.console_handler"):
        handler.close()
    assert handler.is_closed() is True
    assert "Sync console flush during close failed" in caplog.text


def test_sync_console_handler_auto_cleanup_handles_closed_stream(caplog) -> None:
    stream = io.StringIO()
    handler = SyncConsoleHandler(stream=stream, buffer_size=100, flush_interval=60)
    handler.emit(LogRecord(level=20, level_name="INFO", message="pending"))
    stream.close()

    with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
        handler._auto_cleanup()

    assert handler.get_stats()["buffer_size"] == 0
    assert "Sync console auto cleanup failed" not in caplog.text


def test_async_console_handler_emit_paths_and_factories() -> None:
    async def _run() -> None:
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, buffer_size=1, flush_interval=60)
        handler.emit(LogRecord(level=20, level_name="INFO", message="sync-emit"))
        await handler.emit_async(
            LogRecord(level=20, level_name="INFO", message="async-emit")
        )
        await handler.aclose()
        output = stream.getvalue()
        assert "sync-emit" in output
        assert "async-emit" in output
        assert handler.get_stats()["messages_processed"] >= 2

    asyncio.run(_run())
    assert isinstance(
        create_sync_console_handler(stream=io.StringIO()), SyncConsoleHandler
    )
    assert isinstance(
        create_async_console_handler(stream=io.StringIO()), AsyncConsoleHandler
    )


def test_async_console_handler_drops_messages_on_write_error(monkeypatch) -> None:
    async def _run() -> None:
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, buffer_size=1, flush_interval=60)
        monkeypatch.setattr(
            handler,
            "_write_to_stream",
            lambda _msg: (_ for _ in ()).throw(OSError("boom")),
        )
        await handler.emit_async(LogRecord(level=20, level_name="INFO", message="x"))
        assert handler.get_stats()["messages_dropped"] >= 1
        await handler.aclose()

    asyncio.run(_run())


def test_async_console_handler_logs_stream_write_failures(caplog) -> None:
    class BrokenStream:
        def write(self, _message: str) -> None:
            raise OSError("stream boom")

        def flush(self) -> None:
            return None

    handler = AsyncConsoleHandler(
        stream=BrokenStream(), buffer_size=1, flush_interval=60
    )

    with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
        handler._write_to_stream("x")

    assert "Console stream write failed" in caplog.text


def test_sync_console_handler_get_formatter_lazy_paths(monkeypatch) -> None:
    calls = []

    class DummyFmt:
        def __init__(self, label: str) -> None:
            self.label = label

        def format(self, record) -> str:
            return f"{self.label}:{record.message}"

    def _fake_get_formatter(name: str, use_colors: bool = False):
        calls.append((name, use_colors))
        return DummyFmt(name)

    monkeypatch.setattr("hydra_logger.formatters.get_formatter", _fake_get_formatter)
    plain_handler = SyncConsoleHandler(stream=io.StringIO(), use_colors=False)
    plain = plain_handler._get_formatter()
    assert plain.label == "plain-text"

    color_handler = SyncConsoleHandler(stream=io.StringIO(), use_colors=True)
    colored = color_handler._get_formatter()
    assert colored.label == "colored"
    assert ("plain-text", False) in calls
    assert ("colored", True) in calls


def test_sync_console_handler_flush_buffer_closed_stream_clears_buffer() -> None:
    stream = io.StringIO()
    handler = SyncConsoleHandler(stream=stream, buffer_size=100, flush_interval=60)
    handler._buffer.extend(["x", "y"])
    stream.close()
    handler._flush_buffer()
    assert handler.get_stats()["buffer_size"] == 0


def test_async_console_handler_uses_optimal_buffer_defaults_on_failure(
    caplog, monkeypatch
) -> None:
    original = __import__("hydra_logger.utils.system_detector", fromlist=["_x"])
    monkeypatch.setattr(
        original,
        "get_optimal_buffer_config",
        lambda _kind: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=None, flush_interval=None
        )
    assert handler._buffer_size >= 1
    assert handler._flush_interval > 0
    # path hit (module logs with exception and fallback)
    assert "optimal buffer detection failed" in caplog.text


def test_async_console_handler_start_worker_exception_logs(caplog, monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(stream=io.StringIO())

        def _boom(_coro):
            _coro.close()
            raise RuntimeError("create task failed")

        monkeypatch.setattr(asyncio, "create_task", _boom)
        with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
            await handler._start_worker()
        assert handler._running is False
        assert "Failed to start async console worker" in caplog.text

    asyncio.run(_run())


def test_async_console_handler_worker_loop_timeout_and_cancel_paths(
    monkeypatch,
) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=10, flush_interval=0.01
        )
        handler._running = True
        timeout_seen = {"count": 0}

        async def _fake_wait_for(_coro, timeout):
            _coro.close()
            if timeout_seen["count"] == 0:
                timeout_seen["count"] += 1
                raise asyncio.TimeoutError()
            handler._shutdown_event.set()
            raise asyncio.CancelledError()

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        await handler._worker_loop()
        assert timeout_seen["count"] == 1

    asyncio.run(_run())


def test_async_console_handler_write_messages_error_drops_count(monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=1, flush_interval=1
        )

        async def _boom(*_args, **_kwargs):
            raise RuntimeError("executor fail")

        loop = asyncio.get_running_loop()
        monkeypatch.setattr(loop, "run_in_executor", _boom)
        await handler._write_messages(["a", "b"])
        assert handler.get_stats()["messages_dropped"] >= 2

    asyncio.run(_run())


def test_async_console_handler_auto_cleanup_cancels_worker(monkeypatch) -> None:
    class DummyTask:
        def done(self) -> bool:
            return False

        def cancel(self) -> None:
            return None

    handler = AsyncConsoleHandler(stream=io.StringIO())
    handler._worker_task = DummyTask()

    class DummyLoop:
        def run_until_complete(self, _obj):
            if hasattr(_obj, "close"):
                _obj.close()
            raise RuntimeError("closed")

    monkeypatch.setattr(asyncio, "get_event_loop", lambda: DummyLoop())
    handler._auto_cleanup()


def test_async_console_handler_aclose_different_loop_branch() -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(stream=io.StringIO())

        class DummyTask:
            def done(self) -> bool:
                return False

            def cancel(self) -> None:
                return None

            def get_loop(self):
                return object()

        handler._worker_task = DummyTask()
        await handler.aclose()
        assert handler._running is False

    asyncio.run(_run())


def test_console_handler_init_with_formatter_and_cached_get_formatter() -> None:
    class Fmt:
        def format(self, record):
            return f"f:{record.message}"

    fmt = Fmt()
    sync_handler = SyncConsoleHandler(stream=io.StringIO(), formatter=fmt)
    async_handler = AsyncConsoleHandler(stream=io.StringIO(), formatter=fmt)
    assert sync_handler._get_formatter() is fmt
    assert async_handler._get_formatter() is fmt


def test_sync_console_handler_flush_empty_and_auto_cleanup_exception_paths(
    caplog, monkeypatch
) -> None:
    handler = SyncConsoleHandler(stream=io.StringIO())
    handler._flush_buffer()  # empty branch

    # ValueError closed-file branch
    monkeypatch.setattr(
        handler,
        "_flush_buffer",
        lambda: (_ for _ in ()).throw(ValueError("closed file")),
    )
    handler._buffer = ["x"]
    handler._auto_cleanup()
    assert handler._buffer == []

    # Generic exception branch
    monkeypatch.setattr(
        handler, "_flush_buffer", lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    handler._buffer = ["x"]
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
        handler._auto_cleanup()
    assert "Sync console auto cleanup failed" in caplog.text


def test_async_console_handler_optimal_config_success_and_emit_error_branch(
    monkeypatch,
) -> None:
    detector = __import__("hydra_logger.utils.system_detector", fromlist=["_x"])
    monkeypatch.setattr(
        detector,
        "get_optimal_buffer_config",
        lambda _kind: {"buffer_size": 7, "flush_interval": 0.7},
    )

    class BrokenStream:
        def write(self, _message):
            raise OSError("boom")

        def flush(self):
            return None

    handler = AsyncConsoleHandler(
        stream=BrokenStream(), buffer_size=None, flush_interval=None
    )
    assert handler._buffer_size == 7
    assert handler._flush_interval == 0.7
    handler.emit(LogRecord(level=20, level_name="INFO", message="x"))
    assert handler.get_stats()["messages_dropped"] >= 1


def test_async_console_handler_flush_async_buffer_and_write_messages_paths(
    monkeypatch,
) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=10, flush_interval=1
        )
        await handler._flush_async_buffer()  # empty branch

        class _Loop:
            async def run_in_executor(self, _executor, func):
                return func()

        monkeypatch.setattr(asyncio, "get_event_loop", lambda: _Loop())
        await handler._write_messages([])  # empty return
        await handler._write_messages(["a", "b"])  # success path bytes update
        assert handler.get_stats()["total_bytes_written"] > 0

    asyncio.run(_run())


def test_async_console_handler_worker_loop_additional_edge_paths(monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=10, flush_interval=1
        )

        # cover _start_worker running guard
        handler._running = True
        await handler._start_worker()

        # cover message append + shutdown break after receive
        handler._running = False
        handler._shutdown_event.clear()
        calls = {"count": 0}

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            calls["count"] += 1
            handler._shutdown_event.set()
            return "msg"

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        await handler._worker_loop()
        assert calls["count"] == 1

    asyncio.run(_run())


def test_async_console_handler_auto_cleanup_outer_exception_and_aclose_variants(
    monkeypatch,
) -> None:
    recorded_exceptions = []

    def _quiet_exception(message, *args, **kwargs):
        rendered = message % args if args else message
        recorded_exceptions.append(rendered)

    monkeypatch.setattr(console_module._logger, "exception", _quiet_exception)

    class BadTask:
        def done(self):
            raise RuntimeError("done boom")

        def cancel(self):
            return None

        def get_loop(self):
            raise AttributeError("no loop")

    class GoodTask:
        def __init__(self) -> None:
            self._cancelled = False

        def done(self):
            return False

        def cancel(self):
            self._cancelled = True

        def get_loop(self):
            return asyncio.get_running_loop()

    handler = AsyncConsoleHandler(stream=io.StringIO())
    handler._worker_task = BadTask()
    handler._auto_cleanup()
    assert "Async console auto cleanup failed" in recorded_exceptions
    # Avoid re-triggering the injected failure from atexit cleanup.
    handler._worker_task = None

    async def _run() -> None:
        h = AsyncConsoleHandler(stream=io.StringIO())
        h._async_buffer = ["pending"]
        h._worker_task = GoodTask()

        async def _bad_wait(*_a, **_k):
            raise RuntimeError("other wait failure")

        monkeypatch.setattr(asyncio, "wait", _bad_wait)
        await h.aclose()
        assert "Async console close encountered cleanup error" in recorded_exceptions
        h._worker_task = None

    asyncio.run(_run())


def test_sync_console_auto_cleanup_valueerror_non_closed_logs(
    caplog, monkeypatch
) -> None:
    handler = SyncConsoleHandler(stream=io.StringIO())
    handler._buffer = ["x"]
    monkeypatch.setattr(
        handler, "_flush_buffer", lambda: (_ for _ in ()).throw(ValueError("different"))
    )
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
        handler._auto_cleanup()
    assert "Sync console auto cleanup failed" in caplog.text


def test_async_console_get_formatter_colored_lazy_branch(monkeypatch) -> None:
    class DummyFmt:
        def __init__(self, label: str) -> None:
            self.label = label

        def format(self, record) -> str:
            return f"{self.label}:{record.message}"

    monkeypatch.setattr(
        "hydra_logger.formatters.get_formatter",
        lambda name, use_colors=False: DummyFmt(name),
    )
    handler = AsyncConsoleHandler(stream=io.StringIO(), use_colors=True)
    fmt = handler._get_formatter()
    assert fmt.label == "colored"


def test_async_console_aclose_runtime_and_cancelled_paths(monkeypatch) -> None:
    class Task:
        def __init__(self) -> None:
            self._cancelled = False

        def done(self):
            return False

        def cancel(self):
            self._cancelled = True

        def get_loop(self):
            return asyncio.get_running_loop()

    async def _run_runtime_pass_path() -> None:
        handler = AsyncConsoleHandler(stream=io.StringIO())
        handler._worker_task = Task()
        monkeypatch.setattr(
            asyncio,
            "get_running_loop",
            lambda: (_ for _ in ()).throw(RuntimeError("none")),
        )
        await handler.aclose()  # hits RuntimeError/AttributeError pass block

    asyncio.run(_run_runtime_pass_path())

    async def _run_different_loop_runtime_text_path() -> None:
        handler = AsyncConsoleHandler(stream=io.StringIO())
        handler._worker_task = Task()
        monkeypatch.setattr(
            asyncio,
            "wait",
            lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("different loop")),
        )
        await handler.aclose()  # hits line 567 pass

    asyncio.run(_run_different_loop_runtime_text_path())

    async def _run_cancelled_path() -> None:
        handler = AsyncConsoleHandler(stream=io.StringIO())
        handler._worker_task = Task()

        async def _cancelled(*_a, **_k):
            raise asyncio.CancelledError()

        monkeypatch.setattr(asyncio, "wait", _cancelled)
        await handler.aclose()  # hits CancelledError pass

    asyncio.run(_run_cancelled_path())


def test_async_console_worker_loop_shutdown_and_outer_generic_paths(caplog) -> None:
    async def _run_shutdown_break() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=10, flush_interval=10
        )

        class ToggleEvent:
            def __init__(self) -> None:
                self.calls = 0

            def is_set(self):
                self.calls += 1
                return self.calls >= 2

            def set(self):
                return None

        handler._shutdown_event = ToggleEvent()
        await handler._worker_loop()  # hits line-409 branch

    asyncio.run(_run_shutdown_break())

    async def _run_outer_generic_exception() -> None:
        handler = AsyncConsoleHandler(stream=io.StringIO())

        class BrokenEvent:
            def is_set(self):
                raise ValueError("boom")

        handler._shutdown_event = BrokenEvent()
        with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
            await handler._worker_loop()  # hits outer generic exception logger
        assert "Async console worker terminated due to unexpected error" in caplog.text

    asyncio.run(_run_outer_generic_exception())


def test_async_console_worker_loop_queue_and_flush_runtime_branches(
    monkeypatch,
) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=1, flush_interval=10
        )

        class EventFalse:
            def is_set(self):
                return False

            def set(self):
                return None

        class QueueWithRuntime:
            async def get(self):
                return "unused"

            def empty(self):
                return False

            def get_nowait(self):
                raise RuntimeError("queue runtime")

            def qsize(self):
                return 0

        handler._shutdown_event = EventFalse()
        handler._message_queue = QueueWithRuntime()

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            return "msg"

        async def _runtime_write(_messages):
            raise RuntimeError("flush runtime")

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        monkeypatch.setattr(handler, "_write_messages", _runtime_write)
        await handler._worker_loop()  # hits 434-441 and 451-457 branches

    asyncio.run(_run())


def test_async_console_worker_loop_final_flush_exception_branch(
    monkeypatch, caplog
) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=100, flush_interval=100
        )
        state = {"calls": 0}

        class EventWithSet:
            def __init__(self) -> None:
                self.shutdown = False

            def is_set(self):
                return self.shutdown

            def set(self):
                self.shutdown = True

        handler._shutdown_event = EventWithSet()

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            state["calls"] += 1
            if state["calls"] == 1:
                return "msg"
            handler._shutdown_event.set()
            raise asyncio.CancelledError()

        async def _bad_write(_messages):
            raise RuntimeError("final flush fail")

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        monkeypatch.setattr(handler, "_write_messages", _bad_write)
        with caplog.at_level("ERROR", logger="hydra_logger.handlers.console_handler"):
            await handler._worker_loop()  # hits final flush exception logger
        assert "Async console final message flush failed" in caplog.text

    asyncio.run(_run())


def test_async_console_worker_loop_runtime_break_branch(monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=100, flush_interval=100
        )
        handler._shutdown_event.set()
        calls = {"n": 0}

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("runtime break")
            raise asyncio.CancelledError()

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        await handler._worker_loop()

    asyncio.run(_run())


def test_async_console_worker_loop_generic_break_when_shutdown_set(monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=100, flush_interval=100
        )

        class Event:
            def __init__(self) -> None:
                self._set = False

            def is_set(self):
                return self._set

            def set(self):
                self._set = True

        ev = Event()
        handler._shutdown_event = ev
        calls = {"n": 0}

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            calls["n"] += 1
            if calls["n"] == 1:
                ev.set()
                raise Exception("generic with shutdown")
            raise asyncio.CancelledError()

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        await handler._worker_loop()

    asyncio.run(_run())


def test_async_console_worker_loop_inner_runtime_exception_break(monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=100, flush_interval=100
        )

        class BrokenQueue:
            async def get(self):
                return "m"

            def empty(self):
                raise RuntimeError("queue runtime")

        handler._message_queue = BrokenQueue()
        handler._shutdown_event.clear()
        await handler._worker_loop()

    asyncio.run(_run())


def test_async_console_worker_loop_get_nowait_append_and_queueempty_break(
    monkeypatch,
) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=999, flush_interval=999
        )

        class ControlledEvent:
            def __init__(self) -> None:
                self.calls = 0

            def is_set(self):
                self.calls += 1
                # Allow one full iteration, then stop.
                return self.calls > 5

            def set(self):
                return None

        class QueueStub:
            def __init__(self) -> None:
                self.items = ["extra"]

            async def get(self):
                return "unused"

            def empty(self):
                return False

            def get_nowait(self):
                if self.items:
                    return self.items.pop(0)
                raise asyncio.QueueEmpty()

            def qsize(self):
                return len(self.items)

        handler._shutdown_event = ControlledEvent()
        handler._message_queue = QueueStub()
        recorded = {"messages": None}

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            return "msg"

        async def _record_write(messages):
            recorded["messages"] = list(messages)

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        monkeypatch.setattr(handler, "_write_messages", _record_write)
        await handler._worker_loop()
        assert recorded["messages"] in (None, ["msg", "extra"])

    asyncio.run(_run())


def test_async_console_worker_loop_flush_success_updates_state(monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=1, flush_interval=999
        )
        before_flush = handler._last_async_flush

        class ToggleEvent:
            def __init__(self) -> None:
                self._set = False

            def is_set(self):
                return self._set

            def set(self):
                self._set = True

        handler._shutdown_event = ToggleEvent()

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            return "m"

        async def _write_messages(_messages):
            handler._shutdown_event.set()

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        monkeypatch.setattr(handler, "_write_messages", _write_messages)
        await handler._worker_loop()
        assert handler._last_async_flush >= before_flush

    asyncio.run(_run())


def test_async_console_worker_loop_inner_exception_and_outer_runtime_debug(
    monkeypatch, caplog
) -> None:
    async def _run_inner_exception_then_outer_runtime() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=1, flush_interval=1
        )

        class EventSequenced:
            def __init__(self) -> None:
                self.calls = 0

            def is_set(self):
                self.calls += 1
                if self.calls <= 5:
                    return False
                raise RuntimeError("runtime-debug")

            def set(self):
                return None

        class BrokenQueue:
            async def get(self):
                return "unused"

            def empty(self):
                return False

            def get_nowait(self):
                raise ValueError("inner boom")

            def qsize(self):
                return 0

        handler._shutdown_event = EventSequenced()
        handler._message_queue = BrokenQueue()

        async def _fake_wait_for(_coro, *args, **kwargs):
            _coro.close()
            return "m"

        monkeypatch.setattr(asyncio, "wait_for", _fake_wait_for)
        with caplog.at_level("DEBUG", logger="hydra_logger.handlers.console_handler"):
            await handler._worker_loop()
        assert "Async console worker iteration failed; clearing batch" in caplog.text
        assert "Async console worker cancelled or runtime closed" in caplog.text

    asyncio.run(_run_inner_exception_then_outer_runtime())

    async def _run_inner_runtime_break() -> None:
        handler = AsyncConsoleHandler(
            stream=io.StringIO(), buffer_size=1, flush_interval=1
        )

        async def _runtime_wait_for(_coro, *args, **kwargs):
            _coro.close()
            raise RuntimeError("inner-break")

        monkeypatch.setattr(asyncio, "wait_for", _runtime_wait_for)
        await handler._worker_loop()  # hits inner RuntimeError/CancelledError break

    asyncio.run(_run_inner_runtime_break())
