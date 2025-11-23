"""
Null Handler for Hydra-Logger

This module provides a no-operation handler that discards all log records.
It's useful for testing, debugging, and scenarios where logging should be
disabled without removing handler references.

ARCHITECTURE:
- NullHandler: No-operation handler that discards all records
- Minimal overhead and memory usage
- Thread-safe operations
- Performance monitoring capabilities

CORE FEATURES:
- Discards all log records without processing
- Minimal memory and CPU overhead
- Thread-safe operations
- Performance statistics tracking
- Async support for compatibility

USAGE EXAMPLES:

Basic Null Handler:
    from hydra_logger.handlers import NullHandler

    handler = NullHandler()
    logger.addHandler(handler)

    # All log messages will be discarded
    logger.info("This message will be discarded")

Testing and Debugging:
    # Use null handler to disable logging during tests
    handler = NullHandler()
    logger.addHandler(handler)

    # Perform operations without logging
    result = some_operation()

    # Remove null handler to re-enable logging
    logger.removeHandler(handler)

Performance Testing:
    # Use null handler to measure pure logging overhead
    handler = NullHandler()
    logger.addHandler(handler)

    # Measure performance without I/O overhead
    start_time = time.time()
    for i in range(1000000):
        logger.info(f"Message {i}")
    end_time = time.time()

    print(f"Null handler performance: {end_time - start_time:.2f} seconds")

Async Support:
    # Null handler supports async operations
    await handler.emit_async(record)

PERFORMANCE CHARACTERISTICS:
- Minimal CPU overhead
- Zero I/O operations
- Minimal memory usage
- Thread-safe operations
- Fastest possible handler

THREAD SAFETY:
- Thread-safe operations
- Safe concurrent access
- No shared state
- Atomic operations

ERROR HANDLING:
- No error conditions possible
- Always succeeds
- No fallback needed
- Graceful operation
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
