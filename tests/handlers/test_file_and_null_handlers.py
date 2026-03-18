"""
Role: Pytest coverage for file and null handler behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates file write lifecycle and null handler formatter flags.
"""

import builtins
import sys
import types
from pathlib import Path
import asyncio
from types import SimpleNamespace

from hydra_logger.formatters.structured_formatter import CsvFormatter
from hydra_logger.handlers import file_handler as file_module
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


def test_null_handler_resets_formatter_flags_and_async_noop() -> None:
    class JsonLikeFormatter:
        def write_header(self):
            return None

    class StreamingFormatter:
        def format_for_streaming(self, _record):
            return "x"

    async def _run() -> None:
        handler = NullHandler()
        handler.setFormatter(JsonLikeFormatter())
        assert handler._is_json_formatter is True
        assert handler._needs_special_handling is True

        handler.setFormatter(StreamingFormatter())
        assert handler._is_streaming_formatter is True
        assert handler._needs_special_handling is True

        handler.setFormatter(None)
        assert handler._needs_special_handling is False
        handler.handle(LogRecord(level=20, level_name="INFO", message="ignored"))
        await handler.emit_async(LogRecord(level=20, level_name="INFO", message="ignored"))

    asyncio.run(_run())


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


def test_async_file_handler_logs_warning_when_queue_is_full(caplog, tmp_path: Path) -> None:
    handler = AsyncFileHandler(filename=str(tmp_path / "warn-queue.log"), max_queue_size=1)
    handler._running = True
    handler._message_queue.put_nowait("occupied")
    with caplog.at_level("WARNING", logger="hydra_logger.handlers.file_handler"):
        handler.emit(LogRecord(level=20, level_name="INFO", message="drop-me"))
    assert "Async file handler queue full; dropped=1" in caplog.text
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


def test_sync_file_handler_format_message_variants(tmp_path: Path) -> None:
    class PlainFormatter:
        name = "plain"

        def format(self, _record):
            return "formatted"

    class BytesFormatter:
        name = "binary"

        def format(self, _record):
            return b"\x01\x02"

    class BrokenFormatter:
        name = "broken"

        def format(self, _record):
            raise RuntimeError("format failed")

    record = LogRecord(level=20, level_name="INFO", message="msg")
    handler = SyncFileHandler(filename=str(tmp_path / "variants.log"), buffer_size=10)

    handler.setFormatter(PlainFormatter())
    assert handler._format_message(record).endswith("\n")

    handler.setFormatter(BytesFormatter())
    assert handler._format_message(record) == b"\x01\x02"

    handler.setFormatter(BrokenFormatter())
    fallback = handler._format_message(record)
    assert "msg" in fallback
    handler.close()


def test_sync_file_handler_emit_handles_invalid_file_handle(tmp_path: Path) -> None:
    handler = SyncFileHandler(filename=str(tmp_path / "invalid.log"), buffer_size=1)
    handler._file_handle.close()
    handler._file_handle = None
    handler.emit(LogRecord(level=20, level_name="INFO", message="ignored"))
    assert handler.get_stats()["messages_processed"] == 0
    handler.close()


def test_sync_file_handler_logs_invalid_file_handle(caplog, tmp_path: Path) -> None:
    handler = SyncFileHandler(filename=str(tmp_path / "invalid-log2.log"), buffer_size=1)
    handler._file_handle.close()
    handler._file_handle = None
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.file_handler"):
        handler.emit(LogRecord(level=20, level_name="INFO", message="ignored"))
    assert "Cannot emit to closed or invalid file handle" in caplog.text
    handler.close()


def test_async_file_handler_csv_header_write_failure_returns_false(tmp_path: Path) -> None:
    class BrokenCsvFormatter:
        include_headers = True

        def format_headers(self):
            raise RuntimeError("header fail")

        def format(self, record):
            return record.message

    handler = AsyncFileHandler(filename=str(tmp_path / "broken-header.csv"))
    handler.setFormatter(BrokenCsvFormatter())
    assert handler._check_and_write_csv_headers() is False
    handler.close()


def test_file_handler_wrapper_async_fallbacks_when_underlying_is_sync(tmp_path: Path) -> None:
    class SyncOnlyHandler:
        def __init__(self) -> None:
            self.emitted = []
            self.closed = False

        def emit(self, record) -> None:
            self.emitted.append(record.message)

        def close(self) -> None:
            self.closed = True

        def get_stats(self):
            return {"kind": "sync-only"}

        def setFormatter(self, formatter) -> None:
            self.formatter = formatter

    async def _run() -> None:
        handler = FileHandler(filename=str(tmp_path / "wrapper-fallback.log"))
        handler._handler = SyncOnlyHandler()
        await handler.emit_async(LogRecord(level=20, level_name="INFO", message="fallback"))
        await handler.aclose()
        assert handler.get_stats()["kind"] == "sync-only"
        assert handler._handler.closed is True
        assert "fallback" in handler._handler.emitted

    asyncio.run(_run())


