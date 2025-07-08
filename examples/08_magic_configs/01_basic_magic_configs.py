"""
Example: Custom Magic Config System (Sync & Async)

Demonstrates how to register, list, and use custom and built-in magic configs
with both HydraLogger and AsyncHydraLogger.
"""

import asyncio
from hydra_logger import HydraLogger, LoggingConfig
from hydra_logger.config import LogLayer, LogDestination
from hydra_logger.async_hydra import AsyncHydraLogger

# --- Register a custom magic config for sync logger ---
@HydraLogger.register_magic("my_sync_app", description="Custom config for my sync app")
def my_sync_config():
    return LoggingConfig(
        layers={
            "FRONTEND": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(type="console", format="plain-text", color_mode="always")
                ]
            )
        }
    )

# --- Register a custom magic config for async logger ---
@AsyncHydraLogger.register_magic("my_async_app", description="Custom config for my async app")
def my_async_config():
    return LoggingConfig(
        layers={
            "BACKEND": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(type="console", format="plain-text", color_mode="always")
                ]
            )
        }
    )

print("\n=== List of Available Magic Configs ===")
print(HydraLogger.list_magic_configs())

# --- Using built-in magic configs (sync) ---
print("\n=== Logging with Built-in Production Config (Sync) ===")
logger_prod = HydraLogger.for_production()
logger_prod.info("FRONTEND", "This is a production log message.")

# --- Using custom magic config (sync) ---
print("\n=== Logging with Custom Magic Config (Sync) ===")
logger_custom = HydraLogger.for_custom("my_sync_app")
logger_custom.info("FRONTEND", "This is a custom sync magic config log message.")

# --- Async usage ---
async def async_demo():
    print("\n=== Logging with Built-in Development Config (Async) ===")
    async_logger_dev = AsyncHydraLogger.for_development()
    await async_logger_dev.initialize()
    await async_logger_dev.info("BACKEND", "This is an async development log message.")

    print("\n=== Logging with Custom Magic Config (Async) ===")
    async_logger_custom = AsyncHydraLogger.for_custom("my_async_app")
    await async_logger_custom.initialize()
    await async_logger_custom.info("BACKEND", "This is a custom async magic config log message.")
    
    # Close the loggers
    await async_logger_dev.close()
    await async_logger_custom.close()

if __name__ == "__main__":
    # Run async demo
    asyncio.run(async_demo()) 