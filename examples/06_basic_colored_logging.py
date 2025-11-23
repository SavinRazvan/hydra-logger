#!/usr/bin/env python3
"""
Example 6: Basic Colored Logging
Demonstrates the color system for console output.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

# Create logger with colors
config = LoggingConfig(
 layers={
 "app": LogLayer(
 destinations=[
 LogDestination(
 type="console",
 format="plain-text",
 use_colors=True # Enable colors
 ),
 LogDestination(
 type="file",
 path="logs/examples/06_basic_colored_logging.log",
 format="json-lines"
 )
 ]
 )
 }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def log_debug_message():
        """Log a debug message."""
        logger.debug("[06] Debug message", layer="app") # Blue DEBUG, Cyan app

    def log_info_message():
        """Log an info message."""
        logger.info("[06] Info message", layer="app") # Green INFO, Cyan app

    def log_warning_message():
        """Log a warning message."""
        logger.warning("[06] Warning message", layer="app") # Yellow WARNING, Cyan app

    def log_error_message():
        """Log an error message."""
        logger.error("[06] Error message", layer="app") # Red ERROR, Cyan app

    def log_critical_message():
        """Log a critical message."""
        logger.critical("[06] Critical message", layer="app") # Bright Red CRITICAL, Cyan app

    # Test all log levels from actual functions
    log_debug_message()
    log_info_message()
    log_warning_message()
    log_error_message()
    log_critical_message()

print("Example 6 completed: Basic Colored Logging")