def test_sync_file_handler_uses_optimal_config_when_explicit_values_missing(
    monkeypatch, tmp_path: Path
) -> None:
    detector = __import__("hydra_logger.utils.system_detector", fromlist=["_x"])
    monkeypatch.setattr(
        detector,
        "get_optimal_buffer_config",
        lambda _kind: {"buffer_size": 3, "flush_interval": 0.1},
    )
    handler = SyncFileHandler(
        filename=str(tmp_path / "opt.log"), buffer_size=None, flush_interval=None
    )
    assert handler._buffer_size == 3
    assert handler._flush_interval == 0.1
    handler.close()


def test_sync_file_handler_set_formatter_reopen_failure_sets_invalid_handle(
    monkeypatch, tmp_path: Path
) -> None:
    class BinaryFormatter:
        name = "binary-format"

        def format(self, _record):
            return b"x"

    original_open = builtins.open
    call_count = {"count": 0}

    def _fake_open(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] >= 2:
            raise OSError("cannot reopen")
        return original_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", _fake_open)
    handler = SyncFileHandler(filename=str(tmp_path / "reopen.log"))
    handler.setFormatter(BinaryFormatter())
    assert handler._file_handle is None


def test_sync_file_handler_flush_closed_and_invalid_handles(tmp_path: Path) -> None:
    handler = SyncFileHandler(filename=str(tmp_path / "flush.log"))
    handler._buffer.append("abc\n")
    handler._file_handle.close()
    closed_handle = SimpleNamespace(closed=True)
    handler._file_handle = closed_handle
    handler._flush_buffer()
    assert len(handler._buffer) == 1

    class BrokenFile:
        closed = False

        def write(self, _msg):
            raise OSError("broken")

        def flush(self):
            return None

    handler._file_handle = BrokenFile()
    handler._flush_buffer()
    handler.close()


def test_async_file_handler_helpers_cover_transfer_flush_and_sleep(tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(
            filename=str(tmp_path / "helper.log"),
            use_threading=False,
            memory_buffer_size=1,
            disk_flush_interval=0.0,
        )
        handler._memory_buffer = ["m1\n"]
        await handler._smart_memory_to_disk_transfer()
        assert handler._disk_buffer == ["m1\n"]

        await handler._fast_disk_flush()
        assert handler._disk_buffer == []

        handler._message_buffer = ["x"]
        handler._overflow_buffer = []
        handler._current_batch_size = 1
        handler._current_flush_interval = 999
        assert handler._should_flush_smart() is True
        assert handler._calculate_smart_sleep() in (0.001, 0.01, 0.1)
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_flush_batch_binary_and_text_paths(tmp_path: Path) -> None:
    async def _run() -> None:
        binary_path = tmp_path / "bin.log"
        binary_handler = AsyncFileHandler(filename=str(binary_path), use_threading=False)
        binary_handler._message_buffer = [b"a", b"b"]
        await binary_handler._flush_batch()
        assert binary_handler._total_bytes_written == 2
        await binary_handler.aclose()

        text_path = tmp_path / "txt.log"
        text_handler = AsyncFileHandler(filename=str(text_path), use_threading=False)
        text_handler._message_buffer = ["line1\n", "line2\n"]
        await text_handler._flush_batch()
        await text_handler.aclose()
        assert "line1" in text_path.read_text(encoding="utf-8")

    asyncio.run(_run())


def test_async_file_handler_write_methods_and_threaded_lock_guard(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "writes.log"), use_threading=False)
        await handler._write_messages_async(["a\n", "b\n"])
        assert handler._total_bytes_written == 4
        await handler._write_messages_to_file(["c\n"])
        await handler.aclose()

    asyncio.run(_run())

    guard = AsyncFileHandler(filename=str(tmp_path / "guard.log"), use_threading=True)
    guard._file_lock = None
    try:
        guard._write_messages_threaded(["x\n"])
    except RuntimeError as exc:
        assert "File lock unavailable" in str(exc)
    else:
        raise AssertionError("Expected lock guard RuntimeError")
    guard.close()


def test_async_file_handler_emit_and_flush_error_paths(monkeypatch, tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "errors.log"), max_queue_size=1)
        monkeypatch.setattr(handler, "_format_message", lambda _r: (_ for _ in ()).throw(RuntimeError("fmt")))
        handler.emit(LogRecord(level=20, level_name="INFO", message="x"))
        assert handler.get_stats()["messages_dropped"] >= 1

        handler2 = AsyncFileHandler(filename=str(tmp_path / "flush-errors.log"))
        monkeypatch.setattr(handler2, "_flush_batch", lambda: (_ for _ in ()).throw(RuntimeError("flush")))
        handler2._message_buffer = ["x"]
        await handler2.flush()
        await handler2.aclose()

    asyncio.run(_run())


def test_async_file_handler_close_cleanup_helpers(tmp_path: Path) -> None:
    handler = AsyncFileHandler(filename=str(tmp_path / "cleanup.log"))
    handler._shutdown_event.set()
    asyncio.run(handler.close_async())
    handler._auto_cleanup()
    handler._pytest_cleanup()
    handler.__del__()
    handler.close()


