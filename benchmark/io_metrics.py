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


def count_written_lines(file_path: str | Path) -> int:
    """Best-effort line counter for line-based output files."""
    path = Path(file_path)
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    except Exception:
        return 0


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
        return 0
    return max_bytes


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
        final_size = os.path.getsize(path)
        file_bytes = max(final_size - int(initial_size), 0)
        bytes_written = int(handler_bytes) if int(handler_bytes) > 0 else file_bytes
        return {
            "file_exists": True,
            "final_size": final_size,
            "file_bytes": file_bytes,
            "bytes_written": bytes_written,
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
) -> dict[str, Any]:
    """Build normalized file I/O benchmark result payload."""
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
        "actual_emitted": total_messages,
        "written_lines": written_lines,
        "written_lines_observed": written_lines > 0,
        "file_path": file_path,
        "status": "COMPLETED",
    }
