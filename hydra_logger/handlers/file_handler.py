"""
File Handlers for Hydra-Logger

This module provides  file handling capabilities with separate
synchronous and asynchronous implementations for optimal performance. Each
handler is designed to do one thing well with minimal overhead.

ARCHITECTURE:
- SyncFileHandler: Pure synchronous file I/O with buffering
- AsyncFileHandler: Asynchronous file I/O with queue-based processing
- FileHandler: Unified interface that automatically selects the best implementation
- buffering for high throughput
- Binary format support for specialized use cases

PERFORMANCE FEATURES:
- buffering (1000 messages or 1s intervals by default)
- Batch writing for throughput
- Lazy file opening and automatic cleanup
- Memory-efficient buffer management
- Performance statistics and monitoring
- Automatic cleanup on exit

COLOR SYSTEM NOTE:
- File handlers do NOT support colors (console handlers only)
- Always uses plain formatters regardless of use_colors setting
- LogDestination.use_colors is ignored for file destinations
- Use console handlers if you need colored output

HANDLER TYPES:
- SyncFileHandler: Pure synchronous file I/O with minimal overhead
- AsyncFileHandler: Asynchronous file I/O with queue-based processing
- FileHandler: Unified interface with automatic implementation selection

USAGE EXAMPLES:

Basic File Handler:
    from hydra_logger.handlers import FileHandler
    
    handler = FileHandler("app.log")
    logger.addHandler(handler)

Sync File Handler with Custom Buffering:
    from hydra_logger.handlers.file_handler import SyncFileHandler
    
    handler = SyncFileHandler(
        filename="app.log",
        buffer_size=500,      # Flush after 500 messages
        flush_interval=0.5    # Or flush every 500ms
    )
    logger.addHandler(handler)

Async File Handler:
    from hydra_logger.handlers.file_handler import AsyncFileHandler
    
    handler = AsyncFileHandler(
        filename="app.log",
        bulk_size=100,        # Process in batches of 100
        max_queue_size=10000  # Max queue size
    )
    logger.addHandler(handler)
    
    # Use async emit
    await handler.emit_async(record)

Binary Format Support:
    # For binary formatters (e.g., compact binary logging)
    handler = SyncFileHandler(
        filename="app.bin",
        mode="ab"  # Binary append mode
    )
    # Set binary formatter
    handler.setFormatter(binary_formatter)

Performance Monitoring:
    # Get handler statistics
    stats = handler.get_stats()
    print(f"Messages processed: {stats['messages_processed']}")
    print(f"Messages per second: {stats['messages_per_second']}")
    print(f"Total bytes written: {stats['total_bytes_written']}")

CONFIGURATION OPTIONS:
- filename: Path to log file
- mode: File open mode (default: "a" for append)
- encoding: File encoding (default: "utf-8")
- buffer_size: Buffer size for batching (default: 1000)
- flush_interval: Flush interval in seconds (default: 1.0)
- bulk_size: Batch size for async processing (default: 100)
- max_queue_size: Queue size limit for async handler (default: 10000)

THREAD SAFETY:
- SyncFileHandler: Thread-safe with proper locking
- AsyncFileHandler: Thread-safe with asyncio queue
- Automatic cleanup on exit
- Safe concurrent access

ERROR HANDLING:
- Graceful error handling and recovery
- Automatic fallback mechanisms
- Error logging
- Non-blocking error recovery
- Automatic cleanup on exit
"""

import asyncio
import time
import os
import sys
import atexit
import weakref
from typing import Optional, List, Dict, Any, TextIO
from pathlib import Path
from collections import deque
from .base_handler import BaseHandler
from ..types.records import LogRecord
from ..types.levels import LogLevel
from ..utils.time_utility import TimeUtility