def test_async_file_handler_optimization_and_parameter_adjustment_branches(
    tmp_path: Path,
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "optimize.log"), use_threading=False)

        # Build enough samples to trigger both adjustment branches.
        handler._performance_samples = [
            {"duration": 0.01, "messages": 200, "timestamp": 1.0} for _ in range(12)
        ]
        original_batch = handler._current_batch_size
        await handler._parameter_adjustment()
        assert handler._current_batch_size >= original_batch

        handler._performance_samples = [
            {"duration": 1.0, "messages": 1, "timestamp": 1.0} for _ in range(12)
        ]
        await handler._parameter_adjustment()
        assert handler._current_batch_size >= handler._min_batch_size

        # _optimization should trim sample history.
        handler._performance_samples = [
            {"duration": 0.1, "messages": 1, "timestamp": 1.0} for _ in range(60)
        ]
        handler._last_performance_check = 0.0
        await handler._optimization(0.0, 1)
        assert len(handler._performance_samples) <= 50
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_flush_smart_and_write_error_paths(monkeypatch, tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "smart-flush.log"), use_threading=False)
        handler._message_buffer = ["a\n"]
        handler._overflow_buffer = ["b\n"]

        async def _broken_write(_messages):
            raise RuntimeError("write fail")

        monkeypatch.setattr(handler, "_write_messages_to_file", _broken_write)
        await handler._flush_batch_smart()
        # On error, current buffer should be preserved into overflow.
        assert handler._overflow_buffer

        handler._message_buffer = ["x\n"]
        handler._overflow_buffer = ["queued-overflow\n"]
        handler._buffer_capacity = 10
        handler._current_batch_size = 100
        handler._current_flush_interval = 999
        assert handler._should_flush_smart() is True
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_start_worker_runtime_and_exception_paths(
    monkeypatch, tmp_path: Path
) -> None:
    handler = AsyncFileHandler(filename=str(tmp_path / "worker.log"), use_threading=False)

    # RuntimeError path: no event loop running.
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: (_ for _ in ()).throw(RuntimeError("no loop")))
    handler._running = False
    handler._worker_tasks = []
    handler._start_worker()
    assert handler._running is False

    # Generic exception path from create_task.
    class BrokenLoop:
        def create_task(self, coro):
            coro.close()
            raise ValueError("bad task")

    monkeypatch.setattr(asyncio, "get_running_loop", lambda: BrokenLoop())
    handler._start_worker()
    assert handler._running is False
    handler.close()


def test_async_file_handler_format_and_emit_queuefull_paths(monkeypatch, tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "format-emit.log"), max_queue_size=1)
        record = LogRecord(level=20, level_name="INFO", message="m")

        # Exercise AsyncFileHandler._format_message branches.
        class PlainFormatter:
            def format(self, _record):
                return "plain"

        class BytesFormatter:
            def format(self, _record):
                return b"\x01"

        class BrokenFormatter:
            def format(self, _record):
                raise RuntimeError("boom")

        handler.setFormatter(PlainFormatter())
        assert handler._format_message(record).endswith("\n")
        handler.setFormatter(BytesFormatter())
        assert handler._format_message(record) == b"\x01"
        handler.setFormatter(BrokenFormatter())
        assert "m" in handler._format_message(record)

        # Queue full path in emit_async.
        handler._running = True
        handler._message_queue.put_nowait("occupied")
        await handler.emit_async(record)
        assert handler.get_stats()["messages_dropped"] >= 1
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_aclose_and_cleanup_fallback_paths(monkeypatch, tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "aclose.log"), use_threading=False)

        class DummyTask:
            def __init__(self) -> None:
                self._done = False

            def done(self):
                return self._done

            def cancel(self):
                self._done = True

        handler._worker_tasks = [DummyTask()]
        monkeypatch.setattr(asyncio, "wait", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("wait fail")))
        monkeypatch.setattr(asyncio, "gather", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("gather fail")))
        await handler.aclose()
        assert handler._running is False

    asyncio.run(_run())

    # cover close() fallback exception branch
    handler2 = AsyncFileHandler(filename=str(tmp_path / "close-fallback.log"), use_threading=False)

    class BrokenEvent:
        def set(self):
            raise RuntimeError("set fail")

    handler2._shutdown_event = BrokenEvent()
    handler2.close()
    # Restore to avoid noisy destructor/atexit traces from intentionally broken event.
    handler2._shutdown_event = asyncio.Event()


def test_file_handler_wrapper_methods_delegate_to_inner(tmp_path: Path) -> None:
    path = tmp_path / "wrapper-delegate.log"
    wrapper = FileHandler(filename=str(path))
    record = LogRecord(level=20, level_name="INFO", message="delegated")
    wrapper.setFormatter(None)
    wrapper.emit(record)
    wrapper.close()
    assert "delegated" in path.read_text(encoding="utf-8")


def test_sync_file_handler_uses_safe_defaults_when_optimal_lookup_fails(
    monkeypatch, tmp_path: Path
) -> None:
    detector = __import__("hydra_logger.utils.system_detector", fromlist=["_x"])
    monkeypatch.setattr(
        detector,
        "get_optimal_buffer_config",
        lambda _kind: (_ for _ in ()).throw(RuntimeError("detector failed")),
    )
    handler = SyncFileHandler(
        filename=str(tmp_path / "fallback-opt.log"),
        buffer_size=None,
        flush_interval=None,
    )
    assert handler._buffer_size == 1000
    assert handler._flush_interval == 1.0
    handler.close()


