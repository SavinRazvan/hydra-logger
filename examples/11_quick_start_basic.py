#!/usr/bin/env python3
"""
Example 11: Quick Start - Basic Usage
Basic usage example from README.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

# Configure logger to write to example-specific file
config = LoggingConfig(
 layers={
 "default": LogLayer(
 destinations=[
 LogDestination(type="file", path="logs/examples/11_quick_start_basic.jsonl", format="json-lines")
 ]
 )
 }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def start_application():
        """Start the application."""
        logger.info("[11] Application started")

    def check_memory():
        """Check system memory."""
        logger.warning("[11] Low memory")

    def connect_database():
        """Connect to database."""
        logger.error("[11] Database connection failed")

    def handle_user_action():
        """Handle a user action."""
        logger.info("[11] User action",
 extra={"user_id": 12345, "action": "login"},
 context={"correlation_id": "corr-123"}
 )

    # Test logging from actual functions
    start_application()
    check_memory()
    connect_database()
    handle_user_action()

print("Example 11 completed: Quick Start - Basic Usage")

