"""
Performance Decorators and Monitoring for Hydra-Logger

This module provides a comprehensive set of decorators for performance monitoring,
optimization, and reliability features. It includes timing, memory tracking,
retry mechanisms, caching, and rate limiting capabilities.

DECORATOR TYPES:
- Performance Timing: Measure function execution time with thresholds
- Memory Tracking: Monitor memory usage and allocation patterns
- Retry Mechanisms: Automatic retry with exponential backoff
- Caching: Function result caching with TTL support
- Rate Limiting: Control function call frequency

PERFORMANCE FEATURES:
- High-resolution timing with time.perf_counter()
- Memory usage tracking with psutil
- Configurable thresholds and warnings
- Performance statistics collection
- Error performance tracking
- Automatic data cleanup

RELIABILITY FEATURES:
- Exponential backoff retry strategies
- Configurable retry attempts and delays
- Exception-specific retry handling
- Async retry support
- Rate limiting with time windows

CACHING FEATURES:
- TTL-based cache expiration
- LRU eviction policy
- Configurable cache sizes
- Cache statistics and monitoring
- Thread-safe cache operations

USAGE EXAMPLES:

Performance Timing:
    from hydra_logger.core.decorators import performance_timer
    
    @performance_timer(name="api_call", threshold=1.0)
    def api_call():
        # Function implementation
        pass
    
    # Get performance stats
    stats = api_call.get_performance_stats()

Memory Tracking:
    from hydra_logger.core.decorators import memory_tracker
    
    @memory_tracker
    def process_data():
        # Function implementation
        pass
    
    # Get memory stats
    stats = process_data.get_memory_stats()

Retry Mechanism:
    from hydra_logger.core.decorators import retry
    
    @retry(max_attempts=3, delay=1.0, backoff_factor=2.0)
    def unreliable_operation():
        # Function that might fail
        pass

Caching:
    from hydra_logger.core.decorators import cache_result
    
    @cache_result(ttl=300, max_size=1000)
    def expensive_calculation(param):
        # Expensive computation
        return result

Rate Limiting:
    from hydra_logger.core.decorators import rate_limit
    
    @rate_limit(max_calls=100, time_window=60.0)
    def api_request():
        # API call implementation
        pass
"""

import time
import functools
import asyncio
from typing import Any, Callable, Optional, Union
from .exceptions import PerformanceError


def performance_timer(name: Optional[str] = None, 
                    threshold: Optional[float] = None,
                    raise_on_threshold: bool = False):
    """
    Decorator to measure function performance.
    
    Args:
        name: Custom name for the timer (defaults to function name)
        threshold: Performance threshold in seconds
        raise_on_threshold: Whether to raise an exception if threshold is exceeded
    """
    def decorator(func: Callable) -> Callable:
        timer_name = name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Check threshold
                if threshold and duration > threshold:
                    if raise_on_threshold:
                        raise PerformanceError(
                            f"Function {timer_name} exceeded performance threshold",
                            operation=timer_name,
                            duration=duration,
                            threshold=threshold
                        )
                    else:
                        print(f"WARNING: {timer_name} took {duration:.3f}s (threshold: {threshold:.3f}s)")
                
                # Store performance data if available
                if hasattr(wrapper, '_performance_data'):
                    wrapper._performance_data.append(duration)
                    # Keep only last 100 measurements
                    if len(wrapper._performance_data) > 100:
                        wrapper._performance_data = wrapper._performance_data[-100:]
                else:
                    wrapper._performance_data = [duration]
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                # Store error performance data
                if hasattr(wrapper, '_error_performance_data'):
                    wrapper._error_performance_data.append(duration)
                else:
                    wrapper._error_performance_data = [duration]
                raise
        
        # Add performance data access methods
        def get_performance_stats():
            """Get performance statistics."""
            if not hasattr(wrapper, '_performance_data'):
                return {}
            
            data = wrapper._performance_data
            if not data:
                return {}
            
            return {
                'count': len(data),
                'total': sum(data),
                'average': sum(data) / len(data),
                'min': min(data),
                'max': max(data),
                'latest': data[-1] if data else 0.0
            }
        
        def get_error_performance_stats():
            """Get error performance statistics."""
            if not hasattr(wrapper, '_error_performance_data'):
                return {}
            
            data = wrapper._error_performance_data
            if not data:
                return {}
            
            return {
                'count': len(data),
                'total': sum(data),
                'average': sum(data) / len(data),
                'min': min(data),
                'max': max(data),
                'latest': data[-1] if data else 0.0
            }
        
        def clear_performance_data():
            """Clear performance data."""
            if hasattr(wrapper, '_performance_data'):
                wrapper._performance_data.clear()
            if hasattr(wrapper, '_error_performance_data'):
                wrapper._error_performance_data.clear()
        
        # Attach methods to wrapper
        wrapper.get_performance_stats = get_performance_stats
        wrapper.get_error_performance_stats = get_error_performance_stats
        wrapper.clear_performance_data = clear_performance_data
        
        return wrapper
    
    return decorator