def test_sync_file_handler_init_logs_directory_and_open_failures(
    monkeypatch, tmp_path: Path, caplog
) -> None:
    monkeypatch.setattr(file_module.os, "makedirs", lambda *_a, **_k: (_ for _ in ()).throw(OSError("mkdir boom")))
    monkeypatch.setattr(
        builtins,
        "open",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("open boom")),
    )
    with caplog.at_level("WARNING", logger="hydra_logger.handlers.file_handler"):
        handler = SyncFileHandler(filename=str(tmp_path / "nested" / "broken.log"))
    assert handler._file_handle is None
    assert "Could not create directory" in caplog.text
    assert "Could not open log file" in caplog.text


def test_sync_file_handler_emit_exception_path_is_logged(
    monkeypatch, tmp_path: Path, caplog
) -> None:
    handler = SyncFileHandler(filename=str(tmp_path / "emit-error.log"), buffer_size=10)
    monkeypatch.setattr(
        handler,
        "_format_message",
        lambda _record: (_ for _ in ()).throw(RuntimeError("emit fail")),
    )
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.file_handler"):
        handler.emit(LogRecord(level=20, level_name="INFO", message="x"))
    assert "Sync file emit error" in caplog.text
    handler.close()


def test_sync_file_handler_flush_generic_exception_and_cleanup_swallows(
    monkeypatch, tmp_path: Path, caplog
) -> None:
    recorded_exceptions = []

    def _quiet_exception(message, *args, **kwargs):
        rendered = message % args if args else message
        recorded_exceptions.append(rendered)

    monkeypatch.setattr(file_module._logger, "exception", _quiet_exception)

    class BrokenRuntimeFile:
        closed = False

        def write(self, _message):
            raise RuntimeError("bad runtime write")

        def flush(self):
            return None

    handler = SyncFileHandler(filename=str(tmp_path / "flush-generic.log"))
    handler._buffer.append("x\n")
    handler._file_handle.close()
    handler._file_handle = BrokenRuntimeFile()
    with caplog.at_level("ERROR", logger="hydra_logger.handlers.file_handler"):
        handler.flush()
    assert any("File buffer flush error" in message for message in recorded_exceptions)

    monkeypatch.setattr(
        handler, "close", lambda: (_ for _ in ()).throw(RuntimeError("close fail"))
    )
    handler._auto_cleanup()
    handler.__del__()
    # Ensure teardown/atexit paths do not replay the injected broken writer.
    handler._buffer.clear()
    handler._file_handle = None


