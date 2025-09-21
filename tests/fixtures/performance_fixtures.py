"""
Performance test fixtures for Hydra-Logger.

Provides fixtures and utilities for performance testing.
"""

import pytest
import time
import asyncio
from typing import Dict, Any, List, Callable
from contextlib import contextmanager


@pytest.fixture
def performance_timer():
    """Timer fixture for performance measurements."""
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return PerformanceTimer()


@pytest.fixture
def performance_benchmark():
    """Benchmark fixture for performance testing."""
    class PerformanceBenchmark:
        def __init__(self):
            self.results = []
        
        def measure(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
            """Measure function execution time and performance."""
            start_time = time.perf_counter()
            start_memory = self._get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
            
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            
            measurement = {
                'function': func.__name__,
                'execution_time': end_time - start_time,
                'memory_usage': end_memory - start_memory,
                'success': success,
                'error': error,
                'timestamp': time.time()
            }
            
            self.results.append(measurement)
            return measurement
        
        def get_average_time(self) -> float:
            """Get average execution time."""
            if not self.results:
                return 0
            return sum(r['execution_time'] for r in self.results) / len(self.results)
        
        def get_max_time(self) -> float:
            """Get maximum execution time."""
            if not self.results:
                return 0
            return max(r['execution_time'] for r in self.results)
        
        def get_min_time(self) -> float:
            """Get minimum execution time."""
            if not self.results:
                return 0
            return min(r['execution_time'] for r in self.results)
        
        def _get_memory_usage(self) -> int:
            """Get current memory usage."""
            try:
                import psutil
                return psutil.Process().memory_info().rss
            except ImportError:
                return 0
    
    return PerformanceBenchmark()


@pytest.fixture
def throughput_measurement():
    """Throughput measurement fixture."""
    class ThroughputMeasurement:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.message_count = 0
        
        def start(self):
            self.start_time = time.perf_counter()
            self.message_count = 0
        
        def increment(self, count: int = 1):
            self.message_count += count
        
        def stop(self):
            self.end_time = time.perf_counter()
            return self.get_throughput()
        
        def get_throughput(self) -> float:
            """Get messages per second."""
            if self.start_time and self.end_time and self.message_count > 0:
                duration = self.end_time - self.start_time
                return self.message_count / duration
            return 0
        
        def get_duration(self) -> float:
            """Get total duration in seconds."""
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return ThroughputMeasurement()


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        'min_messages_per_second': 10000,
        'max_execution_time': 1.0,
        'max_memory_usage_mb': 50,
        'min_object_pool_hit_rate': 0.8,
        'max_test_duration': 300
    }


@pytest.fixture
def load_test_scenarios():
    """Load test scenarios for stress testing."""
    return {
        'light_load': {
            'message_count': 1000,
            'concurrent_workers': 1,
            'duration_seconds': 10
        },
        'medium_load': {
            'message_count': 10000,
            'concurrent_workers': 4,
            'duration_seconds': 30
        },
        'heavy_load': {
            'message_count': 100000,
            'concurrent_workers': 8,
            'duration_seconds': 60
        },
        'extreme_load': {
            'message_count': 1000000,
            'concurrent_workers': 16,
            'duration_seconds': 300
        }
    }


@contextmanager
def performance_context(measurement_name: str, benchmark: Any):
    """Context manager for performance measurements."""
    start_time = time.perf_counter()
    start_memory = benchmark._get_memory_usage()
    
    try:
        yield
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        end_time = time.perf_counter()
        end_memory = benchmark._get_memory_usage()
        
        measurement = {
            'name': measurement_name,
            'execution_time': end_time - start_time,
            'memory_usage': end_memory - start_memory,
            'success': success,
            'error': error,
            'timestamp': time.time()
        }
        
        benchmark.results.append(measurement)


@pytest.fixture
def async_performance_timer():
    """Async timer fixture for performance measurements."""
    class AsyncPerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        async def start(self):
            self.start_time = time.perf_counter()
        
        async def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return AsyncPerformanceTimer()
