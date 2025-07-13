#!/usr/bin/env python3
"""
Async Structured Logging Example

This example demonstrates structured logging with JSON, XML, and correlation IDs.
Shows how to use AsyncHydraLogger for structured logging scenarios.
"""

import asyncio
import json
import uuid
from datetime import datetime
from hydra_logger.async_hydra import AsyncHydraLogger


async def json_structured_logging():
    """Demonstrate JSON structured logging."""
    print("=== JSON Structured Logging ===")
    
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
    
    # Log structured JSON data
    user_data = {
        "user_id": "12345",
        "email": "john.doe@example.com",
        "action": "login",
        "timestamp": datetime.now().isoformat(),
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    await logger.info("USER", json.dumps(user_data))
    
    # Log API request data
    api_data = {
        "request_id": str(uuid.uuid4()),
        "method": "POST",
        "endpoint": "/api/users",
        "status_code": 201,
        "response_time_ms": 150,
        "request_size_bytes": 1024,
        "response_size_bytes": 512
    }
    
    await logger.info("API", json.dumps(api_data))
    
    await logger.aclose()


async def xml_structured_logging():
    """Demonstrate XML structured logging."""
    print("\n=== XML Structured Logging ===")
    
    config = {
        'handlers': [
            {
                'type': 'console',
                'use_colors': False
            }
        ]
    }
    
    logger = AsyncHydraLogger(config)
    await logger.initialize()
    
    # Log structured XML data
    xml_data = f"""<log>
        <timestamp>{datetime.now().isoformat()}</timestamp>
        <level>INFO</level>
        <layer>DATABASE</layer>
        <message>Database connection established</message>
        <details>
            <connection_id>db_conn_001</connection_id>
            <pool_size>10</pool_size>
            <active_connections>3</active_connections>
        </details>
    </log>"""
    
    await logger.info("DATABASE", xml_data)
    
    await logger.aclose()


async def dict_structured_logging():
    """Demonstrate dictionary structured logging."""
    print("\n=== Dictionary Structured Logging ===")
    
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
    
    # Log structured dictionary data
    performance_data = {
        "metric_type": "performance",
        "component": "web_server",
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "cpu_usage_percent": 45.2,
            "memory_usage_mb": 1024,
            "active_connections": 127,
            "requests_per_second": 150.5,
            "average_response_time_ms": 125.3
        },
        "alerts": [
            "High memory usage detected",
            "Response time approaching threshold"
        ]
    }
    
    await logger.info("PERFORMANCE", str(performance_data))
    
    await logger.aclose()


async def correlation_context_example():
    """Demonstrate correlation context in structured logging."""
    print("\n=== Correlation Context Example ===")
    
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
    
    # Generate correlation ID for this request
    correlation_id = str(uuid.uuid4())
    
    # Log messages with correlation context
    await logger.info("REQUEST", f"Request started - Correlation ID: {correlation_id}")
    await logger.info("AUTH", f"Authentication successful - Correlation ID: {correlation_id}")
    await logger.info("DB", f"Database query executed - Correlation ID: {correlation_id}")
    await logger.info("RESPONSE", f"Response sent - Correlation ID: {correlation_id}")
    
    await logger.aclose()


async def context_manager_example():
    """Demonstrate context manager usage."""
    print("\n=== Context Manager Example ===")
    
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
    
    # Simulate a context manager pattern
    try:
        await logger.info("CONTEXT", "Entering critical section")
        # Simulate some work
        await asyncio.sleep(0.1)
        await logger.info("CONTEXT", "Critical section completed successfully")
    except Exception as e:
        await logger.error("CONTEXT", f"Error in critical section: {e}")
    finally:
        await logger.info("CONTEXT", "Exiting critical section")
    
    await logger.aclose()


async def main():
    """Run all structured logging examples."""
    print("=== Async Structured Logging Examples ===")
    print("Demonstrating various structured logging patterns.\n")
    
    await json_structured_logging()
    await xml_structured_logging()
    await dict_structured_logging()
    await correlation_context_example()
    await context_manager_example()
    
    print("\n✅ All structured logging examples completed!")
    print("Check the console output above to see the structured async logs.")


if __name__ == "__main__":
    asyncio.run(main()) 