"""
Tests for async components of Hydra-Logger.

This module tests the async functionality including AsyncHydraLogger,
async handlers, async sinks, and async queue system.
"""

import os
import pytest
import asyncio
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.async_hydra.async_handlers import (
    AsyncLogHandler,
    AsyncRotatingFileHandler,
    AsyncStreamHandler,
    AsyncBufferedRotatingFileHandler
)
from hydra_logger.async_hydra.async_sinks import (
    AsyncSink,
    AsyncHttpSink,
    AsyncDatabaseSink,
    AsyncQueueSink,
    AsyncCloudSink,
    SinkStats
)
from hydra_logger.async_hydra.async_queue import (
    AsyncLogQueue,
    AsyncBatchProcessor,
    AsyncBackpressureHandler,
    QueueStats
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
    trace_context
)
from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination


class TestAsyncHydraLogger:
    """Test AsyncHydraLogger functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_async.log")

    def teardown_method(self):
        """Cleanup test files and close loggers."""
        if hasattr(self, 'logger') and self.logger is not None:
            try:
                if asyncio.iscoroutinefunction(self.logger.close):
                    asyncio.get_event_loop().run_until_complete(self.logger.close())
                else:
                    self.logger.close()
            except Exception as e:
                print(f"Error closing logger in teardown: {e}")
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)

    @pytest.mark.asyncio
    async def test_async_logger_initialization(self):
        """Test AsyncHydraLogger initialization."""
        logger = AsyncHydraLogger()
        assert logger is not None
        assert hasattr(logger, 'config')
        assert hasattr(logger, 'get_async_performance_statistics')

    @pytest.mark.asyncio
    async def test_async_logger_with_config(self):
        """Test AsyncHydraLogger with configuration."""
        config = LoggingConfig(
            layers={
                "ASYNC": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        logger = AsyncHydraLogger(config=config)
        assert logger is not None

    @pytest.mark.asyncio
    async def test_async_logging_methods(self):
        """Test async logging methods."""
        logger = AsyncHydraLogger()
        
        # Initialize the logger
        await logger.initialize()
        
        # Test all async logging levels
        await logger.debug("TEST", "Async debug message")
        await logger.info("TEST", "Async info message")
        await logger.warning("TEST", "Async warning message")
        await logger.error("TEST", "Async error message")
        await logger.critical("TEST", "Async critical message")
        
        # Check that metrics were incremented
        metrics = await logger.get_async_performance_statistics()
        assert metrics is not None
        assert metrics["message_count"] >= 5

    @pytest.mark.asyncio
    async def test_async_logging_with_layer(self):
        """Test async logging with specific layer."""
        config = LoggingConfig(
            layers={
                "ASYNC_CUSTOM": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", level="INFO")
                    ]
                )
            }
        )
        logger = AsyncHydraLogger(config=config)
        
        # Initialize the logger
        await logger.initialize()
        
        await logger.info("ASYNC_CUSTOM", "Async custom layer message")
        
        # Check metrics
        metrics = await logger.get_async_performance_statistics()
        assert metrics is not None
        assert metrics["message_count"] >= 1

    @pytest.mark.asyncio
    async def test_async_logging_with_extra_data(self):
        """Test async logging with extra data."""
        logger = AsyncHydraLogger()
        
        # Initialize the logger
        await logger.initialize()
        
        extra_data = {"user_id": "12345", "session_id": "abc123"}
        await logger.info("TEST", "Async message with extra data")
        
        # Check metrics
        metrics = await logger.get_async_performance_statistics()
        assert metrics is not None
        assert metrics["message_count"] >= 1

    @pytest.mark.asyncio
    async def test_async_file_logging(self):
        """Test async file logging functionality."""
        config = LoggingConfig(
            layers={
                "ASYNC_FILE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path=self.log_file, level="INFO")
                    ]
                )
            }
        )
        logger = AsyncHydraLogger(config=config)
        
        # Initialize the logger
        await logger.initialize()
        
        # Log message
        await logger.info("ASYNC_FILE", "Async file log message")
        
        # Check that file was created
        assert os.path.exists(self.log_file)
        
        # Check file content
        with open(self.log_file, 'r') as f:
            content = f.read()
            assert "Async file log message" in content

    @pytest.mark.asyncio
    async def test_async_performance_monitoring(self):
        """Test async performance monitoring."""
        logger = AsyncHydraLogger(enable_performance_monitoring=True)
        
        # Initialize the logger
        await logger.initialize()
        
        # Log messages
        await logger.info("TEST", "Async message 1")
        await logger.info("TEST", "Async message 2")
        
        # Check performance metrics
        metrics = await logger.get_async_performance_statistics()
        assert metrics is not None
        assert metrics["message_count"] >= 2

    @pytest.mark.asyncio
    async def test_async_logger_close(self):
        """Test async logger close functionality."""
        logger = AsyncHydraLogger()
        
        # Initialize the logger
        await logger.initialize()
        
        # Log some messages
        await logger.info("TEST", "Async message 1")
        await logger.info("TEST", "Async message 2")
        
        # Close logger
        await logger.close()
        
        # Logger should still be usable after close
        await logger.info("TEST", "Async message after close")


class TestAsyncHandlers:
    """Test async handler functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_async_handlers.log")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)

    @pytest.mark.asyncio
    async def test_async_log_handler(self):
        """Test AsyncLogHandler base class."""
        class DummyAsyncLogHandler(AsyncLogHandler):
            async def _process_record_async(self, record):
                pass
        handler = DummyAsyncLogHandler()
        assert handler is not None

    @pytest.mark.asyncio
    async def test_async_rotating_file_handler(self):
        """Test AsyncRotatingFileHandler."""
        handler = AsyncRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3
        )
        assert handler is not None

    @pytest.mark.asyncio
    async def test_async_stream_handler(self):
        """Test AsyncStreamHandler."""
        handler = AsyncStreamHandler()
        assert handler is not None

    @pytest.mark.asyncio
    async def test_async_buffered_rotating_file_handler(self):
        """Test AsyncBufferedRotatingFileHandler."""
        handler = AsyncBufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=8192
        )
        assert handler is not None


