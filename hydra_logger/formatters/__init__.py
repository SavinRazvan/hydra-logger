"""
Hydra-Logger Formatters System

This module provides a comprehensive formatter system for Hydra-Logger with
ultra-high performance, standardized formatting, and support for multiple
output formats. The formatter system is designed for maximum throughput
and minimal latency while maintaining data integrity.

ARCHITECTURE:
- BaseFormatter: Abstract base class for all formatters
- Standardized interface across all formatter types
- Consistent timestamp formatting
- Structured data support for complex logging scenarios

FORMATTER TYPES:
- Text Formatters: PlainTextFormatter for clean text output
- JSON Formatters: JsonLinesFormatter for structured logging
- Structured Formatters: CSV, Syslog, GELF, Logstash formats

FORMATTER FEATURES:
- High-performance string formatting
- Consistent timestamp formatting
- Structured data support (extra and context fields)
- Industry standard compliance
- Clean, readable output formats

TEXT FORMATTING:
- PlainTextFormatter: Clean text output without colors
- Optimized for file handlers and console output
- Standardized format string support
- High performance with minimal overhead

STANDARDIZED FORMATTING:
- Unified format function interface across all formatters
- Consistent timestamp formatting across all formatters
- Structured data support (extra and context fields)
- Industry standard compliance
- Thread-safe operations

USAGE EXAMPLES:

Basic Formatter Usage:
    from hydra_logger.formatters import get_formatter
    
    # Get colored formatter for console
    formatter = get_formatter('colored', use_colors=True)
    
    # Get plain formatter for file
    formatter = get_formatter('plain-text', use_colors=False)
    
    # Get JSON formatter for structured logging
    formatter = get_formatter('json-lines', use_colors=False)

Direct Formatter Creation:
    from hydra_logger.formatters import PlainTextFormatter, JsonLinesFormatter
    
    # Create text formatter
    text_formatter = PlainTextFormatter()
    
    # Create JSON formatter
    json_formatter = JsonLinesFormatter()

Custom Formatting:
    from hydra_logger.formatters import PlainTextFormatter
    
    # Create formatter with custom format string
    formatter = PlainTextFormatter("{timestamp} {level_name} {message}")
    
    # Create formatter with custom timestamp config
    from hydra_logger.utils.time_utility import TimestampConfig, TimestampFormat, TimestampPrecision
    config = TimestampConfig(
        format_type=TimestampFormat.RFC3339_MICRO,
        precision=TimestampPrecision.MICROSECONDS
    )
    formatter = PlainTextFormatter(timestamp_config=config)

AVAILABLE FORMATTERS:
- PlainTextFormatter: Basic text formatting with customizable format strings
- JsonLinesFormatter: JSON Lines format for structured logging
- CsvFormatter: CSV format with proper headers and quoting
- SyslogFormatter: Syslog format for system logging
- GelfFormatter: Graylog Extended Log Format
- LogstashFormatter: Logstash format for Elasticsearch

FORMATTER FEATURES:
- Standardized interface across all formatters
- Consistent timestamp formatting
- Structured data support (extra and context fields)
- Industry standard compliance
- High performance with minimal overhead
- Thread-safe operations
"""

# Core formatters
from .base import BaseFormatter
from .text_formatter import PlainTextFormatter
from .colored_formatter import ColoredFormatter
from .json_formatter import JsonLinesFormatter
from .structured_formatter import GelfFormatter, LogstashFormatter, CsvFormatter, SyslogFormatter

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
    "get_formatter"
]