"""
Shared test fixtures and base classes for HydraLogger tests.

This module provides common test infrastructure including:
- Base test classes with common setup/teardown
- Shared fixtures for test data
- Coverage tracking
- Test environment management
"""

import os
import pytest
import tempfile
import shutil
import time
import glob
from pathlib import Path
from unittest.mock import MagicMock, patch

from hydra_logger import HydraLogger
# from hydra_logger.async_hydra import AsyncHydraLogger  # Temporarily disabled during refactor
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


class BaseLoggerTest:
    """Base class for all logger tests with common setup and teardown."""
    
    def setup_method(self):
        """Common setup for all logger tests."""
        self.test_logs_dir = tempfile.mkdtemp(prefix="hydra_test_")
        self.log_file = os.path.join(self.test_logs_dir, "test.log")
        self.error_log_file = os.path.join(self.test_logs_dir, "error.log")
        self.debug_log_file = os.path.join(self.test_logs_dir, "debug.log")
        
        # Store original environment
        self.original_env = os.environ.copy()
        
        # Set test environment variables
        os.environ['HYDRA_LOG_LEVEL'] = 'DEBUG'
        os.environ['HYDRA_LOG_DATE_FORMAT'] = '%Y-%m-%d'
        os.environ['HYDRA_LOG_TIME_FORMAT'] = '%H:%M:%S'
        
    def teardown_method(self):
        """Common cleanup for all logger tests."""
        # Cleanup test files
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir, ignore_errors=True)
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def create_test_config(self, **overrides):
        """Create standard test configuration with overrides."""
        config = {
            "layers": {
                "TEST": {
                    "level": "DEBUG",
                    "destinations": [
                        {"type": "file", "path": self.log_file, "level": "DEBUG"}
                    ]
                },
                "ERROR": {
                    "level": "ERROR",
                    "destinations": [
                        {"type": "file", "path": self.error_log_file, "level": "ERROR"}
                    ]
                }
            }
        }
        config.update(overrides)
        return config
    
    def create_console_config(self):
        """Create configuration with console output."""
        return {
            "layers": {
                "CONSOLE": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "console", "level": "INFO", "color_mode": "always"}
                    ]
                }
            }
        }
    
    def create_multi_destination_config(self):
        """Create configuration with multiple destinations."""
        return {
            "layers": {
                "MULTI": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "console", "level": "INFO"},
                        {"type": "file", "path": self.log_file, "level": "INFO"},
                        {"type": "file", "path": self.debug_log_file, "level": "DEBUG"}
                    ]
                }
            }
        }
    
    def assert_log_file_exists(self, file_path=None):
        """Assert that log file exists and has content."""
        if file_path is None:
            file_path = self.log_file
        
        assert os.path.exists(file_path), f"Log file {file_path} should exist"
        
        with open(file_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, f"Log file {file_path} should have content"
    
    def assert_log_contains(self, expected_text, file_path=None):
        """Assert that log file contains expected text."""
        if file_path is None:
            file_path = self.log_file
        
        with open(file_path, 'r') as f:
            content = f.read()
            assert expected_text in content, f"Log should contain '{expected_text}'"


# class BaseAsyncLoggerTest(BaseLoggerTest):
#     """Base class for async logger tests."""
#     
#     @pytest.fixture(autouse=True)
#     async def async_setup(self):
#         """Setup async test environment."""
#         self.async_logger = AsyncHydraLogger()
#         await self.async_logger.initialize()
#         yield
#         await self.async_logger.close()


# Global cleanup fixture to ensure all test files are cleaned up
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_files():
    """Global cleanup fixture to remove any test files left in root directory."""
    # Clean up before tests
    cleanup_root_test_files()
    yield
    # Clean up after tests
    cleanup_root_test_files()


def cleanup_root_test_files():
    """Clean up any test files and directories that might be in the root directory."""
    root_dir = Path(".")
    
    # File patterns to clean up
    test_file_patterns = [
        "test_*.log",
        "*_test.log", 
        "test_composite.log",
        "test_integration.log",
        "test_e2e_async.log",
        "*.tmp",
        "test_*.txt",
        "test_*.json",
        "test_*.csv",
        "test_*.yaml",
        "test_*.toml",
        "*.test",
        "test_*",
        "*_test",
        "MagicMock*",
        "test_cache*",
        ".test_cache*",
        "pytest_cache*",
        ".pytest_cache*",
        "_tests_logs*",
        "_tests_*",
        "tests_*",
        # Additional patterns to catch files created by tests
        "*.json",
        "*.jsonl", 
        "*.csv",
        "*.backup",
        "{'test': 'data'}*",
        "test.json",
        "test.jsonl",
        "test.csv"
    ]
    
    # Directory patterns to clean up
    test_dir_patterns = [
        "test_*",
        "*_test",
        "test_cache*",
        ".test_cache*",
        "pytest_cache*",
        ".pytest_cache*",
        "MagicMock*",
        "temp_*",
        "tmp_*",
        "_temp_*",
        "_tmp_*",
        "_tests_logs*",
        "_tests_*",
        "tests_*"
    ]
    
    # Clean up files
    for pattern in test_file_patterns:
        for file_path in root_dir.glob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                    print(f"✅ Cleaned up test file: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not clean up file {file_path}: {e}")
    
    # Clean up directories
    for pattern in test_dir_patterns:
        for dir_path in root_dir.glob(pattern):
            try:
                if dir_path.is_dir():
                    shutil.rmtree(dir_path, ignore_errors=True)
                    print(f"✅ Cleaned up test directory: {dir_path}")
            except Exception as e:
                print(f"⚠️  Could not clean up directory {dir_path}: {e}")
    
    # Also clean up any temporary files that might have been created
    try:
        import tempfile
        temp_dir = tempfile.gettempdir()
        for item in os.listdir(temp_dir):
            if item.startswith(('test_', 'hydra_', 'temp_', 'tmp_')):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass  # Ignore errors for temp files
    except Exception:
        pass  # Ignore errors for temp directory access


# Shared fixtures
@pytest.fixture
def test_logs_dir():
    """Provide temporary test logs directory."""
    test_dir = tempfile.mkdtemp(prefix="hydra_test_")
    yield test_dir
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def sample_config():
    """Provide sample configuration for testing."""
    return {
        "layers": {
            "DEFAULT": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "level": "INFO"}
                ]
            },
            "ERROR": {
                "level": "ERROR",
                "destinations": [
                    {"type": "file", "path": "logs/error.log", "level": "ERROR"}
                ]
            }
        }
    }


