#!/usr/bin/env python3
"""
Role: Runnable example for 05 custom configurations.
Used By:
 - Developers running examples manually and `examples/run_all_examples.py`.
Depends On:
 - hydra_logger
Notes:
 - Demonstrates 05 custom configurations usage patterns for manual verification and onboarding.
"""

from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

# Users can create completely custom configurations
custom_config = LoggingConfig(
    default_level="INFO",
    enable_security=True,
    layers={
        "database": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/examples/05_custom_configurations_db.log",
                    format="json",
                ),
                LogDestination(type="console", format="colored"),
            ],
        )
    },
    extensions={
        "custom_security": {
            "enabled": True,
            "type": "security",
            "patterns": ["email", "ssn", "credit_card"],
        }
    },
)

# Use context manager for automatic cleanup
with create_logger(custom_config, logger_type="sync") as logger:
    # Database operation functions
    def execute_query(query: str):
        """Execute a database query."""
        logger.debug(f"[05] Executing query: {query}", layer="database")
        # Simulate query execution
        return {"rows": 100}

    def run_migration():
        """Run database migration."""
        logger.info("[05] Starting database migration", layer="database")
        # Migration logic here
        logger.info("[05] Migration completed successfully", layer="database")

    def monitor_slow_queries():
        """Monitor for slow database queries."""
        logger.warning(
            "[05] Slow query detected: SELECT * FROM large_table", layer="database"
        )

    # Query optimization logic here

    # Test custom configuration with actual functions
    execute_query("SELECT * FROM users WHERE id = 123")
    run_migration()
    monitor_slow_queries()

print("Example 5 completed: Custom Configurations")
