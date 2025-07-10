"""
Async handlers for Hydra-Logger.

This module provides async-compatible logging handlers that support non-blocking I/O
operations for high-performance async applications. All handlers implement async
emit methods and support concurrent logging operations.

Key Features:
- AsyncLogHandler base class for async handler implementations
- AsyncRotatingFileHandler for non-blocking file operations
- AsyncStreamHandler for async console output
- Async queue system for buffering and batching
- Thread-safe async operations
- Performance monitoring for async operations

Example:
    >>> from hydra_logger.async_handlers import AsyncRotatingFileHandler
    >>> handler = AsyncRotatingFileHandler("app.log")
    >>> await handler.emit_async(log_record)
"""

import asyncio
import logging
import os
import sys
import time
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union, TYPE_CHECKING
from logging.handlers import RotatingFileHandler

# Import from new modular structure
from hydra_logger.core.constants import Colors, DEFAULT_COLORS

# Optional imports with fallbacks
try:
    import aiofiles  # type: ignore
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    aiofiles = None

# Type checking imports
if TYPE_CHECKING:
    if aiofiles is not None:
        from aiofiles import open as aio_open  # type: ignore


class BufferedRotatingFileHandler(RotatingFileHandler):
    """Buffered rotating file handler for improved performance."""
    
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, 
                 buffer_size=8192, flush_interval=1.0):
        # Convert parameters to proper types for RotatingFileHandler
        maxBytes = int(maxBytes) if maxBytes is not None else 0
        backupCount = int(backupCount) if backupCount is not None else 0
        super().__init__(filename, mode='a', maxBytes=maxBytes, backupCount=backupCount, encoding=encoding)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self._buffer = []
        self._last_flush = time.time()
    
    def emit(self, record):
        """Emit a record with buffering."""
        try:
            msg = self.format(record)
            self._buffer.append(msg)
            
            # Flush if buffer is full or enough time has passed
            if (len(self._buffer) >= self.buffer_size or 
                time.time() - self._last_flush >= self.flush_interval):
                self._flush_buffer()
                
        except Exception:
            self.handleError(record)
    
    def _flush_buffer(self):
        """Flush the buffer to the file."""
        if self._buffer:
            try:
                for msg in self._buffer:
                    self.stream.write(msg + '\n')
                self.stream.flush()
                self._buffer.clear()
                self._last_flush = time.time()
            except Exception:
                pass
    
    def close(self):
        """Close the handler and flush any remaining data."""
        self._flush_buffer()
        super().close()
    
    def flush(self):
        """Flush the buffer."""
        self._flush_buffer()
        super().flush()


