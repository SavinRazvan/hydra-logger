#!/usr/bin/env python3
"""
Role: Runnable example for 02 destination control.
Used By:
 - Developers running examples manually and `examples/run_all_examples.py`.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates 02 destination control usage patterns for manual verification and onboarding.
"""

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

# Users can choose any destination combination
config = LoggingConfig(
    layers={
        "auth": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/02_destination_control_auth.log",
                    format="json",
                )
            ]
        ),
        "api": LogLayer(
            destinations=[
                LogDestination(type="console", format="colored"),
                LogDestination(
                    type="file",
                    path="logs/examples/02_destination_control_api.jsonl",
                    format="json-lines",
                ),
            ]
        ),
        "error": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/02_destination_control_errors.log",
                    format="plain-text",
                ),
            ]
        ),
    }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def authenticate_user(user_id: str):
        """Authenticate a user."""
        logger.info(f"[02] Authenticating user {user_id}", layer="auth")
        # Simulate auth logic
        return True

    def process_api_request(endpoint: str):
        """Process an API request."""
        logger.info(f"[02] Processing API request to {endpoint}", layer="api")
        # Simulate API processing
        return {"status": "success"}

    def handle_error(error_msg: str):
        """Handle an error."""
        logger.error(f"[02] Error occurred: {error_msg}", layer="error")
        # Error handling logic here

    # Test different layers from actual functions
    authenticate_user("user123")
    process_api_request("/api/users")
    handle_error("Database connection failed")

print("Example 2 completed: Destination Control")
