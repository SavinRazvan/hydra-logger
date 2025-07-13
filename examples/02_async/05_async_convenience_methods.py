#!/usr/bin/env python3
"""
Async Convenience Methods Example

This example demonstrates convenience methods for common logging scenarios.
Shows how to use AsyncHydraLogger for HTTP requests, user actions, and errors.
"""

import asyncio
import time
from hydra_logger.async_hydra import AsyncHydraLogger


async def http_request_logging():
    """Demonstrate HTTP request logging."""
    print("=== HTTP Request Logging ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate HTTP request logging
    request_id = "req-12345"
    user_id = "user-67890"
    
    await logger.info("HTTP", f"Request started - ID: {request_id}, User: {user_id}")
    await logger.info("HTTP", f"Request method: GET, Path: /api/users/{user_id}")
    await logger.info("HTTP", f"Request headers: Content-Type=application/json, Authorization=Bearer ***")
    
    # Simulate processing time
    await asyncio.sleep(0.1)
    
    await logger.info("HTTP", f"Response status: 200 OK, Response time: 150ms")
    await logger.info("HTTP", f"Response body size: 2.5KB, Cache hit: false")
    await logger.info("HTTP", f"Request completed - ID: {request_id}")
    
    await logger.aclose()


async def user_action_logging():
    """Demonstrate user action logging."""
    print("\n=== User Action Logging ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate user action logging
    user_id = "user-12345"
    session_id = "session-67890"
    
    await logger.info("USER", f"User {user_id} logged in - Session: {session_id}")
    await logger.info("USER", f"User {user_id} navigated to /dashboard")
    await logger.info("USER", f"User {user_id} updated profile information")
    await logger.info("USER", f"User {user_id} uploaded file: document.pdf (2.3MB)")
    await logger.info("USER", f"User {user_id} shared document with user-67890")
    await logger.info("USER", f"User {user_id} logged out - Session: {session_id}")
    
    await logger.aclose()


async def error_logging_with_context():
    """Demonstrate error logging with context."""
    print("\n=== Error Logging with Context ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate error scenarios with context
    try:
        # Simulate a database error
        await logger.error("DATABASE", "Connection timeout - Database: postgres, Pool: main")
        await logger.error("DATABASE", "Query failed - SQL: SELECT * FROM users WHERE id = ?, Params: [12345]")
        await logger.error("DATABASE", "Retry attempt 1/3 - Backoff: 1s")
        
        # Simulate an API error
        await logger.error("API", "External API call failed - Service: payment-gateway, Endpoint: /charge")
        await logger.error("API", "HTTP 500 Internal Server Error - Response: {'error': 'service_unavailable'}")
        await logger.error("API", "Circuit breaker opened - Service: payment-gateway, Threshold: 5 failures")
        
        # Simulate a validation error
        await logger.error("VALIDATION", "Invalid input data - Field: email, Value: invalid-email, Rule: email_format")
        await logger.error("VALIDATION", "Missing required field - Field: password, Context: user_registration")
        
    except Exception as e:
        await logger.critical("SYSTEM", f"Unexpected error: {e}")
    
    await logger.aclose()


async def performance_logging():
    """Demonstrate performance logging."""
    print("\n=== Performance Logging ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate performance metrics
    await logger.info("PERFORMANCE", "Memory usage: 45% (1.2GB/2.7GB)")
    await logger.info("PERFORMANCE", "CPU usage: 23% (4 cores, 2.4GHz)")
    await logger.info("PERFORMANCE", "Database connections: 15/20 active")
    await logger.info("PERFORMANCE", "Cache hit rate: 78% (1,234 hits, 345 misses)")
    await logger.info("PERFORMANCE", "Average response time: 125ms (p95: 250ms)")
    await logger.info("PERFORMANCE", "Requests per second: 150 (peak: 200)")
    
    await logger.aclose()


async def context_injection_example():
    """Demonstrate context injection in logging."""
    print("\n=== Context Injection Example ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate context injection
    request_context = {
        "request_id": "req-abc123",
        "user_id": "user-xyz789",
        "session_id": "session-def456",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    await logger.info("CONTEXT", f"Request context: {request_context}")
    await logger.info("CONTEXT", f"Processing request with ID: {request_context['request_id']}")
    await logger.info("CONTEXT", f"User session: {request_context['session_id']}")
    await logger.info("CONTEXT", f"Client IP: {request_context['ip_address']}")
    
    await logger.aclose()


async def nested_context_example():
    """Demonstrate nested context logging."""
    print("\n=== Nested Context Example ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate nested context
    await logger.info("OUTER", "Starting outer operation")
    
    # Inner context 1
    await logger.info("INNER1", "Starting inner operation 1")
    await logger.info("INNER1", "Processing step 1.1")
    await logger.info("INNER1", "Processing step 1.2")
    await logger.info("INNER1", "Completed inner operation 1")
    
    # Inner context 2
    await logger.info("INNER2", "Starting inner operation 2")
    await logger.info("INNER2", "Processing step 2.1")
    await logger.info("INNER2", "Processing step 2.2")
    await logger.info("INNER2", "Completed inner operation 2")
    
    await logger.info("OUTER", "Completed outer operation")
    
    await logger.aclose()


async def real_world_scenario():
    """Demonstrate a real-world logging scenario."""
    print("\n=== Real-World Scenario ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': True
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Simulate a complete user journey
    user_id = "user-12345"
    order_id = "order-67890"
    
    # User login
    await logger.info("AUTH", f"User {user_id} attempting login")
    await logger.info("AUTH", f"User {user_id} authenticated successfully")
    
    # Browse products
    await logger.info("USER", f"User {user_id} browsing products")
    await logger.info("USER", f"User {user_id} viewed product: laptop-xyz")
    await logger.info("USER", f"User {user_id} added product to cart: laptop-xyz")
    
    # Checkout process
    await logger.info("ORDER", f"User {user_id} started checkout process")
    await logger.info("PAYMENT", f"Processing payment for user {user_id}, order {order_id}")
    await logger.info("PAYMENT", f"Payment successful for order {order_id}, amount: $999.99")
    await logger.info("ORDER", f"Order {order_id} confirmed for user {user_id}")
    
    # Order fulfillment
    await logger.info("FULFILLMENT", f"Order {order_id} queued for processing")
    await logger.info("FULFILLMENT", f"Order {order_id} shipped via FedEx, tracking: 123456789")
    await logger.info("USER", f"User {user_id} received shipping confirmation")
    
    await logger.aclose()


async def main():
    """Run all convenience method examples."""
    print("=== Async Convenience Methods Examples ===")
    print("Demonstrating various convenience methods for common scenarios.\n")
    
    await http_request_logging()
    await user_action_logging()
    await error_logging_with_context()
    await performance_logging()
    await context_injection_example()
    await nested_context_example()
    await real_world_scenario()
    
    print("\n✅ All convenience method examples completed!")
    print("Check the console output above to see the async logs.")


if __name__ == "__main__":
    asyncio.run(main()) 