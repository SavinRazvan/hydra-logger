"""
Role: Init implementation.
Used By:
 - (update when known)
Depends On:
 - records
 - levels
 - context
 - enums
Notes:
 - Header standardized by slim-header migration.
"""

from .records import LogRecord, LogRecordBatch
from .levels import (
    LogLevel,
    LogLevelManager,
    get_level_name,
    get_level,
    is_valid_level,
    all_levels,
    all_level_names,
)
from .context import (
    LogContext,
    ContextType,
    CallerInfo,
    SystemInfo,
    ContextManager,
    ContextDetector,
)

# Metadata and Events modules removed - simplified architecture
from .enums import (
    HandlerType,
    FormatterType,
    PluginType,
    LogLayer,
    SecurityLevel,
    QueuePolicy,
    ShutdownPhase,
    RotationStrategy,
    CompressionType,
    EncryptionType,
    NetworkProtocol,
    DatabaseType,
    CloudProvider,
    LogFormat,
    ColorMode,
    ValidationLevel,
    MonitoringLevel,
    ErrorHandling,
    AsyncMode,
    CacheStrategy,
    BackupStrategy,
    HealthCheckType,
    AlertSeverity,
    MetricType,
    TimeUnit,
    SizeUnit,
)

# Handlers and Formatters types removed - simplified architecture

__all__ = [
    # Core types
    "LogRecord",
    "LogRecordBatch",
    "LogLevel",
    "LogLevelManager",
    "LogContext",
    # Enums
    "HandlerType",
    "FormatterType",
    "PluginType",
    "LogLayer",
    "SecurityLevel",
    "QueuePolicy",
    "ShutdownPhase",
    "RotationStrategy",
    "CompressionType",
    "EncryptionType",
    "NetworkProtocol",
    "DatabaseType",
    "CloudProvider",
    "LogFormat",
    "ColorMode",
    "ValidationLevel",
    "MonitoringLevel",
    "ErrorHandling",
    "AsyncMode",
    "CacheStrategy",
    "BackupStrategy",
    "HealthCheckType",
    "AlertSeverity",
    "MetricType",
    "TimeUnit",
    "SizeUnit",
    # Handler and Formatter types removed - simplified architecture
    # Context types
    "ContextType",
    "CallerInfo",
    "SystemInfo",
    "ContextManager",
    "ContextDetector",
    # Utility functions
    "get_level_name",
    "get_level",
    "is_valid_level",
    "all_levels",
    "all_level_names",
]
