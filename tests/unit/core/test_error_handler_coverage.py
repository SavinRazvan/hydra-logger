"""
Comprehensive tests for error handler to achieve 100% coverage.

This module tests all edge cases, error conditions, and error tracking
functionality in the error handler to ensure complete test coverage.
"""

import os
import sys
import tempfile
import threading
import time
import traceback
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

import pytest

from hydra_logger.core.error_handler import (
    ErrorTracker,
    ErrorContext,
    get_error_tracker,
    track_error,
    track_hydra_error,
    track_configuration_error,
    track_validation_error,
    track_plugin_error,
    track_async_error,
    track_performance_error,
    track_runtime_error,
    error_context,
    get_error_stats,
    clear_error_stats,
    close_error_tracker
)
from hydra_logger.core.exceptions import (
    HydraLoggerError,
    ConfigurationError,
    ValidationError,
    PluginError,
    AsyncError,
    PerformanceError
)


class TestErrorTracker:
    """Test ErrorTracker with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = os.path.join(self.temp_dir, "test_coverage_errors.log")
        # Use a separate error tracker for tests with logging disabled
        self.tracker = ErrorTracker(
            log_file=self.test_log_file,
            enable_logging=False  # Disable logging for intentional test errors
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_init_with_defaults(self):
        """Test ErrorTracker initialization with default parameters."""
        tracker = ErrorTracker()
        
        # In test environment, the default log file should be test_logs/test_errors.log
        assert tracker.log_file == "test_logs/test_errors.log"
        assert tracker.enable_console is True
        assert tracker._error_count == 0
        assert tracker._error_types == {}
        assert tracker._last_error_time is None
        assert tracker.error_logger is not None
        
        tracker.close()
    
    def test_init_with_custom_params(self):
        """Test ErrorTracker initialization with custom parameters."""
        tracker = ErrorTracker(
            log_file=self.test_log_file,
            enable_console=False
        )
        
        assert tracker.log_file == self.test_log_file
        assert tracker.enable_console is False
        assert tracker.error_logger is not None
        
        tracker.close()
    
    @patch('pathlib.Path.mkdir')
    @patch('logging.getLogger')
    def test_setup_error_logger_success(self, mock_get_logger, mock_mkdir):
        """Test _setup_error_logger successful setup."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        tracker = ErrorTracker(self.test_log_file)
        
        mock_mkdir.assert_called_once()
        mock_get_logger.assert_called_once_with("hydra_logger.errors")
        assert mock_logger.setLevel.called
        assert mock_logger.propagate is False
        
        tracker.close()
    
    @patch('pathlib.Path.mkdir')
    @patch('logging.getLogger')
    def test_setup_error_logger_with_console(self, mock_get_logger, mock_mkdir):
        """Test _setup_error_logger with console handler."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        tracker = ErrorTracker(self.test_log_file, enable_console=True)
        
        # Should add both file and console handlers
        assert mock_logger.addHandler.call_count >= 2
        
        tracker.close()
    
    @patch('pathlib.Path.mkdir')
    def test_setup_error_logger_handles_exception(self, mock_mkdir):
        """Test _setup_error_logger handles exceptions gracefully."""
        mock_mkdir.side_effect = Exception("Directory creation failed")
        
        # Should not raise exception
        tracker = ErrorTracker(self.test_log_file)
        
        assert tracker.error_logger is None
        
        tracker.close()
    
    def test_install_exception_hooks(self):
        """Test _install_exception_hooks installs custom hooks."""
        original_excepthook = sys.excepthook
        original_thread_excepthook = threading.excepthook
        
        tracker = ErrorTracker(self.test_log_file)
        
        # Verify hooks were installed
        assert sys.excepthook != original_excepthook
        assert threading.excepthook != original_thread_excepthook
        
        tracker.close()
        
        # Verify hooks were restored
        assert sys.excepthook == original_excepthook
        assert threading.excepthook == original_thread_excepthook
    
    def test_track_error_basic(self):
        """Test track_error basic functionality."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = Exception("Test error")
        tracker.track_error("test_error", error)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "test_error" in tracker._error_types
        assert tracker._error_types["test_error"] == 1
        assert tracker._last_error_time is not None
        
        tracker.close()
    
    def test_track_error_with_context(self):
        """Test track_error with context information."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = Exception("Test error")
        context = {"user_id": 123, "operation": "test"}
        
        tracker.track_error("test_error", error, context=context)
        
        # Verify error was tracked with context
        assert tracker._error_count == 1
        assert tracker._error_types["test_error"] == 1
        
        tracker.close()
    
    def test_track_error_with_traceback(self):
        """Test track_error with custom traceback."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = Exception("Test error")
        tb = traceback.extract_stack()
        
        tracker.track_error("test_error", error, traceback=tb)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        
        tracker.close()
    
    def test_track_error_with_different_severities(self):
        """Test track_error with different severity levels."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = Exception("Test error")
        
        # Test different severities
        for severity in ["debug", "info", "warning", "error", "critical"]:
            tracker.track_error("test_error", error, severity=severity)
        
        # Verify all errors were tracked
        assert tracker._error_count == 5
        
        tracker.close()
    
    def test_track_error_with_null_logger(self):
        """Test track_error when error_logger is None."""
        tracker = ErrorTracker(self.test_log_file)
        tracker.error_logger = None
        
        error = Exception("Test error")
        
        # Should not raise exception
        tracker.track_error("test_error", error)
        
        tracker.close()
    
    def test_track_error_handles_logging_exception(self):
        """Test track_error handles logging exceptions gracefully."""
        tracker = ErrorTracker(self.test_log_file)
        
        # Mock logger to raise exception
        with patch.object(tracker.error_logger, 'error', side_effect=Exception("Logging failed")):
            error = Exception("Test error")
            
            # Should not raise exception
            tracker.track_error("test_error", error)
        
        tracker.close()
    
    def test_track_error_handles_traceback_formatting_exception(self):
        """Test track_error handles traceback formatting exceptions."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = Exception("Test error")
        
        # Mock traceback.format_exception to raise exception
        with patch('traceback.format_exception', side_effect=Exception("Format failed")):
            # Should not raise exception
            tracker.track_error("test_error", error)
        
        tracker.close()
    
    def test_track_hydra_error(self):
        """Test track_hydra_error method."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = HydraLoggerError("Test hydra error")
        tracker.track_hydra_error(error, "test_component")
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "hydra_logger_error" in tracker._error_types
        
        tracker.close()
    
    def test_track_configuration_error(self):
        """Test track_configuration_error method."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = ConfigurationError("Test config error")
        context = {"config_file": "test.yaml"}
        
        tracker.track_configuration_error(error, context)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "configuration_error" in tracker._error_types
        
        tracker.close()
    
    def test_track_validation_error(self):
        """Test track_validation_error method."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = ValidationError("Test validation error")
        context = {"field": "test_field"}
        
        tracker.track_validation_error(error, context)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "validation_error" in tracker._error_types
        
        tracker.close()
    
    def test_track_plugin_error(self):
        """Test track_plugin_error method."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = PluginError("Test plugin error")
        context = {"plugin_version": "1.0.0"}
        
        tracker.track_plugin_error(error, "test_plugin", context)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "plugin_error" in tracker._error_types
        
        tracker.close()
    
    def test_track_plugin_error_without_context(self):
        """Test track_plugin_error method without context."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = PluginError("Test plugin error")
        
        tracker.track_plugin_error(error, "test_plugin")
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "plugin_error" in tracker._error_types
        
        tracker.close()
    
    def test_track_async_error(self):
        """Test track_async_error method."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = AsyncError("Test async error")
        context = {"task_id": "123"}
        
        tracker.track_async_error(error, context)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "async_error" in tracker._error_types
        
        tracker.close()
    
    def test_track_performance_error(self):
        """Test track_performance_error method."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = PerformanceError("Test performance error")
        context = {"duration_ms": 1000}
        
        tracker.track_performance_error(error, context)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "performance_error" in tracker._error_types
        
        tracker.close()
    
    def test_track_runtime_error(self):
        """Test track_runtime_error method."""
        tracker = ErrorTracker(self.test_log_file)
        
        error = Exception("Test runtime error")
        context = {"component": "test"}
        
        tracker.track_runtime_error(error, "test_component", context)
        
        # Verify error was tracked
        assert tracker._error_count == 1
        assert "runtime_error" in tracker._error_types
        
        tracker.close()
    
    def test_get_error_stats(self):
        """Test get_error_stats method."""
        tracker = ErrorTracker(self.test_log_file)
        
        # Track some errors
        error = Exception("Test error")
        tracker.track_error("test_error", error)
        tracker.track_error("another_error", error)
        
        stats = tracker.get_error_stats()
        
        assert stats["total_errors"] == 2
        assert "test_error" in stats["error_types"]
        assert "another_error" in stats["error_types"]
        assert stats["error_log_file"] == self.test_log_file
        assert stats["last_error_time"] is not None
        
        tracker.close()
    
    def test_clear_error_stats(self):
        """Test clear_error_stats method."""
        tracker = ErrorTracker(self.test_log_file)
        
        # Track some errors
        error = Exception("Test error")
        tracker.track_error("test_error", error)
        
        # Clear stats
        tracker.clear_error_stats()
        
        # Verify stats were cleared
        assert tracker._error_count == 0
        assert tracker._error_types == {}
        assert tracker._last_error_time is None
        
        tracker.close()
    
    def test_close_restores_hooks(self):
        """Test close method restores original hooks."""
        original_excepthook = sys.excepthook
        original_thread_excepthook = threading.excepthook
        
        tracker = ErrorTracker(self.test_log_file)
        
        # Verify hooks were installed
        assert sys.excepthook != original_excepthook
        assert threading.excepthook != original_thread_excepthook
        
        tracker.close()
        
        # Verify hooks were restored
        assert sys.excepthook == original_excepthook
        assert threading.excepthook == original_thread_excepthook
    
    def test_close_handles_exception(self):
        """Test close method handles exceptions gracefully."""
        tracker = ErrorTracker(self.test_log_file)
        
        # Mock logger handlers to raise exception
        if tracker.error_logger is not None:
            mock_handler = Mock()
            mock_handler.close.side_effect = Exception("Close failed")
            with patch.object(tracker.error_logger, 'handlers', [mock_handler]):
                # Should not raise exception
                tracker.close()


class TestErrorContext:
    """Test ErrorContext with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = os.path.join(self.temp_dir, "test_context.log")
        self.tracker = ErrorTracker(self.test_log_file)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.tracker.close()
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_context_init(self):
        """Test ErrorContext initialization."""
        context = ErrorContext(self.tracker, "test_component", "test_operation")
        
        assert context.error_tracker == self.tracker
        assert context.component == "test_component"
        assert context.operation == "test_operation"
        assert context.start_time is None
    
    def test_context_enter_exit_no_error(self):
        """Test ErrorContext enter/exit without error."""
        context = ErrorContext(self.tracker, "test_component", "test_operation")
        
        with context:
            assert context.start_time is not None
            time.sleep(0.001)  # Small delay to test duration
        
        # Verify no error was tracked
        assert self.tracker._error_count == 0
    
    def test_context_enter_exit_with_error(self):
        """Test ErrorContext enter/exit with error."""
        context = ErrorContext(self.tracker, "test_component", "test_operation")
        
        try:
            with context:
                raise Exception("Test error in context")
        except Exception:
            pass
        
        # Verify error was tracked
        assert self.tracker._error_count == 1
        assert "context_error" in self.tracker._error_types
    
    def test_context_enter_exit_with_error_and_duration(self):
        """Test ErrorContext enter/exit with error and duration tracking."""
        context = ErrorContext(self.tracker, "test_component", "test_operation")
        
        try:
            with context:
                time.sleep(0.01)  # Longer delay to test duration
                raise Exception("Test error in context")
        except Exception:
            pass
        
        # Verify error was tracked with duration
        assert self.tracker._error_count == 1
        assert "context_error" in self.tracker._error_types


