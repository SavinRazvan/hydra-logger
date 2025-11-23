#!/usr/bin/env python3
"""
Example 4: Runtime Control
Demonstrates how users can control extensions at runtime.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger
from hydra_logger.extensions import ExtensionManager

# Create a basic config
config = LoggingConfig(
 layers={
 "app": LogLayer(
 destinations=[
 LogDestination(type="console", format="plain-text", use_colors=True),
 LogDestination(type="file", path="logs/examples/04_runtime_control.jsonl", format="json-lines")
 ]
 )
 }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def create_security_extension():
        """Create a security extension at runtime."""
        try:
            manager = ExtensionManager()
            manager.create_extension("my_security", "security", enabled=True, patterns=["email"])
            logger.info("[04] Extension created", layer="app")
        except Exception as e:
            print(f"ExtensionManager example - this may require additional setup: {e}")

    def disable_security_extension():
        """Disable security extension at runtime."""
        try:
            manager = ExtensionManager()
            manager.disable_extension("my_security")
            logger.info("[04] Extension disabled", layer="app")
        except Exception as e:
            print(f"ExtensionManager example - this may require additional setup: {e}")

    def enable_security_extension():
        """Re-enable security extension at runtime."""
        try:
            manager = ExtensionManager()
            manager.enable_extension("my_security")
            logger.info("[04] Extension re-enabled", layer="app")
        except Exception as e:
            print(f"ExtensionManager example - this may require additional setup: {e}")

    # Test runtime extension control from actual functions
    create_security_extension()
    disable_security_extension()
    enable_security_extension()

print("Example 4 completed: Runtime Control")

