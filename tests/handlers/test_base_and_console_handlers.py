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
