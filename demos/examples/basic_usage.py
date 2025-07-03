"""
Basic usage examples for Hydra-Logger.

Demonstrates different ways to use the logging system:
1. Simple backward-compatible usage
2. Advanced multi-layered logging with different formats
3. Configuration file usage with format examples
"""

import logging

from hydra_logger import HydraLogger, migrate_to_hydra, setup_logging


def example_1_backward_compatible():
    """Example 1: Backward compatible usage (same as original flexiai)."""
    print("\n=== Example 1: Backward Compatible Usage ===")

    # This works exactly like the original setup_logging from flexiai
    setup_logging(enable_file_logging=True, console_level=logging.INFO)

    # Use standard logging
    logger = logging.getLogger(__name__)
    logger.info("This goes to logs/app.log and console")
    logger.debug("This goes to logs/app.log only")
    logger.warning("This goes to both logs/app.log and console")


def example_2_migration_path():
    """Example 2: Migration path with custom log file path."""
    print("\n=== Example 2: Migration Path with Custom Path ===")

    # Migrate from old setup_logging to Hydra-Logger with custom path
    logger = migrate_to_hydra(
        enable_file_logging=True,
        console_level=logging.INFO,
        log_file_path="logs/custom/app.log",  # Custom folder path!
    )

    # Use the new Hydra-Logger interface
    logger.info("DEFAULT", "This goes to logs/custom/app.log and console")
    logger.debug("DEFAULT", "This goes to logs/custom/app.log only")


def example_3_multi_layered():
    """Example 3: Multi-layered logging with different destinations and formats."""
    print("\n=== Example 3: Multi-layered Logging with Formats ===")

    # Create a Hydra-Logger with multiple layers and different formats
    from hydra_logger.config import LogDestination, LoggingConfig, LogLayer

    config = LoggingConfig(
        layers={
            "CONFIG": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/config/app.log",  # Custom folder!
                        max_size="5MB",
                        backup_count=3,
                        format="text"  # Plain text format
                    ),
                    LogDestination(
                        type="console", 
                        level="WARNING",
                        format="json"  # JSON format for console
                    ),
                ],
            ),
            "EVENTS": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/events/stream.json",  # Different folder!
                        max_size="10MB",
                        format="json"  # JSON format for structured logging
                    )
                ],
            ),
            "SECURITY": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/security/auth.log",  # Security folder!
                        max_size="1MB",
                        format="syslog"  # Syslog format for security
                    )
                ],
            ),
            "ANALYTICS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/analytics/metrics.csv",  # Analytics folder!
                        format="csv"  # CSV format for data analysis
                    )
                ],
            ),
            "MONITORING": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/monitoring/alerts.gelf",  # Monitoring folder!
                        format="gelf"  # GELF format for centralized logging
                    )
                ],
            ),
        }
    )

    logger = HydraLogger(config)

    # Log to different layers with different formats
    logger.info("CONFIG", "Configuration loaded successfully")
    logger.warning("CONFIG", "This warning goes to console in JSON format")

    logger.debug("EVENTS", "Event stream started")
    logger.info("EVENTS", "Event processed")

    logger.error("SECURITY", "Authentication failed")
    logger.critical("SECURITY", "Security breach detected!")

    logger.info("ANALYTICS", "Performance metric recorded")
    logger.info("MONITORING", "System health check completed")


def example_4_config_file():
    """Example 4: Using configuration file with format examples."""
    print("\n=== Example 4: Configuration File Usage with Formats ===")

    # This would use a YAML file like config_examples/advanced.yaml
    try:
        logger = HydraLogger.from_config(
            "hydra_logger/examples/config_examples/advanced.yaml"
        )

        logger.info("CONFIG", "Loaded from config file")
        logger.debug("EVENTS", "Event from config file")
        logger.error("SECURITY", "Security event from config file")

    except FileNotFoundError:
        print("Config file not found - skipping this example")


def example_5_format_demonstration():
    """Example 5: Demonstrating different log formats."""
    print("\n=== Example 5: Log Format Demonstration ===")

    from hydra_logger.config import LogDestination, LoggingConfig, LogLayer

    config = LoggingConfig(
        layers={
            "FORMATS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/formats/text.log",
                        format="text"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/formats/json.log",
                        format="json"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/formats/csv.log",
                        format="csv"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/formats/syslog.log",
                        format="syslog"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/formats/gelf.log",
                        format="gelf"
                    ),
                ],
            )
        }
    )

    logger = HydraLogger(config)

    # Log the same message to see different formats
    logger.info("FORMATS", "This message will appear in different formats")
    logger.warning("FORMATS", "Warning message in multiple formats")
    logger.error("FORMATS", "Error message demonstrating format differences")

    print("Check the logs/formats/ directory to see the different output formats!")


if __name__ == "__main__":
    print("Hydra-Logger Basic Usage Examples")
    print("=" * 50)

    # Run examples
    example_1_backward_compatible()
    example_2_migration_path()
    example_3_multi_layered()
    example_4_config_file()
    example_5_format_demonstration()

    print("\n" + "=" * 50)
    print("Examples completed! Check the logs/ directory for output files.")
    print("Different formats will be visible in their respective log files.")
