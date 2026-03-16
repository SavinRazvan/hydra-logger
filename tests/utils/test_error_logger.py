"""
Role: Pytest coverage for safe error logger behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates resilient write behavior and session limits.
"""

import json
from pathlib import Path

from hydra_logger.utils.error_logger import SafeErrorLogger


def _reset_error_logger_state() -> None:
    SafeErrorLogger.close()
    SafeErrorLogger._error_count = 0
    SafeErrorLogger._initialized = False
    SafeErrorLogger._error_file = None


def test_safe_error_logger_writes_json_line_to_logs_file(monkeypatch, tmp_path) -> None:
    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)

    SafeErrorLogger.log_message(
        "something failed",
        level="ERROR",
        component="test_component",
        context={"trace_id": "t-1"},
    )
    SafeErrorLogger.close()

    error_file = Path(tmp_path) / "logs" / "error.jsonl"
    assert error_file.exists()
    payload = json.loads(error_file.read_text(encoding="utf-8").splitlines()[0])
    assert payload["component"] == "test_component"
    assert payload["level"] == "ERROR"
    assert payload["context"]["trace_id"] == "t-1"


def test_safe_error_logger_stops_logging_after_session_limit(monkeypatch, tmp_path) -> None:
    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)
    SafeErrorLogger._max_errors_per_session = 1

    SafeErrorLogger.log_error(ValueError("first"), component="first")
    SafeErrorLogger.log_error(ValueError("second"), component="second")
    SafeErrorLogger.close()

    error_file = Path(tmp_path) / "logs" / "error.jsonl"
    lines = error_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert "first" in lines[0]
    SafeErrorLogger._max_errors_per_session = 10000


def test_safe_error_logger_memory_error_record_path(monkeypatch, tmp_path) -> None:
    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)

    SafeErrorLogger.log_error(
        MemoryError("oom"),
        component="mem_guard",
        context={"stage": "serialize"},
    )
    SafeErrorLogger.close()

    error_file = Path(tmp_path) / "logs" / "error.jsonl"
    payload = json.loads(error_file.read_text(encoding="utf-8").splitlines()[0])
    assert payload["error_type"] == "MemoryError"
    assert payload["component"] == "mem_guard"
    assert "minimal traceback" in payload["traceback"]
