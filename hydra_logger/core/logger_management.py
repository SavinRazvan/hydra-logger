"""
Role: Logger management implementation.
Used By:
 - hydra_logger/__init__.py for `getLogger`/`getSyncLogger`/`getAsyncLogger` public API exports.
Depends On:
 - threading
 - typing
 - collections
 - factories
 - config
Notes:
 - Provides cached logger manager and Python-logging-style convenience accessors.
"""

import threading
from collections import defaultdict
from typing import Any, Dict, Optional, Union

from ..config.defaults import get_default_config
from ..config.models import LoggingConfig
from ..core.exceptions import HydraLoggerError

# from pathlib import Path  # unused
from ..factories.logger_factory import LoggerFactory


class LoggerManager:
    """
    Centralized logger manager providing getLogger() functionality.

    This class mimics Python's logging.getLogger() behavior:
    - Caches loggers by name
    - Provides hierarchical logger names
    - Automatic inheritance from parent loggers
    - Shared configuration across loggers
    """

    def __init__(self, default_config: Optional[LoggingConfig] = None):
        """Initialize the logger manager."""
        self._loggers: Dict[str, Any] = {}
        self._default_config = default_config or get_default_config()
        self._factory = LoggerFactory()
        # Use separate locks for different logger names to reduce contention
        self._locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()  # For logger registry operations

    def getLogger(
        self,
        name: Optional[str] = None,
        config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
        logger_type: str = "sync",
        **kwargs,
    ) -> Any:
        """
        Get or create a logger by name.

        This mimics Python's logging.getLogger() behavior:
        - If logger exists, return cached instance
        - If logger doesn't exist, create new one
        - Logger names can be hierarchical (e.g., 'package.module')

        Args:
            name: Logger name (default: None for root logger)
            config: Logger configuration (default: global default)
            logger_type: Type of logger to create
            **kwargs: Additional logger parameters

        Returns:
            Logger instance

        Examples:
            # Get root logger
            root_logger = getLogger()

            # Get package logger
            package_logger = getLogger('myapp')

            # Get module logger (most common pattern)
            module_logger = getLogger(__name__)

            # Get specific logger with config
            custom_logger = getLogger('myapp.api', config=my_config)
        """
        if name is None:
            name = "root"

        # Fast path: check if logger exists without locking
        if name in self._loggers:
            return self._loggers[name]

        # Use per-logger lock to reduce contention
        with self._locks[name]:
            # Double-check pattern: logger might have been created by another thread
            if name in self._loggers:
                return self._loggers[name]

            # Create new logger
            logger = self._create_logger(name, config, logger_type, **kwargs)

            # Update registry with global lock (minimal time)
            with self._global_lock:
                self._loggers[name] = logger

            return logger

    def _create_logger(
        self,
        name: str,
        config: Optional[Union[LoggingConfig, Dict[str, Any]]],
        logger_type: str,
        **kwargs,
    ) -> Any:
        """Create a new logger instance."""
        try:
            # Use provided config or create from default
            if config is None:
                config = self._create_config_for_logger(name)

            # Create logger using factory
            logger = self._factory.create_logger(
                config=config, logger_type=logger_type, **kwargs
            )

            # Set logger name for identification
            if hasattr(logger, "name"):
                logger.name = name

            return logger

        except Exception as e:
            # Fallback to basic logger if creation fails
            raise HydraLoggerError(f"Failed to create logger '{name}': {e}")

    def _create_config_for_logger(self, name: str) -> LoggingConfig:
        """Create configuration for a specific logger."""
        # Start with default config
        config = self._default_config

        # For hierarchical loggers, we could add specific configurations
        # based on the logger name (e.g., 'myapp.api' gets API-specific config)
        if name != "root" and "." in name:
            # Could implement hierarchical config inheritance here
            pass

        return config

    def hasLogger(self, name: str) -> bool:
        """Check if a logger with the given name exists."""
        return name in self._loggers

    def removeLogger(self, name: str) -> bool:
        """
        Remove a logger from the registry.

        Args:
            name: Logger name to remove

        Returns:
            True if logger was removed, False if not found
        """
        if name in self._loggers:
            logger = self._loggers[name]

            # Close logger if it has close method
            if hasattr(logger, "close") and callable(logger.close):
                try:
                    logger.close()
                except Exception:
                    pass  # Ignore errors during cleanup

            del self._loggers[name]
            return True

        return False

    def listLoggers(self) -> list:
        """List all registered logger names."""
        return list(self._loggers.keys())

    def clearLoggers(self) -> None:
        """Clear all registered loggers."""
        with self._global_lock:
            for name in list(self._loggers.keys()):
                self.removeLogger(name)

    def getLoggerConfig(self, name: str) -> Optional[LoggingConfig]:
        """Get the configuration for a specific logger."""
        if name in self._loggers:
            logger = self._loggers[name]
            if hasattr(logger, "get_config"):
                return logger.get_config()
        return None

    def setDefaultConfig(self, config: LoggingConfig) -> None:
        """Set the default configuration for new loggers."""
        self._default_config = config

    def getDefaultConfig(self) -> LoggingConfig:
        """Get the current default configuration."""
        return self._default_config


# Global logger manager instance
_logger_manager = LoggerManager()


def getLogger(
    name: Optional[str] = None,
    config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
    logger_type: str = "sync",
    **kwargs,
) -> Any:
    """
    Get or create a logger by name.

    This is the main entry point for getting loggers, similar to Python's
    logging.getLogger() function.

    Args:
        name: Logger name (default: None for root logger)
        config: Logger configuration (default: global default)
        logger_type: Type of logger to create
        **kwargs: Additional logger parameters

    Returns:
        Logger instance

    Examples:
        # Most common usage - get module logger
        logger = getLogger(__name__)
        logger.info("This is a module log message")

        # Get package logger
        package_logger = getLogger('myapp')

        # Get specific logger with custom config
        api_logger = getLogger('myapp.api', config=api_config)

        # Get root logger
        root_logger = getLogger()
    """
    return _logger_manager.getLogger(name, config, logger_type, **kwargs)


def hasLogger(name: str) -> bool:
    """Check if a logger with the given name exists."""
    return _logger_manager.hasLogger(name)


def removeLogger(name: str) -> bool:
    """Remove a logger from the registry."""
    return _logger_manager.removeLogger(name)


def listLoggers() -> list:
    """List all registered logger names."""
    return _logger_manager.listLoggers()


def clearLoggers() -> None:
    """Clear all registered loggers."""
    _logger_manager.clearLoggers()


def setDefaultConfig(config: LoggingConfig) -> None:
    """Set the default configuration for new loggers."""
    _logger_manager.setDefaultConfig(config)


def getDefaultConfig() -> LoggingConfig:
    """Get the current default configuration."""
    return _logger_manager.getDefaultConfig()


# Convenience functions for common logger types
def getSyncLogger(
    name: Optional[str] = None,
    config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
    **kwargs,
) -> Any:
    """Get or create a synchronous logger by name."""
    return getLogger(name, config, "sync", **kwargs)


def getAsyncLogger(
    name: Optional[str] = None,
    config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
    **kwargs,
) -> Any:
    """Get or create an asynchronous logger by name."""
    return getLogger(name, config, "async", **kwargs)
