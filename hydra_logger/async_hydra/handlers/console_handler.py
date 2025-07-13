"""
Professional AsyncConsoleHandler for async console output.

This module provides world-class async console logging with:
- Async console output with performance optimization
- Bounded queue with backpressure
- Memory monitoring and safe operation
- Safe shutdown with data integrity
- Comprehensive error handling and sync fallback
- Optional color support for enhanced readability
"""

import asyncio
import logging
import sys
import time
from typing import Optional, Dict, Any, TextIO

try:
    import colorama
    from colorama import Fore, Back, Style
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

from .base_handler import BaseAsyncHandler
from ..core.coroutine_manager import CoroutineManager
from ..core.bounded_queue import BoundedAsyncQueue, QueuePolicy
from ..core.memory_monitor import MemoryMonitor
from ..core.shutdown_manager import HandlerShutdownManager
from ..core.error_tracker import AsyncErrorTracker
from ..core.health_monitor import AsyncHealthMonitor


class AsyncConsoleHandler(BaseAsyncHandler):
    """
    Professional async console handler with world-class reliability.
    
    Features:
    - Async console output with performance optimization
    - Bounded queue with configurable backpressure
    - Memory monitoring integration
    - Safe shutdown with pending message handling
    - Professional error handling and sync fallback
    - Optional color support for enhanced readability
    """
    
    def __init__(self, stream: Optional[TextIO] = None, 
                 max_queue_size: int = 1000,
                 memory_threshold: float = 70.0,
                 use_colors: bool = True,
                 **kwargs):
        """
        Initialize AsyncConsoleHandler.
        
        Args:
            stream: Output stream (defaults to sys.stderr)
            max_queue_size: Maximum queue size for buffering
            memory_threshold: Memory usage threshold percentage
            use_colors: Whether to use color output
            **kwargs: Additional handler configuration
        """
        super().__init__()
        
        self.stream = stream or sys.stderr
        self._queue = BoundedAsyncQueue(maxsize=max_queue_size)
        self._memory_monitor = MemoryMonitor(max_percent=memory_threshold)
        self._shutdown_manager = HandlerShutdownManager(self)
        self._health_monitor = AsyncHealthMonitor(self)
        
        # Color support
        self._use_colors = use_colors and COLORAMA_AVAILABLE
        if self._use_colors:
            colorama.init()
        
        # Console handling
        self._writer_task = None
        self._running = False
        
        # Statistics
        self._dropped_messages = 0
        self._sync_fallbacks = 0
        self._color_usage = 0
        self._start_time = time.time()
    
    async def emit_async(self, record: logging.LogRecord) -> None:
        """
        Professional async emit with memory monitoring and fallback.
        
        Args:
            record: Log record to emit
        """
        try:
            # Check memory health first
            if not self._memory_monitor.check_memory():
                self._sync_fallbacks += 1
                return self._write_record_sync(record)
            
            # Format the record
            msg = self.format(record) + '\n'
            
            # Add color if enabled
            if self._use_colors:
                msg = self._add_color(msg, record.levelno)
                self._color_usage += 1
            
            # Put in queue with backpressure handling
            try:
                await self._queue.put(msg)
                
                # Start writer task if not running
                if self._writer_task is None and self._running:
                    # Use CoroutineManager to track the writer task properly
                    self._writer_task = self._coroutine_manager.track(self._writer())
                    
            except Exception as e:
                # Queue full or other error, fallback to sync
                self._sync_fallbacks += 1
                await self._error_tracker.record_error("queue_put", e)
                return self._write_record_sync(record)
                
        except Exception as e:
            # Any error, fallback to sync
            self._sync_fallbacks += 1
            await self._error_tracker.record_error("emit_async", e)
            return self._write_record_sync(record)
    
    async def _emit_async_internal(self, record: logging.LogRecord) -> None:
        """
        Internal async emit implementation.
        
        Args:
            record: Log record to emit
        """
        # This is called by the base handler's emit_async
        # We override emit_async directly for better control
        pass
    
    def _add_color(self, msg: str, level: int) -> str:
        """
        Add color to message based on log level.
        
        Args:
            msg: Message to colorize
            level: Log level
            
        Returns:
            str: Colorized message
        """
        if not self._use_colors:
            return msg
        
        try:
            if level >= logging.CRITICAL:
                return f"{Fore.RED}{Style.BRIGHT}{msg}{Style.RESET_ALL}"
            elif level >= logging.ERROR:
                return f"{Fore.RED}{msg}{Style.RESET_ALL}"
            elif level >= logging.WARNING:
                return f"{Fore.YELLOW}{msg}{Style.RESET_ALL}"
            elif level >= logging.INFO:
                return f"{Fore.GREEN}{msg}{Style.RESET_ALL}"
            else:  # DEBUG
                return f"{Fore.CYAN}{msg}{Style.RESET_ALL}"
        except Exception:
            # If colorama fails, return original message
            return msg
    
    async def _writer(self) -> None:
        """
        Professional background writer task.
        
        Continuously reads from queue and writes to console.
        """
        while self._running and not self._shutdown_manager.is_shutdown_requested():
            try:
                # Get message from queue with timeout - ensure it's always awaited
                try:
                    msg = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Timeout is expected, continue
                    continue
                except asyncio.CancelledError:
                    # Task cancelled, break
                    break
                
                if msg is None:
                    # Timeout, continue
                    continue
                
                # Write to console
                await self._write_to_console(msg)
                
            except asyncio.CancelledError:
                # Task cancelled, break
                break
            except Exception as e:
                try:
                    await self._error_tracker.record_error("writer", e)
                except Exception:
                    # If error tracking fails, just continue
                    pass
                # Continue processing other messages
                continue
    
    async def _write_to_console(self, msg: str) -> None:
        """
        Write message to console asynchronously.
        
        Args:
            msg: Message to write
        """
        try:
            # Use asyncio to write to stream in a non-blocking way
            await asyncio.get_event_loop().run_in_executor(
                None, self._write_sync, msg
            )
        except Exception as e:
            try:
                await self._error_tracker.record_error("console_write", e)
            except Exception:
                # If error tracking fails, just continue
                pass
    
    def _write_sync(self, msg: str) -> None:
        """
        Synchronous write to console.
        
        Args:
            msg: Message to write
        """
        try:
            self.stream.write(msg)
            self.stream.flush()
        except Exception as e:
            # Fallback to stderr if stream fails
            try:
                sys.stderr.write(msg)
                sys.stderr.flush()
            except Exception:
                pass
    
    def _write_record_sync(self, record: logging.LogRecord) -> None:
        """
        Synchronous fallback for writing records.
        
        Args:
            record: Log record to write
        """
        try:
            msg = self.format(record) + '\n'
            
            # Add color if enabled
            if self._use_colors:
                msg = self._add_color(msg, record.levelno)
            
            # Write directly to console
            self._write_sync(msg)
                
        except Exception as e:
            # Log error but don't raise to avoid breaking the application
            self._error_tracker.record_error_sync("sync_console_write", e)
    
    async def initialize(self) -> None:
        """Initialize the handler."""
        await super().initialize()
        
        # Start writer task
        self._running = True
        self._writer_task = self._coroutine_manager.track(self._writer())
    
    async def aclose(self) -> None:
        """Professional async close with data integrity."""
        self._running = False
        
        # Cancel writer task if it exists and wait for it to complete
        if hasattr(self, '_writer_task') and self._writer_task and not self._writer_task.done():
            self._writer_task.cancel()
            try:
                await asyncio.wait_for(self._writer_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                # Task was cancelled or timed out, which is expected
                pass
            except Exception:
                # Handle any other exceptions during task cleanup
                pass
            finally:
                # Ensure task is marked as done and properly cleaned up
                if not self._writer_task.done():
                    try:
                        self._writer_task.set_exception(asyncio.CancelledError())
                    except Exception:
                        pass
                # Clear the task reference to prevent memory leaks
                self._writer_task = None
        
        # Shutdown with pending message handling
        try:
            await self._shutdown_manager.shutdown()
        except Exception:
            # Handle shutdown errors gracefully
            pass
        
        # Close base handler
        try:
            await super().aclose()
        except Exception:
            # Handle base handler close errors gracefully
            pass
    
    def close(self) -> None:
        """Sync close (best effort)."""
        self._running = False
        
        # Force sync shutdown
        self._shutdown_manager.force_sync_shutdown()
        
        super().close()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        base_status = super().get_health_status()
        
        # Add console-specific metrics
        console_stats = {
            'stream_name': self.stream.name if hasattr(self.stream, 'name') else str(self.stream),
            'use_colors': self._use_colors,
            'colorama_available': COLORAMA_AVAILABLE,
            'queue_stats': self._queue.get_stats(),
            'memory_stats': self._memory_monitor.get_memory_stats(),
            'dropped_messages': self._dropped_messages,
            'sync_fallbacks': self._sync_fallbacks,
            'color_usage': self._color_usage,
            'writer_running': self._running,
            'uptime': time.time() - self._start_time
        }
        
        base_status.update(console_stats)
        return base_status
    
    def is_healthy(self) -> bool:
        """Check if handler is healthy."""
        if not super().is_healthy():
            return False
        
        # Check if stream is writable
        try:
            self.stream.write("")
            self.stream.flush()
            return True
        except Exception:
            return False
    
    def set_use_colors(self, use_colors: bool) -> None:
        """Enable or disable color output."""
        self._use_colors = use_colors and COLORAMA_AVAILABLE
    
    def set_stream(self, stream: TextIO) -> None:
        """Set output stream."""
        self.stream = stream
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self._running = False
            # Clear task reference to prevent coroutine warnings
            if hasattr(self, '_writer_task') and self._writer_task:
                self._writer_task = None
        except Exception:
            pass 