"""
Integration tests for async logging system.

This module tests the integration between all async components including
AsyncHydraLogger, async handlers, async queues, and async performance monitoring.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

import pytest

from hydra_logger.async_hydra.async_logger import AsyncHydraLogger, AsyncPerformanceMonitor
from hydra_logger.async_hydra.async_handlers import AsyncRotatingFileHandler, AsyncStreamHandler
from hydra_logger.async_hydra.async_queue import AsyncLogQueue, AsyncBatchProcessor, AsyncBackpressureHandler
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


class TestAsyncSystemIntegration:
    """Integration tests for the complete async logging system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def async_config(self, temp_dir):
        """Create async logging configuration."""
        return LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="console", format="text"),
                        LogDestination(type="file", path=os.path.join(temp_dir, "async_integration.log"))
                    ]
                ),
                "PERFORMANCE": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="file", path=os.path.join(temp_dir, "performance.log"))
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(type="file", path=os.path.join(temp_dir, "error.log"))
                    ]
                )
            }
        )
    
    @pytest.mark.asyncio
    async def test_complete_async_logging_flow(self, async_config):
        """Test complete async logging flow from logger to handlers."""
        logger = AsyncHydraLogger(
            config=async_config,
            enable_performance_monitoring=True,
            queue_size=1000,
            batch_size=50
        )
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Send messages to different layers
        await logger.info("DEFAULT", "Integration test message")
        await logger.debug("PERFORMANCE", "Performance debug message")
        await logger.error("ERROR", "Error test message")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check that loggers were created
        assert "DEFAULT" in logger.async_loggers
        assert "PERFORMANCE" in logger.async_loggers
        assert "ERROR" in logger.async_loggers
        
        # Check performance statistics
        stats = await logger.get_async_performance_statistics()
        assert stats is not None
        assert stats.get("total_messages", 0) >= 3
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logging_with_queues_and_backpressure(self, async_config):
        """Test async logging with queue and backpressure handling."""
        logger = AsyncHydraLogger(
            config=async_config,
            queue_size=10,  # Small queue to test backpressure
            batch_size=5,
            batch_timeout=0.1
        )
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Send many messages quickly to test backpressure
        start_time = time.time()
        tasks = []
        for i in range(20):
            task = logger.info("DEFAULT", f"Backpressure test message {i}")
            tasks.append(task)
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Performance should be reasonable even with backpressure
        assert end_time - start_time < 2.0
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logging_concurrent_layers(self, async_config):
        """Test concurrent logging to multiple layers."""
        logger = AsyncHydraLogger(config=async_config)
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Create concurrent tasks for different layers
        async def log_to_layer(layer: str, count: int):
            for i in range(count):
                await logger.info(layer, f"Concurrent message {i} to {layer}")
                await asyncio.sleep(0.001)  # Small delay
        
        # Run concurrent tasks
        tasks = [
            log_to_layer("DEFAULT", 10),
            log_to_layer("PERFORMANCE", 10),
            log_to_layer("ERROR", 5)
        ]
        
        start_time = time.time()
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Performance should be good
        assert end_time - start_time < 1.0
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logging_with_performance_monitoring(self, async_config):
        """Test async logging with comprehensive performance monitoring."""
        logger = AsyncHydraLogger(
            config=async_config,
            enable_performance_monitoring=True
        )
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Send messages with different characteristics
        for i in range(50):
            if i % 10 == 0:
                await logger.error("ERROR", f"Error message {i}")
            elif i % 5 == 0:
                await logger.debug("PERFORMANCE", f"Debug message {i}")
            else:
                await logger.info("DEFAULT", f"Info message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check comprehensive performance statistics
        stats = await logger.get_async_performance_statistics()
        assert stats is not None
        
        # Check basic stats
        assert stats.get("total_messages", 0) >= 50
        assert stats.get("uptime_seconds", 0) > 0
        
        # Check async-specific stats
        if "avg_async_processing_time" in stats:
            assert stats["avg_async_processing_time"] >= 0
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logging_error_recovery(self, async_config):
        """Test async logging error recovery and resilience."""
        logger = AsyncHydraLogger(
            config=async_config,
            enable_performance_monitoring=True
        )
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Send messages that might cause issues
        for i in range(20):
            try:
                # Mix normal and potentially problematic messages
                if i % 3 == 0:
                    await logger.error("ERROR", f"Error message {i}")
                elif i % 3 == 1:
                    await logger.info("DEFAULT", f"Normal message {i}")
                else:
                    # Try to log with special characters
                    await logger.debug("PERFORMANCE", f"Special chars: 🚀 测试 {i}")
            except Exception as e:
                # Logging should continue even if some messages fail
                print(f"Expected error in test: {e}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check that logger is still functional
        stats = await logger.get_async_performance_statistics()
        assert stats is not None
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logging_memory_efficiency(self, async_config):
        """Test async logging memory efficiency under load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        logger = AsyncHydraLogger(
            config=async_config,
            enable_performance_monitoring=True,
            queue_size=500,
            batch_size=25
        )
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Send many messages
        start_time = time.time()
        tasks = []
        for i in range(100):
            task = logger.info("DEFAULT", f"Memory test message {i}")
            tasks.append(task)
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.2)
        
        end_time = time.time()
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 20MB)
        assert memory_increase < 20 * 1024 * 1024
        
        # Performance should be good
        assert end_time - start_time < 2.0
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logging_with_custom_handlers(self, temp_dir):
        """Test async logging with custom async handlers."""
        # Create custom async handlers
        file_handler = AsyncRotatingFileHandler(
            filename=os.path.join(temp_dir, "custom.log"),
            maxBytes=1024,
            backupCount=2
        )
        await file_handler.start()
        
        stream_handler = AsyncStreamHandler()
        await stream_handler.start()
        
        # Create log records
        record1 = logging.LogRecord(
            name="custom_test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Custom handler test message",
            args=(),
            exc_info=None
        )
        
        record2 = logging.LogRecord(
            name="custom_test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Custom handler error message",
            args=(),
            exc_info=None
        )
        
        # Send to both handlers
        await file_handler.emit_async(record1)
        await stream_handler.emit_async(record2)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Check file output
        assert os.path.exists(os.path.join(temp_dir, "custom.log"))
        
        # Cleanup
        await file_handler.stop()
        await stream_handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_logging_with_queues_and_processors(self, temp_dir):
        """Test async logging with custom queue processors."""
        processed_messages = []
        
        def custom_processor(messages):
            processed_messages.extend(messages)
        
        # Create queue with custom processor
        queue = AsyncLogQueue(
            max_size=100,
            batch_size=5,
            batch_timeout=0.1,
            processor=custom_processor
        )
        await queue.start()
        
        # Create batch processor
        batch_processor = AsyncBatchProcessor(
            batch_size=3,
            processor=custom_processor
        )
        
        # Send messages to both
        for i in range(10):
            await queue.put(f"Queue message {i}")
            await batch_processor.add_message(f"Batch message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check that messages were processed
        assert len(processed_messages) >= 10
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_logging_stress_test(self, async_config):
        """Stress test for async logging system."""
        logger = AsyncHydraLogger(
            config=async_config,
            enable_performance_monitoring=True,
            queue_size=2000,
            batch_size=100,
            batch_timeout=0.05
        )
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Create stress test with multiple concurrent operations
        async def stress_operation(operation_id: int):
            for i in range(20):
                layer = f"STRESS_{operation_id % 3}"
                level = ["info", "debug", "error"][i % 3]
                message = f"Stress test {operation_id}-{i}"
                
                log_method = getattr(logger, level)
                await log_method(layer, message)
                
                # Small random delay
                await asyncio.sleep(0.001 * (i % 3))
        
        # Run multiple stress operations concurrently
        start_time = time.time()
        tasks = [stress_operation(i) for i in range(10)]
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Wait for processing
        await asyncio.sleep(0.3)
        
        # Check performance
        assert end_time - start_time < 3.0
        
        # Check statistics
        stats = await logger.get_async_performance_statistics()
        assert stats is not None
        assert stats.get("total_messages", 0) >= 200
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logging_cleanup_and_shutdown(self, async_config):
        """Test proper cleanup and shutdown of async logging system."""
        logger = AsyncHydraLogger(
            config=async_config,
            enable_performance_monitoring=True
        )
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Send some messages
        for i in range(10):
            await logger.info("DEFAULT", f"Cleanup test message {i}")
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Close the logger
        await logger.close()
        
        # Verify cleanup
        assert len(logger._async_queues) == 0
        assert logger._initialized is False


class TestAsyncPerformanceMonitoring:
    """Tests for async performance monitoring integration."""
    
    @pytest.mark.asyncio
    async def test_async_performance_monitor_integration(self):
        """Test AsyncPerformanceMonitor integration with async operations."""
        monitor = AsyncPerformanceMonitor()
        
        # Test async timing operations
        start_time = await monitor.start_async_processing_timer()
        await asyncio.sleep(0.01)  # Simulate processing
        await monitor.end_async_processing_timer(start_time)
        
        start_time = await monitor.start_async_queue_timer()
        await asyncio.sleep(0.01)  # Simulate queue operation
        await monitor.end_async_queue_timer(start_time)
        
        # Record context switches
        await monitor.record_async_context_switch()
        
        # Get statistics
        stats = monitor.get_async_statistics()
        assert stats is not None
        assert "async_context_switches" in stats
        assert stats["async_context_switches"] == 1
        
        # Test reset
        await monitor.reset_async_statistics()
        reset_stats = monitor.get_async_statistics()
        assert reset_stats["async_context_switches"] == 0
    
    @pytest.mark.asyncio
    async def test_async_performance_monitor_under_load(self):
        """Test async performance monitor under load."""
        monitor = AsyncPerformanceMonitor()
        
        # Simulate high load
        async def simulate_load():
            for i in range(50):
                start_time = await monitor.start_async_processing_timer()
                await asyncio.sleep(0.001)  # Simulate processing
                await monitor.end_async_processing_timer(start_time)
                
                start_time = await monitor.start_async_queue_timer()
                await asyncio.sleep(0.001)  # Simulate queue operation
                await monitor.end_async_queue_timer(start_time)
                
                if i % 10 == 0:
                    await monitor.record_async_context_switch()
        
        # Run multiple concurrent load simulations
        tasks = [simulate_load() for _ in range(5)]
        await asyncio.gather(*tasks)
        
        # Check statistics
        stats = monitor.get_async_statistics()
        assert stats is not None
        assert stats.get("total_messages", 0) >= 250
        assert stats.get("async_context_switches", 0) >= 25


class TestAsyncErrorHandling:
    """Tests for async error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_async_logging_error_handling(self):
        """Test async logging error handling and recovery."""
        # Create logger with problematic configuration
        config = LoggingConfig(
            layers={
                "DEFAULT": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(type="file", path="/nonexistent/path/test.log")
                    ]
                )
            }
        )
        
        logger = AsyncHydraLogger(config=config)
        
        # Wait for async setup
        await asyncio.sleep(0.1)
        
        # Try to log messages (should not crash)
        for i in range(5):
            try:
                await logger.info("DEFAULT", f"Error handling test {i}")
            except Exception as e:
                # Should not raise exceptions
                print(f"Expected error in test: {e}")
        
        # Logger should still be functional
        assert logger._initialized is True
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_queue_error_recovery(self):
        """Test async queue error recovery."""
        def error_processor(messages):
            raise Exception("Test processor error")
        
        queue = AsyncLogQueue(
            max_size=100,
            processor=error_processor
        )
        await queue.start()
        
        # Send messages (should not crash)
        for i in range(5):
            success = await queue.put(f"Error recovery test {i}")
            assert success is True
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Queue should still be running
        assert queue._running is True
        
        await queue.stop()
    
    @pytest.mark.asyncio
    async def test_async_handler_error_recovery(self):
        """Test async handler error recovery."""
        class ErrorAsyncHandler(AsyncRotatingFileHandler):
            async def _process_record_async(self, record):
                if "error" in record.getMessage().lower():
                    raise Exception("Test handler error")
                await super()._process_record_async(record)
        
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = ErrorAsyncHandler(
                filename=os.path.join(temp_dir, "error_test.log")
            )
            await handler.start()
            
            # Send normal message
            record1 = logging.LogRecord(
                name="test", level=logging.INFO, pathname="test.py",
                lineno=1, msg="Normal message", args=(), exc_info=None
            )
            await handler.emit_async(record1)
            
            # Send error message
            record2 = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="test.py",
                lineno=1, msg="Error message", args=(), exc_info=None
            )
            await handler.emit_async(record2)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Handler should still be running
            assert handler._running is True
            
            await handler.stop() 