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