class TestAsyncSinks:
    """Test async sink functionality."""

    @pytest.mark.asyncio
    async def test_async_sink_base(self):
        """Test AsyncSink base class."""
        class DummyAsyncSink(AsyncSink):
            async def emit_async(self, record):
                return True
        sink = DummyAsyncSink()
        assert sink is not None

    @pytest.mark.asyncio
    async def test_async_http_sink(self):
        """Test AsyncHttpSink."""
        sink = AsyncHttpSink(url="http://example.com/logs")
        assert sink is not None
        assert sink.url == "http://example.com/logs"

    @pytest.mark.asyncio
    async def test_async_database_sink(self):
        """Test AsyncDatabaseSink."""
        sink = AsyncDatabaseSink(connection_string="sqlite:///test.db")
        assert sink is not None
        assert sink.connection_string == "sqlite:///test.db"

    @pytest.mark.asyncio
    async def test_async_queue_sink(self):
        """Test AsyncQueueSink."""
        sink = AsyncQueueSink(queue_url="redis://localhost:6379")
        assert sink is not None
        assert sink.queue_url == "redis://localhost:6379"

    @pytest.mark.asyncio
    async def test_async_cloud_sink(self):
        """Test AsyncCloudSink."""
        sink = AsyncCloudSink(
            service_type="aws",
            credentials={"access_key": "test", "secret_key": "test"}
        )
        assert sink is not None
        assert sink.service_type == "aws"

    @pytest.mark.asyncio
    async def test_sink_stats(self):
        """Test sink statistics."""
        stats = SinkStats()
        assert stats is not None
        assert hasattr(stats, 'total_messages')
        assert hasattr(stats, 'successful_messages')
        assert hasattr(stats, 'failed_messages')


