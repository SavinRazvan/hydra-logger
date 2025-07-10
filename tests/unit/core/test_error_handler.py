"""
Tests for comprehensive error handling system.

This module tests the error tracking and logging functionality
to ensure all errors are properly captured and logged.
"""

import os
import sys
import pytest
import tempfile
import shutil
import threading
import time
from unittest.mock import patch, MagicMock
from pathlib import Path

from hydra_logger import HydraLogger
from hydra_logger.core.error_handler import (
    ErrorTracker, get_error_tracker, track_error, track_hydra_error,
    track_configuration_error, track_runtime_error, error_context,
    get_error_stats, clear_error_stats, close_error_tracker
)
from hydra_logger.core.exceptions import (
    HydraLoggerError, ConfigurationError, ValidationError, PluginError
)


class TestErrorHandling:
    """Test comprehensive error handling functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_test_error_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.error_log_file = os.path.join(self.test_logs_dir, "hydra_logs.log")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)
        # Clear global error tracker
        close_error_tracker()

    def test_error_tracker_initialization(self):
        """Test error tracker initialization."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        assert tracker is not None
        assert hasattr(tracker, 'error_logger')
        assert tracker.log_file == self.error_log_file
        tracker.close()

    def test_error_tracker_file_creation(self):
        """Test that error log file is created."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        assert os.path.exists(self.error_log_file)
        tracker.close()

    def test_track_general_error(self):
        """Test tracking general errors."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Create a test error
        test_error = ValueError("Test error message")
        
        # Track the error
        tracker.track_error(
            error_type="test_error",
            error=test_error,
            context={"test_key": "test_value"},
            component="test_component",
            severity="error"
        )
        
        # Check that error was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "TEST_ERROR" in content
            assert "Test error message" in content
            assert "[TEST_COMPONENT]" in content
        
        tracker.close()

    def test_track_hydra_error(self):
        """Test tracking Hydra-Logger specific errors."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Create a Hydra-Logger error
        hydra_error = HydraLoggerError("Hydra logger test error")
        
        # Track the error
        tracker.track_hydra_error(hydra_error, "test_component")
        
        # Check that error was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "HYDRA_LOGGER_ERROR" in content
            assert "Hydra logger test error" in content
        
        tracker.close()

    def test_track_configuration_error(self):
        """Test tracking configuration errors."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Create a configuration error
        config_error = ConfigurationError("Configuration test error")
        
        # Track the error
        tracker.track_configuration_error(config_error, {"config_key": "config_value"})
        
        # Check that error was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "CONFIGURATION_ERROR" in content
            assert "Configuration test error" in content
            assert "config_key=config_value" in content
        
        tracker.close()

    def test_track_validation_error(self):
        """Test tracking validation errors."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Create a validation error
        validation_error = ValidationError("Validation test error")
        
        # Track the error
        tracker.track_validation_error(validation_error, {"validation_key": "validation_value"})
        
        # Check that error was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "VALIDATION_ERROR" in content
            assert "Validation test error" in content
        
        tracker.close()

    def test_track_plugin_error(self):
        """Test tracking plugin errors."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Create a plugin error
        plugin_error = PluginError("Plugin test error")
        
        # Track the error
        tracker.track_plugin_error(plugin_error, "test_plugin", {"plugin_key": "plugin_value"})
        
        # Check that error was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "PLUGIN_ERROR" in content
            assert "Plugin test error" in content
            assert "plugin_name=test_plugin" in content
        
        tracker.close()

    def test_track_runtime_error(self):
        """Test tracking runtime errors."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Create a runtime error
        runtime_error = RuntimeError("Runtime test error")
        
        # Track the error
        tracker.track_runtime_error(runtime_error, "test_component", {"runtime_key": "runtime_value"})
        
        # Check that error was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "RUNTIME_ERROR" in content
            assert "Runtime test error" in content
            assert "runtime_key=runtime_value" in content
        
        tracker.close()

    def test_error_context_manager(self):
        """Test error context manager."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Test successful operation
        with error_context("test_context", "successful_operation"):
            pass  # No error
        
        # Test operation with error
        with pytest.raises(ValueError):
            with error_context("test_context", "failing_operation"):
                raise ValueError("Context test error")
        
        # Check that error was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "CONTEXT_ERROR" in content
            assert "Context test error" in content
        
        tracker.close()

    def test_error_statistics(self):
        """Test error statistics tracking."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Track some errors
        tracker.track_error("type1", ValueError("Error 1"))
        tracker.track_error("type1", ValueError("Error 2"))
        tracker.track_error("type2", RuntimeError("Error 3"))
        
        # Get statistics
        stats = tracker.get_error_stats()
        
        assert stats["total_errors"] == 3
        assert stats["error_types"]["type1"] == 2
        assert stats["error_types"]["type2"] == 1
        assert "error_log_file" in stats
        
        tracker.close()

    def test_clear_error_statistics(self):
        """Test clearing error statistics."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Track some errors
        tracker.track_error("test_type", ValueError("Test error"))
        
        # Clear statistics
        tracker.clear_error_stats()
        
        # Check that statistics are cleared
        stats = tracker.get_error_stats()
        assert stats["total_errors"] == 0
        assert len(stats["error_types"]) == 0
        
        tracker.close()

    def test_global_error_tracker(self):
        """Test global error tracker functionality."""
        # Get global tracker
        tracker = get_error_tracker()
        assert tracker is not None
        
        # Track error using global functions
        track_error("global_test", ValueError("Global test error"))
        
        # Get error stats
        stats = get_error_stats()
        assert stats["total_errors"] >= 1
        
        # Clear stats
        clear_error_stats()
        stats = get_error_stats()
        assert stats["total_errors"] == 0

    def test_logger_with_error_handling(self):
        """Test that logger properly handles errors."""
        logger = HydraLogger()
        
        # Test normal logging
        logger.info("Test message")
        
        # Test logging with error handling
        try:
            # This should not raise an exception due to error handling
            logger.info("Message with potential error")
        except Exception as e:
            pytest.fail(f"Logger should handle errors gracefully: {e}")
        
        # Get error stats
        error_stats = logger.get_error_stats()
        assert isinstance(error_stats, dict)
        
        logger.close()

    def test_logger_error_context(self):
        """Test logger with error context."""
        logger = HydraLogger()
        
        # Test logging within error context
        with error_context("test_component", "test_operation"):
            logger.info("Message in error context")
        
        # This should work without raising exceptions
        assert True
        
        logger.close()

    def test_thread_safety(self):
        """Test error tracker thread safety."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        def worker():
            """Worker function to test thread safety."""
            for i in range(10):
                tracker.track_error(f"thread_error_{i}", ValueError(f"Thread error {i}"))
                time.sleep(0.01)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all errors were tracked
        stats = tracker.get_error_stats()
        assert stats["total_errors"] >= 50  # 5 threads * 10 errors each
        
        tracker.close()

    def test_error_logger_fallback(self):
        """Test error logger fallback when file logging fails."""
        # Try to create tracker with invalid path
        with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
            tracker = ErrorTracker(log_file="/invalid/path/hydra_logs.log")
            assert tracker.error_logger is None
        
        # Test that tracker doesn't crash when error_logger is None
        tracker.track_error("test", ValueError("Test error"))
        # Should not raise exception

    def test_exception_hooks(self):
        """Test that exception hooks are properly installed."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Test that original hooks are saved
        assert hasattr(tracker, '_original_excepthook')
        assert hasattr(tracker, '_original_thread_excepthook')
        
        # Test that custom hooks are installed
        assert sys.excepthook != tracker._original_excepthook
        assert threading.excepthook != tracker._original_thread_excepthook
        
        tracker.close()

    def test_error_tracker_cleanup(self):
        """Test error tracker cleanup."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Track some errors
        tracker.track_error("cleanup_test", ValueError("Cleanup test error"))
        
        # Close tracker
        tracker.close()
        
        # Verify that original hooks are restored
        assert sys.excepthook == tracker._original_excepthook
        assert threading.excepthook == tracker._original_thread_excepthook

    def test_error_severity_levels(self):
        """Test different error severity levels."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Test different severity levels
        severities = ["debug", "info", "warning", "error", "critical"]
        
        for severity in severities:
            tracker.track_error(
                f"severity_test_{severity}",
                ValueError(f"Severity {severity} test"),
                severity=severity
            )
        
        # Check that all severities were logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            for severity in severities:
                assert f"SEVERITY_TEST_{severity.upper()}" in content
        
        tracker.close()

    def test_error_context_information(self):
        """Test that error context information is properly captured."""
        tracker = ErrorTracker(log_file=self.error_log_file)
        
        # Track error with rich context
        context = {
            "user_id": 12345,
            "operation": "database_query",
            "timestamp": time.time(),
            "nested": {"key": "value"}
        }
        
        tracker.track_error(
            "context_test",
            ValueError("Context test error"),
            context=context,
            component="database",
            severity="error"
        )
        
        # Check that context was logged
        with open(self.error_log_file, 'r') as f:
            content = f.read()
            assert "user_id=12345" in content
            assert "operation=database_query" in content
            assert "database" in content
        
        tracker.close() 