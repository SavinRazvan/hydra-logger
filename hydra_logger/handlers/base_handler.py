"""
Role: Base handler implementation.
Used By:
 - (update when known)
Depends On:
 - abc
 - typing
 - types
 - formatters
 - utils
Notes:
 - Header standardized by slim-header migration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..formatters.base import BaseFormatter
from ..types.records import LogRecord
from ..utils.time_utility import TimestampConfig, TimestampFormat, TimestampPrecision


class BaseHandler(ABC):
    """Abstract base class for all handlers."""

    def __init__(
        self,
        name: str = "base",
        level: int = 0,
        timestamp_config: Optional[TimestampConfig] = None,
    ):
        """
        Initialize base handler.

        Args:
            name: Handler name for identification
            level: Minimum log level to handle
            timestamp_config: Configuration for timestamp formatting
        """
        self.name = name
        self.level = level
        self.formatter: Optional[BaseFormatter] = None
        self.timestamp_config = timestamp_config or TimestampConfig(
            format_type=TimestampFormat.RFC3339_MICRO,
            precision=TimestampPrecision.MICROSECONDS,
            timezone_name=None,  # Local timezone
            include_timezone=True,
        )
        self._initialized = True
        self._closed = False

        # Performance optimization: cache formatter name
        self._formatter_name = None

    def format_timestamp(self, record: LogRecord) -> str:
        """
        Format timestamp from log record using configured timestamp format.

        Args:
            record: Log record containing timestamp information

        Returns:
            Formatted timestamp string
        """
        from datetime import datetime, timezone

        # Convert record timestamp to datetime
        if hasattr(record, "timestamp") and record.timestamp:
            if isinstance(record.timestamp, (int, float)):
                # Unix timestamp - use local timezone if configured
                if self.timestamp_config.timezone_name is None:
                    dt = datetime.fromtimestamp(record.timestamp)
                else:
                    dt = datetime.fromtimestamp(record.timestamp, tz=timezone.utc)
            else:
                # Assume it's already a datetime
                dt = record.timestamp
        else:
            # Fallback to current time
            if self.timestamp_config.timezone_name is None:
                dt = datetime.now()
            else:
                dt = datetime.now(timezone.utc)

        return self.timestamp_config.format_timestamp(dt)

    def setFormatter(self, formatter: BaseFormatter) -> None:
        """
        Set the formatter for this handler.

        Args:
            formatter: Formatter instance
        """
        self.formatter = formatter
        # Cache formatter name for performance
        if formatter:
            try:
                self._formatter_name = formatter.get_format_name()
            except Exception:
                self._formatter_name = "unknown"
        else:
            self._formatter_name = None

    def setLevel(self, level: int) -> None:
        """
        Set the minimum log level for this handler.

        Args:
            level: Minimum log level
        """
        self.level = level

    def isEnabledFor(self, level: int) -> bool:
        """
        Check if handler is enabled for the given level.

        Args:
            level: Log level to check

        Returns:
            True if enabled, False otherwise
        """
        return level >= self.level

    @abstractmethod
    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record.

        Args:
            record: Log record to emit
        """
        raise NotImplementedError("Subclasses must implement emit method")

    def handle(self, record: LogRecord) -> None:
        """
        Handle a log record (check level and emit if enabled).

        Args:
            record: Log record to handle
        """
        if self.isEnabledFor(record.level):
            self.emit(record)

    def close(self) -> None:
        """Close the handler and cleanup resources."""
        self._closed = True

    def is_initialized(self) -> bool:
        """
        Check if handler is properly initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    def is_closed(self) -> bool:
        """
        Check if handler is closed.

        Returns:
            True if closed, False otherwise
        """
        return self._closed

    def get_config(self) -> Dict[str, Any]:
        """
        Get handler configuration (OPTIMIZED for performance).

        Returns:
            Configuration dictionary
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "level": self.level,
            "initialized": self._initialized,
            "closed": self._closed,
            "formatter": self._formatter_name,  # Use cached value instead of expensive call
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this handler.

        Returns:
            Performance metrics dictionary
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "level": self.level,
            "initialized": self._initialized,
            "closed": self._closed,
            "formatter_cached": self._formatter_name is not None,
            "performance_optimized": True,
        }
