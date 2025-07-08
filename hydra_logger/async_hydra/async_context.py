"""
Async context propagation for Hydra-Logger.

This module provides async context propagation capabilities for preserving
async context across logging operations in async applications.

Key Features:
- AsyncContextManager for context preservation
- Async trace ID propagation
- Async correlation ID support
- Async context switching detection
- Thread-safe async context operations

Example:
    >>> from hydra_logger.async_context import AsyncContextManager
    >>> async with AsyncContextManager():
    ...     await logger.info("LAYER", "Message with preserved context")
"""

import contextvars
import threading
import time
import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from contextlib import asynccontextmanager


@dataclass
class AsyncContext:
    """Async context information for logging operations."""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    context_switches: int = 0


# Global context variable
_async_context_var: contextvars.ContextVar[Optional[AsyncContext]] = contextvars.ContextVar('async_context')


class AsyncContextManager:
    """
    Async context manager for preserving async context across logging operations.
    
    This class provides context preservation capabilities for async applications,
    ensuring that context information is properly propagated across async
    operations and logging calls.
    """
    
    def __init__(self, context: Optional[AsyncContext] = None):
        """
        Initialize async context manager.
        
        Args:
            context (Optional[AsyncContext]): Initial context or None for auto-generated
        """
        self.context = context or AsyncContext()
        self._previous_context: Optional[AsyncContext] = None
    
    async def __aenter__(self):
        """Enter async context."""
        # Store previous context
        self._previous_context = _async_context_var.get(None)
        
        # Set new context
        _async_context_var.set(self.context)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        # Restore previous context
        if self._previous_context is not None:
            _async_context_var.set(self._previous_context)
        else:
            _async_context_var.set(None)
    
    @classmethod
    def get_current_context(cls) -> Optional[AsyncContext]:
        """Get current async context."""
        return _async_context_var.get(None)
    
    @classmethod
    def set_current_context(cls, context: AsyncContext) -> None:
        """Set current async context."""
        _async_context_var.set(context)
    
    @classmethod
    def clear_current_context(cls) -> None:
        """Clear current async context."""
        _async_context_var.set(None)


class AsyncTraceManager:
    """
    Async trace manager for distributed tracing support.
    
    This class provides distributed tracing capabilities for async applications,
    enabling trace ID propagation across async operations and services.
    """
    
    def __init__(self):
        self._trace_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('trace_id')
        self._correlation_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('correlation_id')
    
    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """
        Start a new trace.
        
        Args:
            trace_id (Optional[str]): Custom trace ID or None for auto-generated
            
        Returns:
            str: Trace ID
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        self._trace_var.set(trace_id)
        return trace_id
    
    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID."""
        return self._trace_var.get(None)
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current trace."""
        self._correlation_var.set(correlation_id)
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        return self._correlation_var.get(None)
    
    def clear_trace(self) -> None:
        """Clear current trace."""
        self._trace_var.set(None)
        self._correlation_var.set(None)


class AsyncContextSwitcher:
    """
    Async context switcher for detecting and handling context switches.
    
    This class provides capabilities for detecting when async context
    switches occur and handling them appropriately.
    """
    
    def __init__(self):
        self._switch_count = 0
        self._last_context = None
        self._lock = threading.Lock()
    
    def detect_context_switch(self, current_context: Optional[AsyncContext]) -> bool:
        """
        Detect if a context switch has occurred.
        
        Args:
            current_context (Optional[AsyncContext]): Current context
            
        Returns:
            bool: True if context switch detected, False otherwise
        """
        with self._lock:
            # If this is the first context (no previous context), no switch detected
            if self._last_context is None:
                self._last_context = current_context
                return False
            
            # If current context is None, no switch detected
            if current_context is None:
                self._last_context = current_context
                return False
            
            # Check if context has changed
            if (self._last_context.trace_id != current_context.trace_id or
                self._last_context.correlation_id != current_context.correlation_id):
                self._switch_count += 1
                self._last_context = current_context
                return True
            
            # No change detected
            self._last_context = current_context
            return False
    
    def get_switch_count(self) -> int:
        """Get total number of context switches."""
        with self._lock:
            return self._switch_count
    
    def reset_switch_count(self) -> None:
        """Reset context switch counter."""
        with self._lock:
            self._switch_count = 0


# Global instances
_async_trace_manager = AsyncTraceManager()
_async_context_switcher = AsyncContextSwitcher()


def get_async_context() -> Optional[AsyncContext]:
    """Get current async context."""
    return AsyncContextManager.get_current_context()


def set_async_context(context: AsyncContext) -> None:
    """Set current async context."""
    AsyncContextManager.set_current_context(context)


def clear_async_context() -> None:
    """Clear current async context."""
    AsyncContextManager.clear_current_context()


def get_trace_id() -> Optional[str]:
    """Get current trace ID."""
    return _async_trace_manager.get_trace_id()


def start_trace(trace_id: Optional[str] = None) -> str:
    """Start a new trace."""
    return _async_trace_manager.start_trace(trace_id)


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current trace."""
    _async_trace_manager.set_correlation_id(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _async_trace_manager.get_correlation_id()


def detect_context_switch(context: Optional[AsyncContext]) -> bool:
    """Detect if a context switch has occurred."""
    return _async_context_switcher.detect_context_switch(context)


def get_context_switch_count() -> int:
    """Get total number of context switches."""
    return _async_context_switcher.get_switch_count()


@asynccontextmanager
async def async_context(context: Optional[AsyncContext] = None):
    """
    Async context manager for preserving context across async operations.
    
    Args:
        context (Optional[AsyncContext]): Context to preserve or None for auto-generated
        
    Example:
        >>> async with async_context():
        ...     await logger.info("LAYER", "Message with preserved context")
    """
    manager = AsyncContextManager(context)
    async with manager:
        yield manager


@asynccontextmanager
async def trace_context(trace_id: Optional[str] = None):
    """
    Async context manager for distributed tracing.
    
    Args:
        trace_id (Optional[str]): Trace ID or None for auto-generated
        
    Example:
        >>> async with trace_context():
        ...     await logger.info("LAYER", "Message with trace ID")
    """
    trace_id = _async_trace_manager.start_trace(trace_id)
    try:
        yield trace_id
    finally:
        _async_trace_manager.clear_trace() 