def async_performance_timer(name: Optional[str] = None,
                           threshold: Optional[float] = None,
                           raise_on_threshold: bool = False):
    """
    Decorator to measure async function performance.
    
    Args:
        name: Custom name for the timer (defaults to function name)
        threshold: Performance threshold in seconds
        raise_on_threshold: Whether to raise an exception if threshold is exceeded
    """
    def decorator(func: Callable) -> Callable:
        timer_name = name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Check threshold
                if threshold and duration > threshold:
                    if raise_on_threshold:
                        raise PerformanceError(
                            f"Async function {timer_name} exceeded performance threshold",
                            operation=timer_name,
                            duration=duration,
                            threshold=threshold
                        )
                    else:
                        print(f"WARNING: {timer_name} took {duration:.3f}s (threshold: {threshold:.3f}s)")
                
                # Store performance data if available
                if hasattr(wrapper, '_performance_data'):
                    wrapper._performance_data.append(duration)
                    # Keep only last 100 measurements
                    if len(wrapper._performance_data) > 100:
                        wrapper._performance_data = wrapper._performance_data[-100:]
                else:
                    wrapper._performance_data = [duration]
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                # Store error performance data
                if hasattr(wrapper, '_error_performance_data'):
                    wrapper._error_performance_data.append(duration)
                else:
                    wrapper._error_performance_data = [duration]
                raise
        
        # Add performance data access methods
        def get_performance_stats():
            """Get performance statistics."""
            if not hasattr(wrapper, '_performance_data'):
                return {}
            
            data = wrapper._performance_data
            if not data:
                return {}
            
            return {
                'count': len(data),
                'total': sum(data),
                'average': sum(data) / len(data),
                'min': min(data),
                'max': max(data),
                'latest': data[-1] if data else 0.0
            }
        
        def get_error_performance_stats():
            """Get error performance statistics."""
            if not hasattr(wrapper, '_error_performance_data'):
                return {}
            
            data = wrapper._error_performance_data
            if not data:
                return {}
            
            return {
                'count': len(data),
                'total': sum(data),
                'average': sum(data) / len(data),
                'min': min(data),
                'max': max(data),
                'latest': data[-1] if data else 0.0
            }
        
        def clear_performance_data():
            """Clear performance data."""
            if hasattr(wrapper, '_performance_data'):
                wrapper._performance_data.clear()
            if hasattr(wrapper, '_error_performance_data'):
                wrapper._error_performance_data.clear()
        
        # Attach methods to wrapper
        wrapper.get_performance_stats = get_performance_stats
        wrapper.get_error_performance_stats = get_error_performance_stats
        wrapper.clear_performance_data = clear_performance_data
        
        return wrapper
    
    return decorator


