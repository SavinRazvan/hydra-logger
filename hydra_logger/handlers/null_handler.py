"""
Role: Null handler implementation.
Used By:
 - (update when known)
Depends On:
 - base_handler
 - types
Notes:
 - Header standardized by slim-header migration.
"""

from .base_handler import BaseHandler
from ..types.records import LogRecord


class NullHandler(BaseHandler):
    """No-operation handler that discards all log records."""

    def __init__(self):
        """Initialize null handler."""
        super().__init__("null", level=0)

        # Formatter-aware handling attributes
        self._is_csv_formatter = False
        self._is_json_formatter = False
        self._is_streaming_formatter = False
        self._needs_special_handling = False

    def setFormatter(self, formatter):
        """
        Set formatter and detect if it needs special handling.

        Args:
            formatter: Formatter instance
        """
        super().setFormatter(formatter)
        if formatter:
            self._is_csv_formatter = hasattr(formatter, "format_headers") and hasattr(
                formatter, "should_write_headers"
            )
            self._is_json_formatter = hasattr(formatter, "write_header")
            self._is_streaming_formatter = hasattr(formatter, "format_for_streaming")
            self._needs_special_handling = (
                self._is_csv_formatter
                or self._is_json_formatter
                or self._is_streaming_formatter
            )
        else:
            self._is_csv_formatter = False
            self._is_json_formatter = False
            self._is_streaming_formatter = False
            self._needs_special_handling = False

    def emit(self, record: LogRecord) -> None:
        """
        Discard the log record (no operation).

        Args:
            record: Log record to discard
        """
        # Do nothing - this is a null handler
        pass

    def handle(self, record: LogRecord) -> None:
        """
        Handle the log record (no operation).

        Args:
            record: Log record to handle
        """
        # Do nothing - this is a null handler
        pass

    async def emit_async(self, record: LogRecord) -> None:
        """
        Async emit method for null handler.

        Args:
            record: Log record to discard
        """
        # Do nothing - this is a null handler
        pass