class ColoredTextFormatter(logging.Formatter):
    """Colored text formatter for terminal output."""
    
    def __init__(self, fmt=None, datefmt=None, force_colors=None, destination_type="auto", color_mode: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.force_colors = force_colors
        self.destination_type = destination_type
        self.color_mode = color_mode or "auto"
    
    def format(self, record):
        """Format the record with colors."""
        # Get the original formatted message
        msg = super().format(record)
        
        # Add colors if appropriate
        if self._should_use_colors():
            # Colorize specific parts
            level_color = DEFAULT_COLORS.get(record.levelname, Colors.RESET)
            name_color = Colors.MAGENTA
            
            # Apply colors to levelname and name specifically
            msg = msg.replace(record.levelname, f"{level_color}{record.levelname}{Colors.RESET}")
            msg = msg.replace(record.name, f"{name_color}{record.name}{Colors.RESET}")
        
        return msg
    
    def _should_use_colors(self):
        """Determine if colors should be used."""
        # Check color_mode first
        if self.color_mode == "never":
            return False
        elif self.color_mode == "always":
            return True
        elif self.color_mode == "auto":
            # Use force_colors if set
            if self.force_colors == "never":
                return False
            elif self.force_colors == "always":
                return True
            else:
                # Auto-detect
                return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        
        # Default to auto-detect
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


class PlainTextFormatter(logging.Formatter):
    """Plain text formatter without colors."""
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
    
    def format(self, record):
        """Format the record without colors."""
        return super().format(record)


class AsyncLogHandler(logging.Handler, ABC):
    """
    Base class for async logging handlers.
    
    This abstract base class provides the foundation for async logging handlers
    that support non-blocking I/O operations. All async handlers should inherit
    from this class and implement the async emit method.
    
    Attributes:
        _lock (threading.Lock): Thread lock for thread-safe operations
        _queue (asyncio.Queue): Async queue for message buffering
        _worker_task (Optional[asyncio.Task]): Background worker task
        _running (bool): Whether the handler is running
    """
    
    def __init__(self, level: int = logging.NOTSET, queue_size: int = 1000):
        """
        Initialize async handler.
        
        Args:
            level (int): Logging level for this handler
            queue_size (int): Maximum queue size for buffering
        """
        super().__init__(level)
        self._lock = threading.Lock()
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_timeout = 30.0  # 30 seconds timeout for shutdown
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Synchronous emit method for compatibility.
        
        Args:
            record (logging.LogRecord): Log record to emit
            
        This method queues the record for async processing to maintain
        compatibility with the standard logging interface.
        """
        try:
            # Always try to queue for async processing if handler is running
            if self._running and self._loop and self._loop.is_running():
                # Schedule async emit in the event loop
                asyncio.create_task(self._queue.put(record))
            else:
                # Fallback to synchronous processing
                self._process_record_sync(record)
                
        except Exception:
            # Fallback to synchronous processing on error
            self._process_record_sync(record)
    
    async def emit_async(self, record: logging.LogRecord) -> None:
        """
        Emit a log record asynchronously.
        
        Args:
            record (logging.LogRecord): Log record to emit
        """
        try:
            if self._running:
                await self._queue.put(record)
            else:
                # Fallback to synchronous processing
                self._process_record_sync(record)
        except Exception:
            # Fallback to synchronous processing on error
            self._process_record_sync(record)
    
    @abstractmethod
    async def _process_record_async(self, record: logging.LogRecord) -> None:
        """
        Process a log record asynchronously.
        
        Args:
            record (logging.LogRecord): Log record to process
        """
        pass
    
    def _process_record_sync(self, record: logging.LogRecord) -> None:
        """
        Process a log record synchronously as fallback.
        
        Args:
            record (logging.LogRecord): Log record to process
        """
        try:
            msg = self.format(record)
            print(msg, file=sys.stderr)
        except Exception:
            self.handleError(record)
    
    async def start(self) -> None:
        """Start the async handler worker."""
        if self._running:
            return
        
        try:
            self._running = True
            self._loop = asyncio.get_running_loop()
            self._worker_task = asyncio.create_task(self._worker())
        except Exception:
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Stop the async handler worker with timeout."""
        if not self._running:
            return
        
        try:
            self._running = False
            
            # Wait for worker to stop with timeout
            if self._worker_task and not self._worker_task.done():
                try:
                    await asyncio.wait_for(self._worker_task, timeout=self._shutdown_timeout)
                except asyncio.TimeoutError:
                    # Cancel the task if it doesn't stop in time
                    self._worker_task.cancel()
                    try:
                        await self._worker_task
                    except asyncio.CancelledError:
                        pass
            
            # Process any remaining messages
            await self._process_remaining()
            
        except Exception:
            # Ensure we mark as stopped even on error
            self._running = False
    
    async def _worker(self) -> None:
        """Main worker loop with proper error handling and shutdown."""
        try:
            while self._running:
                try:
                    # Get message with timeout
                    record = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                    
                    # Process the record
                    await self._process_record_async(record)
                    
                    # Mark task as done
                    self._queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No messages available, continue
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Log error and continue
                    print(f"Error in async handler worker: {e}", file=sys.stderr)
                    await asyncio.sleep(0.1)  # Small delay before retry
                    
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            pass
        except Exception as e:
            print(f"Fatal error in async handler worker: {e}", file=sys.stderr)
        finally:
            # Ensure we process any remaining messages
            try:
                await self._process_remaining()
            except Exception:
                pass
    
    async def _process_remaining(self) -> None:
        """Process any remaining messages in the queue."""
        try:
            remaining_records = []
            
            # Get all remaining records
            while not self._queue.empty():
                try:
                    record = self._queue.get_nowait()
                    remaining_records.append(record)
                except asyncio.QueueEmpty:
                    break
            
            # Process remaining records
            for record in remaining_records:
                try:
                    await self._process_record_async(record)
                    self._queue.task_done()
                except Exception:
                    # Mark as done even on error to prevent deadlock
                    self._queue.task_done()
                    
        except Exception as e:
            print(f"Error processing remaining messages: {e}", file=sys.stderr)
    
    def close(self) -> None:
        """Close the handler synchronously."""
        try:
            self._running = False
            
            # Cancel worker task if running
            if self._worker_task and not self._worker_task.done():
                self._worker_task.cancel()
            
            super().close()
            
        except Exception:
            # Ensure we mark as stopped even on error
            self._running = False
    
    async def aclose(self) -> None:
        """Close the handler asynchronously."""
        await self.stop()


class AsyncRotatingFileHandler(AsyncLogHandler):
    """
    Async rotating file handler for non-blocking file operations.
    
    This handler provides async file operations with automatic log rotation
    and buffered writing for improved performance.
    """
    
    def __init__(self, filename: str, maxBytes: int = 0, backupCount: int = 0,
                 encoding: Optional[str] = None, buffer_size: int = 8192):
        """
        Initialize async rotating file handler.
        
        Args:
            filename: Log file path
            maxBytes: Maximum file size before rotation
            backupCount: Number of backup files to keep
            encoding: File encoding
            buffer_size: Buffer size for writing
        """
        super().__init__()
        self.filename = filename
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self.encoding = encoding or 'utf-8'
        self.buffer_size = buffer_size
        self._file = None
        self._buffer = []
        self._last_flush = time.time()
        self._flush_interval = 1.0
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    async def _process_record_async(self, record: logging.LogRecord) -> None:
        """Process a log record asynchronously."""
        try:
            msg = self.format(record) + '\n'
            data = msg.encode(self.encoding)
            
            # Add to buffer
            self._buffer.append(data)
            
            # Flush if buffer is full or enough time has passed
            if (len(self._buffer) >= self.buffer_size or 
                time.time() - self._last_flush >= self._flush_interval):
                await self._flush_buffer()
                
        except Exception as e:
            print(f"Error processing log record: {e}", file=sys.stderr)
    
    async def _write_to_file(self, data: bytes) -> None:
        """Write data to file asynchronously."""
        try:
            if AIOFILES_AVAILABLE and aiofiles is not None:
                # Use aiofiles for async file operations
                async with aiofiles.open(self.filename, mode='ab') as f:
                    await f.write(data)
            else:
                # Fallback to synchronous file operations
                with open(self.filename, 'ab') as f:
                    f.write(data)
                    
        except Exception as e:
            print(f"Error writing to file: {e}", file=sys.stderr)
    
    async def _rotate_file(self) -> None:
        """Rotate the log file if needed."""
        try:
            if self.maxBytes <= 0:
                return
            
            # Check file size
            if os.path.exists(self.filename):
                size = os.path.getsize(self.filename)
                if size < self.maxBytes:
                    return
            
            # Perform rotation
            for i in range(self.backupCount - 1, 0, -1):
                src = f"{self.filename}.{i}"
                dst = f"{self.filename}.{i + 1}"
                if os.path.exists(src):
                    if os.path.exists(dst):
                        os.remove(dst)
                    os.rename(src, dst)
            
            # Rotate current file
            if os.path.exists(self.filename):
                if self.backupCount > 0:
                    dst = f"{self.filename}.1"
                    if os.path.exists(dst):
                        os.remove(dst)
                    os.rename(self.filename, dst)
            
        except Exception as e:
            print(f"Error rotating file: {e}", file=sys.stderr)
    
    async def _flush_buffer(self) -> None:
        """Flush the buffer to the file."""
        if not self._buffer:
            return
        
        try:
            # Check if rotation is needed
            await self._rotate_file()
            
            # Write all buffered data
            for data in self._buffer:
                await self._write_to_file(data)
            
            # Clear buffer
            self._buffer.clear()
            self._last_flush = time.time()
            
        except Exception as e:
            print(f"Error flushing buffer: {e}", file=sys.stderr)
    
    def close(self) -> None:
        """Close the handler and flush any remaining data."""
        try:
            # Flush buffer synchronously
            if self._buffer:
                try:
                    with open(self.filename, 'ab') as f:
                        for data in self._buffer:
                            f.write(data)
                except Exception:
                    pass
                self._buffer.clear()
            
            super().close()
            
        except Exception:
            pass
    
    async def aclose(self) -> None:
        """Close the handler asynchronously."""
        try:
            # Flush buffer asynchronously
            if self._buffer:
                await self._flush_buffer()
            
            await super().aclose()
            
        except Exception:
            pass


class AsyncStreamHandler(AsyncLogHandler):
    """
    Async stream handler for console output.
    
    This handler provides async console output with buffering for improved
    performance in high-throughput scenarios.
    """
    
    def __init__(self, stream: Optional[Any] = None, use_colors: bool = True,
                 buffer_size: int = 1024):
        """
        Initialize async stream handler.
        
        Args:
            stream: Output stream (defaults to sys.stdout)
            use_colors: Whether to use colored output
            buffer_size: Buffer size for writing
        """
        super().__init__()
        self.stream = stream or sys.stdout
        self.use_colors = use_colors
        self.buffer_size = buffer_size
        self._buffer = []
        self._last_flush = time.time()
        self._flush_interval = 0.1  # More frequent flushing for console
    
    async def _process_record_async(self, record: logging.LogRecord) -> None:
        """Process a log record asynchronously."""
        try:
            msg = self.format(record) + '\n'
            
            # Add to buffer
            self._buffer.append(msg)
            
            # Flush if buffer is full or enough time has passed
            if (len(self._buffer) >= self.buffer_size or 
                time.time() - self._last_flush >= self._flush_interval):
                await self._flush_buffer()
                
        except Exception as e:
            print(f"Error processing log record: {e}", file=sys.stderr)
    
    async def _flush_buffer(self) -> None:
        """Flush the buffer to the stream."""
        if not self._buffer:
            return
        
        try:
            # Write all buffered messages
            for msg in self._buffer:
                self.stream.write(msg)
            
            # Flush the stream
            self.stream.flush()
            
            # Clear buffer
            self._buffer.clear()
            self._last_flush = time.time()
            
        except Exception as e:
            print(f"Error flushing buffer: {e}", file=sys.stderr)
    
    async def stop(self) -> None:
        """Stop the handler and flush any remaining data."""
        try:
            await self._flush_buffer()
            await super().stop()
            
        except Exception:
            pass
    
    async def aclose(self) -> None:
        """Close the handler asynchronously."""
        try:
            await self._flush_buffer()
            await super().aclose()
            
        except Exception:
            pass


class AsyncBufferedRotatingFileHandler(AsyncRotatingFileHandler):
    """
    Async buffered rotating file handler with enhanced buffering.
    
    This handler provides enhanced buffering capabilities for high-throughput
    logging scenarios with automatic rotation.
    """
    
    def __init__(self, filename: str, maxBytes: int = 0, backupCount: int = 0,
                 encoding: Optional[str] = None, buffer_size: int = 8192,
                 flush_interval: float = 1.0):
        """
        Initialize async buffered rotating file handler.
        
        Args:
            filename: Log file path
            maxBytes: Maximum file size before rotation
            backupCount: Number of backup files to keep
            encoding: File encoding
            buffer_size: Buffer size for writing
            flush_interval: Flush interval in seconds
        """
        super().__init__(filename, maxBytes, backupCount, encoding, buffer_size)
        self.flush_interval = flush_interval
        self._flush_interval = flush_interval
    
    async def _process_record_async(self, record: logging.LogRecord) -> None:
        """Process a log record asynchronously with enhanced buffering."""
        try:
            msg = self.format(record) + '\n'
            data = msg.encode(self.encoding)
            
            # Add to buffer
            self._buffer.append(data)
            
            # Flush if buffer is full or enough time has passed
            if (len(self._buffer) >= self.buffer_size or 
                time.time() - self._last_flush >= self._flush_interval):
                await self._flush_buffer()
                
        except Exception as e:
            print(f"Error processing log record: {e}", file=sys.stderr)
    
    async def _flush_buffer(self) -> None:
        """Flush the buffer to the file with enhanced error handling."""
        if not self._buffer:
            return
        
        try:
            # Check if rotation is needed
            await self._rotate_file()
            
            # Write all buffered data in a single operation if possible
            if AIOFILES_AVAILABLE and aiofiles is not None:
                async with aiofiles.open(self.filename, mode='ab') as f:
                    for data in self._buffer:
                        await f.write(data)
            else:
                # Fallback to synchronous file operations
                with open(self.filename, 'ab') as f:
                    for data in self._buffer:
                        f.write(data)
            
            # Clear buffer
            self._buffer.clear()
            self._last_flush = time.time()
            
        except Exception as e:
            print(f"Error flushing buffer: {e}", file=sys.stderr)
    
    async def stop(self) -> None:
        """Stop the handler and flush any remaining data."""
        try:
            await self._flush_buffer()
            await super().stop()
            
        except Exception:
            pass
    
    async def aclose(self) -> None:
        """Close the handler asynchronously."""
        try:
            await self._flush_buffer()
            await super().aclose()
            
        except Exception:
            pass 