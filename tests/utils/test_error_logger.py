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
import io
import builtins
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


def test_initialize_falls_back_to_stderr_when_open_fails(monkeypatch, tmp_path) -> None:
    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)

    stderr_capture = io.StringIO()
    monkeypatch.setattr(
        builtins,
        "open",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("denied")),
    )
    monkeypatch.setattr("hydra_logger.utils.error_logger.sys.stderr", stderr_capture)

    SafeErrorLogger._initialize()
    SafeErrorLogger._initialize()
    assert SafeErrorLogger._initialized is True
    assert SafeErrorLogger._error_file is stderr_capture
    assert "Failed to open error.jsonl" in stderr_capture.getvalue()


def test_log_error_handles_memory_error_and_generic_write_failures(monkeypatch, tmp_path) -> None:
    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)

    class _MemoryFailWriter:
        def write(self, _payload):
            raise MemoryError("writer oom")

        def flush(self):
            pass

    stderr_capture = io.StringIO()
    SafeErrorLogger._error_file = _MemoryFailWriter()
    SafeErrorLogger._initialized = True
    monkeypatch.setattr("hydra_logger.utils.error_logger.sys.stderr", stderr_capture)
    SafeErrorLogger.log_error(ValueError("boom"), component="component_a")
    assert "[MEMORY_ERROR]" in stderr_capture.getvalue()

    class _GenericFailWriter:
        def write(self, _payload):
            raise RuntimeError("writer failed")

        def flush(self):
            pass

    stderr_capture = io.StringIO()
    SafeErrorLogger._error_file = _GenericFailWriter()
    monkeypatch.setattr("hydra_logger.utils.error_logger.sys.stderr", stderr_capture)
    SafeErrorLogger.log_error(ValueError("boom2"), component="component_b")
    assert "[ERROR]" in stderr_capture.getvalue()


def test_create_error_record_handles_trace_and_system_failures(monkeypatch) -> None:
    _reset_error_logger_state()

    monkeypatch.setattr(
        "hydra_logger.utils.error_logger.traceback.format_exception",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("trace fail")),
    )
    monkeypatch.setattr(
        "hydra_logger.utils.error_logger.os.getpid",
        lambda: (_ for _ in ()).throw(OSError("pid fail")),
    )

    payload = SafeErrorLogger._create_error_record(
        ValueError("bad"),
        context={"k": "v"},
        trace=None,
        component="unit",
    )
    assert payload["traceback"] == "Failed to generate traceback"
    assert payload["context"] == {"k": "v"}
    assert "system" not in payload


def test_log_message_handles_memory_and_generic_failures(monkeypatch, tmp_path) -> None:
    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)

    class _MemoryFailWriter:
        def write(self, _payload):
            raise MemoryError("msg oom")

        def flush(self):
            pass

    stderr_capture = io.StringIO()
    SafeErrorLogger._error_file = _MemoryFailWriter()
    SafeErrorLogger._initialized = True
    monkeypatch.setattr("hydra_logger.utils.error_logger.sys.stderr", stderr_capture)
    SafeErrorLogger.log_message("x" * 600, level="CRITICAL")
    assert "[CRITICAL]" in stderr_capture.getvalue()

    class _GenericFailWriter:
        def write(self, _payload):
            raise RuntimeError("msg fail")

        def flush(self):
            pass

    stderr_capture = io.StringIO()
    SafeErrorLogger._error_file = _GenericFailWriter()
    monkeypatch.setattr("hydra_logger.utils.error_logger.sys.stderr", stderr_capture)
    SafeErrorLogger.log_message("still bad", level="ERROR")
    assert "[ERROR]" in stderr_capture.getvalue()


def test_close_swallow_flush_errors_and_convenience_functions(monkeypatch, tmp_path) -> None:
    from hydra_logger.utils.error_logger import log_error_message, log_error_safe

    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)

    class _FlushFailWriter:
        def write(self, _payload):
            return 0

        def flush(self):
            raise RuntimeError("flush fail")

        def close(self):
            raise RuntimeError("close fail")

    SafeErrorLogger._error_file = _FlushFailWriter()
    SafeErrorLogger._initialized = True
    SafeErrorLogger.close()
    assert SafeErrorLogger._initialized is False

    _reset_error_logger_state()
    log_error_safe(ValueError("safe wrapper"), context={"op": "test"}, component="wrap")
    log_error_message("message wrapper", level="ERROR", component="wrap_msg")
    SafeErrorLogger.close()


def test_logger_fallback_paths_ignore_stderr_failures(monkeypatch, tmp_path) -> None:
    _reset_error_logger_state()
    monkeypatch.chdir(tmp_path)

    class _AlwaysFailWriter:
        def write(self, _payload):
            raise MemoryError("write fail")

        def flush(self):
            raise RuntimeError("flush fail")

    class _BrokenStderr:
        def write(self, _payload):
            raise RuntimeError("stderr write fail")

        def flush(self):
            raise RuntimeError("stderr flush fail")

    SafeErrorLogger._error_file = _AlwaysFailWriter()
    SafeErrorLogger._initialized = True
    monkeypatch.setattr("hydra_logger.utils.error_logger.sys.stderr", _BrokenStderr())
    SafeErrorLogger.log_error(ValueError("boom"), component="component_x")
    SafeErrorLogger.log_message("boom message", level="ERROR")