def test_async_file_handler_init_directory_warning_and_start_worker_noop(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.setattr(file_module.os, "makedirs", lambda *_a, **_k: (_ for _ in ()).throw(OSError("mkdir fail")))
    monkeypatch.setattr(AsyncFileHandler, "_start_worker", lambda self: None)
    handler = AsyncFileHandler(filename=str(tmp_path / "nested" / "async.log"))
    output = capsys.readouterr()
    assert "Could not create directory" in output.out
    handler.close()


def test_file_handler_wrapper_uses_async_methods_when_available(tmp_path: Path) -> None:
    class AsyncCapable:
        def __init__(self) -> None:
            self.emit_async_called = False
            self.aclose_called = False

        def emit(self, _record) -> None:
            return None

        async def emit_async(self, _record) -> None:
            self.emit_async_called = True

        def close(self) -> None:
            return None

        async def aclose(self) -> None:
            self.aclose_called = True

        def get_stats(self):
            return {"kind": "async-capable"}

        def setFormatter(self, _formatter) -> None:
            return None

    async def _run() -> None:
        wrapper = FileHandler(filename=str(tmp_path / "wrapper-async.log"))
        wrapper._handler = AsyncCapable()
        await wrapper.emit_async(LogRecord(level=20, level_name="INFO", message="async"))
        await wrapper.aclose()
        assert wrapper._handler.emit_async_called is True
        assert wrapper._handler.aclose_called is True

    asyncio.run(_run())


def test_async_file_handler_worker_and_write_error_clusters(monkeypatch, tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "worker-cluster.log"), use_threading=False)
        handler._shutdown_event.set()
        handler._running = True
        handler._start_worker()  # early return when already running

        # Exercise _direct_memory_to_file_write empty-return and error branch.
        await handler._direct_memory_to_file_write([])

        async def _raise_write(_messages):
            raise RuntimeError("bulk fail")

        monkeypatch.setattr(handler, "_bulk_write_to_disk_async", _raise_write)
        await handler._direct_memory_to_file_write(["x\n"])

        # Exercise _fast_disk_flush early return.
        handler._disk_buffer = []
        await handler._fast_disk_flush()
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_message_processor_queueempty_and_exception_paths(
    monkeypatch, tmp_path: Path
) -> None:
    class QueueStub:
        def __init__(self) -> None:
            self._calls = 0

        def empty(self):
            return False

        def get_nowait(self):
            self._calls += 1
            raise asyncio.QueueEmpty()

        def task_done(self):
            return None

        def qsize(self):
            return 0

    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "processor.log"), use_threading=False)
        queue = QueueStub()
        handler._message_queue = queue
        handler._current_batch_size = 1
        handler._shutdown_event.clear()
        called_sleep = {"count": 0}

        async def _fake_sleep(_value):
            called_sleep["count"] += 1
            if called_sleep["count"] > 1:
                handler._shutdown_event.set()

        monkeypatch.setattr(asyncio, "sleep", _fake_sleep)

        await handler._message_processor("T")
        assert queue._calls >= 1
        handler._shutdown_event.clear()

        async def _bad_opt(*_args, **_kwargs):
            raise RuntimeError("opt fail")

        monkeypatch.setattr(handler, "_optimization", _bad_opt)
        called_sleep["count"] = 0
        await handler._message_processor("T2")
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_bulk_write_paths_and_fallbacks(monkeypatch, tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "bulk.log"), use_threading=False)
        await handler._bulk_write_to_disk_async([])  # early return

        # Force ImportError path for aiofiles.
        original_import = builtins.__import__

        def _import_with_error(name, *args, **kwargs):
            if name == "aiofiles":
                raise ImportError("no aiofiles")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _import_with_error)
        await handler._bulk_write_to_disk_async(["a\n"])
        monkeypatch.setattr(builtins, "__import__", original_import)

        # Force generic exception inside aiofiles context path.
        class _BrokenAiofiles:
            class _Ctx:
                async def __aenter__(self):
                    raise RuntimeError("open failed")

                async def __aexit__(self, _et, _ev, _tb):
                    return None

            def open(self, *_a, **_k):
                return _BrokenAiofiles._Ctx()

        monkeypatch.setitem(sys.modules, "aiofiles", _BrokenAiofiles())
        dropped_before = handler._messages_dropped
        await handler._bulk_write_to_disk_async(["b\n"])
        assert handler._messages_dropped > dropped_before
        monkeypatch.delitem(sys.modules, "aiofiles", raising=False)

        # Cover _bulk_write_to_disk success and error branches.
        threaded = AsyncFileHandler(filename=str(tmp_path / "threaded.log"), use_threading=True)
        threaded._bulk_write_to_disk(["ok\n"])
        threaded._file_lock = None
        try:
            threaded._bulk_write_to_disk(["x\n"])
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected RuntimeError when file lock is missing")
        threaded.close()
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_flush_batch_and_emit_async_direct_write_paths(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "flush-fallback.log"), use_threading=False)
        await handler._flush_batch()  # empty buffer early return

        # Force _flush_batch ImportError branch
        handler._message_buffer = ["line-a\n", "line-b\n"]
        original_import = builtins.__import__

        def _import_with_error(name, *args, **kwargs):
            if name == "aiofiles":
                raise ImportError("missing aiofiles")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _import_with_error)
        await handler._flush_batch()
        monkeypatch.setattr(builtins, "__import__", original_import)

        # Force _flush_batch generic exception path via broken aiofiles.
        class _BrokenAiofilesModule:
            class _Ctx:
                async def __aenter__(self):
                    raise RuntimeError("ctx fail")

                async def __aexit__(self, _et, _ev, _tb):
                    return None

            @staticmethod
            def open(*_a, **_k):
                return _BrokenAiofilesModule._Ctx()

        monkeypatch.setitem(sys.modules, "aiofiles", _BrokenAiofilesModule())
        handler._message_buffer = ["line-c\n"]
        await handler._flush_batch()
        monkeypatch.delitem(sys.modules, "aiofiles", raising=False)

        # Cover emit_async direct-write binary and direct-write error branches.
        direct = AsyncFileHandler(filename=str(tmp_path / "direct-bytes.log"), use_threading=False)
        monkeypatch.setattr(direct, "_start_worker", lambda: None)
        direct._running = False
        direct._worker_tasks = []

        monkeypatch.setattr(
            direct,
            "_format_message",
            lambda _record: b"\x01\x02",
        )
        await direct.emit_async(LogRecord(level=20, level_name="INFO", message="ignored"))

        monkeypatch.setattr(
            direct,
            "_format_message",
            lambda _record: "text-path\n",
        )
        monkeypatch.setattr(
            builtins,
            "open",
            lambda *_a, **_k: (_ for _ in ()).throw(OSError("direct write fail")),
        )
        dropped_before = direct._messages_dropped
        await direct.emit_async(LogRecord(level=20, level_name="INFO", message="ignored"))
        assert direct._messages_dropped > dropped_before

        await handler.aclose()
        await direct.aclose()

    asyncio.run(_run())


def test_async_file_handler_close_async_and_aclose_error_branches(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "close-async.log"), use_threading=False)

        # close_async exception path via _fast_disk_flush failure
        handler._memory_buffer = ["m"]
        handler._disk_buffer = ["d"]

        async def _bad_fast_flush():
            raise RuntimeError("flush boom")

        monkeypatch.setattr(handler, "_fast_disk_flush", _bad_fast_flush)
        await handler.close_async()

        # aclose queue-empty branch + final flush open failure + gather fallback
        handler2 = AsyncFileHandler(filename=str(tmp_path / "aclose-err.log"), use_threading=False)

        class QueueRaise:
            def empty(self):
                return False

            def get_nowait(self):
                raise asyncio.QueueEmpty()

            def qsize(self):
                return 0

        class DoneTask:
            def done(self):
                return False

            def cancel(self):
                return None

        handler2._message_queue = QueueRaise()
        handler2._worker_tasks = [DoneTask()]

        async def _bad_wait(*_a, **_k):
            raise RuntimeError("wait boom")

        async def _bad_gather(*_a, **_k):
            raise RuntimeError("gather boom")

        monkeypatch.setattr(asyncio, "wait", _bad_wait)
        monkeypatch.setattr(asyncio, "gather", _bad_gather)

        # Force remaining write path and open failure
        class QueueRemaining:
            def __init__(self):
                self._messages = ["rem\n"]

            def empty(self):
                return len(self._messages) == 0

            def get_nowait(self):
                return self._messages.pop(0)

            def qsize(self):
                return len(self._messages)

        handler2._message_queue = QueueRemaining()
        monkeypatch.setattr(
            builtins,
            "open",
            lambda *_a, **_k: (_ for _ in ()).throw(OSError("final write fail")),
        )
        await handler2.aclose()

    asyncio.run(_run())


