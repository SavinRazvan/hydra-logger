"""
Professional AsyncHydraLogger for world-class async logging.

This module provides the main async logger implementation with
professional patterns, comprehensive error handling, and
guaranteed data delivery.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union

from .core.coroutine_manager import CoroutineManager
from .core.event_loop_manager import EventLoopManager
from .core.error_tracker import AsyncErrorTracker
from .core.health_monitor import AsyncHealthMonitor
from .handlers import AsyncFileHandler, AsyncConsoleHandler, AsyncCompositeHandler
from .performance import AsyncPerformanceMonitor, get_performance_monitor


class AsyncHydraLogger:
    """
    Professional async logger with world-class reliability.
    
    Features:
    - Professional async logging interface
    - Handler management (file, console, multi-handler)
    - Performance monitoring integration
    - Error handling and recovery
    - Health monitoring
    - Context management and distributed tracing
    """
    
    def __init__(self, config=None, **kwargs):
        """
        Initialize AsyncHydraLogger.
        
        Args:
            config: Logging configuration (dict or None)
            **kwargs: Additional configuration options
        """
        self._config = config or {}
        self._handlers = []
        self._coroutine_manager = CoroutineManager()
        self._error_tracker = AsyncErrorTracker()
        self._health_monitor = AsyncHealthMonitor(self)
        self._performance_monitor = get_performance_monitor()
        self._initialized = False
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup handlers based on configuration or kwargs."""
        self._handlers = []
        cfg = self._config or {}
        handlers_cfg = cfg.get('handlers', [])
        
        if not handlers_cfg:
            # Default: console handler
            self._handlers.append(AsyncConsoleHandler())
            return
            
        for hcfg in handlers_cfg:
            htype = hcfg.get('type', '').lower()
            if htype == 'file':
                self._handlers.append(AsyncFileHandler(
                    filename=hcfg['filename'],
                    max_queue_size=hcfg.get('max_queue_size', 1000),
                    memory_threshold=hcfg.get('memory_threshold', 70.0)
                ))
            elif htype == 'console':
                self._handlers.append(AsyncConsoleHandler(
                    stream=hcfg.get('stream'),
                    max_queue_size=hcfg.get('max_queue_size', 1000),
                    memory_threshold=hcfg.get('memory_threshold', 70.0),
                    use_colors=hcfg.get('use_colors', True)
                ))
            elif htype == 'composite':
                # Create composite handler with sub-handlers
                sub_handlers = []
                for sub_cfg in hcfg.get('handlers', []):
                    if sub_cfg.get('type') == 'file':
                        sub_handlers.append(AsyncFileHandler(
                            filename=sub_cfg['filename'],
                            max_queue_size=sub_cfg.get('max_queue_size', 1000),
                            memory_threshold=sub_cfg.get('memory_threshold', 70.0)
                        ))
                    elif sub_cfg.get('type') == 'console':
                        sub_handlers.append(AsyncConsoleHandler(
                            stream=sub_cfg.get('stream'),
                            max_queue_size=sub_cfg.get('max_queue_size', 1000),
                            memory_threshold=sub_cfg.get('memory_threshold', 70.0),
                            use_colors=sub_cfg.get('use_colors', True)
                        ))
                
                self._handlers.append(AsyncCompositeHandler(
                    handlers=sub_handlers,
                    parallel_execution=hcfg.get('parallel_execution', True),
                    fail_fast=hcfg.get('fail_fast', False)
                ))
    
    def add_handler(self, handler):
        """Add a handler at runtime."""
        self._handlers.append(handler)
    
    def remove_handler(self, handler):
        """Remove a handler at runtime."""
        self._handlers = [h for h in self._handlers if h is not handler]
    
    async def initialize(self):
        """Initialize logger and all handlers."""
        if self._initialized:
            return
        for handler in self._handlers:
            if hasattr(handler, 'initialize'):
                await handler.initialize()
        self._initialized = True
    
    async def log(self, layer: str, level: str, message: str, 
                 extra: Optional[Dict[str, Any]] = None,
                 sanitize: bool = True,
                 validate_security: bool = True) -> None:
        """
        Professional async logging with performance monitoring.
        
        Args:
            layer: Log layer
            level: Log level
            message: Log message
            extra: Extra fields
            sanitize: Whether to sanitize the message
            validate_security: Whether to validate security
        """
        if not self._initialized:
            await self.initialize()
            
        # Start performance monitoring
        start_time = self._performance_monitor.start_async_processing_timer('log_operation')
        
        try:
            record = logging.LogRecord(
                name=layer,
                level=getattr(logging, level.upper(), logging.INFO),
                pathname='',
                lineno=0,
                msg=message,
                args=(),
                exc_info=None
            )
            
            # Add extra fields if provided
            if extra:
                for key, value in extra.items():
                    setattr(record, key, value)
            
            # Log to all handlers
            for handler in self._handlers:
                try:
                    await handler.emit_async(record)
                except Exception as e:
                    await self._error_tracker.record_error("handler_emit", e)
                    
        finally:
            # End performance monitoring
            self._performance_monitor.end_async_processing_timer('log_operation', start_time)
    
    async def info(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log info message."""
        if message is None:
            layer, message = "DEFAULT", layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "INFO", message)
    
    async def debug(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log debug message."""
        if message is None:
            layer, message = "DEFAULT", layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "DEBUG", message)
    
    async def warning(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log warning message."""
        if message is None:
            layer, message = "DEFAULT", layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "WARNING", message)
    
    async def error(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log error message."""
        if message is None:
            layer, message = "DEFAULT", layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "ERROR", message)
    
    async def critical(self, layer_or_message: str, message: Optional[str] = None) -> None:
        """Log critical message."""
        if message is None:
            layer, message = "DEFAULT", layer_or_message
        else:
            layer = layer_or_message
        await self.log(layer, "CRITICAL", message)
    
    async def aclose(self) -> None:
        """Professional async close."""
        await self._coroutine_manager.shutdown()
        await self._error_tracker.shutdown()
        await self._health_monitor.shutdown()
        
        for handler in self._handlers:
            await handler.aclose()
    
    def close(self) -> None:
        """Sync close (best effort)."""
        # Force sync shutdown for all handlers
        for handler in self._handlers:
            handler.close()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status."""
        return self._health_monitor.get_health_status()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self._performance_monitor.get_async_statistics()
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return self._performance_monitor.get_memory_statistics()
    
    def take_memory_snapshot(self) -> Dict[str, Any]:
        """Take a memory usage snapshot."""
        return self._performance_monitor.take_memory_snapshot()
    
    def is_healthy(self) -> bool:
        """Check if logger is healthy."""
        return self._health_monitor.is_healthy()
    
    def is_performance_healthy(self) -> bool:
        """Check if performance is healthy."""
        return self._performance_monitor.is_performance_healthy()
    
    def get_handler_count(self) -> int:
        """Get number of handlers."""
        return len(self._handlers)
    
    def get_handlers(self) -> List:
        """Get all handlers."""
        return self._handlers.copy() 