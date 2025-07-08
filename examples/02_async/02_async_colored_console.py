#!/usr/bin/env python3
"""
Async Colored Console Example

This example demonstrates async logging with colored console output:
- AsyncHydraLogger with colored console
- High-performance async logging
- Color mode control for async operations
"""

import asyncio
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

async def demo_async_colored_console():
    """Demonstrate async logging with colored console output."""
    
    print("⚡ Async Colored Console Example")
    print("=" * 50)
    
    # Configuration for async colored console using LoggingConfig
    config = LoggingConfig(
        layers={
            "ASYNC": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        level="INFO",
                        color_mode="always"
                    )
                ]
            )
        }
    )
    
    # Create async logger
    logger = AsyncHydraLogger(config=config)
    
    # Initialize the async logger
    await logger.initialize()
    
    print("🚀 Starting async logging with colors...")
    
    # Log messages asynchronously with colors
    await logger.info("ASYNC", "Async logger started")
    await logger.info("ASYNC", "Processing user request")
    await logger.warning("ASYNC", "High CPU usage detected")
    await logger.error("ASYNC", "Network timeout")
    
    # Simulate concurrent logging
    print("\n🔄 Simulating concurrent async logging...")
    
    # Create multiple concurrent log operations
    tasks = []
    for i in range(5):
        task = logger.info("ASYNC", f"Concurrent task {i+1}")
        tasks.append(task)
    
    # Execute all tasks concurrently
    await asyncio.gather(*tasks)
    
    print("\n✅ All concurrent tasks completed!")
    
    # Close the async logger
    await logger.close()
    
    print("🎯 Async colored console example completed!")

if __name__ == "__main__":
    asyncio.run(demo_async_colored_console()) 