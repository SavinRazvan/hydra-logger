#!/usr/bin/env python3
"""
Comprehensive Error Handling Example

This example demonstrates how to use Hydra-Logger's comprehensive error handling
system to track all types of errors (internal, runtime, configuration, etc.)
and save them to examples/logs/hydra_logs.log for debugging and monitoring.
"""

import os
import time
import threading
from hydra_logger import (
    HydraLogger, 
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
    HydraLoggerError, ConfigurationError, ValidationError, PluginError, AsyncError, PerformanceError
)
from hydra_logger.core.error_handler import ErrorTracker


def demo_basic_error_tracking():
    """Demonstrate basic error tracking functionality."""
    
    print("🔍 Basic Error Tracking Demo")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Create logger with separate error log file
    logger = HydraLogger()
    
    # Create a separate error tracker for examples
    example_error_tracker = ErrorTracker(
        log_file="examples/logs/example_errors.log",
        enable_logging=True  # Enable for demonstration
    )
    
    # Track different types of errors using the example tracker
    print("\n1️⃣ Tracking General Errors:")
    example_error_tracker.track_error("test_error", ValueError("This is a test error"))
    example_error_tracker.track_error("runtime_error", RuntimeError("Runtime error occurred"))
    
    print("\n2️⃣ Tracking Hydra-Logger Specific Errors:")
    example_error_tracker.track_hydra_error(HydraLoggerError("Hydra logger specific error"))
    
    print("\n3️⃣ Tracking Configuration Errors:")
    example_error_tracker.track_configuration_error(
        ConfigurationError("Configuration error"),
        {"config_file": "config.yaml", "line": 42}
    )
    
    print("\n4️⃣ Tracking Validation Errors:")
    example_error_tracker.track_validation_error(
        ValidationError("Validation failed"),
        {"field": "email", "value": "invalid-email"}
    )
    
    # Get error statistics from the example tracker
    stats = example_error_tracker.get_error_stats()
    print(f"\n📊 Error Statistics: {stats}")
    
    # Clean up
    example_error_tracker.close()
    logger.close()


def demo_error_context():
    """Demonstrate error context manager."""
    
    print("\n🔍 Error Context Manager Demo")
    print("=" * 50)
    
    # Create a separate error tracker for examples
    example_error_tracker = ErrorTracker(
        log_file="examples/logs/example_errors.log",
        enable_logging=True
    )
    
    # Use error context for operations
    with error_context("database", "user_query"):
        # This operation will be tracked
        print("Performing database query...")
        time.sleep(0.1)
    
    # Use error context with potential error
    try:
        with error_context("api", "external_call"):
            print("Making external API call...")
            raise ConnectionError("Network timeout")
    except ConnectionError:
        print("Error was caught and tracked!")
    
    # Get updated statistics
    stats = example_error_tracker.get_error_stats()
    print(f"Updated Error Statistics: {stats}")
    
    example_error_tracker.close()


def demo_thread_safety():
    """Demonstrate thread-safe error tracking."""
    
    print("\n🔍 Thread Safety Demo")
    print("=" * 50)
    
    # Create a separate error tracker for examples
    example_error_tracker = ErrorTracker(
        log_file="examples/logs/example_errors.log",
        enable_logging=True
    )
    
    def worker(worker_id):
        """Worker function that generates errors."""
        for i in range(5):
            example_error_tracker.track_error(f"thread_error_{worker_id}", ValueError(f"Thread {worker_id} error {i}"))
            time.sleep(0.01)
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("All threads completed!")
    
    # Check final statistics
    stats = example_error_tracker.get_error_stats()
    print(f"Final Error Statistics: {stats}")
    
    example_error_tracker.close()


