#!/usr/bin/env python3
"""
Comprehensive Error Handling Example

This example demonstrates how to use Hydra-Logger's comprehensive error handling
system to track all types of errors (internal, runtime, configuration, etc.)
and save them to logs/hydra_logs.log for debugging and monitoring.
"""

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


def demo_basic_error_tracking():
    """Demonstrate basic error tracking functionality."""
    
    print("🔍 Basic Error Tracking Demo")
    print("=" * 50)
    
    # Create logger
    logger = HydraLogger()
    
    # Track different types of errors
    print("\n1️⃣ Tracking General Errors:")
    track_error("test_error", ValueError("This is a test error"))
    track_error("runtime_error", RuntimeError("Runtime error occurred"))
    
    print("\n2️⃣ Tracking Hydra-Logger Specific Errors:")
    track_hydra_error(HydraLoggerError("Hydra logger specific error"))
    
    print("\n3️⃣ Tracking Configuration Errors:")
    track_configuration_error(
        ConfigurationError("Configuration error"),
        {"config_file": "config.yaml", "line": 42}
    )
    
    print("\n4️⃣ Tracking Validation Errors:")
    track_validation_error(
        ValidationError("Validation failed"),
        {"field": "email", "value": "invalid-email"}
    )
    
    # Get error statistics
    stats = get_error_stats()
    print(f"\n📊 Error Statistics: {stats}")
    
    logger.close()


def demo_error_context():
    """Demonstrate error context manager."""
    
    print("\n🔍 Error Context Manager Demo")
    print("=" * 50)
    
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
    stats = get_error_stats()
    print(f"Updated Error Statistics: {stats}")


def demo_thread_safety():
    """Demonstrate thread-safe error tracking."""
    
    print("\n🔍 Thread Safety Demo")
    print("=" * 50)
    
    def worker(worker_id):
        """Worker function that generates errors."""
        for i in range(5):
            track_error(f"thread_error_{worker_id}", ValueError(f"Thread {worker_id} error {i}"))
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
    stats = get_error_stats()
    print(f"Final Error Statistics: {stats}")


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
    
    # Clear previous statistics
    clear_error_stats()
    
    # Track various errors
    track_error("type_a", ValueError("Error A1"))
    track_error("type_a", ValueError("Error A2"))
    track_error("type_b", RuntimeError("Error B1"))
    track_error("type_c", TypeError("Error C1"))
    
    # Get statistics
    stats = get_error_stats()
    print(f"Error Statistics: {stats}")
    
    # Clear statistics
    clear_error_stats()
    stats = get_error_stats()
    print(f"After Clearing: {stats}")


def demo_error_severity_levels():
    """Demonstrate different error severity levels."""
    
    print("\n🔍 Error Severity Levels Demo")
    print("=" * 50)
    
    # Track errors with different severity levels
    severities = ["debug", "info", "warning", "error", "critical"]
    
    for severity in severities:
        track_error(
            f"severity_{severity}",
            ValueError(f"Test error with {severity} severity"),
            severity=severity
        )
        print(f"Tracked {severity} level error")
    
    print("All severity levels tracked!")


def demo_comprehensive_error_scenarios():
    """Demonstrate comprehensive error scenarios."""
    
    print("\n🔍 Comprehensive Error Scenarios Demo")
    print("=" * 50)
    
    # Scenario 1: Plugin error
    track_plugin_error(
        PluginError("Plugin initialization failed"),
        "custom_plugin",
        {"plugin_version": "1.0.0", "operation": "init"}
    )
    
    # Scenario 2: Async error
    track_async_error(
        AsyncError("Async operation timeout"),
        {"timeout_ms": 5000, "operation": "http_request"}
    )
    
    # Scenario 3: Performance error
    track_performance_error(
        PerformanceError("Performance threshold exceeded"),
        {"threshold": "100ms", "actual": "150ms", "operation": "database_query"}
    )
    
    # Scenario 4: Runtime error with rich context
    track_runtime_error(
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


def main():
    """Run comprehensive error handling demo."""
    
    print("🚀 Hydra-Logger Comprehensive Error Handling Demo")
    print("=" * 60)
    print("This demo shows how to track all types of errors in Hydra-Logger.")
    print("All errors are logged to logs/hydra_logs.log")
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
        print("📁 Check logs/hydra_logs.log for detailed error logs")
        
        # Final statistics
        final_stats = get_error_stats()
        print(f"📊 Final Error Statistics: {final_stats}")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
    finally:
        # Clean up
        close_error_tracker()


if __name__ == "__main__":
    main() 