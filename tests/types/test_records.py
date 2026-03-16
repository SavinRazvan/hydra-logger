"""
Role: Pytest coverage for test records behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
 - pytest
Notes:
 - Validates test records behavior, edge cases, and regression safety.
"""

import pytest

from hydra_logger.types.records import (
    LogRecord,
    LogRecordBatch,
    LogRecordFactory,
    RecordCreationStrategy,
    create_log_record,
    extract_filename,
)


def test_extract_filename_handles_unix_windows_and_empty_values() -> None:
    assert extract_filename("/tmp/app/main.py") == "main.py"
    assert extract_filename(r"C:\tmp\app\main.py") == "main.py"
    assert extract_filename("main.py") == "main.py"
    assert extract_filename("") is None
    assert extract_filename(None) is None
    assert extract_filename(123) is None


def test_log_record_validates_required_fields() -> None:
    with pytest.raises(ValueError, match="Message cannot be empty"):
        LogRecord(message="")

    with pytest.raises(ValueError, match="Level name cannot be empty"):
        LogRecord(message="ok", level_name="")


def test_log_record_to_dict_and_string_include_optional_fields() -> None:
    record = LogRecord(
        level_name="WARNING",
        layer="api",
        file_name="service.py",
        function_name="run",
        line_number=42,
        message="event",
        extra={"key": "value"},
        context={"trace_id": "abc"},
    )

    payload = record.to_dict()
    assert payload["level_name"] == "WARNING"
    assert payload["file_name"] == "service.py"
    assert payload["function_name"] == "run"
    assert payload["line_number"] == 42
    assert payload["extra"]["key"] == "value"
    assert payload["context"]["trace_id"] == "abc"

    text = str(record)
    assert "[WARNING]" in text
    assert "[api]" in text
    assert "[service.py]" in text
    assert "[run]" in text
    assert "event" in text
    assert '"level_name": "WARNING"' in record.to_json()


def test_log_record_factory_context_creation_normalizes_filename() -> None:
    record = LogRecordFactory.create_with_context(
        level_name="INFO",
        message="msg",
        file_name="/var/app/worker.py",
        function_name="loop",
    )
    assert record.file_name == "worker.py"
    assert record.function_name == "loop"


def test_record_creation_strategy_supports_level_inputs_and_fallback() -> None:
    strategy = RecordCreationStrategy(strategy="unknown-strategy")
    record = strategy.create_record(level="error", message="failed", layer="test")

    assert record.level_name == "ERROR"
    assert record.level == 40
    assert record.layer == "test"

    int_level_record = strategy.create_record(level=30, message="warn")
    assert int_level_record.level_name == "WARNING"
    assert int_level_record.level == 30


def test_create_log_record_convenience_api() -> None:
    record = create_log_record("INFO", "hello", strategy="minimal", layer="default")
    assert isinstance(record, LogRecord)
    assert record.message == "hello"
    assert record.level_name == "INFO"


def test_log_record_batch_lifecycle() -> None:
    batch = LogRecordBatch(max_size=2)
    first = LogRecord(level_name="INFO", message="one")
    second = LogRecord(level_name="INFO", message="two")

    assert batch.add_record(first) is False
    assert batch.add_record(second) is True
    assert batch.is_full()
    assert len(batch) == 2
    assert list(iter(batch)) == [first, second]

    batch.clear()
    assert len(batch) == 0
    assert not batch.is_full()


def test_auto_context_creation_logs_when_inspection_fails(monkeypatch, caplog) -> None:
    import inspect

    monkeypatch.setattr(inspect, "currentframe", lambda: (_ for _ in ()).throw(Exception()))
    with caplog.at_level("ERROR", logger="hydra_logger.types.records"):
        record = LogRecordFactory.create_with_auto_context("INFO", "hello")
    assert record.message == "hello"
    assert "Auto-context extraction failed; proceeding without caller info" in caplog.text


def test_auto_context_creation_handles_missing_frame(monkeypatch) -> None:
    import inspect

    monkeypatch.setattr(inspect, "currentframe", lambda: None)
    record = LogRecordFactory.create_with_auto_context("INFO", "hello")
    assert record.file_name is None
    assert record.function_name is None
    assert record.line_number is None


def test_auto_context_skips_empty_filename_frames(monkeypatch) -> None:
    import inspect

    class _FakeCode:
        co_filename = ""
        co_name = "hidden"
        co_varnames = ()

    class _FakeFrame:
        def __init__(self):
            self.f_code = _FakeCode()
            self.f_back = None
            self.f_lineno = 1
            self.f_globals = {}
            self.f_locals = {}

    class _TopFrame:
        def __init__(self):
            self.f_back = _FakeFrame()

    monkeypatch.setattr(inspect, "currentframe", lambda: _TopFrame())
    record = LogRecordFactory.create_with_auto_context("INFO", "hello")
    assert record.file_name is None
    assert record.function_name is None


