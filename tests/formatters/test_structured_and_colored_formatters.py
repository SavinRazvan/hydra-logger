"""
Role: Pytest coverage for structured and colored formatter behavior.
Used By:
 - Pytest discovery and local CI quality gates.
Depends On:
 - hydra_logger
Notes:
 - Validates CSV/syslog/GELF/logstash outputs and color toggling.
"""

import json

from hydra_logger.formatters.colored_formatter import ColoredFormatter
from hydra_logger.formatters.structured_formatter import (
    CsvFormatter,
    GelfFormatter,
    LogstashFormatter,
    SyslogFormatter,
)
from hydra_logger.types.records import LogRecord


def _record() -> LogRecord:
    return LogRecord(
        level_name="ERROR",
        message='bad "input", retry',
        level=40,
        layer="api",
        logger_name="HydraLogger",
        file_name="api.py",
        function_name="handle",
        line_number=11,
        extra={"code": "E-1"},
        context={"request_id": "r-1"},
    )


def test_csv_formatter_escapes_commas_and_quotes() -> None:
    formatter = CsvFormatter(include_headers=True)
    headers = formatter.format_headers()
    line = formatter.format(_record())
    assert "timestamp" in headers.lower()
    assert '"bad ""input"", retry"' in line
    assert formatter.get_required_extension() == ".csv"


def test_syslog_gelf_and_logstash_formatters_include_expected_fields() -> None:
    record = _record()
    syslog_payload = SyslogFormatter(app_name="svc").format(record)
    assert "<" in syslog_payload and "svc" in syslog_payload

    gelf_payload = json.loads(GelfFormatter(host="host-a").format(record))
    assert gelf_payload["host"] == "host-a"
    assert gelf_payload["short_message"] == 'bad "input", retry'

    logstash_payload = json.loads(LogstashFormatter(type_name="api-logs").format(record))
    assert logstash_payload["type"] == "api-logs"
    assert logstash_payload["fields"]["request_id"] == "r-1"


def test_colored_formatter_disables_color_when_configured() -> None:
    formatter = ColoredFormatter(use_colors=False)
    line = formatter.format(_record())
    assert "\x1b[" not in line
