"""
Role: Json formatter implementation.
Used By:
 - hydra_logger/formatters/__init__.py for formatter factory and exports.
Depends On:
 - json
 - typing
 - base
 - types
 - utils
Notes:
 - Emits newline-delimited JSON records with predictable field serialization.
"""

import json

# import time  # unused
from typing import Any, Dict, Optional

from ..types.records import LogRecord
from ..utils.time_utility import TimestampConfig
from .base import BaseFormatter


class JsonLinesFormatter(BaseFormatter):
    """Primary JSON formatter for Hydra-Logger - creates valid JSON Lines files."""

    def __init__(
        self,
        ensure_ascii: bool = False,
        timestamp_config: Optional[TimestampConfig] = None,
    ):
        """
        Initialize JSON Lines formatter.

        Args:
            ensure_ascii: Whether to escape non-ASCII characters
            timestamp_config: Configuration for timestamp formatting

        Note: This is the recommended JSON formatter for file output.
        Creates valid JSONL files with one JSON object per line.
        """
        # Set timestamp config if not provided
        if timestamp_config is None:
            timestamp_config = self._get_timestamp_config()
        super().__init__("json_lines", timestamp_config=timestamp_config)
        self.ensure_ascii = ensure_ascii

        # Performance optimization: Pre-compiled JSON encoder
        self._encoder = json.JSONEncoder(
            ensure_ascii=ensure_ascii,
            separators=(",", ":"),  # Compact JSON
            sort_keys=False,  # Don't sort for performance
        )

        # Simplified formatter - no performance optimization
        self._format_func = self._format_default

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
        """Create record dictionary with minimal overhead."""
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