def demo_logger_error_handling():
    """Demonstrate how logger handles errors internally."""
    
    print("\n🔍 Logger Error Handling Demo")
    print("=" * 50)
    
    # Create logger with error handling
    logger = HydraLogger()
    
    # Normal logging (should work)
    logger.info("Normal log message")
    
    # Log with potential errors (should be handled gracefully)
    try:
        logger.info("Message with potential issues")
        logger.debug("Debug message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        print("✅ All logging operations completed successfully!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Get error statistics from logger
    error_stats = logger.get_error_stats()
    print(f"Logger Error Statistics: {error_stats}")
    
    logger.close()


def demo_error_statistics():
    """Demonstrate error statistics functionality."""
    
    print("\n🔍 Error Statistics Demo")
    print("=" * 50)
    
    # Create a separate error tracker for examples
    example_error_tracker = ErrorTracker(
        log_file="examples/logs/example_errors.log",
        enable_logging=True
    )
    
    # Clear previous statistics
    example_error_tracker.clear_error_stats()
    
    # Track various errors
    example_error_tracker.track_error("type_a", ValueError("Error A1"))
    example_error_tracker.track_error("type_a", ValueError("Error A2"))
    example_error_tracker.track_error("type_b", RuntimeError("Error B1"))
    example_error_tracker.track_error("type_c", TypeError("Error C1"))
    
    # Get statistics
    stats = example_error_tracker.get_error_stats()
    print(f"Error Statistics: {stats}")
    
    # Clear statistics
    example_error_tracker.clear_error_stats()
    stats = example_error_tracker.get_error_stats()
    print(f"After Clearing: {stats}")
    
    example_error_tracker.close()


def demo_error_severity_levels():
    """Demonstrate different error severity levels."""
    
    print("\n🔍 Error Severity Levels Demo")
    print("=" * 50)
    
    # Create a separate error tracker for examples
    example_error_tracker = ErrorTracker(
        log_file="examples/logs/example_errors.log",
        enable_logging=True
    )
    
    # Track errors with different severity levels
    severities = ["debug", "info", "warning", "error", "critical"]
    
    for severity in severities:
        example_error_tracker.track_error(
            f"severity_{severity}",
            ValueError(f"Test error with {severity} severity"),
            severity=severity
        )
        print(f"Tracked {severity} level error")
    
    print("All severity levels tracked!")
    
    example_error_tracker.close()


def demo_comprehensive_error_scenarios():
    """Demonstrate comprehensive error scenarios."""
    
    print("\n🔍 Comprehensive Error Scenarios Demo")
    print("=" * 50)
    
    # Create a separate error tracker for examples
    example_error_tracker = ErrorTracker(
        log_file="examples/logs/example_errors.log",
        enable_logging=True
    )
    
    # Scenario 1: Plugin error
    example_error_tracker.track_plugin_error(
        PluginError("Plugin initialization failed"),
        "custom_plugin",
        {"plugin_version": "1.0.0", "operation": "init"}
    )
    
    # Scenario 2: Async error
    example_error_tracker.track_async_error(
        AsyncError("Async operation timeout"),
        {"timeout_ms": 5000, "operation": "http_request"}
    )
    
    # Scenario 3: Performance error
    example_error_tracker.track_performance_error(
        PerformanceError("Performance threshold exceeded"),
        {"threshold": "100ms", "actual": "150ms", "operation": "database_query"}
    )
    
    # Scenario 4: Runtime error with rich context
    example_error_tracker.track_runtime_error(
        ConnectionError("Database connection failed"),
        "database",
        {
            "host": "db.example.com",
            "port": 5432,
            "user": "app_user",
            "retry_count": 3,
            "last_error": "Connection timeout"
        }
    )
    
    print("All error scenarios tracked!")
    
    example_error_tracker.close()


def main():
    """Run comprehensive error handling demo."""
    
    print("🚀 Hydra-Logger Comprehensive Error Handling Demo")
    print("=" * 60)
    print("This demo shows how to track all types of errors in Hydra-Logger.")
    print("All errors are logged to examples/logs/example_errors.log")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_error_tracking()
        demo_error_context()
        demo_thread_safety()
        demo_logger_error_handling()
        demo_error_statistics()
        demo_error_severity_levels()
        demo_comprehensive_error_scenarios()
        
        print("\n✅ All error handling demos completed successfully!")
        print("📁 Check examples/logs/example_errors.log for detailed error logs")
        
        # Final statistics from a fresh tracker
        final_tracker = ErrorTracker(
            log_file="examples/logs/example_errors.log",
            enable_logging=True
        )
        final_stats = final_tracker.get_error_stats()
        print(f"📊 Final Error Statistics: {final_stats}")
        final_tracker.close()
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        # No need to close global tracker since we're using separate ones
        pass


if __name__ == "__main__":
    main() 