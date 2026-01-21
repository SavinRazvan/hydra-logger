#!/usr/bin/env python3
"""
Example 12: Quick Start - Async Usage
Async usage example from README.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_async_logger
import asyncio

# Configure logger to write to example-specific file
config = LoggingConfig(
 layers={
 "default": LogLayer(
 destinations=[
 LogDestination(type="file", path="logs/examples/12_quick_start_async.jsonl", format="json-lines")
 ]
 )
 }
)

async def main():
    # Use async context manager for automatic cleanup
 async with create_async_logger(config, name="MyAsyncApp") as async_logger:
        await async_logger.info("[12] Async logging works")
        await async_logger.warning("[12] Async warning message")

if __name__ == "__main__":
    asyncio.run(main())
    print("Example 12 completed: Quick Start - Async Usage")

