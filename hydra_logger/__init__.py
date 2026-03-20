"""
Role: Public exports for hydra_logger; no runtime logic besides import wiring.
Used By:
 - Importers of `hydra_logger` public API.
Depends On:
 - hydra_logger
Notes:
 - Re-exports the hydra_logger public API with stable import paths.
"""

__version__ = "0.7.0"
__author__ = "Savin Ionut Razvan"
__license__ = "MIT"

# Configuration
from .config.configuration_templates import ConfigurationTemplates
from .config.loader import clear_logging_config_cache, load_logging_config
from .config.models import LogDestination, LoggingConfig, LogLayer

# Exception classes
from .core.exceptions import (
    ConfigurationError,
    FormatterError,
    HandlerError,
    HydraLoggerError,
    PluginError,
    SecurityError,
    ValidationError,
)

# Logger Manager (Python logging style)
from .core.logger_management import getAsyncLogger, getLogger, getSyncLogger

# High-performance loggers
from .factories.logger_factory import (
    create_async_logger,
    create_composite_async_logger,
    create_composite_logger,
    create_logger,
    create_sync_logger,
)
from .loggers.async_logger import AsyncLogger
from .loggers.composite_logger import CompositeAsyncLogger, CompositeLogger

# Main public API
from .loggers.sync_logger import SyncLogger
from .types.context import LogContext
from .types.levels import LogLevel

# Core types
from .types.records import LogRecord
from .utils.stderr_interceptor import (
    StderrInterceptor,
    start_stderr_interception,
    stop_stderr_interception,
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
    "load_logging_config",
    "clear_logging_config_cache",
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
    # Runtime controls
    "StderrInterceptor",
    "start_stderr_interception",
    "stop_stderr_interception",
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
