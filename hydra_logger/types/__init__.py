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

from .context import (
    CallerInfo,
    ContextDetector,
    ContextManager,
    ContextType,
    LogContext,
    SystemInfo,
)

# Metadata and Events modules removed - simplified architecture
from .enums import (
    AlertSeverity,
    AsyncMode,
    BackupStrategy,
    CacheStrategy,
    CloudProvider,
    ColorMode,
    CompressionType,
    DatabaseType,
    EncryptionType,
    ErrorHandling,
    FormatterType,
    HandlerType,
    HealthCheckType,
    LogFormat,
    LogLayer,
    MetricType,
    MonitoringLevel,
    NetworkProtocol,
    PluginType,
    QueuePolicy,
    RotationStrategy,
    SecurityLevel,
    ShutdownPhase,
    SizeUnit,
    TimeUnit,
    ValidationLevel,
)
from .levels import (
    LogLevel,
    LogLevelManager,
    all_level_names,
    all_levels,
    get_level,
    get_level_name,
    is_valid_level,
)
from .records import LogRecord, LogRecordBatch

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
