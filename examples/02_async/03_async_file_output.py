#!/usr/bin/env python3
"""
Async File Output Example

This example demonstrates async logging to files with optimized performance.
Shows how to use AsyncHydraLogger for file-based logging.
"""

import asyncio
import os
from hydra_logger.async_hydra import AsyncHydraLogger


async def main():
    print("=== Async File Output Example ===")
    print("Async logging to files with optimized performance.\n")
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Create async logger with default configuration
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    # Log messages to console (default)
    await logger.info("APP", "Application started successfully")
    await logger.debug("CONFIG", "Configuration loaded from environment")
    await logger.warning("PERF", "Memory usage is approaching threshold")
    await logger.error("SECURITY", "Failed login attempt detected")
    await logger.critical("SYSTEM", "Critical system error - immediate attention required")
    
    # Log some structured data
    await logger.info("USER", "User john.doe@example.com logged in")
    await logger.info("API", "API request to /api/users completed in 150ms")
    await logger.info("DB", "Database query executed successfully")
    
    # Log some performance metrics
    await logger.info("METRICS", "CPU usage: 45%, Memory usage: 67%")
    await logger.info("METRICS", "Active connections: 127, Queue depth: 23")
    
    await logger.aclose()
    
    print("\n✅ File output example completed!")
    print("Check the console output above to see the async logs.")


if __name__ == "__main__":
    asyncio.run(main()) 