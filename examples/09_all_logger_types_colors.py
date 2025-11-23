#!/usr/bin/env python3
"""
Example 9: All Logger Types with Colors
Demonstrates colors with SyncLogger, AsyncLogger, and CompositeLogger.
"""
import asyncio
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger, create_async_logger, create_composite_logger

config = LoggingConfig(
 layers={
 "app": LogLayer(
 destinations=[
 LogDestination(type="console", format="plain-text", use_colors=True),
 LogDestination(type="file", path="logs/examples/09_all_logger_types_colors.jsonl", format="json-lines")
 ]
 )
 }
)

# Use context managers for automatic cleanup
# SyncLogger with colors
with create_logger(config, logger_type="sync") as sync_logger:
    sync_logger.info("[09] Sync colored message", layer="app")

# AsyncLogger with colors (for async contexts)
async def test_async():
    # Use async context manager for automatic cleanup
 async with create_async_logger(config, name="async") as async_logger:
    await async_logger.info("[09] Async colored message", layer="app")

# CompositeLogger with colors
with create_composite_logger(config, name="composite") as composite_logger:
    composite_logger.info("[09] Composite colored message", layer="app")

# Run async test
asyncio.run(test_async())

print("Example 9 completed: All Logger Types with Colors")

