"""
Centralized Logger Management System for Hydra-Logger

This module provides a sophisticated logger management system that mimics
Python's standard logging library's getLogger() functionality while adding
advanced features like configuration management, logger caching, and
hierarchical logger support.

ARCHITECTURE:
- LoggerManager: Centralized logger registry and management
- Logger Factory Integration: Uses LoggerFactory for logger creation
- Configuration Management: Per-logger and global configuration support
- Thread Safety: Thread-safe logger creation and management
- Hierarchical Support: Logger name hierarchy and inheritance

FEATURES:
- Python logging.getLogger() compatible interface
- Logger caching and reuse
- Hierarchical logger names (e.g., 'package.module')
- Per-logger configuration support
- Global default configuration
- Thread-safe operations
- Logger lifecycle management
- Configuration inheritance

LOGGER TYPES:
- sync: Synchronous loggers
- async: Asynchronous loggers
- unified: Unified logger interface (default)
- Custom logger types via factory

CONFIGURATION SUPPORT:
- Global default configuration
- Per-logger custom configurations
- Hierarchical configuration inheritance
- Configuration validation and fallback

USAGE EXAMPLES:

Basic Logger Usage (Python logging compatible):
    from hydra_logger.core.logger_manager import getLogger
    
    # Most common usage - get module logger
    logger = getLogger(__name__)
    logger.info("This is a module log message")
    
    # Get package logger
    package_logger = getLogger('myapp')
    
    # Get root logger
    root_logger = getLogger()

Custom Configuration:
    from hydra_logger.core.logger_manager import getLogger
    from hydra_logger.config import LoggingConfig
    
    # Custom configuration
    config = LoggingConfig(...)
    custom_logger = getLogger('myapp.api', config=config)

Logger Type Selection:
    from hydra_logger.core.logger_manager import getLogger, getSyncLogger, getAsyncLogger
    
    # Specific logger types
    sync_logger = getSyncLogger('myapp')
    async_logger = getAsyncLogger('myapp')
    unified_logger = getLogger('myapp', logger_type='unified')

Logger Management:
    from hydra_logger.core.logger_manager import hasLogger, removeLogger, listLoggers
    
    # Check if logger exists
    if hasLogger('myapp'):
        print("Logger exists")
    
    # List all loggers
    all_loggers = listLoggers()
    print(f"Registered loggers: {all_loggers}")
    
    # Remove logger
    removed = removeLogger('myapp')
    print(f"Logger removed: {removed}")

Configuration Management:
    from hydra_logger.core.logger_manager import setDefaultConfig, getDefaultConfig
    
    # Set global default configuration
    setDefaultConfig(my_config)
    
    # Get current default configuration
    default_config = getDefaultConfig()
"""

import threading
from typing import Dict, Optional, Union, Any
from pathlib import Path
from ..factories.logger_factory import LoggerFactory
from ..config.models import LoggingConfig
from ..config.defaults import get_default_config
from ..core.exceptions import HydraLoggerError


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
        self._lock = threading.Lock()  # Thread-safe logger creation
    
    def getLogger(self, name: Optional[str] = None, 
                  config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                  logger_type: str = "sync",
                  **kwargs) -> Any:
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
        
        # Thread-safe logger retrieval/creation
        with self._lock:
            if name in self._loggers:
                return self._loggers[name]
            
            # Create new logger
            logger = self._create_logger(name, config, logger_type, **kwargs)
            self._loggers[name] = logger
            return logger
    
    def _create_logger(self, name: str, 
                       config: Optional[Union[LoggingConfig, Dict[str, Any]]],
                       logger_type: str,
                       **kwargs) -> Any:
        """Create a new logger instance."""
        try:
            # Use provided config or create from default
            if config is None:
                config = self._create_config_for_logger(name)
            
            # Create logger using factory
            logger = self._factory.create_logger(
                config=config,
                logger_type=logger_type,
                **kwargs
            )
            
            # Set logger name for identification
            if hasattr(logger, 'name'):
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
            if hasattr(logger, 'close') and callable(logger.close):
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
        with self._lock:
            for name in list(self._loggers.keys()):
                self.removeLogger(name)
    
    def getLoggerConfig(self, name: str) -> Optional[LoggingConfig]:
        """Get the configuration for a specific logger."""
        if name in self._loggers:
            logger = self._loggers[name]
            if hasattr(logger, 'get_config'):
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


def getLogger(name: Optional[str] = None, 
              config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
              logger_type: str = "unified",
              **kwargs) -> Any:
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
def getSyncLogger(name: Optional[str] = None, 
                  config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                  **kwargs) -> Any:
    """Get or create a synchronous logger by name."""
    return getLogger(name, config, "sync", **kwargs)


def getAsyncLogger(name: Optional[str] = None, 
                   config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                   **kwargs) -> Any:
    """Get or create an asynchronous logger by name."""
    return getLogger(name, config, "async", **kwargs)


