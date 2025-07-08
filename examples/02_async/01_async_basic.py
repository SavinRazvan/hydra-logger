#!/usr/bin/env python3
"""
Basic AsyncHydraLogger Usage Example

This example demonstrates the simplest possible usage of AsyncHydraLogger.
Shows how to use async logging with minimal configuration.
"""

import asyncio
from hydra_logger.async_hydra import AsyncHydraLogger


async def main():
    print("=== Basic AsyncHydraLogger Usage ===")
    print("Async logging with minimal configuration.\n")
    
    # Create async logger with default configuration
    logger = AsyncHydraLogger()
    
    # Initialize the logger
    await logger.initialize()
    
    # Start logging immediately
    await logger.info("APP", "Application started")
    await logger.debug("CONFIG", "Configuration loaded")
    await logger.warning("PERF", "High memory usage detected")
    await logger.error("SECURITY", "Authentication failed")
    await logger.critical("SYSTEM", "System shutdown initiated")
    
    # Close the logger
    await logger.close()
    
    print("\n✅ Basic async example completed!")
    print("Check the console output above to see the async logs.")


if __name__ == "__main__":
    asyncio.run(main()) 