def test_auto_context_skips_invalid_frame_objects(monkeypatch) -> None:
    import inspect

    class _BadFrame:
        def __init__(self):
            self.f_back = None

    class _TopFrame:
        def __init__(self):
            self.f_back = _BadFrame()

    monkeypatch.setattr(inspect, "currentframe", lambda: _TopFrame())
    record = LogRecordFactory.create_with_auto_context("INFO", "hello")
    assert record.message == "hello"


def test_auto_context_extracts_user_frame_details(monkeypatch) -> None:
    import inspect

    class _FakeCode:
        def __init__(self, filename, name, varnames=()):
            self.co_filename = filename
            self.co_name = name
            self.co_varnames = varnames

    class _FakeFrame:
        def __init__(self, code, lineno, back=None):
            self.f_code = code
            self.f_lineno = lineno
            self.f_back = back
            self.f_globals = {"__name__": "user_module"}
            self.f_locals = {}

    user_frame = _FakeFrame(_FakeCode("/opt/app/user_service.py", "process"), 321)
    top_frame = _FakeFrame(_FakeCode("/tmp/wrapper.py", "wrapper"), 1, back=user_frame)
    monkeypatch.setattr(inspect, "currentframe", lambda: top_frame)

    record = LogRecordFactory.create_with_auto_context("INFO", "hello")
    assert record.file_name == "user_service.py"
    assert record.function_name == "process"
    assert record.line_number == 321


def test_enhanced_function_name_handles_self_cls_special_and_failure_paths() -> None:
    class _Code:
        def __init__(self, name, varnames):
            self.co_name = name
            self.co_varnames = varnames

    class _Frame:
        def __init__(self, code_name, locals_map, varnames):
            self.f_code = _Code(code_name, varnames)
            self.f_locals = locals_map

    class _Service:
        pass

    frame_self = _Frame("run", {"self": _Service()}, ("self",))
    assert LogRecordFactory._get_enhanced_function_name(frame_self).endswith(".run")

    class _ServiceClass:
        pass

    frame_cls = _Frame("build", {"cls": _ServiceClass}, ("cls",))
    assert LogRecordFactory._get_enhanced_function_name(frame_cls) == "_ServiceClass.build"

    frame_lambda = _Frame("<lambda>", {}, ())
    assert LogRecordFactory._get_enhanced_function_name(frame_lambda) == "<lambda>"

    frame_plain = _Frame("work", {}, ("arg1",))
    assert LogRecordFactory._get_enhanced_function_name(frame_plain) == "work"

    class _ExplodingLocals(dict):
        def __contains__(self, _item):
            raise RuntimeError("boom")

    frame_error = _Frame("unstable", _ExplodingLocals(), ())
    assert LogRecordFactory._get_enhanced_function_name(frame_error) == "unstable"


def test_record_creation_strategy_context_branch_includes_context_fields() -> None:
    strategy = RecordCreationStrategy(strategy=RecordCreationStrategy.CONTEXT)
    record = strategy.create_record(
        level="INFO",
        message="contextual",
        layer="api",
        file_name="/tmp/src/service.py",
        function_name="execute",
        line_number=88,
    )
    assert record.level_name == "INFO"
    assert record.layer == "api"
    assert record.file_name == "service.py"
    assert record.function_name == "execute"
    assert record.line_number == 88


def test_enhanced_function_name_covers_co_varnames_self_and_cls_paths() -> None:
    class _Code:
        def __init__(self, name, varnames):
            self.co_name = name
            self.co_varnames = varnames

    class _SelfProbeLocals(dict):
        def __init__(self, self_value):
            super().__init__({"self": self_value})
            self._seen = {"self": 0}

        def __contains__(self, key):
            if key == "self":
                self._seen["self"] += 1
                return self._seen["self"] > 1
            return super().__contains__(key)

    class _ClsProbeLocals(dict):
        def __init__(self, cls_value):
            super().__init__({"cls": cls_value})
            self._seen = {"cls": 0}

        def __contains__(self, key):
            if key == "cls":
                self._seen["cls"] += 1
                return self._seen["cls"] > 1
            return super().__contains__(key)

    class _Frame:
        def __init__(self, code_name, locals_map, varnames):
            self.f_code = _Code(code_name, varnames)
            self.f_locals = locals_map

    class _Service:
        pass

    frame_self_varnames = _Frame(
        "apply",
        _SelfProbeLocals(_Service()),
        ("self",),
    )
    result_self = LogRecordFactory._get_enhanced_function_name(frame_self_varnames)
    assert result_self.endswith(".apply")

    class _Builder:
        pass

    frame_cls_varnames = _Frame(
        "create",
        _ClsProbeLocals(_Builder),
        ("cls",),
    )
    assert LogRecordFactory._get_enhanced_function_name(frame_cls_varnames) == "_Builder.create"