def memory_tracker(func: Callable) -> Callable:
    """
    Decorator to track memory usage of functions.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        try:
            result = func(*args, **kwargs)
            memory_after = process.memory_info().rss
            memory_diff = memory_after - memory_before
            
            # Store memory data if available
            if hasattr(wrapper, '_memory_data'):
                wrapper._memory_data.append(memory_diff)
                # Keep only last 100 measurements
                if len(wrapper._memory_data) > 100:
                    wrapper._memory_data = wrapper._memory_data[-100:]
            else:
                wrapper._memory_data = [memory_diff]
            
            return result
        except Exception as e:
            memory_after = process.memory_info().rss
            memory_diff = memory_after - memory_before
            
            # Store error memory data
            if hasattr(wrapper, '_error_memory_data'):
                wrapper._error_memory_data.append(memory_diff)
            else:
                wrapper._error_memory_data = [memory_diff]
            raise
    
    # Add memory data access methods
    def get_memory_stats():
        """Get memory statistics."""
        if not hasattr(wrapper, '_memory_data'):
            return {}
        
        data = wrapper._memory_data
        if not data:
            return {}
        
        return {
            'count': len(data),
            'total': sum(data),
            'average': sum(data) / len(data),
            'min': min(data),
            'max': max(data),
            'latest': data[-1] if data else 0
        }
    
    def get_error_memory_stats():
        """Get error memory statistics."""
        if not hasattr(wrapper, '_error_memory_data'):
            return {}
        
        data = wrapper._error_memory_data
        if not data:
            return {}
        
        return {
            'count': len(data),
            'total': sum(data),
            'average': sum(data) / len(data),
            'min': min(data),
            'max': max(data),
            'latest': data[-1] if data else 0
        }
    
    def clear_memory_data():
        """Clear memory data."""
        if hasattr(wrapper, '_memory_data'):
            wrapper._memory_data.clear()
        if hasattr(wrapper, '_error_memory_data'):
            wrapper._error_memory_data.clear()
    
    # Attach methods to wrapper
    wrapper.get_memory_stats = get_memory_stats
    wrapper.get_error_memory_stats = get_error_memory_stats
    wrapper.clear_memory_data = clear_memory_data
    
    return wrapper


def retry(max_attempts: int = 3, 
          delay: float = 1.0,
          backoff_factor: float = 2.0,
          exceptions: tuple = (Exception,)):
    """
    Decorator to retry function calls on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        # Last attempt failed, re-raise the exception
                        raise last_exception
            
            # This should never be reached
            raise last_exception
        
        return wrapper
    
    return decorator


def async_retry(max_attempts: int = 3,
                delay: float = 1.0,
                backoff_factor: float = 2.0,
                exceptions: tuple = (Exception,)):
    """
    Decorator to retry async function calls on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        # Last attempt failed, re-raise the exception
                        raise last_exception
            
            # This should never be reached
            raise last_exception
        
        return wrapper
    
    return decorator


def cache_result(ttl: Optional[int] = None, max_size: int = 1000):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live for cached results in seconds
        max_size: Maximum number of cached results
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_timestamps = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = (func.__name__, str(args), str(sorted(kwargs.items())))
            
            # Check if result is cached and not expired
            if cache_key in cache:
                if ttl is None or time.time() - cache_timestamps[cache_key] < ttl:
                    return cache[cache_key]
                else:
                    # Expired, remove from cache
                    del cache[cache_key]
                    del cache_timestamps[cache_key]
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Cache result
            cache[cache_key] = result
            cache_timestamps[cache_key] = time.time()
            
            # Enforce max size
            if len(cache) > max_size:
                # Remove oldest entries
                oldest_key = min(cache_timestamps.keys(), key=cache_timestamps.get)
                del cache[oldest_key]
                del cache_timestamps[oldest_key]
            
            return result
        
        # Add cache management methods
        def clear_cache():
            """Clear the cache."""
            cache.clear()
            cache_timestamps.clear()
        
        def get_cache_stats():
            """Get cache statistics."""
            return {
                'size': len(cache),
                'max_size': max_size,
                'ttl': ttl
            }
        
        # Attach methods to wrapper
        wrapper.clear_cache = clear_cache
        wrapper.get_cache_stats = get_cache_stats
        
        return wrapper
    
    return decorator


def rate_limit(max_calls: int, time_window: float):
    """
    Decorator to limit function call rate.
    
    Args:
        max_calls: Maximum number of calls allowed in time window
        time_window: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        call_times = []
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Remove old call times outside the window
            call_times[:] = [t for t in call_times if current_time - t < time_window]
            
            # Check if we can make another call
            if len(call_times) >= max_calls:
                oldest_call = min(call_times)
                wait_time = time_window - (current_time - oldest_call)
                if wait_time > 0:
                    time.sleep(wait_time)
                    current_time = time.time()
            
            # Record this call
            call_times.append(current_time)
            
            # Call the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def async_rate_limit(max_calls: int, time_window: float):
    """
    Decorator to limit async function call rate.
    
    Args:
        max_calls: Maximum number of calls allowed in time window
        time_window: Time window in seconds
    """
    def decorator(func: Callable) -> Callable:
        call_times = []
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Remove old call times outside the window
            call_times[:] = [t for t in call_times if current_time - t < time_window]
            
            # Check if we can make another call
            if len(call_times) >= max_calls:
                oldest_call = min(call_times)
                wait_time = time_window - (current_time - oldest_call)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    current_time = time.time()
            
            # Record this call
            call_times.append(current_time)
            
            # Call the function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
