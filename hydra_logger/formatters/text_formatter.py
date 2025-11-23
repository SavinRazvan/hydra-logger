"""
Text Formatters for Hydra-Logger

This module provides plain text formatters for different
use cases with performance focus. These formatters are designed
for file output and console output without colors.

ARCHITECTURE:
- PlainTextFormatter: Text formatting with customizable format strings (default includes timestamp)
- Format Optimization: Pre-compiled format functions for common patterns
- Clean Output: Uncolored text suitable for files and console

FORMATTER FEATURES:
- String formatting
- Pre-compiled format functions for common patterns
- Clean, readable text output
- Customizable format strings

FORMAT FEATURES:
- F-string compilation for common format patterns
- Direct string concatenation for better performance
- Format string caching and reuse
- Customizable format templates

COLOR SYSTEM NOTE:
- Plain text formatters do NOT support colors
- Used for file handlers and console handlers with use_colors=False
- ColoredFormatter should be used for colored console output
- These formatters provide clean, uncolored text output

USAGE EXAMPLES:

Basic Text Formatting:
    from hydra_logger.formatters.text_formatter import PlainTextFormatter

    # Create formatter with default format (includes timestamp)
    formatter = PlainTextFormatter()

    # Create formatter with custom format
    formatter = PlainTextFormatter("{timestamp} {level_name} {message}")

    # Create formatter without timestamp
    formatter = PlainTextFormatter("{level_name} {layer} {message}")

Alternative Formats:
    from hydra_logger.formatters.text_formatter import PlainTextFormatter

    # Format without layer information
    formatter = PlainTextFormatter("{timestamp} {level_name} {message}")

    # Minimal format with just level and message
    formatter = PlainTextFormatter("{level_name} {message}")

Custom Formatting:
    from hydra_logger.formatters.text_formatter import PlainTextFormatter

    # Create formatter with custom format string
    formatter = PlainTextFormatter("{timestamp} {level_name} {message}")

    # Create formatter with custom timestamp config
    from hydra_logger.utils.time_utility import TimestampConfig, TimestampFormat, TimestampPrecision
    config = TimestampConfig(
        format_type=TimestampFormat.RFC3339_MICRO,
        precision=TimestampPrecision.MICROSECONDS
    )
    formatter = PlainTextFormatter(timestamp_config=config)

FORMAT STRING PATTERNS:
- "{timestamp} {level_name} {layer} {message}": DEFAULT - Full format with timestamp
- "{level_name} {layer} {message}": Alternative format without timestamp
- "{timestamp} {level_name} {message}": Format with timestamp but no layer
- "{level_name} {message}": Minimal format with level only
- "{message}": Message-only format
"""

# from datetime import datetime  # unused
from typing import Optional
from .base import BaseFormatter
from ..types.records import LogRecord
from ..utils.time_utility import TimestampConfig


