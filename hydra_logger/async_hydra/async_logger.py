"""
Async HydraLogger for non-blocking logging operations.

This module provides AsyncHydraLogger, an async-compatible version of HydraLogger
that supports non-blocking I/O operations and seamless integration with async
applications.

Key Features:
- AsyncHydraLogger with async logging methods
- Non-blocking log routing
- Async performance monitoring
- Async context propagation
- Thread-safe async operations

Example:
    >>> from hydra_logger import AsyncHydraLogger
    >>> logger = AsyncHydraLogger()
    >>> await logger.info("LAYER", "Async log message")
    >>> await logger.error("ERROR", "Async error logging")
"""

import asyncio
import logging
import sys
import threading
import time
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from contextvars import ContextVar
import uuid

from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
# from hydra_logger.core.logger import HydraLogger  # Moved to inside function to avoid circular import
from hydra_logger.async_hydra.async_handlers import AsyncLogHandler, AsyncRotatingFileHandler, AsyncStreamHandler
from hydra_logger.async_hydra.async_queue import AsyncLogQueue, AsyncBatchProcessor, AsyncBackpressureHandler
from hydra_logger.magic_configs import MagicConfigRegistry


@dataclass
class LogContext:
    """Context information for structured logging."""
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.custom_fields is None:
            self.custom_fields = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        result = {
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'request_id': self.request_id,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'custom_fields': self.custom_fields
        }
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class StructuredLogRecord:
    """Structured log record with context and metadata."""
    timestamp: datetime
    level: str
    message: str
    logger_name: str
    context: LogContext
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'logger_name': self.logger_name,
            'context': self.context.to_dict(),
            'metadata': self.metadata
        }, default=str)
    
    def to_xml(self) -> str:
        """Convert to XML string."""
        root = ET.Element('log')
        root.set('timestamp', self.timestamp.isoformat())
        root.set('level', self.level)
        root.set('logger_name', self.logger_name)
        
        message_elem = ET.SubElement(root, 'message')
        message_elem.text = self.message
        
        context_elem = ET.SubElement(root, 'context')
        for key, value in self.context.to_dict().items():
            if value is not None:
                context_elem.set(key, str(value))
        
        if self.metadata:
            metadata_elem = ET.SubElement(root, 'metadata')
            for key, value in self.metadata.items():
                meta_elem = ET.SubElement(metadata_elem, key)
                meta_elem.text = str(value)
        
        return ET.tostring(root, encoding='unicode')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message,
            'logger_name': self.logger_name,
            'context': self.context.to_dict(),
            'metadata': self.metadata
        }


# Global context variables for correlation and context management
_correlation_context: ContextVar[Optional[LogContext]] = ContextVar('correlation_context', default=None)
_logger_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar('logger_context', default=None)


