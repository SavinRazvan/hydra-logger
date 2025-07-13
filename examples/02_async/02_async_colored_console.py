#!/usr/bin/env python3
"""
Async Colored Console Example

This example demonstrates async logging with colored console output.
Shows how to use AsyncHydraLogger with enhanced visual formatting.
"""

import asyncio
from hydra_logger.async_hydra import AsyncHydraLogger


async def main():
    print("=== Async Colored Console Example ===")
    print("Async logging with colored console output.\n")
    
    # Create async logger with colored console configuration
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
    
    # Log messages with different levels (colors will be applied automatically)
    await logger.info("APP", "Application started successfully")
    await logger.debug("CONFIG", "Configuration loaded from environment")
    await logger.warning("PERF", "Memory usage is approaching threshold")
    await logger.error("SECURITY", "Failed login attempt detected")
    await logger.critical("SYSTEM", "Critical system error - immediate attention required")
    
    # Log some structured data
    await logger.info("USER", "User john.doe@example.com logged in")
    await logger.info("API", "API request to /api/users completed in 150ms")
    await logger.info("DB", "Database query executed successfully")
    
    await logger.aclose()
    
    print("\n✅ Colored console example completed!")
    print("Check the console output above to see the colored async logs.")


if __name__ == "__main__":
    asyncio.run(main()) 