"""
Hydra-Logger Factory System

This module provides a comprehensive factory system for creating and managing
all Hydra-Logger components. The factory pattern ensures consistent component
creation, proper configuration, and easy extensibility.

ARCHITECTURE:
- LoggerFactory: Central factory for creating all logger types
- Component Factories: Specialized factories for specific component types
- Magic Configuration Integration: Pre-configured component creation
- Caching System: Intelligent component caching and reuse
- Validation: Built-in validation during component creation

FACTORY TYPES:
- Logger Creation: Sync, Async, Composite, and CompositeAsync loggers
- Handler Creation: Console, File, and specialized handlers
- Formatter Creation: Colored, JSON, CSV, and custom formatters
- Plugin Creation: Extension and plugin component creation
- Configuration Creation: Dynamic configuration generation
- Composite Creation: Multi-component composite systems
- Engine Creation: Processing engines and optimizers
- Monitor Creation: Performance and health monitoring components
- Security Creation: Security and compliance components

CORE FEATURES:
- Type-safe component creation
- Configuration validation and defaults
- Magic configuration shortcuts
- Component caching and reuse
- Dependency injection support
- Plugin system integration
- Performance optimization
- Memory management
- Error handling and recovery

USAGE EXAMPLES:

Basic Logger Creation:
    from hydra_logger.factories import create_logger, create_sync_logger
    
    # Create logger with configuration
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
- create_web_app_logger: Web application logger
- create_api_logger: API service logger
- create_microservice_logger: Microservice logger
"""

from .logger_factory import create_logger, create_sync_logger, create_async_logger, create_composite_logger, create_composite_async_logger

__all__ = [
    # Factory functions
    "create_logger",
    "create_sync_logger",
    "create_async_logger",
    "create_composite_logger",
    "create_composite_async_logger"
]
