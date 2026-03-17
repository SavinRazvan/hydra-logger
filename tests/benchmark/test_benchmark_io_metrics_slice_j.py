"""
Role: Unit tests for benchmark file I/O helper metrics.
Used By:
 - Pytest benchmark slice J validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Verifies deterministic count/byte/result assembly behavior outside orchestrator.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from benchmark.io_metrics import (
    build_file_io_result,
    count_written_lines,
    extract_handler_bytes_written,
    extract_handler_messages_emitted,
    resolve_written_line_delta,
    resolve_bytes_written,
)


def test_count_written_lines_handles_missing_and_existing_file(tmp_path) -> None:
    missing = tmp_path / "missing.log"
    assert count_written_lines(missing) == 0

    written = tmp_path / "written.log"
    written.write_text("a\nb\nc\n", encoding="utf-8")
    assert count_written_lines(written) == 3


def test_count_written_lines_handles_open_error(tmp_path) -> None:
    directory_path = tmp_path / "as-dir"
    directory_path.mkdir()
    assert count_written_lines(directory_path) == 0


def test_extract_handler_bytes_written_uses_max_and_swallows_errors() -> None:
    class _GoodHandler:
        def __init__(self, value: int) -> None:
            self._value = value

        def get_stats(self) -> dict[str, int]:
            return {"total_bytes_written": self._value}

    class _BadHandler:
        def get_stats(self) -> dict[str, int]:
            raise RuntimeError("bad stats")

    logger = SimpleNamespace(
        _layer_handlers={"default": [_GoodHandler(10), _BadHandler(), _GoodHandler(40)]}
    )
    assert extract_handler_bytes_written(logger) == 0

    safe_logger = SimpleNamespace(_layer_handlers={"default": [_GoodHandler(10), _GoodHandler(40)]})
    assert extract_handler_bytes_written(safe_logger) == 40


def test_resolve_bytes_written_prefers_handler_bytes_when_present(tmp_path) -> None:
    path = tmp_path / "file.log"
    path.write_text("abcdef", encoding="utf-8")
    summary = resolve_bytes_written(
        file_path=path,
        initial_size=2,
        handler_bytes=99,
    )
    assert summary["file_exists"] is True
    assert summary["final_size"] == 6
    assert summary["file_bytes"] == 4
    assert summary["bytes_written"] == 99


def test_resolve_bytes_written_falls_back_to_file_or_missing_path(tmp_path) -> None:
    path = tmp_path / "file.log"
    path.write_text("abcde", encoding="utf-8")
    summary = resolve_bytes_written(
        file_path=path,
        initial_size=1,
        handler_bytes=0,
    )
    assert summary["bytes_written"] == 4

    missing = resolve_bytes_written(
        file_path=tmp_path / "missing.log",
        initial_size=0,
        handler_bytes=7,
    )
    assert missing["file_exists"] is False
    assert missing["bytes_written"] == 7


def test_extract_handler_messages_emitted_uses_max_and_swallows_errors() -> None:
    class _GoodHandler:
        def __init__(self, value: int) -> None:
            self._value = value

        def get_stats(self) -> dict[str, int]:
            return {"messages_processed": self._value}

    class _BadHandler:
        def get_stats(self) -> dict[str, int]:
            raise RuntimeError("bad stats")

    logger = SimpleNamespace(
        _layer_handlers={"default": [_GoodHandler(10), _BadHandler(), _GoodHandler(40)]}
    )
    assert extract_handler_messages_emitted(logger) == 0

    safe_logger = SimpleNamespace(_layer_handlers={"default": [_GoodHandler(10), _GoodHandler(40)]})
    assert extract_handler_messages_emitted(safe_logger) == 40


def test_resolve_written_line_delta_clamps_negative_values() -> None:
    assert resolve_written_line_delta(baseline_lines=1000, final_lines=1500) == 500
    assert resolve_written_line_delta(baseline_lines=1500, final_lines=1000) == 0


def test_build_file_io_result_builds_expected_contract() -> None:
    result = build_file_io_result(
        logger_type="File Handler Only",
        total_messages=200,
        duration=2.0,
        warmup_duration=0.1,
        flush_duration=0.05,
        bytes_written=1000,
        written_lines=0,
        file_path=str(Path("/tmp/file.log")),
        actual_emitted=190,
        actual_emitted_source="handler_counter",
        strict_file_evidence=True,
    )
    assert result["logger_type"] == "File Handler Only"
    assert result["messages_per_second"] == 100.0
    assert result["bytes_per_second"] == 500.0
    assert result["expected_emitted"] == 200
    assert result["actual_emitted"] == 190
    assert result["actual_emitted_source"] == "handler_counter"
    assert result["strict_file_evidence"] is True
    assert result["written_lines_observed"] is False
    assert result["status"] == "COMPLETED"


def test_build_file_io_result_handles_zero_duration() -> None:
    result = build_file_io_result(
        logger_type="Async File Handler Only",
        total_messages=10,
        duration=0.0,
        warmup_duration=0.0,
        flush_duration=0.0,
        bytes_written=100,
        written_lines=5,
        file_path="/tmp/async.log",
    )
    assert result["messages_per_second"] == 0.0
    assert result["bytes_per_second"] == 0.0
    assert result["written_lines_observed"] is True
