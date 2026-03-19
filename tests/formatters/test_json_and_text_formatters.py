"""
Role: Pytest coverage for plain text and JSON formatter behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates serialization payload and template rendering behavior.
"""

import json

import pytest

from hydra_logger.formatters.json_formatter import JsonLinesFormatter
from hydra_logger.formatters.text_formatter import PlainTextFormatter
from hydra_logger.types.records import LogRecord
from hydra_logger.utils.time_utility import TimestampFormat


def _record() -> LogRecord:
    return LogRecord(
        level_name="WARNING",
        message="disk nearly full",
        level=30,
        layer="storage",
        logger_name="HydraLogger",
        file_name="service.py",
        function_name="check_disk",
        line_number=22,
        extra={"host": "node-1"},
        context={"trace_id": "abc"},
    )


def test_plain_text_formatter_replaces_placeholders() -> None:
    formatter = PlainTextFormatter(
        format_string="{level_name}|{layer}|{message}|{file_name}"
    )
    rendered = formatter.format(_record())
    assert "WARNING|storage|disk nearly full|service.py" in rendered


def test_json_lines_formatter_serializes_structured_fields() -> None:
    formatter = JsonLinesFormatter()
    payload = json.loads(formatter.format(_record()))
    assert payload["level_name"] == "WARNING"
    assert payload["layer"] == "storage"
    assert payload["extra"]["host"] == "node-1"
    assert payload["context"]["trace_id"] == "abc"
    assert formatter.get_required_extension() == ".jsonl"


@pytest.mark.parametrize(
    "pattern, expected",
    [
        ("| {timestamp} | {level_name} | {layer} | {message}", "| "),
        (
            "{timestamp} {level_name} {layer} {message}",
            "WARNING storage disk nearly full",
        ),
        ("{level_name} {layer} {message}", "WARNING storage disk nearly full"),
        ("{timestamp} {level_name} {message}", "WARNING disk nearly full"),
        ("{level_name} {message}", "WARNING disk nearly full"),
        ("{message}", "disk nearly full"),
    ],
)
def test_plain_text_formatter_compiled_patterns(pattern: str, expected: str) -> None:
    formatter = PlainTextFormatter(format_string=pattern)
    assert formatter._compiled_format is not None
    rendered = formatter.format(_record())
    assert expected in rendered


def test_plain_text_formatter_non_compiled_fallback_and_extension() -> None:
    formatter = PlainTextFormatter(
        format_string="{level_name}|{layer}|{message}|{logger_name}|{function_name}|{line_number}"
    )
    assert formatter._compiled_format is None
    rendered = formatter.format(_record())
    assert "WARNING|storage|disk nearly full|HydraLogger|check_disk|22" in rendered
    assert formatter.get_required_extension() == ".log"


def test_plain_text_formatter_default_fallback_values() -> None:
    record = LogRecord(
        level_name="INFO",
        message="ok",
        level=20,
        layer="ops",
        logger_name="HydraLogger",
        file_name=None,
        function_name=None,
        line_number=None,
    )
    formatter = PlainTextFormatter(
        format_string="{file_name}|{function_name}|{line_number}"
    )
    rendered = formatter.format(record)
    assert rendered == "unknown|unknown|0"


def test_plain_text_formatter_timestamp_config_env_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod = PlainTextFormatter()
    assert prod.timestamp_config.format_type == TimestampFormat.RFC3339_MICRO

    monkeypatch.setenv("ENVIRONMENT", "development")
    dev = PlainTextFormatter()
    assert dev.timestamp_config.format_type == TimestampFormat.HUMAN_READABLE


def test_plain_text_formatter_compile_returns_none_for_unhandled_pattern() -> None:
    formatter = PlainTextFormatter(format_string="{message}")
    formatter.format_string = "{timestamp}:{message}:custom"
    assert formatter._compile_fstring_format() is None


def test_json_formatter_default_timestamp_config_uses_development_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    formatter = JsonLinesFormatter()
    assert formatter.timestamp_config.format_type == TimestampFormat.HUMAN_READABLE


def test_json_formatter_default_timestamp_config_uses_production_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    formatter = JsonLinesFormatter()
    assert formatter.timestamp_config.format_type == TimestampFormat.RFC3339_MICRO
