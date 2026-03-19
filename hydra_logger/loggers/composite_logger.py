"""
Role: Implements hydra_logger.loggers.composite_logger functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - asyncio
 - hydra_logger
 - pathlib
 - typing
Notes:
 - Implements logger orchestration and routing for composite logger.
"""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
# pyright: reportCallIssue=false, reportArgumentType=false

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from ..config.models import LogDestination, LoggingConfig, LogLayer
from ..core.exceptions import HydraLoggerError
from ..handlers.base_handler import BaseHandler
from ..types.records import LogRecordFactory
from ..utils import internal_diagnostics, slo_metrics
from ..utils.time_utility import TimeUtility
from .base import BaseLogger
from .pipeline import ComponentDispatcher

_logger = logging.getLogger(__name__)


class CompositeLogger(BaseLogger):
    """
    Composite logger for complex scenarios.

    Features:
    - Multiple logger components
    - Unified interface for all components
    - Component-level configuration
    - Aggregate health monitoring
    - Coordinated shutdown
    """

    def __init__(
        self,
        config: Optional[LoggingConfig] = None,
        name: str = "CompositeLogger",
        components: Optional[List[BaseLogger]] = None,
        **kwargs,
    ):
        """Initialize the composite logger."""
        super().__init__(config=config, name=name, **kwargs)

        self.name = name
        self.components = components or []
        self._component_dispatcher = ComponentDispatcher()
        self._initialized = False
        self._closed = False
        self._batch_dispatch_errors = 0

        # FIX: Setup configuration and handlers if config provided
        if config:
            self._setup_from_config(config)

        # Initialize components
        self._initialize_components()

        # Mark as initialized
        self._initialized = True

    def _setup_from_config(self, config: Union[LoggingConfig, Dict[str, Any]]):
        """Setup logger from configuration."""
        if isinstance(config, dict):
            self._config = LoggingConfig(**config)
        else:
            self._config = config

        # Setup layers and handlers
        self._setup_layers()

    def _setup_layers(self):
        """Setup logging layers and handlers."""
        if not self._config:
            return

        for layer_name, layer in self._config.layers.items():
            # For CompositeLogger, we create individual loggers for each layer's destinations
            # and add them as components.
            for destination in layer.destinations:
                handler = self._create_handler_from_destination(destination)
                if handler:
                    # Create a simple logger for this handler and add it as a component
                    from ..loggers.sync_logger import SyncLogger

                    layer_logger = SyncLogger(
                        config=LoggingConfig(
                            layers={layer_name: LogLayer(destinations=[destination])}
                        )
                    )
                    self.add_component(layer_logger)

    def _create_handler_from_destination(
        self, destination: LogDestination
    ) -> BaseHandler:
        """Create handler from destination configuration."""
        # This method is primarily for internal use by _setup_layers
        # For CompositeLogger, we're creating sub-loggers, so this might be simplified
        # or delegate to the sub-logger's handler creation.
        # For now, let's return a NullHandler as the actual handlers are managed
        # by sub-loggers.
        from ..handlers.null_handler import NullHandler

        return NullHandler()

    def _initialize_components(self):
        """Initialize all component loggers."""
        for component in self.components:
            if hasattr(component, "initialize") and callable(component.initialize):
                try:
                    component.initialize()
                except Exception:
                    # Continue with other components if one fails
                    pass

    def add_component(self, component: BaseLogger) -> None:
        """Add a new component logger."""
        if component not in self.components:
            self.components.append(component)

            # Initialize the new component
            if hasattr(component, "initialize") and callable(component.initialize):
                try:
                    component.initialize()
                except Exception:
                    pass

    def remove_component(self, component: BaseLogger) -> None:
        """Remove a component logger."""
        if component in self.components:
            # Close the component
            if hasattr(component, "close") and callable(component.close):
                try:
                    component.close()
                except Exception:
                    pass

            self.components.remove(component)

    def get_component(self, name: str) -> Optional[BaseLogger]:
        """Get a component by name."""
        for component in self.components:
            if hasattr(component, "name") and component.name == name:
                return component
        return None

    def log(self, level: Union[str, int], message: str, **kwargs) -> None:
        """Log a message to all components."""
        if not self._initialized:
            raise HydraLoggerError("Logger not initialized")

        if self._closed:
            raise HydraLoggerError("Logger is closed")

        self._component_dispatcher.dispatch_sync(
            self.components, level, message, **kwargs
        )

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message to all components."""
        for component in self.components:
            try:
                if hasattr(component, "debug"):
                    component.debug(message, **kwargs)
            except Exception:
                pass

    def info(self, message: str, **kwargs) -> None:
        """Log an info message to all components."""
        for component in self.components:
            try:
                if hasattr(component, "info"):
                    component.info(message, **kwargs)
            except Exception:
                pass

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message to all components."""
        for component in self.components:
            try:
                if hasattr(component, "warning"):
                    component.warning(message, **kwargs)
            except Exception:
                pass

    def error(self, message: str, **kwargs) -> None:
        """Log an error message to all components."""
        for component in self.components:
            try:
                if hasattr(component, "error"):
                    component.error(message, **kwargs)
            except Exception:
                pass

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message to all components."""
        for component in self.components:
            try:
                if hasattr(component, "critical"):
                    component.critical(message, **kwargs)
            except Exception:
                pass

    def close(self):
        """Close all component loggers."""
        if self._closed:
            return

        try:
            # Close all components
            for component in self.components:
                try:
                    if hasattr(component, "close") and callable(component.close):
                        component.close()
                except Exception:
                    pass

            # Clear components
            self.components.clear()

            # Mark as closed
            self._closed = True

        except Exception:
            pass

    def get_health_status(self) -> Dict[str, Any]:
        """Get aggregate health status of all components."""
        if not self.components:
            return {
                "initialized": self._initialized,
                "closed": self._closed,
                "component_count": 0,
                "overall_health": "unknown",
            }

        # Collect health status from all components
        component_health = []
        overall_health = "healthy"

        for component in self.components:
            try:
                if hasattr(component, "get_health_status"):
                    health = component.get_health_status()
                    component_health.append(
                        {
                            "name": getattr(component, "name", "unknown"),
                            "health": health,
                        }
                    )

                    # Check if any component is unhealthy
                    if health.get("health", "unknown") == "unhealthy":
                        overall_health = "unhealthy"
                else:
                    component_health.append(
                        {
                            "name": getattr(component, "name", "unknown"),
                            "health": "unknown",
                        }
                    )
            except Exception:
                component_health.append(
                    {"name": getattr(component, "name", "unknown"), "health": "error"}
                )
                overall_health = "unhealthy"

        return {
            "initialized": self._initialized,
            "closed": self._closed,
            "component_count": len(self.components),
            "overall_health": overall_health,
            "components": component_health,
            "batch_dispatch_errors": self._batch_dispatch_errors,
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def log_batch(
        self, messages: List[Tuple[Union[str, int], str, Dict[str, Any]]]
    ) -> None:
        """Batch logging method with resilient dispatch semantics."""
        if not self._initialized or self._closed or not messages:
            return

        def _to_records() -> List[Any]:
            records: List[Any] = []
            for level, message, kwargs in messages:
                payload = kwargs or {}
                records.append(
                    LogRecordFactory.create_minimal(
                        level_name=str(level),
                        message=message,
                        layer=payload.get("layer", "default"),
                        level=int(level) if isinstance(level, int) else 20,
                        extra=payload.get("extra", {}),
                    )
                )
            return records

        records_cache: Optional[List[Any]] = None
        for component in self.components:
            if hasattr(component, "log"):
                for level, message, kwargs in messages:
                    try:
                        component.log(level, message, **(kwargs or {}))
                    except Exception:
                        self._batch_dispatch_errors += 1
                        _logger.exception(
                            "Composite batch dispatch failed in component log for type=%s",
                            type(component).__name__,
                        )
                        break
                continue

            if hasattr(component, "log_batch"):
                try:
                    if records_cache is None:
                        records_cache = _to_records()
                    component.log_batch(records_cache)
                except Exception:
                    self._batch_dispatch_errors += 1
                    _logger.exception(
                        "Composite batch dispatch failed in component log_batch for type=%s",
                        type(component).__name__,
                    )
                continue

            self._batch_dispatch_errors += 1
            _logger.warning(
                "Composite batch dispatch skipped component without log methods: type=%s",
                type(component).__name__,
            )

        # Update count once for all messages (more efficient)
        self._log_count += len(messages)


class CompositeAsyncLogger(BaseLogger):
    """
    High-performance Async Composite Logger

    Features:
    - Multiple async logger components
    - Unified async interface for all components
    - Component-level configuration
    - Aggregate health monitoring
    - Coordinated async shutdown
    """

    def __init__(
        self,
        config: Optional[LoggingConfig] = None,
        name: str = "CompositeAsyncLogger",
        components: Optional[List[BaseLogger]] = None,
        **kwargs,
    ):
        """Initialize the async composite logger."""
        super().__init__(config=config, name=name, **kwargs)

        self.name = name
        self.components = components or []
        self._component_dispatcher = ComponentDispatcher()
        self._initialized = False
        self._closed = False

        # Performance optimization
        self._log_count = 0
        self._start_time = TimeUtility.perf_counter()

        # Use direct I/O instead of complex handlers
        self._use_direct_io = kwargs.get("use_direct_io", True)
        self._direct_io_buffer = []
        self._buffer_size = 1000000  # Large buffer for high throughput
        self._last_flush = TimeUtility.perf_counter()
        self._flush_interval = 2.0  # Balanced flushing for performance

        # Batch processing for high performance - OPTIMIZED
        self._batch_buffer = []
        self._batch_size = 50000  # Balanced batch size for performance
        self._batch_processing = kwargs.get("batch_processing", True)

        # Formatter support
        self._formatters = {}
        self._default_formatter = kwargs.get("formatter", None)

        # Layer support
        self._layers = {}
        self._default_layer = kwargs.get("layer", "default")

        # Level support
        self._level = kwargs.get("level", "INFO")
        self._level_cache = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
            10: "DEBUG",
            20: "INFO",
            30: "WARNING",
            40: "ERROR",
            50: "CRITICAL",
        }

        # Using LogRecordFactory for optimal LogRecord creation
        # No object pooling needed since LogRecord is immutable

        # Pre-allocated strings for common operations (string interning)
        self._common_strings = {
            "DEFAULT": "default",
            "API": "API",
            "DATABASE": "DATABASE",
            "SYSTEM": "SYSTEM",
            "INFO": "INFO",
            "DEBUG": "DEBUG",
            "WARNING": "WARNING",
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }

        # Pre-computed format strings for speed
        self._format_cache = {}
        self._string_cache = {}

        # Direct formatting templates (no LogRecord needed)
        self._direct_format_templates = {
            "simple": "{timestamp} {level} [{layer}] {message}\n",
            "detailed": "{timestamp} {level} [{layer}] [{file_name}] [{function}] {message}\n",
        }

        # Pre-allocated string builder for performance
        self._string_builder = []
        self._string_builder_size = 0
        self._deferred_async_closes = 0
        self._deferred_async_close_failures = 0
        self._deferred_close_tasks = set()

        # Add default async console handler if no components and not using direct I/O
        if not self.components and not self._use_direct_io:
            from ..handlers.console_handler import AsyncConsoleHandler

            self.components.append(
                AsyncConsoleHandler(buffer_size=10000, flush_interval=0.1)
            )

        # Initialize components
        self._initialize_components()

        # Mark as initialized
        self._initialized = True

    def _initialize_components(self):
        """Initialize all component loggers."""
        for component in self.components:
            if hasattr(component, "initialize") and callable(component.initialize):
                try:
                    component.initialize()
                except Exception:
                    # Continue with other components if one fails
                    pass

    def _get_async_close_callable(self, component):
        """Resolve the best available async close callable for a component."""
        try:
            if hasattr(component, "aclose") and asyncio.iscoroutinefunction(
                component.aclose
            ):
                return component.aclose
            if hasattr(component, "close_async") and asyncio.iscoroutinefunction(
                component.close_async
            ):
                return component.close_async
            if hasattr(component, "close") and asyncio.iscoroutinefunction(
                component.close
            ):
                return component.close
        except Exception:
            return None
        return None

    def _on_deferred_close_done(self, task) -> None:
        """Track completion/errors for deferred async close tasks."""
        self._deferred_close_tasks.discard(task)
        try:
            result = task.result()
            if isinstance(result, Exception):
                self._deferred_async_close_failures += 1
        except Exception:
            self._deferred_async_close_failures += 1

    def _schedule_deferred_async_close(self, component) -> bool:
        """Best-effort scheduling for async close in sync contexts."""
        close_callable = self._get_async_close_callable(component)
        if close_callable is None:
            return False

        self._deferred_async_closes += 1
        try:
            loop = asyncio.get_running_loop()
            if loop.is_closed():
                return True
            task = loop.create_task(close_callable())
            self._deferred_close_tasks.add(task)
            task.add_done_callback(self._on_deferred_close_done)
        except RuntimeError:
            # No active loop: run a short-lived event loop for deterministic cleanup.
            try:
                asyncio.run(close_callable())
            except Exception:
                self._deferred_async_close_failures += 1
        except Exception:
            self._deferred_async_close_failures += 1
        return True

    def add_component(self, component: BaseLogger) -> None:
        """Add a new component logger."""
        if component not in self.components:
            self.components.append(component)

            # Initialize the new component
            if hasattr(component, "initialize") and callable(component.initialize):
                try:
                    component.initialize()
                except Exception:
                    pass

    def remove_component(self, component: BaseLogger) -> None:
        """Remove a component logger."""
        if component in self.components:
            # Close the component
            if self._schedule_deferred_async_close(component):
                self.components.remove(component)
                return
            if hasattr(component, "close") and callable(component.close):
                try:
                    component.close()
                except Exception:
                    pass

            self.components.remove(component)

    def get_component(self, name: str) -> Optional[BaseLogger]:
        """Get a component by name."""
        for component in self.components:
            if hasattr(component, "name") and component.name == name:
                return component
        return None

    # Formatter Management
    def add_formatter(self, name: str, formatter) -> None:
        """Add a formatter to the logger."""
        self._formatters[name] = formatter

    def remove_formatter(self, name: str) -> None:
        """Remove a formatter from the logger."""
        if name in self._formatters:
            del self._formatters[name]

    def get_formatter(self, name: str = None):
        """Get a formatter by name or the default formatter."""
        if name and name in self._formatters:
            return self._formatters[name]
        return self._default_formatter

    def get_formatters(self) -> Dict[str, Any]:
        """Get all formatters."""
        return self._formatters.copy()

    def set_default_formatter(self, formatter) -> None:
        """Set the default formatter."""
        self._default_formatter = formatter

    # Layer Management
    def add_layer(self, name: str, layer_config: Dict[str, Any]) -> None:
        """Add a layer configuration."""
        self._layers[name] = layer_config

    def remove_layer(self, name: str) -> None:
        """Remove a layer configuration."""
        if name in self._layers:
            del self._layers[name]

    def get_layer(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a layer configuration by name."""
        return self._layers.get(name)

    def get_layers(self) -> Dict[str, Dict[str, Any]]:
        """Get all layer configurations."""
        return self._layers.copy()

    def set_default_layer(self, layer: str) -> None:
        """Set the default layer."""
        self._default_layer = layer

    # Level Management
    def set_level(self, level: Union[str, int]) -> None:
        """Set the logger level."""
        if isinstance(level, str):
            self._level = level
        else:
            self._level = self._level_cache.get(level, "INFO")

    def get_level(self) -> str:
        """Get the current logger level."""
        return self._level

    def is_enabled_for(self, level: Union[str, int]) -> bool:
        """Check if logging is enabled for the given level."""
        if isinstance(level, str):
            level_int = self._level_cache.get(level, 20)
        else:
            level_int = level

        current_level_int = self._level_cache.get(self._level, 20)
        return level_int >= current_level_int

    async def log(self, level: Union[str, int], message: str, **kwargs) -> None:
        """Async log method."""
        # Fast path validation - minimal operations
        if not self._initialized or self._closed or not message:
            return

        # Level filtering - cached lookup
        if not self.is_enabled_for(level):
            return

        # Convert level to string once - use cached lookup
        level_str = (
            self._level_cache.get(level, "INFO")
            if isinstance(level, int)
            else str(level)
        )

        # Extract layer - use cached string if possible
        layer = kwargs.get("layer", self._default_layer)
        layer_str = self._common_strings.get(layer, layer)

        # : Use direct I/O for speed
        if self._use_direct_io:
            # Check if formatter is specified
            formatter_name = kwargs.get("formatter")
            if formatter_name and formatter_name in self._formatters:
                # Create LogRecord using factory for optimal performance
                record = LogRecordFactory.create_with_context(
                    level_name=level_str,
                    message=message,
                    layer=layer_str,
                    level=self._level_cache.get(level_str, 20),
                    logger_name=self.name,
                    file_name=kwargs.get("file_name"),
                    function_name=kwargs.get("function_name"),
                    extra=kwargs.get("extra", {}),
                )

                # Format the record
                formatter = self._formatters[formatter_name]
                if hasattr(formatter, "format"):
                    formatted_message = formatter.format(record)
                else:
                    formatted_message = message

                # Emit with pre-formatted message
                await self._direct_io_emit(
                    level_str, formatted_message, pre_formatted=True
                )
            else:
                # Direct string formatting
                await self._direct_string_format(level_str, message, layer_str, kwargs)

            self._log_count += 1
            return

        # Fallback to component-based logging
        if not self.components:
            return

        # Level conversion using LogLevelManager
        from ..types.levels import LogLevelManager

        LogLevelManager.get_level(level)

        # STANDARDIZED: Use standardized LogRecord creation
        record = self.create_log_record(level, message, **kwargs)

        await self._component_dispatcher.dispatch_async(
            self.components, level, message, **kwargs
        )

        # Update statistics
        self._log_count += 1

    async def log_batch(
        self, messages: List[Tuple[Union[str, int], str, Dict[str, Any]]]
    ) -> None:
        """Batch logging method."""
        if not self._initialized or self._closed or not messages:
            return

        # Fast: Process all messages at once for performance
        if self._use_direct_io:
            # Process all messages with direct I/O for speed
            for level, message, kwargs in messages:
                if not self.is_enabled_for(level):
                    continue

                # Convert level to string once
                level_str = (
                    self._level_cache.get(level, "INFO")
                    if isinstance(level, int)
                    else str(level)
                )

                # Extract layer
                layer = kwargs.get("layer", self._default_layer)
                layer_str = self._common_strings.get(layer, layer)

                # Use direct string formatting for speed
                await self._direct_string_format(level_str, message, layer_str, kwargs)
                self._log_count += 1
            return

        # Fallback to component-based processing
        batch_size = min(len(messages), self._batch_size)

        for i in range(0, len(messages), batch_size):
            batch = messages[i : i + batch_size]

            # Process batch with direct string formatting
            for level, message, kwargs in batch:
                if not self.is_enabled_for(level):
                    continue

                # Convert level to string once
                level_str = (
                    self._level_cache.get(level, "INFO")
                    if isinstance(level, int)
                    else str(level)
                )

                # Extract layer
                layer = kwargs.get("layer", self._default_layer)
                layer_str = self._common_strings.get(layer, layer)

                # Use direct string formatting for speed
                await self._direct_string_format(level_str, message, layer_str, kwargs)
                self._log_count += 1

    def _resolve_direct_io_file_path(self) -> Optional[str]:
        """Resolve file path for direct I/O from components or config."""
        for component in self.components:
            if hasattr(component, "file_path") and component.file_path:
                return str(component.file_path)
        config = self._config
        if config is not None and getattr(config, "layers", None):
            for layer in config.layers.values():
                for destination in layer.destinations:
                    if destination.type in {"file", "async_file"} and destination.path:
                        return str(
                            config.resolve_log_path(
                                destination.path, destination.format
                            )
                        )
        return None

    def _write_direct_io_payload(self, file_path: Optional[str], payload: str) -> None:
        """Blocking write of buffered direct I/O payload."""
        if not payload:
            return
        if not file_path:
            return
        try:
            with open(
                file_path,
                "a",
                encoding="utf-8",
                buffering=8388608,
            ) as handle:
                handle.write(payload)
        except Exception as exc:
            internal_diagnostics.warning(
                "CompositeAsyncLogger direct I/O write failed (data dropped): %s",
                exc,
            )
            slo_metrics.record_handler_error("CompositeAsyncLogger.direct_io")

    def _flush_direct_io_sync(self) -> None:
        """Flush direct I/O buffer on the current thread (sync close path)."""
        if not self._direct_io_buffer:
            return
        payload = "".join(self._direct_io_buffer)
        self._direct_io_buffer.clear()
        self._last_flush = TimeUtility.perf_counter()
        file_path = self._resolve_direct_io_file_path()
        self._write_direct_io_payload(file_path, payload)

    def _flush_direct_io(self) -> None:
        """Synchronous flush alias (tests, legacy call sites)."""
        self._flush_direct_io_sync()

    async def _flush_direct_io_async(self) -> None:
        """Flush direct I/O without blocking the event loop when possible."""
        if not self._direct_io_buffer:
            return
        payload = "".join(self._direct_io_buffer)
        self._direct_io_buffer.clear()
        self._last_flush = TimeUtility.perf_counter()
        file_path = self._resolve_direct_io_file_path()

        def _run() -> None:
            self._write_direct_io_payload(file_path, payload)

        started = TimeUtility.perf_counter()
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _run)
        except RuntimeError:
            _run()
        slo_metrics.record_flush_latency(
            "composite_direct_io",
            TimeUtility.perf_counter() - started,
        )

    async def _direct_string_format(
        self, level: str, message: str, layer: str, kwargs: dict
    ) -> None:
        """Direct string formatting."""
        # Fast: Use f-strings for speed (faster than manual building)
        timestamp = TimeUtility.timestamp()

        # Check if we have file_name/function for detailed format
        file_name = kwargs.get("file_name")
        function_name = kwargs.get("function_name")

        if file_name and function_name:
            # Fast: f-string formatting for speed
            formatted_message = f"{timestamp} {level} [{layer}] [{file_name}] [{function_name}] {message}\n"
        else:
            # Fast: f-string formatting for simple format
            formatted_message = f"{timestamp} {level} [{layer}] {message}\n"

        # Add to buffer directly - no intermediate string building
        self._direct_io_buffer.append(formatted_message)

        # Check if we should flush - optimize the condition check
        if len(self._direct_io_buffer) >= self._buffer_size:
            await self._flush_direct_io_async()
        else:
            # Only check time if buffer is not full
            current_time = TimeUtility.perf_counter()
            if (current_time - self._last_flush) >= self._flush_interval:
                await self._flush_direct_io_async()

    async def _direct_io_emit(
        self, level: str, message: str, layer: str = None, pre_formatted: bool = False
    ) -> None:
        """Direct I/O emit method."""
        if pre_formatted:
            # Message is already formatted by a formatter, just add newline
            formatted_message = f"{message}\n"
        else:
            # Format message directly (no complex formatting) - use ISO standard
            # timestamp
            timestamp = (
                TimeUtility.timestamp()
            )  # Use proper Unix timestamp for production logs
            layer_str = layer or self._default_layer
            formatted_message = f"{timestamp} {level} [{layer_str}] {message}\n"

        # Add to buffer
        self._direct_io_buffer.append(formatted_message)

        # Check if we should flush - optimize the condition check
        if len(self._direct_io_buffer) >= self._buffer_size:
            await self._flush_direct_io_async()
        else:
            # Only check time if buffer is not full
            current_time = TimeUtility.perf_counter()
            if (current_time - self._last_flush) >= self._flush_interval:
                await self._flush_direct_io_async()

    async def log_bulk(
        self, level: Union[str, int], messages: List[str], **kwargs
    ) -> None:
        """Bulk logging method."""
        if not self._initialized or self._closed or not messages:
            return

        # : Use direct I/O for speed
        if self._use_direct_io:
            level_str = str(level)
            for message in messages:
                if message is not None:
                    if not isinstance(message, str):
                        message = str(message)
                    await self._direct_io_emit(level_str, message)
            self._log_count += len(messages)
            return

        # Fallback to component-based logging
        if not self.components:
            return

        # Level conversion using LogLevelManager
        from ..types.levels import LogLevelManager

        LogLevelManager.get_level(level)
        level_str = str(level)

        # Fast: Process messages in chunks to avoid memory issues
        chunk_size = 10000  # Process 10K messages at a time
        for i in range(0, len(messages), chunk_size):
            chunk = messages[i : i + chunk_size]

            # Create LogRecords for this chunk

            records = []
            for message in chunk:
                if message is not None:
                    if not isinstance(message, str):
                        message = str(message)
                    # STANDARDIZED: Use standardized LogRecord creation
                    record = self.create_log_record(level_str, message, **kwargs)
                    records.append(record)

            # Fast: Process all components sequentially for this chunk
            for component in self.components:
                try:
                    if hasattr(component, "emit_async"):
                        # Process all records for this component
                        for record in records:
                            await component.emit_async(record)
                    elif hasattr(component, "log") and asyncio.iscoroutinefunction(
                        component.log
                    ):
                        # Process all messages for this component
                        for message in chunk:
                            if message is not None:
                                await component.log(level, message, **kwargs)
                except Exception:
                    pass

            # Update statistics
            self._log_count += len(records)

    async def debug(self, message: str, **kwargs) -> None:
        """Log a debug message to all components."""
        await self.log("DEBUG", message, **kwargs)

    async def info(self, message: str, **kwargs) -> None:
        """Log an info message to all components."""
        await self.log("INFO", message, **kwargs)

    async def warning(self, message: str, **kwargs) -> None:
        """Log a warning message to all components."""
        await self.log("WARNING", message, **kwargs)

    async def error(self, message: str, **kwargs) -> None:
        """Log an error message to all components."""
        await self.log("ERROR", message, **kwargs)

    async def critical(self, message: str, **kwargs) -> None:
        """Log a critical message to all components."""
        await self.log("CRITICAL", message, **kwargs)

    async def _async_close(self):
        """Async close all component loggers."""
        if self._closed:
            return

        try:
            # Mark as closed
            self._closed = True

            # Flush any remaining direct I/O
            if self._use_direct_io:
                await self._flush_direct_io_async()

            # Close all components in parallel
            close_tasks = []
            for component in self.components:
                try:
                    # Try async close methods first
                    close_callable = self._get_async_close_callable(component)
                    if close_callable is not None:
                        close_tasks.append(close_callable())
                    elif hasattr(component, "close") and callable(component.close):
                        close_tasks.append(
                            asyncio.get_event_loop().run_in_executor(
                                None, component.close
                            )
                        )
                except Exception as e:
                    component_name = getattr(component, "name", "unknown")
                    internal_diagnostics.warning(
                        "Error preparing to close component %s: %s",
                        component_name,
                        e,
                    )

            if close_tasks:
                try:
                    results = await asyncio.gather(*close_tasks, return_exceptions=True)
                    error_count = sum(
                        1 for result in results if isinstance(result, Exception)
                    )
                    if error_count > 0:
                        self._deferred_async_close_failures += error_count
                        internal_diagnostics.warning(
                            "%s component(s) failed to close properly",
                            error_count,
                        )
                except Exception as e:
                    internal_diagnostics.warning("Error closing components: %s", e)

            if self._deferred_close_tasks:
                deferred_results = await asyncio.gather(
                    *list(self._deferred_close_tasks), return_exceptions=True
                )
                deferred_errors = sum(
                    1 for result in deferred_results if isinstance(result, Exception)
                )
                if deferred_errors > 0:
                    self._deferred_async_close_failures += deferred_errors
                self._deferred_close_tasks.clear()

            # Clear components
            self.components.clear()

        except Exception as e:
            internal_diagnostics.error("Unexpected error during async close: %s", e)
            # Still mark as closed even if there were errors
            self._closed = True

    def close(self):
        """Synchronous close method for backward compatibility."""
        if self._closed:
            return

        try:
            # Mark as closed
            self._closed = True

            # Flush any remaining direct I/O
            if self._use_direct_io:
                self._flush_direct_io_sync()

            # Close all components synchronously
            for component in self.components:
                try:
                    if self._schedule_deferred_async_close(component):
                        continue
                    if hasattr(component, "close") and callable(component.close):
                        component.close()
                except Exception:
                    pass

            # Clear components
            self.components.clear()

        except Exception:
            # Still mark as closed even if there were errors
            self._closed = True

    async def aclose(self):
        """Async close method for async context manager support."""
        await self._async_close()

    def get_health_status(self) -> Dict[str, Any]:
        """Get aggregate health status of all components."""
        if not self.components:
            return {
                "initialized": self._initialized,
                "closed": self._closed,
                "component_count": 0,
                "overall_health": "unknown",
                "deferred_async_closes": self._deferred_async_closes,
                "deferred_async_close_failures": self._deferred_async_close_failures,
                "pending_deferred_closes": len(self._deferred_close_tasks),
            }

        # Collect health status from all components
        component_health = []
        overall_health = "healthy"

        for component in self.components:
            try:
                if hasattr(component, "get_health_status"):
                    health = component.get_health_status()
                    component_health.append(
                        {
                            "name": getattr(component, "name", "unknown"),
                            "health": health,
                        }
                    )

                    # Check if any component is unhealthy
                    if health.get("health", "unknown") == "unhealthy":
                        overall_health = "unhealthy"
                else:
                    component_health.append(
                        {
                            "name": getattr(component, "name", "unknown"),
                            "health": "unknown",
                        }
                    )
            except Exception:
                component_health.append(
                    {"name": getattr(component, "name", "unknown"), "health": "error"}
                )
                overall_health = "unhealthy"

        return {
            "initialized": self._initialized,
            "closed": self._closed,
            "component_count": len(self.components),
            "overall_health": overall_health,
            "components": component_health,
            "log_count": self._log_count,
            "deferred_async_closes": self._deferred_async_closes,
            "deferred_async_close_failures": self._deferred_async_close_failures,
            "pending_deferred_closes": len(self._deferred_close_tasks),
            "uptime": TimeUtility.perf_counter() - self._start_time,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics including object pool stats."""
        current_time = TimeUtility.perf_counter()
        duration = current_time - self._start_time
        messages_per_second = self._log_count / duration if duration > 0 else 0

        return {
            "name": self.name,
            "initialized": self._initialized,
            "closed": self._closed,
            "log_count": self._log_count,
            "duration": duration,
            "messages_per_second": messages_per_second,
            "buffer_size": len(self._direct_io_buffer),
            "formatters": list(self._formatters.keys()),
            "level": self._level,
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if asyncio.iscoroutinefunction(self.close):
            # Can't await in sync context, just mark as closed
            self._closed = True
        else:
            self.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
