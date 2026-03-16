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

from hydra_logger.utils import stderr_interceptor as interceptor_module
from hydra_logger.utils.stderr_interceptor import StderrInterceptor


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
