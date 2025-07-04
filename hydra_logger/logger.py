"""
Main HydraLogger class for multi-layered, multi-destination logging.

This module provides a sophisticated, dynamic logging system that can route different
types of logs across multiple destinations (files, console) with custom folder paths.
The system supports multi-layered logging where each layer can have its own
configuration, destinations, and log levels, enabling complex logging scenarios for
enterprise applications.

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
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional, Union
import threading

from hydra_logger.config import (
    LogDestination,
    LoggingConfig,
    LogLayer,
    create_log_directories,
    get_default_config,
    load_config,
)

# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

# Named color presets for easier customization
NAMED_COLORS = {
    "red": Colors.RED,
    "green": Colors.GREEN,
    "yellow": Colors.YELLOW,
    "blue": Colors.BLUE,
    "magenta": Colors.MAGENTA,
    "cyan": Colors.CYAN,
    "white": Colors.WHITE,
    "bright_red": Colors.BRIGHT_RED,
    "bright_green": Colors.BRIGHT_GREEN,
    "bright_yellow": Colors.BRIGHT_YELLOW,
    "bright_blue": Colors.BRIGHT_BLUE,
    "bright_magenta": Colors.BRIGHT_MAGENTA,
    "bright_cyan": Colors.BRIGHT_CYAN,
}

# Default color mapping for log levels (professional standard)
DEFAULT_COLORS = {
    "DEBUG": Colors.CYAN,
    "INFO": Colors.GREEN,
    "WARNING": Colors.YELLOW,
    "ERROR": Colors.RED,
    "CRITICAL": Colors.BRIGHT_RED,
}

def get_color_config() -> Dict[str, str]:
    """
    Get color configuration from environment variables.
    
    Supports both ANSI codes and named colors:
    - ANSI codes: HYDRA_LOG_COLOR_ERROR='\033[31m'
    - Named colors: HYDRA_LOG_COLOR_ERROR='red'
    
    Returns:
        Dict[str, str]: Color mapping for log levels.
    """
    colors = DEFAULT_COLORS.copy()
    
    # Allow user to override colors via environment variables
    env_colors = {
        "DEBUG": os.getenv("HYDRA_LOG_COLOR_DEBUG"),
        "INFO": os.getenv("HYDRA_LOG_COLOR_INFO"),
        "WARNING": os.getenv("HYDRA_LOG_COLOR_WARNING"),
        "ERROR": os.getenv("HYDRA_LOG_COLOR_ERROR"),
        "CRITICAL": os.getenv("HYDRA_LOG_COLOR_CRITICAL"),
    }
    
    # Update with user-defined colors
    for level, color in env_colors.items():
        if color:
            # Support named colors (e.g., 'red', 'bright_cyan')
            if color in NAMED_COLORS:
                colors[level] = NAMED_COLORS[color]
            else:
                # Assume it's an ANSI code
                colors[level] = color
    
    return colors

def get_layer_color() -> str:
    """
    Get the color for layer names.
    
    Supports both ANSI codes and named colors:
    - ANSI codes: HYDRA_LOG_LAYER_COLOR='\033[35m'
    - Named colors: HYDRA_LOG_LAYER_COLOR='magenta'
    
    Returns:
        str: ANSI color code for layer names.
    """
    layer_color = os.getenv("HYDRA_LOG_LAYER_COLOR", "magenta")
    
    # Support named colors
    if layer_color in NAMED_COLORS:
        return NAMED_COLORS[layer_color]
    
    # Assume it's an ANSI code
    return layer_color

def should_use_colors() -> bool:
    """
    Determine if colors should be used based on environment.
    
    Returns:
        bool: True if colors should be used, False otherwise.
    """
    # Check if colors are explicitly disabled
    if os.getenv("HYDRA_LOG_NO_COLOR", "").lower() in ("1", "true", "yes"):
        return False
    
    # Check if we're in a TTY (terminal)
    if not sys.stdout.isatty():
        return False
    
    # Check if we're in a CI environment (usually no colors)
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("GITLAB_CI"):
        return False
    
    return True

class HydraLoggerError(Exception):
    """
    Base exception for HydraLogger errors.

    This exception is raised when critical errors occur during logger
    initialization, configuration, or operation that cannot be handled
    gracefully by the system.
    """

    pass

class ColoredTextFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to log output.
    
    This formatter adds ANSI color codes to log levels for better readability
    in terminal environments. Colors can be configured via environment variables.
    """
    
    def __init__(self):
        super().__init__(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        self.colors = get_color_config()
        self.layer_color = get_layer_color()
    
    def format(self, record):
        # Get the original formatted message
        formatted = super().format(record)
        
        # Add color to the level name
        level_name = record.levelname
        if level_name in self.colors:
            # Find the level name in the formatted string and color it
            colored_level = f"{self.colors[level_name]}{level_name}{Colors.RESET}"
            formatted = formatted.replace(level_name, colored_level)
        
        # Add color to the layer name (configurable color)
        layer_name = record.name
        colored_layer = f"{self.layer_color}{layer_name}{Colors.RESET}"
        formatted = formatted.replace(layer_name, colored_layer)
        
        return formatted

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
        loggers (Dict[str, logging.Logger]): Dictionary of configured loggers by
            layer name.
    """

    def __init__(self, config: Optional[LoggingConfig] = None, 
                 auto_detect: bool = False,
                 enable_performance_monitoring: bool = False,
                 redact_sensitive: bool = False,
                 date_format: Optional[str] = None,
                 time_format: Optional[str] = None,
                 logger_name_format: Optional[str] = None,
                 message_format: Optional[str] = None):
        """
        Initialize HydraLogger with configuration.

        Args:
            config (Optional[LoggingConfig]): LoggingConfig object. If None,
                uses default config.
            auto_detect (bool): Auto-detect environment and configure accordingly.
                Defaults to False for backward compatibility.
            enable_performance_monitoring (bool): Enable performance monitoring.
                Defaults to False.
            redact_sensitive (bool): Auto-redact sensitive information (emails, 
                passwords, tokens). Defaults to False.
            date_format (Optional[str]): Custom date format string. If None,
                uses environment variable HYDRA_LOG_DATE_FORMAT or default.
            time_format (Optional[str]): Custom time format string. If None,
                uses environment variable HYDRA_LOG_TIME_FORMAT or default.
            logger_name_format (Optional[str]): Custom logger name format string.
                If None, uses environment variable HYDRA_LOG_LOGGER_NAME_FORMAT or default.
            message_format (Optional[str]): Custom message format string. If None,
                uses environment variable HYDRA_LOG_MESSAGE_FORMAT or default.

        Raises:
            HydraLoggerError: If logger setup fails due to configuration issues.

        The initialization process includes:
        - Configuration validation and default setup
        - Directory creation for all file destinations
        - Logger setup for each configured layer
        - Handler creation and configuration
        """
        def _env_or_default(var, default):
            val = os.getenv(var)
            return val if val else default

        try:
            # Store format customization settings, treat empty env as unset
            self.date_format = date_format or _env_or_default("HYDRA_LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
            self.time_format = time_format or _env_or_default("HYDRA_LOG_TIME_FORMAT", "%H:%M:%S")
            self.logger_name_format = logger_name_format or _env_or_default("HYDRA_LOG_LOGGER_NAME_FORMAT", "%(name)s")
            self.message_format = message_format or _env_or_default("HYDRA_LOG_MESSAGE_FORMAT", "%(levelname)s - %(message)s")
            
            # Auto-detect configuration if enabled and no config provided
            if config is None and auto_detect:
                config = self._auto_detect_config()
            
            # Use provided config, auto-detected config, or default config
            if config is None:
                self.config = get_default_config()
            else:
                self.config = config
                
            self.loggers: Dict[str, logging.Logger] = {}
            self._logger_init_lock = threading.Lock()
            self.performance_monitoring = enable_performance_monitoring
            self.redact_sensitive = redact_sensitive
            
            # Create log directories and setup loggers immediately (Week 1 behavior)
            self._setup_loggers()
        except Exception as e:
            raise HydraLoggerError(f"Failed to initialize HydraLogger: {e}") from e

    @classmethod
    def from_config(cls, config_path: Union[str, Path]) -> "HydraLogger":
        """
        Create HydraLogger from configuration file.

        Args:
            config_path (Union[str, Path]): Path to YAML or TOML configuration
                file.

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
        Setup all loggers for configured layers.
        
        This method creates loggers and handlers for all configured layers
        during initialization. It handles directory creation and error recovery.
        """
        try:
            # Create log directories at startup (for file destinations)
            create_log_directories(self.config)
        except OSError as dir_err:
            self._log_warning(f"Directory creation failed: {dir_err}. Falling back to console logging for all layers.")
            for layer in self.config.layers.values():
                layer.destinations = [
                    d if d.type == "console" else LogDestination(type="console", level=d.level, format=getattr(d, "format", "text"))
                    for d in layer.destinations
                ]
        except Exception as e:
            # Handle any other exceptions during directory creation
            self._log_error(f"Failed to setup loggers: {e}")
            raise HydraLoggerError(f"Failed to setup loggers: {e}") from e
        
        # Setup each configured layer
        for layer_name, layer_config in self.config.layers.items():
            self._setup_single_layer(layer_name, layer_config)

    def _setup_single_layer(self, layer_name: str, layer_config: LogLayer) -> None:
        """
        Setup a single logging layer.
        
        Args:
            layer_name (str): Name of the layer to setup.
            layer_config (LogLayer): Configuration for the layer.
        """
        try:
            # Create and configure logger for this layer
            logger = logging.getLogger(layer_name)
            logger.setLevel(getattr(logging, layer_config.level))
            
            # Clear existing handlers
            if logger.hasHandlers():
                logger.handlers.clear()
            
            # Create handlers for each destination
            valid_handlers = 0
            for destination in layer_config.destinations:
                handler = self._create_handler(destination, layer_config.level)
                if handler:
                    logger.addHandler(handler)
                    valid_handlers += 1
            
            if valid_handlers == 0:
                self._log_warning(
                    f"No valid handlers created for layer '{layer_name}'. Layer will not log to any destination."
                )
            
            # Store the logger
            self.loggers[layer_name] = logger
            
        except Exception as e:
            self._log_error(f"Failed to setup layer '{layer_name}': {e}")
            # Create a fallback logger
            try:
                fallback_logger = logging.getLogger(layer_name)
                fallback_logger.setLevel(getattr(logging, self.config.default_level))
                if not fallback_logger.handlers:
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setLevel(getattr(logging, self.config.default_level))
                    console_handler.setFormatter(self._get_formatter())
                    fallback_logger.addHandler(console_handler)
                self.loggers[layer_name] = fallback_logger
            except Exception as fallback_error:
                # If even the fallback fails, create a minimal logger
                self._log_error(f"Fallback logger creation failed for '{layer_name}': {fallback_error}")
                try:
                    minimal_logger = logging.getLogger(f"hydra.{layer_name}")
                    minimal_logger.setLevel(getattr(logging, self.config.default_level))
                    self.loggers[layer_name] = minimal_logger
                except Exception as final_error:
                    # If even the minimal logger fails, create a dummy logger object
                    self._log_error(f"Minimal logger creation failed for '{layer_name}': {final_error}")
                    # Create a minimal logger object that won't fail
                    class DummyLogger:
                        def __init__(self, name, default_level="INFO"):
                            self.name = name
                            self.level = getattr(logging, default_level)
                            self.handlers = []
                        
                        def setLevel(self, level):
                            self.level = level
                        
                        def addHandler(self, handler):
                            self.handlers.append(handler)
                        
                        def hasHandlers(self):
                            return len(self.handlers) > 0
                        
                        def debug(self, msg):
                            pass
                        
                        def info(self, msg):
                            pass
                        
                        def warning(self, msg):
                            pass
                        
                        def error(self, msg):
                            pass
                        
                        def critical(self, msg):
                            pass
                    
                    dummy_logger = DummyLogger(f"hydra.{layer_name}", self.config.default_level)
                    self.loggers[layer_name] = dummy_logger  # type: ignore

    def _create_handler(
        self, destination: LogDestination, layer_level: str
    ) -> Optional[logging.Handler]:
        """
        Create a logging handler for a destination.

        Args:
            destination (LogDestination): LogDestination configuration.
            layer_level (str): The level of the layer this handler belongs to.

        Returns:
            Optional[logging.Handler]: Configured logging handler or None if
                creation fails.

        This method creates the appropriate handler type based on the destination
        configuration. It includes comprehensive error handling and fallback
        mechanisms to ensure robust operation even when individual handlers fail.
        """
        try:
            if destination.type == "file":
                file_handler = self._create_file_handler(destination, layer_level)
                fmt = getattr(destination, "format", "text")
                file_handler.setFormatter(self._get_formatter(fmt))
                return file_handler
            elif destination.type == "console":
                console_handler = self._create_console_handler(destination)
                fmt = getattr(destination, "format", "text")
                console_handler.setFormatter(self._get_formatter(fmt))
                return console_handler
        except ValueError as e:
            self._log_warning(f"Invalid destination configuration: {e}")
            return None
        except Exception as e:
            self._log_warning(f"Failed to create {destination.type} handler: {e}")
            if destination.type == "file":
                try:
                    fallback_handler = self._create_console_handler(destination)
                    fmt = getattr(destination, "format", "text")
                    fallback_handler.setFormatter(self._get_formatter(fmt))
                    return fallback_handler
                except Exception as fallback_error:
                    self._log_error(
                        f"Fallback console handler creation failed: {fallback_error}"
                    )
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
            # Use colored formatter for console output
            fmt = getattr(destination, "format", "text")
            handler.setFormatter(self._get_formatter(fmt))

            return handler

        except Exception as e:
            raise ValueError(f"Failed to create console handler: {e}") from e

    def _get_formatter(self, fmt: str = "text") -> logging.Formatter:
        """
        Get the appropriate formatter based on the specified format.

        Args:
            fmt (str): Format type ('text', 'json', 'csv', 'syslog', 'gelf').

        Returns:
            logging.Formatter: Configured logging formatter.

        Raises:
            ValueError: If the format is not supported or dependencies are missing.
        """
        fmt = fmt.lower()

        if fmt == "json":
            try:
                from pythonjsonlogger.json import JsonFormatter

                # Use the proper JsonFormatter from python-json-logger
                return JsonFormatter(
                    fmt="%(asctime)s %(levelname)s %(name)s %(message)s "
                    "%(filename)s %(lineno)d",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    rename_fields={
                        "asctime": "timestamp",
                        "levelname": "level",
                        "name": "logger",
                    },
                )
            except ImportError:
                self._log_warning(
                    "python-json-logger not installed, falling back to text format."
                )
                return self._get_text_formatter()

        elif fmt == "csv":
            return self._get_csv_formatter()

        elif fmt == "syslog":
            return self._get_syslog_formatter()

        elif fmt == "gelf":
            try:
                # Import graypy to check if it's available
                import graypy  # noqa: F401

                # GELF uses a special handler, but we can create a formatter for it
                return self._get_gelf_formatter()
            except ImportError:
                self._log_warning("graypy not installed, falling back to text format.")
                return self._get_text_formatter()

        else:  # text or unknown
            return self._get_text_formatter()

    def _get_structured_json_formatter(self) -> logging.Formatter:
        """Get a structured JSON formatter that creates valid JSON output."""
        return logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s", '
            '"file": "%(filename)s", "line": %(lineno)d}',
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _get_text_formatter(self) -> logging.Formatter:
        """Get the standard text formatter with custom format support."""
        if should_use_colors():
            return ColoredTextFormatter()
        else:
            # Use custom formats if available, otherwise use defaults
            date_format = getattr(self, 'date_format', "%Y-%m-%d %H:%M:%S")
            logger_name_format = getattr(self, 'logger_name_format', "%(name)s")
            message_format = getattr(self, 'message_format', "%(levelname)s - %(message)s")
            
            # Build the format string using custom components
            format_string = f"%(asctime)s - {logger_name_format} - {message_format} - %(filename)s:%(lineno)d"
            
            return logging.Formatter(format_string, datefmt=date_format)

    def _get_csv_formatter(self) -> logging.Formatter:
        """Get CSV formatter for structured log output."""
        date_format = getattr(self, 'date_format', "%Y-%m-%d %H:%M:%S")
        return logging.Formatter(
            "%(asctime)s,%(name)s,%(levelname)s,%(filename)s,%(lineno)d,%(message)s",
            datefmt=date_format,
        )

    def _get_syslog_formatter(self) -> logging.Formatter:
        """Get syslog-compatible formatter."""
        return logging.Formatter("%(name)s[%(process)d]: %(levelname)s: %(message)s")

    def _get_gelf_formatter(self) -> logging.Formatter:
        """Get GELF-compatible formatter (basic structure)."""
        return logging.Formatter("%(message)s")  # GELF handler will add the structure

    def _get_calling_module_name(self) -> str:
        """
        Get the name of the calling module for automatic module name detection.
        
        Returns:
            str: The name of the calling module or 'DEFAULT' as fallback.
        """
        try:
            import inspect
            # Get the frame of the calling function (2 levels up: current -> logging method -> caller)
            frame = inspect.currentframe()
            if frame:
                # Go up 2 levels to get the caller's frame
                caller_frame = frame.f_back
                if caller_frame:
                    caller_frame = caller_frame.f_back
                    if caller_frame:
                        module_name = caller_frame.f_globals.get('__name__', 'DEFAULT')
                        # Clean up the module name (remove package prefixes if desired)
                        if module_name != '__main__':
                            return module_name
        except Exception:
            pass
        return 'DEFAULT'

    def _log_with_auto_detection(self, level: str, layer_or_message: str, message: Optional[str] = None) -> None:
        """
        Log with automatic module name detection.
        
        Args:
            level (str): Log level (debug, info, warning, error, critical)
            layer_or_message (str): Either layer name or message (if no layer provided)
            message (Optional[str]): Message (if layer was provided in layer_or_message)
        """
        if message is None:
            # Single argument: use automatic module name detection
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            # Two arguments: explicit layer and message
            layer = layer_or_message
            
        # Call the appropriate logging method
        log_method = getattr(self, level.lower())
        log_method(layer, message)

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

    def debug(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "DEBUG", message)

    def info(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "INFO", message)

    def warning(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "WARNING", message)

    def error(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
        self.log(layer, "ERROR", message)

    def critical(self, layer_or_message: str, message: Optional[str] = None) -> None:
        if message is None and layer_or_message is None:
            return
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        if message is None:
            return
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

    def _auto_detect_config(self) -> LoggingConfig:
        """
        Auto-detect environment and create appropriate configuration.
        
        Returns:
            LoggingConfig: Configuration based on detected environment.
            
        This method detects the current environment (development, production, 
        testing) and creates an appropriate configuration with sensible defaults.
        """
        import platform
        
        # Detect environment
        env = os.getenv('ENVIRONMENT', '').lower()
        if not env:
            if os.getenv('FLASK_ENV') == 'development':
                env = 'development'
            elif os.getenv('DJANGO_SETTINGS_MODULE'):
                env = 'production' if os.getenv('DJANGO_DEBUG') != 'True' else 'development'
            elif os.getenv('NODE_ENV'):
                node_env = os.getenv('NODE_ENV')
                env = node_env.lower() if node_env else 'development'
            else:
                # Default to development if no clear indicators
                env = 'development'
        
        # Detect if running in container
        is_container = os.path.exists('/.dockerenv') or os.getenv('KUBERNETES_SERVICE_HOST')
        
        # Detect if running in CI/CD
        is_ci = bool(os.getenv('CI') or os.getenv('GITHUB_ACTIONS') or 
                     os.getenv('GITLAB_CI') or os.getenv('TRAVIS'))
        
        # Detect cloud environments
        is_aws = bool(os.getenv('AWS_REGION') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'))
        is_gcp = bool(os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('K_SERVICE'))
        is_azure = bool(os.getenv('AZURE_FUNCTIONS_ENVIRONMENT') or os.getenv('WEBSITE_SITE_NAME'))
        is_cloud = is_aws or is_gcp or is_azure
        
        # Create base configuration
        config = LoggingConfig(
            layers={}
        )
        
        # Environment-specific configurations
        if env == 'development':
            config.layers = {
                "DEFAULT": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="app.log", format="text")
                    ]
                ),
                "debug": LogLayer(
                    level="DEBUG", 
                    destinations=[
                        LogDestination(type="file", path="debug.log", format="json")
                    ]
                )
            }
        elif env == 'production':
            # Production configuration with cloud awareness
            app_destinations = []
            
            # In cloud environments, prefer console output for better log aggregation
            if is_cloud:
                app_destinations.append(LogDestination(type="console", format="json"))
            else:
                app_destinations.append(LogDestination(type="file", path="app.log", format="json"))
                if not is_container:
                    app_destinations.append(LogDestination(type="file", path="app.log", format="gelf"))
            
            config.layers = {
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=app_destinations
                ),
                "error": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="console" if is_cloud else "file", 
                                     path="error.log" if not is_cloud else None, 
                                     format="json")
                    ]
                ),
                "security": LogLayer(
                    level="WARNING",
                    destinations=[
                        LogDestination(type="console" if is_cloud else "file", 
                                     path="security.log" if not is_cloud else None, 
                                     format="json")
                    ]
                )
            }
        elif env == 'testing':
            config.layers = {
                "DEFAULT": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="file", path="test.log", format="json")
                    ]
                )
            }
        else:
            # Fallback configuration
            config.layers = {
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path="app.log", format="text")
                    ]
                )
            }
        
        # Adjust for container environments
        if is_container:
            # In containers, prefer console output and structured formats
            for layer in config.layers.values():
                for dest in layer.destinations:
                    if dest.type == "file" and dest.format == "text":
                        dest.format = "json"
        
        # Adjust for CI environments
        if is_ci:
            # In CI, prefer console output and minimal file logging
            for layer in config.layers.values():
                layer.destinations = [d for d in layer.destinations if d.type == "console"]
                if not layer.destinations:
                    layer.destinations = [LogDestination(type="console", format="text")]
        
        return config

    def _get_or_create_logger(self, layer: str) -> logging.Logger:
        """
        Get existing logger or create a new one for unknown layers.
        Lazily initializes loggers and handlers for the layer on first use.
        Thread-safe.
        """
        if layer in self.loggers:
            return self.loggers[layer]
        with self._logger_init_lock:
            if layer in self.loggers:
                return self.loggers[layer]
            
            # Create a minimal logger object that won't fail
            class DummyLogger:
                def __init__(self, name, default_level="INFO"):
                    self.name = name
                    self.level = getattr(logging, default_level)
                    self.handlers = []
                
                def setLevel(self, level):
                    self.level = level
                
                def addHandler(self, handler):
                    self.handlers.append(handler)
                
                def hasHandlers(self):
                    return len(self.handlers) > 0
                
                def debug(self, msg):
                    pass
                
                def info(self, msg):
                    pass
                
                def warning(self, msg):
                    pass
                
                def error(self, msg):
                    pass
                
                def critical(self, msg):
                    pass
            
            # Find layer config or fallback
            layer_config = self.config.layers.get(layer)
            if not layer_config and "DEFAULT" in self.config.layers:
                layer_config = self.config.layers["DEFAULT"]
                layer = "DEFAULT"
            if not layer_config:
                # Create a simple logger for unknown layers
                try:
                    logger = logging.getLogger(layer)
                    logger.setLevel(getattr(logging, self.config.default_level))
                    if not logger.handlers:
                        console_handler = logging.StreamHandler(sys.stdout)
                        console_handler.setLevel(getattr(logging, self.config.default_level))
                        console_handler.setFormatter(self._get_formatter())
                        logger.addHandler(console_handler)
                    self.loggers[layer] = logger
                    return logger
                except Exception as e:
                    # If logger creation fails, create a minimal fallback
                    self._log_error(f"Failed to create logger for '{layer}': {e}")
                    try:
                        minimal_logger = logging.getLogger(f"hydra.{layer}")
                        minimal_logger.setLevel(getattr(logging, self.config.default_level))
                        self.loggers[layer] = minimal_logger
                        return minimal_logger
                    except Exception as fallback_error:
                        # If even the fallback fails, create a dummy logger object
                        self._log_error(f"Fallback logger creation failed for '{layer}': {fallback_error}")
                        dummy_logger = DummyLogger(f"hydra.{layer}", self.config.default_level)
                        self.loggers[layer] = dummy_logger  # type: ignore
                        return dummy_logger  # type: ignore
            # Create and configure logger for this layer
            try:
                logger = logging.getLogger(layer)
                logger.setLevel(getattr(logging, layer_config.level))
                if logger.hasHandlers():
                    logger.handlers.clear()
                valid_handlers = 0
                for destination in layer_config.destinations:
                    handler = self._create_handler(destination, layer_config.level)
                    if handler:
                        logger.addHandler(handler)
                        valid_handlers += 1
                if valid_handlers == 0:
                    self._log_warning(
                        f"No valid handlers created for layer '{layer}'. Layer will not log to any destination."
                    )
                self.loggers[layer] = logger
                return logger
            except Exception as e:
                # If logger creation fails, create a minimal fallback
                self._log_error(f"Failed to create logger for '{layer}': {e}")
                try:
                    minimal_logger = logging.getLogger(f"hydra.{layer}")
                    minimal_logger.setLevel(getattr(logging, self.config.default_level))
                    self.loggers[layer] = minimal_logger
                    return minimal_logger
                except Exception as fallback_error:
                    # If even the fallback fails, create a dummy logger object
                    self._log_error(f"Fallback logger creation failed for '{layer}': {fallback_error}")
                    dummy_logger = DummyLogger(f"hydra.{layer}", self.config.default_level)
                    self.loggers[layer] = dummy_logger  # type: ignore
                    return dummy_logger  # type: ignore
