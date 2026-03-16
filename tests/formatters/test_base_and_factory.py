"""
Role: Pytest coverage for formatter base contracts and factory mapping.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates extension rules, validation, and format-type mapping.
"""

import pytest

from hydra_logger.formatters import (
    ColoredFormatter,
    JsonLinesFormatter,
    PlainTextFormatter,
    get_formatter,
)
from hydra_logger.formatters.base import BaseFormatter, FormatterError
from hydra_logger.types.records import LogRecord


class DummyFormatter(BaseFormatter):
    def _format_default(self, record: LogRecord) -> str:
        return f"{record.level_name}:{record.message}"


def test_base_formatter_validate_filename_and_required_extension() -> None:
    formatter = DummyFormatter(name="dummy")
    assert formatter.get_required_extension() == ".log"
    assert formatter.validate_filename("events.txt") == "events.log"
    assert formatter.validate_filename("events") == "events.log"
    assert formatter.validate_filename("events.log") == "events.log"


def test_base_formatter_rejects_none_record() -> None:
    formatter = DummyFormatter(name="dummy")
    with pytest.raises(FormatterError, match="cannot be None"):
        formatter.format(None)  # type: ignore[arg-type]


def test_get_formatter_maps_known_and_unknown_types() -> None:
    assert isinstance(get_formatter("plain-text"), PlainTextFormatter)
    assert isinstance(get_formatter("colored", use_colors=True), ColoredFormatter)
    assert isinstance(get_formatter("json-lines"), JsonLinesFormatter)
    assert isinstance(get_formatter("json"), JsonLinesFormatter)
    assert isinstance(get_formatter("unknown"), PlainTextFormatter)
