"""
Role: Unit tests for benchmark defensive error-handling paths.
Used By:
 - Pytest benchmark package coverage and CI gates.
Depends On:
 - benchmark
 - pytest
Notes:
 - Exercises exception branches added for dev logging and runtime hardening.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

import pytest

import benchmark.dev_logging as dev_logging_mod
import benchmark.io_metrics as io_metrics_mod
import benchmark.metrics as metrics_mod
import benchmark.profiles as profiles_mod
import benchmark.reporting as reporting_mod
import benchmark.runners as runners_mod
import benchmark.schema_validation as schema_validation_mod


def test_dev_logging_is_dev_mode_marker_enabled(monkeypatch) -> None:
    monkeypatch.setenv("HYDRA_BENCHMARK_DEV_LOGS", "1")
    assert dev_logging_mod._is_dev_mode() is True


def test_dev_logging_configure_is_reentrant_inside_lock(monkeypatch) -> None:
    class _ToggleLock:
        def __enter__(self):
            dev_logging_mod._CONFIGURED = True
            return self

        def __exit__(self, _exc_type, _exc, _tb):
            return False

    monkeypatch.setattr(dev_logging_mod, "_CONFIGURED", False)
    monkeypatch.setattr(dev_logging_mod, "_LOGGER_LOCK", _ToggleLock())
    dev_logging_mod._configure_root_benchmark_logger()
    assert dev_logging_mod._CONFIGURED is True


def test_dev_logging_configure_dev_mode_file_handler_failure(monkeypatch) -> None:
    benchmark_logger = logging.getLogger("benchmark")
    previous_handlers = list(benchmark_logger.handlers)
    previous_level = benchmark_logger.level
    previous_propagate = benchmark_logger.propagate
    try:
        benchmark_logger.handlers = []
        monkeypatch.setattr(dev_logging_mod, "_CONFIGURED", False)
        monkeypatch.setattr(dev_logging_mod, "_is_dev_mode", lambda: True)

        class _FailingFileHandler:
            def __init__(self, *_args, **_kwargs) -> None:
                raise OSError("file handler boom")

        monkeypatch.setattr(logging, "FileHandler", _FailingFileHandler)
        dev_logging_mod._configure_root_benchmark_logger()
        assert dev_logging_mod._CONFIGURED is True
    finally:
        benchmark_logger.handlers = previous_handlers
        benchmark_logger.setLevel(previous_level)
        benchmark_logger.propagate = previous_propagate


def test_dev_logging_configure_dev_mode_file_handler_success(monkeypatch) -> None:
    benchmark_logger = logging.getLogger("benchmark")
    previous_handlers = list(benchmark_logger.handlers)
    previous_level = benchmark_logger.level
    previous_propagate = benchmark_logger.propagate
    try:
        benchmark_logger.handlers = []
        monkeypatch.setattr(dev_logging_mod, "_CONFIGURED", False)
        monkeypatch.setattr(dev_logging_mod, "_is_dev_mode", lambda: True)

        class _DummyFileHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                return None

        monkeypatch.setattr(
            logging, "FileHandler", lambda *_args, **_kwargs: _DummyFileHandler()
        )
        dev_logging_mod._configure_root_benchmark_logger()

        assert dev_logging_mod._CONFIGURED is True
        assert benchmark_logger.level == logging.DEBUG
        assert benchmark_logger.propagate is False
    finally:
        benchmark_logger.handlers = previous_handlers
        benchmark_logger.setLevel(previous_level)
        benchmark_logger.propagate = previous_propagate


def test_messages_per_second_rejects_negative_totals() -> None:
    with pytest.raises(ValueError, match="total_messages must be >= 0"):
        metrics_mod.messages_per_second(-1, 1.0)


def test_measure_sync_batch_throughput_propagates_logger_errors() -> None:
    class _BrokenLogger:
        def log_batch(self, _messages: list[tuple[str, str, dict[str, Any]]]) -> None:
            raise RuntimeError("sync boom")

    with pytest.raises(RuntimeError, match="sync boom"):
        metrics_mod.measure_sync_batch_throughput(
            logger=_BrokenLogger(),
            messages=[("INFO", "m", {})],
            flush_sync=lambda _logger: None,
            min_duration_seconds=0.0,
            min_iterations=1,
        )


def test_measure_async_batch_throughput_propagates_logger_errors() -> None:
    class _BrokenAsyncLogger:
        async def log_batch(
            self, _messages: list[tuple[str, str, dict[str, Any]]]
        ) -> None:
            raise RuntimeError("async boom")

    async def _run() -> None:
        await metrics_mod.measure_async_batch_throughput(
            logger=_BrokenAsyncLogger(),
            messages=[("INFO", "m", {})],
            flush_async=lambda _logger: asyncio.sleep(0),
            min_duration_seconds=0.0,
            min_iterations=1,
        )

    with pytest.raises(RuntimeError, match="async boom"):
        asyncio.run(_run())


def test_io_metrics_resolve_bytes_written_fallback_on_getsize_error(
    monkeypatch, tmp_path
) -> None:
    file_path = tmp_path / "out.log"
    file_path.write_text("hello\n", encoding="utf-8")
    monkeypatch.setattr(
        io_metrics_mod.os.path,
        "getsize",
        lambda _path: (_ for _ in ()).throw(OSError("size boom")),
    )

    payload = io_metrics_mod.resolve_bytes_written(
        file_path=file_path,
        initial_size=0,
        handler_bytes=12,
    )
    assert payload["file_exists"] is False
    assert payload["bytes_written"] == 12


def test_load_profile_propagates_oserror_as_contextual_error(
    monkeypatch, tmp_path
) -> None:
    profile = tmp_path / "broken.json"
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(profiles_mod, "PROFILE_DIR", tmp_path)

    original_read_text = Path.read_text

    def _raise_for_target(path: Path, *args, **kwargs):
        if path == profile:
            raise OSError("cannot read")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _raise_for_target)

    with pytest.raises(OSError, match="Could not read benchmark profile file"):
        profiles_mod.load_profile("broken")


def test_reporting_write_results_artifacts_raises_oserror(
    monkeypatch, tmp_path
) -> None:
    payload = {
        "metadata": {"timestamp": "2026-03-16_17-00-00"},
        "results": {},
    }

    def _raise_write(_self, *_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", _raise_write)
    with pytest.raises(OSError, match="Failed to persist benchmark artifacts"):
        reporting_mod.write_results_artifacts(
            output_payload=payload, results_dir=tmp_path
        )


def test_reporting_write_report_files_raises_oserror_on_copy(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(
        reporting_mod.shutil,
        "copy2",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("copy boom")),
    )
    with pytest.raises(OSError, match="Failed to persist benchmark report files"):
        reporting_mod._write_report_files(
            results_dir=tmp_path,
            timestamp="2026-03-16_17-00-00",
            prefix="summary",
            body="# report\n",
        )


def test_parallel_sync_worker_logs_and_propagates_emit_errors(
    monkeypatch, tmp_path
) -> None:
    class _BrokenLogger:
        def info(self, _msg: str) -> None:
            raise RuntimeError("emit boom")

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        runners_mod, "getLogger", lambda *_args, **_kwargs: _BrokenLogger()
    )
    with pytest.raises(RuntimeError, match="emit boom"):
        runners_mod.parallel_sync_worker(str(tmp_path), 1, 0, 1)


def test_run_async_concurrent_suite_propagates_task_errors() -> None:
    class _BrokenAsyncLogger:
        async def log_batch(self, _messages) -> None:
            raise RuntimeError("task boom")

    async def _run() -> None:
        await runners_mod.run_async_concurrent_suite(
            matrix=[1],
            messages_per_task=1,
            create_logger=lambda _count: _BrokenAsyncLogger(),
            flush_async=lambda _logger: asyncio.sleep(0),
            close_async=lambda _logger: asyncio.sleep(0),
            messages_per_second=lambda total, duration: (
                total / duration if duration > 0 else 0.0
            ),
        )

    with pytest.raises(RuntimeError, match="task boom"):
        asyncio.run(_run())


def test_run_async_concurrent_suite_propagates_close_errors() -> None:
    class _OkAsyncLogger:
        async def log_batch(self, _messages) -> None:
            return None

    async def _close_async(_logger) -> None:
        raise RuntimeError("close boom")

    async def _run() -> None:
        await runners_mod.run_async_concurrent_suite(
            matrix=[1],
            messages_per_task=1,
            create_logger=lambda _count: _OkAsyncLogger(),
            flush_async=lambda _logger: asyncio.sleep(0),
            close_async=_close_async,
            messages_per_second=lambda total, duration: (
                total / duration if duration > 0 else 0.0
            ),
        )

    with pytest.raises(RuntimeError, match="close boom"):
        asyncio.run(_run())


def test_run_parallel_workers_suite_propagates_executor_failures(
    monkeypatch, tmp_path
) -> None:
    class _BrokenExecutor:
        def __init__(self, max_workers: int) -> None:
            self.max_workers = max_workers

        def __enter__(self):
            raise RuntimeError("executor boom")

        def __exit__(self, _exc_type, _exc, _tb) -> bool:
            return False

    monkeypatch.setattr(runners_mod, "ProcessPoolExecutor", _BrokenExecutor)
    with pytest.raises(RuntimeError, match="executor boom"):
        runners_mod.run_parallel_workers_suite(
            matrix=[1],
            messages_per_worker=1,
            bench_logs_dir=tmp_path,
            messages_per_second=lambda total, duration: (
                total / duration if duration > 0 else 0.0
            ),
        )


def test_load_result_schema_propagates_oserror_as_contextual_error(monkeypatch) -> None:
    class _BrokenSchemaPath:
        def read_text(self, *, encoding: str) -> str:
            raise OSError("schema unreadable")

        def __str__(self) -> str:
            return "broken_schema.json"

    monkeypatch.setattr(schema_validation_mod, "SCHEMA_PATH", _BrokenSchemaPath())
    with pytest.raises(OSError, match="Could not read benchmark schema file"):
        schema_validation_mod.load_result_schema()
