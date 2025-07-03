"""
Basic usage examples for Hydra-Logger.

Demonstrates different ways to use the logging system:
1. Simple backward-compatible usage
2. Advanced multi-layered logging
3. Configuration file usage
"""

import logging
from hydra_logger import HydraLogger, setup_logging, migrate_to_hydra


def example_1_backward_compatible():
    """Example 1: Backward compatible usage (same as original flexiai)."""
    print("\n=== Example 1: Backward Compatible Usage ===")
    
    # This works exactly like the original setup_logging from flexiai
    setup_logging(
        enable_file_logging=True,
        console_level=logging.INFO
    )
    
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
        log_file_path="logs/custom/app.log"  # Custom folder path!
    )
    
    # Use the new Hydra-Logger interface
    logger.info("DEFAULT", "This goes to logs/custom/app.log and console")
    logger.debug("DEFAULT", "This goes to logs/custom/app.log only")


def example_3_multi_layered():
    """Example 3: Multi-layered logging with different destinations."""
    print("\n=== Example 3: Multi-layered Logging ===")
    
    # Create a Hydra-Logger with multiple layers
    from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
    
    config = LoggingConfig(
        layers={
            "CONFIG": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/config/app.log",  # Custom folder!
                        max_size="5MB",
                        backup_count=3
                    ),
                    LogDestination(
                        type="console",
                        level="WARNING"
                    )
                ]
            ),
            "EVENTS": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/events/stream.log",  # Different folder!
                        max_size="10MB"
                    )
                ]
            ),
            "SECURITY": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/security/auth.log",  # Security folder!
                        max_size="1MB"
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(config)
    
    # Log to different layers
    logger.info("CONFIG", "Configuration loaded successfully")
    logger.warning("CONFIG", "This warning goes to console too")
    
    logger.debug("EVENTS", "Event stream started")
    logger.info("EVENTS", "Event processed")
    
    logger.error("SECURITY", "Authentication failed")
    logger.critical("SECURITY", "Security breach detected!")


def example_4_config_file():
    """Example 4: Using configuration file."""
    print("\n=== Example 4: Configuration File Usage ===")
    
    # This would use a YAML file like config_examples/advanced.yaml
    try:
        logger = HydraLogger.from_config("hydra_logger/examples/config_examples/advanced.yaml")
        
        logger.info("CONFIG", "Loaded from config file")
        logger.debug("EVENTS", "Event from config file")
        logger.error("SECURITY", "Security event from config file")
        
    except FileNotFoundError:
        print("Config file not found - skipping this example")


if __name__ == "__main__":
    print("Hydra-Logger Basic Usage Examples")
    print("=" * 50)
    
    # Run examples
    example_1_backward_compatible()
    example_2_migration_path()
    example_3_multi_layered()
    example_4_config_file()
    
    print("\n" + "=" * 50)
    print("Examples completed! Check the logs/ directory for output files.") 