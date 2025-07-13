"""
Professional Async Hydra-Logger Components.

This package provides world-class async logging functionality with:
- Professional async patterns and error handling
- Comprehensive task tracking and cleanup
- Memory monitoring and backpressure
- Safe shutdown protocols with data integrity
- Health monitoring and performance metrics
- Bounded queues with configurable policies
- Context management and distributed tracing
- Multi-handler support with parallel execution

Key Components:
- Core Components: CoroutineManager, EventLoopManager, BoundedAsyncQueue, etc.
- Handlers: AsyncFileHandler, AsyncConsoleHandler, AsyncCompositeHandler
- Context Management: AsyncContextManager, AsyncTraceManager
- Main Logger: AsyncHydraLogger
- Monitoring: HealthMonitor, ErrorTracker, PerformanceMonitor, etc.

Example:
    >>> from hydra_logger.async_hydra import AsyncHydraLogger, AsyncFileHandler, AsyncConsoleHandler
    >>> logger = AsyncHydraLogger({
    ...     'handlers': [
    ...         {'type': 'file', 'filename': 'mylog.log'},
    ...         {'type': 'console', 'use_colors': True}
    ...     ]
    ... })
    >>> await logger.info("LAYER", "Professional async logging")
"""

# Core components
from .core import (
    CoroutineManager,
    EventLoopManager,
    BoundedAsyncQueue,
    MemoryMonitor,
    SafeShutdownManager,
    AsyncErrorTracker,
    AsyncHealthMonitor
)

# Handlers
from .handlers import (
    BaseAsyncHandler,
    AsyncFileHandler,
    AsyncConsoleHandler,
    AsyncCompositeHandler
)

# Context management
from .context import (
    AsyncContext,
    AsyncContextManager,
    AsyncContextSwitcher,
    TraceContext,
    AsyncTraceManager,
    get_context_switcher,
    get_trace_manager,
    async_context,
    trace_context,
    span_context
)

# Performance monitoring
from .performance import (
    AsyncPerformanceMonitor,
    get_performance_monitor,
    async_timer,
    performance_context
)

# Main logger
from .logger import AsyncHydraLogger

__all__ = [
    # Core components
    "CoroutineManager",
    "EventLoopManager", 
    "BoundedAsyncQueue",
    "MemoryMonitor",
    "SafeShutdownManager",
    "AsyncErrorTracker",
    "AsyncHealthMonitor",
    # Handlers
    "BaseAsyncHandler",
    "AsyncFileHandler",
    "AsyncConsoleHandler",
    "AsyncCompositeHandler",
    # Context management
    "AsyncContext",
    "AsyncContextManager",
    "AsyncContextSwitcher",
    "TraceContext",
    "AsyncTraceManager",
    "get_context_switcher",
    "get_trace_manager",
    "async_context",
    "trace_context",
    "span_context",
    # Performance monitoring
    "AsyncPerformanceMonitor",
    "get_performance_monitor",
    "async_timer",
    "performance_context",
    # Main logger
    "AsyncHydraLogger",
] 