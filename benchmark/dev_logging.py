"""
Role: Benchmark development-only diagnostics logger helpers.
Used By:
 - benchmark modules requiring contextual debug/error traces.
Depends On:
 - logging
 - os
 - pathlib
 - threading
Notes:
 - Enables file-based benchmark diagnostics only in development mode.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Lock


_LOG_FILE_NAME = "benchmark_dev.log"
_LOGGER_LOCK = Lock()
_CONFIGURED = False


def _is_dev_mode() -> bool:
    """Return True when diagnostics logs should be enabled."""
    marker = os.getenv("HYDRA_BENCHMARK_DEV_LOGS", "")
    if marker == "1":
        return True

    candidates = (
        os.getenv("HYDRA_ENV", ""),
        os.getenv("ENVIRONMENT", ""),
        os.getenv("PYTHON_ENV", ""),
    )
    return any(value.lower() in {"dev", "development", "local", "debug"} for value in candidates)


def _configure_root_benchmark_logger() -> None:
    """Configure benchmark logger output once for dev mode."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    with _LOGGER_LOCK:
        if _CONFIGURED:
            return

        benchmark_logger = logging.getLogger("benchmark")
        benchmark_logger.addHandler(logging.NullHandler())

        if _is_dev_mode():
            try:
                logs_dir = Path(__file__).resolve().parent.parent / "logs"
                logs_dir.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(
                    logs_dir / _LOG_FILE_NAME,
                    encoding="utf-8",
                )
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                    )
                )
                benchmark_logger.addHandler(file_handler)
                benchmark_logger.setLevel(logging.DEBUG)
                benchmark_logger.propagate = False
            except Exception:
                # Keep diagnostics non-blocking: benchmark flow must continue.
                benchmark_logger.debug("Benchmark dev logger setup failed", exc_info=True)

        _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a benchmark logger configured for development diagnostics."""
    _configure_root_benchmark_logger()
    return logging.getLogger(name)
