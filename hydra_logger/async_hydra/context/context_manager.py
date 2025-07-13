"""
Professional AsyncContextManager for async context management.

This module provides professional async context management including:
- Context preservation across async operations
- Thread-safe context operations
- Professional error handling
- Context switching detection
"""

import asyncio
import contextvars
import time
from typing import Any, Dict, Optional, TypeVar, Generic
from contextlib import asynccontextmanager

T = TypeVar('T')


class AsyncContext:
    """
    Professional async context with comprehensive metadata.
    
    Features:
    - Context ID generation and tracking
    - Metadata storage and retrieval
    - Timestamp tracking
    - Thread-safe operations
    """
    
    def __init__(self, context_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize AsyncContext.
        
        Args:
            context_id: Unique context identifier
            metadata: Context metadata
        """
        self.context_id = context_id or self._generate_context_id()
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
    
    def _generate_context_id(self) -> str:
        """Generate unique context ID."""
        import uuid
        return f"ctx_{uuid.uuid4().hex[:8]}"
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update context metadata."""
        self.metadata[key] = value
        self._update_access()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get context metadata."""
        self._update_access()
        return self.metadata.get(key, default)
    
    def _update_access(self) -> None:
        """Update access statistics."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics."""
        return {
            'context_id': self.context_id,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'metadata_keys': list(self.metadata.keys()),
            'age_seconds': time.time() - self.created_at
        }


class AsyncContextManager:
    """
    Professional async context manager with comprehensive features.
    
    Features:
    - Context preservation across async operations
    - Thread-safe context operations
    - Professional error handling
    - Context switching detection
    """
    
    # Class variable for context variable
    _context_var = contextvars.ContextVar('async_context', default=None)
    
    def __init__(self, context: Optional[AsyncContext] = None):
        """
        Initialize AsyncContextManager.
        
        Args:
            context: Initial context (optional)
        """
        self.context = context or AsyncContext()
        self._previous_context = None
        self._context_lock = asyncio.Lock()
        self._switch_count = 0
        self._start_time = time.time()
    
    async def __aenter__(self):
        """Professional async context entry."""
        async with self._context_lock:
            old_context = self._context_var.get()
            self._previous_context = old_context
            self._context_var.set(self.context)
            self._switch_count += 1
            # Notify context switcher
            from .context_manager import get_context_switcher
            get_context_switcher().detect_context_switch(old_context, self.context)
            return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Professional async context exit."""
        async with self._context_lock:
            old_context = self._context_var.get()
            if self._previous_context is not None:
                self._context_var.set(self._previous_context)
                new_context = self._previous_context
            else:
                self._context_var.set(None)
                new_context = None
            # Notify context switcher
            from .context_manager import get_context_switcher
            get_context_switcher().detect_context_switch(old_context, new_context)
    
    def __enter__(self):
        """Sync context entry for compatibility."""
        self._previous_context = self._context_var.get()
        self._context_var.set(self.context)
        self._switch_count += 1
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context exit for compatibility."""
        if self._previous_context is not None:
            self._context_var.set(self._previous_context)
        else:
            self._context_var.set(None)
    
    @classmethod
    def get_current_context(cls) -> Optional[AsyncContext]:
        """Get current context from context variable."""
        return cls._context_var.get()
    
    @classmethod
    def set_current_context(cls, context: AsyncContext) -> None:
        """Set current context in context variable."""
        cls._context_var.set(context)
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get context manager statistics."""
        return {
            'context_id': self.context.context_id,
            'switch_count': self._switch_count,
            'uptime': time.time() - self._start_time,
            'context_stats': self.context.get_stats(),
            'has_previous_context': self._previous_context is not None
        }
    
    def update_context_metadata(self, key: str, value: Any) -> None:
        """Update current context metadata."""
        self.context.update_metadata(key, value)
    
    def get_context_metadata(self, key: str, default: Any = None) -> Any:
        """Get current context metadata."""
        return self.context.get_metadata(key, default)


class AsyncContextSwitcher:
    """
    Professional context switcher for detecting and tracking context changes.
    
    Features:
    - Detect async context switches
    - Track context switch patterns
    - Professional context monitoring
    """
    
    def __init__(self):
        """Initialize AsyncContextSwitcher."""
        self._switch_history = []
        self._max_history = 100
        self._switch_count = 0
        self._start_time = time.time()
    
    def detect_context_switch(self, old_context: Optional[AsyncContext], 
                            new_context: Optional[AsyncContext]) -> bool:
        """
        Detect if context has switched.
        
        Args:
            old_context: Previous context
            new_context: New context
            
        Returns:
            bool: True if context switched
        """
        if old_context is None and new_context is None:
            return False
        
        if old_context is None or new_context is None:
            self._record_switch(old_context, new_context)
            return True
        
        if old_context.context_id != new_context.context_id:
            self._record_switch(old_context, new_context)
            return True
        
        return False
    
    def _record_switch(self, old_context: Optional[AsyncContext], 
                      new_context: Optional[AsyncContext]) -> None:
        """Record a context switch."""
        self._switch_count += 1
        switch_record = {
            'timestamp': time.time(),
            'old_context_id': old_context.context_id if old_context else None,
            'new_context_id': new_context.context_id if new_context else None,
            'switch_number': self._switch_count
        }
        
        self._switch_history.append(switch_record)
        
        # Keep history size manageable
        if len(self._switch_history) > self._max_history:
            self._switch_history.pop(0)
    
    def get_switch_count(self) -> int:
        """Get total switch count."""
        return self._switch_count
    
    def get_switch_history(self) -> list:
        """Get recent switch history."""
        return self._switch_history.copy()
    
    def reset_switch_count(self) -> None:
        """Reset switch counter."""
        self._switch_count = 0
        self._switch_history.clear()
    
    def get_switch_stats(self) -> Dict[str, Any]:
        """Get comprehensive switch statistics."""
        return {
            'total_switches': self._switch_count,
            'recent_switches': len(self._switch_history),
            'uptime': time.time() - self._start_time,
            'switch_rate': self._switch_count / max(time.time() - self._start_time, 1),
            'last_switch': self._switch_history[-1] if self._switch_history else None
        }


# Global context switcher instance
_context_switcher = AsyncContextSwitcher()


def get_context_switcher() -> AsyncContextSwitcher:
    """Get global context switcher instance."""
    return _context_switcher


@asynccontextmanager
async def async_context(context: Optional[AsyncContext] = None):
    """
    Async context manager decorator for easy context management.
    
    Args:
        context: Context to use (creates new one if None)
        
    Yields:
        AsyncContextManager: Context manager instance
    """
    manager = AsyncContextManager(context)
    async with manager:
        yield manager 