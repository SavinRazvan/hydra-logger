"""
Hydra-Logger Factory System

This module provides a simplified factory system for creating and managing
all Hydra-Logger components. The factory pattern ensures consistent component
creation, proper configuration, and easy extensibility.

ARCHITECTURE:
- LoggerFactory: Central factory for creating all logger types
- Magic Configuration Integration: Pre-configured component creation
- Caching System: Intelligent component caching and reuse
- Validation: Built-in validation during component creation

FACTORY TYPES:
- Logger Creation: Sync, Async, Composite, and CompositeAsync loggers
- Magic Configuration Loggers: Pre-configured loggers for common use cases

CORE FEATURES:
- Type-safe component creation
- Configuration validation and defaults
- Magic configuration shortcuts
- Component caching and reuse
- Performance optimization
- Memory management
- Error handling and recovery

USAGE EXAMPLES:

Basic Logger Creation:
    from hydra_logger.factories import create_logger, create_sync_logger
    
    # Create logger with name
    logger = create_logger("MyLogger", logger_type="sync")
    
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
        name="MyCompositeLogger",
        components=[sync_logger, async_logger]
    )

Factory Pattern Usage:
    from hydra_logger.factories import LoggerFactory
    
    factory = LoggerFactory()
    
    # Create with magic configuration
    logger = factory.create_logger_with_magic("production", "async")
    
    # Create with custom configuration
    logger = factory.create_logger(config, "sync")
    
    # Cache management
    factory.cache_logger("my_logger", logger)
    cached = factory.get_cached_logger("my_logger")

AVAILABLE FACTORIES:
- create_logger: Main logger creation function
- create_sync_logger: Synchronous logger creation
- create_async_logger: Asynchronous logger creation
- create_composite_logger: Composite logger creation
- create_composite_async_logger: Composite async logger creation
- create_production_logger: Production-ready logger
- create_development_logger: Development logger
- create_testing_logger: Testing logger
- create_custom_logger: Custom configuration logger
"""

from .logger_factory import (
    create_logger, 
    create_sync_logger, 
    create_async_logger, 
    create_composite_logger, 
    create_composite_async_logger,
    create_default_logger,
    create_development_logger,
    create_production_logger,
    create_custom_logger
)

__all__ = [
    # Factory functions
    "create_logger",
    "create_sync_logger",
    "create_async_logger",
    "create_composite_logger",
    "create_composite_async_logger",
    # Magic configuration functions
    "create_default_logger",
    "create_development_logger",
    "create_production_logger",
    "create_custom_logger"
]
