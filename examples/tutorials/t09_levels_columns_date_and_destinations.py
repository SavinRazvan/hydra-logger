#!/usr/bin/env python3
"""
Role: Enterprise onboarding tutorial for levels, columns/date, formats, and destinations.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates level hierarchy, formatter column selection, timestamp format control,
   layers, and multi-destination routing.
"""

import inspect

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger
from hydra_logger.formatters.text_formatter import PlainTextFormatter
from hydra_logger.types.records import LogRecord
from hydra_logger.utils.time_utility import TimestampConfig, TimestampFormat, TimestampPrecision


def build_config() -> LoggingConfig:
    return LoggingConfig(
        default_level="WARNING",
        layers={
            "api": LogLayer(
                level="INFO",
                destinations=[
                    # Destination-level level overrides layer level for this sink.
                    LogDestination(type="console", format="colored", use_colors=True, level="DEBUG"),
                    LogDestination(
                        type="file",
                        path="logs/examples/tutorials/t09_api.jsonl",
                        format="json-lines",
                        level="INFO",
                    ),
                    LogDestination(
                        type="file",
                        path="logs/examples/tutorials/t09_api_audit.log",
                        format="plain-text",
                        level="WARNING",
                    ),
                ],
            ),
            "security": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(type="console", format="plain-text", use_colors=False),
                    LogDestination(
                        type="file",
                        path="logs/examples/tutorials/t09_security.jsonl",
                        format="json-lines",
                    ),
                ],
            ),
        },
    )


def show_columns_and_date_format_control() -> None:
    # Custom columns: timestamp, level, layer, message, function and line.
    # Custom date: RFC3339 with microseconds in UTC.
    formatter = PlainTextFormatter(
        format_string=(
            "{timestamp} | {level_name} | {layer} | {message} | "
            "{function_name}:{line_number}"
        ),
        timestamp_config=TimestampConfig(
            format_type=TimestampFormat.RFC3339_MICRO,
            precision=TimestampPrecision.MICROSECONDS,
            timezone_name="UTC",
            include_timezone=True,
        ),
    )
    current_frame = inspect.currentframe()
    preview_line = current_frame.f_lineno + 1 if current_frame else 0
    preview_record = LogRecord(
        level_name="INFO",
        message="[T09] formatter preview for columns/date customization",
        level=20,
        layer="api",
        logger_name="tutorial-t09",
        file_name="t09_levels_columns_date_and_destinations.py",
        function_name="show_columns_and_date_format_control",
        line_number=preview_line,
        context={"correlation_id": "t09-preview"},
    )
    print("T09 formatter preview:")
    print(formatter.format(preview_record))


def main() -> None:
    config = build_config()

    with create_logger(config, logger_type="sync") as logger:
        # Layer level INFO allows this, destination levels decide final sink behavior.
        logger.debug("[T09] debug event for destination-level filtering", layer="api")
        logger.info("[T09] info event for api layer", layer="api")
        logger.warning("[T09] warning event for api/audit sinks", layer="api")
        logger.error("[T09] security alert", layer="security")

    show_columns_and_date_format_control()
    print("T09 completed: levels, columns/date, formats, layers, destinations")


if __name__ == "__main__":
    main()
