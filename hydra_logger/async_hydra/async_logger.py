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
import time
from typing import Any, Dict, List, Optional, Union

from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from hydra_logger.logger import HydraLogger, PerformanceMonitor
from hydra_logger.async_hydra.async_handlers import AsyncLogHandler, AsyncRotatingFileHandler, AsyncStreamHandler
from hydra_logger.async_hydra.async_queue import AsyncLogQueue, AsyncBatchProcessor, AsyncBackpressureHandler


class AsyncPerformanceMonitor(PerformanceMonitor):
    """
    Async performance monitor for AsyncHydraLogger.
    
    Extends PerformanceMonitor with async-specific metrics and monitoring
    capabilities for async logging operations.
    """
    
    def __init__(self):
        super().__init__()
        self._async_processing_times: List[float] = []
        self._async_queue_times: List[float] = []
        self._async_batch_times: List[float] = []
        self._async_context_switches: int = 0
    
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
            self.reset_statistics()


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
                 enable_performance_monitoring: bool = False,
                 redact_sensitive: bool = False,
                 queue_size: int = 1000,
                 batch_size: int = 100,
                 batch_timeout: float = 1.0):
        """
        Initialize AsyncHydraLogger.
        
        Args:
            config (Optional[LoggingConfig]): Logging configuration
            enable_performance_monitoring (bool): Enable async performance monitoring
            redact_sensitive (bool): Auto-redact sensitive information
            queue_size (int): Maximum queue size for async operations
            batch_size (int): Batch size for async processing
            batch_timeout (float): Timeout for batch processing
        """
        # Use provided config or default
        if config is None:
            from hydra_logger.config import get_default_config
            self.config = get_default_config()
        else:
            self.config = config
        
        self.async_loggers: Dict[str, AsyncLogHandler] = {}
        self.performance_monitoring = enable_performance_monitoring
        self.redact_sensitive = redact_sensitive
        self.queue_size = queue_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        # Initialize async components
        self._async_performance_monitor = AsyncPerformanceMonitor() if enable_performance_monitoring else None
        self._async_queues: Dict[str, AsyncLogQueue] = {}
        self._backpressure_handler = AsyncBackpressureHandler(
            max_queue_size=queue_size,
            drop_threshold=0.9,
            slow_down_threshold=0.7
        )
        self._logger_init_lock = asyncio.Lock()
        self._initialized = False
    
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
                processor=self._create_async_processor(layer_name)
            )
            self._async_queues[layer_name] = queue
            
            # Start the queue
            await queue.start()
            
            # Create async handlers for each destination
            async_handlers = []
            for destination in layer_config.destinations:
                handler = await self._create_async_handler(destination, layer_config.level)
                if handler:
                    async_handlers.append(handler)
            
            # Create composite async handler
            if async_handlers:
                composite_handler = AsyncCompositeHandler(async_handlers)
                self.async_loggers[layer_name] = composite_handler
            else:
                # Create fallback async handler
                fallback_handler = AsyncStreamHandler()
                self.async_loggers[layer_name] = fallback_handler
            
        except Exception as e:
            print(f"Error setting up async layer '{layer_name}': {e}", file=sys.stderr)
            # Create fallback async handler
            fallback_handler = AsyncStreamHandler()
            self.async_loggers[layer_name] = fallback_handler
    
    async def _create_async_handler(self, destination: LogDestination, layer_level: str) -> Optional[AsyncLogHandler]:
        """
        Create an async handler for a destination.
        
        Args:
            destination (LogDestination): LogDestination configuration
            layer_level (str): The level of the layer
            
        Returns:
            Optional[AsyncLogHandler]: Configured async handler or None
        """
        try:
            if destination.type == "file":
                if not destination.path:
                    print(f"Warning: File destination missing path for layer", file=sys.stderr)
                    return None
                
                handler = AsyncRotatingFileHandler(
                    filename=str(destination.path),
                    maxBytes=self._parse_size(destination.max_size or "5MB"),
                    backupCount=destination.backup_count or 3,
                    encoding="utf-8"
                )
                handler.setLevel(getattr(logging, layer_level))
                return handler
                
            elif destination.type == "console":
                handler = AsyncStreamHandler(
                    stream=sys.stdout,
                    use_colors=True
                )
                handler.setLevel(getattr(logging, layer_level))
                return handler
                
            else:
                print(f"Warning: Unknown destination type '{destination.type}'", file=sys.stderr)
                return None
                
        except Exception as e:
            print(f"Error creating async handler: {e}", file=sys.stderr)
            return None
    
    def _create_async_processor(self, layer_name: str):
        """
        Create async processor for a layer.
        
        Args:
            layer_name (str): Layer name
            
        Returns:
            Callable: Async processor function
        """
        async def processor(messages: List[Any]) -> None:
            """Process messages for the layer."""
            if not messages:
                return
                
            # Get async logger for this layer
            logger = self.async_loggers.get(layer_name)
            if not logger:
                return
                
            async def process_messages():
                tasks = []
                for message in messages:
                    task = asyncio.create_task(logger.emit_async(message))
                    tasks.append(task)
                
                # Wait for all tasks to complete
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            
            # Run the async function
            asyncio.create_task(process_messages())
        
        return processor
    
    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string to bytes.
        
        Args:
            size_str (str): Size string like "5MB", "1GB", etc.
            
        Returns:
            int: Size in bytes
        """
        if not size_str:
            return 0
            
        size_str = size_str.upper().strip()
        
        try:
            if size_str.endswith("KB"):
                return int(size_str[:-2]) * 1024
            elif size_str.endswith("MB"):
                return int(size_str[:-2]) * 1024 * 1024
            elif size_str.endswith("GB"):
                return int(size_str[:-2]) * 1024 * 1024 * 1024
            elif size_str.endswith("B"):
                return int(size_str[:-1])
            else:
                return int(size_str)
        except ValueError:
            return 0
    
    async def log(self, layer: str, level: str, message: str) -> None:
        """
        Log a message to a specific layer asynchronously.
        
        Args:
            layer (str): Layer name to log to
            level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message (str): Message to log
        """
        if not message:
            return
        
        # Ensure logger is initialized
        if not self._initialized:
            await self.initialize()
        
        # Redact sensitive data if enabled
        if self.redact_sensitive:
            from hydra_logger.logger import redact_sensitive_data
            message = redact_sensitive_data(message)
        
        # Start performance monitoring if enabled
        start_time = None
        if self._async_performance_monitor:
            start_time = await self._async_performance_monitor.start_async_processing_timer()
        
        try:
            # Normalize the level
            level = level.upper()
            
            # Validate the level
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if level not in valid_levels:
                raise ValueError(f"Invalid log level '{level}'. Must be one of {valid_levels}")
            
            # Create log record
            record = logging.LogRecord(
                name=layer,
                level=getattr(logging, level),
                pathname="",
                lineno=0,
                msg=message,
                args=(),
                exc_info=None
            )
            
            # Get or create async logger for this layer
            async_logger = await self._get_or_create_async_logger(layer)
            
            # Add to async queue for processing
            queue = self._async_queues.get(layer)
            if queue:
                await queue.put(record)
            else:
                # Fallback: emit directly
                await async_logger.emit_async(record)
                
        except Exception as e:
            print(f"Error in async logging: {e}", file=sys.stderr)
        finally:
            # End performance monitoring if enabled
            if self._async_performance_monitor and start_time is not None:
                await self._async_performance_monitor.end_async_processing_timer(start_time)
    
    async def _get_or_create_async_logger(self, layer: str) -> AsyncLogHandler:
        """
        Get existing async logger or create a new one.
        
        Args:
            layer (str): Layer name
            
        Returns:
            AsyncLogHandler: Async logger for the layer
        """
        if layer in self.async_loggers:
            return self.async_loggers[layer]
        
        async with self._logger_init_lock:
            if layer in self.async_loggers:
                return self.async_loggers[layer]
            
            # Create a fallback async logger
            fallback_handler = AsyncStreamHandler()
            self.async_loggers[layer] = fallback_handler
            return fallback_handler
    
    async def debug(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async debug logging."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "DEBUG", message)
    
    async def info(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async info logging."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "INFO", message)
    
    async def warning(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async warning logging."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "WARNING", message)
    
    async def error(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async error logging."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "ERROR", message)
    
    async def critical(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async critical logging."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "CRITICAL", message)
    
    async def security(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async security logging with automatic redaction."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        
        if not message or message.strip() == "":
            return
        
        # Always redact sensitive data for security events
        from hydra_logger.logger import redact_sensitive_data
        redacted_message = redact_sensitive_data(message)
        await self.log(layer, "WARNING", f"[SECURITY] {redacted_message}")
    
    async def audit(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async audit logging with comprehensive tracking."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        
        if not message or message.strip() == "":
            return
        
        # Add audit context
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        audit_message = f"[AUDIT] {timestamp} - {message}"
        
        # Audit events are always redacted
        original_redact_setting = self.redact_sensitive
        self.redact_sensitive = True
        try:
            await self.log(layer, "INFO", audit_message)
        finally:
            self.redact_sensitive = original_redact_setting
    
    async def compliance(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Async compliance logging with regulatory tracking."""
        if message is None:
            layer = self._get_calling_module_name()
            message = layer_or_message
        else:
            layer = layer_or_message
        
        if not message or message.strip() == "":
            return
        
        # Add compliance context
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        compliance_message = f"[COMPLIANCE] {timestamp} - {message}"
        
        # Compliance events are always redacted
        original_redact_setting = self.redact_sensitive
        self.redact_sensitive = True
        try:
            await self.log(layer, "INFO", compliance_message)
        finally:
            self.redact_sensitive = original_redact_setting
    
    def _get_calling_module_name(self) -> str:
        """
        Get the name of the calling module for automatic module name detection.
        
        Returns:
            str: The name of the calling module or 'DEFAULT' as fallback
        """
        try:
            import inspect
            frame = inspect.currentframe()
            if frame:
                caller_frame = frame.f_back
                if caller_frame:
                    caller_frame = caller_frame.f_back
                    if caller_frame:
                        module_name = caller_frame.f_globals.get('__name__', 'DEFAULT')
                        if module_name != '__main__':
                            return module_name
        except Exception:
            pass
        return 'DEFAULT'
    
    async def get_async_performance_statistics(self) -> Optional[Dict[str, float]]:
        """
        Get current async performance statistics.
        
        Returns:
            Optional[Dict[str, float]]: Async performance statistics or None
        """
        if self._async_performance_monitor:
            return self._async_performance_monitor.get_async_statistics()
        return None
    
    async def reset_async_performance_statistics(self) -> None:
        """Reset all async performance statistics."""
        if self._async_performance_monitor:
            await self._async_performance_monitor.reset_async_statistics()
    
    async def close(self) -> None:
        """Close the async logger and cleanup resources."""
        try:
            # Stop all async queues
            for queue in self._async_queues.values():
                await queue.stop()
            
            # Stop all async loggers
            for logger in self.async_loggers.values():
                await logger.stop()
            
            # Clear loggers and queues
            self.async_loggers.clear()
            self._async_queues.clear()
            
        except Exception as e:
            print(f"Error closing async logger: {type(e).__name__}: {e}", file=sys.stderr)


class AsyncCompositeHandler(AsyncLogHandler):
    """
    Composite async handler that routes to multiple async handlers.
    
    This handler combines multiple async handlers and routes log records
    to all of them asynchronously.
    """
    
    def __init__(self, handlers: List[AsyncLogHandler]):
        """
        Initialize composite async handler.
        
        Args:
            handlers (List[AsyncLogHandler]): List of async handlers
        """
        super().__init__()
        self.handlers = handlers
    
    async def _process_record_async(self, record: logging.LogRecord) -> None:
        """Process record through all handlers."""
        tasks = []
        for handler in self.handlers:
            task = asyncio.create_task(handler.emit_async(record))
            tasks.append(task)
        
        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True) 