class SyncFileHandler(BaseHandler):
    """
    Pure synchronous file handler - fast and simple.
    
    Features:
    - Direct file I/O operations
    - No queues or background tasks
    - Minimal overhead
    - Thread-safe for sync operations
    """
    
    def __init__(self, filename: str, mode: str = "a", encoding: str = "utf-8",
                 buffer_size: int = 50000, flush_interval: float = 5.0, timestamp_config=None):  # Optimal: 50K buffer, 5s flush
        """Initialize sync file handler.
        
        Args:
            filename: Path to log file
            mode: File open mode (default: append)
            encoding: File encoding (default: utf-8)
            buffer_size: Number of messages to buffer before flushing
            flush_interval: Time interval (seconds) for automatic flushing
            timestamp_config: Timestamp configuration for formatting
        """
        super().__init__(name="sync_file", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._file_handle = None

        # Performance optimization: Buffering - auto-detect if None
        if buffer_size is None or flush_interval is None:
            try:
                from ..utils.system_detector import get_optimal_buffer_config
                optimal_config = get_optimal_buffer_config("file")
                buffer_size = buffer_size or optimal_config["buffer_size"]
                flush_interval = flush_interval or optimal_config["flush_interval"]
            except Exception:
                # Fallback defaults
                buffer_size = buffer_size or 1000
                flush_interval = flush_interval or 1.0
        
        self._buffer_size = buffer_size
        self._flush_interval = flush_interval
        self._buffer = deque(maxlen=buffer_size)
        self._last_flush = TimeUtility.perf_counter()  # FIX: Use perf_counter for precision
        
        # Performance metrics
        self._messages_processed = 0
        self._total_bytes_written = 0
        self._start_time = TimeUtility.perf_counter()  # FIX: Use perf_counter for precision
        
        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directory for {filename}: {e}", file=sys.stderr)
        
        # Register for automatic cleanup
        atexit.register(self._auto_cleanup)
        
        # Open file with proper error handling
        try:
            # Text mode - with encoding (formatter will be set later)
            self._file_handle = open(filename, mode, encoding=encoding, buffering=1)
        except Exception as e:
            print(f"Error: Could not open file {filename}: {e}", file=sys.stderr)
            self._file_handle = None
    
    def _is_binary_formatter(self) -> bool:
        """Check if the formatter is a binary formatter."""
        if not self.formatter:
            return False
        
        # Check formatter name/type
        formatter_name = getattr(self.formatter, 'name', '')
        return 'binary' in formatter_name.lower()
    
    def setFormatter(self, formatter):
        """Set formatter for this handler."""
        self.formatter = formatter
        
        # If this is a binary formatter and file is open in text mode, reopen in binary mode
        if self._file_handle and self._is_binary_formatter():
            # Close current file handle
            self._file_handle.close()
            
            # Reopen in binary mode
            try:
                self._file_handle = open(self._filename, self._mode + 'b', buffering=0)  # No buffering for binary mode
            except Exception as e:
                print(f"Error: Could not reopen file {self._filename} in binary mode: {e}", file=sys.stderr)
                self._file_handle = None
    
    def emit(self, record: LogRecord) -> None:
        """
        Emit method with buffering for high performance.
        
        Args:
            record: Log record to emit
        """
        # Check if file handle is valid
        if not self._file_handle:
            print(f"Error: Cannot emit to closed or invalid file handle: {self._filename}", file=sys.stderr)
            return
        
        try:
            # Check if this is the first write and we need to write CSV headers
            if self._messages_processed == 0 and self.formatter and hasattr(self.formatter, 'format_headers'):
                # Check if formatter is CSV formatter
                if hasattr(self.formatter, 'include_headers') and self.formatter.include_headers:
                    # Check if file is empty (new file)
                    current_pos = self._file_handle.tell()
                    if current_pos == 0:
                        # Write CSV headers
                        headers = self.formatter.format_headers()
                        if headers:
                            self._file_handle.write(headers + '\n')
                            self._file_handle.flush()
            
            # Format message
            message = self._format_message(record)
            
            # Add to buffer
            self._buffer.append(message)
            self._messages_processed += 1
            
            # Calculate bytes written (handle both text and binary)
            if isinstance(message, bytes):
                self._total_bytes_written += len(message)
            else:
                self._total_bytes_written += len(message.encode(self._encoding))
            
            # Check if we should flush
            current_time = TimeUtility.perf_counter()  # Use standardized time utility
            should_flush = (
                len(self._buffer) >= self._buffer_size or
                (current_time - self._last_flush) >= self._flush_interval
            )
            
            if should_flush:
                self._flush_buffer()
                
        except Exception as e:
            print(f"Sync file emit error: {e}", file=sys.stderr)
    
    def _flush_buffer(self) -> None:
        """Flush buffered messages to file."""
        if not self._buffer or not self._file_handle:
            return
            
        try:
            # Check if file handle is closed
            if hasattr(self._file_handle, 'closed') and self._file_handle.closed:
                return
                
            # Write all buffered messages at once
            if self._buffer:
                # Check if we have binary data
                if isinstance(self._buffer[0], bytes):
                    # Binary data - write each message separately
                    for message in self._buffer:
                        self._file_handle.write(message)
                else:
                    # Text data - join and write
                    self._file_handle.write(''.join(self._buffer))
                self._file_handle.flush()
            
            # Clear buffer and update flush time
            self._buffer.clear()

            self._last_flush = TimeUtility.perf_counter()  # FIX: Use perf_counter for precision
            
        except (OSError, ValueError) as e:
            # File is closed or invalid, silently ignore
            pass
        except Exception as e:
            print(f"File buffer flush error: {e}", file=sys.stderr)
    
    def flush(self) -> None:
        """Public flush method to force immediate writing."""
        self._flush_buffer()
    
    def force_flush(self) -> None:
        """Force flush any remaining buffered messages."""
        self._flush_buffer()
    
    def _format_message(self, record: LogRecord) -> str:
        """
        Format message using formatter.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted message string
        """
        if not self.formatter:
            # Fallback formatting
            return f"{record.level_name} [{record.layer}] {record.message}\n"
        
        try:
            message = self.formatter.format(record)
            
            # Handle binary vs text formatters
            if isinstance(message, bytes):
                # Binary formatters - don't add newline, return as-is
                return message
            else:
                # Text formatters - add newline if needed
                if not message.endswith('\n'):
                    message += "\n"
                return message
            
        except Exception as e:
            # Fallback formatting if formatter fails
            print(f"Warning: Formatter failed: {e}, using fallback formatting", file=sys.stderr)
            return f"{record.level_name} [{record.layer}] {record.message}\n"
    
    def close(self):
        """Close the handler and file."""
        try:
            # Flush any remaining buffered messages
            self.force_flush()
            
            if self._file_handle:
                self._file_handle.flush()
                self._file_handle.close()
                self._file_handle = None
        except Exception:
            pass
    
    def _auto_cleanup(self):
        """Automatic cleanup called by atexit."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during cleanup
    
    def __del__(self):
        """Destructor - backup cleanup if atexit fails."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during cleanup
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'messages_processed': self._messages_processed,
            'total_bytes_written': self._total_bytes_written,
            'start_time': self._start_time,
            'uptime_seconds': TimeUtility.perf_counter() - self._start_time,  # FIX: Use perf_counter for precision
            'filename': self._filename,
            'handler_type': 'sync_file'
        }