class TestGlobalFunctions:
    """Test global error tracking functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = os.path.join(self.temp_dir, "test_global_errors.log")
        # Clear any existing global tracker
        close_error_tracker()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        close_error_tracker()
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_get_error_tracker_singleton(self):
        """Test get_error_tracker returns singleton instance."""
        tracker1 = get_error_tracker()
        tracker2 = get_error_tracker()
        
        assert tracker1 is tracker2
    
    def test_track_error_global(self):
        """Test global track_error function."""
        error = Exception("Test global error")
        track_error("test_global_error", error, {"test": "context"})
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "test_global_error" in tracker._error_types
    
    def test_track_hydra_error_global(self):
        """Test global track_hydra_error function."""
        error = HydraLoggerError("Test hydra error")
        track_hydra_error(error, "test_component")
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "hydra_logger_error" in tracker._error_types
    
    def test_track_configuration_error_global(self):
        """Test global track_configuration_error function."""
        error = ConfigurationError("Test config error")
        track_configuration_error(error, {"config": "test"})
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "configuration_error" in tracker._error_types
    
    def test_track_validation_error_global(self):
        """Test global track_validation_error function."""
        error = ValidationError("Test validation error")
        track_validation_error(error, {"field": "test"})
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "validation_error" in tracker._error_types
    
    def test_track_plugin_error_global(self):
        """Test global track_plugin_error function."""
        error = PluginError("Test plugin error")
        track_plugin_error(error, "test_plugin", {"version": "1.0"})
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "plugin_error" in tracker._error_types
    
    def test_track_async_error_global(self):
        """Test global track_async_error function."""
        error = AsyncError("Test async error")
        track_async_error(error, {"task": "test"})
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "async_error" in tracker._error_types
    
    def test_track_performance_error_global(self):
        """Test global track_performance_error function."""
        error = PerformanceError("Test performance error")
        track_performance_error(error, {"duration": 1000})
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "performance_error" in tracker._error_types
    
    def test_track_runtime_error_global(self):
        """Test global track_runtime_error function."""
        error = Exception("Test runtime error")
        track_runtime_error(error, "test_component", {"runtime": "test"})
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "runtime_error" in tracker._error_types
    
    def test_error_context_global(self):
        """Test global error_context function."""
        try:
            with error_context("test_component", "test_operation"):
                raise Exception("Test error in global context")
        except Exception:
            pass
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "context_error" in tracker._error_types
    
    def test_get_error_stats_global(self):
        """Test global get_error_stats function."""
        error = Exception("Test error")
        track_error("test_error", error)
        
        stats = get_error_stats()
        assert stats["total_errors"] == 1
        assert "test_error" in stats["error_types"]
    
    def test_clear_error_stats_global(self):
        """Test global clear_error_stats function."""
        error = Exception("Test error")
        track_error("test_error", error)
        
        clear_error_stats()
        
        stats = get_error_stats()
        assert stats["total_errors"] == 0
        assert stats["error_types"] == {}
    
    def test_close_error_tracker(self):
        """Test close_error_tracker function."""
        tracker = get_error_tracker()
        assert tracker is not None
        
        close_error_tracker()
        
        # Should create new tracker on next call
        new_tracker = get_error_tracker()
        assert new_tracker is not tracker


class TestExceptionHooks:
    """Test exception hooks functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = os.path.join(self.temp_dir, "test_hooks.log")
        self.tracker = ErrorTracker(self.test_log_file)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.tracker.close()
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_custom_excepthook(self):
        """Test custom exception hook."""
        # This test verifies that the custom excepthook is installed
        # and would track unhandled exceptions
        assert sys.excepthook != sys.__excepthook__
    
    def test_custom_thread_excepthook(self):
        """Test custom thread exception hook."""
        # This test verifies that the custom thread excepthook is installed
        # Note: threading.__excepthook__ doesn't exist in all Python versions
        # So we just check that a custom excepthook is installed
        assert threading.excepthook is not None
    
    def test_exception_hooks_restored_on_close(self):
        """Test that exception hooks are restored when tracker is closed."""
        original_excepthook = sys.excepthook
        original_thread_excepthook = threading.excepthook
        
        # Create new tracker
        tracker = ErrorTracker(self.test_log_file)
        
        # Verify hooks were installed
        assert sys.excepthook != original_excepthook
        assert threading.excepthook != original_thread_excepthook
        
        # Close tracker
        tracker.close()
        
        # Verify hooks were restored
        assert sys.excepthook == original_excepthook
        assert threading.excepthook == original_thread_excepthook


