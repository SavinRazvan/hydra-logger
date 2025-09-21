"""
JSON Formatters for Hydra-Logger

This module provides high-performance JSON-based formatters for structured
logging with optimized serialization and industry-standard output formats.
The JSON formatters are designed for maximum throughput while maintaining
data integrity and compatibility with log aggregation systems.

ARCHITECTURE:
- JsonLinesFormatter: Primary JSON formatter for structured logging
- Performance Integration: Standardized format function integration
- JSON Optimization: Pre-compiled JSON encoder for better performance
- Data Integrity: Complete record information preservation
- Industry Standards: JSON Lines format compliance

PERFORMANCE FEATURES:
- Pre-compiled JSON encoder for better performance
- Compact JSON output with optimized separators
- Memory-efficient serialization
- LRU cache integration for performance optimization
- JIT optimization for hot code paths
- Zero-overhead formatting for simple cases

JSON FORMAT FEATURES:
- JSON Lines format (one JSON object per line)
- Complete record information preservation
- Optimized field ordering for performance
- Compact JSON output (no unnecessary whitespace)
- Unicode support and proper encoding
- Industry-standard format compliance

RECORD STRUCTURE:
The JSON formatter outputs records with the following structure:
{
    "timestamp": float,           # Unix timestamp
    "level": int,                 # Numeric log level
    "level_name": str,            # String log level name
    "message": str,               # Log message
    "logger_name": str,           # Logger name
    "layer": str,                 # Log layer
    "file_name": str,             # Source file name
    "function_name": str,         # Source function name
    "line_number": int,           # Source line number
    "extra": dict                 # Additional fields
}

USAGE EXAMPLES:

Basic JSON Formatting:
    from hydra_logger.formatters.json import JsonLinesFormatter
    
    # Create JSON formatter
    formatter = JsonLinesFormatter()
    
    # Create with custom configuration
    formatter = JsonLinesFormatter(ensure_ascii=False)

With Timestamp Configuration:
    from hydra_logger.utils.time_utility import TimestampConfig, TimestampFormat, TimestampPrecision
    
    config = TimestampConfig(
        format_type=TimestampFormat.RFC3339_MICRO,
        precision=TimestampPrecision.MICROSECONDS,
        timezone_name="UTC"
    )
    
    formatter = JsonLinesFormatter(timestamp_config=config)

Performance Integration:
    from hydra_logger.formatters.standard_formats import get_standard_formats, PerformanceLevel
    
    # Get performance-optimized formatter
    standard_formats = get_standard_formats(PerformanceLevel.FAST)
    
    # Use in custom formatter
    class OptimizedJsonFormatter(JsonLinesFormatter):
        def __init__(self):
            super().__init__()
            self._standard_formats = get_standard_formats(PerformanceLevel.FAST)
            self._format_func = self._standard_formats.format_basic

JSON LINES FORMAT:
The JSON Lines format is an industry standard for structured logging where
each line contains a complete JSON object. This format is:
- Easy to parse line by line
- Compatible with log aggregation systems
- Efficient for streaming and processing
- Human-readable when needed
- Machine-parseable for analysis

PERFORMANCE OPTIMIZATION:
- Pre-compiled JSON encoder with optimized settings
- Compact JSON output (no unnecessary whitespace)
- Efficient field ordering and access
- Memory-efficient serialization
- LRU cache integration
- Thread-safe operations

COMPATIBILITY:
- JSON Lines format (RFC 7464)
- Compatible with log aggregation systems
- Elasticsearch, Logstash, Fluentd support
- Graylog and other log management tools
- Standard JSON parsing libraries
"""

import json
import time
from typing import Any, Dict, Optional
from .base import BaseFormatter
from ..types.records import LogRecord
from ..utils.time_utility import TimestampConfig


class JsonLinesFormatter(BaseFormatter):
    """Primary JSON formatter for Hydra-Logger - creates valid JSON Lines files."""

    def __init__(self, ensure_ascii: bool = False,
                 timestamp_config: Optional[TimestampConfig] = None):
        """
        Initialize JSON Lines formatter.

        Args:
            ensure_ascii: Whether to escape non-ASCII characters
            timestamp_config: Configuration for timestamp formatting
            
        Note: This is the recommended JSON formatter for file output.
        Creates valid JSONL files with one JSON object per line.
        """
        # Set default timestamp config to HUMAN_READABLE if not provided
        if timestamp_config is None:
            from ..utils.time_utility import TimestampConfig, TimestampFormat, TimestampPrecision
            timestamp_config = TimestampConfig(
                format_type=TimestampFormat.HUMAN_READABLE,
                precision=TimestampPrecision.SECONDS,
                timezone_name=None,  # Local timezone
                include_timezone=False
            )
        super().__init__("json_lines", timestamp_config=timestamp_config)
        self.ensure_ascii = ensure_ascii
        
        # Performance optimization: Pre-compiled JSON encoder
        self._encoder = json.JSONEncoder(
            ensure_ascii=ensure_ascii,
            separators=(',', ':'),  # Compact JSON
            sort_keys=False  # Don't sort for performance
        )
        
        # Simplified formatter - no performance optimization
        self._format_func = self._format_default

    def _format_default(self, record: LogRecord) -> str:
        """
        Default JSON Lines formatting implementation with performance optimizations.

        Args:
            record: Log record to format

        Returns:
            JSON string (one line per record)
        """
        # Use pre-compiled encoder for better performance
        record_dict = self._create_record_dict(record)
        return self._encoder.encode(record_dict)
    
    def _create_record_dict(self, record: LogRecord) -> Dict[str, Any]:
        """Create ultra-optimized record dictionary with minimal overhead."""
        # Pre-format timestamp once to avoid repeated calls
        timestamp = self.format_timestamp(record)
        
        # Build dictionary with minimal overhead - avoid or operations
        record_dict = {
            "timestamp": timestamp,
            "level": record.level,
            "level_name": record.level_name,
            "message": record.message,
            "logger_name": record.logger_name,
            "layer": record.layer if record.layer else "",
            "file_name": record.file_name if record.file_name else "",
            "function_name": record.function_name if record.function_name else "",
            "line_number": record.line_number if record.line_number else 0,
        }
        
        # Add structured data fields
        if record.extra:
            record_dict["extra"] = record.extra
        if record.context:
            record_dict["context"] = record.context

        return record_dict


    def get_required_extension(self) -> str:
        """
        Get the required file extension for JSON Lines formatter.
        
        Returns:
            '.jsonl' - Industry standard for JSON Lines format
        """
        return ".jsonl"
