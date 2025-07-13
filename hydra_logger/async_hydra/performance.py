"""
Professional AsyncPerformanceMonitor for async performance monitoring.

This module provides async performance monitoring including:
- Async operation timing
- Performance statistics
- Memory usage tracking
- Professional metrics
"""

import asyncio
import time
import statistics
from typing import Dict, Any, List, Optional, Callable
from contextlib import asynccontextmanager
from functools import wraps


class AsyncPerformanceMonitor:
    """
    Professional async performance monitor with comprehensive metrics.
    
    Features:
    - Async operation timing
    - Performance statistics
    - Memory usage tracking
    - Professional metrics
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize AsyncPerformanceMonitor.
        
        Args:
            max_history: Maximum number of timing records to keep
        """
        self._max_history = max_history
        self._start_time = time.time()
        self._timings: Dict[str, List[float]] = {}
        self._counters: Dict[str, int] = {}
        self._memory_snapshots: List[Dict[str, Any]] = []
        self._performance_alerts: List[Dict[str, Any]] = []
        self._alert_thresholds = {
            'slow_operation': 1.0,  # 1 second
            'memory_high': 80.0,    # 80%
            'error_rate': 0.1       # 10%
        }
    
    @asynccontextmanager
    async def async_timer(self, operation_name: str):
        """
        Async context manager for timing operations.
        
        Args:
            operation_name: Name of the operation to time
            
        Yields:
            float: Start time
        """
        start_time = time.time()
        try:
            yield start_time
        finally:
            duration = time.time() - start_time
            self._record_timing(operation_name, duration)
    
    def start_async_processing_timer(self, operation_name: str) -> float:
        """
        Start timing an async operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            float: Start time
        """
        start_time = time.time()
        self._counters[operation_name] = self._counters.get(operation_name, 0) + 1
        return start_time
    
    def end_async_processing_timer(self, operation_name: str, start_time: float) -> float:
        """
        End timing an async operation.
        
        Args:
            operation_name: Name of the operation
            start_time: Start time from start_async_processing_timer
            
        Returns:
            float: Duration in seconds
        """
        duration = time.time() - start_time
        self._record_timing(operation_name, duration)
        return duration
    
    def _record_timing(self, operation_name: str, duration: float) -> None:
        """Record timing for an operation."""
        if operation_name not in self._timings:
            self._timings[operation_name] = []
        
        self._timings[operation_name].append(duration)
        
        # Keep history size manageable
        if len(self._timings[operation_name]) > self._max_history:
            self._timings[operation_name].pop(0)
        
        # Check for performance alerts
        self._check_performance_alerts(operation_name, duration)
    
    def _check_performance_alerts(self, operation_name: str, duration: float) -> None:
        """Check for performance alerts."""
        if duration > self._alert_thresholds['slow_operation']:
            alert = {
                'timestamp': time.time(),
                'type': 'slow_operation',
                'operation': operation_name,
                'duration': duration,
                'threshold': self._alert_thresholds['slow_operation']
            }
            self._performance_alerts.append(alert)
    
    def get_async_statistics(self) -> Dict[str, Any]:
        """Get comprehensive async performance statistics."""
        stats = {
            'uptime': time.time() - self._start_time,
            'operations': {},
            'counters': self._counters.copy(),
            'alerts': len(self._performance_alerts),
            'memory_snapshots': len(self._memory_snapshots)
        }
        
        # Calculate statistics for each operation
        for operation_name, timings in self._timings.items():
            if timings:
                stats['operations'][operation_name] = {
                    'count': len(timings),
                    'total_time': sum(timings),
                    'average_time': statistics.mean(timings),
                    'median_time': statistics.median(timings),
                    'min_time': min(timings),
                    'max_time': max(timings),
                    'std_dev': statistics.stdev(timings) if len(timings) > 1 else 0,
                    'recent_timings': timings[-10:]  # Last 10 timings
                }
        
        return stats
    
    def reset_async_statistics(self) -> None:
        """Reset all performance statistics."""
        self._timings.clear()
        self._counters.clear()
        self._memory_snapshots.clear()
        self._performance_alerts.clear()
        self._start_time = time.time()
    
    def take_memory_snapshot(self) -> Dict[str, Any]:
        """Take a memory usage snapshot."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            snapshot = {
                'timestamp': time.time(),
                'system_memory': {
                    'total_mb': memory.total / (1024 * 1024),
                    'available_mb': memory.available / (1024 * 1024),
                    'used_mb': memory.used / (1024 * 1024),
                    'percent': memory.percent
                },
                'process_memory': {
                    'rss_mb': process_memory.rss / (1024 * 1024),
                    'vms_mb': process_memory.vms / (1024 * 1024),
                    'cpu_percent': process.cpu_percent()
                }
            }
            
            self._memory_snapshots.append(snapshot)
            
            # Keep history size manageable
            if len(self._memory_snapshots) > self._max_history:
                self._memory_snapshots.pop(0)
            
            # Check for memory alerts
            if memory.percent > self._alert_thresholds['memory_high']:
                alert = {
                    'timestamp': time.time(),
                    'type': 'memory_high',
                    'memory_percent': memory.percent,
                    'threshold': self._alert_thresholds['memory_high']
                }
                self._performance_alerts.append(alert)
            
            return snapshot
            
        except ImportError:
            return {
                'timestamp': time.time(),
                'error': 'psutil not available'
            }
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        if not self._memory_snapshots:
            return {'error': 'No memory snapshots available'}
        
        recent_snapshots = self._memory_snapshots[-10:]  # Last 10 snapshots
        
        system_percentages = [s['system_memory']['percent'] for s in recent_snapshots]
        process_rss = [s['process_memory']['rss_mb'] for s in recent_snapshots]
        
        return {
            'snapshot_count': len(self._memory_snapshots),
            'recent_system_memory': {
                'average_percent': statistics.mean(system_percentages),
                'max_percent': max(system_percentages),
                'min_percent': min(system_percentages)
            },
            'recent_process_memory': {
                'average_rss_mb': statistics.mean(process_rss),
                'max_rss_mb': max(process_rss),
                'min_rss_mb': min(process_rss)
            },
            'latest_snapshot': self._memory_snapshots[-1] if self._memory_snapshots else None
        }
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get recent performance alerts."""
        return self._performance_alerts.copy()
    
    def clear_performance_alerts(self) -> None:
        """Clear performance alerts."""
        self._performance_alerts.clear()
    
    def set_alert_threshold(self, alert_type: str, threshold: float) -> None:
        """Set alert threshold."""
        if alert_type in self._alert_thresholds:
            self._alert_thresholds[alert_type] = threshold
    
    def get_alert_thresholds(self) -> Dict[str, float]:
        """Get current alert thresholds."""
        return self._alert_thresholds.copy()
    
    def is_performance_healthy(self) -> bool:
        """Check if performance is healthy."""
        # Check for recent slow operations
        recent_alerts = [a for a in self._performance_alerts 
                        if time.time() - a['timestamp'] < 300]  # Last 5 minutes
        
        if len(recent_alerts) > 10:  # Too many recent alerts
            return False
        
        # Check memory usage
        memory_stats = self.get_memory_statistics()
        if 'recent_system_memory' in memory_stats:
            avg_memory = memory_stats['recent_system_memory']['average_percent']
            if avg_memory > self._alert_thresholds['memory_high']:
                return False
        
        return True


# Global performance monitor instance
_performance_monitor = AsyncPerformanceMonitor()


def get_performance_monitor() -> AsyncPerformanceMonitor:
    """Get global performance monitor instance."""
    return _performance_monitor


def async_timer(operation_name: str):
    """
    Decorator for timing async functions.
    
    Args:
        operation_name: Name of the operation
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = _performance_monitor.start_async_processing_timer(operation_name)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                _performance_monitor.end_async_processing_timer(operation_name, start_time)
        return wrapper
    return decorator


@asynccontextmanager
async def performance_context(operation_name: str):
    """
    Async context manager for performance monitoring.
    
    Args:
        operation_name: Name of the operation
        
    Yields:
        float: Start time
    """
    async with _performance_monitor.async_timer(operation_name) as start_time:
        yield start_time 