class RecordPool:
    """
    Object pool for LogRecord instances to reduce allocation overhead.
    
    This class provides efficient reuse of LogRecord objects to minimize
    garbage collection pressure and improve performance in high-throughput
    logging scenarios.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize record pool.
        
        Args:
            max_size (int): Maximum number of records to keep in pool
        """
        self._pool: List[logging.LogRecord] = []
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._created_count = 0
        self._reused_count = 0
        self._closed = False
    
    async def get_record(self, name: str, level: int, msg: str, 
                        pathname: str = "", lineno: int = 0, 
                        func: str = "", exc_info: Optional[Any] = None) -> logging.LogRecord:
        """
        Get a LogRecord from the pool or create a new one.
        
        Args:
            name (str): Logger name
            level (int): Log level
            msg (str): Log message
            pathname (str): Source file path
            lineno (int): Source line number
            func (str): Function name
            exc_info (Optional[Any]): Exception info
            
        Returns:
            logging.LogRecord: Reused or new log record
        """
        if self._closed:
            return logging.LogRecord(
                name=name,
                level=level,
                pathname=pathname,
                lineno=lineno,
                msg=msg,
                args=(),
                exc_info=exc_info,
                func=func
            )
        
        async with self._lock:
            if self._pool:
                # Reuse existing record
                record = self._pool.pop()
                self._reused_count += 1
                
                # Reset and update record fields
                record.name = name
                record.levelno = level
                record.levelname = logging.getLevelName(level)
                record.msg = msg
                record.pathname = pathname
                record.lineno = lineno
                record.funcName = func
                record.exc_info = exc_info
                record.exc_text = None
                record.stack_info = None
                
                return record
            else:
                # Create new record
                self._created_count += 1
                return logging.LogRecord(
                    name=name,
                    level=level,
                    pathname=pathname,
                    lineno=lineno,
                    msg=msg,
                    args=(),
                    exc_info=exc_info,
                    func=func
                )
    
    async def return_record(self, record: logging.LogRecord) -> None:
        """
        Return a LogRecord to the pool for reuse.
        
        Args:
            record (logging.LogRecord): Record to return to pool
        """
        if self._closed or len(self._pool) >= self._max_size:
            return
        
        async with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(record)
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Get pool statistics."""
        return {
            "pool_size": len(self._pool),
            "max_size": self._max_size,
            "created_count": self._created_count,
            "reused_count": self._reused_count,
            "reuse_rate": self._reused_count / max(self._created_count, 1),
            "closed": self._closed
        }
    
    def clear(self) -> None:
        """Clear the pool."""
        self._pool.clear()
        self._created_count = 0
        self._reused_count = 0
    
    def close(self) -> None:
        """Close the pool."""
        self._closed = True
        self.clear()


class AsyncPerformanceMonitor:
    """
    Async performance monitor for AsyncHydraLogger.
    
    Provides async-specific metrics and monitoring capabilities for async logging operations.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._message_count: int = 0
        self._error_count: int = 0
        self._handler_creation_times: List[float] = []
        self._log_processing_times: List[float] = []
        self._memory_usage: List[float] = []
        self._async_processing_times: List[float] = []
        self._async_queue_times: List[float] = []
        self._async_batch_times: List[float] = []
        self._async_context_switches: int = 0
    
    def start_handler_creation_timer(self) -> float:
        """Start timing handler creation."""
        return time.time()
    
    def end_handler_creation_timer(self, start_time: float) -> None:
        """End timing handler creation and record the duration."""
        duration = time.time() - start_time
        with self._lock:
            self._handler_creation_times.append(duration)
    
    def start_log_processing_timer(self) -> float:
        """Start timing log message processing."""
        return time.time()
    
    def end_log_processing_timer(self, start_time: float) -> None:
        """End timing log message processing and record the duration."""
        duration = time.time() - start_time
        with self._lock:
            self._log_processing_times.append(duration)
            self._message_count += 1
    
    def record_error(self) -> None:
        """Record an error occurrence."""
        with self._lock:
            self._error_count += 1
    
    def record_security_event(self) -> None:
        """Record a security validation event."""
        with self._lock:
            if not hasattr(self, '_security_events'):
                self._security_events = 0
            self._security_events += 1
    
    def record_sanitization_event(self) -> None:
        """Record a data sanitization event."""
        with self._lock:
            if not hasattr(self, '_sanitization_events'):
                self._sanitization_events = 0
            self._sanitization_events += 1
    
    def record_plugin_event(self) -> None:
        """Record a plugin event."""
        with self._lock:
            if not hasattr(self, '_plugin_events'):
                self._plugin_events = 0
            self._plugin_events += 1
    
    def check_memory_usage(self) -> float:
        """Check current memory usage."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            with self._lock:
                self._memory_usage.append(memory_mb)
            return memory_mb
        except ImportError:
            return 0.0
    
    def get_statistics(self) -> Dict[str, float]:
        """Get current performance statistics."""
        with self._lock:
            stats = {
                "message_count": float(self._message_count),
                "error_count": float(self._error_count),
            }
            
            # Add security and sanitization events
            if hasattr(self, '_security_events'):
                stats["security_events"] = float(self._security_events)
            if hasattr(self, '_sanitization_events'):
                stats["sanitization_events"] = float(self._sanitization_events)
            if hasattr(self, '_plugin_events'):
                stats["plugin_events"] = float(self._plugin_events)
            
            if self._handler_creation_times:
                stats["avg_handler_creation_time"] = sum(self._handler_creation_times) / len(self._handler_creation_times)
                stats["max_handler_creation_time"] = max(self._handler_creation_times)
                stats["min_handler_creation_time"] = min(self._handler_creation_times)
            
            if self._log_processing_times:
                stats["avg_log_processing_time"] = sum(self._log_processing_times) / len(self._log_processing_times)
                stats["max_log_processing_time"] = max(self._log_processing_times)
                stats["min_log_processing_time"] = min(self._log_processing_times)
            
            if self._memory_usage:
                stats["current_memory_mb"] = self._memory_usage[-1]
                stats["avg_memory_mb"] = sum(self._memory_usage) / len(self._memory_usage)
                stats["max_memory_mb"] = max(self._memory_usage)
            
            return stats
    
    def reset_statistics(self) -> None:
        """Reset all performance statistics."""
        with self._lock:
            self._message_count = 0
            self._error_count = 0
            self._handler_creation_times.clear()
            self._log_processing_times.clear()
            self._memory_usage.clear()
    
    async def start_async_processing_timer(self) -> float:
        """Start timing async log message processing."""
        return time.time()
    
    async def end_async_processing_timer(self, start_time: float) -> None:
        """End timing async log message processing and record the duration."""
        duration = time.time() - start_time
        with self._lock:
            self._async_processing_times.append(duration)
            # Also record in base class for compatibility
            self._log_processing_times.append(duration)
            # Increment message count
            self._message_count += 1
    
    async def start_async_queue_timer(self) -> float:
        """Start timing async queue operations."""
        return time.time()
    
    async def end_async_queue_timer(self, start_time: float) -> None:
        """End timing async queue operations and record the duration."""
        duration = time.time() - start_time
        with self._lock:
            self._async_queue_times.append(duration)
    
    async def record_async_context_switch(self) -> None:
        """Record an async context switch."""
        with self._lock:
            self._async_context_switches += 1
    
    def get_async_statistics(self) -> Dict[str, float]:
        """Get current async performance statistics."""
        with self._lock:
            # Get base statistics first
            base_stats = self.get_statistics()
            
            # Add async-specific statistics
            if self._async_processing_times:
                base_stats.update({
                    "avg_async_processing_time": sum(self._async_processing_times) / len(self._async_processing_times),
                    "max_async_processing_time": max(self._async_processing_times),
                    "min_async_processing_time": min(self._async_processing_times),
                })
            
            if self._async_queue_times:
                base_stats.update({
                    "avg_async_queue_time": sum(self._async_queue_times) / len(self._async_queue_times),
                    "max_async_queue_time": max(self._async_queue_times),
                    "min_async_queue_time": min(self._async_queue_times),
                })
            
            if self._async_batch_times:
                base_stats.update({
                    "avg_async_batch_time": sum(self._async_batch_times) / len(self._async_batch_times),
                    "max_async_batch_time": max(self._async_batch_times),
                    "min_async_batch_time": min(self._async_batch_times),
                })
            
            base_stats.update({
                "async_context_switches": self._async_context_switches,
            })
            
            return base_stats
    
    async def reset_async_statistics(self) -> None:
        """Reset all async performance statistics."""
        with self._lock:
            self._async_processing_times.clear()
            self._async_queue_times.clear()
            self._async_batch_times.clear()
            self._async_context_switches = 0
            # Reset base statistics as well
            self._message_count = 0
            self._error_count = 0
            self._handler_creation_times.clear()
            self._log_processing_times.clear()
            self._memory_usage.clear()


class AsyncHydraLogger:
    """
    Async version of HydraLogger for non-blocking logging operations.
    
    This class provides async-compatible logging with all the features of
    HydraLogger plus async-specific optimizations and non-blocking I/O.
    
    Attributes:
        config (LoggingConfig): The logging configuration
        async_loggers (Dict[str, AsyncLogHandler]): Dictionary of async loggers
        performance_monitoring (bool): Whether performance monitoring is enabled
        redact_sensitive (bool): Whether to redact sensitive data
        _async_performance_monitor (Optional[AsyncPerformanceMonitor]): Async performance monitor
        _async_queues (Dict[str, AsyncLogQueue]): Async queues for each layer
        _backpressure_handler (AsyncBackpressureHandler): Backpressure handler
    """
    
    def __init__(self, config: Optional[LoggingConfig] = None,
                 enable_security: bool = True,
                 enable_sanitization: bool = True,
                 enable_plugins: bool = True,
                 enable_performance_monitoring: bool = True,
                 redact_sensitive: bool = False,
                 queue_size: int = 1000,
                 batch_size: int = 100,
                 batch_timeout: float = 1.0,
                 test_mode: bool = False,
                 enable_object_pooling: bool = True,
                 pool_size: int = 1000,
                 date_format: Optional[str] = None,
                 time_format: Optional[str] = None,
                 logger_name_format: Optional[str] = None,
                 message_format: Optional[str] = None,
                 buffer_size: int = 8192,
                 flush_interval: float = 1.0,
                 high_performance_mode: bool = False,
                 ultra_fast_mode: bool = False):
        """
        Initialize AsyncHydraLogger with comprehensive features.
        
        Args:
            config (Optional[LoggingConfig]): Logging configuration
            enable_security (bool): Enable security validation
            enable_sanitization (bool): Enable data sanitization
            enable_plugins (bool): Enable plugin system
            enable_performance_monitoring (bool): Enable async performance monitoring
            redact_sensitive (bool): Auto-redact sensitive information
            queue_size (int): Maximum queue size for async operations
            batch_size (int): Batch size for async processing
            batch_timeout (float): Timeout for batch processing
            test_mode (bool): Enable test events for deterministic testing
            enable_object_pooling (bool): Enable LogRecord object pooling
            pool_size (int): Maximum size of record pool
            date_format (Optional[str]): Custom date format
            time_format (Optional[str]): Custom time format
            logger_name_format (Optional[str]): Custom logger name format
            message_format (Optional[str]): Custom message format
            buffer_size (int): Buffer size for file handlers
            flush_interval (float): Flush interval for file handlers
            high_performance_mode (bool): Enable high performance mode
            ultra_fast_mode (bool): Enable ultra fast mode
        """
        # Ensure we have a proper config with layers
        if config is None:
            from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
            self.config = LoggingConfig(
                layers={
                    "DEFAULT": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(
                                type="console",
                                format="plain-text",
                                color_mode="never"
                            )
                        ]
                    )
                }
            )
        else:
            self.config = config
        
        # Store format customizations
        self._date_format = date_format
        self._time_format = time_format
        self._logger_name_format = logger_name_format
        self._message_format = message_format
        
        # Performance settings
        self.high_performance_mode = high_performance_mode
        self.ultra_fast_mode = ultra_fast_mode
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # Feature flags
        self.enable_security = enable_security
        self.enable_sanitization = enable_sanitization
        self.enable_plugins = enable_plugins
        self.enable_performance_monitoring = enable_performance_monitoring
        self.redact_sensitive = redact_sensitive
        self.test_mode = test_mode
        
        # Initialize error tracker
        from hydra_logger.core.error_handler import get_error_tracker
        self._error_tracker = get_error_tracker()
        
        # Initialize security and sanitization
        self._security_validator = None
        self._data_sanitizer = None
        
        if enable_security:
            try:
                from hydra_logger.data_protection.security import SecurityValidator
                self._security_validator = SecurityValidator()
            except Exception as e:
                print(f"Warning: Failed to initialize security validator: {e}", file=sys.stderr)
        
        if enable_sanitization:
            try:
                from hydra_logger.data_protection.security import DataSanitizer
                self._data_sanitizer = DataSanitizer()
            except Exception as e:
                print(f"Warning: Failed to initialize data sanitizer: {e}", file=sys.stderr)
        
        # Initialize fallback handler
        try:
            from hydra_logger.data_protection.fallbacks import FallbackHandler
            self._fallback_handler = FallbackHandler()
        except Exception as e:
            print(f"Warning: Failed to initialize fallback handler: {e}", file=sys.stderr)
            self._fallback_handler = None
        
        # Initialize plugins
        self._plugins = {}
        if enable_plugins:
            self._load_plugins()
        
        # Initialize object pooling
        self.enable_object_pooling = enable_object_pooling
        if enable_object_pooling:
            self._record_pool = RecordPool(max_size=pool_size)
        else:
            self._record_pool = None
        
        # Initialize performance monitor
        if enable_performance_monitoring:
            self._performance_monitor = AsyncPerformanceMonitor()
        else:
            self._performance_monitor = None
        
        # Initialize closed flag
        self._closed = False
        
        # Initialize async queues for each layer
        self._async_queues: Dict[str, AsyncLogQueue] = {}
        self._async_handlers: Dict[str, List[AsyncLogHandler]] = {}
        self._sync_loggers: Dict[str, Any] = {}  # Use Any instead of 'HydraLogger'
        
        # Initialize magic config registry
        self._magic_registry = MagicConfigRegistry()
        
        # Performance tracking
        self._start_time = time.time()
        self._total_messages = 0
        self._failed_messages = 0
        
        self.async_loggers: Dict[str, AsyncLogHandler] = {}
        self.queue_size = queue_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        # Initialize async components
        self._async_performance_monitor = AsyncPerformanceMonitor() if enable_performance_monitoring else None
        self._backpressure_handler = AsyncBackpressureHandler(
            max_queue_size=queue_size,
            drop_threshold=0.9,
            slow_down_threshold=0.7
        )
        self._logger_init_lock = asyncio.Lock()
        self._initialized = False
        self._accepting_messages = True
        
        # Performance optimizations: Cache handlers and formatters
        self._cached_handlers: Dict[str, asyncio.Task] = {}
        self._cached_formatters: Dict[str, logging.Formatter] = {}
        self._log_record_cache: Dict[str, logging.LogRecord] = {}
        self._precomputed_methods: Dict[str, Callable] = {}
        
        # Initialize layers and handlers
        self._layers = {}
        self._handlers = {}
        
        # Setup ultra-fast mode if enabled
        if ultra_fast_mode:
            self._setup_ultra_fast_mode()
    
    def _load_plugins(self) -> None:
        """Load available plugins."""
        if not self.enable_plugins:
            return
        
        try:
            from hydra_logger.plugins.registry import list_plugins, get_plugin
            available_plugins = list_plugins()
            for plugin_name in available_plugins:
                plugin = get_plugin(plugin_name)
                if plugin:
                    self._plugins[plugin_name] = plugin
        except Exception as e:
            print(f"Warning: Failed to load plugins: {e}", file=sys.stderr)
    
    def _setup_ultra_fast_mode(self) -> None:
        """Setup ultra-fast mode optimizations."""
        self._precompute_log_methods()
    
    def _precompute_log_methods(self) -> None:
        """Precompute log methods for ultra-fast mode."""
        levels = ["debug", "info", "warning", "error", "critical"]
        layers = list(self._layers.keys()) if self._layers else ["DEFAULT"]
        
        for level in levels:
            for layer in layers:
                method_name = f"{level}_{layer}"
                self._precomputed_methods[method_name] = lambda l=level, lay=layer, msg="": self._fast_log(l, msg, lay)
    
    async def _fast_log(self, level: str, message: str, layer: str = "DEFAULT", extra: Optional[Dict[str, Any]] = None) -> None:
        """Fast logging without security validation or sanitization."""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        try:
            await self.log(layer, level, message)
            
            # Record performance metrics
            end_time = time.time()
            if self._performance_monitor:
                self._performance_monitor.record_log(layer, level, message, start_time, end_time)
        except Exception:
            # Minimal error handling for performance
            pass
    
    async def initialize(self) -> None:
        """
        Initialize async components. Call this before using the logger.
        """
        if self._initialized:
            return
            
        async with self._logger_init_lock:
            if self._initialized:
                return
                
            await self._setup_async_loggers()
            self._initialized = True

    async def _setup_async_loggers(self) -> None:
        """Setup async loggers for all configured layers."""
        try:
            # Ensure config has layers attribute
            if not hasattr(self.config, 'layers') or not self.config.layers:
                print("No layers configured, creating default layer", file=sys.stderr)
                # Create a proper LoggingConfig with layers
                from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
                self.config = LoggingConfig(
                    layers={
                        "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console",
                            format="plain-text",
                            color_mode="never"
                        )
                    ]
                        )
                    }
                )
            
            # Setup each layer
            for layer_name, layer_config in self.config.layers.items():
                await self._setup_async_layer(layer_name, layer_config)
            
            self._initialized = True
            
        except Exception as e:
            print(f"Error setting up async loggers: {e}", file=sys.stderr)
    
    async def _setup_async_layer(self, layer_name: str, layer_config: LogLayer) -> None:
        """
        Setup a single async logging layer.
        
        Args:
            layer_name (str): Name of the layer to setup
            layer_config (LogLayer): Configuration for the layer
        """
        try:
            # Create async queue for this layer
            queue = AsyncLogQueue(
                max_size=self.queue_size,
                batch_size=self.batch_size,
                batch_timeout=self.batch_timeout,
                processor=self._create_async_processor(layer_name, layer_config),
                test_mode=self.test_mode
            )
            self._async_queues[layer_name] = queue
            
            # Start the queue
            await queue.start()
            
        except Exception as e:
            print(f"Error setting up async layer '{layer_name}': {e}", file=sys.stderr)
    
    def _create_async_processor(self, layer_name: str, layer_config: LogLayer):
        """Create an async processor for a layer."""
        
        # Pre-create handlers for this layer to avoid repeated creation
        async def _pre_create_handlers():
            handlers = []
            for destination in layer_config.destinations:
                handler = await self._create_async_handler(destination, layer_config.level)
                if handler:
                    handlers.append(handler)
            return handlers
        
        # Store handlers in cache
        self._cached_handlers[layer_name] = asyncio.create_task(_pre_create_handlers())
        
        async def processor(messages: List[Any]) -> None:
            """Process a batch of messages for a layer."""
            try:
                # Get cached handlers
                handlers_task = self._cached_handlers[layer_name]
                handlers = await handlers_task
                if not handlers:
                    return
                
                # Process messages in batch for better performance
                for message in messages:
                    # Create log record once and reuse
                    if isinstance(message, logging.LogRecord):
                        record = message
                    else:
                        # Use cached record template if available
                        cache_key = f"{layer_name}_{layer_config.level}"
                        if cache_key not in self._log_record_cache:
                            self._log_record_cache[cache_key] = logging.LogRecord(
                                name=layer_name,
                                level=getattr(logging, layer_config.level.upper()),
                                pathname="",
                                lineno=0,
                                msg="",  # Will be set per message
                                args=(),
                                exc_info=None
                            )
                        
                        # Clone the cached record for efficiency
                        record = logging.LogRecord(
                            name=layer_name,
                            level=getattr(logging, layer_config.level.upper()),
                            pathname="",
                            lineno=0,
                            msg=str(message),
                            args=(),
                            exc_info=None
                        )
                    
                    # Process through all handlers
                    for handler in handlers:
                        try:
                            await handler.emit_async(record)
                        except Exception as e:
                            if self.enable_performance_monitoring:
                                print(f"Error processing message in handler: {e}", file=sys.stderr)
                    
            except Exception as e:
                if self.enable_performance_monitoring:
                    print(f"Error in async processor for layer '{layer_name}': {e}", file=sys.stderr)
        
        return processor
    
    async def _create_async_handler(self, destination: LogDestination, layer_level: str) -> Optional[AsyncLogHandler]:
        """
        Create an async handler for a destination.
        
        Args:
            destination (LogDestination): Destination configuration
            layer_level (str): Log level for the layer
            
        Returns:
            Optional[AsyncLogHandler]: Created async handler or None if failed
        """
        try:
            handler = None
            if destination.type == "console":
                handler = AsyncStreamHandler()
            elif destination.type == "file":
                filename = destination.path or "default.log"
                handler = AsyncRotatingFileHandler(
                    filename=filename,
                    maxBytes=self._parse_size(destination.max_size or "5MB"),
                    backupCount=destination.backup_count or 3
                )
            else:
                print(f"Unsupported async destination type: {destination.type}", file=sys.stderr)
                return None
            
            # Set formatter based on format and color_mode
            if handler:
                formatter = self._create_async_formatter(destination.format, destination.color_mode)
                handler.setFormatter(formatter)
            
            return handler
                
        except Exception as e:
            print(f"Error creating async handler for {destination.type}: {e}", file=sys.stderr)
            return None
    
    def _create_async_formatter(self, format_type: str, color_mode: Optional[str] = None) -> logging.Formatter:
        """Create a formatter for async handlers based on format type and color mode."""
        # Use cached formatter if available
        cache_key = f"{format_type}_{color_mode}"
        if cache_key in self._cached_formatters:
            return self._cached_formatters[cache_key]
        
        # Create new formatter
        formatter = None
        if format_type == "plain" or format_type == "plain-text":
            formatter = self._create_async_plain_formatter()
        elif format_type == "text":
            formatter = self._create_async_text_formatter(color_mode)
        elif format_type == "json":
            formatter = self._create_async_json_formatter(color_mode)
        elif format_type == "csv":
            formatter = self._create_async_csv_formatter(color_mode)
        elif format_type == "syslog":
            formatter = self._create_async_syslog_formatter(color_mode)
        elif format_type == "gelf":
            formatter = self._create_async_gelf_formatter(color_mode)
        else:
            # Default to plain formatter for maximum performance
            formatter = self._create_async_plain_formatter()
        
        # Cache the formatter
        self._cached_formatters[cache_key] = formatter
        return formatter
    
    def _create_async_plain_formatter(self) -> logging.Formatter:
        """Create a plain text formatter without colors."""
        return logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def _create_async_text_formatter(self, color_mode: Optional[str] = None) -> logging.Formatter:
        """Create a text formatter with colors."""
        from hydra_logger.async_hydra.async_handlers import ColoredTextFormatter
        return ColoredTextFormatter(color_mode=color_mode)
    
    def _create_async_json_formatter(self, color_mode: Optional[str] = None) -> logging.Formatter:
        """Create a JSON formatter."""
        # For now, use text formatter with color control
        if color_mode == "never":
            return self._create_async_plain_formatter()
        else:
            return self._create_async_text_formatter(color_mode)
    
    def _create_async_csv_formatter(self, color_mode: Optional[str] = None) -> logging.Formatter:
        """Create a CSV formatter."""
        # For now, use text formatter with color control
        if color_mode == "never":
            return self._create_async_plain_formatter()
        else:
            return self._create_async_text_formatter(color_mode)
    
    def _create_async_syslog_formatter(self, color_mode: Optional[str] = None) -> logging.Formatter:
        """Create a syslog formatter."""
        # For now, use text formatter with color control
        if color_mode == "never":
            return self._create_async_plain_formatter()
        else:
            return self._create_async_text_formatter(color_mode)
    
    def _create_async_gelf_formatter(self, color_mode: Optional[str] = None) -> logging.Formatter:
        """Create a GELF formatter."""
        # For now, use text formatter with color control
        if color_mode == "never":
            return self._create_async_plain_formatter()
        else:
            return self._create_async_text_formatter(color_mode)
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    async def log(self, layer: str, level: str, message: str, 
                 extra: Optional[Dict[str, Any]] = None,
                 sanitize: bool = True,
                 validate_security: bool = True) -> None:
        """
        Log a message to a specific layer with comprehensive error handling.
        
        Args:
            layer (str): Layer to log to
            level (str): Log level
            message (str): Message to log
            extra (Optional[Dict[str, Any]]): Extra data
            sanitize (bool): Whether to sanitize the message
            validate_security (bool): Whether to validate security
        """
        if self._closed:
            return
        
        # Ensure initialization
        if not self._initialized:
            try:
                await self.initialize()
            except Exception as e:
                print(f"Failed to initialize async logger: {e}", file=sys.stderr)
                # Continue with fallback logging
        
        try:
            if not self._accepting_messages:
                return
                
            # Performance monitoring
            start_time = None
            if self._performance_monitor:
                try:
                    start_time = self._performance_monitor.start_log_processing_timer()
                except Exception:
                    pass  # Continue without performance monitoring
            
            # Security validation with fallback
            if validate_security and self._security_validator:
                try:
                    validate_fn = getattr(self._security_validator, 'validate_message', None) or getattr(self._security_validator, 'validate_input', None)
                    if callable(validate_fn):
                        validate_fn(message)
                        if self._performance_monitor:
                            self._performance_monitor.record_security_event()
                except Exception as e:
                    print(f"Security validation failed: {e}", file=sys.stderr)
                    # Continue without security validation
            
            # Data sanitization with fallback
            if sanitize and self._data_sanitizer:
                try:
                    sanitize_fn = getattr(self._data_sanitizer, 'sanitize_message', None) or getattr(self._data_sanitizer, 'sanitize_data', None)
                    if callable(sanitize_fn):
                        sanitized_message = sanitize_fn(message)
                        if isinstance(sanitized_message, str):
                            message = sanitized_message
                        if self._performance_monitor:
                            self._performance_monitor.record_sanitization_event()
                except Exception as e:
                    print(f"Data sanitization failed: {e}", file=sys.stderr)
                    # Continue with original message
            
            # Plugin processing with fallback
            if self.enable_plugins:
                for plugin_name, plugin in self._plugins.items():
                    try:
                        if hasattr(plugin, 'process_event'):
                            plugin.process_event({
                                "level": level,
                                "message": message,
                                "layer": layer,
                                "extra": extra
                            })
                            if self._performance_monitor:
                                self._performance_monitor.record_plugin_event()
                    except Exception as e:
                        print(f"Plugin processing failed for {plugin_name}: {e}", file=sys.stderr)
                        # Continue without this plugin
            
            # Redact sensitive information if enabled
            if self.redact_sensitive:
                try:
                    message = self._redact_sensitive_data(message)
                except Exception as e:
                    print(f"Redaction failed: {e}", file=sys.stderr)
                    # Continue with original message
            
            # Create log record with fallback
            record = None
            try:
                if self.enable_object_pooling and self._record_pool:
                    record = await self._record_pool.get_record(
                        name=layer,
                        level=getattr(logging, level.upper(), logging.INFO),
                        msg=message,
                        pathname="",
                        lineno=0,
                        func="",
                        exc_info=None
                    )
                else:
                    # Fallback to standard LogRecord creation
                    record = logging.LogRecord(
                        name=layer,
                        level=getattr(logging, level.upper(), logging.INFO),
                        pathname="",
                        lineno=0,
                        msg=message,
                        args=(),
                        exc_info=None
                    )
            except Exception as e:
                print(f"Failed to create log record: {e}", file=sys.stderr)
                # Create minimal record as last resort
                record = logging.LogRecord(
                    name=layer,
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=message,
                    args=(),
                    exc_info=None
                )
            
            # Queue the record with intelligent fallback
            success = False
            try:
                # Try async queue first
                if layer in self._async_queues:
                    success = await self._async_queues[layer].put(record)
                else:
                    # Try fallback layers
                    fallback_layers = ["DEFAULT", "__CENTRALIZED__"]
                    for fallback_layer in fallback_layers:
                        if fallback_layer in self._async_queues:
                            success = await self._async_queues[fallback_layer].put(record)
                            break
                    
                    # If no async queue available, use sync fallback
                    if not success:
                        await self._sync_fallback_log(layer, level, message)
                        success = True
                
                if success:
                    self._total_messages += 1
                else:
                    self._failed_messages += 1
                    if self._performance_monitor:
                        self._performance_monitor.record_error()
                        
            except Exception as e:
                print(f"Failed to queue log message: {e}", file=sys.stderr)
                # Final fallback to sync logging
                try:
                    await self._sync_fallback_log(layer, level, message)
                    self._total_messages += 1
                except Exception as fallback_error:
                    print(f"All logging fallbacks failed: {fallback_error}", file=sys.stderr)
                    self._failed_messages += 1
                    if self._performance_monitor:
                        self._performance_monitor.record_error()
            
            # End performance monitoring
            if self._performance_monitor and start_time:
                try:
                    self._performance_monitor.end_log_processing_timer(start_time)
                except Exception:
                    pass  # Ignore performance monitoring errors
                
        except Exception as e:
            self._failed_messages += 1
            if self._performance_monitor:
                self._performance_monitor.record_error()
            print(f"Critical error in async logging: {e}", file=sys.stderr)
    
    async def _sync_fallback_log(self, layer: str, level: str, message: str) -> None:
        """Fallback to sync logging when async logging fails."""
        try:
            if layer not in self._sync_loggers:
                from hydra_logger.core.logger import HydraLogger
                self._sync_loggers[layer] = HydraLogger(config=self.config)
            
            # Use sync logger with correct arguments
            log_method = getattr(self._sync_loggers[layer], level.lower(), self._sync_loggers[layer].info)
            log_method(message, layer=layer)
            
        except Exception as e:
            print(f"Sync fallback logging failed: {e}", file=sys.stderr)
            # Last resort - print to stderr
            print(f"[{level.upper()}] {layer}: {message}", file=sys.stderr)
    
    async def _get_or_create_async_logger(self, layer: str) -> AsyncLogHandler:
        """
        Get async logger with intelligent fallback chain.
        
        Fallback priority:
        1. Requested layer
        2. DEFAULT layer (user-defined)
        3. __CENTRALIZED__ layer (reserved)
        4. System logger (final fallback)
        """
        try:
            # Try requested layer
            if layer in self._async_queues:
                return self._async_queues[layer]
            
            # Try DEFAULT layer (user-defined)
            if "DEFAULT" in self._async_queues:
                return self._async_queues["DEFAULT"]
            
            # Try centralized fallback (reserved layer)
            if "__CENTRALIZED__" in self._async_queues:
                return self._async_queues["__CENTRALIZED__"]
            
            # Final fallback - create a basic async handler
            from hydra_logger.async_hydra.async_handlers import AsyncStreamHandler
            fallback_handler = AsyncStreamHandler()
            return fallback_handler
            
        except Exception as e:
            print(f"Error getting async logger for layer '{layer}': {e}", file=sys.stderr)
            # Last resort fallback
            from hydra_logger.async_hydra.async_handlers import AsyncStreamHandler
            return AsyncStreamHandler()
    
    async def debug(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log a debug message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "DEFAULT"
        else:
            layer = layer_or_message
        await self.log(layer, "DEBUG", message)
    
    async def info(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log an info message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "DEFAULT"
        else:
            layer = layer_or_message
        await self.log(layer, "INFO", message)
    
    async def warning(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log a warning message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "DEFAULT"
        else:
            layer = layer_or_message
        await self.log(layer, "WARNING", message)
    
    async def error(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log an error message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "DEFAULT"
        else:
            layer = layer_or_message
        await self.log(layer, "ERROR", message)
    
    async def critical(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log a critical message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "DEFAULT"
        else:
            layer = layer_or_message
        await self.log(layer, "CRITICAL", message)
    
    async def security(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log a security message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "SECURITY"
        else:
            layer = layer_or_message
        await self.log(layer, "WARNING", f"[SECURITY] {message}")
    
    async def audit(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log an audit message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "AUDIT"
        else:
            layer = layer_or_message
        await self.log(layer, "INFO", f"[AUDIT] {message}")
    
    async def compliance(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log a compliance message asynchronously."""
        if message is None:
            message = layer_or_message
            layer = "COMPLIANCE"
        else:
            layer = layer_or_message
        await self.log(layer, "INFO", f"[COMPLIANCE] {message}")
    
    def _get_calling_module_name(self) -> str:
        """Get the name of the calling module."""
        try:
            import inspect
            frame = inspect.currentframe()
            while frame:
                frame = frame.f_back
                if frame and frame.f_globals.get('__name__') != __name__:
                    module_name = frame.f_globals.get('__name__', 'unknown')
                    return module_name.split('.')[-1]
            return 'unknown'
        except Exception:
            return 'unknown'
    
    async def get_async_performance_statistics(self) -> Optional[Dict[str, float]]:
        """Get async performance statistics."""
        if self._async_performance_monitor:
            return self._async_performance_monitor.get_async_statistics()
        return None
    
    async def reset_async_performance_statistics(self) -> None:
        """Reset async performance statistics."""
        if self._async_performance_monitor:
            await self._async_performance_monitor.reset_async_statistics()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if self._performance_monitor:
            return self._performance_monitor.get_statistics()
        return {}
    
    def get_plugin_insights(self) -> Dict[str, Any]:
        """Get plugin insights."""
        insights = {}
        for name, plugin in self._plugins.items():
            if hasattr(plugin, 'get_insights'):
                insights[name] = plugin.get_insights()
        return insights
    
    def add_plugin(self, name: str, plugin: Any) -> None:
        """Add a plugin."""
        if not self._closed:
            self._plugins[name] = plugin
    
    def remove_plugin(self, name: str) -> bool:
        """Remove a plugin."""
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False
    
    def update_config(self, new_config: Union[LoggingConfig, Dict[str, Any]]) -> None:
        """Update configuration."""
        if self._closed:
            return
        
        if isinstance(new_config, dict):
            from hydra_logger.config.loaders import load_config_from_dict
            new_config = load_config_from_dict(new_config)
        
        self.config = new_config
        # Re-initialize with new config
        asyncio.create_task(self.initialize())
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics from the error tracker."""
        try:
            return self._error_tracker.get_error_stats()
        except Exception as e:
            print(f"Error getting error stats: {e}", file=sys.stderr)
            return {"error": "Failed to get error stats"}
    
    def clear_error_stats(self) -> None:
        """Clear error statistics."""
        try:
            self._error_tracker.clear_error_stats()
        except Exception as e:
            print(f"Error clearing error stats: {e}", file=sys.stderr)
    
    async def close(self) -> None:
        """
        Close the async logger and cleanup all resources.
        
        This method ensures proper cleanup of all async resources,
        handlers, and queues to prevent memory leaks.
        """
        if self._closed:
            return
        
        self._closed = True
        
        try:
            # Cancel all pending tasks
            if hasattr(self, '_pending_tasks'):
                for task in self._pending_tasks:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
            
            # Close all async handlers
            if hasattr(self, '_async_handlers'):
                for handler in self._async_handlers.values():
                    try:
                        if hasattr(handler, 'close'):
                            await handler.close()
                    except Exception:
                        pass
            
            # Close async queue
            if hasattr(self, '_async_queue'):
                try:
                    await self._async_queue.close()
                except Exception:
                    pass
            
            # Close batch processor
            if hasattr(self, '_batch_processor'):
                try:
                    await self._batch_processor.close()
                except Exception:
                    pass
            
            # Close backpressure handler
            if hasattr(self, '_backpressure_handler'):
                try:
                    await self._backpressure_handler.close()
                except Exception:
                    pass
            
            # Clear object pool if enabled
            if hasattr(self, '_record_pool') and self._record_pool:
                self._record_pool.close()
            
            # Clear correlation contexts
            if hasattr(self, '_correlation_context'):
                self._correlation_context.set(None)
            
            if hasattr(self, '_logger_context'):
                self._logger_context.set(None)
            
            # Clear all internal collections
            if hasattr(self, '_async_loggers'):
                self._async_loggers.clear()
            
            if hasattr(self, '_async_handlers'):
                self._async_handlers.clear()
            
            if hasattr(self, '_pending_tasks'):
                self._pending_tasks.clear()
            
            # Close performance monitor
            if hasattr(self, '_performance_monitor'):
                self._performance_monitor.reset_statistics()
            
        except Exception as e:
            # Log error but don't fail cleanup
            print(f"Error during async logger cleanup: {e}", file=sys.stderr)
        finally:
            # Ensure we're marked as closed even if cleanup fails
            self._closed = True

    # --- Magic Config System Methods ---
    @classmethod
    def register_magic(cls, name: str, description: str = "") -> Callable:
        """
        Register a custom magic configuration for async logger.
        Args:
            name: The name of the magic config (e.g., "my_async_app")
            description: Optional description of the config
        Returns:
            Decorator function that registers the config
        Example:
            @AsyncHydraLogger.register_magic("my_async_app")
            def my_async_config():
                return LoggingConfig(...)
        """
        return MagicConfigRegistry.register(name, description)

    @classmethod
    def for_custom(cls, name: str, **kwargs) -> 'AsyncHydraLogger':
        """
        Create an async logger using a custom magic configuration.
        Args:
            name: The name of the magic config to use
            **kwargs: Additional arguments to pass to AsyncHydraLogger constructor
        Returns:
            AsyncHydraLogger instance with the custom configuration
        Raises:
            HydraLoggerException: If the magic config is not found
        Example:
            logger = AsyncHydraLogger.for_custom("my_async_app")
        """
        try:
            config = MagicConfigRegistry.get_config(name)
            return cls(config=config, **kwargs)
        except Exception as e:
            # Fallback to default config if magic config fails
            print(f"Warning: Failed to load magic config '{name}': {e}", file=sys.stderr)
            return cls(**kwargs)

    @classmethod
    def list_magic_configs(cls) -> dict:
        """
        List all available magic configurations.
        Returns:
            Dictionary mapping config names to descriptions
        """
        return MagicConfigRegistry.list_configs()

    @classmethod
    def has_magic_config(cls, name: str) -> bool:
        """
        Check if a magic configuration exists.
        Args:
            name: The name of the magic config to check
        Returns:
            True if the config exists, False otherwise
        """
        return MagicConfigRegistry.has_config(name)

    # Built-in magic config methods for convenience
    @classmethod
    def for_production(cls, **kwargs) -> 'AsyncHydraLogger':
        """Create an async logger with production configuration."""
        return cls.for_custom("production", **kwargs)

    @classmethod
    def for_development(cls, **kwargs) -> 'AsyncHydraLogger':
        """Create an async logger with development configuration."""
        return cls.for_custom("development", **kwargs)

    @classmethod
    def for_testing(cls, **kwargs) -> 'AsyncHydraLogger':
        """Create an async logger with testing configuration."""
        return cls.for_custom("testing", **kwargs)

    @classmethod
    def for_microservice(cls, **kwargs) -> 'AsyncHydraLogger':
        """Create an async logger with microservice configuration."""
        return cls.for_custom("microservice", **kwargs)

    @classmethod
    def for_web_app(cls, **kwargs) -> 'AsyncHydraLogger':
        """Create an async logger with web application configuration."""
        return cls.for_custom("web_app", **kwargs)

    @classmethod
    def for_api_service(cls, **kwargs) -> 'AsyncHydraLogger':
        """Create an async logger with API service configuration."""
        return cls.for_custom("api_service", **kwargs)

    @classmethod
    def for_background_worker(cls, **kwargs) -> 'AsyncHydraLogger':
        """Create an async logger with background worker configuration."""
        return cls.for_custom("background_worker", **kwargs)

    @classmethod
    def for_high_performance(cls, **kwargs) -> 'AsyncHydraLogger':
        """
        Create a high-performance async logger optimized for maximum throughput.
        
        This configuration:
        - Uses optimal batch size (100) and timeout (0.001s) from benchmarks
        - Disables colors and formatting overhead
        - Uses larger queue size for better throughput
        - Disables data protection and backpressure for speed
        - Uses minimal retry delays
        - Caches handlers and formatters for efficiency
        
        Args:
            **kwargs: Additional arguments to pass to AsyncHydraLogger constructor
            
        Returns:
            AsyncHydraLogger: High-performance logger instance
            
        Example:
            logger = AsyncHydraLogger.for_high_performance()
            await logger.info("PERFORMANCE", "Fast log message")
        """
        try:
            # Use the high_performance magic config
            config = MagicConfigRegistry.get_config("high_performance")
            
            # Override with performance optimizations based on benchmark results
            return cls(
                config=config,
                enable_performance_monitoring=False,  # Disable monitoring overhead
                redact_sensitive=False,
                queue_size=50000,  # Much larger queue for high throughput
                batch_size=100,    # Optimal batch size from benchmarks
                batch_timeout=0.001, # Optimal timeout from benchmarks (1ms)
                **kwargs
            )
        except Exception as e:
            # Fallback to default config with performance optimizations
            print(f"Warning: Failed to load high_performance config: {e}", file=sys.stderr)
            return cls(
                enable_performance_monitoring=False,
                redact_sensitive=False,
                queue_size=50000,
                batch_size=100,
                batch_timeout=0.001,
                **kwargs
            )

    @classmethod
    def for_ultra_fast(cls, **kwargs) -> 'AsyncHydraLogger':
        """
        Create an ultra-fast async logger optimized for maximum throughput.
        
        This configuration:
        - Uses optimal parameters from benchmarks (batch=100, timeout=0.001)
        - Disables all monitoring and overhead features
        - Uses pre-computed formatters and handlers
        - Minimizes async operations
        - Uses direct string operations
        
        Args:
            **kwargs: Additional arguments to pass to AsyncHydraLogger constructor
            
        Returns:
            AsyncHydraLogger: Ultra-fast logger instance
            
        Example:
            logger = AsyncHydraLogger.for_ultra_fast()
            await logger.info("PERFORMANCE", "Ultra fast log message")
        """
        try:
            # Use the high_performance magic config
            config = MagicConfigRegistry.get_config("high_performance")
            
            # Override with ultra-fast optimizations
            return cls(
                config=config,
                enable_performance_monitoring=False,  # Disable all monitoring
                redact_sensitive=False,
                queue_size=100000,  # Very large queue
                batch_size=100,     # Optimal batch size from benchmarks
                batch_timeout=0.001, # Optimal timeout from benchmarks (1ms)
                **kwargs
            )
        except Exception as e:
            # Fallback to default config with ultra-fast optimizations
            print(f"Warning: Failed to load high_performance config: {e}", file=sys.stderr)
            return cls(
                enable_performance_monitoring=False,
                redact_sensitive=False,
                queue_size=100000,
                batch_size=100,
                batch_timeout=0.001,
                **kwargs
            )

    def start(self) -> None:
        """No-op for benchmark compatibility."""
        pass

    def stop(self) -> None:
        """No-op for benchmark compatibility."""
        pass

    async def flush(self) -> None:
        """
        Flush all pending messages in all queues.
        
        This method ensures all pending log messages are processed
        before returning, useful for testing and graceful shutdown.
        """
        for queue in self._async_queues.values():
            await queue.flush()
    
    async def await_pending(self) -> None:
        """
        Wait for all pending messages to be processed.
        
        This method waits until all queues are empty and all messages
        have been processed, providing deterministic shutdown.
        """
        for queue in self._async_queues.values():
            await queue.await_pending()
    
    async def graceful_shutdown(self, timeout: float = 30.0) -> None:
        """
        Gracefully shutdown the async logger with timeout.
        
        Args:
            timeout (float): Maximum time to wait for shutdown in seconds
        """
        try:
            # Stop accepting new messages
            self._accepting_messages = False
            
            # Flush all pending messages
            await self.flush()
            
            # Wait for processing to complete
            await asyncio.wait_for(self.await_pending(), timeout=timeout)
            
            # Close all components
            await self.close()
            
        except asyncio.TimeoutError:
            print(f"Warning: Async logger shutdown timed out after {timeout} seconds", file=sys.stderr)
            # Force close even if timeout
            await self.close()
        except Exception as e:
            print(f"Error during graceful shutdown: {e}", file=sys.stderr)
            await self.close()
    
    async def get_pending_count(self) -> int:
        """
        Get the total number of pending messages across all queues.
        
        Returns:
            int: Total number of messages waiting to be processed
        """
        total_pending = 0
        for queue in self._async_queues.values():
            total_pending += await queue.get_pending_count()
        return total_pending

    def _redact_sensitive_data(self, message: str) -> str:
        """
        Redact sensitive information from log messages.
        
        Args:
            message (str): Original message
            
        Returns:
            str: Message with sensitive data redacted
        """
        import re
        
        # Common patterns for sensitive data
        patterns = [
            r'password["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',  # passwords
            r'api_key["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',   # API keys
            r'token["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',     # tokens
            r'secret["\']?\s*[:=]\s*["\']?[^"\s]+["\']?',    # secrets
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',     # credit cards
            r'\b\d{3}-\d{2}-\d{4}\b',                        # SSN
        ]
        
        redacted_message = message
        for pattern in patterns:
            redacted_message = re.sub(pattern, '[REDACTED]', redacted_message, flags=re.IGNORECASE)
        
        return redacted_message

    async def log_structured(self, layer: str, level: str, message: str,
                           correlation_id: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None,
                           metadata: Optional[Dict[str, Any]] = None,
                           format: str = "json") -> None:
        """
        Log a structured message with context and correlation.
        
        Args:
            layer (str): Layer to log to
            level (str): Log level
            message (str): Message to log
            correlation_id (Optional[str]): Correlation ID for request tracing
            context (Optional[Dict[str, Any]]): Additional context
            metadata (Optional[Dict[str, Any]]): Additional metadata
            format (str): Output format (json, xml, dict)
        """
        try:
            # Get current context
            current_context = _correlation_context.get()
            if current_context is None:
                current_context = LogContext()
            
            # Update context with provided values
            if correlation_id:
                current_context.correlation_id = correlation_id
            if context:
                if current_context.custom_fields is None:
                    current_context.custom_fields = {}
                current_context.custom_fields.update(context)
            
            # Create structured log record
            structured_record = StructuredLogRecord(
                timestamp=datetime.now(),
                level=level.upper(),
                message=message,
                logger_name=layer,
                context=current_context,
                metadata=metadata or {}
            )
            
            # Convert to desired format
            if format.lower() == "json":
                formatted_message = structured_record.to_json()
            elif format.lower() == "xml":
                formatted_message = structured_record.to_xml()
            elif format.lower() == "dict":
                formatted_message = str(structured_record.to_dict())
            else:
                formatted_message = structured_record.to_json()
            
            # Log the formatted message
            await self.log(layer, level, formatted_message)
            
        except Exception as e:
            self._failed_messages += 1
            if self._performance_monitor:
                self._performance_monitor.record_error()
            if self.enable_performance_monitoring:
                print(f"Error in structured logging: {e}", file=sys.stderr)
    
    def set_correlation_context(self, correlation_id: str, **kwargs) -> None:
        """
        Set correlation context for the current execution context.
        
        Args:
            correlation_id (str): Correlation ID
            **kwargs: Additional context fields
        """
        context = LogContext(correlation_id=correlation_id, **kwargs)
        _correlation_context.set(context)
    
    def get_correlation_context(self) -> Optional[LogContext]:
        """
        Get current correlation context.
        
        Returns:
            Optional[LogContext]: Current correlation context
        """
        return _correlation_context.get()
    
    def clear_correlation_context(self) -> None:
        """Clear current correlation context."""
        _correlation_context.set(None)
    
    def set_logger_context(self, **kwargs) -> None:
        """
        Set logger context for the current execution context.
        
        Args:
            **kwargs: Context fields to set
        """
        current_context = _logger_context.get() or {}
        current_context.update(kwargs)
        _logger_context.set(current_context)
    
    def get_logger_context(self) -> Optional[Dict[str, Any]]:
        """
        Get current logger context.
        
        Returns:
            Optional[Dict[str, Any]]: Current logger context
        """
        return _logger_context.get()
    
    def clear_logger_context(self) -> None:
        """Clear current logger context."""
        _logger_context.set(None)
    
    async def log_with_context(self, layer: str, level: str, message: str,
                             **context_fields) -> None:
        """
        Log a message with automatic context injection.
        
        Args:
            layer (str): Layer to log to
            level (str): Log level
            message (str): Message to log
            **context_fields: Additional context fields
        """
        # Get current contexts
        correlation_context = self.get_correlation_context()
        logger_context = self.get_logger_context()
        
        # Merge contexts
        merged_context = {}
        if correlation_context:
            merged_context.update(correlation_context.to_dict())
        if logger_context:
            merged_context.update(logger_context)
        if context_fields:
            merged_context.update(context_fields)
        
        # Log with structured context
        await self.log_structured(
            layer=layer,
            level=level,
            message=message,
            context=merged_context
        )

    def correlation_context(self, correlation_id: str, **kwargs):
        """
        Context manager for correlation context.
        
        Args:
            correlation_id (str): Correlation ID
            **kwargs: Additional context fields
            
        Example:
            with logger.correlation_context("req-123", user_id="456"):
                await logger.info("Processing request")
        """
        return CorrelationContextManager(self, correlation_id, **kwargs)
    
    def logger_context(self, **kwargs):
        """
        Context manager for logger context.
        
        Args:
            **kwargs: Context fields to set
            
        Example:
            with logger.logger_context(user_id="456", session_id="abc"):
                await logger.info("User action")
        """
        return LoggerContextManager(self, **kwargs)

    async def log_request(self, request_id: str, method: str, path: str, 
                         status_code: Optional[int] = None, 
                         duration: Optional[float] = None,
                         **kwargs) -> None:
        """
        Log HTTP request information with structured context.
        
        Args:
            request_id (str): Unique request identifier
            method (str): HTTP method (GET, POST, etc.)
            path (str): Request path
            status_code (Optional[int]): HTTP status code
            duration (Optional[float]): Request duration in seconds
            **kwargs: Additional context fields
        """
        context = {
            "request_id": request_id,
            "method": method,
            "path": path,
            **kwargs
        }
        
        if status_code is not None:
            context["status_code"] = status_code
        if duration is not None:
            context["duration"] = duration
        
        await self.log_structured(
            layer="REQUEST",
            level="INFO",
            message=f"{method} {path}",
            correlation_id=request_id,
            context=context
        )
    
    async def log_user_action(self, user_id: str, action: str, 
                             resource: Optional[str] = None,
                             success: bool = True,
                             **kwargs) -> None:
        """
        Log user actions with structured context.
        
        Args:
            user_id (str): User identifier
            action (str): Action performed
            resource (Optional[str]): Resource affected
            success (bool): Whether action was successful
            **kwargs: Additional context fields
        """
        context = {
            "user_id": user_id,
            "action": action,
            "success": success,
            **kwargs
        }
        
        if resource:
            context["resource"] = resource
        
        level = "INFO" if success else "WARNING"
        message = f"User {user_id} performed {action}"
        if resource:
            message += f" on {resource}"
        
        await self.log_structured(
            layer="USER_ACTION",
            level=level,
            message=message,
            context=context
        )
    
    async def log_error_with_context(self, error: Exception, 
                                   layer: str = "ERROR",
                                   context: Optional[Dict[str, Any]] = None,
                                   **kwargs) -> None:
        """
        Log an exception with structured context.
        
        Args:
            error (Exception): The exception to log
            layer (str): Logging layer
            context (Optional[Dict[str, Any]]): Additional context
            **kwargs: Additional context fields
        """
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs
        }
        
        if context:
            error_context.update(context)
        
        await self.log_structured(
            layer=layer,
            level="ERROR",
            message=f"Exception: {str(error)}",
            context=error_context
        )
    
    async def log_performance(self, operation: str, duration: float,
                            layer: str = "PERFORMANCE",
                            **kwargs) -> None:
        """
        Log performance metrics with structured context.
        
        Args:
            operation (str): Operation name
            duration (float): Duration in seconds
            layer (str): Logging layer
            **kwargs: Additional context fields
        """
        context = {
            "operation": operation,
            "duration": duration,
            "duration_ms": duration * 1000,
            **kwargs
        }
        
        level = "INFO"
        if duration > 1.0:
            level = "WARNING"
        elif duration > 5.0:
            level = "ERROR"
        
        await self.log_structured(
            layer=layer,
            level=level,
            message=f"{operation} took {duration:.3f}s",
            context=context
        )

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the async logger.
        
        Returns:
            Dict[str, Any]: Health status including all components
        """
        try:
            health_status = {
                "initialized": self._initialized,
                "accepting_messages": self._accepting_messages,
                "queue_count": len(self._async_queues),
                "handler_count": len(self.async_loggers),
                "total_messages": self._total_messages,
                "failed_messages": self._failed_messages,
                "queues": {},
                "performance": {},
                "errors": []
            }
            
            # Check each queue
            for queue_name, queue in self._async_queues.items():
                try:
                    stats = queue.get_stats()
                    health_status["queues"][queue_name] = {
                        "running": queue._running,
                        "queue_size": stats.queue_size,
                        "max_queue_size": stats.max_queue_size,
                        "processed_messages": stats.processed_messages,
                        "failed_messages": stats.failed_messages,
                        "error_count": stats.error_count,
                        "recovery_count": stats.recovery_count
                    }
                except Exception as e:
                    health_status["errors"].append(f"Error checking queue {queue_name}: {e}")
            
            # Get performance statistics
            if self._performance_monitor:
                health_status["performance"]["sync"] = self._performance_monitor.get_statistics()
            
            if self._async_performance_monitor:
                health_status["performance"]["async"] = self._async_performance_monitor.get_async_statistics()
            
            # Check object pool if enabled
            if self._record_pool:
                health_status["object_pool"] = self._record_pool.get_stats()
            
            return health_status
            
        except Exception as e:
            return {
                "error": f"Failed to get health status: {e}",
                "initialized": self._initialized,
                "accepting_messages": self._accepting_messages
            }
    
    async def is_healthy(self) -> bool:
        """
        Check if the async logger is healthy.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                return False
            
            if not self._accepting_messages:
                return False
            
            # Check all queues are running
            for queue_name, queue in self._async_queues.items():
                if not queue._running:
                    return False
                
                # Check for excessive errors
                stats = queue.get_stats()
                if stats.error_count > 50:  # Threshold for unhealthy
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """
        Get detailed metrics for monitoring and alerting.
        
        Returns:
            Dict[str, Any]: Detailed metrics
        """
        try:
            metrics = {
                "timestamp": time.time(),
                "health": await self.is_healthy(),
                "queues": {},
                "performance": {},
                "memory": {},
                "errors": []
            }
            
            # Queue metrics
            for queue_name, queue in self._async_queues.items():
                stats = queue.get_stats()
                metrics["queues"][queue_name] = {
                    "queue_size": stats.queue_size,
                    "max_queue_size": stats.max_queue_size,
                    "utilization_percent": (stats.queue_size / stats.max_queue_size) * 100 if stats.max_queue_size > 0 else 0,
                    "processed_messages": stats.processed_messages,
                    "failed_messages": stats.failed_messages,
                    "dropped_messages": stats.dropped_messages,
                    "error_count": stats.error_count,
                    "recovery_count": stats.recovery_count,
                    "avg_processing_time": stats.avg_processing_time,
                    "batch_count": stats.batch_count
                }
            
            # Performance metrics
            if self._performance_monitor:
                sync_stats = self._performance_monitor.get_statistics()
                metrics["performance"]["sync"] = sync_stats
            
            if self._async_performance_monitor:
                async_stats = self._async_performance_monitor.get_async_statistics()
                metrics["performance"]["async"] = async_stats
            
            # Memory metrics
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                metrics["memory"] = {
                    "rss_mb": memory_info.rss / 1024 / 1024,
                    "vms_mb": memory_info.vms / 1024 / 1024,
                    "percent": process.memory_percent()
                }
            except ImportError:
                metrics["memory"] = {"error": "psutil not available"}
            
            return metrics
            
        except Exception as e:
            return {
                "error": f"Failed to get detailed metrics: {e}",
                "timestamp": time.time()
            }


class CorrelationContextManager:
    """Context manager for correlation context."""
    
    def __init__(self, logger: AsyncHydraLogger, correlation_id: str, **kwargs):
        self.logger = logger
        self.correlation_id = correlation_id
        self.kwargs = kwargs
        self.previous_context = None
    
    def __enter__(self):
        # Store previous context
        self.previous_context = self.logger.get_correlation_context()
        
        # Set new context
        self.logger.set_correlation_context(self.correlation_id, **self.kwargs)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self.previous_context:
            _correlation_context.set(self.previous_context)
        else:
            _correlation_context.set(None)


class LoggerContextManager:
    """Context manager for logger context."""
    
    def __init__(self, logger: AsyncHydraLogger, **kwargs):
        self.logger = logger
        self.kwargs = kwargs
        self.previous_context = None
    
    def __enter__(self):
        # Store previous context
        self.previous_context = self.logger.get_logger_context()
        
        # Set new context
        self.logger.set_logger_context(**self.kwargs)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self.previous_context:
            _logger_context.set(self.previous_context)
        else:
            _logger_context.set(None)


class AsyncCompositeHandler(AsyncLogHandler):
    """Composite async handler that combines multiple async handlers."""
    
    def __init__(self, handlers: List[AsyncLogHandler]):
        super().__init__()
        self.handlers = handlers
    
    async def emit_async(self, record: logging.LogRecord) -> None:
        """Emit a record to all handlers."""
        await self._process_record_async(record)
    
    async def _process_record_async(self, record: logging.LogRecord) -> None:
        """Process a record through all handlers."""
        for handler in self.handlers:
            try:
                await handler.emit_async(record)
            except Exception as e:
                print(f"Error in async composite handler: {e}", file=sys.stderr)
    
    async def close(self) -> None:
        """Close all handlers."""
        for handler in self.handlers:
            try:
                await handler.aclose()
            except Exception as e:
                print(f"Error closing async handler: {e}", file=sys.stderr) 