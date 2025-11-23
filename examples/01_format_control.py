#!/usr/bin/env python3
"""
Example 1: Format Control
Demonstrates how users can choose any format for any destination.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

# Users can choose any format for any destination
config = LoggingConfig(
    layers={
        "app": LogLayer(
            destinations=[
                LogDestination(type="console", format="json", use_colors=True),
                LogDestination(type="file", path="logs/examples/01_format_control.log", format="plain-text"),
                LogDestination(type="file", path="logs/examples/01_format_control.jsonl", format="json-lines")
                ]
            )
    }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Application functions
    def initialize_application():
        """Initialize the application."""
        logger.info("[01] Application initializing", layer="app")

    def process_data(data_id: str):
        """Process some data."""
        logger.debug(f"[01] Processing data with ID: {data_id}", layer="app")

    def handle_warning(message: str):
        """Handle a warning."""
        logger.warning(f"[01] Warning: {message}", layer="app")

    # Test logging from actual functions
    initialize_application()
    process_data("data123")
    handle_warning("Low memory detected")

print("Example 1 completed: Format Control")
