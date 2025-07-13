"""
Comprehensive tests for AsyncFileHandler.

Tests include:
- Basic async file logging
- Queue overflow and backpressure
- Memory pressure scenarios
- Safe shutdown with pending messages
- Sync fallback when async fails
- Error handling and recovery
"""

import asyncio
import os
import tempfile
import time
import pytest
import logging

from hydra_logger.async_hydra.handlers.file_handler import AsyncFileHandler


class TestAsyncFileHandler:
    """Test suite for AsyncFileHandler."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_filename = f.name
        
        yield temp_filename
        
        # Cleanup
        try:
            os.unlink(temp_filename)
        except OSError:
            pass
    
    @pytest.fixture
    def async_handler(self, temp_file):
        """Create an AsyncFileHandler instance."""
        handler = AsyncFileHandler(
            filename=temp_file,
            max_queue_size=10,  # Small queue for testing
            memory_threshold=90.0
        )
        return handler
    
    @pytest.mark.asyncio
    async def test_basic_async_logging(self, async_handler, temp_file):
        """Test basic async file logging functionality."""
        await async_handler.initialize()
        
        # Create a test record
        record = logging.LogRecord(
            name='test',
            level=logging.INFO,
            pathname='',
            lineno=0,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Log asynchronously
        await async_handler.emit_async(record)
        
        # Wait a bit for the writer to process
        await asyncio.sleep(0.1)
        
        # Check if file was written
        assert os.path.exists(temp_file)
        
        with open(temp_file, 'r') as f:
            content = f.read()
            assert 'Test message' in content
        
        await async_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_multiple_messages(self, async_handler, temp_file):
        """Test logging multiple messages."""
        await async_handler.initialize()
        
        # Log multiple messages
        for i in range(5):
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f'Message {i}',
                args=(),
                exc_info=None
            )
            await async_handler.emit_async(record)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check file content
        with open(temp_file, 'r') as f:
            content = f.read()
            for i in range(5):
                assert f'Message {i}' in content
        
        await async_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_queue_overflow(self, async_handler, temp_file):
        """Test queue overflow and backpressure handling."""
        await async_handler.initialize()
        
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
            await async_handler.emit_async(record)
        
        # Wait for processing
        await asyncio.sleep(0.3)
        
        # Check health status
        health = async_handler.get_health_status()
        assert 'queue_stats' in health
        
        await async_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_sync_fallback(self, async_handler, temp_file):
        """Test sync fallback when async operations fail."""
        await async_handler.initialize()
        
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
        async_handler._write_record_sync(record)
        
        # Check if file was written
        with open(temp_file, 'r') as f:
            content = f.read()
            assert 'Sync fallback test' in content
        
        await async_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_safe_shutdown(self, async_handler, temp_file):
        """Test safe shutdown with pending messages."""
        await async_handler.initialize()
        
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
            await async_handler.emit_async(record)
        
        # Shutdown immediately (messages should still be processed)
        await async_handler.aclose()
        
        # Check if messages were written during shutdown
        with open(temp_file, 'r') as f:
            content = f.read()
            for i in range(5):
                assert f'Shutdown test {i}' in content
    
    @pytest.mark.asyncio
    async def test_error_handling(self, async_handler, temp_file):
        """Test error handling and recovery."""
        await async_handler.initialize()
        
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
        await async_handler._error_tracker.record_error("test_error", Exception("Test error"))
        
        # Check error stats
        error_stats = async_handler.get_error_stats()
        assert error_stats['total_errors'] > 0
        
        await async_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, async_handler, temp_file):
        """Test health monitoring functionality."""
        await async_handler.initialize()
        
        # Get health status
        health = async_handler.get_health_status()
        
        # Check required fields
        assert 'filename' in health
        assert 'file_exists' in health
        assert 'queue_stats' in health
        assert 'memory_stats' in health
        assert 'writer_running' in health
        assert 'aiofiles_available' in health
        
        # Check if handler is healthy
        assert async_handler.is_healthy()
        
        await async_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_memory_pressure(self, async_handler, temp_file):
        """Test behavior under memory pressure."""
        await async_handler.initialize()
        
        # Simulate memory pressure by setting a very low threshold
        async_handler._memory_monitor.set_threshold(1.0)  # 1% threshold
        
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
        await async_handler.emit_async(record)
        
        # Check sync fallback count
        health = async_handler.get_health_status()
        assert health['sync_fallbacks'] > 0
        
        await async_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, async_handler, temp_file):
        """Test concurrent access to the handler."""
        await async_handler.initialize()
        
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
            await async_handler.emit_async(record)
        
        # Run multiple concurrent tasks
        tasks = [log_message(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # Check that all messages were written
        with open(temp_file, 'r') as f:
            content = f.read()
            for i in range(10):
                assert f'Concurrent message {i}' in content
        
        await async_handler.aclose()
    
    def test_sync_close(self, async_handler, temp_file):
        """Test synchronous close method."""
        # Test sync close without async initialization
        async_handler.close()
        
        # Should not raise any exceptions
        assert True


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 