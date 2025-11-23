"""
Loggers Module for Hydra-Logger

This module provides all logger implementations including sync, async, unified,
and composite loggers. It serves as the main entry point for all logging
functionality in Hydra-Logger.

ARCHITECTURE:
- BaseLogger: Abstract base class for all logger implementations
- SyncLogger: Synchronous logging with immediate output
- AsyncLogger: Asynchronous logging with queue-based processing
- CompositeLogger: Composite pattern for multiple logger components
- CompositeAsyncLogger: Async version of composite logger

CORE LOGGER TYPES:
- SyncLogger: Synchronous logging with multi-layer support
- AsyncLogger: Asynchronous logging with async processing
- CompositeLogger: Composite pattern for complex logging scenarios
- CompositeAsyncLogger: Async composite logger

PERFORMANCE FEATURES:
- Optimized logging with minimal overhead
- Multi-layer logging with independent configurations
- Built-in performance monitoring and health checks
- Memory leak prevention and resource management
- Plugin system for extensibility
- Security features (PII detection, sanitization)

USAGE EXAMPLES:

Basic Logger Creation:
    from hydra_logger.loggers import SyncLogger, AsyncLogger
    from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination

    # Create configuration
    destination = LogDestination(type="console", use_colors=True)
    layer = LogLayer(destinations=[destination])
    config = LoggingConfig(layers={"my_layer": layer})

    # Create loggers
    sync_logger = SyncLogger(config)
    async_logger = AsyncLogger(config)

    # Use loggers
    sync_logger.info("Sync message", layer="my_layer")
    await async_logger.info("Async message", layer="my_layer")

Magic Configuration:
    from hydra_logger.loggers import SyncLogger

    # Use magic configurations
    logger = SyncLogger().for_production()
    logger = SyncLogger().for_development()
    logger = SyncLogger().for_high_performance()
    logger = SyncLogger().for_minimal()

Composite Logging:
    from hydra_logger.loggers import CompositeLogger, SyncLogger, AsyncLogger

    # Create component loggers
    sync_logger = SyncLogger(sync_config)
    async_logger = AsyncLogger(async_config)

    # Create composite logger
    composite = CompositeLogger(components=[sync_logger, async_logger])

    # Log to all components
    composite.log("INFO", "Message", layer="sync")
    composite.log("INFO", "Message", layer="async")

Python Logging Style:
    from hydra_logger.loggers import getLogger

    # Get logger (Python logging style)
    logger = getLogger("my_module")
    logger.info("This is an info message")
    logger.error("This is an error message")

Performance Monitoring:
    from hydra_logger.loggers import AsyncLogger

    # Create logger with monitoring
    logger = AsyncLogger(config)

    # Check health status
    health = logger.get_health_status()
    print(f"Logger health: {health}")

    # Get performance metrics
    stats = logger.get_concurrency_info()
    print(f"Concurrency info: {stats}")

STANDARDIZED RECORD CREATION:
- RecordCreationStrategy: Strategy pattern for LogRecord creation
- get_record_creation_strategy(): Get strategy by performance profile
- create_log_record(): Create LogRecord with standardized fields
- Performance profiles: MINIMAL, CONTEXT, AUTO_CONTEXT

FACTORY FUNCTIONS:
- getLogger(): Python logging style logger creation
- create_logger(): Factory function for logger creation
- Magic configuration methods for common use cases

THREAD SAFETY:
- All loggers are thread-safe
- Async loggers use proper asyncio synchronization
- Composite loggers coordinate component loggers safely
- Resource cleanup is handled automatically

ERROR HANDLING:
- Graceful error handling with fallback mechanisms
- Silent error handling for performance
- Health monitoring and status reporting
- Automatic resource cleanup on errors

BENEFITS:
- Logging with optimized processing
- Feature set with optional components
- Easy migration from standard Python logging
- Extensive configuration and customization options
- Production-ready with monitoring and health checks
"""

from .base import BaseLogger
from .sync_logger import SyncLogger
from .async_logger import AsyncLogger
from .composite_logger import CompositeLogger, CompositeAsyncLogger

# Standardized record creation
from ..types.records import (
    RecordCreationStrategy,
    get_record_creation_strategy,
    create_log_record,
    MINIMAL_STRATEGY,
    CONTEXT_STRATEGY,
    AUTO_CONTEXT_STRATEGY,
)

# PerformanceProfiles is now in base.py

# No factory imports to avoid circular imports


# Convenience function for Python logging style
def getLogger(name: str = None):
    """Get a logger instance (Python logging style)."""
    # Import here to avoid circular imports
    from ..factories.logger_factory import create_logger

    return create_logger(name=name)


# Public API
__all__ = [
    # Base classes
    "BaseLogger",
    "PerformanceProfiles",
    # Logger implementations
    "SyncLogger",
    "AsyncLogger",
    "CompositeLogger",
    "CompositeAsyncLogger",
    # Standardized record creation
    "RecordCreationStrategy",
    "get_record_creation_strategy",
    "create_log_record",
    "MINIMAL_STRATEGY",
    "CONTEXT_STRATEGY",
    "AUTO_CONTEXT_STRATEGY",
    # Factory functions (imported separately to avoid circular imports)
    # Python logging style
    "getLogger",
]

# Version info
__version__ = "0.4.0"
__author__ = "Savin Ionut Razvan"
