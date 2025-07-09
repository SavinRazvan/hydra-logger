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
from pathlib import Path
from unittest.mock import MagicMock, patch

from hydra_logger import HydraLogger
from hydra_logger.async_hydra import AsyncHydraLogger
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


class BaseAsyncLoggerTest(BaseLoggerTest):
    """Base class for async logger tests."""
    
    @pytest.fixture(autouse=True)
    async def async_setup(self):
        """Setup async test environment."""
        self.async_logger = AsyncHydraLogger()
        await self.async_logger.initialize()
        yield
        await self.async_logger.close()


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
    """Provide configuration with plugins enabled."""
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


# Coverage tracking fixtures
@pytest.fixture(scope="session")
def coverage_tracker():
    """Session-wide coverage tracking."""
    # Disabled for now to prevent hanging issues
    yield None


@pytest.fixture(autouse=False)  # Changed from autouse=True to False
def track_coverage(coverage_tracker):
    """Track coverage for each test."""
    if coverage_tracker:
        coverage_tracker.start()
    yield
    if coverage_tracker:
        coverage_tracker.stop()


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Provide performance monitoring for tests."""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_start = None
            self.memory_end = None
        
        def start(self):
            """Start performance monitoring."""
            self.start_time = time.time()
            try:
                import psutil
                self.memory_start = psutil.Process().memory_info().rss
            except ImportError:
                self.memory_start = 0
        
        def stop(self):
            """Stop performance monitoring."""
            self.end_time = time.time()
            try:
                import psutil
                self.memory_end = psutil.Process().memory_info().rss
            except ImportError:
                self.memory_end = 0
        
        def get_duration(self):
            """Get test duration in seconds."""
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
        
        def get_memory_usage(self):
            """Get memory usage in bytes."""
            if self.memory_start and self.memory_end:
                return self.memory_end - self.memory_start
            return 0
    
    monitor = PerformanceMonitor()
    monitor.start()
    yield monitor
    monitor.stop()


# Mock fixtures for testing
@pytest.fixture
def mock_file_handler():
    """Provide mock file handler for testing."""
    with patch('hydra_logger.core.logger.BufferedFileHandler') as mock:
        mock.return_value.emit.return_value = None
        yield mock


@pytest.fixture
def mock_console_handler():
    """Provide mock console handler for testing."""
    with patch('hydra_logger.core.logger.logging.StreamHandler') as mock:
        mock.return_value.emit.return_value = None
        yield mock


@pytest.fixture
def mock_security_validator():
    """Provide mock security validator for testing."""
    with patch('hydra_logger.core.logger.SecurityValidator') as mock:
        validator = MagicMock()
        validator.validate_message.return_value = True
        mock.return_value = validator
        yield mock


@pytest.fixture
def mock_data_sanitizer():
    """Provide mock data sanitizer for testing."""
    with patch('hydra_logger.core.logger.DataSanitizer') as mock:
        sanitizer = MagicMock()
        sanitizer.sanitize_message.return_value = "sanitized_message"
        mock.return_value = sanitizer
        yield mock


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_log_config(**overrides):
        """Create standard log configuration for testing."""
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
        """Create various test messages."""
        return [
            "Simple message",
            "Message with special chars: !@#$%^&*()",
            "Unicode message: 你好世界",
            "Very long message " * 100,
            "",  # Empty message
            None  # None message
        ]
    
    @staticmethod
    def create_error_scenarios():
        """Create various error scenarios for testing."""
        return [
            {"config": None, "expected_error": "ConfigurationError"},
            {"config": {}, "expected_error": None},
            {"config": {"invalid": "config"}, "expected_error": "ConfigurationError"},
            {"config": {"layers": {}}, "expected_error": None},
        ]


# Export test data factory as fixture
@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory


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


# Test categories for organization
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (component interaction)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance tests (throughput, memory)"
    )
    config.addinivalue_line(
        "markers", "security: Security tests (validation, sanitization)"
    )
    config.addinivalue_line(
        "markers", "asyncio: Async tests (async functionality)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (time-consuming)"
    )


# Test collection hooks for organization
def pytest_collection_modifyitems(config, items):
    """Modify test collection for better organization."""
    for item in items:
        # Mark tests based on file path
        if "test_core_logger" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_async" in item.nodeid:
            item.add_marker(pytest.mark.asyncio)
        elif "test_security" in item.nodeid:
            item.add_marker(pytest.mark.security)
        elif "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Mark slow tests
        if "comprehensive" in item.nodeid or "stress" in item.nodeid:
            item.add_marker(pytest.mark.slow)