def test_async_file_handler_adaptive_helpers_and_threaded_paths(monkeypatch, tmp_path: Path) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "adaptive.log"), use_threading=True)

        class _Loop:
            async def run_in_executor(self, _executor, func, messages):
                return func(messages)

        monkeypatch.setattr(asyncio, "get_event_loop", lambda: _Loop())

        # _direct_memory_to_file_write / _fast_disk_flush threaded branches
        await handler._direct_memory_to_file_write(["a\n"])
        handler._disk_buffer = ["b\n"]
        await handler._fast_disk_flush()

        # _flush_batch_smart early return + success path
        handler._message_buffer = []
        handler._overflow_buffer = []
        await handler._flush_batch_smart()
        handler._message_buffer = ["x\n"]
        handler._overflow_buffer = ["y\n"]
        await handler._flush_batch_smart()
        assert handler._batch_count >= 1

        # _write_messages_to_file error path
        async def _bad_write(_messages):
            raise RuntimeError("write fail")

        monkeypatch.setattr(handler, "_write_messages_async", _bad_write)
        handler._use_threading = False
        try:
            await handler._write_messages_to_file(["z\n"])
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected RuntimeError from _write_messages_to_file")

        # _write_messages_threaded success + _write_messages_async error path
        threaded = AsyncFileHandler(filename=str(tmp_path / "threaded-success.log"), use_threading=True)
        threaded._write_messages_threaded(["ok\n"])
        monkeypatch.setattr(
            file_module.os,
            "makedirs",
            lambda *_a, **_k: (_ for _ in ()).throw(OSError("mkdir fail")),
        )
        try:
            await threaded._write_messages_async(["bad\n"])
        except OSError:
            pass
        else:
            raise AssertionError("Expected OSError from _write_messages_async")
        threaded.close()

        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_optimize_adjust_sleep_flush_batch_and_emit_paths(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "perf.log"), use_threading=False)

        # _optimize_performance + _adjust_performance_parameters paths
        handler._last_performance_check = 0.0
        handler._performance_samples = []
        await handler._optimize_performance(0.0, 1)
        await handler._adjust_performance_parameters()  # <10 sample early return

        handler._performance_samples = [
            {"duration": 0.01, "messages": 40, "timestamp": 1.0} for _ in range(20)
        ]
        await handler._adjust_performance_parameters()  # high throughput branch
        handler._performance_samples = [
            {"duration": 1.0, "messages": 1, "timestamp": 1.0} for _ in range(20)
        ]
        await handler._adjust_performance_parameters()  # low throughput branch

        # _calculate_smart_sleep medium / low branches
        handler._max_queue_size = 10
        handler._message_queue = asyncio.Queue(maxsize=100)
        for _ in range(6):
            handler._message_queue.put_nowait("x")
        assert handler._calculate_smart_sleep() == 0.01
        while not handler._message_queue.empty():
            handler._message_queue.get_nowait()
        assert handler._calculate_smart_sleep() == 0.1

        # _should_flush_batch branches
        handler._flush_interval = 1000
        handler._batch_size = 10
        handler._last_flush = file_module.TimeUtility.perf_counter()
        handler._message_buffer = ["x"] * 5
        assert handler._should_flush_batch() is True
        handler._message_buffer = ["x"] * 10
        assert handler._should_flush_batch() is True

        # _flush_batch outer exception branch
        monkeypatch.setattr(
            builtins,
            "open",
            lambda *_a, **_k: (_ for _ in ()).throw(OSError("batch fail")),
        )
        handler._message_buffer = [b"\x01"]
        dropped_before = handler._messages_dropped
        await handler._flush_batch()
        assert handler._messages_dropped > dropped_before

        # _check_and_write_csv_headers branches and emit/emit_async outer error paths
        class CsvLike:
            include_headers = False

            def format_headers(self):
                return "h1,h2"

        handler.setFormatter(CsvLike())
        assert handler._check_and_write_csv_headers() is False

        class CsvLikeWrite:
            include_headers = True

            def format_headers(self):
                return "h1,h2"

        monkeypatch.setattr(file_module.os.path, "exists", lambda _p: True)
        monkeypatch.setattr(
            file_module.os.path,
            "getsize",
            lambda _p: (_ for _ in ()).throw(OSError("size fail")),
        )
        handler.setFormatter(CsvLikeWrite())
        assert handler._check_and_write_csv_headers() is False

        monkeypatch.setattr(handler, "_format_message", lambda _r: (_ for _ in ()).throw(RuntimeError("fmt")))
        handler.emit(LogRecord(level=20, level_name="INFO", message="x"))
        await handler.emit_async(LogRecord(level=20, level_name="INFO", message="x"))
        assert handler._messages_dropped >= 2
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_cleanup_destructor_and_pytest_cleanup_branches(
    monkeypatch, tmp_path: Path
) -> None:
    recorded_exceptions = []

    def _quiet_exception(message, *args, **kwargs):
        rendered = message % args if args else message
        recorded_exceptions.append(rendered)

    monkeypatch.setattr(file_module._logger, "exception", _quiet_exception)

    class _Task:
        def __init__(self) -> None:
            self.cancelled = False

        def done(self):
            return False

        def cancel(self):
            self.cancelled = True

    class _Loop:
        def is_closed(self):
            return False

    handler = AsyncFileHandler(filename=str(tmp_path / "cleanup-branches.log"), use_threading=False)
    handler._worker_tasks = [_Task()]
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: _Loop())
    monkeypatch.setattr(file_module.time, "sleep", lambda _v: None)
    handler._auto_cleanup()
    handler.__del__()
    assert handler._worker_tasks[0].cancelled is True

    # _auto_cleanup outer exception branch
    class _BrokenEvent:
        def set(self):
            raise RuntimeError("set fail")

    handler._shutdown_event = _BrokenEvent()
    handler._auto_cleanup()

    # __del__ outer exception branch
    handler.__del__()
    # Restore a safe event for any later cleanup hooks.
    handler._shutdown_event = asyncio.Event()
    handler._worker_tasks = []

    # _pytest_cleanup cancel and exception branches
    handler2 = AsyncFileHandler(filename=str(tmp_path / "pytest-clean.log"), use_threading=False)
    task = _Task()
    handler2._worker_tasks = [task]
    handler2._pytest_cleanup()
    assert task.cancelled is True
    handler2._shutdown_event = _BrokenEvent()
    handler2._pytest_cleanup()
    # Restore safe state for registered cleanup hooks.
    handler2._shutdown_event = asyncio.Event()
    handler2._worker_tasks = []
    assert "Async file auto cleanup failed" in recorded_exceptions
    assert "Async file destructor cleanup failed" in recorded_exceptions
    assert "Async file pytest cleanup failed" in recorded_exceptions


