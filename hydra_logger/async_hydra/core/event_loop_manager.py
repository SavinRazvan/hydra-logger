"""
Professional EventLoopManager for event loop safety and fallback management.

This module provides safe event loop detection and fallback mechanisms
to ensure async operations work correctly in all environments.
"""

import asyncio
from typing import Callable, Any, Optional, TypeVar, Awaitable
from functools import wraps

T = TypeVar('T')


class EventLoopManager:
    """
    Professional event loop safety and fallback management.
    
    Features:
    - Safe event loop detection
    - Graceful fallback to sync operations
    - Professional error handling for async context
    - Decorator support for automatic fallback
    """
    
    @staticmethod
    def has_running_loop() -> bool:
        """
        Professional check for running event loop.
        
        Returns:
            bool: True if event loop is running, False otherwise
        """
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    @staticmethod
    def safe_create_task(coro: Awaitable[T]) -> Optional[asyncio.Task[T]]:
        """
        Safely create task only if event loop is running.
        
        Args:
            coro: Coroutine to create task from
            
        Returns:
            Optional[asyncio.Task]: Task if created, None if no event loop
            
        Raises:
            RuntimeError: If no event loop and no fallback provided
        """
        if EventLoopManager.has_running_loop():
            return asyncio.create_task(coro)
        else:
            raise RuntimeError("No event loop running")
    
    @staticmethod
    async def safe_async_operation(
        operation: Callable[[], Awaitable[T]], 
        fallback_operation: Optional[Callable[[], T]] = None
    ) -> T:
        """
        Execute async operation with professional fallback.
        
        Args:
            operation: Async operation to execute
            fallback_operation: Sync fallback operation
            
        Returns:
            T: Result of operation or fallback
            
        Raises:
            RuntimeError: If no event loop and no fallback provided
        """
        if EventLoopManager.has_running_loop():
            try:
                return await operation()
            except Exception as e:
                if fallback_operation:
                    return fallback_operation()
                raise
        else:
            if fallback_operation:
                return fallback_operation()
            raise RuntimeError("No event loop and no fallback provided")
    
    @staticmethod
    def with_fallback(fallback_func: Callable[[], T]):
        """
        Decorator to add fallback to async functions.
        
        Args:
            fallback_func: Sync fallback function
            
        Returns:
            Callable: Decorated function with fallback
        """
        def decorator(async_func: Callable[[], Awaitable[T]]) -> Callable[[], T]:
            @wraps(async_func)
            def wrapper(*args, **kwargs):
                if EventLoopManager.has_running_loop():
                    try:
                        # Create task and run it
                        task = asyncio.create_task(async_func(*args, **kwargs))
                        # This is a simplified version - in practice you'd need
                        # to handle the event loop properly
                        return task
                    except Exception:
                        return fallback_func(*args, **kwargs)
                else:
                    return fallback_func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def ensure_event_loop():
        """
        Ensure event loop is available or create one.
        
        Returns:
            asyncio.AbstractEventLoop: Available event loop
        """
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
    
    @staticmethod
    def run_async_safely(coro: Awaitable[T]) -> T:
        """
        Run async coroutine safely with fallback to sync.
        
        Args:
            coro: Coroutine to run
            
        Returns:
            T: Result of coroutine execution
        """
        if EventLoopManager.has_running_loop():
            # We're already in an async context
            # This should be awaited by the caller
            return coro
        else:
            # No event loop, create one and run
            loop = EventLoopManager.ensure_event_loop()
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()


class AsyncContextGuard:
    """
    Context guard for ensuring async operations are safe.
    """
    
    def __init__(self, fallback_operation: Optional[Callable[[], Any]] = None):
        """
        Initialize async context guard.
        
        Args:
            fallback_operation: Sync fallback operation
        """
        self.fallback_operation = fallback_operation
        self._has_event_loop = EventLoopManager.has_running_loop()
    
    def __enter__(self):
        """Enter sync context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sync context."""
        pass
    
    async def __aenter__(self):
        """Enter async context."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        pass
    
    def execute(self, async_operation: Callable[[], Awaitable[T]], *args, **kwargs) -> T:
        """
        Execute operation with appropriate context.
        
        Args:
            async_operation: Async operation to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            T: Result of operation
        """
        if self._has_event_loop:
            # We're in async context, return coroutine
            return async_operation(*args, **kwargs)
        else:
            # We're in sync context, use fallback
            if self.fallback_operation:
                return self.fallback_operation(*args, **kwargs)
            else:
                raise RuntimeError("No event loop and no fallback provided") 