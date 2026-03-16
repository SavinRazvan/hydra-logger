"""
Role: Implements hydra_logger.loggers.async_logger functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - asyncio
 - hydra_logger
 - psutil
 - sys
 - typing
Notes:
 - Implements logger orchestration and routing for async logger.
"""

# pyright: reportAttributeAccessIssue=false, reportOptionalMemberAccess=false
# pyright: reportCallIssue=false, reportArgumentType=false

import asyncio
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from ..config.models import LogDestination, LoggingConfig
from ..core.exceptions import HydraLoggerError
from ..formatters.base import BaseFormatter
from ..handlers.base_handler import BaseHandler
from ..handlers.null_handler import NullHandler
from ..types.levels import LogLevel, LogLevelManager
from ..types.records import LogRecord
from ..utils import internal_diagnostics as diagnostics
from ..utils.time_utility import TimeUtility
from .base import BaseLogger
from .pipeline import ExtensionProcessor, HandlerDispatcher, LayerRouter, RecordBuilder

class AsyncLogger(BaseLogger):
    """Asynchronous logger with layer routing and handler-based emission."""

    def __init__(
        self, config: Optional[Union[LoggingConfig, Dict[str, Any]]] = None, **kwargs
    ):
        """Initialize the async logger."""
        # Call parent init first
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

        # Setup layers and handlers
        self._setup_layers()

        # Setup plugins
        self._setup_plugins()

        # Setup fallback configuration
        self._setup_fallback_configuration()

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
        self._plugin_manager = None

        # Feature flags - DISABLED by default for performance
        self._enable_security = False
        self._enable_sanitization = False
        self._enable_plugins = False

        # Object pooling removed - using standardized LogRecord creation

        # Async infrastructure
        self._shutdown_event = None
        self._writer_tasks = {}

        self._concurrency_semaphore = None
        self._optimal_concurrency = None
        self._overflow_queue = asyncio.Queue(maxsize=100000)  # Larger overflow queue
        self._overflow_worker_task = None

        # Statistics
        self._log_count = 0
        self._start_time = TimeUtility.timestamp()

        # Formatter cache for performance
        self._formatter_cache = {}

        # Performance optimization: Handler lookup caching
        self._handler_cache = {}
        self._layer_cache = {}

        # Shared hot-path pipeline services
        self._record_builder = RecordBuilder(self)
        self._extension_processor = ExtensionProcessor()
        self._layer_router = LayerRouter(
            self._layers, self._layer_handlers, self._handler_cache, self._layer_cache
        )
        self._handler_dispatcher = HandlerDispatcher()

    def _setup_core_systems(self):
        """Setup core system integration."""

        self._security_engine = None

        # Setup data protection if enabled
        self._setup_data_protection()

        # Plugin system removed - simplified architecture

    def _setup_data_protection(self):
        """Setup simple data protection features."""
        if self._enable_data_protection:
            try:
                from ..extensions.extension_base import SecurityExtension

                # Get extension config from LoggingConfig if available
                patterns = ["email", "phone", "ssn", "credit_card", "api_key"]
                if (
                    self._config
                    and hasattr(self._config, "extensions")
                    and self._config.extensions
                ):
                    data_protection_config = self._config.extensions.get(
                        "data_protection", {}
                    )
                    patterns = data_protection_config.get("patterns", patterns)

                # Create simple security extension
                self._data_protection = SecurityExtension(
                    enabled=True, patterns=patterns
                )
            except ImportError:
                self._data_protection = None
        else:
            self._data_protection = None

    def _setup_plugins(self):
        """Setup plugin system."""
        # Plugin system removed - simplified architecture
        self._plugin_manager = None

    def _get_optimal_concurrency(self) -> int:
        """Get optimal concurrency based on available system memory."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            available_mb = memory.available / 1024 / 1024

            # Dynamic concurrency based on available memory
            if available_mb > 8000:  # 8GB+ available
                concurrency = 500
            elif available_mb > 4000:  # 4GB+ available
                concurrency = 250
            elif available_mb > 2000:  # 2GB+ available
                concurrency = 100
            else:  # <2GB available
                concurrency = 50

            return concurrency

        except ImportError:
            # Fallback if psutil not available
            return 100

    def _ensure_concurrency_semaphore(self):
        """Ensure concurrency semaphore is initialized with overflow handling."""
        if self._concurrency_semaphore is None:
            self._optimal_concurrency = self._get_optimal_concurrency()
            self._concurrency_semaphore = asyncio.Semaphore(self._optimal_concurrency)

            if self._overflow_worker_task is None:
                self._overflow_worker_task = asyncio.create_task(
                    self._overflow_worker()
                )

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

        self._setup_layers()

    def _setup_default_configuration(self):
        """Setup SIMPLIFIED configuration for performance."""

        from ..handlers.console_handler import AsyncConsoleHandler

        self._console_handler = AsyncConsoleHandler(
            buffer_size=10000,  # Larger buffer
            flush_interval=1.0,  # Less frequent flushes
        )
        self._handlers = {"console": self._console_handler}
        self._layer_handlers = {"default": [self._console_handler]}
        self._initialized = True

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
        if destination.type in ["console", "async_console"]:
            # Use dedicated async console handler for better performance
            from ..handlers.console_handler import AsyncConsoleHandler

            handler = AsyncConsoleHandler(
                stream=sys.stdout,
                use_colors=destination.use_colors,  # Use the actual value from destination
                buffer_size=5000,  # Larger buffer for better batching
                flush_interval=0.5,  # Balanced flush interval (throughput vs latency)
            )
            # Set formatter for console
            use_colors = destination.use_colors  # Use the actual value from destination
            formatter = self._create_formatter_for_destination(
                destination, is_console=True, use_colors=use_colors
            )
            handler.setFormatter(formatter)

        elif destination.type in ["file", "async_file"]:
            # Use dedicated async file handler for better performance
            from ..handlers.file_handler import AsyncFileHandler

            # Resolve log path using config settings with format-aware extension
            resolved_path = self._config.resolve_log_path(
                destination.path, destination.format
            )
            handler = AsyncFileHandler(
                filename=resolved_path, mode="a", encoding="utf-8"  # Append mode
            )
            # Set formatter for file
            formatter = self._create_formatter_for_destination(
                destination, is_console=False
            )
            handler.setFormatter(formatter)

            handler._start_worker()

        elif destination.type == "null":
            handler = NullHandler()

        else:
            # For now, return null handler for unsupported types
            handler = NullHandler()

        return handler

    def _create_formatter_for_destination(
        self,
        destination: LogDestination,
        is_console: bool = False,
        use_colors: bool = True,
    ) -> BaseFormatter:
        """Create appropriate formatter for destination type using standardized formatters."""
        try:
            format_type = getattr(destination, "format", "plain-text")

            # Create cache key for this destination
            cache_key = f"{destination.type}_{format_type}_{is_console}_{use_colors}"

            # Check if we have a cached formatter
            if cache_key in self._formatter_cache:
                return self._formatter_cache[cache_key]

            from ..formatters import get_formatter

            # Map old format types to new standardized types
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

    def _setup_fallback_configuration(self):
        """Setup fallback configuration for error handling."""
        # Create a null handler as fallback
        fallback_handler = NullHandler()
        self._fallback_handler = fallback_handler

    def log(self, level: Union[str, int], message: str, **kwargs):
        """
        Log method with automatic async/sync detection.

        This method automatically detects if it's being called from an async context
        and handles both synchronous and asynchronous logging appropriately.

        Args:
            level: Log level (string or numeric)
            message: Log message
            **kwargs: Additional log record fields
        """
        # Fast path checks (minimal overhead)
        if not self._initialized:
            return

        try:
            # Check if we're in an async context
            try:
                asyncio.get_running_loop()
                # We're in an async context - return coroutine
                return self._log_async(level, message, **kwargs)
            except RuntimeError:
                # No event loop - use synchronous fallback
                self._log_sync(level, message, **kwargs)

        except Exception:
            # Silent error handling for speed
            pass

    async def log_async(self, level: Union[str, int], message: str, **kwargs) -> None:
        """
        Async log method for explicit async usage.

        Args:
            level: Log level (string or numeric)
            message: Log message
            **kwargs: Additional log record fields
        """
        if not self._initialized:
            return

        try:
            await self._log_async(level, message, **kwargs)
        except Exception:
            # Silent error handling for speed
            pass

    def _log_sync(self, level: Union[str, int], message: str, **kwargs) -> None:
        """Synchronous fallback logging method - SIMPLIFIED."""
        try:
            level = self._record_builder.normalize_level(level)
            record = self._record_builder.create(level, message, **kwargs)
            record = self._extension_processor.apply_data_protection(
                record, self._data_protection
            )

            layer_name = getattr(record, "layer", "default")
            handlers = self._get_handlers_for_layer(layer_name)
            self._handler_dispatcher.dispatch_sync(record, handlers)

            # Update statistics
            self._log_count += 1

        except Exception:
            # Silent error handling for speed
            pass

    async def _log_async(self, level: Union[str, int], message: str, **kwargs) -> None:
        """Internal async logging method - SIMPLIFIED for reliability."""
        try:
            level = self._record_builder.normalize_level(level)
            record = self._record_builder.create(level, message, **kwargs)
            record = self._extension_processor.apply_data_protection(
                record, self._data_protection
            )

            await self._emit_to_handlers(record)

            # Update statistics
            self._log_count += 1

        except Exception as e:
            # Use fallback handler if available
            if hasattr(self, "_fallback_handler") and self._fallback_handler:
                try:
                    if "record" in locals():
                        self._fallback_handler.handle(record)
                except Exception:
                    pass

            # Re-raise the error
            raise HydraLoggerError(f"Failed to log message: {e}") from e

    async def _overflow_worker(self):
        """Process overflow messages when semaphore is busy - FIXED VERSION."""
        while not self._closed:
            try:
                # Process overflow messages with proper error handling
                try:
                    # Wait for message with timeout to avoid blocking
                    record = await asyncio.wait_for(
                        self._overflow_queue.get(), timeout=0.1
                    )
                except asyncio.TimeoutError:
                    # No message available, continue
                    continue
                except Exception:
                    # Queue might be closed, exit gracefully
                    break

                # Try to acquire semaphore (non-blocking)
                if self._concurrency_semaphore and self._concurrency_semaphore.locked():
                    # Still busy, put back in overflow queue
                    try:
                        self._overflow_queue.put_nowait(record)
                    except asyncio.QueueFull:
                        # Overflow queue full, drop message
                        diagnostics.warning("Overflow queue full, dropping message")
                        # Drop message to prevent memory leak
                else:
                    # Semaphore available, process message
                    if self._concurrency_semaphore:
                        async with self._concurrency_semaphore:
                            try:
                                # INTEGRATION: Monitor overflow message processing
                                TimeUtility.perf_counter()
                                await self._emit_to_handlers(record)

                                self._log_count += 1
                            finally:
                                # Record processing completed
                                pass
                    else:
                        # No semaphore, process directly
                        try:
                            await self._emit_to_handlers(record)
                            self._log_count += 1
                        finally:
                            # Record processing completed
                            pass

            except Exception:
                # Silently handle errors to prevent StreamWriter issues
                await asyncio.sleep(0.001)

    async def log_batch(
        self, messages: List[Tuple[Union[str, int], str, Dict]], **kwargs
    ) -> None:
        """
        Log multiple messages with HIGHLY OPTIMIZED batch processing.

        Args:
            messages: List of tuples (level, message, extra_kwargs)
            **kwargs: Common kwargs for all messages
        """
        if not self._initialized:
            raise HydraLoggerError("Logger not initialized")

        if not messages:
            return

        try:

            optimal_chunk_size = min(5000, len(messages) // 10)  # Dynamic chunk sizing
            optimal_chunk_size = max(100, optimal_chunk_size)  # Minimum chunk size

            # Progress tracking (only for large batches)
            if len(messages) > 10000:
                diagnostics.info(
                    "Processing %s messages in chunks of %s",
                    f"{len(messages):,}",
                    f"{optimal_chunk_size:,}",
                )

            for i in range(0, len(messages), optimal_chunk_size):
                chunk = messages[i : i + optimal_chunk_size]

                await self._process_chunk_optimized(chunk, **kwargs)

        except Exception as e:
            raise HydraLoggerError(f"Failed to log batch: {e}") from e

    async def _process_chunk_optimized(
        self, chunk: List[Tuple[Union[str, int], str, Dict]], **kwargs
    ) -> None:
        """Process a chunk of messages with minimal overhead - NO TASK CANCELLATION ISSUES."""

        if len(chunk) <= 100:
            # Sequential processing - no task management overhead
            for level, message, extra_kwargs in chunk:
                try:
                    await self.log(level, message, **{**kwargs, **extra_kwargs})
                except Exception as e:
                    diagnostics.warning("Message processing error: %s", e)
                    continue
        else:
            # For larger chunks, use controlled concurrency with proper cleanup
            concurrency = min(20, len(chunk) // 100)  # Conservative concurrency
            concurrency = max(1, concurrency)  # At least 1

            # Progress tracking (only for large chunks)
            if len(chunk) > 1000:
                diagnostics.info(
                    "Processing %s messages with concurrency %s",
                    f"{len(chunk):,}",
                    concurrency,
                )

            # Process in smaller sub-chunks to avoid overwhelming the system
            sub_chunk_size = max(50, len(chunk) // concurrency)

            for i in range(0, len(chunk), sub_chunk_size):
                sub_chunk = chunk[i : i + sub_chunk_size]

                # Process sub-chunk sequentially (most reliable)
                for level, message, extra_kwargs in sub_chunk:
                    try:
                        await self.log(level, message, **{**kwargs, **extra_kwargs})
                    except Exception as e:
                        diagnostics.warning("Message processing error: %s", e)
                        continue

    async def log_concurrent(
        self,
        messages: List[Tuple[Union[str, int], str, Dict]],
        max_concurrent: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Log multiple messages with TRUE PARALLEL PROCESSING using asyncio.

        Args:
            messages: List of tuples (level, message, extra_kwargs)
            max_concurrent: Maximum concurrent operations (defaults to memory-optimal)
            **kwargs: Common kwargs for all messages
        """
        if not self._initialized:
            raise HydraLoggerError("Logger not initialized")

        if not messages:
            return

        try:

            if max_concurrent is None:
                # Dynamic concurrency: more messages = more concurrency (up to limit)
                concurrency = min(100, max(10, len(messages) // 100))
            else:
                concurrency = min(max_concurrent, 100)  # Cap at 100

            # Progress tracking (only for large batches)
            if len(messages) > 10000:
                diagnostics.info(
                    "Processing %s messages with concurrency %s",
                    f"{len(messages):,}",
                    concurrency,
                )

            semaphore = asyncio.Semaphore(concurrency)

            tasks = []
            for level, message, extra_kwargs in messages:
                task = asyncio.create_task(
                    self._log_with_semaphore(
                        semaphore, level, message, **{**kwargs, **extra_kwargs}
                    )
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            raise HydraLoggerError(f"Failed to log concurrent: {e}") from e

    async def _log_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        level: Union[str, int],
        message: str,
        **kwargs,
    ) -> None:
        """Log a single message with semaphore control for true parallelization."""
        async with semaphore:
            await self.log(level, message, **kwargs)

    async def log_background_work(
        self, work_tasks: List[callable], max_concurrent: Optional[int] = None
    ) -> List[Any]:
        """
        Execute background work tasks with TRUE PARALLEL PROCESSING.

        This method demonstrates how async loggers can provide real background processing benefits
        by parallelizing CPU-intensive work that would otherwise be sequential.

        Args:
            work_tasks: List of async callable functions to execute in parallel
            max_concurrent: Maximum concurrent operations (defaults to optimal)

        Returns:
            List of results from all work tasks
        """
        if not work_tasks:
            return []

        try:

            if max_concurrent is None:
                concurrency = min(50, max(5, len(work_tasks) // 10))
            else:
                concurrency = min(max_concurrent, 50)  # Cap at 50 for work tasks

            semaphore = asyncio.Semaphore(concurrency)

            tasks = []
            for work_task in work_tasks:
                task = asyncio.create_task(
                    self._execute_work_with_semaphore(semaphore, work_task)
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and return only successful results
            successful_results = [r for r in results if not isinstance(r, Exception)]

            return successful_results

        except Exception as e:
            diagnostics.error("Background work execution failed: %s", e)
            return []

    async def _execute_work_with_semaphore(
        self, semaphore: asyncio.Semaphore, work_task: callable
    ) -> Any:
        """Execute a single work task with semaphore control."""
        async with semaphore:
            if asyncio.iscoroutinefunction(work_task):
                return await work_task()
            else:
                # Run sync function in executor for true parallelization
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, work_task)

    async def _apply_security_processing(self, record: LogRecord) -> LogRecord:
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

    async def _execute_pre_log_plugins(self, record: LogRecord) -> LogRecord:
        """Execute pre-log plugins to modify the record before processing."""
        # Plugin system removed - simplified architecture
        return record

    async def _execute_post_log_plugins(self, record: LogRecord) -> None:
        """Execute post-log plugins after the record has been processed."""
        # Plugin system removed - simplified architecture
        pass

    async def _emit_to_handlers(self, record: LogRecord) -> None:
        """Emit record to all appropriate handlers for the layer."""
        # Get handlers for the record's layer
        layer_name = getattr(record, "layer", "default")
        handlers = self._get_handlers_for_layer(layer_name)
        await self._handler_dispatcher.dispatch_async(record, handlers)

    def _get_handlers_for_layer(self, layer_name: str) -> list:
        """Get handlers for a specific layer with caching."""
        return self._layer_router.handlers_for_layer(layer_name)

    # Convenience methods for different log levels
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        result = self.log(LogLevel.DEBUG, message, **kwargs)
        if asyncio.iscoroutine(result):
            # Schedule the coroutine in the current event loop
            try:
                loop = asyncio.get_running_loop()
                return loop.create_task(result)
            except RuntimeError:
                # No event loop running, return the coroutine
                return result
        return result

    def info(self, message: str, **kwargs):
        """Log an info message."""
        result = self.log(LogLevel.INFO, message, **kwargs)
        if asyncio.iscoroutine(result):
            # Schedule the coroutine in the current event loop
            try:
                loop = asyncio.get_running_loop()
                return loop.create_task(result)
            except RuntimeError:
                # No event loop running, return the coroutine
                return result
        return result

    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        result = self.log(LogLevel.WARNING, message, **kwargs)
        if asyncio.iscoroutine(result):
            # Schedule the coroutine in the current event loop
            try:
                loop = asyncio.get_running_loop()
                return loop.create_task(result)
            except RuntimeError:
                # No event loop running, return the coroutine
                return result
        return result

    def error(self, message: str, **kwargs):
        """Log an error message."""
        result = self.log(LogLevel.ERROR, message, **kwargs)
        if asyncio.iscoroutine(result):
            # Schedule the coroutine in the current event loop
            try:
                loop = asyncio.get_running_loop()
                return loop.create_task(result)
            except RuntimeError:
                # No event loop running, return the coroutine
                return result
        return result

    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        result = self.log(LogLevel.CRITICAL, message, **kwargs)
        if asyncio.iscoroutine(result):
            # Schedule the coroutine in the current event loop
            try:
                loop = asyncio.get_running_loop()
                return loop.create_task(result)
            except RuntimeError:
                # No event loop running, return the coroutine
                return result
        return result

    # Async convenience methods for explicit async usage
    async def debug_async(self, message: str, **kwargs) -> None:
        """Async log a debug message."""
        await self.log_async(LogLevel.DEBUG, message, **kwargs)

    async def info_async(self, message: str, **kwargs) -> None:
        """Async log an info message."""
        await self.log_async(LogLevel.INFO, message, **kwargs)

    async def warning_async(self, message: str, **kwargs) -> None:
        """Async log a warning message."""
        await self.log_async(LogLevel.WARNING, message, **kwargs)

    async def error_async(self, message: str, **kwargs) -> None:
        """Async log an error message."""
        await self.log_async(LogLevel.ERROR, message, **kwargs)

    async def critical_async(self, message: str, **kwargs) -> None:
        """Async log a critical message."""
        await self.log_async(LogLevel.CRITICAL, message, **kwargs)

    def warn(self, message: str, **kwargs) -> None:
        """Alias for warning (compatibility)."""
        return self.warning(message, **kwargs)

    def fatal(self, message: str, **kwargs) -> None:
        """Alias for critical (compatibility)."""
        return self.critical(message, **kwargs)

    def close(self):
        """Close the logger and cleanup resources - SIMPLIFIED VERSION."""
        if self._closed:
            return

        try:
            # Mark as closed first to prevent new operations
            self._closed = True

            # Clean up handlers
            for handler in self._handlers.values():
                try:
                    if hasattr(handler, "close"):
                        handler.close()
                except Exception:
                    pass

            # Clean up console handler
            if hasattr(self, "_console_handler") and self._console_handler:
                try:
                    self._console_handler.close()
                except Exception:
                    pass

            # Clean up concurrency resources
            if hasattr(self, "_concurrency_semaphore"):
                self._concurrency_semaphore = None

            # Clean up overflow worker
            if (
                hasattr(self, "_overflow_worker_task")
                and self._overflow_worker_task
                and not self._overflow_worker_task.done()
            ):
                self._overflow_worker_task.cancel()

            # Clear handler cache
            self._handler_cache.clear()

        except Exception:
            # Silent cleanup - don't fail on close
            pass

    async def close_async(self):
        """Async close method for proper async cleanup."""
        await self.aclose()

    async def aclose(self):
        """Async close method (standard async context manager protocol)."""
        if self._closed:
            return

        try:
            # Mark as closed first
            self._closed = True

            # Clean up handlers asynchronously
            for handler in self._handlers.values():
                try:
                    # Try aclose first (standard), then close_async (legacy), then sync
                    # close
                    if hasattr(handler, "aclose") and asyncio.iscoroutinefunction(
                        handler.aclose
                    ):
                        await handler.aclose()
                    elif hasattr(
                        handler, "close_async"
                    ) and asyncio.iscoroutinefunction(handler.close_async):
                        await handler.close_async()
                    elif hasattr(handler, "close"):
                        handler.close()
                except Exception:
                    pass

            # Clean up console handler
            if hasattr(self, "_console_handler") and self._console_handler:
                try:
                    if hasattr(
                        self._console_handler, "aclose"
                    ) and asyncio.iscoroutinefunction(self._console_handler.aclose):
                        await self._console_handler.aclose()
                    elif hasattr(
                        self._console_handler, "close_async"
                    ) and asyncio.iscoroutinefunction(
                        self._console_handler.close_async
                    ):
                        await self._console_handler.close_async()
                    else:
                        self._console_handler.close()
                except Exception:
                    pass

            # Clean up concurrency resources
            if hasattr(self, "_concurrency_semaphore"):
                self._concurrency_semaphore = None

            # Clean up overflow worker
            if (
                hasattr(self, "_overflow_worker_task")
                and self._overflow_worker_task
                and not self._overflow_worker_task.done()
            ):
                self._overflow_worker_task.cancel()
                try:
                    await self._overflow_worker_task
                except (asyncio.CancelledError, Exception):
                    pass

            # Clear handler cache
            self._handler_cache.clear()

        except Exception:
            # Silent cleanup - don't fail on close
            pass

    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the logger."""
        health_status = {
            "initialized": self._initialized,
            "closed": self._closed,
            "log_count": self._log_count,
            "start_time": self._start_time,
            "handler_count": len(self._handlers),
            "layer_count": len(self._layers),
        }

        # REAL ASYNC: Add concurrency information
        if self._concurrency_semaphore:
            health_status.update(
                {
                    "concurrency_optimal": self._optimal_concurrency,
                    "concurrency_semaphore": "active",
                    "concurrency_available": self._concurrency_semaphore._value,
                }
            )
        else:
            health_status.update(
                {
                    "concurrency_optimal": None,
                    "concurrency_semaphore": "inactive",
                    "concurrency_available": None,
                }
            )

        return health_status

    def update_security_level(self, level: str) -> None:
        """Update security level at runtime."""
        if self._config:
            self._config.update_security_level(level)
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
            self._config.update_monitoring_config(detail_level, sample_rate, background)

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

    def get_concurrency_info(self) -> Dict[str, Any]:
        """Get detailed concurrency information."""
        if not self._concurrency_semaphore:
            return {"status": "not_initialized"}

        try:
            import psutil

            memory = psutil.virtual_memory()
            return {
                "status": "active",
                "optimal_concurrency": self._optimal_concurrency,
                "semaphore_value": self._concurrency_semaphore._value,
                "memory_available_mb": memory.available / 1024 / 1024,
                "memory_percent": memory.percent,
                "concurrency_reasoning": self._get_concurrency_reasoning(),
            }
        except ImportError:
            return {
                "status": "active_no_psutil",
                "optimal_concurrency": self._optimal_concurrency,
                "semaphore_value": self._concurrency_semaphore._value,
            }

    def _get_concurrency_reasoning(self) -> str:
        """Get human-readable explanation of concurrency choice."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            available_mb = memory.available / 1024 / 1024

            if available_mb > 8000:
                return (
                    f"High concurrency ({self._optimal_concurrency}) - "
                    f"{available_mb:.0f}MB available"
                )
            elif available_mb > 4000:
                return (
                    f"Medium concurrency ({self._optimal_concurrency}) - "
                    f"{available_mb:.0f}MB available"
                )
            elif available_mb > 2000:
                return (
                    f"Low concurrency ({self._optimal_concurrency}) - "
                    f"{available_mb:.0f}MB available"
                )
            else:
                return (
                    f"Conservative concurrency ({self._optimal_concurrency}) - "
                    f"{available_mb:.0f}MB available"
                )
        except ImportError:
            return (
                f"Default concurrency ({self._optimal_concurrency}) - "
                "psutil not available"
            )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
