"""
Base async handler for Hydra-Logger.

This module provides the base class for all async handlers with
common functionality, error handling, and fallback mechanisms.
"""

import asyncio
import logging
import sys
from typing import Optional, Any, Dict
from abc import ABC, abstractmethod

from ..core.coroutine_manager import CoroutineManager
from ..core.event_loop_manager import EventLoopManager
from ..core.error_tracker import AsyncErrorTracker


class BaseAsyncHandler(logging.Handler, ABC):
    """
    Base class for all async handlers.
    
    Features:
    - Common async handler functionality
    - Error handling and fallback
    - Coroutine management integration
    - Professional async patterns
    """
    
    def __init__(self):
        """Initialize base async handler."""
        super().__init__()
        self._coroutine_manager = CoroutineManager()
        self._error_tracker = AsyncErrorTracker()
        self._health_monitor = None  # Will be set by subclasses
        self._initialized = False
        self._shutdown_requested = False
    
    async def emit_async(self, record: logging.LogRecord) -> None:
        """
        Professional async emit with proper error handling.
        
        Args:
            record: Log record to emit
        """
        try:
            if self._shutdown_requested:
                # Handler is shutting down, use sync fallback
                return self._write_record_sync(record)
            
            return await EventLoopManager.safe_async_operation(
                lambda: self._coroutine_manager.track(self._emit_async_internal(record)),
                lambda: self._write_record_sync(record)
            )
        except Exception as e:
            await self._error_tracker.record_error("emit_async", e)
            return self._write_record_sync(record)
    
    @abstractmethod
    async def _emit_async_internal(self, record: logging.LogRecord) -> None:
        """
        Internal async emit implementation.
        
        Args:
            record: Log record to emit
        """
        pass
    
    def _write_record_sync(self, record: logging.LogRecord) -> None:
        """
        Sync fallback for writing records.
        
        Args:
            record: Log record to write
        """
        try:
            msg = self.format(record) + '\n'
            # Default sync implementation - subclasses can override
            print(msg, end='', file=sys.stderr)
        except Exception as e:
            # Use synchronous error handling to avoid coroutine warnings
            try:
                self.handleError(record)
            except Exception as error_e:
                print(f"Error in sync fallback: {error_e}", file=sys.stderr)
    
    async def aclose(self) -> None:
        """Professional async close."""
        self._shutdown_requested = True
        await self._coroutine_manager.shutdown()
        await self._error_tracker.shutdown()
        self._initialized = False
    
    def close(self) -> None:
        """Sync close (best effort)."""
        self._shutdown_requested = True
        # Don't call async methods in sync close
        if hasattr(self, '_sync_file_handle') and self._sync_file_handle is not None:
            try:
                self._sync_file_handle.close()
            except Exception:
                pass
            self._sync_file_handle = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Sync emit for compatibility.
        
        Args:
            record: Log record to emit
        """
        try:
            if EventLoopManager.has_running_loop():
                # We're in async context, create task
                asyncio.create_task(self.emit_async(record))
            else:
                # No event loop, use sync fallback
                self._write_record_sync(record)
        except Exception as e:
            # Always fallback to sync on any error
            self._write_record_sync(record)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return self._error_tracker.get_error_stats()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status."""
        if self._health_monitor:
            return self._health_monitor.get_health_status()
        else:
            return {
                'handler_type': self.__class__.__name__,
                'initialized': self._initialized,
                'shutdown_requested': self._shutdown_requested,
                'coroutine_stats': self._coroutine_manager.get_stats()
            }
    
    def is_healthy(self) -> bool:
        """Check if handler is healthy."""
        health_status = self.get_health_status()
        return (
            self._initialized and 
            not self._shutdown_requested and
            health_status.get('error_count', 0) < 10
        )
    
    async def initialize(self) -> None:
        """Initialize handler."""
        if self._initialized:
            return
        self._initialized = True
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self._shutdown_requested = True
            # Don't call async methods in destructor
            if hasattr(self, '_sync_file_handle') and self._sync_file_handle is not None:
                try:
                    self._sync_file_handle.close()
                except Exception:
                    pass
                self._sync_file_handle = None
        except Exception:
            pass 