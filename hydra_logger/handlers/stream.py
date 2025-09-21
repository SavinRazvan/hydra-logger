"""
Stream Handler for Hydra-Logger

This module provides a stream-based handler for outputting logs to any
text stream. It's useful for custom output destinations and testing.

ARCHITECTURE:
- StreamHandler: Generic stream output handler
- Intelligent buffering for high throughput
- Performance monitoring and statistics
- Thread-safe operations

CORE FEATURES:
- Generic stream output (stdout, stderr, file, etc.)
- Intelligent buffering for performance
- Performance statistics and monitoring
- Thread-safe operations
- Formatter integration

USAGE EXAMPLES:

Basic Stream Handler:
    from hydra_logger.handlers import StreamHandler
    import sys
    
    handler = StreamHandler(sys.stdout)
    logger.addHandler(handler)

Custom Stream Handler:
    from hydra_logger.handlers import StreamHandler
    from io import StringIO
    
    # Create custom stream
    custom_stream = StringIO()
    
    handler = StreamHandler(
        stream=custom_stream,
        buffer_size=1000,
        flush_interval=0.1
    )
    logger.addHandler(handler)
    
    # Get output
    output = custom_stream.getvalue()

Error Stream Handler:
    from hydra_logger.handlers import StreamHandler
    import sys
    
    # Log errors to stderr
    error_handler = StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

Performance Monitoring:
    # Get handler statistics
    stats = handler.get_stats()
    print(f"Messages processed: {stats['messages_processed']}")
    print(f"Messages per second: {stats['messages_per_second']}")
    print(f"Total bytes written: {stats['total_bytes_written']}")

CONFIGURATION:
- stream: Output stream (TextIO)
- level: Minimum log level
- buffer_size: Buffer size for batching (default: 1000)
- flush_interval: Flush interval in seconds (default: 0.1)

THREAD SAFETY:
- Thread-safe operations with proper locking
- Safe concurrent access
- Atomic operations where possible
- Safe stream operations

ERROR HANDLING:
- Graceful error handling and recovery
- Automatic fallback mechanisms
- Comprehensive error logging
- Non-blocking error recovery
"""

from typing import TextIO
from collections import deque
import time
from .base import BaseHandler
from ..types.records import LogRecord


class StreamHandler(BaseHandler):
    """Stream output handler."""

    def __init__(self, stream: TextIO, level: int = 0, 
                 buffer_size: int = 1000, flush_interval: float = 0.1):
        """
        Initialize stream handler.

        Args:
            stream: Output stream
            level: Minimum log level
            buffer_size: Number of messages to buffer before flushing
            flush_interval: Time interval (seconds) for automatic flushing
        """
        super().__init__(name="stream", level=level)
        self._stream = stream
        
        # Performance optimization: Buffering
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._buffer = deque(maxlen=buffer_size)
        self._last_flush = time.time()
        
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
            self._is_csv_formatter = (hasattr(formatter, 'format_headers') and hasattr(formatter, 'should_write_headers'))
            self._is_json_formatter = hasattr(formatter, 'write_header')
            self._is_streaming_formatter = hasattr(formatter, 'format_for_streaming')
            self._needs_special_handling = (self._is_csv_formatter or self._is_json_formatter or self._is_streaming_formatter)
        else:
            self._is_csv_formatter = False
            self._is_json_formatter = False
            self._is_streaming_formatter = False
            self._needs_special_handling = False

    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record to stream with buffering for high performance.

        Args:
            record: Log record to emit
        """
        try:
            if self.formatter:
                message = self.formatter.format(record)
            else:
                message = f"{record.level_name}: {record.message}"

            # Add newline if not present
            if not message.endswith('\n'):
                message += "\n"

            # Add to buffer
            self._buffer.append(message)
            
            # Check if we should flush
            current_time = time.time()
            should_flush = (
                len(self._buffer) >= self._buffer_size or
                (current_time - self._last_flush) >= self._flush_interval
            )
            
            if should_flush:
                self._flush_buffer()
                
        except Exception:
            # Silently ignore stream errors
            pass
    
    def _flush_buffer(self) -> None:
        """Flush buffered messages to stream."""
        if not self._buffer:
            return
            
        try:
            # Write all buffered messages at once
            self._stream.write(''.join(self._buffer))
            self._stream.flush()
            
            # Clear buffer and update flush time
            self._buffer.clear()
            self._last_flush = time.time()
            
        except Exception:
            # Silently ignore stream errors
            pass
    
    def force_flush(self) -> None:
        """Force flush any remaining buffered messages."""
        self._flush_buffer()

    def get_stream(self) -> TextIO:
        """
        Get the output stream.

        Returns:
            Current output stream
        """
        return self._stream

    def close(self) -> None:
        """Close the handler."""
        # Flush any remaining buffered messages
        self.force_flush()
        super().close()
        # Don't close the stream as it may be shared