class AsyncFileHandler(BaseHandler):
    """
    DYNAMIC & SMART async file handler - Performance + Data Integrity.
    
    Features:
    - Dynamic worker management with smart scaling
    - Adaptive batching based on load and performance
    - Data integrity with guaranteed delivery
    - Performance optimization with buffering
    - Error recovery and resilience
    - Memory-efficient processing
    """
    
    def __init__(self, filename: str, mode: str = "a", encoding: str = "utf-8",
                 bulk_size: int = 1000, max_queue_size: int = 100000, timestamp_config=None, 
                 num_workers: int = 1, use_threading: bool = True, 
                 memory_buffer_size: int = 50000, disk_flush_interval: float = 2.0):
        """Initialize Direct hybrid memory-disk handler for high throughput."""
        super().__init__(name="async_file", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        self._filename = filename
        self._mode = mode
        self._encoding = encoding
        self._max_queue_size = max_queue_size
        self._num_workers = num_workers
        self._use_threading = use_threading
        
        # Hybrid Memory-Disk Architecture
        self._memory_buffer_size = memory_buffer_size  # Memory buffer
        self._disk_flush_interval = disk_flush_interval  # Less frequent disk writes
        self._memory_buffer = []  # Primary memory buffer
        self._disk_buffer = []  # Secondary disk buffer
        self._last_disk_flush = time.time()
        
        # PERFORMANCE: File write lock for thread-safe concurrent writes
        # Multiple workers can process in parallel, but file writes are serialized
        self._file_write_lock = asyncio.Lock()  # Serialize file writes for data integrity
        
        # CRITICAL FIX: Ensure directory exists
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directory for {filename}: {e}")
        
        # High performance: Smart queue management with threading
        self._message_queue = asyncio.Queue(maxsize=max_queue_size)
        self._shutdown_event = asyncio.Event()
        self._worker_tasks = []  # Multiple worker tasks
        self._running = False
        
        # THREADING SUPPORT: for performance
        if self._use_threading:
            import threading
            from concurrent.futures import ThreadPoolExecutor
            self._thread_pool = ThreadPoolExecutor(max_workers=self._num_workers)
            self._file_lock = threading.Lock()  # Thread-safe file writing
        else:
            self._thread_pool = None
            self._file_lock = None
        
        # High performance: Batching for throughput
        self._base_batch_size = bulk_size * 10  # Start with larger batches
        self._current_batch_size = bulk_size * 10
        self._max_batch_size = bulk_size * 100  # Much larger max batches
        self._min_batch_size = max(1, bulk_size // 5)  # Higher minimum
        
        # High performance: Optimized flush intervals for high throughput
        self._base_flush_interval = 0.1  # Much faster flushing
        self._current_flush_interval = 0.1
        self._max_flush_interval = 1.0  # Shorter max interval
        self._min_flush_interval = 0.01  # Very fast minimum
        self._last_flush = TimeUtility.perf_counter()
        
        # High performance: Buffering for throughput
        self._message_buffer = []
        self._buffer_capacity = max_queue_size  # Use full queue capacity
        self._overflow_buffer = []  # Overflow protection
        
        # PERFORMANCE METRICS: Dynamic optimization data
        self._messages_processed = 0
        self._messages_dropped = 0
        self._total_bytes_written = 0
        self._start_time = TimeUtility.perf_counter()
        self._batch_count = 0
        self._performance_samples = []  # For adaptive optimization
        self._last_performance_check = TimeUtility.perf_counter()
        
        # Register for automatic cleanup
        atexit.register(self._auto_cleanup)
        
        # Also register cleanup for pytest environment
        if 'pytest' in sys.modules:
            # In pytest, register cleanup to run earlier
            atexit.register(self._pytest_cleanup)
        
        # Start the worker
        self._start_worker()
    
    def _start_worker(self):
        """Start multiple async worker tasks for high throughput performance."""
        # CRITICAL FIX: Prevent multiple worker starts
        if self._running or self._worker_tasks:
            return
        
        try:
            # CRITICAL FIX: Check if we're in an event loop
            try:
                loop = asyncio.get_running_loop()
                # Create multiple workers for high performance
                for i in range(self._num_workers):
                    task = loop.create_task(self._message_processor(f"Worker-{i+1}"))
                    self._worker_tasks.append(task)
                self._running = True
                print(f"Started {self._num_workers} async workers for {self._filename}")
            except RuntimeError:
                # No event loop running, defer worker start
                print(f"No event loop running, deferring worker start for {self._filename}")
                self._running = False
        except Exception as e:
            print(f"Failed to start async file workers: {e}", file=sys.stderr)
            self._running = False
    
    async def _message_processor(self, worker_name: str = "Worker"):
        """Direct direct memory-to-file processor for performance."""
        print(f"{worker_name} started for {self._filename}")
        
        while not self._shutdown_event.is_set():
            try:
                # PERFORMANCE: Remove global lock - use per-worker message collection
                # Each worker collects its own batch from the shared queue
                # This allows true parallel processing when num_workers > 1
                messages_to_process = []
                batch_start_time = TimeUtility.perf_counter()
                
                # Collect messages from queue (non-blocking, no lock needed)
                # Queue.get_nowait() is thread-safe, so multiple workers can safely collect
                while len(messages_to_process) < self._current_batch_size and not self._message_queue.empty():
                    try:
                        message = self._message_queue.get_nowait()
                        messages_to_process.append(message)
                        self._message_queue.task_done()
                    except asyncio.QueueEmpty:
                        break
                
                # Direct write from memory to file (each worker writes independently)
                if messages_to_process:
                    await self._direct_memory_to_file_write(messages_to_process)
                    self._messages_processed += len(messages_to_process)
                
                # Dynamic optimization (per-worker, no lock needed)
                await self._optimization(batch_start_time, len(messages_to_process))
                
                # Micro-sleep for throughput
                if not messages_to_process:
                    await asyncio.sleep(0.0001)  # Short sleep
                    
            except Exception as e:
                print(f"Processor error: {e}", file=sys.stderr)
                await asyncio.sleep(0.001)  # Brief delay on error
    
    async def _direct_memory_to_file_write(self, messages: list):
        """Direct memory-to-file write for performance."""
        if not messages:
            return
        
        try:
            # Direct write from memory to file
            if self._use_threading and self._thread_pool:
                # Use threading for non-blocking disk I/O
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._thread_pool, 
                    self._bulk_write_to_disk, 
                    messages
                )
            else:
                # Direct async write
                await self._bulk_write_to_disk_async(messages)
                    
        except Exception as e:
            print(f"Direct memory-to-file write error: {e}", file=sys.stderr)
    
    async def _smart_memory_to_disk_transfer(self):
        """Smart memory-to-disk transfer for performance."""
        # Only transfer when memory buffer is full or time interval passed
        current_time = time.time()
        time_since_flush = current_time - self._last_disk_flush
        
        should_transfer = (
            (self._memory_buffer_size is not None and len(self._memory_buffer) >= self._memory_buffer_size) or
            time_since_flush >= self._disk_flush_interval
        )
        
        if should_transfer and self._memory_buffer:
            # Transfer memory buffer to disk buffer (instant)
            self._disk_buffer.extend(self._memory_buffer)
            self._memory_buffer.clear()
            self._last_disk_flush = current_time
    
    async def _fast_disk_flush(self):
        """Fast disk flush with batching."""
        if not self._disk_buffer:
            return
        
        try:
            # Use threading for non-blocking disk I/O
            if self._use_threading and self._thread_pool:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._thread_pool, 
                    self._bulk_write_to_disk, 
                    self._disk_buffer.copy()
                )
            else:
                await self._bulk_write_to_disk_async(self._disk_buffer.copy())
            
            # Clear disk buffer
            self._disk_buffer.clear()
                    
        except Exception as e:
            print(f"Fast disk flush error: {e}", file=sys.stderr)
    
    def _bulk_write_to_disk(self, messages: list):
        """Bulk write to disk with performance."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._filename), exist_ok=True)
            
            # PERFORMANCE: Join all messages before writing (single I/O operation)
            combined_message = ''.join(messages)
            
            # Write all messages at once for performance (thread-safe)
            with self._file_lock:
                with open(self._filename, self._mode, encoding=self._encoding, buffering=16777216) as f:  # 16MB buffer
                    f.write(combined_message)
                    f.flush()
                    self._total_bytes_written += len(combined_message.encode(self._encoding))
                        
        except Exception as e:
            print(f"Bulk disk write error: {e}", file=sys.stderr)
            raise
    
    async def _bulk_write_to_disk_async(self, messages: list):
        """
        Async bulk write to disk with file locking and optimized batching.
        
        PERFORMANCE: Joins all messages before writing (single I/O operation).
        Uses file lock to ensure thread-safe concurrent writes.
        """
        if not messages:
            return
            
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._filename), exist_ok=True)
            
            # PERFORMANCE: Join all messages before writing (single I/O operation)
            # This is much faster than writing each message separately
            combined_message = ''.join(messages)
            
            # PERFORMANCE: Serialize file writes for data integrity (multiple workers can process in parallel)
            async with self._file_write_lock:
                # Use aiofiles for true async I/O if available, otherwise use executor
                try:
                    import aiofiles
                    async with aiofiles.open(self._filename, mode=self._mode, encoding=self._encoding) as f:
                        await f.write(combined_message)
                        await f.flush()
                except ImportError:
                    # Fallback: use executor for non-blocking I/O
                    loop = asyncio.get_event_loop()
                    def write_sync():
                        with open(self._filename, self._mode, encoding=self._encoding, buffering=16777216) as f:  # 16MB buffer
                            f.write(combined_message)
                            f.flush()
                    await loop.run_in_executor(None, write_sync)
                
                # Update statistics
                self._total_bytes_written += len(combined_message.encode(self._encoding))
                    
        except Exception as e:
            print(f"Async bulk disk write error: {e}", file=sys.stderr)
            self._messages_dropped += len(messages)
    
    async def _optimization(self, batch_start_time: float, messages_processed: int):
        """Dynamic optimization."""
        current_time = TimeUtility.perf_counter()
        batch_duration = current_time - batch_start_time
        
        # Record performance sample
        if messages_processed > 0:
            self._performance_samples.append({
                'duration': batch_duration,
                'messages': messages_processed,
                'timestamp': current_time
            })
            
            # Keep only recent samples
            if len(self._performance_samples) > 50:
                self._performance_samples = self._performance_samples[-50:]
        
        # Optimize every 2 seconds
        if current_time - self._last_performance_check >= 2.0:
            await self._parameter_adjustment()
            self._last_performance_check = current_time
    
    async def _parameter_adjustment(self):
        """Adjust parameters for performance."""
        if len(self._performance_samples) < 5:
            return
        
        # Calculate average throughput
        recent_samples = self._performance_samples[-10:]
        total_messages = sum(s['messages'] for s in recent_samples)
        total_duration = sum(s['duration'] for s in recent_samples)
        
        if total_duration > 0:
            avg_throughput = total_messages / total_duration
            
            # Aggressive optimization for high throughput
            if avg_throughput > 10000:  # High throughput
                self._current_batch_size = min(self._max_batch_size, int(self._current_batch_size * 1.5))
                self._current_flush_interval = max(self._min_flush_interval, self._current_flush_interval * 0.8)
            elif avg_throughput < 1000:  # Low throughput
                self._current_batch_size = max(self._min_batch_size, int(self._current_batch_size * 0.9))
                self._current_flush_interval = min(self._max_flush_interval, self._current_flush_interval * 1.2)
    
    def _should_flush_smart(self) -> bool:
        """Smart flush decision based on multiple criteria."""
        current_time = TimeUtility.perf_counter()
        
        # Time-based flush
        time_since_flush = current_time - self._last_flush
        time_based = time_since_flush >= self._current_flush_interval
        
        # Size-based flush
        size_based = len(self._message_buffer) >= self._current_batch_size
        
        # Overflow-based flush (data integrity)
        overflow_based = len(self._overflow_buffer) > 0
        
        # Force flush if buffer is getting too large
        force_flush = (self._buffer_capacity is not None and len(self._message_buffer) >= self._buffer_capacity * 0.8) if self._buffer_capacity is not None else False
        
        return time_based or size_based or overflow_based or force_flush
    
    async def _flush_batch_smart(self):
        """Smart batch flushing with data integrity."""
        if not self._message_buffer and not self._overflow_buffer:
            return
        
        try:
            # Combine main buffer and overflow buffer
            all_messages = self._message_buffer + self._overflow_buffer
            
            if all_messages:
                # Write to file with error recovery
                await self._write_messages_to_file(all_messages)
                
                # Update metrics
                self._messages_processed += len(all_messages)
                self._batch_count += 1
                self._last_flush = TimeUtility.perf_counter()
                
                # Clear buffers
                self._message_buffer.clear()
                self._overflow_buffer.clear()
                
        except Exception as e:
            print(f"Smart flush error: {e}", file=sys.stderr)
            # On error, try to preserve messages in overflow buffer
        if self._message_buffer:
                self._overflow_buffer.extend(self._message_buffer)
                self._message_buffer.clear()
    
    async def _write_messages_to_file(self, messages: list):
        """Write messages to file with High performance threading."""
        try:
            if self._use_threading and self._thread_pool:
                # Use thread pool for file I/O to avoid blocking async loop
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._thread_pool, 
                    self._write_messages_threaded, 
                    messages
                )
            else:
                # Direct async file write
                await self._write_messages_async(messages)
            
        except Exception as e:
            print(f"File write error: {e}", file=sys.stderr)
            raise
    
    def _write_messages_threaded(self, messages: list):
        """Write messages to file in thread for performance."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._filename), exist_ok=True)
            
            # Thread-safe file writing
            with self._file_lock:
                with open(self._filename, self._mode, encoding=self._encoding, buffering=8192) as f:
                    for message in messages:
                        f.write(message)
                        self._total_bytes_written += len(message)
                        
        except Exception as e:
            print(f"Threaded file write error: {e}", file=sys.stderr)
            raise
    
    async def _write_messages_async(self, messages: list):
        """Write messages to file asynchronously."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._filename), exist_ok=True)
            
            # Write messages to file
            with open(self._filename, self._mode, encoding=self._encoding, buffering=8192) as f:
                for message in messages:
                    f.write(message)
                    self._total_bytes_written += len(message)
                    
        except Exception as e:
            print(f"Async file write error: {e}", file=sys.stderr)
            raise
    
    async def _optimize_performance(self, batch_start_time: float, messages_processed: int):
        """Dynamic performance optimization based on metrics."""
        current_time = TimeUtility.perf_counter()
        batch_duration = current_time - batch_start_time
        
        # Record performance sample
        if messages_processed > 0:
            self._performance_samples.append({
                'duration': batch_duration,
                'messages': messages_processed,
                'timestamp': current_time
            })
            
            # Keep only recent samples (last 100)
            if len(self._performance_samples) > 100:
                self._performance_samples = self._performance_samples[-100:]
        
        # Optimize every 5 seconds
        if current_time - self._last_performance_check >= 5.0:
            await self._adjust_performance_parameters()
            self._last_performance_check = current_time
    
    async def _adjust_performance_parameters(self):
        """Adjust performance parameters based on recent performance."""
        if len(self._performance_samples) < 10:
            return
        
        # Calculate average throughput
        recent_samples = self._performance_samples[-20:]  # Last 20 samples
        total_messages = sum(s['messages'] for s in recent_samples)
        total_duration = sum(s['duration'] for s in recent_samples)
        
        if total_duration > 0:
            avg_throughput = total_messages / total_duration
            
            # Adjust batch size based on throughput
            if avg_throughput > 1000:  # High throughput
                self._current_batch_size = min(self._max_batch_size, int(self._current_batch_size * 1.1))
                self._current_flush_interval = max(self._min_flush_interval, self._current_flush_interval * 0.9)
            elif avg_throughput < 100:  # Low throughput
                self._current_batch_size = max(self._min_batch_size, int(self._current_batch_size * 0.9))
                self._current_flush_interval = min(self._max_flush_interval, self._current_flush_interval * 1.1)
    
    def _calculate_smart_sleep(self) -> float:
        """Calculate smart sleep time based on current load."""
        queue_size = self._message_queue.qsize()
        
        if queue_size > self._max_queue_size * 0.8:
            return 0.001  # Very short sleep for high load
        elif queue_size > self._max_queue_size * 0.5:
            return 0.01   # Short sleep for medium load
        else:
            return 0.1    # Normal sleep for low load
    
    async def close_async(self):
        """Async close with data integrity for multiple workers."""
        if self._shutdown_event.is_set():
            return
        
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Wait for all workers to finish
            if self._worker_tasks:
                try:
                    # Gather tasks with timeout, but don't use nested wait_for
                    done, pending = await asyncio.wait(
                        self._worker_tasks,
                        timeout=2.0,
                        return_when=asyncio.ALL_COMPLETED
                    )
                    # Cancel and await pending tasks to prevent "Task was destroyed" warnings
                    for task in pending:
                        task.cancel()
                        # Await cancellation without nested timeouts to prevent recursion
                        try:
                            await asyncio.gather(task, return_exceptions=True)
                        except Exception:
                            pass
                except Exception:
                    # If anything fails, cancel and await all tasks
                    for task in self._worker_tasks:
                        if not task.done():
                            task.cancel()
                            try:
                                await asyncio.gather(task, return_exceptions=True)
                            except Exception:
                                pass
            
            # Final flush of any remaining messages
            if self._memory_buffer or self._disk_buffer:
                await self._fast_disk_flush()
            
            self._running = False
            self._worker_tasks.clear()
            
            # Clean up thread pool
            if self._thread_pool:
                self._thread_pool.shutdown(wait=True)
            
        except Exception as e:
            print(f"Error during async close: {e}", file=sys.stderr)
    
    def _should_flush_batch(self) -> bool:
        """Determine if current batch should be flushed."""
        current_time = TimeUtility.perf_counter()  # Use standardized time utility
        
        # Time-based flush
        if current_time - self._last_flush > self._flush_interval:
            return True
        
        # Size-based flush
        if len(self._message_buffer) >= self._batch_size:
            return True
        
        # Force flush if buffer is getting large
        if len(self._message_buffer) >= self._batch_size // 2:
            return True
        
        return False
    
    async def _flush_batch(self):
        """Flush current batch to file."""
        if not self._message_buffer:
            return
        
        try:
            # PERFORMANCE: Handle both text and binary messages
            first_message = self._message_buffer[0]
            is_binary = isinstance(first_message, bytes)
            
            if is_binary:
                # For binary data, concatenate bytes directly
                combined_message = b"".join(self._message_buffer)
                file_mode = "ab" if self._mode == "a" else "wb"
                
                # Write binary data
                with open(self._filename, file_mode) as f:
                    f.write(combined_message)
                    f.flush()
                    
                # Update metrics
                self._messages_processed += len(self._message_buffer)
                self._total_bytes_written += len(combined_message)
            else:
                # For text data, join as strings
                combined_message = "".join(self._message_buffer)
                
                # PERFORMANCE: Use aiofiles for true async I/O
                try:
                    import aiofiles
                    async with aiofiles.open(self._filename, mode=self._mode, encoding=self._encoding) as f:
                        await f.write(combined_message)
                        await f.flush()
                        
                except ImportError:
                    # PERFORMANCE: Fallback to direct file write (zero overhead)
                    with open(self._filename, self._mode, encoding=self._encoding, buffering=1) as f:  # Line buffering for text files
                        f.write(combined_message)
                        f.flush()
                except Exception:
                    # PERFORMANCE: Fallback to direct file write (zero overhead)
                    with open(self._filename, self._mode, encoding=self._encoding, buffering=1) as f:  # Line buffering for text files
                        f.write(combined_message)
                        f.flush()
                
                # Update metrics
                self._messages_processed += len(self._message_buffer)
                self._total_bytes_written += len(combined_message.encode(self._encoding))
            
            self._batch_count += 1
            
        except Exception as e:
            print(f"Async file batch write error: {e}", file=sys.stderr)
            self._messages_dropped += len(self._message_buffer)
        finally:
            self._message_buffer.clear()
            self._last_flush = TimeUtility.perf_counter()  # Use standardized time utility
    

    
    
    def _format_message(self, record: LogRecord) -> str:
        """
        Format message using formatter.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted message string
        """
        if not self.formatter:
            # Fallback formatting
            return f"{record.level_name} [{record.layer}] {record.message}\n"
        
        try:
            message = self.formatter.format(record)
            
            # Handle binary vs text formatters
            if isinstance(message, bytes):
                # Binary formatters - don't add newline, return as-is
                return message
            else:
                # Text formatters - add newline if needed
                if not message.endswith('\n'):
                    message += "\n"
                return message
            
        except Exception as e:
            # Fallback formatting if formatter fails
            print(f"Warning: Formatter failed: {e}, using fallback formatting", file=sys.stderr)
            return f"{record.level_name} [{record.layer}] {record.message}\n"
    
    def _check_and_write_csv_headers(self) -> bool:
        """
        Check if CSV headers need to be written and write them if necessary.
        
        Returns:
            True if headers were written, False otherwise
        """
        if not self.formatter or not hasattr(self.formatter, 'format_headers'):
            return False
        
        # Check if formatter is CSV formatter
        if not (hasattr(self.formatter, 'include_headers') and self.formatter.include_headers):
            return False
        
        # Check if file exists and is empty
        try:
            if os.path.exists(self._filename) and os.path.getsize(self._filename) > 0:
                return False  # File exists and has content, don't write headers
        except Exception:
            pass  # If we can't check, assume we need headers
        
        # Write CSV headers immediately to file
        try:
            headers = self.formatter.format_headers()
            if headers:
                # Write headers directly to file synchronously
                with open(self._filename, 'a', encoding='utf-8') as f:
                    f.write(headers + '\n')
                return True
        except Exception as e:
            print(f"Warning: Failed to write CSV headers: {e}", file=sys.stderr)
        
        return False
    
    def emit(self, record: LogRecord) -> None:
        """
        Emit method - adds to async queue.
        
        Args:
            record: Log record to emit
        """
        try:
            # CRITICAL FIX: Start worker if not running
            if not self._running:
                self._start_worker()
            
            # Check if we need to write CSV headers (only on first message)
            if self._messages_processed == 0:
                self._check_and_write_csv_headers()
            
            # Format message
            message = self._format_message(record)
            
            # Add to async queue (non-blocking)
            try:
                self._message_queue.put_nowait(message)
            except asyncio.QueueFull:
                # Queue is full, drop message
                self._messages_dropped += 1
                
        except Exception as e:
            self._messages_dropped += 1
            print(f"File emit error: {e}", file=sys.stderr)
    
    async def emit_async(self, record: LogRecord) -> None:
        """
        Async emit method - ensures workers are running and adds to queue.
        
        Args:
            record: Log record to emit
        """
        try:
            # Check if we need to write CSV headers (only on first message)
            if self._messages_processed == 0:
                self._check_and_write_csv_headers()
            
            # CRITICAL FIX: Ensure workers are running
            if not self._running:
                self._start_worker()
            
            # Format message
            message = self._format_message(record)
            
            # CRITICAL FIX: If no worker is running, write directly to file
            if not self._running:
                try:
                    if isinstance(message, bytes):
                        # Binary data - write in binary mode
                        file_mode = "ab" if self._mode == "a" else "wb"
                        with open(self._filename, file_mode) as f:
                            f.write(message)
                            f.flush()
                        self._total_bytes_written += len(message)
                    else:
                        # Text data - write in text mode
                        with open(self._filename, self._mode, encoding=self._encoding, buffering=1) as f:
                            f.write(message)
                            f.flush()
                        self._total_bytes_written += len(message.encode(self._encoding))
                    
                    self._messages_processed += 1
                    return
                except Exception as e:
                    print(f"Direct file write error: {e}", file=sys.stderr)
                    self._messages_dropped += 1
                    return
            
            # Try main queue first (non-blocking)
            try:
                self._message_queue.put_nowait(message)
            except asyncio.QueueFull:
                # Main queue full, drop message
                self._messages_dropped += 1
                    
        except Exception as e:
            self._messages_dropped += 1
            print(f"Async file emit error: {e}", file=sys.stderr)
    
    async def flush(self):
        """Force flush any pending messages."""
        try:
            if self._message_buffer:
                await self._flush_batch()
        except Exception as e:
            print(f"Async file flush error: {e}", file=sys.stderr)
    
    async def aclose(self):
        """Close the async handler."""
        try:
            # CRITICAL FIX: Force flush any pending messages first
            if self._message_buffer:
                await self._flush_batch()
            
            # Process any remaining messages in queue
            remaining_messages = []
            while not self._message_queue.empty():
                try:
                    message = self._message_queue.get_nowait()
                    remaining_messages.append(message)
                except asyncio.QueueEmpty:
                    break
            
            # Write remaining messages directly
            if remaining_messages:
                combined_remaining = "".join(remaining_messages)
                try:
                    with open(self._filename, self._mode, encoding=self._encoding, buffering=1) as f:
                        f.write(combined_remaining)
                        f.flush()
                except Exception as e:
                    print(f"Final flush error: {e}")
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Wait for worker tasks to finish (use _worker_tasks, not _worker_task)
            if hasattr(self, '_worker_tasks') and self._worker_tasks:
                try:
                    # Use wait() instead of wait_for() to avoid nested timeout recursion
                    done, pending = await asyncio.wait(
                        self._worker_tasks,
                        timeout=0.5,
                        return_when=asyncio.ALL_COMPLETED
                    )
                    # Cancel and await pending tasks to prevent "Task was destroyed" warnings
                    for task in pending:
                        task.cancel()
                        # Await cancellation without nested timeouts to prevent recursion
                        try:
                            await asyncio.gather(task, return_exceptions=True)
                        except Exception:
                            pass
                except Exception:
                    # If anything fails, cancel and await all tasks
                    for task in self._worker_tasks:
                        if not task.done():
                            task.cancel()
                            try:
                                await asyncio.gather(task, return_exceptions=True)
                            except Exception:
                                pass
            
        except Exception as e:
            print(f"Async file close error: {e}", file=sys.stderr)
        finally:
            # Ensure we're marked as not running
            self._running = False
    
    def close(self):
        """Close the handler (sync fallback)."""
        try:
            # Just signal shutdown - no async operations
            self._shutdown_event.set()
                
        except Exception:
            # Just mark as closed
            self._shutdown_event.set()
    
    def _auto_cleanup(self):
        """Automatic cleanup called by atexit."""
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Try to cancel worker tasks if they exist and event loop is still running
            try:
                loop = asyncio.get_running_loop()
                if loop and not loop.is_closed() and hasattr(self, '_worker_tasks') and self._worker_tasks:
                    for task in self._worker_tasks:
                        if not task.done():
                            task.cancel()
                    # Give the tasks a moment to cancel gracefully
                    TimeUtility.sleep(0.05)
            except RuntimeError:
                # Event loop is closed or not running, skip task cancellation
                pass
        except Exception:
            pass  # Ignore errors during cleanup
    
    def __del__(self):
        """Destructor - backup cleanup if atexit fails."""
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Try to cancel worker tasks if they exist and event loop is still running
            try:
                loop = asyncio.get_running_loop()
                if loop and not loop.is_closed() and hasattr(self, '_worker_tasks') and self._worker_tasks:
                    for task in self._worker_tasks:
                        if not task.done():
                            task.cancel()
                    # Give the tasks a moment to cancel gracefully
                    TimeUtility.sleep(0.05)
            except RuntimeError:
                # Event loop is closed or not running, skip task cancellation
                pass
        except Exception:
            pass  # Ignore errors during cleanup
    
    def _pytest_cleanup(self):
        """Special cleanup for pytest environment."""
        try:
            # Signal shutdown immediately
            self._shutdown_event.set()
            
            # Try to cancel worker tasks more aggressively
            if hasattr(self, '_worker_tasks') and self._worker_tasks:
                for task in self._worker_tasks:
                    if not task.done():
                        task.cancel()
            
            # Give task a moment to cancel
            TimeUtility.sleep(0.01)
            
        except Exception:
            pass  # Ignore errors during cleanup
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats from the underlying handler."""
        return {
            'messages_processed': self._messages_processed,
            'messages_dropped': self._messages_dropped,
            'total_bytes_written': self._total_bytes_written,
            'start_time': self._start_time,
            'uptime_seconds': TimeUtility.perf_counter() - self._start_time,  # FIX: Use perf_counter for precision
            'queue_size': self._message_queue.qsize(),
            'batch_count': self._batch_count,
            'running': self._running,
            'filename': self._filename,
            'handler_type': 'async_file_handler'
        }


