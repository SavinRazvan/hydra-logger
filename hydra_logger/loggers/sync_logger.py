"""
Role: Implements hydra_logger.loggers.sync_logger functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - hydra_logger
 - sys
 - threading
 - typing
Notes:
 - Implements logger orchestration and routing for sync logger.
"""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
# pyright: reportCallIssue=false, reportArgumentType=false

import sys
import threading
from typing import Any, Dict, Literal, Optional, Union, cast

from ..config.models import LogDestination, LoggingConfig
from ..core.exceptions import HydraLoggerError
from ..handlers.base_handler import BaseHandler
from ..handlers.console_handler import SyncConsoleHandler
from ..handlers.null_handler import NullHandler
from ..types.levels import LogLevel, LogLevelManager
from ..types.records import LogRecord
from ..utils import internal_diagnostics as diagnostics
from ..utils.destination_contracts import unsupported_destination_message
from ..utils.reliability_lifecycle import handle_lifecycle_failure
from ..utils.time_utility import TimeUtility
from .base import BaseLogger
from .pipeline import ExtensionProcessor, HandlerDispatcher, LayerRouter, RecordBuilder


class SyncLogger(BaseLogger):
    """Synchronous logger with layer-aware routing and cached handler lookup."""

    def __init__(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None, **kwargs
    ):
        """Initialize the sync logger."""
        super().__init__(config, **kwargs)

        # Initialize core attributes
        self._initialize_attributes()

        # Setup configuration FIRST
        if config:
            self._setup_from_config(config)
        else:
            self._setup_default_configuration()

        # are set)
        self._setup_core_systems()

        # Setup data protection
        self._setup_data_protection()

        # Setup layers and handlers
        self._setup_layers()

        # Setup plugins
        self._setup_plugins()

        # Setup fallback configuration
        self._setup_fallback_configuration()

        # Precompute logging methods
        self._precompute_log_methods()

        # Mark as initialized
        self._initialized = True

    def _initialize_attributes(self):
        """Initialize internal attributes."""
        # Core state
        self._initialized = False
        self._closed = False

        # Configuration
        self._config = None
        self._layers = {}
        self._handlers = {}
        self._layer_handlers = {}

        # Core system integration
        self._security_engine = None

        # Feature components
        self._performance_monitor = None
        self._error_tracker = None
        self._security_validator = None
        self._data_sanitizer = None
        self._fallback_handler = None
        self._plugin_manager = None

        # Feature flags - DISABLED by default for performance
        self._enable_security = False
        self._enable_sanitization = False
        self._enable_plugins = False

        # Object pooling for performance
        # Object pooling removed - using standardized LogRecord creation
        self._enable_data_protection = False

        # Buffer configuration - OPTIMIZED for performance
        self._buffer_size = 50000  # Larger buffer for fewer flushes
        self._flush_interval = 5.0  # Less frequent flushes

        # Magic configuration
        self._magic_registry = {}

        # Threading
        self._lock = threading.RLock()

        # Statistics
        self._log_count = 0
        self._start_time = TimeUtility.timestamp()
        self._swallowed_error_count = 0
        self._strict_reliability_mode = False
        self._reliability_error_policy = "silent"
        self._failure_warning_interval = 100
        self._handler_close_failures = 0
        self._last_lifecycle_error: Optional[str] = None
        self._close_completed = True

        # Formatter cache to ensure consistent instances
        self._formatter_cache = {}

        # Performance optimization: Handler lookup caching
        self._handler_cache = {}
        self._layer_cache = {}

        # Shared hot-path pipeline services
        self._record_builder = RecordBuilder(self)
        self._extension_processor = ExtensionProcessor(self)
        self._layer_router = LayerRouter(
            self._layers, self._layer_handlers, self._handler_cache, self._layer_cache
        )
        self._handler_dispatcher = HandlerDispatcher()

    def _setup_from_config(self, config: Union[LoggingConfig, Dict[str, Any]]):
        """Setup logger from configuration."""
        if isinstance(config, dict):
            self._config = LoggingConfig(**config)
        else:
            self._config = config

        if self._config:
            self._enable_security = self._config.enable_security
            self._enable_sanitization = self._config.enable_sanitization
            self._enable_data_protection = getattr(
                self._config, "enable_data_protection", False
            )
            self._enable_plugins = self._config.enable_plugins
            self._buffer_size = self._config.buffer_size
            self._flush_interval = self._config.flush_interval
            self._strict_reliability_mode = bool(
                getattr(self._config, "strict_reliability_mode", False)
            )
            self._reliability_error_policy = str(
                getattr(self._config, "reliability_error_policy", "silent")
            ).lower()

    def _report_unsupported_destination(self, destination: LogDestination) -> None:
        """Surface unsupported destination types that resolve to a null sink."""
        msg = unsupported_destination_message(destination.type)
        if self._strict_reliability_mode or self._reliability_error_policy == "raise":
            raise HydraLoggerError(msg)
        if self._reliability_error_policy == "warn":
            diagnostics.warning("%s", msg)
        else:
            diagnostics.debug("%s", msg)

    def _handle_internal_failure(self, context: str, error: Exception) -> None:
        """Process internal failure according to configured reliability policy."""
        self._swallowed_error_count += 1
        if self._reliability_error_policy in {"warn", "raise"}:
            if (
                self._swallowed_error_count == 1
                or self._swallowed_error_count % self._failure_warning_interval == 0
            ):
                diagnostics.warning("Sync logger failure [%s]: %s", context, error)

        if self._strict_reliability_mode or self._reliability_error_policy == "raise":
            raise HydraLoggerError(
                f"Sync logger internal failure [{context}]"
            ) from error

    def _increment_handler_close_failures(self) -> None:
        self._handler_close_failures += 1

    def _set_last_lifecycle_error(self, message: str) -> None:
        self._last_lifecycle_error = message

    def _report_lifecycle_failure(self, context: str, error: Exception) -> None:
        handle_lifecycle_failure(
            context=context,
            error=error,
            logger_name=self._name,
            strict_reliability_mode=self._strict_reliability_mode,
            reliability_error_policy=self._reliability_error_policy,
            failure_warning_interval=self._failure_warning_interval,
            increment_close_failures=self._increment_handler_close_failures,
            get_close_failure_count=lambda: self._handler_close_failures,
            set_last_error=self._set_last_lifecycle_error,
        )

    def _setup_default_configuration(self):
        """Setup simplified configuration."""

        from ..handlers.console_handler import SyncConsoleHandler

        self._console_handler = SyncConsoleHandler(
            buffer_size=10000,  # Larger buffer
            flush_interval=1.0,  # Less frequent flushes
        )
        self._handlers = {"console": self._console_handler}

    def _setup_core_systems(self):
        """Setup core system integration."""

        self._security_engine = None

    def _setup_data_protection(self):
        """Setup simple data protection features."""
        self._data_protection = None
        if not self._enable_data_protection:
            return

        mgr = (
            getattr(self._config, "_extension_manager", None)
            if self._config is not None
            else None
        )
        if mgr is not None:
            from ..extensions.extension_base import SecurityExtension

            ext = mgr.get_extension("data_protection")
            if ext is None:
                for candidate in mgr.extensions.values():
                    if isinstance(candidate, SecurityExtension):
                        ext = candidate
                        break
            if isinstance(ext, SecurityExtension):
                self._data_protection = ext
                return

        try:
            from ..extensions.extension_base import SecurityExtension

            # Get extension config from LoggingConfig if available
            patterns = [
                "email",
                "phone",
                "ssn",
                "credit_card",
                "api_key",
                "password",
                "token",
                "secret",
            ]
            if (
                self._config
                and hasattr(self._config, "extensions")
                and self._config.extensions
            ):
                data_protection_config = self._config.extensions.get(
                    "data_protection", {}
                )
                patterns = data_protection_config.get("patterns", patterns)

            # Create simple security extension when no manager instance is available
            self._data_protection = SecurityExtension(enabled=True, patterns=patterns)
        except ImportError:
            self._data_protection = None

    def _setup_layers(self):
        """Setup logging layers and handlers."""
        if not self._config:
            return

        for layer_name, layer in self._config.layers.items():
            self._layers[layer_name] = layer
            self._layer_handlers[layer_name] = []

            # Create handlers for this layer
            for destination in layer.destinations:
                handler = self._create_handler_from_destination(destination)
                if handler:
                    self._layer_handlers[layer_name].append(handler)
                    self._handlers[id(handler)] = handler

    def _create_handler_from_destination(
        self, destination: LogDestination
    ) -> BaseHandler:
        """Create handler from destination configuration."""
        handler: BaseHandler
        if destination.type in ["console", "sync_console", "async_console"]:
            # Use dedicated sync console handler for better performance
            from ..handlers.console_handler import SyncConsoleHandler

            handler = SyncConsoleHandler(
                stream=sys.stdout,
                use_colors=destination.use_colors,  # Use the actual value from destination
            )
            # Set formatter for console
            use_colors = destination.use_colors  # Use the actual value from destination
            formatter = self._create_formatter_for_destination(
                destination, is_console=True, use_colors=use_colors
            )
            handler.setFormatter(formatter)

            # Set handler level if specified
            if destination.level is not None:
                handler.setLevel(LogLevelManager.get_level(destination.level))

        elif destination.type in ["file", "sync_file"]:
            # Use dedicated sync file handler for better performance
            from ..handlers.file_handler import SyncFileHandler

            if self._config is None:
                return NullHandler()

            # Resolve log path using config settings with format-aware extension
            resolved_path = self._config.resolve_log_path(
                destination.path or "", destination.format
            )
            handler = SyncFileHandler(
                filename=resolved_path,
                mode="a",  # Append mode
                encoding="utf-8",
                buffer_size=50000,  # Large buffer for performance
                flush_interval=5.0,  # Less frequent flushes
            )
            # Set formatter for file
            formatter = self._create_formatter_for_destination(
                destination, is_console=False
            )
            handler.setFormatter(formatter)

            # Set handler level if specified
            if destination.level is not None:
                handler.setLevel(LogLevelManager.get_level(destination.level))

        elif destination.type == "null":
            handler = NullHandler()
        elif destination.type in {
            "network_http",
            "network_ws",
            "network_socket",
            "network_datagram",
        }:
            handler = self._create_network_handler_from_destination(destination)
            formatter = self._create_formatter_for_destination(
                destination, is_console=False
            )
            handler.setFormatter(formatter)
            if destination.level is not None:
                handler.setLevel(LogLevelManager.get_level(destination.level))

        else:
            # For now, return null handler for unsupported types
            handler = NullHandler()
            self._report_unsupported_destination(destination)

        return handler

    def _create_network_handler_from_destination(
        self, destination: LogDestination
    ) -> BaseHandler:
        """Create network handler from typed destination configuration."""
        from ..handlers.http_payload_encoders import resolve_http_payload_encoder
        from ..handlers.network_handler import NetworkHandlerFactory

        if destination.type == "network_http":
            encoder = None
            if destination.http_payload_encoder:
                encoder = resolve_http_payload_encoder(destination.http_payload_encoder)
            url = destination.url or ""
            timeout = destination.timeout or 30.0
            headers = destination.credentials or {}
            connection_probe = destination.connection_probe
            probe_method = destination.probe_method
            if destination.http_batch_size and destination.http_batch_size > 0:
                from ..handlers.batched_http_handler import BatchedHTTPHandler

                return BatchedHTTPHandler(
                    url=url,
                    timeout=timeout,
                    headers=headers,
                    connection_probe=connection_probe,
                    probe_method=probe_method,
                    payload_encoder=encoder,
                    batch_size=destination.http_batch_size,
                    flush_interval=destination.http_batch_flush_interval,
                )
            return NetworkHandlerFactory.create_http_handler(
                url=url,
                timeout=timeout,
                headers=headers,
                connection_probe=connection_probe,
                probe_method=probe_method,
                payload_encoder=encoder,
            )
        if destination.type == "network_ws":
            return NetworkHandlerFactory.create_websocket_handler(
                url=destination.url or "",
                use_real_websocket_transport=destination.use_real_websocket_transport,
            )
        if destination.type == "network_socket":
            return NetworkHandlerFactory.create_socket_handler(
                host=destination.host or "localhost",
                port=destination.port or 514,
                protocol="tcp",
            )
        if destination.type == "network_datagram":
            return NetworkHandlerFactory.create_datagram_handler(
                host=destination.host or "localhost",
                port=destination.port or 514,
            )
        raise ValueError(f"Unsupported network destination type: {destination.type}")

    def _create_formatter_for_destination(
        self, destination, is_console: bool = False, use_colors: bool = True
    ):
        """
        Create appropriate formatter for destination type using standardized formatters.

        This method implements the standardized color system:
        - Console handlers with use_colors=True get ColoredFormatter
        - Console handlers with use_colors=False get plain formatter
        - Non-console handlers always get plain formatter (no colors)
        - All formatters are cached for performance

        Args:
            destination: LogDestination configuration
            is_console: Whether this is a console handler
            use_colors: Whether to enable colors (console only)

        Returns:
            Configured formatter instance
        """
        try:
            format_type = getattr(destination, "format", "plain-text")

            # Create cache key for this destination
            cache_key = f"{destination.type}_{format_type}_{is_console}_{use_colors}"

            # Check if we have a cached formatter
            if cache_key in self._formatter_cache:
                return self._formatter_cache[cache_key]

            from ..formatters import get_formatter

            format_mapping = {
                "text": "plain-text",
                "binary-compact": "binary-compact",
                "binary-extended": "binary-extended",
            }

            standardized_format = format_mapping.get(format_type, format_type)

            # 🎨 COLORS: Only console handlers can use colors
            if is_console and use_colors:
                # Colors enabled for console - use colored formatter
                formatter = get_formatter("colored", use_colors=True)
            elif is_console:
                # Console handler but colors disabled - use plain formatter
                formatter = get_formatter(standardized_format, use_colors=False)
            else:
                # Non-console handler - no colors
                formatter = get_formatter(standardized_format, use_colors=False)

            # Cache the formatter
            self._formatter_cache[cache_key] = formatter
            return formatter

        except Exception:
            # Fallback to plain text formatter
            from ..formatters import get_formatter

            return get_formatter("plain-text", use_colors=False)

    def _setup_plugins(self):
        """Setup plugin system."""
        # Plugin system removed - simplified architecture
        self._plugin_manager = None

    def _setup_fallback_configuration(self):
        """Setup emergency fallback configuration."""
        # Ensure we have at least one working handler
        if not self._handlers:
            fallback_handler = SyncConsoleHandler()
            # Set a plain formatter for fallback (no colors to avoid issues)
            from ..formatters import get_formatter

            fallback_handler.setFormatter(get_formatter("plain-text", use_colors=False))
            self._handlers[id(fallback_handler)] = fallback_handler
            self._layer_handlers["default"] = [fallback_handler]

    def _precompute_log_methods(self):
        """Precompute optimized logging methods."""
        # Always use standard logging since performance modes are removed
        self._log_methods = {
            "debug": self._standard_log,
            "info": self._standard_log,
            "warning": self._standard_log,
            "error": self._standard_log,
            "critical": self._standard_log,
        }

    def log(self, level: Union[str, int], message: str, **kwargs) -> None:
        """Log method with minimal overhead."""
        # Fast path checks (minimal overhead)
        if not self._initialized or self._closed:
            return

        try:

            if isinstance(level, str):
                level = self._record_builder.normalize_level(level)

            record = self._record_builder.create(level, message, **kwargs)
            record = self._extension_processor.apply_data_protection(
                record, self._data_protection
            )

            layer_name = kwargs.get("layer", "default")
            if not self._is_level_enabled_for_layer(layer_name, int(level)):
                return

            layer_handlers = self._get_handlers_for_layer(layer_name)
            self._handler_dispatcher.dispatch_sync(record, layer_handlers)

            # Record processing completed

        except Exception as error:
            self._handle_internal_failure("log", error)

    def _emit_to_handlers(self, record: LogRecord):
        """Emit record to appropriate handlers."""
        # Get layer from record or use default (optimized)
        layer = record.layer if hasattr(record, "layer") and record.layer else "default"

        # Get handlers for this layer
        handlers = self._get_handlers_for_layer(layer)

        # Emit to all handlers
        for handler in handlers:
            try:
                handler.emit(record)
            except Exception as error:
                self._handle_internal_failure("emit_to_handlers", error)

    def _get_handlers_for_layer(self, layer_name: str) -> list:
        """Get handlers for a specific layer with caching."""
        return self._layer_router.handlers_for_layer(layer_name)

    def _get_layer_threshold(self, layer_name: str) -> int:
        """Get minimum log level for a layer with caching."""
        default_level = self._config.default_level if self._config else "INFO"
        return self._layer_router.layer_threshold(layer_name, default_level)

    def _is_level_enabled_for_layer(self, layer_name: str, level: int) -> bool:
        """Check if a level is enabled for a specific layer."""
        default_level = self._config.default_level if self._config else "INFO"
        return self._layer_router.is_level_enabled(layer_name, level, default_level)

    def _standard_log(self, level: str, message: str, **kwargs) -> None:
        """Standard logging path with full features."""
        self.log(level, message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        if self._log_methods and "debug" in self._log_methods:
            self._log_methods["debug"]("DEBUG", message, **kwargs)
        else:
            self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        if self._log_methods and "info" in self._log_methods:
            self._log_methods["info"]("INFO", message, **kwargs)
        else:
            self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        if self._log_methods and "warning" in self._log_methods:
            self._log_methods["warning"]("WARNING", message, **kwargs)
        else:
            self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        if self._log_methods and "error" in self._log_methods:
            self._log_methods["error"]("ERROR", message, **kwargs)
        else:
            self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        if self._log_methods and "critical" in self._log_methods:
            self._log_methods["critical"]("CRITICAL", message, **kwargs)
        else:
            self.log(LogLevel.CRITICAL, message, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        """Alias for warning (compatibility)."""
        self.warning(message, **kwargs)

    def fatal(self, message: str, **kwargs) -> None:
        """Alias for critical (compatibility)."""
        self.critical(message, **kwargs)

    def _apply_security_processing(self, record: LogRecord) -> LogRecord:
        """Apply security processing to log record if security engine is available."""
        try:
            if self._security_engine and self._enable_security:
                # Process through security engine
                processed_record = self._security_engine.process_log_record(record)

                # Update security statistics
                if hasattr(self, "_security_stats"):
                    self._security_stats["processed_records"] = (
                        self._security_stats.get("processed_records", 0) + 1
                    )

                return processed_record
            else:
                return record
        except Exception as e:
            # Log security processing error but don't fail the log operation
            diagnostics.warning("Security processing failed: %s", e)
            return record

    def _execute_pre_log_plugins(self, record: LogRecord) -> LogRecord:
        """Execute pre-log plugins to modify the record before processing."""
        # Plugin system removed - simplified architecture
        return record

    def _execute_post_log_plugins(self, record: LogRecord) -> None:
        """Execute post-log plugins after the record has been processed."""
        # Plugin system removed - simplified architecture
        pass

    def close(self):
        """Close the logger and cleanup resources."""
        if self._closed:
            return

        self._close_completed = False
        try:
            # Close all handlers
            for handler in self._handlers.values():
                try:
                    handler.close()
                except Exception as error:
                    self._report_lifecycle_failure(
                        f"handler_close:{type(handler).__name__}", error
                    )

            # Clear collections (legacy: if clear fails, leave logger not closed)
            try:
                self._handlers.clear()
                self._layer_handlers.clear()
                self._layers.clear()
            except Exception as error:
                try:
                    self._report_lifecycle_failure("close_cleanup", error)
                except HydraLoggerError:
                    self._closed = True
                    raise
                return

            # Mark as closed
            self._closed = True
            self._close_completed = True

        except HydraLoggerError:
            if not self._closed:
                self._closed = True
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the logger."""
        health_status: Dict[str, Any] = {
            "initialized": self._initialized,
            "closed": self._closed,
            "log_count": self._log_count,
            "start_time": self._start_time,
            "handler_count": len(self._handlers),
            "layer_count": len(self._layers),
        }

        # Add core system health status
        if self._security_engine:
            health_status["security_engine"] = (
                self._security_engine.get_security_metrics()
            )
        health_status["swallowed_error_count"] = self._swallowed_error_count
        health_status["handler_close_failures"] = self._handler_close_failures
        health_status["close_completed"] = self._close_completed
        if self._last_lifecycle_error is not None:
            health_status["last_lifecycle_error"] = self._last_lifecycle_error

        return health_status

    def update_security_level(self, level: str) -> None:
        """Update security level at runtime."""
        if self._config:
            self._config.update_security_level(
                cast(Literal["low", "medium", "high", "strict"], level)
            )
            diagnostics.info("Security level updated to: %s", level)
        else:
            diagnostics.warning("No configuration available for runtime updates")

    def update_monitoring_config(
        self,
        detail_level: Optional[str] = None,
        sample_rate: Optional[int] = None,
        background: Optional[bool] = None,
    ) -> None:
        """Update monitoring configuration at runtime."""
        if self._config:
            self._config.update_monitoring_config(
                cast(
                    Optional[Literal["basic", "standard", "detailed"]],
                    detail_level,
                ),
                sample_rate,
                background,
            )

            # Update local monitoring settings
            if detail_level:
                diagnostics.info("Monitoring detail level updated to: %s", detail_level)
            if sample_rate is not None:
                diagnostics.info("Monitoring sample rate updated to: %s", sample_rate)
            if background is not None:
                state = "enabled" if background else "disabled"
                diagnostics.info("Monitoring background processing: %s", state)
        else:
            diagnostics.warning("No configuration available for runtime updates")

    def toggle_feature(self, feature: str, enabled: bool) -> None:
        """Toggle a feature on/off at runtime."""
        if self._config:
            self._config.toggle_feature(feature, enabled)

            # Update local feature flags
            if feature == "security":
                self._enable_security = enabled
            elif feature == "sanitization":
                self._enable_sanitization = enabled
            elif feature == "plugins":
                self._enable_plugins = enabled

            diagnostics.info("%s %s", feature, "enabled" if enabled else "disabled")
        else:
            diagnostics.warning("No configuration available for runtime updates")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        if self._config:
            return self._config.get_configuration_summary()
        else:
            return {"status": "no_configuration"}

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get object pool statistics (deprecated - using standardized LogRecord creation)."""
        return {
            "status": "deprecated",
            "message": "Using standardized LogRecord creation",
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
