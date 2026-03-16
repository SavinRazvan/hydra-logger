"""
Role: Pytest coverage for file and null handler behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates file write lifecycle and null handler formatter flags.
"""

from pathlib import Path
import asyncio

from hydra_logger.formatters.structured_formatter import CsvFormatter
from hydra_logger.handlers.file_handler import AsyncFileHandler, FileHandler, SyncFileHandler
from hydra_logger.handlers.null_handler import NullHandler
from hydra_logger.types.records import LogRecord


def test_sync_file_handler_writes_and_closes(tmp_path: Path) -> None:
    log_path = tmp_path / "app.log"
    handler = SyncFileHandler(filename=str(log_path), buffer_size=1, flush_interval=60.0)
    handler.emit(LogRecord(level=20, level_name="INFO", message="file message"))
    handler.close()

    content = log_path.read_text(encoding="utf-8")
    assert "file message" in content
    stats = handler.get_stats()
    assert stats["messages_processed"] >= 1


def test_null_handler_tracks_special_formatter_capabilities() -> None:
    handler = NullHandler()
    handler.setFormatter(CsvFormatter())
    assert handler._is_csv_formatter is True
    assert handler._needs_special_handling is True
    handler.emit(LogRecord(level=20, level_name="INFO", message="ignored"))


def test_sync_file_handler_writes_csv_headers_once_for_new_file(tmp_path: Path) -> None:
    log_path = tmp_path / "events.csv"
    handler = SyncFileHandler(filename=str(log_path), buffer_size=1, flush_interval=60.0)
    handler.setFormatter(CsvFormatter(include_headers=True))
    handler.emit(LogRecord(level=20, level_name="INFO", message="first event"))
    handler.emit(LogRecord(level=20, level_name="INFO", message="second event"))
    handler.close()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert lines
    assert lines[0].startswith("timestamp")
    assert len([line for line in lines if line.startswith("timestamp")]) == 1


def test_sync_file_handler_falls_back_when_formatter_fails(tmp_path: Path) -> None:
    class BrokenFormatter:
        name = "broken"

        def format(self, _record):
            raise RuntimeError("broken formatter")

    log_path = tmp_path / "fallback.log"
    handler = SyncFileHandler(filename=str(log_path), buffer_size=1, flush_interval=60.0)
    handler.setFormatter(BrokenFormatter())
    handler.emit(LogRecord(level=40, level_name="ERROR", message="fallback event"))
    handler.close()
    content = log_path.read_text(encoding="utf-8")
    assert "fallback event" in content


def test_async_file_handler_emit_async_and_close(tmp_path: Path) -> None:
    async def _run() -> None:
        log_path = tmp_path / "async.log"
        handler = AsyncFileHandler(filename=str(log_path), bulk_size=10, max_queue_size=100)
        await handler.emit_async(LogRecord(level=20, level_name="INFO", message="async file event"))
        await handler.aclose()
        content = log_path.read_text(encoding="utf-8")
        assert "async file event" in content

    asyncio.run(_run())


def test_sync_file_handler_reopens_for_binary_formatter(tmp_path: Path) -> None:
    class BinaryFormatter:
        name = "binary_payload"

        def format(self, _record):
            return b"abc"

    log_path = tmp_path / "binary.log"
    handler = SyncFileHandler(filename=str(log_path), buffer_size=1, flush_interval=60.0)
    handler.setFormatter(BinaryFormatter())
    handler.emit(LogRecord(level=20, level_name="INFO", message="ignored"))
    handler.close()
    assert log_path.read_bytes() == b"abc"


def test_file_handler_emit_async_falls_back_to_sync_handler(tmp_path: Path) -> None:
    async def _run() -> None:
        log_path = tmp_path / "wrapper.log"
        handler = FileHandler(filename=str(log_path))
        await handler.emit_async(LogRecord(level=20, level_name="INFO", message="wrapped"))
        await handler.aclose()
        assert "wrapped" in log_path.read_text(encoding="utf-8")

    asyncio.run(_run())


def test_async_file_handler_drops_messages_when_queue_is_full(tmp_path: Path) -> None:
    handler = AsyncFileHandler(filename=str(tmp_path / "queue.log"), max_queue_size=1)
    handler._running = True
    handler._message_queue.put_nowait("occupied")
    handler.emit(LogRecord(level=20, level_name="INFO", message="dropped"))
    assert handler.get_stats()["messages_dropped"] >= 1
    handler.close()


def test_async_file_handler_direct_write_path_when_worker_start_is_noop(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        log_path = tmp_path / "direct-write.log"
        handler = AsyncFileHandler(filename=str(log_path))
        monkeypatch.setattr(handler, "_start_worker", lambda: None)
        await handler.emit_async(
            LogRecord(level=20, level_name="INFO", message="direct fallback")
        )
        await handler.aclose()
        assert "direct fallback" in log_path.read_text(encoding="utf-8")

    asyncio.run(_run())


def test_async_file_handler_csv_header_check_for_non_empty_file(tmp_path: Path) -> None:
    log_path = tmp_path / "events.csv"
    log_path.write_text("already here\n", encoding="utf-8")
    handler = AsyncFileHandler(filename=str(log_path))
    handler.setFormatter(CsvFormatter(include_headers=True))
    assert handler._check_and_write_csv_headers() is False
    handler.close()
