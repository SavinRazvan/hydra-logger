#!/usr/bin/env python3
"""
Async Convenience Methods Example

This example demonstrates all the convenience methods for common logging patterns:
- HTTP request logging
- User action logging
- Error logging with context
- Performance logging
- Context injection
"""

import asyncio
import time
from hydra_logger.async_hydra.async_logger import AsyncHydraLogger


async def http_request_logging():
    """Demonstrate HTTP request logging."""
    print("\n=== HTTP Request Logging ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Successful GET request
    await logger.log_request(
        request_id="req-200",
        method="GET",
        path="/api/users",
        status_code=200,
        duration=0.15
    )
    
    # Successful POST request
    await logger.log_request(
        request_id="req-201",
        method="POST",
        path="/api/users",
        status_code=201,
        duration=0.25
    )
    
    # Failed request
    await logger.log_request(
        request_id="req-404",
        method="GET",
        path="/api/nonexistent",
        status_code=404,
        duration=0.05
    )
    
    # Slow request
    await logger.log_request(
        request_id="req-500",
        method="POST",
        path="/api/complex-operation",
        status_code=500,
        duration=2.5
    )


async def user_action_logging():
    """Demonstrate user action logging."""
    print("\n=== User Action Logging ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Successful user actions
    await logger.log_user_action(
        user_id="user-123",
        action="login",
        resource="auth",
        success=True
    )
    
    await logger.log_user_action(
        user_id="user-456",
        action="create_account",
        resource="user_management",
        success=True
    )
    
    await logger.log_user_action(
        user_id="user-789",
        action="update_profile",
        resource="profile",
        success=True
    )
    
    # Failed user actions
    await logger.log_user_action(
        user_id="user-999",
        action="login",
        resource="auth",
        success=False
    )
    
    await logger.log_user_action(
        user_id="user-888",
        action="delete_account",
        resource="user_management",
        success=False
    )


async def error_logging_with_context():
    """Demonstrate error logging with context."""
    print("\n=== Error Logging with Context ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Database error
    try:
        raise ConnectionError("Database connection timeout")
    except Exception as e:
        await logger.log_error_with_context(
            error=e,
            layer="ERROR",
            context={
                "operation": "user_creation",
                "database": "postgres",
                "connection_pool": "main",
                "retry_count": 3
            }
        )
    
    # Validation error
    try:
        raise ValueError("Invalid email format")
    except Exception as e:
        await logger.log_error_with_context(
            error=e,
            layer="VALIDATION",
            context={
                "operation": "user_registration",
                "field": "email",
                "value": "invalid-email",
                "validation_rule": "email_format"
            }
        )
    
    # External service error
    try:
        raise TimeoutError("Payment service timeout")
    except Exception as e:
        await logger.log_error_with_context(
            error=e,
            layer="EXTERNAL",
            context={
                "operation": "payment_processing",
                "service": "stripe",
                "endpoint": "/v1/charges",
                "timeout_seconds": 30
            }
        )


async def performance_logging():
    """Demonstrate performance logging."""
    print("\n=== Performance Logging ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Fast operations
    await logger.log_performance(
        operation="cache_lookup",
        duration=0.005,
        layer="PERFORMANCE"
    )
    
    await logger.log_performance(
        operation="database_query",
        duration=0.15,
        layer="PERFORMANCE"
    )
    
    # Normal operations
    await logger.log_performance(
        operation="user_authentication",
        duration=0.5,
        layer="PERFORMANCE"
    )
    
    await logger.log_performance(
        operation="file_upload",
        duration=1.2,
        layer="PERFORMANCE"
    )
    
    # Slow operations (will trigger warnings)
    await logger.log_performance(
        operation="complex_calculation",
        duration=3.5,
        layer="PERFORMANCE"
    )
    
    # Very slow operations (will trigger errors)
    await logger.log_performance(
        operation="data_export",
        duration=8.0,
        layer="PERFORMANCE"
    )


async def context_injection_example():
    """Demonstrate automatic context injection."""
    print("\n=== Context Injection ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Set up correlation context
    logger.set_correlation_context("req-300", user_id="user-300", session_id="session-300")
    
    # Set up logger context
    logger.set_logger_context(environment="production", service="user-service")
    
    # Log with automatic context injection
    await logger.log_with_context(
        layer="API",
        level="INFO",
        message="Processing user request",
        operation="user_authentication",
        custom_field="custom_value"
    )
    
    # Log with additional context
    await logger.log_with_context(
        layer="DATABASE",
        level="INFO",
        message="Executing query",
        table="users",
        query_type="SELECT",
        custom_field="another_value"
    )
    
    # Clear contexts
    logger.clear_correlation_context()
    logger.clear_logger_context()


async def nested_context_example():
    """Demonstrate nested context management."""
    print("\n=== Nested Context Management ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Outer context
    with logger.correlation_context("outer-req", user_id="outer-user"):
        await logger.info("OUTER", "Outer context active")
        
        # Inner context
        with logger.correlation_context("inner-req", session_id="inner-session"):
            await logger.info("INNER", "Inner context active")
            
            # Deepest context
            with logger.logger_context(operation="deep_operation"):
                await logger.info("DEEP", "Deepest context active")
                
                # Use convenience methods in nested context
                await logger.log_user_action(
                    user_id="nested-user",
                    action="nested_action",
                    resource="nested_resource",
                    success=True
                )
            
            await logger.info("INNER", "Back to inner context")
        
        await logger.info("OUTER", "Back to outer context")
    
    await logger.info("SYSTEM", "All contexts cleared")


async def real_world_scenario():
    """Demonstrate a real-world scenario using all features."""
    print("\n=== Real-World Scenario ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Simulate a user login flow
    request_id = "req-login-001"
    
    # Start request
    await logger.log_request(
        request_id=request_id,
        method="POST",
        path="/api/auth/login",
        status_code=200,
        duration=0.8
    )
    
    # Set correlation context
    with logger.correlation_context(request_id, user_id="user-123", session_id="session-456"):
        # User action
        await logger.log_user_action(
            user_id="user-123",
            action="login",
            resource="auth",
            success=True
        )
        
        # Performance metrics
        await logger.log_performance(
            operation="password_verification",
            duration=0.1,
            layer="PERFORMANCE"
        )
        
        await logger.log_performance(
            operation="session_creation",
            duration=0.05,
            layer="PERFORMANCE"
        )
        
        # Context injection
        await logger.log_with_context(
            layer="SECURITY",
            level="INFO",
            message="User login successful",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
    
    print("✅ Real-world scenario completed successfully!")


async def main():
    """Run all convenience method examples."""
    print("🚀 Async Convenience Methods Examples")
    print("=" * 50)
    
    await http_request_logging()
    await user_action_logging()
    await error_logging_with_context()
    await performance_logging()
    await context_injection_example()
    await nested_context_example()
    await real_world_scenario()
    
    print("\n✅ All convenience method examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 