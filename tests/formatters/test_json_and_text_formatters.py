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

from hydra_logger.formatters.json_formatter import JsonLinesFormatter
from hydra_logger.formatters.text_formatter import PlainTextFormatter
from hydra_logger.types.records import LogRecord


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
    formatter = PlainTextFormatter(format_string="{level_name}|{layer}|{message}|{file_name}")
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
