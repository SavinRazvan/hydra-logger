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
import socket
import sys
import types

import pytest

from hydra_logger.formatters.colored_formatter import ColoredFormatter
from hydra_logger.formatters.structured_formatter import (
    CsvFormatter,
    GelfFormatter,
    LogstashFormatter,
    SyslogFormatter,
    _get_timestamp_config,
)
from hydra_logger.types.records import LogRecord
from hydra_logger.utils.time_utility import TimestampFormat


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

    logstash_payload = json.loads(
        LogstashFormatter(type_name="api-logs").format(record)
    )
    assert logstash_payload["type"] == "api-logs"
    assert logstash_payload["fields"]["request_id"] == "r-1"


def test_colored_formatter_disables_color_when_configured() -> None:
    formatter = ColoredFormatter(use_colors=False)
    line = formatter.format(_record())
    assert "\x1b[" not in line


def test_colored_formatter_color_helpers_cover_unknown_levels() -> None:
    formatter = ColoredFormatter(use_colors=True)
    assert "\x1b[" in formatter._colorize("x", "\x1b[31m")
    assert formatter._colorize_level("custom")
    assert formatter._colorize_layer("unknown-layer")
    plain = ColoredFormatter(use_colors=False)
    assert plain._colorize("x", "\x1b[31m") == "x"


def test_colored_formatter_format_applies_level_and_layer_colors() -> None:
    formatter = ColoredFormatter(use_colors=True)
    rendered = formatter.format(_record())
    assert "\x1b[" in rendered


def test_environment_timestamp_config_switches_between_profiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    prod = _get_timestamp_config()
    assert prod.format_type == TimestampFormat.RFC3339_MICRO

    monkeypatch.setenv("ENVIRONMENT", "dev")
    dev = _get_timestamp_config()
    assert dev.format_type == TimestampFormat.HUMAN_READABLE


def test_csv_formatter_header_write_lifecycle(tmp_path) -> None:
    formatter = CsvFormatter(include_headers=True)
    file_path = tmp_path / "events.csv"
    file_path.write_text("existing content")

    assert formatter.should_write_headers(str(file_path)) is False
    assert formatter.should_write_headers() is True
    formatter.mark_headers_written()
    assert formatter.should_write_headers() is False

    formatter.mark_headers_written(str(file_path))
    assert formatter.should_write_headers(str(file_path)) is False

    formatter_disabled = CsvFormatter(include_headers=False)
    assert formatter_disabled.should_write_headers(str(file_path)) is False

    empty_file = tmp_path / "new.csv"
    empty_file.write_text("")
    assert formatter_disabled.should_write_headers(str(empty_file)) is False
    assert formatter.should_write_headers(str(empty_file)) is True


def test_syslog_detect_app_name_from_env_and_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_NAME", "svc-env")
    assert SyslogFormatter().app_name == "svc-env"

    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.setattr(sys, "argv", ["/tmp/run_worker.py"])
    assert SyslogFormatter().app_name == "run_worker"


def test_syslog_detect_app_name_from_psutil_and_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("SERVICE_NAME", raising=False)
    monkeypatch.setattr(sys, "argv", ["-c"])

    fake_psutil = types.SimpleNamespace(
        Process=lambda: types.SimpleNamespace(name=lambda: "proc-name")
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    assert SyslogFormatter().app_name == "proc-name"

    monkeypatch.setitem(sys.modules, "psutil", None)
    assert SyslogFormatter().app_name == "hydra-logger"


def test_syslog_format_default_and_unknown_level_path() -> None:
    record = _record()
    record.level = 15
    formatter = SyslogFormatter(app_name="svc")
    rendered = formatter._format_default(record)
    assert "<14>" in rendered
    assert formatter.get_required_extension() == ".log"

    record.file_name = None
    record.function_name = None
    short = formatter.format(record)
    assert "svc ERROR" in short


def test_gelf_detect_hostname_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTNAME", "env-host")
    assert GelfFormatter().host == "env-host"

    monkeypatch.delenv("HOSTNAME", raising=False)
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.setattr(socket, "gethostname", lambda: "host-1")
    assert GelfFormatter().host == "host-1"

    monkeypatch.setattr(socket, "gethostname", lambda: "localhost")
    monkeypatch.setattr(socket, "getfqdn", lambda: "fqdn.local")
    assert GelfFormatter().host == "fqdn.local"

    monkeypatch.setattr(
        socket, "gethostname", lambda: (_ for _ in ()).throw(RuntimeError("host fail"))
    )
    monkeypatch.setattr(
        socket,
        "getfqdn",
        lambda: (_ for _ in ()).throw(RuntimeError("fqdn fail")),
    )
    assert GelfFormatter().host == "localhost"


def test_gelf_and_logstash_format_default_methods() -> None:
    record = _record()
    gelf = GelfFormatter(host="h")
    logstash = LogstashFormatter(type_name="x", tags=["a"])

    assert json.loads(gelf._format_default(record))["host"] == "h"
    assert json.loads(logstash._format_default(record))["type"] == "x"
    assert gelf.get_required_extension() == ".gelf"
    assert logstash.get_required_extension() == ".log"


def test_logstash_detect_type_and_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_TYPE", "api-custom")
    assert LogstashFormatter().type_name == "api-custom"

    monkeypatch.delenv("LOG_TYPE", raising=False)
    monkeypatch.delenv("SERVICE_TYPE", raising=False)
    monkeypatch.setattr(sys, "argv", ["/tmp/web_server.py"])
    assert LogstashFormatter().type_name == "web-logs"

    monkeypatch.setattr(sys, "argv", ["/tmp/worker_jobs.py"])
    assert LogstashFormatter().type_name == "worker-logs"

    monkeypatch.setattr(sys, "argv", ["/tmp/cron_tick.py"])
    assert LogstashFormatter().type_name == "cron-logs"

    monkeypatch.setattr(sys, "argv", ["/tmp/api_server.py"])
    assert LogstashFormatter().type_name == "api-logs"

    monkeypatch.setattr(sys, "argv", ["/tmp/any_script.py"])
    detected = LogstashFormatter().type_name
    assert detected == "any_script-logs"

    monkeypatch.setattr(sys, "argv", ["-c"])
    assert LogstashFormatter().type_name == "application-logs"

    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("SERVICE_NAME", "orders")
    monkeypatch.setenv("PLATFORM", "k8s")
    tags = LogstashFormatter().tags
    assert tags[:3] == ["staging", "orders", "k8s"]


def test_csv_formatter_formats_empty_structured_data_without_context() -> None:
    record = LogRecord(level_name="INFO", message="ok", level=20)
    record.extra = {}
    record.context = {}
    row = CsvFormatter().format(record)
    assert row.endswith(",")
