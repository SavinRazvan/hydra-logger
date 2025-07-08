"""
Hydra-Logger: A dynamic, multi-headed logging system for Python applications.

A standalone, reusable logging module that supports:
- Multi-layered logging with different destinations per layer
- Custom folder paths for each log file
- Configuration via YAML/TOML files
- Backward compatibility with simple setup_logging()
- Async logging support for high-performance applications
- Async sinks for HTTP, database, queue, and cloud destinations
- Async context propagation and distributed tracing
- Async framework integration for FastAPI, Django, and Flask
"""

from hydra_logger.compatibility import migrate_to_hydra, setup_logging
from hydra_logger.config import LogDestination, LoggingConfig, LogLayer, get_async_default_config
from hydra_logger.logger import HydraLogger, HydraLoggerError

# Import async components
from hydra_logger.async_hydra import (
    AsyncHydraLogger,
    AsyncLogHandler,
    AsyncRotatingFileHandler,
    AsyncStreamHandler,
    AsyncBufferedRotatingFileHandler,
    AsyncLogQueue,
    AsyncBatchProcessor,
    AsyncBackpressureHandler,
    QueueStats,
    AsyncSink,
    AsyncHttpSink,
    AsyncDatabaseSink,
    AsyncQueueSink,
    AsyncCloudSink,
    SinkStats,
    AsyncContext,
    AsyncContextManager,
    AsyncTraceManager,
    AsyncContextSwitcher,
    get_async_context,
    set_async_context,
    clear_async_context,
    get_trace_id,
    start_trace,
    set_correlation_id,
    get_correlation_id,
    detect_context_switch,
    get_context_switch_count,
    async_context,
    trace_context,
)

__version__ = "0.2.0"
__author__ = "Savin Ionut Razvan"

__all__ = [
    # Core components
    "HydraLogger",
    "HydraLoggerError",
    "LoggingConfig",
    "LogLayer",
    "LogDestination",
    "setup_logging",
    "migrate_to_hydra",
    "get_async_default_config",
    
    # Async components
    "AsyncHydraLogger",
    "AsyncLogHandler",
    "AsyncRotatingFileHandler",
    "AsyncStreamHandler",
    "AsyncBufferedRotatingFileHandler",
    "AsyncLogQueue",
    "AsyncBatchProcessor",
    "AsyncBackpressureHandler",
    "QueueStats",
    
    # Async sinks
    "AsyncSink",
    "AsyncHttpSink",
    "AsyncDatabaseSink",
    "AsyncQueueSink",
    "AsyncCloudSink",
    "SinkStats",
    
    # Async context
    "AsyncContext",
    "AsyncContextManager",
    "AsyncTraceManager",
    "AsyncContextSwitcher",
    "get_async_context",
    "set_async_context",
    "clear_async_context",
    "get_trace_id",
    "start_trace",
    "set_correlation_id",
    "get_correlation_id",
    "detect_context_switch",
    "get_context_switch_count",
    "async_context",
    "trace_context",
]
