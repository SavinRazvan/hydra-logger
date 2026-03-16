"""
Role: Pytest coverage for base and console handler behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates level filtering and buffered console flush lifecycle.
"""

import io
import asyncio
from datetime import datetime, timezone

from hydra_logger.handlers.base_handler import BaseHandler
from hydra_logger.handlers.console_handler import (
    AsyncConsoleHandler,
    SyncConsoleHandler,
    create_async_console_handler,
    create_sync_console_handler,
)
from hydra_logger.types.records import LogRecord


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
    assert handler.format_timestamp(LogRecord(level=20, level_name="INFO", message="fallback now"))

    handler.setFormatter(None)  # type: ignore[arg-type]
    assert handler.get_config()["formatter"] is None
    handler.setLevel(10)
    assert handler.isEnabledFor(10) is True
    assert handler.is_initialized() is True
    handler.close()
    assert handler.is_closed() is True
    metrics = handler.get_performance_metrics()
    assert metrics["performance_optimized"] is True


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
    assert isinstance(create_sync_console_handler(stream=io.StringIO()), SyncConsoleHandler)
    assert isinstance(
        create_async_console_handler(stream=io.StringIO()), AsyncConsoleHandler
    )


def test_async_console_handler_drops_messages_on_write_error(monkeypatch) -> None:
    async def _run() -> None:
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, buffer_size=1, flush_interval=60)
        monkeypatch.setattr(handler, "_write_to_stream", lambda _msg: (_ for _ in ()).throw(OSError("boom")))
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

    handler = AsyncConsoleHandler(stream=BrokenStream(), buffer_size=1, flush_interval=60)

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


def test_async_console_handler_worker_loop_timeout_and_cancel_paths(monkeypatch) -> None:
    async def _run() -> None:
        handler = AsyncConsoleHandler(stream=io.StringIO(), buffer_size=10, flush_interval=0.01)
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
        handler = AsyncConsoleHandler(stream=io.StringIO(), buffer_size=1, flush_interval=1)

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
