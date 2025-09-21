"""
Test helper utilities for Hydra-Logger.

Provides common helper functions for testing.
"""

import os
import sys
import tempfile
import shutil
from typing import Any, Dict, List, Optional
from contextlib import contextmanager


def setup_test_environment():
    """Set up test environment."""
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def cleanup_test_environment():
    """Clean up test environment."""
    # Remove any temporary files
    temp_dir = tempfile.gettempdir()
    for item in os.listdir(temp_dir):
        if item.startswith('hydra_logger_test_'):
            item_path = os.path.join(temp_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)


@contextmanager
def temporary_directory():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix='hydra_logger_test_')
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@contextmanager
def temporary_file(suffix='.log', content=''):
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        yield temp_file
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def suppress_output():
    """Suppress stdout and stderr for testing."""
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    class SuppressOutput:
        def __init__(self):
            self.stdout = io.StringIO()
            self.stderr = io.StringIO()
        
        def __enter__(self):
            self.old_stdout = sys.stdout
            self.old_stderr = sys.stderr
            sys.stdout = self.stdout
            sys.stderr = self.stderr
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr
    
    return SuppressOutput()


def capture_logs(logger, level='INFO'):
    """Capture logs from a logger for testing."""
    import logging
    from io import StringIO
    
    class LogCapture:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = getattr(logging, level.upper())
            self.stream = StringIO()
            self.handler = logging.StreamHandler(self.stream)
            self.handler.setLevel(self.level)
            self.logger.addHandler(self.handler)
        
        def get_logs(self):
            return self.stream.getvalue()
        
        def clear(self):
            self.stream.seek(0)
            self.stream.truncate(0)
        
        def close(self):
            self.logger.removeHandler(self.handler)
            self.handler.close()
    
    return LogCapture(logger, level)


def assert_performance(actual: float, expected: float, tolerance: float = 0.1):
    """Assert performance is within tolerance."""
    if actual < expected * (1 - tolerance):
        raise AssertionError(f"Performance {actual} is below expected {expected} (tolerance: {tolerance})")


def assert_memory_usage(actual_mb: float, max_mb: float):
    """Assert memory usage is within limits."""
    if actual_mb > max_mb:
        raise AssertionError(f"Memory usage {actual_mb:.2f}MB exceeds limit {max_mb}MB")


def assert_object_pool_stats(stats: Dict[str, Any], min_hit_rate: float = 0.8):
    """Assert object pool statistics are acceptable."""
    hit_rate = stats.get('hit_rate', 0)
    if hit_rate < min_hit_rate:
        raise AssertionError(f"Object pool hit rate {hit_rate:.2f} is below minimum {min_hit_rate}")


def generate_test_data(count: int, message_template: str = "Test message {i}") -> List[str]:
    """Generate test data for performance testing."""
    return [message_template.format(i=i) for i in range(count)]


def measure_execution_time(func, *args, **kwargs) -> Dict[str, Any]:
    """Measure function execution time."""
    import time
    import psutil
    
    start_time = time.perf_counter()
    start_memory = psutil.Process().memory_info().rss
    
    try:
        result = func(*args, **kwargs)
        success = True
        error = None
    except Exception as e:
        result = None
        success = False
        error = str(e)
    
    end_time = time.perf_counter()
    end_memory = psutil.Process().memory_info().rss
    
    return {
        'result': result,
        'execution_time': end_time - start_time,
        'memory_usage': end_memory - start_memory,
        'success': success,
        'error': error
    }


def create_test_logger_config(enable_features: bool = False) -> Dict[str, Any]:
    """Create test logger configuration."""
    return {
        'enable_security': enable_features,
        'enable_sanitization': enable_features,
        'enable_plugins': enable_features,
        'enable_monitoring': enable_features,
        'buffer_size': 100,
        'flush_interval': 0.1
    }


def validate_logger_interface(logger, required_methods: List[str] = None):
    """Validate logger implements required interface."""
    if required_methods is None:
        required_methods = ['log', 'debug', 'info', 'warning', 'error', 'critical', 'close']
    
    missing_methods = []
    for method in required_methods:
        if not hasattr(logger, method):
            missing_methods.append(method)
    
    if missing_methods:
        raise AssertionError(f"Logger missing required methods: {missing_methods}")


def check_async_methods(logger, async_methods: List[str] = None):
    """Check if logger has async methods."""
    if async_methods is None:
        async_methods = ['log', 'debug', 'info', 'warning', 'error', 'critical', 'aclose']
    
    import asyncio
    
    async_methods_found = []
    for method in async_methods:
        if hasattr(logger, method):
            method_obj = getattr(logger, method)
            if asyncio.iscoroutinefunction(method_obj):
                async_methods_found.append(method)
    
    return async_methods_found
