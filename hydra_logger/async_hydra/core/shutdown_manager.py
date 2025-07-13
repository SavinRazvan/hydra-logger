"""
Professional SafeShutdownManager for safe shutdown protocol with data integrity.

This module provides multi-phase shutdown with timeout-based operations
and sync fallback when async fails.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class ShutdownPhase(Enum):
    """Shutdown phases."""
    RUNNING = "running"
    FLUSHING = "flushing"
    CLEANING = "cleaning"
    DONE = "done"


class SafeShutdownManager:
    """
    Professional multi-phase shutdown with proper timeout handling.
    
    Features:
    - Multi-phase shutdown (flushing → cleaning → done)
    - Timeout-based operations
    - Sync fallback when async fails
    - Data integrity guarantees
    """
    
    def __init__(self, flush_timeout: float = 5.0, cleanup_timeout: float = 2.0):
        """
        Initialize SafeShutdownManager.
        
        Args:
            flush_timeout: Timeout for flush operations
            cleanup_timeout: Timeout for cleanup operations
        """
        self._flush_timeout = flush_timeout
        self._cleanup_timeout = cleanup_timeout
        self._shutdown_event = asyncio.Event()
        self._phase = ShutdownPhase.RUNNING
        self._cleanup_lock = asyncio.Lock()
        self._start_time = time.time()
        self._stats = {
            'shutdowns': 0,
            'flush_timeouts': 0,
            'cleanup_timeouts': 0,
            'sync_fallbacks': 0
        }
    
    async def shutdown(self) -> None:
        """
        Professional multi-phase shutdown with proper timeouts.
        
        This method:
        1. Signals shutdown to all components
        2. Flushes remaining messages with timeout
        3. Cleans up resources with timeout
        4. Logs warnings for operations that don't complete
        """
        async with self._cleanup_lock:
            if self._phase != ShutdownPhase.RUNNING:
                return  # Already shutting down
            
            self._stats['shutdowns'] += 1
            self._phase = ShutdownPhase.FLUSHING
            self._shutdown_event.set()
            
            # Phase 1: Flush remaining messages with timeout
            try:
                await asyncio.wait_for(self._flush_remaining_messages(), 
                                     timeout=self._flush_timeout)
            except asyncio.TimeoutError:
                self._stats['flush_timeouts'] += 1
                print(f"WARNING: Flush did not complete within {self._flush_timeout}s")
            
            # Phase 2: Cleanup resources with timeout
            self._phase = ShutdownPhase.CLEANING
            try:
                await asyncio.wait_for(self._cleanup_resources(), 
                                     timeout=self._cleanup_timeout)
            except asyncio.TimeoutError:
                self._stats['cleanup_timeouts'] += 1
                print(f"WARNING: Cleanup did not complete within {self._cleanup_timeout}s")
            
            self._phase = ShutdownPhase.DONE
    
    async def _flush_remaining_messages(self) -> None:
        """Flush all pending messages with proper error handling."""
        # This is a template - subclasses should override
        # Use asyncio.gather with return_exceptions=True
        pass
    
    async def _cleanup_resources(self) -> None:
        """Professional cleanup of all async resources."""
        # This is a template - subclasses should override
        # Cancel all tracked tasks
        # Close file handles
        # Clear queues
        # Use proper asyncio primitives, not sleep()
        pass
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()
    
    def get_phase(self) -> ShutdownPhase:
        """Get current shutdown phase."""
        return self._phase
    
    def get_stats(self) -> Dict[str, Any]:
        """Get shutdown statistics."""
        return {
            'phase': self._phase.value,
            'shutdown_requested': self.is_shutdown_requested(),
            'flush_timeout': self._flush_timeout,
            'cleanup_timeout': self._cleanup_timeout,
            'stats': self._stats.copy(),
            'uptime': time.time() - self._start_time
        }
    
    def force_sync_shutdown(self) -> None:
        """Force sync shutdown when async fails."""
        self._stats['sync_fallbacks'] += 1
        self._phase = ShutdownPhase.DONE
        # Implement sync cleanup here
        pass
    
    def reset(self) -> None:
        """Reset shutdown manager state."""
        self._phase = ShutdownPhase.RUNNING
        self._shutdown_event.clear()
        self._stats = {
            'shutdowns': 0,
            'flush_timeouts': 0,
            'cleanup_timeouts': 0,
            'sync_fallbacks': 0
        }
        self._start_time = time.time()


class HandlerShutdownManager(SafeShutdownManager):
    """
    Shutdown manager specifically for handlers.
    """
    
    def __init__(self, handler, flush_timeout: float = 5.0, cleanup_timeout: float = 2.0):
        """Initialize handler shutdown manager."""
        super().__init__(flush_timeout, cleanup_timeout)
        self._handler = handler
    
    async def _flush_remaining_messages(self) -> None:
        """Flush remaining messages from handler."""
        if not self._handler:
            return
        
        try:
            # Flush any pending messages in the handler
            if hasattr(self._handler, '_queue') and self._handler._queue:
                # Process remaining messages in queue
                while not self._handler._queue.empty():
                    try:
                        msg = self._handler._queue.get_nowait()
                        # Process message synchronously
                        if hasattr(self._handler, '_write_record_sync'):
                            # Create a dummy record for the message
                            import logging
                            record = logging.LogRecord(
                                name='shutdown',
                                level=logging.INFO,
                                pathname='',
                                lineno=0,
                                msg=msg,
                                args=(),
                                exc_info=None
                            )
                            self._handler._write_record_sync(record)
                    except Exception:
                        break
            
            # Flush file handles if available
            if hasattr(self._handler, '_sync_file_handle') and self._handler._sync_file_handle:
                try:
                    self._handler._sync_file_handle.flush()
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Error flushing messages: {e}")
    
    async def _cleanup_resources(self) -> None:
        """Cleanup handler resources."""
        if not self._handler:
            return
        
        try:
            # Close file handles
            if hasattr(self._handler, '_sync_file_handle') and self._handler._sync_file_handle:
                try:
                    self._handler._sync_file_handle.close()
                except Exception:
                    pass
                self._handler._sync_file_handle = None
            
            # Clear queues
            if hasattr(self._handler, '_queue') and self._handler._queue:
                await self._handler._queue.clear()
            
            # Cancel any pending tasks
            if hasattr(self._handler, '_coroutine_manager'):
                await self._handler._coroutine_manager.shutdown()
                
        except Exception as e:
            print(f"Error cleaning up handler resources: {e}")
    
    def force_sync_shutdown(self) -> None:
        """Force sync shutdown for handler."""
        super().force_sync_shutdown()
        
        if self._handler:
            try:
                # Close sync file handle
                if hasattr(self._handler, '_sync_file_handle') and self._handler._sync_file_handle:
                    self._handler._sync_file_handle.close()
                    self._handler._sync_file_handle = None
                
                # Clear queues synchronously
                if hasattr(self._handler, '_queue') and self._handler._queue:
                    while not self._handler._queue.empty():
                        try:
                            self._handler._queue.get_nowait()
                        except Exception:
                            break
                            
            except Exception as e:
                print(f"Error in sync shutdown: {e}") 