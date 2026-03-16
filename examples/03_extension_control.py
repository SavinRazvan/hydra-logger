#!/usr/bin/env python3
"""
Role: Runnable example for 03 extension control.
Used By:
 - Developers running examples manually and `examples/run_all_examples.py`.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates 03 extension control usage patterns for manual verification and onboarding.
"""

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

# Users can enable/disable and configure any extension
config = LoggingConfig(
    extensions={
        "security": {
            "enabled": True,
            "type": "security",
            "patterns": ["email", "phone", "api_key"],
            "redaction_enabled": True,
            "sanitization_enabled": True,
        },
        "performance": {
            "enabled": False,  # User disables for max performance
            "type": "performance",
        },
    },
    layers={
        "app": LogLayer(
            destinations=[
                LogDestination(type="console", format="plain-text", use_colors=True),
                LogDestination(
                    type="file",
                    path="logs/examples/03_extension_control.jsonl",
                    format="json-lines",
                ),
            ]
        )
    },
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def test_extensions():
        """Test extension functionality."""
        logger.info("[03] Extension control example", layer="app")

    def test_warning_with_extensions():
        """Test warning with extensions enabled."""
        logger.warning("[03] Test message with extensions", layer="app")

    # Test logging from actual functions
    test_extensions()
    test_warning_with_extensions()

print("Example 3 completed: Extension Control")
