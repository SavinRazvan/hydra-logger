#!/usr/bin/env python3
"""
Example 8: Mixed Console and File Output
Demonstrates console with colors, file without colors.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

# Console with colors, file without colors
config = LoggingConfig(
 layers={
 "app": LogLayer(
 destinations=[
 LogDestination(
 type="console",
 format="plain-text",
 use_colors=True # Colored console
 ),
 LogDestination(
 type="file",
 path="logs/examples/08_mixed_console_file_output.log",
 format="plain-text"
    # No use_colors for file (colors are console-only)
 )
 ]
 )
 }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    def save_user_data(user_id: str, data: dict):
        """Save user data to database."""
        logger.info(f"[08] Saving data for user {user_id}", layer="app")
    # Save logic here

    def validate_input(data: str):
        """Validate user input."""
        logger.warning(f"[08] Input validation warning: {data}", layer="app")
    # Validation logic here

    def log_error(error_type: str):
        """Log an error."""
        logger.error(f"[08] Error type: {error_type}", layer="app")
    # Error handling logic here

    # Test mixed output from functions
    save_user_data("user456", {"name": "John", "email": "john@example.com"})
    validate_input("Invalid format detected")
    log_error("Database timeout")

print("Example 8 completed: Mixed Console and File Output")
