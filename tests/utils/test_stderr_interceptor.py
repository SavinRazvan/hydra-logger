"""
Role: Pytest coverage for stderr interceptor behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates start/stop lifecycle and keyword-triggered forwarding.
"""

import sys
from types import SimpleNamespace

from hydra_logger.utils import stderr_interceptor as interceptor_module
from hydra_logger.utils.error_logger import SafeErrorLogger
from hydra_logger.utils.stderr_interceptor import (
    StderrInterceptor,
    start_stderr_interception,
    stop_stderr_interception,
)


def test_stderr_interceptor_start_stop_is_idempotent() -> None:
    StderrInterceptor.stop_intercepting()
    original = sys.stderr
    StderrInterceptor.start_intercepting()
    wrapped = sys.stderr
    StderrInterceptor.start_intercepting()
    assert sys.stderr is wrapped
    assert StderrInterceptor.is_intercepting() is True
    StderrInterceptor.stop_intercepting()
    assert sys.stderr is original
    assert StderrInterceptor.is_intercepting() is False


def test_stderr_interceptor_logs_keyword_errors(monkeypatch) -> None:
    calls = []

    def fake_log_error_message(message, level="ERROR", component=None, context=None):
        calls.append((message, level, component, context))

    monkeypatch.setattr(interceptor_module, "log_error_message", fake_log_error_message)

    StderrInterceptor.stop_intercepting()
    StderrInterceptor.start_intercepting()
    try:
        sys.stderr.write("malloc failed while processing\n")
        sys.stderr.flush()
    finally:
        StderrInterceptor.stop_intercepting()

    assert calls
    assert calls[0][1] == "ERROR"
    assert calls[0][2] == "StderrInterceptor"


def test_stderr_interceptor_helper_functions_toggle_state() -> None:
    stop_stderr_interception()
    start_stderr_interception()
    assert StderrInterceptor.is_intercepting() is True
    stop_stderr_interception()
    assert StderrInterceptor.is_intercepting() is False


def test_stderr_interceptor_flush_failure_and_attribute_forwarding(monkeypatch) -> None:
    calls = []
    original_stderr = sys.stderr
    original_initialized = SafeErrorLogger._initialized
    original_error_file = SafeErrorLogger._error_file

    class FakeErrorFile:
        def flush(self) -> None:
            raise OSError("flush failed")

        def fileno(self) -> int:
            return 1

    def fake_log_error_message(message, level="ERROR", component=None, context=None):
        calls.append((message, level, component, context))

    monkeypatch.setattr(interceptor_module, "log_error_message", fake_log_error_message)
    SafeErrorLogger._initialized = True
    SafeErrorLogger._error_file = FakeErrorFile()
    StderrInterceptor.stop_intercepting()
    StderrInterceptor.start_intercepting()
    try:
        wrapped = sys.stderr
        assert wrapped.encoding == original_stderr.encoding
        wrapped.write("allocation failed\n")
    finally:
        StderrInterceptor.stop_intercepting()
        SafeErrorLogger._initialized = original_initialized
        SafeErrorLogger._error_file = original_error_file

    assert calls


def test_stderr_interceptor_warns_when_logging_fails(monkeypatch) -> None:
    warnings = []

    class FakeOriginalStderr:
        encoding = "utf-8"

        def write(self, text: str) -> None:
            warnings.append(text)

        def flush(self) -> None:
            return None

    monkeypatch.setattr(sys, "stderr", FakeOriginalStderr())
    monkeypatch.setattr(
        interceptor_module,
        "log_error_message",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("logging failed")),
    )

    original_initialized = SafeErrorLogger._initialized
    original_error_file = SafeErrorLogger._error_file
    SafeErrorLogger._initialized = True
    SafeErrorLogger._error_file = SimpleNamespace(flush=lambda: None, fileno=lambda: 1)

    StderrInterceptor.stop_intercepting()
    StderrInterceptor.start_intercepting()
    try:
        sys.stderr.write("malloc failed here\n")
    finally:
        StderrInterceptor.stop_intercepting()
        SafeErrorLogger._initialized = original_initialized
        SafeErrorLogger._error_file = original_error_file

    assert any("Failed to log stderr error to error.jsonl" in item for item in warnings)


def test_stderr_interceptor_swallows_warning_write_failures(monkeypatch) -> None:
    class BrokenOriginalStderr:
        encoding = "utf-8"
        write_calls = 0

        def write(self, _text: str) -> None:
            self.write_calls += 1
            if self.write_calls >= 2:
                raise OSError("stderr broken during warning path")
            return None

        def flush(self) -> None:
            raise OSError("flush broken")

    monkeypatch.setattr(sys, "stderr", BrokenOriginalStderr())
    monkeypatch.setattr(
        interceptor_module,
        "log_error_message",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("logging failed")),
    )

    original_initialized = SafeErrorLogger._initialized
    original_error_file = SafeErrorLogger._error_file
    SafeErrorLogger._initialized = True
    SafeErrorLogger._error_file = SimpleNamespace(flush=lambda: None, fileno=lambda: 1)

    StderrInterceptor.stop_intercepting()
    StderrInterceptor.start_intercepting()
    try:
        # No exception should escape even though warning write/flush fail.
        sys.stderr.write("memory allocation failed\n")
    finally:
        StderrInterceptor.stop_intercepting()
        SafeErrorLogger._initialized = original_initialized
        SafeErrorLogger._error_file = original_error_file


def test_stderr_interceptor_initializes_error_logger_and_fsyncs(monkeypatch) -> None:
    calls = {"init": 0, "fsync": 0}

    class FakeErrorFile:
        def flush(self) -> None:
            return None

        def fileno(self) -> int:
            return 1

    def _fake_initialize() -> None:
        calls["init"] += 1
        SafeErrorLogger._initialized = True
        SafeErrorLogger._error_file = FakeErrorFile()

    monkeypatch.setattr(SafeErrorLogger, "_initialize", _fake_initialize)
    monkeypatch.setattr(interceptor_module, "log_error_message", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "os.fsync", lambda _fd: calls.__setitem__("fsync", calls["fsync"] + 1)
    )

    original_initialized = SafeErrorLogger._initialized
    original_error_file = SafeErrorLogger._error_file
    SafeErrorLogger._initialized = False
    SafeErrorLogger._error_file = None

    StderrInterceptor.stop_intercepting()
    StderrInterceptor.start_intercepting()
    try:
        sys.stderr.write("malloc failed once\n")
    finally:
        StderrInterceptor.stop_intercepting()
        SafeErrorLogger._initialized = original_initialized
        SafeErrorLogger._error_file = original_error_file

    assert calls["init"] >= 1
    assert calls["fsync"] >= 1
