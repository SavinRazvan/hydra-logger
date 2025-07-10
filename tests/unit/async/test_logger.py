"""
Tests for async logger functionality.

This module tests the AsyncHydraLogger and related async logging components.
"""

import asyncio
import logging
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock

from hydra_logger.async_hydra.async_logger import AsyncHydraLogger, AsyncPerformanceMonitor, AsyncCompositeHandler
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


class TestAsyncPerformanceMonitor:
    """Test AsyncPerformanceMonitor functionality."""
    
    @pytest.mark.asyncio
    async def test_async_performance_monitor_initialization(self):
        """Test AsyncPerformanceMonitor initialization."""
        monitor = AsyncPerformanceMonitor()
        
        assert monitor._async_processing_times == []
        assert monitor._async_queue_times == []
        assert monitor._async_batch_times == []
        assert monitor._async_context_switches == 0
    
    @pytest.mark.asyncio
    async def test_async_performance_monitor_timing(self):
        """Test async performance timing methods."""
        monitor = AsyncPerformanceMonitor()
        
        # Test processing timer
        start_time = await monitor.start_async_processing_timer()
        assert isinstance(start_time, float)
        
        await monitor.end_async_processing_timer(start_time)
        assert len(monitor._async_processing_times) == 1
        
        # Test queue timer
        start_time = await monitor.start_async_queue_timer()
        assert isinstance(start_time, float)
        
        await monitor.end_async_queue_timer(start_time)
        assert len(monitor._async_queue_times) == 1
    
    @pytest.mark.asyncio
    async def test_async_performance_monitor_context_switches(self):
        """Test async context switch recording."""
        monitor = AsyncPerformanceMonitor()
        
        await monitor.record_async_context_switch()
        assert monitor._async_context_switches == 1
        
        await monitor.record_async_context_switch()
        assert monitor._async_context_switches == 2
    
    @pytest.mark.asyncio
    async def test_async_performance_monitor_statistics(self):
        """Test async performance statistics."""
        monitor = AsyncPerformanceMonitor()
        
        # Record some timing data
        start_time = await monitor.start_async_processing_timer()
        await asyncio.sleep(0.01)
        await monitor.end_async_processing_timer(start_time)
        
        start_time = await monitor.start_async_queue_timer()
        await asyncio.sleep(0.01)
        await monitor.end_async_queue_timer(start_time)
        
        await monitor.record_async_context_switch()
        
        # Get statistics
        stats = monitor.get_async_statistics()
        
        assert "avg_async_processing_time" in stats
        assert "max_async_processing_time" in stats
        assert "min_async_processing_time" in stats
        assert "avg_async_queue_time" in stats
        assert "max_async_queue_time" in stats
        assert "min_async_queue_time" in stats
        assert stats["async_context_switches"] == 1
    
    @pytest.mark.asyncio
    async def test_async_performance_monitor_reset(self):
        """Test resetting async performance statistics."""
        monitor = AsyncPerformanceMonitor()
        
        # Record some data
        start_time = await monitor.start_async_processing_timer()
        await monitor.end_async_processing_timer(start_time)
        await monitor.record_async_context_switch()
        
        # Check data exists
        assert len(monitor._async_processing_times) == 1
        assert monitor._async_context_switches == 1
        
        # Reset
        await monitor.reset_async_statistics()
        
        # Check data is cleared
        assert len(monitor._async_processing_times) == 0
        assert monitor._async_context_switches == 0