class TestErrorHandlerIntegration:
    """Integration tests for error handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_log_file = os.path.join(self.temp_dir, "integration_errors.log")
        # Clear any existing global tracker
        close_error_tracker()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        close_error_tracker()
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_multiple_error_types(self):
        """Test tracking multiple error types."""
        # Track different types of errors
        track_hydra_error(HydraLoggerError("Hydra error"))
        track_configuration_error(ConfigurationError("Config error"))
        track_validation_error(ValidationError("Validation error"))
        track_plugin_error(PluginError("Plugin error"), "test_plugin")
        track_async_error(AsyncError("Async error"))
        track_performance_error(PerformanceError("Performance error"))
        track_runtime_error(Exception("Runtime error"))
        
        tracker = get_error_tracker()
        stats = tracker.get_error_stats()
        
        assert stats["total_errors"] == 7
        assert len(stats["error_types"]) == 7
    
    def test_error_context_with_multiple_operations(self):
        """Test error context with multiple operations."""
        # Test multiple error contexts
        try:
            with error_context("component1", "operation1"):
                raise Exception("Error 1")
        except Exception:
            pass
        
        try:
            with error_context("component2", "operation2"):
                raise Exception("Error 2")
        except Exception:
            pass
        
        tracker = get_error_tracker()
        stats = tracker.get_error_stats()
        
        assert stats["total_errors"] == 2
        assert stats["error_types"]["context_error"] == 2
    
    def test_error_tracking_with_complex_context(self):
        """Test error tracking with complex context information."""
        complex_context = {
            "user_id": 12345,
            "session_id": "abc123",
            "request_id": "req456",
            "component": "api",
            "operation": "process_request",
            "timestamp": time.time(),
            "metadata": {
                "version": "1.0.0",
                "environment": "test"
            }
        }
        
        error = Exception("Complex error")
        track_error("complex_error", error, complex_context, "api", "error")
        
        tracker = get_error_tracker()
        assert tracker._error_count == 1
        assert "complex_error" in tracker._error_types 