"""
Role: Implements hydra_logger.core.logger_management functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - collections
 - hydra_logger
 - threading
 - typing
Notes:
 - Provides core runtime primitives for logger management.
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
    """Thread-safe registry for named logger instances."""

    def __init__(self, default_config: Optional[LoggingConfig] = None):
        """Initialize the logger manager."""
        self._loggers: Dict[str, Any] = {}
        self._default_config = default_config or get_default_config()
        self._factory = LoggerFactory()
        self._locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()

    def getLogger(
        self,
        name: Optional[str] = None,
        config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
        logger_type: str = "sync",
        **kwargs,
    ) -> Any:
        """Return a cached logger by name or create and register one."""
        if name is None:
            name = "root"

        if name in self._loggers:
            return self._loggers[name]

        with self._locks[name]:
            if name in self._loggers:
                return self._loggers[name]

            logger = self._create_logger(name, config, logger_type, **kwargs)

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
            if config is None:
                config = self._create_config_for_logger(name)

            logger = self._factory.create_logger(
                config=config, logger_type=logger_type, **kwargs
            )

            if hasattr(logger, "name"):
                logger.name = name

            return logger

        except Exception as e:
            raise HydraLoggerError(f"Failed to create logger '{name}': {e}")

    def _create_config_for_logger(self, name: str) -> LoggingConfig:
        """Create configuration for a specific logger."""
        config = self._default_config
        if name != "root" and "." in name:
            pass

        return config

    def hasLogger(self, name: str) -> bool:
        """Check if a logger with the given name exists."""
        return name in self._loggers

    def removeLogger(self, name: str) -> bool:
        """Remove a logger from the registry and close it when supported."""
        if name in self._loggers:
            logger = self._loggers[name]

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
    """Module-level accessor mirroring Python's `logging.getLogger` API."""
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
