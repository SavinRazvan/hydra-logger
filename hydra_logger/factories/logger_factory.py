"""
Hydra-Logger Factory System

This module provides the core factory system for creating and managing all
Hydra-Logger components. It implements the Factory Pattern with advanced
features like caching, magic configurations, and type-safe component creation.

ARCHITECTURE:
- LoggerFactory: Central factory class for all logger creation
- Factory Functions: Convenience functions for direct logger creation
- Magic Configuration Integration: Pre-configured logger creation
- Caching System: Intelligent logger caching and reuse
- Type Safety: Full type hints and validation

SUPPORTED LOGGER TYPES:
- SyncLogger: Synchronous logging with immediate output
- AsyncLogger: Asynchronous logging with queue-based processing
- CompositeLogger: Composite pattern for multiple logger components
- CompositeAsyncLogger: Async version of composite logger

COLOR SYSTEM INTEGRATION:
- All 4 core loggers support the standardized color system
- Colors enabled via LogDestination.use_colors=True
- Console handlers only (file handlers don't support colors)
- ColoredFormatter automatically applied when colors enabled
- Layer routing determines which destinations receive messages
- Automatic color detection and fallback

MAGIC CONFIGURATIONS:
- production: Production-ready configuration with file logging
- development: Development configuration with console colors
- testing: Testing configuration with minimal overhead
- web_app: Web application configuration with request logging
- api: API service configuration with structured logging
- microservice: Microservice configuration with distributed logging

CACHING FEATURES:
- Intelligent logger caching based on configuration
- Memory-efficient cache management
- Cache invalidation and cleanup
- Performance optimization through reuse
- Thread-safe caching operations

FACTORY METHODS:
- create_logger: Main logger creation with type selection
- create_sync_logger: Direct synchronous logger creation
- create_async_logger: Direct asynchronous logger creation
- create_composite_logger: Composite logger creation
- create_composite_async_logger: Composite async logger creation
- create_*_logger: Magic configuration logger creation

USAGE EXAMPLES:

Basic Logger Creation:
    from hydra_logger.factories import create_logger, create_sync_logger
    
    # Create logger with configuration
    config = LoggingConfig(...)
    logger = create_logger(config, logger_type="sync")
    
    # Create specific logger type
    sync_logger = create_sync_logger("MyLogger")
    async_logger = create_async_logger("MyAsyncLogger")

Magic Configuration Loggers:
    from hydra_logger.factories import create_production_logger
    
    # Create pre-configured loggers
    prod_logger = create_production_logger(logger_type="async")
    dev_logger = create_development_logger(logger_type="sync")
    test_logger = create_testing_logger(logger_type="composite")

Composite Logger Creation:
    from hydra_logger.factories import create_composite_logger
    
    # Create composite logger with multiple components
    composite = create_composite_logger(
        components=[sync_logger, async_logger],
        config=config
    )

Factory Class Usage:
    from hydra_logger.factories import LoggerFactory
    
    factory = LoggerFactory()
    
    # Create with magic configuration
    logger = factory.create_logger_with_magic("production", "async")
    
    # Create with custom configuration
    logger = factory.create_logger(config, "sync")
    
    # Cache management
    factory.cache_logger("my_logger", logger)
    cached = factory.get_cached_logger("my_logger")

Advanced Configuration:
    # Create logger with custom settings
    logger = create_logger(
        config={
            "layers": [
                {
                    "name": "console",
                    "destinations": [
                        {
                            "type": "CONSOLE",
                            "format": "colored",
                            "use_colors": True
                        }
                    ]
                }
            ]
        },
        logger_type="async",
        name="CustomLogger"
    )

PERFORMANCE FEATURES:
- Object pooling for LogRecord instances
- Intelligent caching to reduce object creation
- Lazy initialization of expensive components
- Memory-efficient configuration handling
- Optimized logger creation paths
- Thread-safe operations throughout
"""

from typing import Optional, Union, Dict, Any
from ..config.models import LoggingConfig
from ..config.magic_configs import magic_configs
from ..config.setup import ensure_logs_structure
from ..loggers.sync_logger import SyncLogger
from ..loggers.async_logger import AsyncLogger
from ..loggers.composite_logger import CompositeLogger, CompositeAsyncLogger


