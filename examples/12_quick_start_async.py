#!/usr/bin/env python3
"""
Role: Runnable example for 12 quick start async.
Used By:
 - Developers running examples manually and `examples/run_all_examples.py`.
Depends On:
 - asyncio
 - hydra_logger
Notes:
 - Demonstrates 12 quick start async usage patterns for manual verification and onboarding.
"""

import asyncio

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_async_logger

# Configure logger to write to example-specific file
config = LoggingConfig(
    layers={
        "default": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/12_quick_start_async.jsonl",
                    format="json-lines",
                )
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
