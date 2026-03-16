"""
Role: Pytest coverage for test context behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates test context behavior, edge cases, and regression safety.
"""

from hydra_logger.types.context import (
    CallerInfo,
    ContextDetector,
    ContextManager,
    ContextType,
    LogContext,
    SystemInfo,
    clear_current_context,
    create_context,
    get_current_context,
)


class _RaisingContextVar:
    def set(self, _value):
        raise RuntimeError("no context available")

    def get(self):
        raise LookupError("no context value")


def test_system_info_sets_pid_when_missing() -> None:
    info = SystemInfo(thread_id=1, process_id=2, pid=None)
    assert info.pid is not None


def test_log_context_metadata_and_usage_tracking() -> None:
    ctx = LogContext(context_type=ContextType.REQUEST)
    initial_access_count = ctx.access_count

    ctx.update_metadata("trace_id", "t-1")
    assert ctx.get_metadata("trace_id") == "t-1"
    assert ctx.has_metadata("trace_id")

    ctx.add_metadata({"user_id": "u-1", "region": "eu"})
    assert ctx.get_metadata("user_id") == "u-1"
    assert ctx.remove_metadata("region") == "eu"

    ctx.increment_log_count()
    stats = ctx.get_stats()
    assert stats["context_type"] == "request"
    assert stats["metadata_count"] >= 1
    assert stats["access_count"] > initial_access_count
    assert stats["log_count"] == 1
    assert ctx.is_active(max_idle_seconds=3600)
    assert not ctx.is_active(max_idle_seconds=-1)

    ctx.clear_metadata()
    assert ctx.metadata == {}


def test_context_manager_set_get_clear_and_get_or_create() -> None:
    clear_current_context()
    assert get_current_context() is None

    created = ContextManager.create_context(ContextType.SESSION, {"session": "s1"})
    ContextManager.set_current_context(created)
    assert ContextManager.get_current_context() is created

    reused = ContextManager.get_or_create_context(ContextType.REQUEST)
    assert reused is created

    ContextManager.clear_current_context()
    assert ContextManager.get_current_context() is None


def test_context_detector_returns_caller_info_and_cache_controls() -> None:
    ContextDetector.disable_cache()
    uncached = ContextDetector.get_caller_info(depth=1)
    assert isinstance(uncached, CallerInfo)
    assert isinstance(uncached.filename, str)
    assert isinstance(uncached.function_name, str)

    ContextDetector.enable_cache()
    ContextDetector.set_cache_size(2)
    cached = ContextDetector.get_caller_info(depth=1)
    assert isinstance(cached, CallerInfo)

    ContextDetector._clear_cache()
    assert ContextDetector._cache == {}


def test_create_context_convenience_function() -> None:
    ctx = create_context(ContextType.TRANSACTION, {"tx": "123"})
    assert isinstance(ctx, LogContext)
    assert ctx.context_type == ContextType.TRANSACTION
    assert ctx.get_metadata("tx") == "123"


def test_context_manager_falls_back_to_thread_local_when_context_var_fails() -> None:
    original_context_var = ContextManager._context_var
    try:
        ContextManager._context_var = _RaisingContextVar()
        created = ContextManager.create_context(ContextType.CUSTOM, {"key": "value"})
        ContextManager.set_current_context(created)
        assert ContextManager.get_current_context() is created

        ContextManager.clear_current_context()
        assert ContextManager.get_current_context() is None
    finally:
        ContextManager._context_var = original_context_var


def test_context_detector_returns_error_caller_info_on_inspect_failure(monkeypatch) -> None:
    import inspect

    monkeypatch.setattr(inspect, "currentframe", lambda: (_ for _ in ()).throw(Exception()))
    caller = ContextDetector.get_caller_info(depth=1)
    assert caller.filename == "<error>"
    assert caller.function_name == "<error>"
    assert caller.line_number == 0


def test_context_detector_logs_on_inspect_failure(monkeypatch, caplog) -> None:
    import inspect

    ContextDetector.disable_cache()
    monkeypatch.setattr(inspect, "currentframe", lambda: (_ for _ in ()).throw(Exception()))
    with caplog.at_level("ERROR", logger="hydra_logger.types.context"):
        ContextDetector.get_caller_info(depth=1)
    assert "Caller info detection failed at depth=1" in caplog.text
    ContextDetector.enable_cache()
