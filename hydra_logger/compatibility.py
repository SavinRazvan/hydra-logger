"""
Backward compatibility layer for Hydra-Logger.

This module provides seamless migration support from the original flexiai-toolsmith
logging system to the new Hydra-Logger. It maintains full backward compatibility
while enabling users to gradually adopt the advanced features of Hydra-Logger.

Key Features:
- Original setup_logging function with identical interface
- Migration utilities for converting legacy configurations
- Level conversion between integer and string representations
- Smooth transition path to multi-layered logging
- Preservation of existing logging behavior and file structures

The compatibility layer ensures that existing applications can continue to work
without modification while providing clear migration paths to leverage the
advanced capabilities of Hydra-Logger.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


from hydra_logger.config import LogDestination, LoggingConfig, LogLayer
from hydra_logger.logger import HydraLogger


def setup_logging(
    root_level: int = logging.DEBUG,
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
) -> None:
    """
    Configure root, file, and console logging (backward compatibility).

    This function provides the exact same interface as the original setup_logging
    from flexiai-toolsmith for seamless migration and continued operation of
    existing applications.

    The function sets up a complete logging configuration including:
    - Root logger at the specified root_level
    - RotatingFileHandler writing to 'logs/app.log' (max 5 MB, 3 backups) at file_level
    - StreamHandler (console) at console_level
    - Standard formatter: '%(asctime)s - %(levelname)s - %(filename)s - %(message)s'

    Args:
        root_level (int): Logging level for the root logger (default: DEBUG).
        file_level (int): Logging level for the file handler (default: DEBUG).
        console_level (int): Logging level for the console handler (default: INFO).
        enable_file_logging (bool): Whether to enable file logging (default: True).
        enable_console_logging (bool): Whether to enable console logging \
            (default: True).

    Returns:
        None

    Side Effects:
        - Creates the 'logs/' directory if it does not exist and file logging is \
            enabled.
        - Clears existing handlers on the root logger to prevent duplication.
        - Configures the root logger with the specified handlers and levels.

    Raises:
        OSError: If the log directory cannot be created due to permission or disk \
            issues.

    Example:
        >>> setup_logging(
        ...     root_level=logging.INFO,
        ...     file_level=logging.DEBUG,
        ...     console_level=logging.WARNING
        ... )
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    current_directory = os.getcwd()

    # Define log directory and file relative to the project root
    log_directory = os.path.join(current_directory, "logs")
    log_file = os.path.join(log_directory, "app.log")

    # Only create the log directory if file logging is enabled
    if enable_file_logging:
        try:
            os.makedirs(log_directory, exist_ok=True)
        except OSError as e:
            logging.debug(
                f"[setup_logging] Error creating log directory {log_directory}: {e}"
            )
            return

    # Get the root logger instance
    logger = logging.getLogger()

    # Clear existing handlers to prevent duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    try:
        # Set the logging level for the root logger
        logger.setLevel(root_level)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
        )

        if enable_file_logging:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3
            )
            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    except Exception as e:
        logging.debug(f"Error setting up logging: {e}")


def create_hydra_config_from_legacy(
    root_level: int = logging.DEBUG,
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    log_file_path: str = "logs/app.log",
) -> LoggingConfig:
    """
    Create a Hydra-Logger configuration from legacy setup_logging parameters.

    This function helps migrate from the old setup_logging to the new Hydra-Logger
    by creating a compatible configuration object that preserves all the original
    settings while enabling the advanced features of Hydra-Logger.

    Args:
        root_level (int): Logging level for the root logger (default: DEBUG).
        file_level (int): Logging level for the file handler (default: DEBUG).
        console_level (int): Logging level for the console handler (default: INFO).
        enable_file_logging (bool): Whether to enable file logging (default: True).
        enable_console_logging (bool): Whether to enable console logging \
            (default: True).
        log_file_path (str): Custom path for the log file (default: "logs/app.log").

    Returns:
        LoggingConfig: Configuration object compatible with Hydra-Logger that
        preserves the original logging behavior while enabling advanced features.

    Example:
        >>> config = create_hydra_config_from_legacy(
        ...     root_level=logging.INFO,
        ...     file_level=logging.DEBUG,
        ...     log_file_path="logs/custom/app.log"
        ... )
        >>> logger = HydraLogger(config)
    """

    destinations = []

    if enable_file_logging:
        destinations.append(
            LogDestination(
                type="file",
                path=log_file_path,
                level=_level_int_to_str(file_level),
                max_size="5MB",
                backup_count=3,
            )
        )

    if enable_console_logging:
        destinations.append(
            LogDestination(type="console", level=_level_int_to_str(console_level))
        )

    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level=_level_int_to_str(root_level), destinations=destinations
            )
        },
        default_level=_level_int_to_str(root_level),
    )


def _level_int_to_str(level_int: int) -> str:
    """
    Convert logging level integer to string representation.

    Args:
        level_int (int): Python logging level integer (e.g., logging.DEBUG).

    Returns:
        str: String representation of the logging level (e.g., "DEBUG").

    This utility function converts Python's integer logging levels to their
    string equivalents for use in Hydra-Logger configurations. It provides
    a fallback to "INFO" for unknown level values.

    Example:
        >>> _level_int_to_str(logging.DEBUG)
        'DEBUG'
        >>> _level_int_to_str(logging.ERROR)
        'ERROR'
        >>> _level_int_to_str(999)  # Unknown level
        'INFO'
    """
    level_map = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }
    return level_map.get(level_int, "INFO")


def migrate_to_hydra(
    root_level: int = logging.DEBUG,
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    log_file_path: str = "logs/app.log",
) -> HydraLogger:
    """
    Migrate from legacy setup_logging to Hydra-Logger.

    This function provides a smooth migration path from the old logging setup
    to the new Hydra-Logger system. It creates a fully configured HydraLogger
    instance that preserves the original logging behavior while enabling
    advanced features like multi-layered logging and custom folder paths.

    Args:
        root_level (int): Logging level for the root logger (default: DEBUG).
        file_level (int): Logging level for the file handler (default: DEBUG).
        console_level (int): Logging level for the console handler (default: INFO).
        enable_file_logging (bool): Whether to enable file logging (default: True).
        enable_console_logging (bool): Whether to enable console logging \
            (default: True).
        log_file_path (str): Custom path for the log file (default: "logs/app.log").

    Returns:
        HydraLogger: Fully configured HydraLogger instance ready for use.

    This function is the primary migration utility, combining configuration
    creation and logger instantiation in a single call for maximum convenience.

    Example:
        >>> logger = migrate_to_hydra(
        ...     root_level=logging.INFO,
        ...     file_level=logging.DEBUG,
        ...     log_file_path="logs/migrated/app.log"
        ... )
        >>> logger.info("DEFAULT", "Application migrated successfully")
    """

    config = create_hydra_config_from_legacy(
        root_level=root_level,
        file_level=file_level,
        console_level=console_level,
        enable_file_logging=enable_file_logging,
        enable_console_logging=enable_console_logging,
        log_file_path=log_file_path,
    )

    return HydraLogger(config)
