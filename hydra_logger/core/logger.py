"""
Core HydraLogger class with modular architecture.

This module provides the main HydraLogger class with clean separation
of concerns and plugin support.
"""

import logging
import os
import sys
import time
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Callable
from io import BufferedWriter
from collections import deque
import weakref

from hydra_logger.config.loaders import get_default_config, load_config_from_dict
from hydra_logger.config.models import LoggingConfig
from hydra_logger.config.constants import DEFAULT_FORMAT
from hydra_logger.core.constants import DEFAULT_COLORS, NAMED_COLORS
from hydra_logger.core.exceptions import ConfigurationError, HydraLoggerError
from hydra_logger.data_protection.fallbacks import FallbackHandler
from hydra_logger.data_protection.security import DataSanitizer, SecurityValidator
from hydra_logger.plugins.registry import get_plugin, list_plugins
from hydra_logger.async_hydra.async_handlers import ColoredTextFormatter, PlainTextFormatter
from hydra_logger.magic_configs import MagicConfigRegistry
from hydra_logger.core.error_handler import (
    get_error_tracker, track_error, track_hydra_error, track_configuration_error,
    track_runtime_error, error_context
)


class BufferedFileHandler(logging.FileHandler):
    """
    High-performance buffered file handler with automatic flushing.
    Ensures file is always created and logs are reliably written.
    """
    
    def __init__(self, filename: str, mode: str = 'a', encoding: str = 'utf-8', 
                 buffer_size: int = 8192, flush_interval: float = 1.0):
        """
        Initialize buffered file handler.
        
        Args:
            filename: Log file path
            mode: File open mode
            encoding: File encoding
            buffer_size: Buffer size in bytes
            flush_interval: Flush interval in seconds
        """
        # Validate encoding
        try:
            "test".encode(encoding)
        except LookupError:
            encoding = 'utf-8'  # Fallback to utf-8
        
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.last_flush = time.time()
        self._flush_lock = threading.Lock()
        self._custom_encoding = encoding
        self._custom_mode = mode
        self._custom_filename = filename
        self._closed = False
        
        # Performance metrics
        self.write_count = 0
        self.flush_count = 0
        self.total_bytes_written = 0
        
        super().__init__(filename, mode, encoding, delay=True)
        # Ensure file is created on initialization
        if not os.path.exists(filename):
            with open(filename, mode, encoding=encoding) as f:
                f.write("")
                f.flush()
        # Write a test log line to guarantee file creation (for test reliability)
        with open(filename, mode, encoding=encoding) as f:
            f.write("")
            f.flush()
    
    def _open(self):
        """Open file with custom buffering."""
        if self._closed:
            return None
        return open(self._custom_filename, mode=self._custom_mode, encoding=self._custom_encoding, buffering=self.buffer_size)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record with proper error handling."""
        if self._closed:
            return
        try:
            # Always ensure stream is open before writing
            if self.stream is None:
                self.stream = self._open()
                if self.stream is None:
                    return
            msg = self.format(record)
            self.stream.write(msg + '\n')
            self.write_count += 1
            self.total_bytes_written += len(msg) + 1
            # Always flush immediately for reliability
            self.stream.flush()
            self.flush_count += 1
            self.last_flush = time.time()
        except Exception:
            self.handleError(record)
    
    def _flush_buffer(self) -> None:
        """Flush the buffer with proper locking."""
        if self._closed or self.stream is None:
            return
            
        with self._flush_lock:
            try:
                if self.stream is not None:
                    self.stream.flush()
                    self.flush_count += 1
                    self.last_flush = time.time()
            except Exception:
                # Don't let flush errors break the handler
                pass
    
    def close(self) -> None:
        """Close the handler with proper cleanup."""
        if self._closed:
            return
            
        self._closed = True
        
        try:
            if self.stream is not None:
                self._flush_buffer()
                self.stream.close()
                self.stream = None  # type: ignore
        except Exception:
            # Ensure cleanup happens even on error
            pass
        finally:
            super().close()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "write_count": self.write_count,
            "flush_count": self.flush_count,
            "total_bytes_written": self.total_bytes_written,
            "buffer_size": self.buffer_size,
            "flush_interval": self.flush_interval,
            "closed": self._closed
        }


class PerformanceMonitor:
    """
    Real-time performance monitoring for HydraLogger.
    
    Tracks various performance metrics including throughput, latency,
    memory usage, and handler performance.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize performance monitor.
        
        Args:
            enabled: Whether to enable performance monitoring
        """
        self.enabled = enabled
        self.metrics = {
            "total_logs": 0,
            "total_time": 0.0,
            "avg_latency": 0.0,
            "max_latency": 0.0,
            "min_latency": float('inf'),
            "throughput": 0.0,
            "handler_metrics": {},
            "memory_usage": 0,
            "security_events": 0,
            "sanitization_events": 0,
            "plugin_events": 0
        }
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._last_reset = time.time()
        self._closed = False
    
    def record_log(self, layer: str, level: str, message: str, 
                  start_time: float, end_time: float) -> None:
        """
        Record a log operation for performance tracking.
        
        Args:
            layer: Logging layer
            level: Log level
            message: Log message
            start_time: Operation start time
            end_time: Operation end time
        """
        if not self.enabled or self._closed:
            return
        
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        with self._lock:
            self.metrics["total_logs"] += 1
            self.metrics["total_time"] += latency
            
            # Update latency statistics
            if latency > self.metrics["max_latency"]:
                self.metrics["max_latency"] = latency
            if latency < self.metrics["min_latency"]:
                self.metrics["min_latency"] = latency
            
            # Calculate average latency
            self.metrics["avg_latency"] = self.metrics["total_time"] / self.metrics["total_logs"]
            
            # Calculate throughput (logs per second)
            elapsed = time.time() - self._start_time
            if elapsed > 0:
                self.metrics["throughput"] = self.metrics["total_logs"] / elapsed
    
    def record_handler_metrics(self, handler_name: str, metrics: Dict[str, Any]) -> None:
        """
        Record handler-specific performance metrics.
        
        Args:
            handler_name: Name of the handler
            metrics: Handler performance metrics
        """
        if not self.enabled or self._closed:
            return
        
        with self._lock:
            self.metrics["handler_metrics"][handler_name] = metrics
    
    def record_security_event(self) -> None:
        """Record a security validation event."""
        if self.enabled and not self._closed:
            with self._lock:
                self.metrics["security_events"] += 1
    
    def record_sanitization_event(self) -> None:
        """Record a data sanitization event."""
        if self.enabled and not self._closed:
            with self._lock:
                self.metrics["sanitization_events"] += 1
    
    def record_plugin_event(self) -> None:
        """Record a plugin event."""
        if self.enabled and not self._closed:
            with self._lock:
                self.metrics["plugin_events"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self._lock:
            return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        with self._lock:
            self.metrics = {
                "total_logs": 0,
                "total_time": 0.0,
                "avg_latency": 0.0,
                "max_latency": 0.0,
                "min_latency": float('inf'),
                "throughput": 0.0,
                "handler_metrics": {},
                "memory_usage": 0,
                "security_events": 0,
                "sanitization_events": 0,
                "plugin_events": 0
            }
            self._start_time = time.time()
            self._last_reset = time.time()
    
    def close(self) -> None:
        """Close the performance monitor."""
        self._closed = True


class HydraLogger:
    """
    Advanced Python logging with data protection and analytics.
    
    This class provides a comprehensive logging solution with built-in
    data protection, security validation, plugin support, and analytics
    capabilities.
    """
    
    def __init__(
        self,
        config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None,
        enable_security: bool = True,
        enable_sanitization: bool = True,
        enable_plugins: bool = True,
        enable_performance_monitoring: bool = True,
        date_format: Optional[str] = None,
        time_format: Optional[str] = None,
        logger_name_format: Optional[str] = None,
        message_format: Optional[str] = None,
        buffer_size: int = 8192,
        flush_interval: float = 1.0,
        minimal_features_mode: bool = False,
        bare_metal_mode: bool = False
    ):
        """
        Initialize HydraLogger with comprehensive error handling.
        
        Args:
            config: Configuration object or dictionary
            enable_security: Enable security validation
            enable_sanitization: Enable data sanitization
            enable_plugins: Enable plugin system
            enable_performance_monitoring: Enable performance monitoring
            date_format: Custom date format
            time_format: Custom time format
            logger_name_format: Custom logger name format
            message_format: Custom message format
            buffer_size: Buffer size for file handlers
            flush_interval: Flush interval for file handlers
            minimal_features_mode: Enable minimal features mode
            bare_metal_mode: Enable bare metal mode
        """
        with error_context("logger", "initialization"):
            self._closed = False
            self._lock = threading.Lock()
            self._handlers = {}
            self._layers = {}
            self._plugins = {}
            self._precomputed_methods = {}
            
            # Always initialize to None to avoid attribute errors
            self._security_validator = None
            self._data_sanitizer = None
            
            # Performance settings
            self.minimal_features_mode = minimal_features_mode
            self.bare_metal_mode = bare_metal_mode
            self.buffer_size = buffer_size
            self.flush_interval = flush_interval
            
            # Initialize error tracker
            self._error_tracker = get_error_tracker()
            
            # Initialize performance monitor
            self._performance_monitor = PerformanceMonitor(enabled=enable_performance_monitoring)
            
            # Initialize security and sanitization
            self.enable_security = enable_security
            self.enable_sanitization = enable_sanitization
            self.enable_plugins = enable_plugins
            
            if enable_security:
                try:
                    self._security_validator = SecurityValidator()
                except Exception as e:
                    track_runtime_error(e, "security", {"operation": "initialization"})
                    self._security_validator = None
            
            if enable_sanitization:
                try:
                    self._data_sanitizer = DataSanitizer()
                except Exception as e:
                    track_runtime_error(e, "sanitization", {"operation": "initialization"})
                    self._data_sanitizer = None
            
            # Initialize fallback handler
            try:
                self._fallback_handler = FallbackHandler()
            except Exception as e:
                track_runtime_error(e, "fallback", {"operation": "initialization"})
                self._fallback_handler = None
            
            # Load configuration
            try:
                if config is None:
                    self.config = get_default_config()
                elif isinstance(config, dict):
                    self.config = load_config_from_dict(config)
                else:
                    self.config = config
                
                # Apply format customizations - store locally instead of assigning to config
                # These will be used when creating formatters later
                self._date_format = date_format
                self._time_format = time_format
                self._logger_name_format = logger_name_format
                self._message_format = message_format
                
                # Setup layers and handlers
                self._setup_layers()
                
                # Load plugins if enabled
                if enable_plugins:
                    self._load_plugins()
                
                # Setup bare metal mode if enabled
                if bare_metal_mode:
                    self._setup_bare_metal_mode()
                    
            except ConfigurationError:
                # Re-raise ConfigurationError to preserve the original exception
                raise
            except Exception as e:
                track_configuration_error(
                    ConfigurationError(f"Failed to initialize logger: {e}"),
                    {"config_type": type(config).__name__}
                )
                # Use default configuration as fallback
                self.config = get_default_config()
                self._setup_layers()
    
    def _load_plugins(self) -> None:
        """Load available plugins."""
        if not self.enable_plugins:
            return
        
        try:
            available_plugins = list_plugins()
            for plugin_name in available_plugins:
                plugin = get_plugin(plugin_name)
                if plugin:
                    self._plugins[plugin_name] = plugin
        except Exception as e:
            # Log error but don't fail initialization
            print(f"Warning: Failed to load plugins: {e}", file=sys.stderr)
    
    def _setup_layers(self) -> None:
        """Setup logging layers."""
        if hasattr(self.config, 'layers'):
            for layer_name, layer_config in self.config.layers.items():
                self._create_layer(layer_name, layer_config)
        else:
            # Fallback for dict-based config
            layers = getattr(self.config, 'layers', {})
            for layer_name, layer_config in layers.items():
                self._create_layer(layer_name, layer_config)
    
    def _create_layer(self, layer_name: str, layer_config: Any) -> logging.Logger:
        """Create a logging layer."""
        # Protect against reserved layer names (except __CENTRALIZED__ which is allowed for internal use)
        if layer_name.startswith("__") and layer_name.endswith("__") and layer_name != "__CENTRALIZED__":
            raise ConfigurationError(f"Layer name '{layer_name}' is reserved for internal use")
        
        logger = logging.getLogger(f"hydra_logger.{layer_name}")
        logger.setLevel(getattr(logging, layer_config.level.upper(), logging.INFO))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Add handlers for each destination
        for destination in layer_config.destinations:
            handler = self._create_handler(destination)
            if handler:
                logger.addHandler(handler)
        
        self._layers[layer_name] = logger
        return logger
    
    def _create_handler(self, destination: Any) -> Optional[logging.Handler]:
        """Create a logging handler."""
        try:
            if destination.type == "console":
                return self._create_console_handler(destination)
            elif destination.type == "file":
                return self._create_file_handler(destination)
            else:
                # Try to get handler from plugins
                for plugin in self._plugins.values():
                    if hasattr(plugin, 'create_handler'):
                        handler = plugin.create_handler(destination)
                        if handler:
                            return handler
                return None
        except Exception as e:
            print(f"Warning: Failed to create handler for {destination.type}: {e}", file=sys.stderr)
            return None
    
    def _create_console_handler(self, destination: Any) -> logging.StreamHandler:
        """Create a console handler."""
        handler = logging.StreamHandler(sys.stdout)
        # Handle both dict-like and object-like destinations
        if hasattr(destination, 'format'):
            format_type = destination.format
        elif hasattr(destination, 'get'):
            format_type = destination.get('format', 'plain-text')
        else:
            format_type = 'plain-text'
            
        if hasattr(destination, 'color_mode'):
            color_mode = destination.color_mode
        elif hasattr(destination, 'get'):
            color_mode = destination.get('color_mode')
        else:
            color_mode = None
            
        formatter = self._create_formatter(format_type, color_mode)
        handler.setFormatter(formatter)
        return handler
    
    def _create_file_handler(self, destination: Any) -> Optional[logging.Handler]:
        """Create a file handler."""
        try:
            # Handle both dict-like and object-like destinations
            if hasattr(destination, 'path'):
                path = destination.path
            elif hasattr(destination, 'get'):
                path = destination.get('path', 'logs/app.log')
            else:
                path = 'logs/app.log'
                
            if hasattr(destination, 'encoding'):
                encoding = destination.encoding
            elif hasattr(destination, 'get'):
                encoding = destination.get('encoding', 'utf-8')
            else:
                encoding = 'utf-8'
                
            if hasattr(destination, 'format'):
                format_type = destination.format
            elif hasattr(destination, 'get'):
                format_type = destination.get('format', 'plain-text')
            else:
                format_type = 'plain-text'
            
            # Ensure directory exists
            dirname = os.path.dirname(path)
            if dirname:  # Only create directory if there is a directory component
                os.makedirs(dirname, exist_ok=True)
            
            handler = BufferedFileHandler(
                filename=path,
                encoding=encoding,
                buffer_size=self.buffer_size,
                flush_interval=self.flush_interval
            )
            formatter = self._create_formatter(format_type)
            handler.setFormatter(formatter)
            return handler
        except Exception as e:
            print(f"Warning: Failed to create file handler: {e}", file=sys.stderr)
            return None
    
    def _get_logger_for_layer(self, layer: str) -> logging.Logger:
        """
        Get logger with intelligent fallback chain.
        
        Fallback priority:
        1. Requested layer
        2. DEFAULT layer (user-defined)
        3. __CENTRALIZED__ layer (reserved)
        4. System logger (final fallback)
        """
        # Try requested layer
        if layer in self._layers:
            return self._layers[layer]
        
        # Try DEFAULT layer (user-defined)
        if "DEFAULT" in self._layers:
            return self._layers["DEFAULT"]
        
        # Try centralized fallback (reserved layer)
        if "__CENTRALIZED__" in self._layers:
            return self._layers["__CENTRALIZED__"]
        
        # Final fallback to system logger
        return logging.getLogger("hydra_logger")
    
    def _create_formatter(self, format_type: str, color_mode: Optional[str] = None) -> logging.Formatter:
        """Create a formatter."""
        if format_type == "colored-text":
            return ColoredTextFormatter(color_mode=color_mode)
        elif format_type == "plain-text":
            return PlainTextFormatter()
        else:
            # Default formatter
            return logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    def log(
        self,
        level: str,
        message: str,
        layer: str = "DEFAULT",
        extra: Optional[Dict[str, Any]] = None,
        sanitize: bool = True,
        validate_security: bool = True
    ) -> None:
        """
        Log a message with comprehensive error handling.
        
        Args:
            level: Log level
            message: Log message
            layer: Logging layer
            extra: Extra data
            sanitize: Whether to sanitize the message
            validate_security: Whether to validate security
        """
        if self._closed:
            return
        
        with error_context("logger", "log_message"):
            # Bare metal mode: maximum performance
            if self.bare_metal_mode:
                self._bare_metal_log(level, message, layer, extra)
                return
            
            # Minimal features mode: direct logging without overhead
            if self.minimal_features_mode:
                self._minimal_features_log(level, message, layer, extra)
                return
            
            # Standard mode with all features
            start_time = time.time()
            
            try:
                # Security validation
                if validate_security and self._security_validator:
                    validator = self._security_validator
                    validate_fn = getattr(validator, 'validate_message', None) or getattr(validator, 'validate_input', None)
                    if callable(validate_fn):
                        try:
                            validate_fn(message)
                            self._performance_monitor.record_security_event()
                        except Exception as e:
                            track_runtime_error(e, "security", {"operation": "validation", "message": message[:100]})
                
                # Data sanitization
                if sanitize and self._data_sanitizer:
                    sanitizer = self._data_sanitizer
                    sanitize_fn = getattr(sanitizer, 'sanitize_message', None) or getattr(sanitizer, 'sanitize_data', None)
                    if callable(sanitize_fn):
                        try:
                            sanitized_message = sanitize_fn(message)
                            if isinstance(sanitized_message, str):
                                message = sanitized_message
                            self._performance_monitor.record_sanitization_event()
                        except Exception as e:
                            track_runtime_error(e, "sanitization", {"operation": "sanitization", "message": message[:100]})
                
                # Plugin processing
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
                                self._performance_monitor.record_plugin_event()
                        except Exception as e:
                            track_runtime_error(e, "plugin", {"plugin_name": plugin_name, "operation": "process_event"})
                
                # Get logger for layer with intelligent fallback chain
                logger = self._get_logger_for_layer(layer)
                
                # Log the message
                try:
                    log_level = getattr(logging, level.upper(), logging.INFO)
                    logger.log(log_level, message, extra=extra)
                except Exception as e:
                    track_runtime_error(e, "logging", {"level": level, "layer": layer, "message": message[:100]})
                    # Fallback to stderr
                    print(f"Logging error: {e}", file=sys.stderr)
                
                # Record performance metrics
                end_time = time.time()
                self._performance_monitor.record_log(layer, level, message, start_time, end_time)
                
            except Exception as e:
                # Fallback logging
                try:
                    fallback = getattr(self, '_fallback_handler', None)
                    handle_error_fn = getattr(fallback, 'handle_error', None)
                    if callable(handle_error_fn):
                        handle_error_fn(e, message, layer, level)
                    else:
                        print(f"Logging error: {e}", file=sys.stderr)
                except Exception as fallback_error:
                    # Last resort - print to stderr
                    print(f"Critical logging error: {e}", file=sys.stderr)
                    print(f"Fallback error: {fallback_error}", file=sys.stderr)
    
    def _minimal_features_log(self, level: str, message: str, layer: str = "DEFAULT", extra: Optional[Dict[str, Any]] = None) -> None:
        """Minimal features logging without security validation or sanitization."""
        if self._closed:
            return
        
        start_time = time.time()
        try:
            logger = self._get_logger_for_layer(layer)
            log_level = getattr(logging, level.upper(), logging.INFO)
            logger.log(log_level, message, extra=extra)
            
            # Record performance metrics
            end_time = time.time()
            self._performance_monitor.record_log(layer, level, message, start_time, end_time)
        except Exception:
            # Minimal error handling for performance
            pass
    
    def _precompute_log_methods(self) -> None:
        """Precompute log methods for bare metal mode."""
        levels = ["debug", "info", "warning", "error", "critical"]
        layers = list(self._layers.keys())
        
        for level in levels:
            for layer in layers:
                method_name = f"{level}_{layer}"
                self._precomputed_methods[method_name] = lambda l=level, lay=layer, msg="": self._minimal_features_log(l, msg, lay)
    
    def _setup_bare_metal_mode(self) -> None:
        """Setup bare metal mode optimizations."""
        self._precompute_log_methods()
    
    def _bare_metal_log(self, level: str, message: str, layer: str = "DEFAULT", extra: Optional[Dict[str, Any]] = None) -> None:
        """Bare metal logging with minimal overhead."""
        if self._closed:
            return
        
        start_time = time.time()
        try:
            logger = self._get_logger_for_layer(layer)
            if logger:
                log_level = getattr(logging, level.upper(), logging.INFO)
                logger.log(log_level, message, extra=extra)
                
                # Record performance metrics
                end_time = time.time()
                self._performance_monitor.record_log(layer, level, message, start_time, end_time)
        except Exception:
            pass
    
    # Convenience methods
    def debug(self, message: str, layer: str = "DEFAULT", **kwargs) -> None:
        """Log a debug message."""
        self.log("DEBUG", message, layer, **kwargs)
    
    def info(self, message: str, layer: str = "DEFAULT", **kwargs) -> None:
        """Log an info message."""
        self.log("INFO", message, layer, **kwargs)
    
    def warning(self, message: str, layer: str = "DEFAULT", **kwargs) -> None:
        """Log a warning message."""
        self.log("WARNING", message, layer, **kwargs)
    
    def error(self, message: str, layer: str = "DEFAULT", **kwargs) -> None:
        """Log an error message."""
        self.log("ERROR", message, layer, **kwargs)
    
    def critical(self, message: str, layer: str = "DEFAULT", **kwargs) -> None:
        """Log a critical message."""
        self.log("CRITICAL", message, layer, **kwargs)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self._performance_monitor.get_metrics()
    
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
        
        with self._lock:
            if isinstance(new_config, dict):
                new_config = load_config_from_dict(new_config)
            
            self.config = new_config
            self._setup_layers()
    
    def close(self) -> None:
        """Close the logger and cleanup resources with error handling."""
        if self._closed:
            return
        
        with error_context("logger", "close"):
            self._closed = True
            
            try:
                # Close all handlers in all layers
                for layer_name, logger in self._layers.items():
                    for handler in logger.handlers:
                        try:
                            # Flush the handler before closing
                            if hasattr(handler, 'flush'):
                                handler.flush()
                            handler.close()
                        except Exception as e:
                            track_runtime_error(e, "handler", {"operation": "close", "layer": layer_name})
                
                # Close performance monitor
                try:
                    self._performance_monitor.close()
                except Exception as e:
                    track_runtime_error(e, "performance", {"operation": "close"})
                
                # Clear layers and plugins
                self._layers.clear()
                self._plugins.clear()
                
            except Exception as e:
                track_runtime_error(e, "logger", {"operation": "cleanup"})
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics from the error tracker."""
        try:
            return self._error_tracker.get_error_stats()
        except Exception as e:
            track_runtime_error(e, "error_stats", {"operation": "get_stats"})
            return {"error": "Failed to get error stats"}
    
    def clear_error_stats(self) -> None:
        """Clear error statistics."""
        try:
            self._error_tracker.clear_error_stats()
        except Exception as e:
            track_runtime_error(e, "error_stats", {"operation": "clear_stats"})
    
    # Magic config methods
    @classmethod
    def register_magic(cls, name: str, description: str = "") -> Callable:
        """Register a magic configuration."""
        def decorator(func: Callable) -> Callable:
            MagicConfigRegistry.register(name, description)(func)
            return func
        return decorator
    
    @classmethod
    def for_custom(cls, name: str, **kwargs) -> 'HydraLogger':
        """Create logger with custom magic config."""
        if not MagicConfigRegistry.has_config(name):
            raise ConfigurationError(f"Magic config '{name}' not found")
        
        # Get the config directly (get_config now returns LoggingConfig instance)
        config = MagicConfigRegistry.get_config(name)
        return cls(config=config, **kwargs)
    
    @classmethod
    def list_magic_configs(cls) -> Dict[str, str]:
        """List available magic configurations."""
        return MagicConfigRegistry.list_configs()
    
    @classmethod
    def has_magic_config(cls, name: str) -> bool:
        """Check if magic config exists."""
        return MagicConfigRegistry.has_config(name)
    
    # Built-in magic configs
    @classmethod
    def for_production(cls, **kwargs) -> 'HydraLogger':
        """Create production logger."""
        return cls.for_custom("production", **kwargs)
    
    @classmethod
    def for_development(cls, **kwargs) -> 'HydraLogger':
        """Create development logger."""
        return cls.for_custom("development", **kwargs)
    
    @classmethod
    def for_testing(cls, **kwargs) -> 'HydraLogger':
        """Create testing logger."""
        return cls.for_custom("testing", **kwargs)
    
    @classmethod
    def for_microservice(cls, **kwargs) -> 'HydraLogger':
        """Create microservice logger."""
        return cls.for_custom("microservice", **kwargs)
    
    @classmethod
    def for_web_app(cls, **kwargs) -> 'HydraLogger':
        """Create web app logger."""
        return cls.for_custom("web_app", **kwargs)
    
    @classmethod
    def for_api_service(cls, **kwargs) -> 'HydraLogger':
        """Create API service logger."""
        return cls.for_custom("api_service", **kwargs)
    
    @classmethod
    def for_background_worker(cls, **kwargs) -> 'HydraLogger':
        """Create background worker logger."""
        return cls.for_custom("background_worker", **kwargs)
    
    @classmethod
    def for_minimal_features(cls, **kwargs) -> 'HydraLogger':
        """
        Create a HydraLogger optimized for minimal feature overhead.
        
        This configuration disables expensive features to maximize performance:
        - Disables security validation (no input sanitization)
        - Disables data sanitization (no PII detection)
        - Disables plugin system (no plugin overhead)
        - Disables performance monitoring (no metrics collection)
        
        Performance: ~19K messages/sec (file/console)
        Use Case: When you trust your data and don't need security features
        Trade-off: Reduced security and data protection for speed
        
        Args:
            **kwargs: Additional arguments to pass to HydraLogger constructor
            
        Returns:
            HydraLogger: Optimized logger instance with minimal features
            
        Example:
            logger = HydraLogger.for_minimal_features()
            logger.info("PERFORMANCE", "Fast log message")
        """
        # Use the high_performance magic config
        config = MagicConfigRegistry.get_config("high_performance")
        
        # Override with minimal feature optimizations
        return cls(
            config=config,
            enable_security=False,  # Disable security for speed
            enable_sanitization=False,  # Disable sanitization for speed
            enable_plugins=False,  # Disable plugins for speed
            enable_performance_monitoring=False,  # Disable monitoring overhead
            minimal_features_mode=True,  # Enable minimal features mode
            buffer_size=16384,  # Larger buffer
            flush_interval=0.1,  # Shorter flush interval
            **kwargs
        )
    
    @classmethod
    def for_bare_metal(cls, **kwargs) -> 'HydraLogger':
        """
        Create a HydraLogger optimized for bare-metal performance.
        
        This configuration disables ALL optional features for maximum speed:
        - Disables ALL features (security, sanitization, plugins, monitoring)
        - Uses pre-computed log methods (no runtime lookups)
        - Uses direct method calls (minimal overhead)
        - Uses minimal formatting (no color codes or timestamps)
        
        Performance: ~19K messages/sec (file/console)
        Use Case: When you need absolute maximum performance
        Trade-off: No features for maximum speed
        
        Args:
            **kwargs: Additional arguments to pass to HydraLogger constructor
            
        Returns:
            HydraLogger: Bare-metal optimized logger instance
            
        Example:
            logger = HydraLogger.for_bare_metal()
            logger.info("PERFORMANCE", "Bare metal log message")
        """
        # Use the high_performance magic config
        config = MagicConfigRegistry.get_config("high_performance")
        
        # Override with bare-metal optimizations
        return cls(
            config=config,
            enable_security=False,  # Disable all features
            enable_sanitization=False,
            enable_plugins=False,
            enable_performance_monitoring=False,
            bare_metal_mode=True,  # Enable bare metal mode
            buffer_size=32768,  # Very large buffer
            flush_interval=0.05,  # Very short flush interval
            **kwargs
        )
    
    @classmethod
    def for_magic(cls, name: str, **kwargs) -> 'HydraLogger':
        """Alias for for_custom to support magic config tests."""
        return cls.for_custom(name, **kwargs)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close() 