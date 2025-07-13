"""
Comprehensive tests for AsyncConsoleHandler.

Tests include:
- Basic async console logging
- Color support and formatting
- Queue overflow and backpressure
- Memory pressure scenarios
- Safe shutdown with pending messages
- Sync fallback when async fails
- Error handling and recovery
- Concurrent access patterns
"""

import asyncio
import io
import sys
import time
import pytest
import logging

from hydra_logger.async_hydra.handlers.console_handler import AsyncConsoleHandler


class TestAsyncConsoleHandler:
    """Test suite for AsyncConsoleHandler."""
    
    @pytest.fixture
    def console_stream(self):
        """Create a string stream for testing console output."""
        return io.StringIO()
    
    @pytest.fixture
    def async_console_handler(self, console_stream):
        """Create an AsyncConsoleHandler instance."""
        handler = AsyncConsoleHandler(
            stream=console_stream,
            max_queue_size=10,  # Small queue for testing
            memory_threshold=90.0,
            use_colors=False  # Disable colors for testing
        )
        return handler
    
    @pytest.mark.asyncio
    async def test_basic_async_console_logging(self, async_console_handler, console_stream):
        """Test basic async console logging functionality."""
        await async_console_handler.initialize()
        
        # Create a test record
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test console message',
            args=(),
            exc_info=None
        )
        
        # Log asynchronously
        await async_console_handler.emit_async(record)
        
        # Wait for writer to process using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Check if message was written to stream
        console_stream.seek(0)
        content = console_stream.read()
        assert 'Test console message' in content
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_multiple_messages(self, async_console_handler, console_stream):
        """Test logging multiple messages."""
        await async_console_handler.initialize()
        
        # Log multiple messages
        for i in range(5):
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f'Console message {i}',
                args=(),
                exc_info=None
            )
            await async_console_handler.emit_async(record)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Check stream content
        console_stream.seek(0)
        content = console_stream.read()
        for i in range(5):
            assert f'Console message {i}' in content
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_color_support(self):
        """Test color support functionality."""
        # Create handler with colors enabled
        console_stream = io.StringIO()
        handler = AsyncConsoleHandler(
            stream=console_stream,
            use_colors=True
        )
        
        await handler.initialize()
        
        # Test different log levels with colors
        levels = [
            (logging.DEBUG, 'debug message'),
            (logging.INFO, 'info message'),
            (logging.WARNING, 'warning message'),
            (logging.ERROR, 'error message'),
            (logging.CRITICAL, 'critical message')
        ]
        
        for level, message in levels:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='',
                lineno=0,
                msg=message,
                args=(),
                exc_info=None
            )
            await handler.emit_async(record)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(handler)
        
        # Check that messages were written (colors may not be visible in StringIO)
        console_stream.seek(0)
        content = console_stream.read()
        for _, message in levels:
            assert message in content
        
        # Check health status for color usage
        health = handler.get_health_status()
        assert 'color_usage' in health
        assert 'use_colors' in health
        assert 'colorama_available' in health
        
        await handler.aclose()
    
    @pytest.mark.asyncio
    async def test_queue_overflow(self, async_console_handler, console_stream):
        """Test queue overflow and backpressure handling."""
        await async_console_handler.initialize()
        
        # Fill the queue beyond capacity
        for i in range(15):  # More than max_queue_size (10)
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f'Overflow message {i}',
                args=(),
                exc_info=None
            )
            await async_console_handler.emit_async(record)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Check health status
        health = async_console_handler.get_health_status()
        assert 'queue_stats' in health
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_sync_fallback(self, async_console_handler, console_stream):
        """Test sync fallback when async operations fail."""
        await async_console_handler.initialize()
        
        # Create a record
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Sync fallback test',
            args=(),
            exc_info=None
        )
        
        # Test sync fallback
        async_console_handler._write_record_sync(record)
        
        # Check if message was written
        console_stream.seek(0)
        content = console_stream.read()
        assert 'Sync fallback test' in content
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_safe_shutdown(self, async_console_handler, console_stream):
        """Test safe shutdown with pending messages."""
        await async_console_handler.initialize()
        
        # Add some messages to the queue
        for i in range(5):
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f'Shutdown test {i}',
                args=(),
                exc_info=None
            )
            await async_console_handler.emit_async(record)
        
        # Shutdown immediately (messages should still be processed)
        await async_console_handler.aclose()
        
        # Check if messages were written during shutdown
        console_stream.seek(0)
        content = console_stream.read()
        for i in range(5):
            assert f'Shutdown test {i}' in content
    
    @pytest.mark.asyncio
    async def test_error_handling(self, async_console_handler, console_stream):
        """Test error handling and recovery."""
        await async_console_handler.initialize()
        
        # Create a record that might cause issues
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Error handling test',
            args=(),
            exc_info=None
        )
        
        # Test error recording
        await async_console_handler._error_tracker.record_error("test_error", Exception("Test error"))
        
        # Check error stats
        error_stats = async_console_handler.get_error_stats()
        assert error_stats['total_errors'] > 0
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, async_console_handler, console_stream):
        """Test health monitoring functionality."""
        await async_console_handler.initialize()
        
        # Get health status
        health = async_console_handler.get_health_status()
        
        # Check required fields
        assert 'stream_name' in health
        assert 'use_colors' in health
        assert 'colorama_available' in health
        assert 'queue_stats' in health
        assert 'memory_stats' in health
        assert 'writer_running' in health
        
        # Check if handler is healthy
        assert async_console_handler.is_healthy()
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_memory_pressure(self, async_console_handler, console_stream):
        """Test behavior under memory pressure."""
        await async_console_handler.initialize()
        
        # Simulate memory pressure by setting a very low threshold
        async_console_handler._memory_monitor.set_threshold(1.0)  # 1% threshold
        
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Memory pressure test',
            args=(),
            exc_info=None
        )
        
        # This should trigger sync fallback due to memory pressure
        await async_console_handler.emit_async(record)
        
        # Check sync fallback count
        health = async_console_handler.get_health_status()
        assert health['sync_fallbacks'] > 0
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, async_console_handler, console_stream):
        """Test concurrent access to the handler."""
        await async_console_handler.initialize()
        
        # Create multiple concurrent logging tasks
        async def log_message(i):
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f'Concurrent message {i}',
                args=(),
                exc_info=None
            )
            await async_console_handler.emit_async(record)
        
        # Run multiple concurrent tasks
        tasks = [log_message(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Ensure all messages are flushed by closing the handler
        await async_console_handler.aclose()
        
        # Check that all messages were written
        console_stream.seek(0)
        content = console_stream.read()
        for i in range(10):
            assert f'Concurrent message {i}' in content
    
    @pytest.mark.asyncio
    async def test_stream_switching(self, async_console_handler):
        """Test switching output streams."""
        await async_console_handler.initialize()
        
        # Create a new stream
        new_stream = io.StringIO()
        
        # Switch streams
        async_console_handler.set_stream(new_stream)
        
        # Log a message
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Stream switch test',
            args=(),
            exc_info=None
        )
        await async_console_handler.emit_async(record)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Check that message went to new stream
        new_stream.seek(0)
        content = new_stream.read()
        assert 'Stream switch test' in content
        
        await async_console_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_color_toggle(self, async_console_handler, console_stream):
        """Test enabling and disabling colors."""
        await async_console_handler.initialize()
        
        # Test with colors disabled (default)
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Color test disabled',
            args=(),
            exc_info=None
        )
        await async_console_handler.emit_async(record)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Check health status
        health = async_console_handler.get_health_status()
        assert 'use_colors' in health
        assert 'colorama_available' in health
        
        # Test enabling colors
        async_console_handler.set_use_colors(True)
        
        record2 = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Color test enabled',
            args=(),
            exc_info=None
        )
        await async_console_handler.emit_async(record2)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Check that color usage increased
        health2 = async_console_handler.get_health_status()
        assert health2['color_usage'] >= health['color_usage']
        
        await async_console_handler.aclose()
    
    async def _wait_for_writer(self, handler):
        """Wait for writer to process using proper async patterns."""
        # Wait for queue to be empty and writer to finish
        for _ in range(100):
            if handler._queue.empty():
                break
            await asyncio.sleep(0.01)
    
    def test_sync_close(self, async_console_handler, console_stream):
        """Test synchronous close method."""
        # Test sync close without async initialization
        async_console_handler.close()
        
        # Should not raise any exceptions
        assert True
    
    @pytest.mark.asyncio
    async def test_different_log_levels(self, async_console_handler, console_stream):
        """Test different log levels."""
        await async_console_handler.initialize()
        
        levels = [
            (logging.DEBUG, 'debug'),
            (logging.INFO, 'info'),
            (logging.WARNING, 'warning'),
            (logging.ERROR, 'error'),
            (logging.CRITICAL, 'critical')
        ]
        
        for level, level_name in levels:
            record = logging.LogRecord(
                name='test',
                level=level,
                pathname='',
                lineno=0,
                msg=f'{level_name} message',
                args=(),
                exc_info=None
            )
            await async_console_handler.emit_async(record)
        
        # Wait for processing using proper async pattern
        await self._wait_for_writer(async_console_handler)
        
        # Check that all levels were written
        console_stream.seek(0)
        content = console_stream.read()
        for _, level_name in levels:
            assert f'{level_name} message' in content
        
        await async_console_handler.aclose()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 