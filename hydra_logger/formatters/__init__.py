"""
Role: Public formatter package exports and factory helpers.
Used By:
 - hydra_logger/handlers/base_handler.py for formatter type references.
 - Client code importing `hydra_logger.formatters` symbols and helpers.
Depends On:
 - base
 - text_formatter
 - colored_formatter
 - json_formatter
 - structured_formatter
Notes:
 - Re-exports formatter classes and creates formatter instances by format name.
"""

# Core formatters
from .base import BaseFormatter
from .colored_formatter import ColoredFormatter
from .json_formatter import JsonLinesFormatter
from .structured_formatter import (
    CsvFormatter,
    GelfFormatter,
    LogstashFormatter,
    SyslogFormatter,
)
from .text_formatter import PlainTextFormatter


def get_formatter(format_type: str, use_colors: bool = False):
    """
    Get the appropriate formatter for a given format type.

    Args:
        format_type: Format type (e.g., 'plain-text', 'json-lines', 'colored')
        use_colors: Whether to use colors (for console output only)

    Returns:
        Formatter instance or None if not found

    Example:
        # Get colored formatter for console
        formatter = get_formatter('colored', use_colors=True)

        # Get plain formatter for file
        formatter = get_formatter('plain-text', use_colors=False)
    """
    if format_type == "plain-text":
        return PlainTextFormatter()
    elif format_type == "colored":
        return ColoredFormatter(use_colors=use_colors)
    elif format_type == "json-lines":
        return JsonLinesFormatter()
    elif format_type == "json":
        return JsonLinesFormatter()
    elif format_type == "csv":
        return CsvFormatter()
    elif format_type == "syslog":
        return SyslogFormatter()
    elif format_type == "gelf":
        return GelfFormatter()
    elif format_type == "logstash":
        return LogstashFormatter()
    else:
        # Default to plain text
        return PlainTextFormatter()


# Export all formatters
__all__ = [
    # Core formatters
    "BaseFormatter",
    "PlainTextFormatter",
    "ColoredFormatter",
    "JsonLinesFormatter",
    "GelfFormatter",
    "LogstashFormatter",
    "CsvFormatter",
    "SyslogFormatter",
    # Utility functions
    "get_formatter",
]
