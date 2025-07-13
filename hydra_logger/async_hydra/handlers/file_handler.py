"""
Professional AsyncFileHandler for true async file logging.

This module provides world-class async file logging with:
- True async file I/O using aiofiles
- Bounded queue with backpressure
- Memory monitoring and safe operation
- Safe shutdown with data integrity
- Comprehensive error handling and sync fallback
"""

import asyncio
import logging
import os
import time
from typing import Optional, Dict, Any

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

from .base_handler import BaseAsyncHandler
from ..core.coroutine_manager import CoroutineManager
from ..core.bounded_queue import BoundedAsyncQueue, QueuePolicy
from ..core.memory_monitor import MemoryMonitor
from ..core.shutdown_manager import HandlerShutdownManager
from ..core.error_tracker import AsyncErrorTracker
from ..core.health_monitor import AsyncHealthMonitor


class AsyncFileHandler(BaseAsyncHandler):
    """
    Professional async file handler with world-class reliability.
    
    Features:
    - True async file I/O with aiofiles
    - Bounded queue with configurable backpressure
    - Memory monitoring integration
    - Safe shutdown with pending message handling
    - Professional error handling and sync fallback
    """
    
    def __init__(self, filename: str, max_queue_size: int = 1000, 
                 memory_threshold: float = 70.0, **kwargs):
        """
        Initialize AsyncFileHandler.
        
        Args:
            filename: File path for logging
            max_queue_size: Maximum queue size for buffering
            memory_threshold: Memory usage threshold percentage
            **kwargs: Additional handler configuration
        """
        super().__init__()
        
        self.filename = filename
        self._queue = BoundedAsyncQueue(maxsize=max_queue_size)
        self._memory_monitor = MemoryMonitor(max_percent=memory_threshold)
        self._shutdown_manager = HandlerShutdownManager(self)
        self._health_monitor = AsyncHealthMonitor(self)
        
        # File handling
        self._sync_file_handle = None
        self._writer_task = None
        self._running = False
        
        # Statistics
        self._dropped_messages = 0
        self._sync_fallbacks = 0
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
            
            # Ensure running and writer task started
            if not self._running:
                self._running = True
            if self._writer_task is None:
                # Use CoroutineManager to track the writer task properly
                self._writer_task = self._coroutine_manager.track(self._writer())
            
            # Put in queue with backpressure handling
            try:
                await self._queue.put(msg)
                
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
    
    async def _writer(self) -> None:
        """
        Professional background writer task.
        
        Continuously reads from queue and writes to file using aiofiles.
        """
        if not AIOFILES_AVAILABLE:
            # Fallback to sync writing if aiofiles not available
            await self._writer_sync()
            return
        
        try:
            async with aiofiles.open(self.filename, 'a', encoding='utf-8') as f:
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
                        
                        # Write to file
                        await f.write(msg)
                        await f.flush()
                        
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
                        
        except Exception as e:
            try:
                await self._error_tracker.record_error("writer_setup", e)
            except Exception:
                # If error tracking fails, just continue
                pass
            # Fallback to sync writer
            await self._writer_sync()
    
    async def _writer_sync(self) -> None:
        """
        Sync fallback writer for when aiofiles is not available.
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
                    continue
                
                # Write synchronously
                with open(self.filename, 'a', encoding='utf-8') as f:
                    f.write(msg)
                    f.flush()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                try:
                    await self._error_tracker.record_error("writer_sync", e)
                except Exception:
                    # If error tracking fails, just continue
                    pass
                continue
    
    def _write_record_sync(self, record: logging.LogRecord) -> None:
        """
        Synchronous fallback for writing records.
        
        Args:
            record: Log record to write
        """
        try:
            msg = self.format(record) + '\n'
            
            # Write directly to file
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(msg)
                f.flush()
                
        except Exception as e:
            # Log error but don't raise to avoid breaking the application
            self._error_tracker.record_error_sync("sync_write", e)
    
    async def initialize(self) -> None:
        """Initialize the handler."""
        await super().initialize()
        
        # Ensure directory exists if needed
        dir_name = os.path.dirname(self.filename)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        
        # Start writer task
        self._running = True
        # Create the writer task and track it properly
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
        
        # Close sync file handle
        if self._sync_file_handle is not None:
            try:
                self._sync_file_handle.close()
            except Exception:
                pass
            self._sync_file_handle = None
        
        super().close()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        base_status = super().get_health_status()
        
        # Add file-specific metrics
        file_stats = {
            'filename': self.filename,
            'file_exists': os.path.exists(self.filename),
            'file_size': os.path.getsize(self.filename) if os.path.exists(self.filename) else 0,
            'queue_stats': self._queue.get_stats(),
            'memory_stats': self._memory_monitor.get_memory_stats(),
            'dropped_messages': self._dropped_messages,
            'sync_fallbacks': self._sync_fallbacks,
            'writer_running': self._running,
            'aiofiles_available': AIOFILES_AVAILABLE,
            'uptime': time.time() - self._start_time
        }
        
        base_status.update(file_stats)
        return base_status
    
    def is_healthy(self) -> bool:
        """Check if handler is healthy."""
        if not super().is_healthy():
            return False
        
        # Check file accessibility
        try:
            # Try to write a test message
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write("")
            return True
        except Exception:
            return False
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self._running = False
            if self._sync_file_handle is not None:
                self._sync_file_handle.close()
            # Clear task reference to prevent coroutine warnings
            if hasattr(self, '_writer_task') and self._writer_task:
                self._writer_task = None
        except Exception:
            pass 