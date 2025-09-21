"""
Performance-Optimized Monitoring System for Hydra-Logger

This module provides sampling-based metrics collection to minimize performance impact
while maintaining useful monitoring data. It offers configurable sampling strategies
to balance monitoring detail with system performance.

FEATURES:
- Configurable sampling strategies (disabled, minimal, low, medium, high, full)
- Performance-optimized metrics collection
- Decorator-based function monitoring
- Sampling rate management
- Minimal overhead monitoring

USAGE:
    from hydra_logger.monitoring.performance_monitoring import (
        PerformanceMonitor, SamplingStrategy, conditional_monitoring
    )
    
    # Create performance monitor
    monitor = PerformanceMonitor(sampling_strategy=SamplingStrategy.LOW)
    
    # Use decorator for conditional monitoring
    @conditional_monitoring(SamplingStrategy.MEDIUM)
    def my_function():
        # Function implementation
        pass
    
    # Get metrics
    metrics = monitor.get_metrics()
"""

import time
import random
from typing import Dict, Any, Optional, Callable
from functools import wraps
from enum import Enum


class SamplingStrategy(Enum):
    """Sampling strategies for performance monitoring."""
    DISABLED = "disabled"        # No monitoring - zero overhead
    MINIMAL = "minimal"         # 0.1% sampling - very low overhead
    LOW = "low"                 # 1% sampling - low overhead
    MEDIUM = "medium"           # 5% sampling - moderate overhead
    HIGH = "high"               # 10% sampling - higher overhead
    FULL = "full"               # 100% sampling - maximum overhead


class PerformanceMonitor:
    """High-performance monitoring with configurable sampling."""
    
    def __init__(self, sampling_strategy: SamplingStrategy = SamplingStrategy.DISABLED):
        self.sampling_strategy = sampling_strategy
        self._sampling_rate = self._get_sampling_rate()
        self._metrics = {
            'total_calls': 0,
            'sampled_calls': 0,
            'skipped_calls': 0,
            'total_processing_time': 0.0,
            'last_reset': time.time()
        }
        self._enabled = sampling_strategy != SamplingStrategy.DISABLED
    
    def _get_sampling_rate(self) -> float:
        """Get sampling rate based on strategy."""
        rates = {
            SamplingStrategy.DISABLED: 0.0,
            SamplingStrategy.MINIMAL: 0.001,  # 0.1%
            SamplingStrategy.LOW: 0.01,       # 1%
            SamplingStrategy.MEDIUM: 0.05,    # 5%
            SamplingStrategy.HIGH: 0.1,       # 10%
            SamplingStrategy.FULL: 1.0        # 100%
        }
        return rates.get(self.sampling_strategy, 0.0)
    
    def should_sample(self) -> bool:
        """Determine if current call should be sampled."""
        if not self._enabled:
            return False
        
        self._metrics['total_calls'] += 1
        
        if random.random() < self._sampling_rate:
            self._metrics['sampled_calls'] += 1
            return True
        else:
            self._metrics['skipped_calls'] += 1
            return False
    
    def record_processing_time(self, duration: float):
        """Record processing time for sampled calls."""
        if self._enabled:
            self._metrics['total_processing_time'] += duration
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self._enabled:
            return {'monitoring_enabled': False}
        
        total_calls = self._metrics['total_calls']
        sampled_calls = self._metrics['sampled_calls']
        
        return {
            'monitoring_enabled': True,
            'sampling_strategy': self.sampling_strategy.value,
            'sampling_rate': self._sampling_rate,
            'total_calls': total_calls,
            'sampled_calls': sampled_calls,
            'skipped_calls': self._metrics['skipped_calls'],
            'sampling_ratio': sampled_calls / total_calls if total_calls > 0 else 0.0,
            'avg_processing_time_ms': (self._metrics['total_processing_time'] / sampled_calls * 1000 
                                     if sampled_calls > 0 else 0.0),
            'total_processing_time_ms': self._metrics['total_processing_time'] * 1000,
            'uptime_seconds': time.time() - self._metrics['last_reset']
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self._metrics = {
            'total_calls': 0,
            'sampled_calls': 0,
            'skipped_calls': 0,
            'total_processing_time': 0.0,
            'last_reset': time.time()
        }


def conditional_monitoring(sampling_strategy: SamplingStrategy = SamplingStrategy.DISABLED):
    """
    Decorator for conditional performance monitoring.
    
    Args:
        sampling_strategy: Sampling strategy to use
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check if monitoring is enabled
            if (hasattr(self, '_performance_monitor') and 
                self._performance_monitor and 
                self._performance_monitor._enabled):
                
                if self._performance_monitor.should_sample():
                    start_time = time.perf_counter()
                    result = func(self, *args, **kwargs)
                    end_time = time.perf_counter()
                    
                    # Record processing time
                    duration = end_time - start_time
                    self._performance_monitor.record_processing_time(duration)
                    
                    return result
                else:
                    # Skip monitoring, just execute function
                    return func(self, *args, **kwargs)
            else:
                # No monitoring, just execute function
                return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


class FastMonitoringEngine:
    """High-performance monitoring engine with sampling."""
    
    def __init__(self, sampling_strategy: SamplingStrategy = SamplingStrategy.DISABLED):
        self._performance_monitor = PerformanceMonitor(sampling_strategy)
        self._initialized = sampling_strategy != SamplingStrategy.DISABLED
    
    def initialize(self):
        """Initialize monitoring engine."""
        self._initialized = True
    
    def is_initialized(self) -> bool:
        """Check if monitoring engine is initialized."""
        return self._initialized
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self._performance_monitor.get_metrics()
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self._performance_monitor.reset_metrics()


# Global monitoring configuration
_global_monitoring_strategy: SamplingStrategy = SamplingStrategy.DISABLED


def set_global_monitoring_strategy(strategy: SamplingStrategy):
    """Set global monitoring strategy for all loggers."""
    global _global_monitoring_strategy
    _global_monitoring_strategy = strategy


def get_global_monitoring_strategy() -> SamplingStrategy:
    """Get global monitoring strategy."""
    return _global_monitoring_strategy


def create_fast_monitoring_engine(strategy: SamplingStrategy = SamplingStrategy.DISABLED) -> FastMonitoringEngine:
    """Create a fast monitoring engine with specified strategy."""
    engine = FastMonitoringEngine(strategy)
    if strategy != SamplingStrategy.DISABLED:
        engine.initialize()
    return engine