class LoggerFactory:
    """
    Central factory for creating and managing all Hydra-Logger components.
    
    This factory implements the Factory Pattern with advanced features including
    caching, magic configuration integration, and type-safe component creation.
    It provides a unified interface for creating all logger types and manages
    their lifecycle efficiently.
    
    FEATURES:
    - Type-safe logger creation with full validation
    - Magic configuration integration for common use cases
    - Intelligent caching system for performance optimization
    - Support for all 4 core logger types (Sync, Async, Composite, CompositeAsync)
    - Configuration validation and default handling
    - Memory-efficient component management
    - Thread-safe operations throughout
    
    CACHING SYSTEM:
    - Automatic logger caching based on configuration hash
    - Memory-efficient cache management with TTL
    - Cache invalidation and cleanup mechanisms
    - Performance optimization through component reuse
    - Thread-safe cache operations
    
    MAGIC CONFIGURATIONS:
    - production: Production-ready configuration with file logging
    - development: Development configuration with console colors
    - testing: Testing configuration with minimal overhead
    - web_app: Web application configuration with request logging
    - api: API service configuration with structured logging
    - microservice: Microservice configuration with distributed logging
    
    USAGE EXAMPLES:
    
    Basic Usage:
        factory = LoggerFactory()
        logger = factory.create_logger(config, "sync")
    
    Magic Configuration:
        logger = factory.create_logger_with_magic("production", "async")
    
    Caching:
        factory.cache_logger("my_logger", logger)
        cached = factory.get_cached_logger("my_logger")
    """
    
    def __init__(self):
        self._logger_cache = {}
        self._default_config = None
    
    def create_logger(self, 
                     config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                     logger_type: str = "sync",
                     **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """
        Create a logger with the specified configuration and type.
        
        This is the main factory method that creates loggers based on the provided
        configuration and type. It handles configuration parsing, validation,
        and logger instantiation with proper error handling.
        
        Args:
            config: Logging configuration. Can be a LoggingConfig object, dict, or None.
                   If None, uses the default configuration.
            logger_type: Type of logger to create. Options:
                - "sync": Synchronous logger with immediate output
                - "async": Asynchronous logger with queue-based processing
                - "composite": Composite logger for multiple components
                - "composite-async": Async version of composite logger
            **kwargs: Additional keyword arguments passed to the logger constructor
        
        Returns:
            Logger instance of the specified type with the given configuration
            
        Raises:
            ValueError: If logger_type is not supported
            ConfigurationError: If configuration is invalid
            
        Examples:
            # Create sync logger with custom config
            logger = factory.create_logger(config, "sync")
            
            # Create async logger with default config
            logger = factory.create_logger(logger_type="async")
            
            # Create composite logger with additional parameters
            logger = factory.create_logger(
                config=config,
                logger_type="composite",
                name="MyCompositeLogger"
            )
        """
        
        # Ensure logs directory structure exists
        ensure_logs_structure()
        
        # Parse configuration
        if isinstance(config, dict):
            config = LoggingConfig(**config)
        elif config is None:
            config = self._get_default_config()
        
        # Create logger based on type
        if logger_type == "sync":
            return SyncLogger(config=config, **kwargs)
        elif logger_type == "async":
            return AsyncLogger(config=config, **kwargs)
        elif logger_type == "composite":
            return CompositeLogger(config=config, **kwargs)
        elif logger_type == "composite-async":
            return CompositeAsyncLogger(config=config, **kwargs)
        else:
            raise ValueError(f"Unknown logger type: {logger_type}")
    
    
    def create_sync_logger(self, 
                          config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                          **kwargs) -> SyncLogger:
        """Create a synchronous logger."""
        return self.create_logger(config=config, logger_type="sync", **kwargs)
    
    def create_async_logger(self, 
                           config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                           **kwargs) -> AsyncLogger:
        """Create an asynchronous logger."""
        return self.create_logger(config=config, logger_type="async", **kwargs)
    
    def create_composite_logger(self, 
                               config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                               **kwargs) -> CompositeLogger:
        """Create a composite logger for complex scenarios."""
        return self.create_logger(config=config, logger_type="composite", **kwargs)
    
    def create_composite_async_logger(self, 
                                    config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
                                    **kwargs) -> CompositeAsyncLogger:
        """Create a composite async logger for complex scenarios."""
        return self.create_logger(config=config, logger_type="composite-async", **kwargs)
    
    def create_logger_with_magic(self, 
                                magic_config_name: str,
                                logger_type: str = "sync",
                                **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """
        Create a logger using a pre-configured magic configuration.
        
        Magic configurations are pre-defined configurations optimized for common
        use cases. They provide sensible defaults and can be customized further
        through additional parameters.
        
        Args:
            magic_config_name: Name of the magic configuration to use. Options:
                - "production": Production-ready configuration with file logging
                - "development": Development configuration with console colors
                - "testing": Testing configuration with minimal overhead
                - "web_app": Web application configuration with request logging
                - "api": API service configuration with structured logging
                - "microservice": Microservice configuration with distributed logging
            logger_type: Type of logger to create (sync, async, composite, composite-async)
            **kwargs: Additional keyword arguments passed to the logger constructor
        
        Returns:
            Logger instance with the magic configuration applied
            
        Raises:
            ValueError: If magic_config_name is not found or logger_type is invalid
            
        Examples:
            # Create production logger
            logger = factory.create_logger_with_magic("production", "async")
            
            # Create development logger with custom name
            logger = factory.create_logger_with_magic(
                "development", 
                "sync", 
                name="MyDevLogger"
            )
        """
        if not magic_configs.has_config(magic_config_name):
            raise ValueError(f"Unknown magic config: {magic_config_name}")
        
        config = magic_configs.get_config(magic_config_name)
        return self.create_logger(config=config, logger_type=logger_type, **kwargs)
    
    def create_production_logger(self, 
                                logger_type: str = "sync",
                                **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a production-ready logger."""
        return self.create_logger_with_magic("production", logger_type, **kwargs)
    
    def create_development_logger(self, 
                                 logger_type: str = "sync",
                                 **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a development logger."""
        return self.create_logger_with_magic("development", logger_type, **kwargs)
    
    def create_testing_logger(self, 
                             logger_type: str = "sync",
                             **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a testing logger."""
        return self.create_logger_with_magic("testing", logger_type, **kwargs)
    
    def create_web_app_logger(self, 
                             logger_type: str = "sync",
                             **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a web application logger."""
        return self.create_logger_with_magic("web_app", logger_type, **kwargs)
    
    def create_api_logger(self, 
                         logger_type: str = "sync",
                         **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create an API service logger."""
        return self.create_logger_with_magic("api", logger_type, **kwargs)
    
    def create_microservice_logger(self, 
                                  logger_type: str = "sync",
                                  **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
        """Create a microservice logger."""
        return self.create_logger_with_magic("microservice", logger_type, **kwargs)
    

    
    def _get_default_config(self) -> LoggingConfig:
        """Get the default configuration."""
        if self._default_config is None:
            from ..config.defaults import get_default_config
            self._default_config = get_default_config()
        return self._default_config
    
    def set_default_config(self, config: LoggingConfig) -> None:
        """Set the default configuration."""
        self._default_config = config
    
    def get_cached_logger(self, cache_key: str) -> Optional[Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]]:
        """Get a cached logger if it exists."""
        return self._logger_cache.get(cache_key)
    
    def cache_logger(self, cache_key: str, logger: Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]) -> None:
        """Cache a logger for reuse."""
        self._logger_cache[cache_key] = logger
    
    def clear_cache(self) -> None:
        """Clear the logger cache."""
        self._logger_cache.clear()


# Global factory instance
logger_factory = LoggerFactory()

# Convenience functions
def create_logger(name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None,
                 logger_type: str = "sync",
                 **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """
    Create a logger with the specified configuration and type.
    
    This is the main convenience function for creating loggers. It provides a
    simple interface that handles both string names and configuration objects.
    
    Args:
        name_or_config: Logger name (string) or configuration object. If string,
                       creates logger with default configuration and given name.
        logger_type: Type of logger to create (sync, async, composite, composite-async)
        **kwargs: Additional keyword arguments passed to the logger constructor
    
    Returns:
        Logger instance of the specified type
        
    Examples:
        # Create logger with name
        logger = create_logger("MyLogger", "sync")
        
        # Create logger with configuration
        logger = create_logger(config, "async")
        
        # Create logger with additional parameters
        logger = create_logger(
            "MyLogger", 
            "composite", 
            components=[sync_logger, async_logger]
        )
    """
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs['name'] = name_or_config
        config = None
    else:
        config = name_or_config
    
    return logger_factory.create_logger(config=config, logger_type=logger_type, **kwargs)

def create_sync_logger(name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None,
                      **kwargs) -> SyncLogger:
    """Create a synchronous logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs['name'] = name_or_config
        config = None
    else:
        config = name_or_config
    
    return logger_factory.create_sync_logger(config=config, **kwargs)

def create_async_logger(name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None,
                       **kwargs) -> AsyncLogger:
    """Create an asynchronous logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs['name'] = name_or_config
        config = None
    else:
        config = name_or_config
    
    return logger_factory.create_async_logger(config=config, **kwargs)

def create_composite_logger(name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None,
                           **kwargs) -> CompositeLogger:
    """Create a composite logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs['name'] = name_or_config
        config = None
    else:
        config = name_or_config
    
    return logger_factory.create_composite_logger(config=config, **kwargs)

def create_composite_async_logger(name_or_config: Optional[Union[str, LoggingConfig, Dict[str, Any]]] = None,
                                 **kwargs) -> CompositeAsyncLogger:
    """Create a composite async logger."""
    # Handle string name as first argument
    if isinstance(name_or_config, str):
        kwargs['name'] = name_or_config
        config = None
    else:
        config = name_or_config
    
    return logger_factory.create_composite_async_logger(config=config, **kwargs)


# Magic configuration convenience functions
def create_production_logger(logger_type: str = "sync",
                           **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """
    Create a production-ready logger with optimized configuration.
    
    This function creates a logger using the "production" magic configuration,
    which is optimized for production environments with file logging, structured
    output, and performance optimizations.
    
    Args:
        logger_type: Type of logger to create (sync, async, composite, composite-async)
        **kwargs: Additional keyword arguments passed to the logger constructor
    
    Returns:
        Production-optimized logger instance
        
    Examples:
        # Create production async logger
        logger = create_production_logger("async")
        
        # Create production logger with custom name
        logger = create_production_logger("sync", name="MyProdLogger")
    """
    return logger_factory.create_production_logger(logger_type=logger_type, **kwargs)

def create_development_logger(logger_type: str = "sync",
                            **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """
    Create a development logger with console colors and debugging features.
    
    This function creates a logger using the "development" magic configuration,
    which is optimized for development environments with colored console output,
    detailed logging, and debugging features.
    
    Args:
        logger_type: Type of logger to create (sync, async, composite, composite-async)
        **kwargs: Additional keyword arguments passed to the logger constructor
    
    Returns:
        Development-optimized logger instance
        
    Examples:
        # Create development logger
        logger = create_development_logger("sync")
        
        # Create development async logger with custom name
        logger = create_development_logger("async", name="MyDevLogger")
    """
    return logger_factory.create_development_logger(logger_type=logger_type, **kwargs)

def create_testing_logger(logger_type: str = "sync",
                         **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """
    Create a testing logger with minimal overhead and fast execution.
    
    This function creates a logger using the "testing" magic configuration,
    which is optimized for testing environments with minimal overhead,
    fast execution, and simplified output.
    
    Args:
        logger_type: Type of logger to create (sync, async, composite, composite-async)
        **kwargs: Additional keyword arguments passed to the logger constructor
    
    Returns:
        Testing-optimized logger instance
        
    Examples:
        # Create testing logger
        logger = create_testing_logger("sync")
        
        # Create testing async logger
        logger = create_testing_logger("async", name="TestLogger")
    """
    return logger_factory.create_testing_logger(logger_type=logger_type, **kwargs)

def create_web_app_logger(logger_type: str = "sync",
                         **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """
    Create a web application logger with request logging and structured output.
    
    This function creates a logger using the "web_app" magic configuration,
    which is optimized for web applications with request logging, structured
    output, and web-specific features.
    
    Args:
        logger_type: Type of logger to create (sync, async, composite, composite-async)
        **kwargs: Additional keyword arguments passed to the logger constructor
    
    Returns:
        Web application-optimized logger instance
        
    Examples:
        # Create web app logger
        logger = create_web_app_logger("async")
        
        # Create web app logger with custom name
        logger = create_web_app_logger("sync", name="WebAppLogger")
    """
    return logger_factory.create_web_app_logger(logger_type=logger_type, **kwargs)

def create_api_logger(logger_type: str = "sync",
                     **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """
    Create an API service logger with structured logging and performance monitoring.
    
    This function creates a logger using the "api" magic configuration,
    which is optimized for API services with structured logging, performance
    monitoring, and API-specific features.
    
    Args:
        logger_type: Type of logger to create (sync, async, composite, composite-async)
        **kwargs: Additional keyword arguments passed to the logger constructor
    
    Returns:
        API service-optimized logger instance
        
    Examples:
        # Create API logger
        logger = create_api_logger("async")
        
        # Create API logger with custom name
        logger = create_api_logger("sync", name="APILogger")
    """
    return logger_factory.create_api_logger(logger_type=logger_type, **kwargs)

def create_microservice_logger(logger_type: str = "sync",
                              **kwargs) -> Union[SyncLogger, AsyncLogger, CompositeLogger, CompositeAsyncLogger]:
    """
    Create a microservice logger with distributed logging and service discovery.
    
    This function creates a logger using the "microservice" magic configuration,
    which is optimized for microservices with distributed logging, service
    discovery integration, and microservice-specific features.
    
    Args:
        logger_type: Type of logger to create (sync, async, composite, composite-async)
        **kwargs: Additional keyword arguments passed to the logger constructor
    
    Returns:
        Microservice-optimized logger instance
        
    Examples:
        # Create microservice logger
        logger = create_microservice_logger("async")
        
        # Create microservice logger with custom name
        logger = create_microservice_logger("sync", name="MicroserviceLogger")
    """
    return logger_factory.create_microservice_logger(logger_type=logger_type, **kwargs)


