#!/usr/bin/env python3
"""
Example 11: Quick Start - Basic Usage
Basic usage example from README.
"""
import sys
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger
except ImportError:
    print("=" * 70)
    print("ERROR: hydra_logger package not found")
    print("=" * 70)
    print("\nTo fix this:")
    print("  1. Activate virtual environment: source .venv/bin/activate")
    print("  2. Or install package: pip install -e .")
    print("  3. Or run setup: ./setup_env.sh")
    print("\n" + "=" * 70)
    sys.exit(1)

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

