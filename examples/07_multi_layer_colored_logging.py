#!/usr/bin/env python3
"""
Role: Runnable example for 07 multi layer colored logging.
Used By:
 - Developers running examples manually and `examples/run_all_examples.py`.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates 07 multi layer colored logging usage patterns for manual verification and onboarding.
"""

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

# Different layers with different colors
config = LoggingConfig(
    layers={
        "api": LogLayer(
            destinations=[
                LogDestination(type="console", format="plain-text", use_colors=True),
                LogDestination(
                    type="file",
                    path="logs/examples/07_multi_layer_colored_logging.jsonl",
                    format="json-lines",
                ),
            ]
        ),
        "database": LogLayer(
            destinations=[
                LogDestination(type="console", format="plain-text", use_colors=True),
                LogDestination(
                    type="file",
                    path="logs/examples/07_multi_layer_colored_logging.jsonl",
                    format="json-lines",
                ),
            ]
        ),
        "security": LogLayer(
            destinations=[
                LogDestination(type="console", format="plain-text", use_colors=True),
                LogDestination(
                    type="file",
                    path="logs/examples/07_multi_layer_colored_logging.jsonl",
                    format="json-lines",
                ),
            ]
        ),
    }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def process_api_request():
        """Process an API request."""
        logger.info(
            "[07] API request processed", layer="api"
        )  # Green INFO, Bright Blue API

    def execute_database_query():
        """Execute a database query."""
        logger.info(
            "[07] Database query executed", layer="database"
        )  # Green INFO, Blue DATABASE

    def handle_security_alert():
        """Handle a security alert."""
        logger.warning(
            "[07] Security alert", layer="security"
        )  # Yellow WARNING, Red SECURITY

    # Test different layers from actual functions
    process_api_request()
    execute_database_query()
    handle_security_alert()

print("Example 7 completed: Multi-Layer Colored Logging")
