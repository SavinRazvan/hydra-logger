#!/usr/bin/env python3
"""
Async File Output Example

This example demonstrates async logging with file output:
- AsyncHydraLogger with file destinations
- High-performance async file writing
- Batch processing for file operations
"""

import asyncio
import os
from pathlib import Path
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

async def demo_async_file_output():
    """Demonstrate async logging with file output."""
    
    print("📁 Async File Output Example")
    print("=" * 50)
    
    # Create logs directory
    logs_dir = Path("examples/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration for async file output using LoggingConfig
    config = LoggingConfig(
        layers={
            "ASYNC_FILE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/async_app.log",
                        format="plain-text",
                        level="INFO",
                        max_size="5MB",
                        backup_count=3
                    ),
                    LogDestination(
                        type="file",
                        path="examples/logs/async_errors.log",
                        format="json",
                        level="ERROR",
                        max_size="2MB",
                        backup_count=5
                    )
                ]
            )
        }
    )
    
    # Create async logger
    logger = AsyncHydraLogger(config=config)
    
    # Initialize the async logger
    await logger.initialize()
    
    print("🚀 Starting async file logging...")
    
    # Log messages asynchronously to files
    await logger.info("ASYNC_FILE", "Async file logger started")
    await logger.info("ASYNC_FILE", "Processing batch of requests")
    await logger.warning("ASYNC_FILE", "High memory usage detected")
    await logger.error("ASYNC_FILE", "Database connection failed")
    await logger.critical("ASYNC_FILE", "System shutdown initiated")
    
    # Simulate high-throughput file logging
    print("\n🔄 Simulating high-throughput async file logging...")
    
    # Create multiple concurrent file write operations
    tasks = []
    for i in range(20):
        task = logger.info("ASYNC_FILE", f"High-throughput message {i+1}")
        tasks.append(task)
    
    # Execute all tasks concurrently
    await asyncio.gather(*tasks)
    
    print("\n✅ All async file operations completed!")
    
    # Check if files were created
    app_log_path = Path("examples/logs/async_app.log")
    errors_log_path = Path("examples/logs/async_errors.log")
    
    if app_log_path.exists():
        print(f"✅ App log file created: {app_log_path}")
        print(f"   Size: {app_log_path.stat().st_size} bytes")
    
    if errors_log_path.exists():
        print(f"✅ Errors log file created: {errors_log_path}")
        print(f"   Size: {errors_log_path.stat().st_size} bytes")
    
    # Close the async logger
    await logger.close()
    
    print("🎯 Async file output example completed!")

if __name__ == "__main__":
    asyncio.run(demo_async_file_output()) 