@pytest.fixture
def test_messages():
    """Provide various test messages."""
    return [
        "Simple test message",
        "Message with special chars: !@#$%^&*()",
        "Unicode message: 你好世界",
        "Very long message " * 50,
        "",  # Empty message
        None,  # None message
        "Message with newlines\nand tabs\tand spaces",
        "Message with quotes: 'single' and \"double\"",
        "Message with brackets: [square] and {curly}",
        "Message with parentheses: (round) and <angle>"
    ]


@pytest.fixture
def performance_config():
    """Provide high-performance configuration for testing."""
    return {
        "layers": {
            "PERF": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "level": "INFO"}
                ]
            }
        }
    }


@pytest.fixture
def security_config():
    """Provide configuration with security features enabled."""
    return {
        "layers": {
            "SECURITY": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "level": "INFO"}
                ]
            }
        }
    }


@pytest.fixture
def plugin_config():
    """Provide configuration with plugin support enabled."""
    return {
        "layers": {
            "PLUGIN": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "level": "INFO"}
                ]
            }
        }
    }


# Coverage tracking
@pytest.fixture(scope="session")
def coverage_tracker():
    """Provide coverage tracking for tests."""
    class CoverageTracker:
        def __init__(self):
            self.covered_modules = set()
            self.covered_functions = set()
    
    return CoverageTracker()


