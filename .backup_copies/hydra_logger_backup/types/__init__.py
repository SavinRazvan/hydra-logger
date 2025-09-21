"""
Type Definitions and Data Structures for Hydra-Logger

This module contains all the core data types used throughout the system
including log records, levels, context management, metadata handling,
event processing, and system enums. It provides comprehensive type
definitions for consistent data handling across all components.

CORE TYPES:
- LogRecord: Optimized log record with essential fields
- LogRecordBatch: High-performance batch processing
- LogLevel: Standard log level definitions and management
- LogContext: Context management and caller information
- LogMetadata: Metadata container and validation
- LogEvent: Event system for notifications and monitoring

SYSTEM ENUMS:
- HandlerType: Log handler types (console, file, network, etc.)
- FormatterType: Log formatter types (JSON, plain text, etc.)
- PluginType: Plugin categories and types
- SecurityLevel: Security and data protection levels
- QueuePolicy: Queue management policies
- RotationStrategy: File rotation strategies

CONFIGURATION TYPES:
- HandlerConfig: Handler configuration and settings
- FormatterConfig: Formatter configuration and options
- PluginConfig: Plugin configuration and metadata
- FormatOptions: Formatting options and customization

USAGE:
    from hydra_logger.types import LogRecord, LogLevel, create_log_record
    
    # Create a log record
    record = create_log_record(
        level="INFO",
        message="Application started",
        strategy="minimal"
    )
    
    # Use log levels
    if LogLevel.INFO >= LogLevel.DEBUG:
        print("Debug logging is enabled")
    
    # Create context
    from hydra_logger.types import LogContext, ContextType
    context = LogContext(
        context_type=ContextType.REQUEST,
        metadata={"user_id": "123", "session_id": "abc"}
    )
"""

from .records import LogRecord, LogRecordBatch
from .levels import LogLevel, LogLevelManager, get_level_name, get_level, is_valid_level, all_levels, all_level_names
from .context import LogContext, ContextType, CallerInfo, SystemInfo, ContextManager, ContextDetector
from .metadata import LogMetadata, MetadataSchema, MetadataField, create_metadata, merge_metadata
from .events import LogEvent, EventType, EventSeverity, EventStatus, LogEntryEvent, SecurityEvent, PerformanceEvent, ErrorEvent, SystemEvent, EventHandler, EventBus
from .enums import (
    HandlerType, FormatterType, PluginType, LogLayer, SecurityLevel,
    QueuePolicy, ShutdownPhase, RotationStrategy, CompressionType, EncryptionType,
    NetworkProtocol, DatabaseType, CloudProvider, LogFormat, ColorMode, ValidationLevel,
    MonitoringLevel, ErrorHandling, AsyncMode, CacheStrategy, BackupStrategy,
    HealthCheckType, AlertSeverity, MetricType, TimeUnit, SizeUnit
)
from .handlers import HandlerConfig, HandlerState, HandlerMetrics, HandlerHealth
from .formatters import FormatterConfig, FormatOptions, ColorScheme, FormatTemplate, FormatResult

__all__ = [
    # Core types
    "LogRecord",
    "LogRecordBatch",
    "LogLevel",
    "LogLevelManager",
    "LogContext",
    "LogMetadata",
    "LogEvent",
    
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
    
    # Handler types
    "HandlerConfig",
    "HandlerState",
    "HandlerMetrics",
    "HandlerHealth",
    
    # Formatter types
    "FormatterConfig",
    "FormatOptions",
    "ColorScheme",
    "FormatTemplate",
    "FormatResult",
    
    # Plugin types
    "PluginConfig",
    "PluginState",
    "PluginMetadata",
    "PluginCompatibility",
    
    # Context types
    "ContextType",
    "CallerInfo",
    "SystemInfo",
    "ContextManager",
    "ContextDetector",
    
    # Metadata types
    "MetadataSchema",
    "MetadataField",
    
    # Event types
    "EventType",
    "EventSeverity",
    "EventStatus",
    "LogEntryEvent",
    "SecurityEvent",
    "PerformanceEvent",
    "ErrorEvent",
    "SystemEvent",
    "EventHandler",
    "EventBus",
    
    # Utility functions
    "get_level_name",
    "get_level",
    "is_valid_level",
    "all_levels",
    "all_level_names",
    "create_metadata",
    "merge_metadata"
]
