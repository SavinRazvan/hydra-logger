"""
Professional AsyncErrorTracker for comprehensive error tracking and monitoring.

This module provides async-safe error recording with callbacks and
comprehensive error statistics.
"""

import asyncio
import time
from typing import Dict, Any, List, Callable, Optional


class AsyncErrorTracker:
    """
    Professional error tracking with async-safe operations.
    
    Features:
    - Async-safe error recording
    - Error statistics and trends
    - Callback system for error handling
    - Professional error categorization
    """
    
    def __init__(self):
        """Initialize AsyncErrorTracker."""
        self._error_counts: Dict[str, int] = {}
        self._last_error_time: Optional[float] = None
        self._error_callbacks: List[Callable] = []
        self._error_lock = asyncio.Lock()
        self._start_time = time.time()
        self._stats = {
            'total_errors': 0,
            'error_types': 0,
            'callback_calls': 0,
            'callback_errors': 0
        }
    
    async def record_error(self, error_type: str, error: Exception) -> None:
        """
        Professional error recording with proper async handling.
        
        Args:
            error_type: Type/category of error
            error: Exception that occurred
        """
        async with self._error_lock:
            self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
            self._last_error_time = time.time()
            self._stats['total_errors'] += 1
            self._stats['error_types'] = len(self._error_counts)
            
            # Call error callbacks with proper exception handling
            for callback in self._error_callbacks:
                try:
                    self._stats['callback_calls'] += 1
                    if asyncio.iscoroutinefunction(callback):
                        await callback(error_type, error)
                    else:
                        callback(error_type, error)
                except Exception as callback_error:
                    self._stats['callback_errors'] += 1
                    # Don't let callback errors break error tracking
                    print(f"Error in error callback: {callback_error}")
    
    def record_error_sync(self, error_type: str, error: Exception) -> None:
        """
        Synchronous error recording for sync contexts.
        
        Args:
            error_type: Type/category of error
            error: Exception that occurred
        """
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        self._last_error_time = time.time()
        self._stats['total_errors'] += 1
        self._stats['error_types'] = len(self._error_counts)
        
        # Call error callbacks synchronously
        for callback in self._error_callbacks:
            try:
                self._stats['callback_calls'] += 1
                callback(error_type, error)
            except Exception as callback_error:
                self._stats['callback_errors'] += 1
                print(f"Error in error callback: {callback_error}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        return {
            'error_counts': self._error_counts.copy(),
            'last_error_time': self._last_error_time,
            'total_errors': self._stats['total_errors'],
            'error_types': self._stats['error_types'],
            'callback_stats': {
                'calls': self._stats['callback_calls'],
                'errors': self._stats['callback_errors']
            },
            'uptime': time.time() - self._start_time
        }
    
    def add_error_callback(self, callback: Callable) -> None:
        """
        Add error callback function.
        
        Args:
            callback: Function to call when errors occur
        """
        self._error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable) -> bool:
        """
        Remove error callback function.
        
        Args:
            callback: Function to remove
            
        Returns:
            bool: True if callback was removed, False if not found
        """
        try:
            self._error_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def clear_error_stats(self) -> None:
        """Clear all error statistics."""
        self._error_counts.clear()
        self._last_error_time = None
        self._stats = {
            'total_errors': 0,
            'error_types': 0,
            'callback_calls': 0,
            'callback_errors': 0
        }
        self._start_time = time.time()
    
    def get_error_count(self, error_type: str) -> int:
        """Get count for specific error type."""
        return self._error_counts.get(error_type, 0)
    
    def get_total_error_count(self) -> int:
        """Get total error count."""
        return self._stats['total_errors']
    
    def get_error_types(self) -> List[str]:
        """Get list of error types."""
        return list(self._error_counts.keys())
    
    def is_healthy(self) -> bool:
        """Check if error tracker is healthy."""
        return self._stats['total_errors'] < 100  # Threshold for health
    
    async def shutdown(self) -> None:
        """Shutdown error tracker."""
        # Clear callbacks to prevent memory leaks
        self._error_callbacks.clear() 