class PlainTextFormatter(BaseFormatter):
    """Plain text formatter with customizable format string. Default format includes timestamp, level, layer, and message."""

    def __init__(
        self,
        format_string: str = None,
        timestamp_config: Optional[TimestampConfig] = None,
    ):
        """
        Initialize plain text formatter.

        Args:
            format_string: Format template using {field} placeholders
            timestamp_config: Configuration for timestamp formatting
        """
        # Set timestamp config if not provided
        if timestamp_config is None:
            timestamp_config = self._get_timestamp_config()
        super().__init__("plain_text", timestamp_config)
        self.format_string = (
            format_string or "{timestamp} {level_name} {layer} {message}"
        )

        # Simplified formatter - no performance optimization
        self._format_func = self._format_default

        # Performance optimization: Caching
        self._format_cache = {}
        self._use_fstring = self._should_use_fstring()
        self._compiled_format = None

        # Pre-compile format string if possible
        if self._use_fstring:
            self._compiled_format = self._compile_fstring_format()

    def _get_timestamp_config(self):
        """
        Get timestamp configuration based on environment.

        Returns:
            Timestamp configuration
        """
        import os
        from ..utils.time_utility import (
            TimestampConfig,
            TimestampFormat,
            TimestampPrecision,
        )

        # Check if we're in production environment
        is_production = os.environ.get("ENVIRONMENT", "").lower() in [
            "production",
            "prod",
        ]

        if is_production:
            # Production: UTC, microsecond precision, RFC3339 format
            return TimestampConfig(
                format_type=TimestampFormat.RFC3339_MICRO,
                precision=TimestampPrecision.MICROSECONDS,
                timezone_name="UTC",
                include_timezone=True,
            )
        else:
            # Development: Local timezone, second precision, human readable
            return TimestampConfig(
                format_type=TimestampFormat.HUMAN_READABLE,
                precision=TimestampPrecision.SECONDS,
                timezone_name=None,  # Local timezone
                include_timezone=False,
            )

    def _should_use_fstring(self) -> bool:
        """Check if we can use f-string formatting for better performance."""
        # Use f-string for simple, common format patterns
        simple_patterns = [
            "{level_name} {layer} {message}",
            "{timestamp} {level_name} {layer} {message}",
            "{timestamp} {level_name} {message}",
            "{level_name} {message}",
            "{message}",
        ]
        return self.format_string in simple_patterns

    def _compile_fstring_format(self) -> callable:
        """Compile format string into function with cached timestamp formatting."""
        # Use f-strings with timestamp caching
        if self.format_string == "{timestamp} {level_name} {layer} {message}":
            # Pre-cache timestamp formatting method for speed
            format_ts = self.format_timestamp
            return lambda r: f"{format_ts(r)} {r.level_name} {r.layer} {r.message}"
        elif self.format_string == "{level_name} {layer} {message}":
            # No timestamp - fastest path
            return lambda r: f"{r.level_name} {r.layer} {r.message}"
        elif self.format_string == "{timestamp} {level_name} {message}":
            format_ts = self.format_timestamp
            return lambda r: f"{format_ts(r)} {r.level_name} {r.message}"
        elif self.format_string == "{level_name} {message}":
            return lambda r: f"{r.level_name} {r.message}"
        elif self.format_string == "{message}":
            return lambda r: f"{r.message}"
        else:
            return None

    def format(self, record: LogRecord) -> str:
        """
        Format record using format string template or FormattingEngine.

        Args:
            record: Log record to format

        Returns:
            Formatted string
        """
        # Use compiled path if available
        if self._compiled_format:
            # Use pre-compiled f-string
            return self._compiled_format(record)
        else:
            # Use standardized formatter with LRU cache
            return self._format_func(record)

    def get_required_extension(self) -> str:
        """
        Get the required file extension for Plain Text formatter.

        Returns:
            '.log' - Industry standard for plain text log files
        """
        return ".log"

    def _format_default(self, record: LogRecord) -> str:
        """
        Default formatting implementation for backward compatibility.
        
        Uses f-strings instead of .format() for better performance.

        Args:
            record: Log record to format

        Returns:
            Formatted string
        """
        # Use f-strings instead of .format()
        # Extract values once for better performance
        timestamp_str = self.format_timestamp(record)
        level_name = record.level_name
        message = record.message
        layer = record.layer
        file_name = record.file_name or "unknown"
        function_name = record.function_name or "unknown"
        
        # Direct f-string interpolation
        # Replace placeholders with f-string interpolation
        result = self.format_string.replace("{timestamp}", timestamp_str)\
                                   .replace("{level_name}", level_name)\
                                   .replace("{message}", message)\
                                   .replace("{layer}", layer)\
                                   .replace("{logger_name}", record.logger_name)\
                                   .replace("{file_name}", file_name)\
                                   .replace("{function_name}", function_name)\
                                   .replace("{line_number}", str(record.line_number or 0))
        
        return result
