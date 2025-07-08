"""
Async logging components for Hydra-Logger.

This package provides async-compatible logging functionality including
async handlers, async queues, async sinks, async context propagation,
and async framework integration for high-performance async applications.

Key Components:
- AsyncHydraLogger: Main async logger class
- AsyncLogHandler: Base async handler class
- AsyncRotatingFileHandler: Async file handler with rotation
- AsyncStreamHandler: Async console output handler
- AsyncBufferedRotatingFileHandler: Async buffered file handler
- AsyncLogQueue: Async message queue system
- AsyncBatchProcessor: Async batch processing
- AsyncBackpressureHandler: Async backpressure management
- AsyncHttpSink: Async HTTP logging sink
- AsyncDatabaseSink: Async database logging sink
- AsyncQueueSink: Async message queue sink
- AsyncCloudSink: Async cloud service sink
- AsyncContextManager: Async context propagation
- AsyncTraceManager: Async distributed tracing
- QueueStats: Queue performance statistics
"""

from hydra_logger.async_hydra.async_logger import AsyncHydraLogger, AsyncPerformanceMonitor, AsyncCompositeHandler
from hydra_logger.async_hydra.async_handlers import (
    AsyncLogHandler,
    AsyncRotatingFileHandler,
    AsyncStreamHandler,
    AsyncBufferedRotatingFileHandler,
)
from hydra_logger.async_hydra.async_queue import (
    AsyncLogQueue,
    AsyncBatchProcessor,
    AsyncBackpressureHandler,
    QueueStats,
)
from hydra_logger.async_hydra.async_sinks import (
    AsyncSink,
    AsyncHttpSink,
    AsyncDatabaseSink,
    AsyncQueueSink,
    AsyncCloudSink,
    SinkStats,
)
from hydra_logger.async_hydra.async_context import (
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

__all__ = [
    # Core async logger
    "AsyncHydraLogger",
    "AsyncPerformanceMonitor",
    "AsyncCompositeHandler",
    
    # Async handlers
    "AsyncLogHandler",
    "AsyncRotatingFileHandler",
    "AsyncStreamHandler",
    "AsyncBufferedRotatingFileHandler",
    
    # Async queue system
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