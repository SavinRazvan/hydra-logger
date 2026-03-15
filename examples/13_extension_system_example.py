#!/usr/bin/env python3
"""
Role: 13 extension system example implementation.
Used By:
 - (update when known)
Depends On:
 - hydra_logger
Notes:
 - Header standardized by slim-header migration.
"""
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

config = LoggingConfig(
 extensions={
 "data_protection": {
 "enabled": True,
 "redaction_patterns": ["password", "token"],
 "encryption_key": "your-key-here"
 },
 },
 layers={
 "app": LogLayer(
 destinations=[
 LogDestination(type="console", format="plain-text", use_colors=True),
 LogDestination(type="file", path="logs/examples/13_extension_system_example.jsonl", format="json-lines")
 ]
 )
 }
)

# Use context manager for automatic cleanup
with create_logger(config, logger_type="sync") as logger:
    # Functions that demonstrate proper function name tracking
    def test_extension_system():
        """Test the extension system."""
        logger.info("[13] Extension system example", layer="app")

    def test_data_protection():
        """Test data protection extension."""
        logger.info("[13] Message with sensitive data: password=secret123", layer="app")

    # Test extension system from actual functions
    test_extension_system()
    test_data_protection()

print("Example 13 completed: Extension System Example")