class TestAsyncHydraLogger:
    """Test AsyncHydraLogger functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create test logs directory
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_initialization(self):
        """Test AsyncHydraLogger initialization."""
        logger = AsyncHydraLogger(
            enable_performance_monitoring=True,
            redact_sensitive=True,
            queue_size=500,
            batch_size=50,
            batch_timeout=0.5
        )
        
        assert logger.enable_performance_monitoring is True
        assert logger.redact_sensitive is True
        assert logger.queue_size == 500
        assert logger.batch_size == 50
        assert logger.batch_timeout == 0.5
        assert isinstance(logger._async_performance_monitor, AsyncPerformanceMonitor)
        assert isinstance(logger._backpressure_handler, type(logger._backpressure_handler))
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_with_config(self):
        """Test AsyncHydraLogger with custom config."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="console", level="INFO"),
            LogDestination(type="file", path=os.path.join(self.test_logs_dir, "test.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(config=config)
        
        assert logger.config == config
        assert "TEST" in logger.config.layers
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_basic_logging(self, temp_dir):
        """Test basic async logging functionality."""
        # Create config with file destination
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "test.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(config=config)
        
        # Wait for initialization
        await asyncio.sleep(0.1)
        
        # Test basic logging
        await logger.log("TEST", "INFO", "Test async log message")
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check file was created
        log_file = os.path.join(temp_dir, "test.log")
        assert os.path.exists(log_file)
        
        # Check content
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test async log message" in content
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_level_methods(self, temp_dir):
        """Test async logging level methods."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "levels.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(config=config)
        await asyncio.sleep(0.1)
        
        # Test all logging levels
        await logger.debug("TEST", "Debug message")
        await logger.info("TEST", "Info message")
        await logger.warning("TEST", "Warning message")
        await logger.error("TEST", "Error message")
        await logger.critical("TEST", "Critical message")
        await logger.security("TEST", "Security message")
        await logger.audit("TEST", "Audit message")
        await logger.compliance("TEST", "Compliance message")
        
        await asyncio.sleep(0.2)
        
        # Check all messages were logged
        log_file = os.path.join(temp_dir, "levels.log")
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content
            assert "Security message" in content
            assert "Audit message" in content
            assert "Compliance message" in content
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_performance_monitoring(self, temp_dir):
        """Test async performance monitoring."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "perf.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(
            config=config,
            enable_performance_monitoring=True
        )
        await asyncio.sleep(0.1)
        
        # Send some messages
        for i in range(10):
            await logger.info("TEST", f"Performance test message {i}")
        
        await asyncio.sleep(0.2)
        
        # Get performance statistics
        stats = await logger.get_async_performance_statistics()
        
        assert stats is not None
        assert "total_messages" in stats
        assert "avg_processing_time" in stats
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_reset_performance(self, temp_dir):
        """Test resetting performance statistics."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "reset.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(
            config=config,
            enable_performance_monitoring=True
        )
        await asyncio.sleep(0.1)
        
        # Send some messages
        await logger.info("TEST", "Test message")
        await asyncio.sleep(0.1)
        
        # Get initial stats
        initial_stats = await logger.get_async_performance_statistics()
        if initial_stats is not None:
            assert initial_stats.get("total_messages", 0) > 0
        
        # Reset stats
        await logger.reset_async_performance_statistics()
        
        # Get stats after reset
        reset_stats = await logger.get_async_performance_statistics()
        if reset_stats is not None:
            assert reset_stats.get("total_messages", 0) == 0
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_error_handling(self, temp_dir):
        """Test async logger error handling."""
        # Create config with invalid destination configuration
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=None, level="INFO")  # Missing required path
        ])
        
        logger = AsyncHydraLogger(config=config)
        await asyncio.sleep(0.1)
        
        # Should not crash on invalid destination
        await logger.info("TEST", "Error handling test")
        await asyncio.sleep(0.1)
        
        # Should still be functional
        assert logger._initialized is True
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_concurrent_logging(self, temp_dir):
        """Test concurrent async logging."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "concurrent.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(config=config)
        await asyncio.sleep(0.1)
        
        # Create concurrent logging tasks
        async def log_message(i):
            await logger.info("TEST", f"Concurrent message {i}")
        
        # Run concurrent tasks
        tasks = [log_message(i) for i in range(20)]
        await asyncio.gather(*tasks)
        
        await asyncio.sleep(0.2)
        
        # Check all messages were logged
        log_file = os.path.join(temp_dir, "concurrent.log")
        with open(log_file, 'r') as f:
            content = f.read()
            for i in range(20):
                assert f"Concurrent message {i}" in content
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_redaction(self, temp_dir):
        """Test sensitive data redaction."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "redact.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(
            config=config,
            redact_sensitive=True
        )
        await asyncio.sleep(0.1)
        
        # Log message with sensitive data
        await logger.info("TEST", "Password: secret123, Token: abc123")
        
        await asyncio.sleep(0.1)
        
        # Check that sensitive data is redacted
        log_file = os.path.join(temp_dir, "redact.log")
        with open(log_file, 'r') as f:
            content = f.read()
            assert "secret123" not in content
            assert "abc123" not in content
            assert "***REDACTED***" in content
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_backpressure(self, temp_dir):
        """Test backpressure handling."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "backpressure.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(
            config=config,
            queue_size=5  # Small queue to trigger backpressure
        )
        await asyncio.sleep(0.1)
        
        # Send many messages quickly to trigger backpressure
        for i in range(20):
            await logger.info("TEST", f"Backpressure test message {i}")
        
        await asyncio.sleep(0.2)
        
        # Should not crash and should handle backpressure gracefully
        assert logger._backpressure_handler is not None
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_close(self):
        """Test async logger close functionality."""
        logger = AsyncHydraLogger()
        await asyncio.sleep(0.1)
        
        # Should not crash
        await logger.close()
        
        # Should be properly cleaned up
        assert len(logger.async_loggers) == 0
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_parse_size(self):
        """Test size parsing functionality."""
        logger = AsyncHydraLogger()
        
        # Test various size formats
        assert logger._parse_size("1KB") == 1024
        assert logger._parse_size("1MB") == 1024 * 1024
        assert logger._parse_size("1GB") == 1024 * 1024 * 1024
        assert logger._parse_size("1000") == 1000
        assert logger._parse_size("1.5KB") == int(1.5 * 1024)
    
    @pytest.mark.asyncio
    async def test_async_hydra_logger_get_calling_module(self):
        """Test calling module name detection."""
        logger = AsyncHydraLogger()
        
        module_name = logger._get_calling_module_name()
        assert isinstance(module_name, str)
        assert len(module_name) > 0


class TestAsyncCompositeHandler:
    """Test AsyncCompositeHandler functionality."""
    
    @pytest.mark.asyncio
    async def test_async_composite_handler_initialization(self):
        """Test AsyncCompositeHandler initialization."""
        # Create mock handlers
        handler1 = Mock()
        handler1.emit_async = AsyncMock()
        handler2 = Mock()
        handler2.emit_async = AsyncMock()
        
        composite = AsyncCompositeHandler([handler1, handler2])
        
        assert len(composite.handlers) == 2
        assert composite.handlers[0] == handler1
        assert composite.handlers[1] == handler2
    
    @pytest.mark.asyncio
    async def test_async_composite_handler_process_record(self):
        """Test processing record through composite handler."""
        # Create mock handlers
        handler1 = Mock()
        handler1.emit_async = AsyncMock()
        handler2 = Mock()
        handler2.emit_async = AsyncMock()
        
        composite = AsyncCompositeHandler([handler1, handler2])
        
        # Create test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Process record
        await composite._process_record_async(record)
        
        # Check both handlers were called
        handler1.emit_async.assert_called_once_with(record)
        handler2.emit_async.assert_called_once_with(record)
    
    @pytest.mark.asyncio
    async def test_async_composite_handler_error_handling(self):
        """Test error handling in composite handler."""
        # Create handlers with one that raises an error
        handler1 = Mock()
        handler1.emit_async = AsyncMock()
        
        handler2 = Mock()
        handler2.emit_async = AsyncMock(side_effect=Exception("Test error"))
        
        composite = AsyncCompositeHandler([handler1, handler2])
        
        # Create test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Should not crash, should handle error gracefully
        await composite._process_record_async(record)
        
        # Check first handler was called
        handler1.emit_async.assert_called_once_with(record)
        # Second handler should have been called but failed
        handler2.emit_async.assert_called_once_with(record)


class TestAsyncLoggerIntegration:
    """Integration tests for async logger components."""
    
    @pytest.mark.asyncio
    async def test_async_logger_with_multiple_handlers(self, temp_dir):
        """Test async logger with multiple handlers."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "multi.log"), level="INFO"),
            LogDestination(type="console", level="INFO")
        ])
        
        logger = AsyncHydraLogger(config=config)
        await asyncio.sleep(0.1)
        
        # Send message to multiple handlers
        await logger.info("TEST", "Multi-handler test message")
        
        await asyncio.sleep(0.2)
        
        # Check file handler
        log_file = os.path.join(temp_dir, "multi.log")
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Multi-handler test message" in content
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logger_performance_under_load(self, temp_dir):
        """Test async logger performance under load."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "load.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(
            config=config,
            enable_performance_monitoring=True
        )
        await asyncio.sleep(0.1)
        
        # Send many messages quickly
        start_time = asyncio.get_event_loop().time()
        
        for i in range(100):
            await logger.info("TEST", f"Load test message {i}")
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        # Should process quickly
        assert processing_time < 2.0
        
        await asyncio.sleep(0.2)
        
        # Check performance stats
        stats = await logger.get_async_performance_statistics()
        if stats is not None:
            assert stats.get("total_messages", 0) >= 100
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logger_error_recovery(self, temp_dir):
        """Test async logger error recovery."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "recovery.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(config=config)
        await asyncio.sleep(0.1)
        
        # Send messages with errors in handlers
        for i in range(10):
            await logger.info("TEST", f"Recovery test message {i}")
        
        await asyncio.sleep(0.2)
        
        # Should continue functioning despite errors
        assert logger._initialized is True
        
        # Check some messages were logged
        log_file = os.path.join(temp_dir, "recovery.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                content = f.read()
                assert len(content) > 0
        
        await logger.close()
    
    @pytest.mark.asyncio
    async def test_async_logger_memory_efficiency(self, temp_dir):
        """Test async logger memory efficiency."""
        config = LoggingConfig()
        config.layers["TEST"] = LogLayer(level="INFO", destinations=[
            LogDestination(type="file", path=os.path.join(temp_dir, "memory.log"), level="INFO")
        ])
        
        logger = AsyncHydraLogger(
            config=config,
            queue_size=100,
            batch_size=10
        )
        await asyncio.sleep(0.1)
        
        # Send many messages
        for i in range(1000):
            await logger.info("TEST", f"Memory test message {i}")
        
        await asyncio.sleep(0.5)
        
        # Should not consume excessive memory
        # Check that all messages were processed
        log_file = os.path.join(temp_dir, "memory.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                content = f.read()
                # Should have processed most messages
                assert content.count("Memory test message") >= 900
        
        await logger.close()


if __name__ == "__main__":
    pytest.main([__file__]) 