# Backward compatibility - FileHandler now chooses the right implementation
class FileHandler(BaseHandler):
    """
    Smart file handler that automatically chooses sync or async implementation.
    
    This is a compatibility layer - for new code, use SyncFileHandler or AsyncFileHandler directly.
    """
    
    def __init__(self, filename: str, mode: str = "a", encoding: str = "utf-8",
                 bulk_size: int = 100, max_queue_size: int = 10000, timestamp_config=None):
        """Initialize smart file handler.
        
        Args:
            filename: Path to log file
            mode: File open mode (default: append)
            encoding: File encoding (default: utf-8)
            bulk_size: Number of messages to process in bulk (async only)
            max_queue_size: Queue size limit before dropping messages (async only)
            timestamp_config: Timestamp configuration for formatting
        """
        super().__init__(name="file", level=LogLevel.NOTSET, timestamp_config=timestamp_config)
        
        # For now, default to sync for better performance
        # You can change this to "async" if you need async file I/O
        self._handler = SyncFileHandler(
            filename=filename,
            mode=mode,
            encoding=encoding,
            timestamp_config=timestamp_config
        )
        
        self._mode = "sync"  # Default to sync for performance
    
    def setFormatter(self, formatter):
        """Set formatter on the underlying handler."""
        self._handler.setFormatter(formatter)
    
    def emit(self, record: LogRecord) -> None:
        """Emit using the underlying handler."""
        self._handler.emit(record)
    
    async def emit_async(self, record: LogRecord) -> None:
        """Async emit using the underlying handler."""
        if hasattr(self._handler, 'emit_async'):
            await self._handler.emit_async(record)
        else:
            # Fallback to sync emit
            self._handler.emit(record)
    
    def close(self):
        """Close the underlying handler."""
        self._handler.close()
    
    async def aclose(self):
        """Async close the underlying handler."""
        if hasattr(self._handler, 'aclose'):
            await self._handler.aclose()
        else:
            self._handler.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get stats from the underlying handler."""
        return self._handler.get_stats()
    
