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
    CsvFormatter,
    GelfFormatter,
    JsonLinesFormatter,
    LogstashFormatter,
    PlainTextFormatter,
    SyslogFormatter,
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
    assert isinstance(get_formatter("csv"), CsvFormatter)
    assert isinstance(get_formatter("syslog"), SyslogFormatter)
    assert isinstance(get_formatter("gelf"), GelfFormatter)
    assert isinstance(get_formatter("logstash"), LogstashFormatter)
    assert isinstance(get_formatter("unknown"), PlainTextFormatter)


def test_base_formatter_rejects_empty_name() -> None:
    with pytest.raises(FormatterError, match="name cannot be empty"):
        DummyFormatter(name="")


def test_base_formatter_format_timestamp_uses_cache_and_eviction() -> None:
    formatter = DummyFormatter(name="dummy")

    r1 = LogRecord(message="one", level_name="INFO", level=20)
    r1.timestamp = 1700000000.001
    r2 = LogRecord(message="two", level_name="INFO", level=20)
    r2.timestamp = 1700000000.002

    first = formatter.format_timestamp(r1)
    formatter._timestamp_cache_size = 1
    assert formatter.format_timestamp(r1) == first
    formatter.format_timestamp(r2)
    assert len(formatter._timestamp_cache) == 1


def test_base_formatter_timestamp_branches_and_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    formatter = DummyFormatter(name="dummy")

    record_no_ts = object()
    monkeypatch.setattr("hydra_logger.formatters.base.time.time", lambda: 123.0)
    assert formatter.format_timestamp(record_no_ts)

    record_dt = LogRecord(message="dt", level_name="INFO", level=20)
    from datetime import datetime

    from hydra_logger.utils.time_utility import (
        TimestampConfig,
        TimestampFormat,
        TimestampPrecision,
    )

    record_dt.timestamp = datetime(2025, 1, 1, 0, 0, 0)
    assert formatter.format_timestamp(record_dt)

    formatter_utc = DummyFormatter(
        name="dummy-utc",
        timestamp_config=TimestampConfig(
            format_type=TimestampFormat.RFC3339_MICRO,
            precision=TimestampPrecision.MICROSECONDS,
            timezone_name="UTC",
            include_timezone=True,
        ),
    )
    record_utc = LogRecord(message="utc", level_name="INFO", level=20)
    record_utc.timestamp = 1700000000.0
    assert formatter_utc.format_timestamp(record_utc)


def test_base_formatter_strip_ansi_and_failure_fallback(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    formatter = DummyFormatter(name="dummy")
    assert formatter._strip_ansi_colors("\x1b[31mboom\x1b[0m") == "boom"
    assert formatter._strip_ansi_colors("") == ""

    import re

    def raising_compile(_pattern: str) -> object:
        raise RuntimeError("regex failed")

    monkeypatch.setattr(re, "compile", raising_compile)
    clean = formatter._strip_ansi_colors("\x1b[32mok\x1b[0m")
    assert clean == "\x1b[32mok\x1b[0m"
    assert "Failed to strip ANSI colors" in caplog.text


def test_base_formatter_error_tracking_and_state_helpers() -> None:
    class FailingFormatter(BaseFormatter):
        def _format_default(self, record: LogRecord) -> str:
            raise RuntimeError("boom")

    formatter = FailingFormatter(name="failing")
    record = LogRecord(level_name="INFO", message="msg", level=20)
    with pytest.raises(FormatterError, match="Formatting failed for record"):
        formatter.format(record)

    assert formatter.has_errors() is True
    errors = formatter.get_formatting_errors()
    assert errors and "Formatting failed for record" in errors[0]
    formatter.clear_formatting_errors()
    assert formatter.has_errors() is False

    formatter.include_headers = True
    assert formatter.should_write_headers() is True
    formatter.write_header(None)
    assert formatter.should_write_headers() is False
    formatter.reset_for_new_file()
    formatter.set_file_id("file-a")
    formatter.mark_headers_written()
    assert formatter.get_format_name() == "failing"
    assert formatter.is_initialized() is True
    assert formatter.get_stats()["formatting_errors"] == 0

    healthy = DummyFormatter(name="healthy")
    assert healthy.format_for_streaming(record) == "INFO:msg"
    assert healthy.format_headers() == ""


def test_base_formatter_get_config_error_fallback() -> None:
    class BadCopyList(list):
        def copy(self) -> "BadCopyList":
            raise RuntimeError("copy failed")

    formatter = DummyFormatter(name="dummy")
    formatter._formatting_errors = BadCopyList()
    cfg = formatter.get_config()
    assert cfg["name"] == "dummy"
    assert cfg["error"] == "copy failed"


def test_base_formatter_validate_record_handles_missing_and_exceptional_attrs() -> None:
    formatter = DummyFormatter(name="dummy")
    assert formatter.validate_record(None) is False
    assert formatter.validate_record(object()) is False
    assert formatter.validate_record(
        LogRecord(level_name="INFO", message="ok", level=20)
    )

    class BrokenAttrs:
        level = 20
        message = "msg"

        def __getattribute__(self, name: str) -> object:
            if name == "level_name":
                raise RuntimeError("attr error")
            return super().__getattribute__(name)

    assert formatter.validate_record(BrokenAttrs()) is False
    assert formatter.get_config()["name"] == "dummy"


def test_base_formatter_cached_datetime_path_and_abstract_body() -> None:
    formatter = DummyFormatter(name="dummy")
    formatter.timestamp_config.format_timestamp = lambda _dt: "formatted-any"  # type: ignore[method-assign]

    class WeirdTimestamp:
        def __mul__(self, other: int) -> int:
            return other

    record = LogRecord(level_name="INFO", message="x", level=20)
    record.timestamp = WeirdTimestamp()
    assert formatter.format_timestamp(record) == "formatted-any"
    assert (
        BaseFormatter._format_default(
            formatter, LogRecord(level_name="INFO", message="x", level=20)
        )
        is None
    )