def test_async_file_handler_remaining_worker_and_flush_branches(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "remaining-worker.log"), use_threading=False)
        handler._message_queue.put_nowait("msg\n")
        handler._current_batch_size = 1

        async def _direct(messages):
            assert messages == ["msg\n"]
            handler._shutdown_event.set()

        async def _opt(_start, _count):
            return None

        monkeypatch.setattr(handler, "_direct_memory_to_file_write", _direct)
        monkeypatch.setattr(handler, "_optimization", _opt)
        await handler._message_processor("R")
        assert handler._messages_processed >= 1

        # _fast_disk_flush exception branch
        handler._disk_buffer = ["x\n"]

        async def _boom_bulk(_messages):
            raise RuntimeError("disk flush fail")

        monkeypatch.setattr(handler, "_bulk_write_to_disk_async", _boom_bulk)
        await handler._fast_disk_flush()
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_remaining_perf_sleep_headers_emit_paths(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "remaining-perf.log"), use_threading=False)

        # _parameter_adjustment len<5 early return
        handler._performance_samples = [{"duration": 1.0, "messages": 1, "timestamp": 1.0}] * 4
        await handler._parameter_adjustment()

        # _optimize_performance sample-trim branch (>100)
        handler._performance_samples = [{"duration": 0.1, "messages": 1, "timestamp": 1.0}] * 101
        handler._last_performance_check = file_module.TimeUtility.perf_counter()
        await handler._optimize_performance(file_module.TimeUtility.perf_counter(), 1)
        assert len(handler._performance_samples) <= 100

        # _calculate_smart_sleep high-load branch
        handler._max_queue_size = 10
        handler._message_queue = asyncio.Queue(maxsize=100)
        for _ in range(9):
            handler._message_queue.put_nowait("x")
        assert handler._calculate_smart_sleep() == 0.001

        # _should_flush_batch false branch
        handler._flush_interval = 1000
        handler._last_flush = file_module.TimeUtility.perf_counter()
        handler._batch_size = 20
        handler._message_buffer = ["x"] * 1
        assert handler._should_flush_batch() is False

        # CSV headers successful write path
        class CsvOk:
            include_headers = True

            def format_headers(self):
                return "h1,h2"

        csv_handler = AsyncFileHandler(filename=str(tmp_path / "headers-ok.csv"), use_threading=False)
        csv_handler.setFormatter(CsvOk())
        assert csv_handler._check_and_write_csv_headers() is True

        # emit() _start_worker branch
        starts = {"n": 0}
        csv_handler._running = False
        monkeypatch.setattr(csv_handler, "_start_worker", lambda: starts.__setitem__("n", starts["n"] + 1))
        csv_handler.emit(LogRecord(level=20, level_name="INFO", message="start-worker"))
        assert starts["n"] == 1

        # emit_async direct text-write success branch
        direct = AsyncFileHandler(filename=str(tmp_path / "direct-text.log"), use_threading=False)
        monkeypatch.setattr(direct, "_start_worker", lambda: None)
        direct._running = False
        monkeypatch.setattr(direct, "_format_message", lambda _record: "direct-text\n")
        await direct.emit_async(LogRecord(level=20, level_name="INFO", message="x"))
        assert direct._total_bytes_written > 0

        await csv_handler.aclose()
        await direct.aclose()
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_remaining_close_and_aclose_pending_paths(
    monkeypatch, tmp_path: Path
) -> None:
    class PendingTask:
        def __init__(self) -> None:
            self.cancelled = False

        def cancel(self):
            self.cancelled = True

        def done(self):
            return False

    async def _run() -> None:
        # close_async pending gather exception + thread pool cleanup
        handler = AsyncFileHandler(filename=str(tmp_path / "close-remaining.log"), use_threading=False)
        pending = PendingTask()
        handler._worker_tasks = [pending]

        class Pool:
            def __init__(self) -> None:
                self.shutdown_called = False

            def shutdown(self, wait=True):
                self.shutdown_called = True

        pool = Pool()
        handler._thread_pool = pool

        async def _wait_with_pending(*_a, **_k):
            return set(), [pending]

        async def _gather_boom(*_a, **_k):
            raise RuntimeError("gather fail")

        monkeypatch.setattr(asyncio, "wait", _wait_with_pending)
        monkeypatch.setattr(asyncio, "gather", _gather_boom)
        await handler.close_async()
        assert pending.cancelled is True
        assert pool.shutdown_called is True
        assert handler._running is False
        assert handler._worker_tasks == []

        # aclose pending-task gather exception branch (lines 1211+)
        handler2 = AsyncFileHandler(filename=str(tmp_path / "aclose-remaining.log"), use_threading=False)
        pending2 = PendingTask()
        handler2._worker_tasks = [pending2]
        handler2._message_queue = asyncio.Queue()
        handler2._shutdown_event.clear()

        async def _wait_pending(*_a, **_k):
            return set(), [pending2]

        monkeypatch.setattr(asyncio, "wait", _wait_pending)
        monkeypatch.setattr(asyncio, "gather", _gather_boom)
        await handler2.aclose()
        assert pending2.cancelled is True

    asyncio.run(_run())


