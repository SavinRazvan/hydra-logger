"""
Main HydraLogger class for multi-layered, multi-destination logging.

This module provides a sophisticated, dynamic logging system that can route different
types of logs across multiple destinations (files, console) with custom folder paths.
The system supports multi-layered logging where each layer can have its own configuration,
destinations, and log levels, enabling complex logging scenarios for enterprise applications.

Key Features:
- Multi-layered logging with custom folder paths for each layer
- Multiple destinations per layer (file, console) with independent configurations
- Configurable file rotation and backup counts with size-based rotation
- Graceful error handling and fallback mechanisms for robust operation
- Thread-safe logging operations for concurrent applications
- Backward compatibility with standard Python logging module
- Automatic directory creation for custom log file paths
- Comprehensive log level filtering and message routing

The HydraLogger class is the core component that orchestrates all logging operations,
managing multiple logging layers, handling configuration validation, and providing
a unified interface for complex logging requirements.

Example:
    >>> from hydra_logger import HydraLogger
    >>> logger = HydraLogger()
    >>> logger.info("CONFIG", "Configuration loaded successfully")
    >>> logger.error("SECURITY", "Authentication failed")
    >>> logger.debug("EVENTS", "Event stream started")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional, Union

from hydra_logger.config import (
    LogDestination,
    LoggingConfig,
    LogLayer,
    create_log_directories,
    get_default_config,
    load_config,
)


class HydraLoggerError(Exception):
    """
    Base exception for HydraLogger errors.

    This exception is raised when critical errors occur during logger
    initialization, configuration, or operation that cannot be handled
    gracefully by the system.
    """

    pass


class HydraLogger:
    """
    Dynamic multi-headed logging system with layer-based routing.

    This class provides a sophisticated logging system that can route different types
    of logs to different destinations with custom folder paths. Each layer can have
    its own configuration, including multiple destinations (files, console) with
    different log levels and file rotation settings.

    The HydraLogger manages multiple logging layers simultaneously, each with its
    own configuration and destinations. It automatically creates necessary directories,
    handles file rotation, and provides fallback mechanisms for error recovery.

    Attributes:
        config (LoggingConfig): The logging configuration for this instance.
        loggers (Dict[str, logging.Logger]): Dictionary of configured loggers by layer name.
    """

    def __init__(self, config: Optional[LoggingConfig] = None):
        """
        Initialize HydraLogger with configuration.

        Args:
            config (Optional[LoggingConfig]): LoggingConfig object. If None, uses default configuration.

        Raises:
            HydraLoggerError: If logger setup fails due to configuration issues.

        The initialization process includes:
        - Configuration validation and default setup
        - Directory creation for all file destinations
        - Logger setup for each configured layer
        - Handler creation and configuration
        """
        try:
            self.config = config or get_default_config()
            self.loggers: Dict[str, logging.Logger] = {}
            self._setup_loggers()
        except Exception as e:
            raise HydraLoggerError(f"Failed to initialize HydraLogger: {e}") from e

    @classmethod
    def from_config(cls, config_path: Union[str, Path]) -> "HydraLogger":
        """
        Create HydraLogger from configuration file.

        Args:
            config_path (Union[str, Path]): Path to YAML or TOML configuration file.

        Returns:
            HydraLogger: Instance configured from file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the configuration file is invalid or malformed.
            HydraLoggerError: If logger initialization fails after config loading.

        This method provides a convenient way to create a HydraLogger instance
        directly from a configuration file, handling all the loading and validation
        automatically.
        """
        try:
            config = load_config(config_path)
            return cls(config)
        except (FileNotFoundError, ValueError):
            # Re-raise FileNotFoundError and ValueError as-is
            raise
        except Exception as e:
            raise HydraLoggerError(
                f"Failed to create HydraLogger from config: {e}"
            ) from e

    def _setup_loggers(self) -> None:
        """
        Set up individual loggers for each layer.

        This method creates and configures logging handlers for each layer defined
        in the configuration. It handles directory creation, handler setup, and
        error recovery for invalid configurations.

        The setup process includes:
        - Creating all necessary log directories
        - Setting up individual loggers for each layer
        - Configuring handlers for each destination
        - Error handling and fallback mechanisms

        Raises:
            HydraLoggerError: If critical setup failures occur that prevent
                the logger from functioning properly.
        """
        try:
            # Create log directories first
            create_log_directories(self.config)

            # Set up each layer
            for layer_name, layer_config in self.config.layers.items():
                self._setup_single_layer(layer_name, layer_config)

        except Exception as e:
            raise HydraLoggerError(f"Failed to setup loggers: {e}") from e

    def _setup_single_layer(self, layer_name: str, layer_config: LogLayer) -> None:
        """
        Set up a single logging layer.

        Args:
            layer_name (str): Name of the layer to configure.
            layer_config (LogLayer): Configuration for this layer.

        This method configures a single logging layer with its destinations,
        handlers, and log levels. It includes error handling to ensure that
        failures in one layer don't prevent other layers from being set up.

        Raises:
            HydraLoggerError: If layer setup fails completely and cannot be recovered.
        """
        try:
            logger = logging.getLogger(f"hydra.{layer_name}")
            logger.setLevel(getattr(logging, layer_config.level))

            # Clear existing handlers to avoid duplicates
            if logger.hasHandlers():
                logger.handlers.clear()

            # Add handlers for each destination
            valid_handlers = 0
            for destination in layer_config.destinations:
                handler = self._create_handler(destination, layer_config.level)
                if handler:
                    logger.addHandler(handler)
                    valid_handlers += 1

            # Warn if no valid handlers were created for this layer
            if valid_handlers == 0:
                self._log_warning(
                    f"No valid handlers created for layer '{layer_name}'. "
                    f"Layer will not log to any destination."
                )

            self.loggers[layer_name] = logger

        except Exception as e:
            self._log_error(f"Failed to setup layer '{layer_name}': {e}")
            # Don't raise here to allow other layers to be set up

    def _create_handler(
        self, destination: LogDestination, layer_level: str
    ) -> Optional[logging.Handler]:
        """
        Create a logging handler for a destination.

        Args:
            destination (LogDestination): LogDestination configuration.
            layer_level (str): The level of the layer this handler belongs to.

        Returns:
            Optional[logging.Handler]: Configured logging handler or None if creation fails.

        This method creates the appropriate handler type based on the destination
        configuration. It includes comprehensive error handling and fallback
        mechanisms to ensure robust operation even when individual handlers fail.
        """
        try:
            if destination.type == "file":
                return self._create_file_handler(destination, layer_level)
            elif destination.type == "console":
                return self._create_console_handler(destination)
            # Note: destination.type is Literal["file", "console"], so no else needed

        except ValueError as e:
            # Handle validation errors (e.g., missing path for file destinations)
            self._log_warning(f"Invalid destination configuration: {e}")
            return None
        except Exception as e:
            # Fallback to console logging if file handler creation fails
            self._log_warning(f"Failed to create {destination.type} handler: {e}")
            if destination.type == "file":
                # Try to create a console handler as fallback
                try:
                    return self._create_console_handler(destination)
                except Exception as fallback_error:
                    self._log_error(
                        f"Fallback console handler creation failed: {fallback_error}"
                    )
            # For any destination type that fails, return None
            return None

    def _create_file_handler(
        self, destination: LogDestination, layer_level: str
    ) -> RotatingFileHandler:
        """
        Create a rotating file handler.

        Args:
            destination (LogDestination): File destination configuration.
            layer_level (str): The level of the layer this handler belongs to.

        Returns:
            RotatingFileHandler: Configured rotating file handler.

        Raises:
            ValueError: If path is None or invalid for file destinations.
            OSError: If file system operations fail.

        This method creates a RotatingFileHandler with the specified configuration,
        including file size limits, backup counts, and proper encoding. It handles
        path validation and provides detailed error messages for troubleshooting.
        """
        # Validate that path is provided for file destinations
        if not destination.path:
            raise ValueError("Path is required for file destinations")

        # Ensure the path is a string
        file_path = str(destination.path)

        # Parse max_size (e.g., "5MB" -> 5 * 1024 * 1024)
        max_bytes = self._parse_size(destination.max_size or "5MB")

        # Create the handler with proper error handling
        try:
            handler = RotatingFileHandler(
                file_path,
                maxBytes=max_bytes,
                backupCount=destination.backup_count or 3,
                encoding="utf-8",  # Ensure consistent encoding
            )

            # Use the layer level, not the destination level for file handlers
            handler.setLevel(getattr(logging, layer_level))
            handler.setFormatter(self._get_formatter())

            return handler

        except OSError as e:
            raise OSError(
                f"Failed to create file handler for '{file_path}': {e}"
            ) from e

    def _create_console_handler(
        self, destination: LogDestination
    ) -> logging.StreamHandler:
        """
        Create a console handler.

        Args:
            destination (LogDestination): Console destination configuration.

        Returns:
            logging.StreamHandler: Configured console stream handler.

        Raises:
            ValueError: If the log level is invalid or handler creation fails.

        This method creates a StreamHandler that outputs to stdout with the
        specified log level and standard formatting for console output.
        """
        try:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(getattr(logging, destination.level))
            handler.setFormatter(self._get_formatter())

            return handler

        except Exception as e:
            raise ValueError(f"Failed to create console handler: {e}") from e

    def _get_formatter(self) -> logging.Formatter:
        """
        Get the standard formatter for all handlers.

        Returns:
            logging.Formatter: Configured logging formatter with timestamp, logger name,
            level, filename, line number, and message.

        The formatter provides a consistent, detailed log format that includes:
        - Timestamp with date and time
        - Logger name (hydra.layer_name)
        - Log level
        - Source filename and line number
        - Log message
        """
        return logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string to bytes.

        Args:
            size_str (str): Size string like "5MB", "1GB", "1024", etc.

        Returns:
            int: Size in bytes.

        Raises:
            ValueError: If the size string format is invalid or empty.

        This method supports various size formats:
        - KB: Kilobytes (e.g., "1KB" = 1024 bytes)
        - MB: Megabytes (e.g., "5MB" = 5,242,880 bytes)
        - GB: Gigabytes (e.g., "1GB" = 1,073,741,824 bytes)
        - B: Bytes (e.g., "1024B" = 1024 bytes)
        - Raw numbers: Assumed to be bytes (e.g., "1024" = 1024 bytes)
        """
        if not size_str:
            raise ValueError("Size string cannot be empty")

        size_str = size_str.upper().strip()

        try:
            if size_str.endswith("KB"):
                return int(size_str[:-2]) * 1024
            elif size_str.endswith("MB"):
                return int(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith("GB"):
                return int(size_str[:-2]) * 1024 * 1024 * 1024
            elif size_str.endswith("B"):
                return int(size_str[:-1])
            else:
                # Assume bytes if no unit specified
                return int(size_str)
        except ValueError as e:
            raise ValueError(f"Invalid size format '{size_str}': {e}") from e

    def log(self, layer: str, level: str, message: str) -> None:
        """
        Log a message to a specific layer.

        Args:
            layer (str): Layer name to log to.
            level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            message (str): Message to log.

        Raises:
            ValueError: If the log level is invalid.

        This method provides the core logging functionality, routing messages
        to the appropriate layer and handling log level validation. It includes
        fallback mechanisms to ensure messages are logged even if the specific
        level method fails.
        """
        if not message:
            return  # Skip empty messages

        # Normalize the level
        level = level.upper()

        # Validate the level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level not in valid_levels:
            raise ValueError(
                f"Invalid log level '{level}'. Must be one of {valid_levels}"
            )

        # Get or create logger for the layer
        logger = self._get_or_create_logger(layer)

        # Log the message
        try:
            log_method = getattr(logger, level.lower())
            log_method(message)
        except Exception as e:
            # Fallback to info level if the specific level fails
            self._log_error(f"Failed to log {level} message to layer '{layer}': {e}")
            logger.info(message)

    def _get_or_create_logger(self, layer: str) -> logging.Logger:
        """
        Get existing logger or create a new one for unknown layers.

        Args:
            layer (str): Layer name.

        Returns:
            logging.Logger: Configured logging.Logger instance.

        This method provides fallback functionality for logging to layers that
        weren't explicitly configured. It first tries to use the DEFAULT layer
        if available, otherwise creates a simple logger with console output
        for unknown layers.
        """
        if layer not in self.loggers:
            # Fallback to default layer if available
            if "DEFAULT" in self.loggers:
                layer = "DEFAULT"
            else:
                # Create a simple logger for unknown layers
                logger = logging.getLogger(f"hydra.{layer}")
                logger.setLevel(getattr(logging, self.config.default_level))

                # Add a console handler for unknown layers
                if not logger.handlers:
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setLevel(
                        getattr(logging, self.config.default_level)
                    )
                    console_handler.setFormatter(self._get_formatter())
                    logger.addHandler(console_handler)

                self.loggers[layer] = logger

        return self.loggers[layer]

    def debug(self, layer: str, message: str) -> None:
        """
        Log debug message to layer.

        Args:
            layer (str): Layer name to log to.
            message (str): Debug message to log.
        """
        self.log(layer, "DEBUG", message)

    def info(self, layer: str, message: str) -> None:
        """
        Log info message to layer.

        Args:
            layer (str): Layer name to log to.
            message (str): Info message to log.
        """
        self.log(layer, "INFO", message)

    def warning(self, layer: str, message: str) -> None:
        """
        Log warning message to layer.

        Args:
            layer (str): Layer name to log to.
            message (str): Warning message to log.
        """
        self.log(layer, "WARNING", message)

    def error(self, layer: str, message: str) -> None:
        """
        Log error message to layer.

        Args:
            layer (str): Layer name to log to.
            message (str): Error message to log.
        """
        self.log(layer, "ERROR", message)

    def critical(self, layer: str, message: str) -> None:
        """
        Log critical message to layer.

        Args:
            layer (str): Layer name to log to.
            message (str): Critical message to log.
        """
        self.log(layer, "CRITICAL", message)

    def get_logger(self, layer: str) -> logging.Logger:
        """
        Get the underlying logging.Logger for a layer.

        Args:
            layer (str): Layer name.

        Returns:
            logging.Logger: Configured logging.Logger instance.

        This method provides access to the underlying Python logging.Logger
        instance for advanced usage scenarios where direct access to the
        logger is needed.
        """
        return self.loggers.get(layer, logging.getLogger(f"hydra.{layer}"))

    def _log_warning(self, message: str) -> None:
        """
        Log a warning message to stderr.

        Args:
            message (str): Warning message to log.

        This internal method provides a simple way to log warnings
        during logger setup and operation when the logging system
        itself may not be fully initialized.
        """
        print(f"WARNING: {message}", file=sys.stderr)

    def _log_error(self, message: str) -> None:
        """
        Log an error message to stderr.

        Args:
            message (str): Error message to log.

        This internal method provides a simple way to log errors
        during logger setup and operation when the logging system
        itself may not be fully initialized.
        """
        print(f"ERROR: {message}", file=sys.stderr)
