"""
Role: File I/O benchmark metric helpers.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - os
 - pathlib
 - typing
Notes:
 - Keeps counting/size/rate/result assembly logic outside the benchmark orchestrator.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from benchmark.dev_logging import get_logger


_logger = get_logger(__name__)


def count_written_lines(file_path: str | Path) -> int:
    """Best-effort line counter for line-based output files."""
    path = Path(file_path)
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except Exception:
        _logger.exception("Failed counting lines in benchmark output file: %s", path)
        return 0


def resolve_written_line_delta(*, baseline_lines: int, final_lines: int) -> int:
    """Return timed-run written lines by subtracting warm-up baseline."""
    return max(0, int(final_lines) - int(baseline_lines))


def extract_handler_bytes_written(logger: Any, layer_name: str = "default") -> int:
    """Extract max bytes written from handler stats if available."""
    max_bytes = 0
    try:
        handlers = getattr(logger, "_layer_handlers", {}).get(layer_name, [])
        for handler in handlers:
            if not hasattr(handler, "get_stats"):
                continue
            stats = handler.get_stats()
            if "total_bytes_written" in stats:
                max_bytes = max(max_bytes, int(stats["total_bytes_written"]))
    except Exception:
        _logger.exception(
            "Failed extracting handler byte counters for layer '%s'",
            layer_name,
        )
        return 0
    return max_bytes


def extract_handler_messages_emitted(logger: Any, layer_name: str = "default") -> int:
    """Extract max emitted-message counters from handlers when available."""
    max_messages = 0
    counter_keys = (
        "messages_processed",
        "total_messages_processed",
        "messages_written",
        "records_written",
        "total_records_written",
    )
    try:
        handlers = getattr(logger, "_layer_handlers", {}).get(layer_name, [])
        for handler in handlers:
            if not hasattr(handler, "get_stats"):
                continue
            stats = handler.get_stats()
            if not isinstance(stats, dict):
                continue
            for key in counter_keys:
                if key in stats:
                    max_messages = max(max_messages, int(stats[key]))
    except Exception:
        _logger.exception(
            "Failed extracting emitted-message counters for layer '%s'",
            layer_name,
        )
        return 0
    return max_messages


def resolve_bytes_written(
    *,
    file_path: str | Path,
    initial_size: int,
    handler_bytes: int,
) -> dict[str, int | bool]:
    """
    Resolve byte totals from handler stats and file-size delta.

    Prefers handler byte counters when available, falls back to file size delta.
    """
    path = Path(file_path)
    if path.exists():
        try:
            final_size = os.path.getsize(path)
            file_bytes = max(final_size - int(initial_size), 0)
            bytes_written = int(handler_bytes) if int(handler_bytes) > 0 else file_bytes
            return {
                "file_exists": True,
                "final_size": final_size,
                "file_bytes": file_bytes,
                "bytes_written": bytes_written,
            }
        except Exception:
            _logger.exception("Failed resolving byte counts for benchmark file: %s", path)
            return {
                "file_exists": False,
                "final_size": 0,
                "file_bytes": 0,
                "bytes_written": max(int(handler_bytes), 0),
            }
    return {
        "file_exists": False,
        "final_size": 0,
        "file_bytes": 0,
        "bytes_written": max(int(handler_bytes), 0),
    }


def build_file_io_result(
    *,
    logger_type: str,
    total_messages: int,
    duration: float,
    warmup_duration: float,
    flush_duration: float,
    bytes_written: int,
    written_lines: int,
    file_path: str,
    actual_emitted: int | None = None,
    actual_emitted_source: str = "handler_counter",
    strict_file_evidence: bool = True,
) -> dict[str, Any]:
    """Build normalized file I/O benchmark result payload."""
    resolved_actual = int(actual_emitted) if actual_emitted is not None else int(total_messages)
    if resolved_actual < 0:
        resolved_actual = 0
    messages_rate = (total_messages / duration) if duration > 0 else 0.0
    bytes_rate = (bytes_written / duration) if duration > 0 else 0.0
    return {
        "logger_type": logger_type,
        "messages_per_second": messages_rate,
        "bytes_per_second": bytes_rate,
        "bytes_written": bytes_written,
        "duration": duration,
        "measured_duration": duration,
        "warmup_duration": warmup_duration,
        "flush_duration": flush_duration,
        "total_messages": total_messages,
        "expected_emitted": total_messages,
        "actual_emitted": resolved_actual,
        "actual_emitted_source": actual_emitted_source,
        "written_lines": written_lines,
        "written_lines_observed": written_lines > 0,
        "strict_file_evidence": strict_file_evidence,
        "file_path": file_path,
        "status": "COMPLETED",
    }
