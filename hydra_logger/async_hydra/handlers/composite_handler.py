"""
Professional AsyncCompositeHandler for multi-handler support.

This module provides multi-handler support including:
- Multiple handler management
- Parallel handler execution
- Error isolation between handlers
- Professional multi-handler patterns
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from .base_handler import BaseAsyncHandler
from ..core.coroutine_manager import CoroutineManager
from ..core.error_tracker import AsyncErrorTracker
from ..core.health_monitor import AsyncHealthMonitor


class AsyncCompositeHandler(BaseAsyncHandler):
    """
    Professional composite handler for multi-handler support.
    
    Features:
    - Multiple handler management
    - Parallel handler execution
    - Error isolation between handlers
    - Professional multi-handler patterns
    """
    
    def __init__(self, handlers: Optional[List[BaseAsyncHandler]] = None,
                 parallel_execution: bool = True,
                 fail_fast: bool = False):
        """
        Initialize AsyncCompositeHandler.
        
        Args:
            handlers: List of handlers to manage
            parallel_execution: Whether to execute handlers in parallel
            fail_fast: Whether to stop on first handler error
        """
        super().__init__()
        
        self._handlers = handlers or []
        self._parallel_execution = parallel_execution
        self._fail_fast = fail_fast
        self._health_monitor = AsyncHealthMonitor(self)
        self._executor = ThreadPoolExecutor(max_workers=4)  # For sync handlers
        
        # Statistics
        self._handler_stats = {}
        self._start_time = asyncio.get_event_loop().time()
    
    def add_handler(self, handler: BaseAsyncHandler) -> None:
        """
        Add a handler to the composite.
        
        Args:
            handler: Handler to add
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            self._handler_stats[id(handler)] = {
                'added_at': asyncio.get_event_loop().time(),
                'success_count': 0,
                'error_count': 0,
                'last_error': None
            }
    
    def remove_handler(self, handler: BaseAsyncHandler) -> bool:
        """
        Remove a handler from the composite.
        
        Args:
            handler: Handler to remove
            
        Returns:
            bool: True if handler was removed
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            handler_id = id(handler)
            if handler_id in self._handler_stats:
                del self._handler_stats[handler_id]
            return True
        return False
    
    def get_handlers(self) -> List[BaseAsyncHandler]:
        """Get all handlers."""
        return self._handlers.copy()
    
    def get_handler_count(self) -> int:
        """Get number of handlers."""
        return len(self._handlers)
    
    async def emit_async(self, record: logging.LogRecord) -> None:
        """
        Professional async emit to all handlers.
        
        Args:
            record: Log record to emit
        """
        if not self._handlers:
            return
        
        if self._parallel_execution:
            await self._emit_parallel(record)
        else:
            await self._emit_sequential(record)
    
    async def _emit_parallel(self, record: logging.LogRecord) -> None:
        """
        Emit to all handlers in parallel.
        
        Args:
            record: Log record to emit
        """
        tasks = []
        
        for handler in self._handlers:
            task = self._emit_to_handler(handler, record)
            tasks.append(task)
        
        # Execute all handlers in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            handler = self._handlers[i]
            handler_id = id(handler)
            
            if isinstance(result, Exception):
                self._record_handler_error(handler_id, result)
                await self._error_tracker.record_error(f"handler_{i}_error", result)
            else:
                self._record_handler_success(handler_id)
    
    async def _emit_sequential(self, record: logging.LogRecord) -> None:
        """
        Emit to all handlers sequentially.
        
        Args:
            record: Log record to emit
        """
        for i, handler in enumerate(self._handlers):
            try:
                await self._emit_to_handler(handler, record)
                self._record_handler_success(id(handler))
            except Exception as e:
                self._record_handler_error(id(handler), e)
                await self._error_tracker.record_error(f"handler_{i}_error", e)
                
                if self._fail_fast:
                    break
    
    async def _emit_to_handler(self, handler: BaseAsyncHandler, 
                             record: logging.LogRecord) -> None:
        """
        Emit to a single handler with proper error handling.
        
        Args:
            handler: Handler to emit to
            record: Log record to emit
        """
        try:
            if hasattr(handler, 'emit_async'):
                await handler.emit_async(record)
            else:
                # Fallback to sync emit
                handler.emit(record)
        except Exception as e:
            # Re-raise to let caller handle
            raise
    
    def _record_handler_success(self, handler_id: int) -> None:
        """Record successful handler execution."""
        if handler_id in self._handler_stats:
            self._handler_stats[handler_id]['success_count'] += 1
    
    def _record_handler_error(self, handler_id: int, error: Exception) -> None:
        """Record handler error."""
        if handler_id in self._handler_stats:
            self._handler_stats[handler_id]['error_count'] += 1
            self._handler_stats[handler_id]['last_error'] = str(error)
    
    async def _emit_async_internal(self, record: logging.LogRecord) -> None:
        """
        Internal async emit implementation.
        
        Args:
            record: Log record to emit
        """
        # This is called by the base handler's emit_async
        # We override emit_async directly for better control
        pass
    
    def _write_record_sync(self, record: logging.LogRecord) -> None:
        """
        Sync fallback for writing records.
        
        Args:
            record: Log record to write
        """
        # Write to all handlers synchronously
        for handler in self._handlers:
            try:
                handler.emit(record)
            except Exception as e:
                # Log error but continue with other handlers
                self._error_tracker.record_error_sync("sync_handler_error", e)
    
    async def initialize(self) -> None:
        """Initialize all handlers."""
        await super().initialize()
        
        # Initialize all handlers
        for handler in self._handlers:
            if hasattr(handler, 'initialize'):
                try:
                    await handler.initialize()
                except Exception as e:
                    await self._error_tracker.record_error("handler_init_error", e)
    
    async def aclose(self) -> None:
        """Close all handlers."""
        # Close all handlers
        close_tasks = []
        for handler in self._handlers:
            if hasattr(handler, 'aclose'):
                close_tasks.append(handler.aclose())
            elif hasattr(handler, 'close'):
                handler.close()
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Close executor
        self._executor.shutdown(wait=True)
        
        await super().aclose()
    
    def close(self) -> None:
        """Sync close all handlers."""
        for handler in self._handlers:
            if hasattr(handler, 'close'):
                handler.close()
        
        # Close executor
        self._executor.shutdown(wait=True)
        
        super().close()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        base_status = super().get_health_status()
        
        # Add composite-specific metrics
        composite_stats = {
            'handler_count': len(self._handlers),
            'parallel_execution': self._parallel_execution,
            'fail_fast': self._fail_fast,
            'handler_stats': self._handler_stats.copy(),
            'uptime': asyncio.get_event_loop().time() - self._start_time
        }
        
        # Add individual handler health
        handler_health = {}
        for i, handler in enumerate(self._handlers):
            try:
                if hasattr(handler, 'get_health_status'):
                    handler_health[f'handler_{i}'] = handler.get_health_status()
                else:
                    handler_health[f'handler_{i}'] = {
                        'type': handler.__class__.__name__,
                        'healthy': True
                    }
            except Exception as e:
                handler_health[f'handler_{i}'] = {
                    'type': handler.__class__.__name__,
                    'healthy': False,
                    'error': str(e)
                }
        
        composite_stats['handler_health'] = handler_health
        base_status.update(composite_stats)
        
        return base_status
    
    def is_healthy(self) -> bool:
        """Check if composite handler is healthy."""
        if not super().is_healthy():
            return False
        
        # Check if all handlers are healthy
        for handler in self._handlers:
            if hasattr(handler, 'is_healthy'):
                if not handler.is_healthy():
                    return False
            # If handler doesn't have is_healthy, assume it's OK
        
        return True
    
    def set_parallel_execution(self, parallel: bool) -> None:
        """Set parallel execution mode."""
        self._parallel_execution = parallel
    
    def set_fail_fast(self, fail_fast: bool) -> None:
        """Set fail-fast mode."""
        self._fail_fast = fail_fast
    
    def get_handler_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return {
            'total_handlers': len(self._handlers),
            'handler_stats': self._handler_stats.copy(),
            'parallel_execution': self._parallel_execution,
            'fail_fast': self._fail_fast
        }
    
    def clear_handler_stats(self) -> None:
        """Clear handler statistics."""
        self._handler_stats.clear()
        for handler in self._handlers:
            self._handler_stats[id(handler)] = {
                'added_at': asyncio.get_event_loop().time(),
                'success_count': 0,
                'error_count': 0,
                'last_error': None
            } 