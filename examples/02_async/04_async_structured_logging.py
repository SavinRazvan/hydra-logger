#!/usr/bin/env python3
"""
Async Structured Logging Example

This example demonstrates structured logging capabilities with:
- JSON, XML, and custom formats
- Correlation IDs and request tracing
- Context management and injection
- Rich metadata and context fields
"""

import asyncio
import time
from hydra_logger.async_hydra.async_logger import AsyncHydraLogger


async def json_structured_logging():
    """Demonstrate JSON structured logging."""
    print("\n=== JSON Structured Logging ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Basic JSON structured log
    await logger.log_structured(
        layer="API",
        level="INFO",
        message="User authentication successful",
        correlation_id="req-123",
        context={
            "user_id": "user-456",
            "method": "oauth",
            "provider": "google",
            "ip_address": "192.168.1.100"
        },
        format="json"
    )
    
    # Error with context
    await logger.log_structured(
        layer="ERROR",
        level="ERROR",
        message="Database connection failed",
        correlation_id="req-124",
        context={
            "database": "postgres",
            "operation": "user_creation",
            "retry_count": 3,
            "error_code": "CONNECTION_TIMEOUT"
        },
        format="json"
    )
    
    # Performance metric
    await logger.log_structured(
        layer="PERFORMANCE",
        level="INFO",
        message="Database query executed",
        correlation_id="req-125",
        context={
            "query": "SELECT * FROM users WHERE id = ?",
            "duration_ms": 45.2,
            "rows_returned": 1,
            "cache_hit": False
        },
        format="json"
    )


async def xml_structured_logging():
    """Demonstrate XML structured logging."""
    print("\n=== XML Structured Logging ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Security event in XML
    await logger.log_structured(
        layer="SECURITY",
        level="WARNING",
        message="Failed login attempt",
        correlation_id="req-126",
        context={
            "ip": "192.168.1.101",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "attempt_count": 5,
            "username": "admin",
            "reason": "invalid_password"
        },
        format="xml"
    )
    
    # Audit trail in XML
    await logger.log_structured(
        layer="AUDIT",
        level="INFO",
        message="User permissions modified",
        correlation_id="req-127",
        context={
            "admin_user": "admin-123",
            "target_user": "user-789",
            "permissions_added": ["read", "write"],
            "permissions_removed": ["delete"],
            "reason": "role_change"
        },
        format="xml"
    )


async def dict_structured_logging():
    """Demonstrate dict structured logging."""
    print("\n=== Dict Structured Logging ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Business event
    await logger.log_structured(
        layer="BUSINESS",
        level="INFO",
        message="Order placed successfully",
        correlation_id="req-128",
        context={
            "order_id": "ORD-2024-001",
            "customer_id": "CUST-456",
            "total_amount": 299.99,
            "currency": "USD",
            "payment_method": "credit_card",
            "items_count": 3
        },
        format="dict"
    )
    
    # System health check
    await logger.log_structured(
        layer="SYSTEM",
        level="INFO",
        message="Health check completed",
        correlation_id="req-129",
        context={
            "service": "user-service",
            "status": "healthy",
            "response_time_ms": 12.5,
            "memory_usage_mb": 256.8,
            "cpu_usage_percent": 15.2
        },
        format="dict"
    )


async def correlation_context_example():
    """Demonstrate correlation context management."""
    print("\n=== Correlation Context Management ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Set correlation context for a request
    logger.set_correlation_context("req-130", user_id="user-456", session_id="session-789")
    
    # All logs in this context will have the correlation ID
    await logger.info("API", "Processing user request")
    await logger.info("DATABASE", "Executing user query")
    await logger.info("CACHE", "Checking user cache")
    await logger.info("EXTERNAL", "Calling payment service")
    
    # Clear context
    logger.clear_correlation_context()
    await logger.info("SYSTEM", "Request context cleared")


async def context_manager_example():
    """Demonstrate context managers."""
    print("\n=== Context Managers ===")
    
    logger = AsyncHydraLogger(test_mode=True)
    
    # Correlation context manager
    with logger.correlation_context("req-131", user_id="user-789"):
        await logger.info("API", "Request started")
        
        # Nested logger context
        with logger.logger_context(session_id="session-abc", operation="data_processing"):
            await logger.info("PROCESSING", "Processing user data")
            await logger.info("VALIDATION", "Validating input data")
            await logger.info("TRANSFORMATION", "Transforming data format")
        
        await logger.info("API", "Request completed")
    
    # Context is automatically cleared
    await logger.info("SYSTEM", "Outside context")


async def main():
    """Run all structured logging examples."""
    print("🚀 Async Structured Logging Examples")
    print("=" * 50)
    
    await json_structured_logging()
    await xml_structured_logging()
    await dict_structured_logging()
    await correlation_context_example()
    await context_manager_example()
    
    print("\n✅ All structured logging examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 