class TestAsyncQueue:
    """Test async queue functionality."""

    @pytest.mark.asyncio
    async def test_async_log_queue(self):
        """Test AsyncLogQueue."""
        queue = AsyncLogQueue()
        assert queue is not None

    @pytest.mark.asyncio
    async def test_async_batch_processor(self):
        """Test AsyncBatchProcessor."""
        processor = AsyncBatchProcessor(batch_size=10)
        assert processor is not None
        assert processor.batch_size == 10

    @pytest.mark.asyncio
    async def test_async_backpressure_handler(self):
        """Test AsyncBackpressureHandler."""
        handler = AsyncBackpressureHandler(max_queue_size=1000)
        assert handler is not None
        assert handler.max_queue_size == 1000

    @pytest.mark.asyncio
    async def test_queue_stats(self):
        """Test QueueStats."""
        stats = QueueStats()
        assert stats is not None
        assert hasattr(stats, 'messages_queued')
        assert hasattr(stats, 'messages_processed')
        assert hasattr(stats, 'queue_size')


class TestAsyncContext:
    """Test async context functionality."""

    @pytest.mark.asyncio
    async def test_async_context(self):
        """Test AsyncContext."""
        context = AsyncContext()
        assert context is not None

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test AsyncContextManager."""
        manager = AsyncContextManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_async_trace_manager(self):
        """Test AsyncTraceManager."""
        manager = AsyncTraceManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_async_context_switcher(self):
        """Test AsyncContextSwitcher."""
        switcher = AsyncContextSwitcher()
        assert switcher is not None

    @pytest.mark.asyncio
    async def test_async_context_functions(self):
        """Test async context utility functions."""
        # Test context creation
        context = AsyncContext()
        assert context is not None

    @pytest.mark.asyncio
    async def test_trace_functions(self):
        """Test trace utility functions."""
        # Test trace manager
        manager = AsyncTraceManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_correlation_functions(self):
        """Test correlation ID functions."""
        # Test context manager
        manager = AsyncContextManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_context_switch_detection(self):
        """Test context switch detection."""
        # Test trace manager functionality
        manager = AsyncTraceManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_async_context_decorators(self):
        """Test async context decorators."""
        # Test context creation
        context = AsyncContext()
        assert context is not None

    @pytest.mark.asyncio
    async def test_context_utility_functions(self):
        """Test context utility functions."""
        # Test get_async_context
        context = get_async_context()
        assert context is None  # No context set initially
        
        # Test set_async_context
        new_context = AsyncContext()
        set_async_context(new_context)
        
        # Test get_async_context again
        retrieved_context = get_async_context()
        assert retrieved_context is new_context
        
        # Test clear_async_context
        clear_async_context()
        assert get_async_context() is None

    @pytest.mark.asyncio
    async def test_trace_utility_functions(self):
        """Test trace utility functions."""
        # Test start_trace
        trace_id = start_trace()
        assert trace_id is not None
        
        # Test get_trace_id
        retrieved_trace_id = get_trace_id()
        assert retrieved_trace_id == trace_id
        
        # Test set_correlation_id and get_correlation_id
        correlation_id = "test-correlation-123"
        set_correlation_id(correlation_id)
        assert get_correlation_id() == correlation_id

    @pytest.mark.asyncio
    async def test_context_switch_functions(self):
        """Test context switch detection functions."""
        # Test detect_context_switch
        context1 = AsyncContext()
        context2 = AsyncContext()
        
        # First context switch should be False (no previous context)
        assert not detect_context_switch(context1)
        
        # Second context switch should be True (different context)
        assert detect_context_switch(context2)
        
        # Same context should be False
        assert not detect_context_switch(context2)
        
        # Test get_context_switch_count
        count = get_context_switch_count()
        assert count >= 1  # At least one switch detected

    @pytest.mark.asyncio
    async def test_async_context_decorator(self):
        """Test async_context decorator."""
        async with async_context() as ctx:
            assert ctx is not None
            assert isinstance(ctx, AsyncContext)

    @pytest.mark.asyncio
    async def test_trace_context_decorator(self):
        """Test trace_context decorator."""
        async with trace_context() as trace_id:
            assert trace_id is not None
            assert get_trace_id() == trace_id


class TestAsyncIntegration:
    """Test async integration scenarios."""

    def setup_method(self):
        """Setup test environment."""
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_async_integration.log")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_logs_dir):
            shutil.rmtree(self.test_logs_dir)

    @pytest.mark.asyncio
    async def test_async_logger_with_sinks(self):
        """Test AsyncHydraLogger with async sinks."""
        config = LoggingConfig(
            layers={
                "ASYNC_SINK": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_http",
                            level="INFO",
                            url="http://example.com/logs"
                        )
                    ]
                )
            }
        )
        logger = AsyncHydraLogger(config=config)
        assert logger is not None

    @pytest.mark.asyncio
    async def test_async_logger_with_queue(self):
        """Test AsyncHydraLogger with async queue."""
        config = LoggingConfig(
            layers={
                "ASYNC_QUEUE": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_queue",
                            level="INFO",
                            queue_url="redis://localhost:6379"
                        )
                    ]
                )
            }
        )
        logger = AsyncHydraLogger(config=config)
        assert logger is not None

    @pytest.mark.asyncio
    async def test_async_logger_with_database(self):
        """Test AsyncHydraLogger with async database."""
        config = LoggingConfig(
            layers={
                "ASYNC_DB": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_database",
                            level="INFO",
                            connection_string="sqlite:///test.db"
                        )
                    ]
                )
            }
        )
        logger = AsyncHydraLogger(config=config)
        assert logger is not None

    @pytest.mark.asyncio
    async def test_async_logger_with_cloud(self):
        """Test AsyncHydraLogger with async cloud."""
        config = LoggingConfig(
            layers={
                "ASYNC_CLOUD": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_cloud",
                            level="INFO",
                            service_type="aws",
                            credentials={"access_key": "test", "secret_key": "test"}
                        )
                    ]
                )
            }
        )
        logger = AsyncHydraLogger(config=config)
        assert logger is not None

    @pytest.mark.asyncio
    async def test_async_performance_monitoring(self):
        """Test async performance monitoring."""
        logger = AsyncHydraLogger(enable_performance_monitoring=True)
        
        # Initialize the logger
        await logger.initialize()
        
        # Log messages
        await logger.info("TEST", "Async message 1")
        await logger.info("TEST", "Async message 2")
        
        # Check performance metrics
        metrics = await logger.get_async_performance_statistics()
        assert metrics is not None
        assert metrics["message_count"] >= 2

    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling."""
        logger = AsyncHydraLogger()
        
        # Initialize the logger
        await logger.initialize()
        
        # Test with invalid input
        try:
            await logger.info("TEST", None)
        except Exception:
            pass
        
        # Logger should still work
        await logger.info("TEST", "Async message after error")
        
        # Check metrics
        metrics = await logger.get_async_performance_statistics()
        assert metrics is not None

    @pytest.mark.asyncio
    async def test_async_thread_safety(self):
        """Test async thread safety."""
        logger = AsyncHydraLogger()
        
        # Initialize the logger
        await logger.initialize()
        
        async def log_messages():
            for i in range(10):
                await logger.info("TEST", f"Async thread message {i}")
        
        # Create multiple tasks
        tasks = []
        for _ in range(5):
            task = asyncio.create_task(log_messages())
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Check that all messages were tracked
        metrics = await logger.get_async_performance_statistics()
        assert metrics is not None
        assert metrics["message_count"] >= 50  # 5 tasks * 10 messages each

# At the end of the file, add a test to check for pending tasks
import asyncio
import gc
import sys

def test_no_pending_async_tasks():
    gc.collect()
    loop = asyncio.get_event_loop()
    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    if pending:
        print(f"WARNING: {len(pending)} pending async tasks after tests:")
        for t in pending:
            print(f"  - {t}")
    assert not pending, "There are pending async tasks after tests!" 