@pytest.fixture(autouse=False)  # Changed from autouse=True to False
def track_coverage(coverage_tracker):
    """Track coverage for each test."""
    yield
    # Coverage tracking logic can be added here if needed


# Performance monitoring
@pytest.fixture
def performance_monitor():
    """Provide performance monitoring for tests."""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_before = None
            self.memory_after = None
        
        def start(self):
            """Start performance monitoring."""
            self.start_time = time.time()
            # Memory monitoring could be added here
        
        def stop(self):
            """Stop performance monitoring."""
            self.end_time = time.time()
            # Memory monitoring could be added here
        
        def get_duration(self):
            """Get test duration."""
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
        
        def get_memory_usage(self):
            """Get memory usage statistics."""
            # Memory monitoring implementation could be added here
            return {"before": self.memory_before, "after": self.memory_after}
    
    monitor = PerformanceMonitor()
    monitor.start()
    yield monitor
    monitor.stop()


# Mock fixtures
@pytest.fixture
def mock_file_handler():
    """Provide mock file handler."""
    with patch('hydra_logger.core.logger.BufferedFileHandler') as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_console_handler():
    """Provide mock console handler."""
    with patch('hydra_logger.core.logger.logging.StreamHandler') as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_security_validator():
    """Provide mock security validator."""
    with patch('hydra_logger.core.logger.SecurityValidator') as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_data_sanitizer():
    """Provide mock data sanitizer."""
    with patch('hydra_logger.core.logger.DataSanitizer') as mock:
        mock.return_value = MagicMock()
        yield mock


# Test data factory
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_log_config(**overrides):
        """Create a log configuration for testing."""
        config = {
            "layers": {
                "DEFAULT": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "console", "level": "INFO"}
                    ]
                }
            }
        }
        config.update(overrides)
        return config
    
    @staticmethod
    def create_test_messages():
        """Create test messages."""
        return [
            "Test message 1",
            "Test message 2",
            "Test message with special chars: !@#$%",
            "Unicode message: 你好世界"
        ]
    
    @staticmethod
    def create_error_scenarios():
        """Create error scenarios for testing."""
        return [
            {"type": "configuration", "error": "Invalid config"},
            {"type": "validation", "error": "Invalid data"},
            {"type": "runtime", "error": "Runtime error"}
        ]


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory()


# Environment management
@pytest.fixture
def test_environment():
    """Provide test environment management."""
    class TestEnvironment:
        def __init__(self):
            self.temp_dir = None
            self.original_env = {}
        
        def setup(self):
            """Setup test environment."""
            self.temp_dir = tempfile.mkdtemp()
            self.original_env = os.environ.copy()
            
            # Set test environment variables
            os.environ['HYDRA_LOG_LEVEL'] = 'DEBUG'
            os.environ['HYDRA_LOG_DATE_FORMAT'] = '%Y-%m-%d'
        
        def teardown(self):
            """Cleanup test environment."""
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            # Restore original environment
            os.environ.clear()
            os.environ.update(self.original_env)
    
    env = TestEnvironment()
    env.setup()
    yield env
    env.teardown()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for HydraLogger tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "async_test: marks tests as async tests"
    )
    
    # Set test environment variables
    os.environ['HYDRA_LOGGER_TEST_MODE'] = '1'
    os.environ['HYDRA_LOGGER_ASYNC_TEST_MODE'] = '1'


def pytest_collection_modifyitems(config, items):
    """Modify test collection for better organization."""
    for item in items:
        # Add default markers based on test location
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "async" in item.nodeid:
            item.add_marker(pytest.mark.async_test)
        
        # Add slow marker for tests that take longer
        if any(keyword in item.nodeid.lower() for keyword in ["performance", "stress", "memory"]):
            item.add_marker(pytest.mark.slow)