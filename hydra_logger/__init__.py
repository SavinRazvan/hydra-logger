"""
Hydra-Logger public package API.

Exports logger implementations, factory helpers, configuration models, core
types, and key exception classes for application use.
"""

__version__ = "0.4.0"
__author__ = "Savin Ionut Razvan"
__license__ = "MIT"

# ✅ CRITICAL: Start stderr interception to capture tracemalloc and system errors
# This must happen early, before any logging operations
try:
    from .utils.stderr_interceptor import StderrInterceptor
    StderrInterceptor.start_intercepting()
except Exception:
    # Fail silently if interception can't be set up
    pass

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
from .core.logger_management import getLogger, getSyncLogger, getAsyncLogger

# Configuration
from .config.configuration_templates import ConfigurationTemplates
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
