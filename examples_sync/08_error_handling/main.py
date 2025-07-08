#!/usr/bin/env python3
"""
08 - Error Handling

This example demonstrates error handling patterns with Hydra-Logger.
Shows how to log different types of errors and handle exceptions.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import traceback
import sys

def simulate_error(error_type):
    """Simulate different types of errors."""
    if error_type == "value_error":
        raise ValueError("Invalid value provided")
    elif error_type == "type_error":
        raise TypeError("Invalid type for operation")
    elif error_type == "file_not_found":
        raise FileNotFoundError("File not found: /path/to/missing/file")
    elif error_type == "connection_error":
        raise ConnectionError("Failed to connect to database")
    elif error_type == "custom_error":
        raise Exception("Custom application error")

def main():
    """Demonstrate error handling patterns."""
    
    print("❌ Error Handling Demo")
    print("=" * 40)
    
    # Create configuration with error handling
    config = LoggingConfig(
        layers={
            "ERRORS": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/errors/application_errors.log",
                        format="text"
                    ),
                    LogDestination(
                        type="console",
                        level="ERROR",
                        format="text"
                    )
                ]
            ),
            "DEBUG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/errors/debug.log",
                        format="text"
                    )
                ]
            ),
            "CRITICAL": LogLayer(
                level="CRITICAL",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/errors/critical.log",
                        format="text"
                    ),
                    LogDestination(
                        type="console",
                        level="CRITICAL",
                        format="text"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🔍 Error Handling Patterns")
    print("-" * 30)
    
    # Pattern 1: Try-catch with detailed logging
    print("\n📝 Pattern 1: Try-catch with detailed logging")
    print("-" * 40)
    
    try:
        # Simulate some operation that might fail
        result = 10 / 0
    except ZeroDivisionError as e:
        logger.error("ERRORS", "Division by zero error",
                    operation="division",
                    dividend=10,
                    divisor=0,
                    error=str(e),
                    error_type=type(e).__name__)
        logger.debug("DEBUG", "Error context",
                    stack_trace=traceback.format_exc(),
                    line_number=traceback.extract_tb(sys.exc_info()[2])[-1].lineno)
    
    # Pattern 2: Logging with context information
    print("\n📝 Pattern 2: Logging with context information")
    print("-" * 40)
    
    try:
        # Simulate file operation
        with open("non_existent_file.txt", "r") as f:
            content = f.read()
    except FileNotFoundError as e:
        logger.error("ERRORS", "File not found error",
                    operation="file_read",
                    file_path="non_existent_file.txt",
                    error=str(e),
                    user_id="123",
                    session_id="abc123")
    
    # Pattern 3: Different error types
    print("\n📝 Pattern 3: Different error types")
    print("-" * 40)
    
    error_types = ["value_error", "type_error", "file_not_found", "connection_error", "custom_error"]
    
    for error_type in error_types:
        try:
            simulate_error(error_type)
        except Exception as e:
            logger.error("ERRORS", f"{error_type.replace('_', ' ').title()} occurred",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        operation="simulation",
                        error_category=error_type)
    
    # Pattern 4: Critical errors
    print("\n📝 Pattern 4: Critical errors")
    print("-" * 40)
    
    try:
        # Simulate critical system failure
        raise SystemError("Critical system failure - database connection lost")
    except SystemError as e:
        logger.critical("CRITICAL", "Critical system error",
                       error=str(e),
                       system_component="database",
                       impact="high",
                       action_required="immediate_restart")
    
    # Pattern 5: Error with recovery attempt
    print("\n📝 Pattern 5: Error with recovery attempt")
    print("-" * 40)
    
    def attempt_operation_with_retry(operation_name, max_retries=3):
        for attempt in range(max_retries):
            try:
                # Simulate operation that might fail
                if attempt == 0:
                    raise ConnectionError("Connection timeout")
                elif attempt == 1:
                    raise ConnectionError("Connection refused")
                else:
                    # Success on third attempt
                    logger.info("ERRORS", f"{operation_name} completed successfully",
                               attempt=attempt + 1,
                               total_attempts=max_retries)
                    return True
            except ConnectionError as e:
                logger.warning("ERRORS", f"{operation_name} failed, retrying",
                             attempt=attempt + 1,
                             max_attempts=max_retries,
                             error=str(e))
                if attempt == max_retries - 1:
                    logger.error("ERRORS", f"{operation_name} failed after all retries",
                               total_attempts=max_retries,
                               final_error=str(e))
                    return False
    
    attempt_operation_with_retry("Database connection")
    
    # Pattern 6: Structured error logging
    print("\n📝 Pattern 6: Structured error logging")
    print("-" * 40)
    
    try:
        # Simulate complex operation
        data = {"user_id": 123, "action": "data_processing"}
        result = data["non_existent_key"]
    except KeyError as e:
        logger.error("ERRORS", "Missing key in data structure",
                    error_type="KeyError",
                    missing_key=str(e),
                    available_keys=list(data.keys()),
                    context="data_processing",
                    user_id=data.get("user_id"),
                    action=data.get("action"))
    
    # Pattern 7: Error aggregation
    print("\n📝 Pattern 7: Error aggregation")
    print("-" * 40)
    
    error_count = 0
    for i in range(5):
        try:
            if i % 2 == 0:
                raise ValueError(f"Error {i}")
        except ValueError as e:
            error_count += 1
            logger.error("ERRORS", f"Error {i} occurred",
                        error_number=i,
                        total_errors=error_count,
                        error_type="ValueError")
    
    logger.info("ERRORS", "Error aggregation completed",
               total_errors=error_count,
               success_rate=f"{((5-error_count)/5)*100:.1f}%")
    
    print("\n✅ Error handling demo completed!")
    print("📝 Check the logs/errors/ directory for error logs")
    
    # Show error statistics
    print("\n📊 Error Statistics:")
    print("-" * 20)
    print(f"• Total error types demonstrated: {len(error_types) + 6}")
    print(f"• Error categories: ValueError, TypeError, FileNotFoundError, ConnectionError, SystemError, KeyError")
    print(f"• Log files: application_errors.log, debug.log, critical.log")

if __name__ == "__main__":
    main() 