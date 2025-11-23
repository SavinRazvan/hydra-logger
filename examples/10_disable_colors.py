#!/usr/bin/env python3
"""
Example 10: Disable Colors
Demonstrates how to disable colors for clean output.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

# Disable colors for clean output
config = LoggingConfig(
 layers={
 "app": LogLayer(
 destinations=[
 LogDestination(
 type="console",
 format="plain-text",
 use_colors=False # No colors
 ),
 LogDestination(
 type="file",
 path="logs/examples/10_disable_colors.log",
 format="json-lines"
 )
 ]
 )
 }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def log_plain_info():
        """Log plain text info message."""
        logger.info("[10] This will be plain text without colors", layer="app")

    def log_plain_warning():
        """Log plain text warning message."""
        logger.warning("[10] Plain warning message", layer="app")

    def log_plain_error():
        """Log plain text error message."""
        logger.error("[10] Plain error message", layer="app")

    # Test plain text logging from actual functions
    log_plain_info()
    log_plain_warning()
    log_plain_error()

print("Example 10 completed: Disable Colors")

