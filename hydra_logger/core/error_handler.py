"""
Comprehensive Error Handler for Hydra-Logger

This module provides robust error handling and logging for all Hydra-Logger components.
It captures internal errors, runtime errors, configuration errors, and other issues
to help with debugging and monitoring.
"""

import os
import sys
import traceback
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
from contextlib import contextmanager
import weakref

from hydra_logger.core.exceptions import (
    HydraLoggerError,
    ConfigurationError,
    ValidationError,
    HandlerError,
    FormatterError,
    AsyncError,
    PluginError,
    DataProtectionError,
    AnalyticsError,
    CompatibilityError,
    PerformanceError
)


class ErrorTracker:
    """
    Comprehensive error tracking and logging system.
    
    Captures all types of errors with detailed context and logs them
    to a dedicated error log file for debugging and monitoring.
    """
    
    def __init__(self, log_file: str = None, enable_console: bool = True, enable_logging: bool = True):
        """
        Initialize error tracker.
        
        Args:
            log_file: Path to error log file (auto-detected if None)
            enable_console: Whether to also log to console
            enable_logging: Whether to actually log errors (can be disabled for tests)
        """
        self.enable_logging = enable_logging
        
        # Auto-detect log file based on environment
        if log_file is None:
            log_file = self._detect_log_file()
        
        self.log_file = log_file
        self.enable_console = enable_console
        self._lock = threading.Lock()
        self._error_count = 0
        self._error_types = {}
        self._last_error_time = None
        self._setup_error_logger()
        self._install_exception_hooks()
    
    def _detect_log_file(self) -> str:
        """Detect appropriate log file based on environment."""
        # Check if we're in a test environment
        if self._is_test_environment():
            return "test_logs/test_errors.log"
        elif self._is_example_environment():
            return "examples/logs/example_errors.log"
        else:
            return "logs/hydra_logs.log"
    
    def _is_test_environment(self) -> bool:
        """Check if we're running in a test environment."""
        import sys
        # Check for pytest, unittest, or test-related environment variables
        return (
            'pytest' in sys.modules or
            'unittest' in sys.modules or
            'PYTEST_CURRENT_TEST' in os.environ or
            'TESTING' in os.environ or
            any('test' in arg.lower() for arg in sys.argv)
        )
    
    def _is_example_environment(self) -> bool:
        """Check if we're running in an example environment."""
        import sys
        # Check if we're running example scripts
        return (
            'examples' in sys.argv[0] if sys.argv else False or
            any('example' in arg.lower() for arg in sys.argv)
        )
    
    def _setup_error_logger(self) -> None:
        """Setup dedicated error logger."""
        try:
            # Ensure log directory exists
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create error logger
            self.error_logger = logging.getLogger("hydra_logger.errors")
            self.error_logger.setLevel(logging.DEBUG)
            
            # Prevent propagation to avoid infinite loops
            self.error_logger.propagate = False
            
            # File handler for error logs
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Create detailed formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.error_logger.addHandler(file_handler)
            
            # Console handler if enabled
            if self.enable_console:
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setLevel(logging.ERROR)
                console_handler.setFormatter(formatter)
                self.error_logger.addHandler(console_handler)
                
        except Exception as e:
            # Fallback to stderr if file logging fails
            print(f"Failed to setup error logger: {e}", file=sys.stderr)
            self.error_logger = None
    
    def _install_exception_hooks(self) -> None:
        """Install global exception hooks to catch unhandled exceptions."""
        self._original_excepthook = sys.excepthook
        self._original_thread_excepthook = threading.excepthook
        
        def custom_excepthook(exc_type, exc_value, exc_traceback):
            """Custom exception hook for unhandled exceptions."""
            self.track_error(
                error_type="unhandled_exception",
                error=exc_value,
                traceback=exc_traceback,
                context={
                    "exc_type": exc_type.__name__,
                    "source": "global_exception_hook"
                }
            )
            # Call original hook
            self._original_excepthook(exc_type, exc_value, exc_traceback)
        
        def custom_thread_excepthook(args):
            """Custom thread exception hook."""
            self.track_error(
                error_type="thread_exception",
                error=args.exc_value,
                traceback=args.exc_traceback,
                context={
                    "thread_name": args.thread.name,
                    "thread_id": args.thread.ident,
                    "source": "thread_exception_hook"
                }
            )
            # Call original hook
            self._original_thread_excepthook(args)
        
        sys.excepthook = custom_excepthook
        threading.excepthook = custom_thread_excepthook
    
    def track_error(
        self,
        error_type: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        traceback: Optional[Any] = None,
        component: str = "unknown",
        severity: str = "error"
    ) -> None:
        """
        Track an error with detailed context.
        
        Args:
            error_type: Type of error (e.g., 'configuration', 'runtime', 'plugin')
            error: The exception object
            context: Additional context information
            traceback: Traceback object (if not provided, current traceback is used)
            component: Component where error occurred
            severity: Error severity (debug, info, warning, error, critical)
        """
        # Skip logging if disabled
        if not self.enable_logging:
            return
        
        if self.error_logger is None:
            return
        
        try:
            with self._lock:
                self._error_count += 1
                self._last_error_time = time.time()
                
                # Track error types
                if error_type not in self._error_types:
                    self._error_types[error_type] = 0
                self._error_types[error_type] += 1
            
            # Prepare error message
            error_msg = f"[{component.upper()}] {error_type.upper()}: {str(error)}"
            
            # Add context information
            if context:
                context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
                error_msg += f" | Context: {context_str}"
            
            # Get traceback
            if traceback is None:
                traceback = sys.exc_info()[2]
            
            if traceback:
                try:
                    tb_lines = traceback.format_exception(type(error), error, traceback)
                    error_msg += f"\nTraceback:\n{''.join(tb_lines)}"
                except Exception:
                    # Fallback if traceback formatting fails
                    error_msg += f"\nTraceback: {str(traceback)}"
            
            # Log based on severity
            log_method = getattr(self.error_logger, severity.lower(), self.error_logger.error)
            log_method(error_msg)
            
        except Exception as e:
            # Fallback error logging
            print(f"Error in error tracker: {e}", file=sys.stderr)
    
    def track_hydra_error(self, error: HydraLoggerError, component: str = "core") -> None:
        """Track Hydra-Logger specific errors."""
        self.track_error(
            error_type="hydra_logger_error",
            error=error,
            component=component,
            severity="error"
        )
    
    def track_configuration_error(self, error: ConfigurationError, context: Optional[Dict[str, Any]] = None) -> None:
        """Track configuration-related errors."""
        self.track_error(
            error_type="configuration_error",
            error=error,
            context=context,
            component="config",
            severity="error"
        )
    
    def track_validation_error(self, error: ValidationError, context: Optional[Dict[str, Any]] = None) -> None:
        """Track validation errors."""
        self.track_error(
            error_type="validation_error",
            error=error,
            context=context,
            component="validation",
            severity="warning"
        )
    
    def track_plugin_error(self, error: PluginError, plugin_name: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Track plugin-related errors."""
        context = context or {}
        context["plugin_name"] = plugin_name
        
        self.track_error(
            error_type="plugin_error",
            error=error,
            context=context,
            component="plugin",
            severity="error"
        )
    
    def track_async_error(self, error: AsyncError, context: Optional[Dict[str, Any]] = None) -> None:
        """Track async-related errors."""
        self.track_error(
            error_type="async_error",
            error=error,
            context=context,
            component="async",
            severity="error"
        )
    
    def track_performance_error(self, error: PerformanceError, context: Optional[Dict[str, Any]] = None) -> None:
        """Track performance-related errors."""
        self.track_error(
            error_type="performance_error",
            error=error,
            context=context,
            component="performance",
            severity="warning"
        )
    
    def track_runtime_error(self, error: Exception, component: str = "runtime", context: Optional[Dict[str, Any]] = None) -> None:
        """Track general runtime errors."""
        self.track_error(
            error_type="runtime_error",
            error=error,
            context=context,
            component=component,
            severity="error"
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self._lock:
            return {
                "total_errors": self._error_count,
                "error_types": self._error_types.copy(),
                "last_error_time": self._last_error_time,
                "error_log_file": self.log_file
            }
    
    def clear_error_stats(self) -> None:
        """Clear error statistics."""
        with self._lock:
            self._error_count = 0
            self._error_types.clear()
            self._last_error_time = None
    
    def close(self) -> None:
        """Close error tracker and restore original hooks."""
        try:
            # Restore original exception hooks
            sys.excepthook = self._original_excepthook
            threading.excepthook = self._original_thread_excepthook
            
            # Close logger handlers
            if hasattr(self, 'error_logger') and self.error_logger:
                for handler in self.error_logger.handlers[:]:
                    handler.close()
                    self.error_logger.removeHandler(handler)
                    
        except Exception as e:
            print(f"Error closing error tracker: {e}", file=sys.stderr)


class ErrorContext:
    """
    Context manager for tracking errors in specific code blocks.
    """
    
    def __init__(self, error_tracker: ErrorTracker, component: str, operation: str):
        """
        Initialize error context.
        
        Args:
            error_tracker: Error tracker instance
            component: Component name
            operation: Operation being performed
        """
        self.error_tracker = error_tracker
        self.component = component
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """Enter error context."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit error context and track any errors."""
        if exc_type is not None:
            context = {
                "operation": self.operation,
                "duration_ms": (time.time() - self.start_time) * 1000 if self.start_time else 0
            }
            
            self.error_tracker.track_error(
                error_type="context_error",
                error=exc_val,
                context=context,
                traceback=exc_tb,
                component=self.component,
                severity="error"
            )
        
        return False  # Don't suppress the exception


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None
_error_tracker_lock = threading.Lock()


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance."""
    global _error_tracker
    if _error_tracker is None:
        # For tests, we want error tracking to work but use test-specific log files
        # The enable_logging parameter controls whether errors are actually logged
        # In tests, we want to track errors but use test log files
        _error_tracker = ErrorTracker()
    return _error_tracker


def track_error(
    error_type: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    component: str = "unknown",
    severity: str = "error"
) -> None:
    """Track an error using the global error tracker."""
    tracker = get_error_tracker()
    tracker.track_error(error_type, error, context, None, component, severity)


def track_hydra_error(error: HydraLoggerError, component: str = "core") -> None:
    """Track Hydra-Logger specific error."""
    tracker = get_error_tracker()
    tracker.track_hydra_error(error, component)


def track_configuration_error(error: ConfigurationError, context: Optional[Dict[str, Any]] = None) -> None:
    """Track configuration error."""
    tracker = get_error_tracker()
    tracker.track_configuration_error(error, context)


def track_validation_error(error: ValidationError, context: Optional[Dict[str, Any]] = None) -> None:
    """Track validation error."""
    tracker = get_error_tracker()
    tracker.track_validation_error(error, context)


def track_plugin_error(error: PluginError, plugin_name: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Track plugin error."""
    tracker = get_error_tracker()
    tracker.track_plugin_error(error, plugin_name, context)


def track_async_error(error: AsyncError, context: Optional[Dict[str, Any]] = None) -> None:
    """Track async error."""
    tracker = get_error_tracker()
    tracker.track_async_error(error, context)


def track_performance_error(error: PerformanceError, context: Optional[Dict[str, Any]] = None) -> None:
    """Track performance error."""
    tracker = get_error_tracker()
    tracker.track_performance_error(error, context)


def track_runtime_error(error: Exception, component: str = "runtime", context: Optional[Dict[str, Any]] = None) -> None:
    """Track runtime error."""
    tracker = get_error_tracker()
    tracker.track_runtime_error(error, component, context)


@contextmanager
def error_context(component: str, operation: str):
    """Context manager for tracking errors in code blocks."""
    tracker = get_error_tracker()
    with ErrorContext(tracker, component, operation):
        yield


def get_error_stats() -> Dict[str, Any]:
    """Get error statistics."""
    tracker = get_error_tracker()
    return tracker.get_error_stats()


def clear_error_stats() -> None:
    """Clear error statistics."""
    tracker = get_error_tracker()
    tracker.clear_error_stats()


def close_error_tracker() -> None:
    """Close the global error tracker."""
    global _error_tracker
    if _error_tracker:
        _error_tracker.close()
        _error_tracker = None 