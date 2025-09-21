"""
Hydra-Logger: Advanced Modular Logging Framework

A comprehensive, extensible logging system with unified sync/async support,
modular architecture, and intelligent configuration management. Built for
performance, flexibility, and ease of use in modern Python applications.

FEATURES:
- Unified sync/async logging interface
- Modular handler and formatter system
- Intelligent configuration management
- Performance-optimized logging operations
- Security and data protection features
- Security and compliance features
- Plugin system for extensibility
- Multiple output formats and destinations

CORE COMPONENTS:
- Loggers: SyncLogger, AsyncLogger, CompositeLogger
- Handlers: Console, file, network, database, cloud handlers
- Formatters: JSON, plain text, CSV, syslog formatters
- Configuration: MagicConfigs, LoggingConfig, LogDestination
- Types: LogRecord, LogLevel, LogContext
- Utilities: Text processing, time management, file operations

USAGE:
    from hydra_logger import SyncLogger, AsyncLogger, create_logger
    
    # Simple usage
    logger = SyncLogger("my_app")
    logger.info("Application started")
    
    # Async usage
    async_logger = AsyncLogger("my_app")
    await async_logger.info("Async operation completed")
    
    # Factory pattern
    logger = create_logger("my_app", level="INFO")
    
    # Python logging style
    from hydra_logger import getLogger
    logger = getLogger("my_app")
"""

__version__ = "1.0.0"
__author__ = "Savin Ionut Razvan"
__license__ = "MIT"

# Main public API
from .loggers.sync_logger import SyncLogger
from .loggers.async_logger import AsyncLogger
from .loggers.composite_logger import CompositeLogger, CompositeAsyncLogger

# High-performance loggers
from .factories.logger_factory import (
    create_logger,
    create_sync_logger,
    create_async_logger,
    create_composite_logger,
    create_composite_async_logger,
)

# Logger Manager (Python logging style)
from .core.logger_manager import getLogger, getSyncLogger, getAsyncLogger

# Configuration
from .config.magic_configs import ConfigurationTemplates
from .config.models import LoggingConfig, LogDestination, LogLayer

# Core types
from .types.records import LogRecord
from .types.levels import LogLevel
from .types.context import LogContext

# Exception classes
from .core.exceptions import (
    HydraLoggerError,
    ConfigurationError,
    ValidationError,
    HandlerError,
    FormatterError,
    PluginError,
    SecurityError,
)

# Public API
__all__ = [
    # Main loggers
    "SyncLogger",
    "AsyncLogger",
    "CompositeLogger",
    "CompositeAsyncLogger",
    # Factory functions
    "create_logger",
    "create_sync_logger",
    "create_async_logger",
    "create_composite_logger",
    "create_composite_async_logger",
    # Logger Manager (Python logging style)
    "getLogger",
    "getSyncLogger",
    "getAsyncLogger",
    # Configuration
    "LoggingConfig",
    "LogDestination",
    "LogLayer",
    "ConfigurationTemplates",
    # Core types
    "LogRecord",
    "LogLevel",
    "LogContext",
    # Exceptions
    "HydraLoggerError",
    "ConfigurationError",
    "ValidationError",
    "HandlerError",
    "FormatterError",
    "PluginError",
    "SecurityError",
    # Version
    "__version__",
    "__author__",
    "__license__",
]

# Backward compatibility aliases
HydraLogger = SyncLogger  # Main logger alias
AsyncHydraLogger = AsyncLogger

# Add to __all__ for backward compatibility
__all__.extend(["HydraLogger", "AsyncHydraLogger"])