def test_async_file_handler_close_async_fallback_cancel_and_time_flush_branch(
    monkeypatch, tmp_path: Path
) -> None:
    class PendingTask:
        def __init__(self) -> None:
            self.cancelled = False

        def cancel(self):
            self.cancelled = True

        def done(self):
            return False

    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "close-fallback.log"), use_threading=False)
        task = PendingTask()
        handler._worker_tasks = [task]

        async def _wait_boom(*_a, **_k):
            raise RuntimeError("wait fail")

        async def _gather_boom(*_a, **_k):
            raise RuntimeError("gather fail")

        monkeypatch.setattr(asyncio, "wait", _wait_boom)
        monkeypatch.setattr(asyncio, "gather", _gather_boom)
        await handler.close_async()
        assert task.cancelled is True

        # _should_flush_batch time-based branch.
        handler._last_flush = 0.0
        handler._flush_interval = 0.0001
        assert handler._should_flush_batch() is True
        await handler.aclose()

    asyncio.run(_run())


def test_async_file_handler_payload_helpers_and_direct_sync_error_path(
    monkeypatch, tmp_path: Path
) -> None:
    async def _run() -> None:
        handler = AsyncFileHandler(filename=str(tmp_path / "payload.log"), use_threading=False)

        # _combine_messages_payload empty and mixed-text/binary branches.
        payload, is_binary = handler._combine_messages_payload([])
        assert payload == ""
        assert is_binary is False
        payload, is_binary = handler._combine_messages_payload([b"a", "b"])
        assert payload == b"ab"
        assert is_binary is True

        # _write_payload_async binary branch with aiofiles available.
        writes = {"count": 0}

        class _AioCtx:
            async def __aenter__(self):
                return self

            async def __aexit__(self, _et, _ev, _tb):
                return None

            async def write(self, data):
                writes["count"] += len(data)

            async def flush(self):
                return None

        class _AioFiles:
            @staticmethod
            def open(*_a, **_k):
                return _AioCtx()

        monkeypatch.setitem(sys.modules, "aiofiles", _AioFiles())
        await handler._write_payload_async(b"xy", True)
        assert writes["count"] == 2
        monkeypatch.delitem(sys.modules, "aiofiles", raising=False)

        # emit() direct sync-write error branch.
        monkeypatch.setattr(AsyncFileHandler, "_start_worker", lambda self: None)
        direct = AsyncFileHandler(filename=str(tmp_path / "direct-error.log"), use_threading=False)
        monkeypatch.setattr(
            direct,
            "_write_payload_sync",
            lambda *_a, **_k: (_ for _ in ()).throw(OSError("sync write failed")),
        )
        direct._running = False
        direct._worker_tasks = []
        dropped_before = direct._messages_dropped
        direct.emit(LogRecord(level=20, level_name="INFO", message="x"))
        assert direct._messages_dropped > dropped_before
        await direct.aclose()
        await handler.aclose()

    asyncio.run(_run())
