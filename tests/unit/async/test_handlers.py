"""
Comprehensive tests for async handlers.

This module provides extensive test coverage for all async handler
components including edge cases, error conditions, and performance scenarios.
"""

import asyncio
import logging
import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from hydra_logger.async_hydra.async_handlers import (
    AsyncLogHandler,
    AsyncRotatingFileHandler,
    AsyncStreamHandler,
    AsyncBufferedRotatingFileHandler
)


class TestAsyncHandler(AsyncLogHandler):
    """Concrete test implementation of AsyncLogHandler."""
    
    async def _process_record_async(self, record: logging.LogRecord) -> None:
        """Test implementation of abstract method."""
        msg = self.format(record)
        print(f"TEST_HANDLER: {msg}")


class TestAsyncLogHandler:
    """Test AsyncLogHandler base class."""
    
    @pytest.mark.asyncio
    async def test_async_handler_initialization(self):
        """Test AsyncLogHandler initialization."""
        handler = TestAsyncHandler(level=logging.INFO, queue_size=100)
        
        assert handler.level == logging.INFO
        assert handler._queue.maxsize == 100
        assert not handler._running
    
    @pytest.mark.asyncio
    async def test_async_handler_start_stop(self):
        """Test async handler start and stop operations."""
        handler = TestAsyncHandler()
        
        # Start handler
        await handler.start()
        assert handler._running is True
        
        # Stop handler
        await handler.stop()
        assert handler._running is False
    
    @pytest.mark.asyncio
    async def test_async_handler_double_start_stop(self):
        """Test double start and stop operations."""
        handler = TestAsyncHandler()
        
        # Double start
        await handler.start()
        await handler.start()  # Should be no-op
        assert handler._running is True
        
        # Double stop
        await handler.stop()
        await handler.stop()  # Should be no-op
        assert handler._running is False
    
    @pytest.mark.asyncio
    async def test_async_handler_emit_sync(self):
        """Test synchronous emit method."""
        handler = TestAsyncHandler()
        await handler.start()
        
        try:
            # Create log record
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Test sync emit
            handler.emit(record)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_handler_emit_async(self):
        """Test asynchronous emit method."""
        handler = TestAsyncHandler()
        await handler.start()
        
        try:
            # Create log record
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Test async emit
            await handler.emit_async(record)
            
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_handler_worker_error_handling(self):
        """Test worker error handling."""
        handler = TestAsyncHandler()
        await handler.start()
        
        try:
            # Mock queue.get to raise exception
            with patch.object(handler._queue, 'get', side_effect=Exception("Queue error")):
                # Worker should handle exception gracefully
                await asyncio.sleep(0.1)
                assert handler._running is True
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_handler_worker_cancellation(self):
        """Test worker task cancellation."""
        handler = TestAsyncHandler()
        await handler.start()
        
        # Cancel worker task
        if handler._worker_task:
            handler._worker_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await handler._worker_task
        
        await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_handler_no_event_loop(self):
        """Test handler behavior when no event loop is running."""
        handler = TestAsyncHandler()
        
        # Test start without event loop
        with patch('asyncio.get_running_loop', side_effect=RuntimeError("No loop")):
            await handler.start()
            assert handler._running is True
    
    @pytest.mark.asyncio
    async def test_async_handler_close(self):
        """Test handler close method."""
        handler = TestAsyncHandler()
        await handler.start()
        
        # Test close
        handler.close()
        assert handler._running is False


class TestAsyncRotatingFileHandler:
    """Test AsyncRotatingFileHandler."""
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.mark.asyncio
    async def test_async_rotating_file_handler_initialization(self, temp_file):
        """Test AsyncRotatingFileHandler initialization."""
        handler = AsyncRotatingFileHandler(
            filename=temp_file,
            maxBytes=1024,
            backupCount=3
        )
        
        assert handler.filename == temp_file
        assert handler.maxBytes == 1024
        assert handler.backupCount == 3
        assert handler.encoding == 'utf-8'
    
    @pytest.mark.asyncio
    async def test_async_rotating_file_handler_write(self, temp_file):
        """Test async file writing."""
        handler = AsyncRotatingFileHandler(filename=temp_file)
        await handler.start()
        
        try:
            # Create log record
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Test async emit
            await handler.emit_async(record)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Check file content
            with open(temp_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
                
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_rotating_file_handler_rotation(self, temp_file):
        """Test file rotation functionality."""
        # Create handler with small max size
        handler = AsyncRotatingFileHandler(
            filename=temp_file,
            maxBytes=50,  # Small size to trigger rotation
            backupCount=2
        )
        await handler.start()
        
        try:
            # Write large message to trigger rotation
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="This is a very long message that should trigger file rotation",
                args=(),
                exc_info=None
            )
            
            await handler.emit_async(record)
            await asyncio.sleep(0.1)
            
            # Check if backup file was created
            backup_file = f"{temp_file}.1"
            assert os.path.exists(backup_file)
            
            # Cleanup backup
            try:
                os.unlink(backup_file)
            except OSError:
                pass
                
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_rotating_file_handler_write_error(self, temp_file):
        """Test file write error handling."""
        handler = AsyncRotatingFileHandler(filename=temp_file)
        await handler.start()
        
        try:
            # Mock file write to raise exception
            with patch('builtins.open', side_effect=OSError("Write error")):
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg="Test message",
                    args=(),
                    exc_info=None
                )
                
                # Should handle error gracefully
                await handler.emit_async(record)
                
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_rotating_file_handler_rotation_error(self, temp_file):
        """Test file rotation error handling."""
        handler = AsyncRotatingFileHandler(
            filename=temp_file,
            maxBytes=50,
            backupCount=2
        )
        await handler.start()
        
        try:
            # Mock os.rename to raise exception
            with patch('os.rename', side_effect=OSError("Rotation error")):
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg="Long message to trigger rotation",
                    args=(),
                    exc_info=None
                )
                
                # Should handle rotation error gracefully
                await handler.emit_async(record)
                
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_rotating_file_handler_without_aiofiles(self, temp_file):
        """Test handler without aiofiles dependency."""
        # Mock aiofiles as unavailable
        with patch('hydra_logger.async_hydra.async_handlers.AIOFILES_AVAILABLE', False):
            handler = AsyncRotatingFileHandler(filename=temp_file)
            await handler.start()
            
            try:
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg="Test message",
                    args=(),
                    exc_info=None
                )
                
                await handler.emit_async(record)
                await asyncio.sleep(0.1)
                
                # Check file content
                with open(temp_file, 'r') as f:
                    content = f.read()
                    assert "Test message" in content
                    
            finally:
                await handler.stop()


class TestAsyncStreamHandler:
    """Test AsyncStreamHandler."""
    
    @pytest.mark.asyncio
    async def test_async_stream_handler_initialization(self):
        """Test AsyncStreamHandler initialization."""
        handler = AsyncStreamHandler(
            stream=sys.stdout,
            use_colors=True,
            buffer_size=1024
        )
        
        assert handler.stream == sys.stdout
        assert handler.use_colors is True
        assert handler.buffer_size == 1024
    
    @pytest.mark.asyncio
    async def test_async_stream_handler_write(self):
        """Test async stream writing."""
        handler = AsyncStreamHandler()
        await handler.start()
        
        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            await handler.emit_async(record)
            await asyncio.sleep(0.1)
            
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_stream_handler_buffer_flush(self):
        """Test buffer flushing functionality."""
        handler = AsyncStreamHandler(buffer_size=10)  # Small buffer
        await handler.start()
        
        try:
            # Add message that exceeds buffer size
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Long message that exceeds buffer size",
                args=(),
                exc_info=None
            )
            
            await handler.emit_async(record)
            await asyncio.sleep(0.1)
            
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_stream_handler_flush_error(self):
        """Test buffer flush error handling."""
        handler = AsyncStreamHandler()
        await handler.start()
        
        try:
            # Mock stream.write to raise exception
            with patch.object(handler.stream, 'write', side_effect=OSError("Write error")):
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg="Test message",
                    args=(),
                    exc_info=None
                )
                
                # Should handle error gracefully
                await handler.emit_async(record)
                
        finally:
            await handler.stop()


class TestAsyncBufferedRotatingFileHandler:
    """Test AsyncBufferedRotatingFileHandler."""
    
    @pytest.fixture
    def temp_file(self):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.mark.asyncio
    async def test_async_buffered_rotating_file_handler_initialization(self, temp_file):
        """Test AsyncBufferedRotatingFileHandler initialization."""
        handler = AsyncBufferedRotatingFileHandler(
            filename=temp_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=512,
            flush_interval=0.5
        )
        
        assert handler.filename == temp_file
        assert handler.maxBytes == 1024
        assert handler.backupCount == 3
        assert handler.buffer_size == 512
        assert handler.flush_interval == 0.5
    
    @pytest.mark.asyncio
    async def test_async_buffered_rotating_file_handler_write(self, temp_file):
        """Test buffered file writing."""
        handler = AsyncBufferedRotatingFileHandler(
            filename=temp_file,
            buffer_size=100,
            flush_interval=0.1
        )
        await handler.start()
        
        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            await handler.emit_async(record)
            await asyncio.sleep(0.2)  # Wait for flush
            
            # Check file content
            with open(temp_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
                
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_buffered_rotating_file_handler_buffer_overflow(self, temp_file):
        """Test buffer overflow handling."""
        handler = AsyncBufferedRotatingFileHandler(
            filename=temp_file,
            buffer_size=10,  # Small buffer
            flush_interval=1.0  # Long flush interval
        )
        await handler.start()
        
        try:
            # Add message that exceeds buffer size
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Long message that exceeds buffer size",
                args=(),
                exc_info=None
            )
            
            await handler.emit_async(record)
            await asyncio.sleep(0.1)
            
            # Should flush immediately due to buffer overflow
            
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_buffered_rotating_file_handler_flush_error(self, temp_file):
        """Test buffer flush error handling."""
        handler = AsyncBufferedRotatingFileHandler(filename=temp_file)
        await handler.start()
        
        try:
            # Mock file write to raise exception
            with patch('builtins.open', side_effect=OSError("Write error")):
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg="Test message",
                    args=(),
                    exc_info=None
                )
                
                # Should handle error gracefully
                await handler.emit_async(record)
                
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_async_buffered_rotating_file_handler_stop_with_buffer(self, temp_file):
        """Test stopping handler with buffered content."""
        handler = AsyncBufferedRotatingFileHandler(
            filename=temp_file,
            buffer_size=1000,  # Large buffer
            flush_interval=10.0  # Long flush interval
        )
        await handler.start()
        
        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            await handler.emit_async(record)
            
            # Stop immediately - should flush buffer
            await handler.stop()
            
            # Check if message was written
            with open(temp_file, 'r') as f:
                content = f.read()
                assert "Test message" in content
                
        finally:
            await handler.stop()


class TestAsyncHandlersIntegration:
    """Integration tests for async handlers."""
    
    @pytest.mark.asyncio
    async def test_multiple_handlers_concurrent(self):
        """Test multiple handlers running concurrently."""
        handlers = []
        
        try:
            # Create multiple handlers
            for i in range(3):
                handler = AsyncStreamHandler()
                await handler.start()
                handlers.append(handler)
            
            # Send messages to all handlers
            for i in range(5):
                record = logging.LogRecord(
                    name=f"test_{i}",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=f"Message {i}",
                    args=(),
                    exc_info=None
                )
                
                for handler in handlers:
                    await handler.emit_async(record)
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # All handlers should still be running
            for handler in handlers:
                assert handler._running is True
                
        finally:
            # Stop all handlers
            for handler in handlers:
                await handler.stop()
    
    @pytest.mark.asyncio
    async def test_handler_performance_under_load(self):
        """Test handler performance under load."""
        handler = AsyncStreamHandler()
        await handler.start()
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Send many messages quickly
            for i in range(100):
                record = logging.LogRecord(
                    name="test",
                    level=logging.INFO,
                    pathname="",
                    lineno=0,
                    msg=f"Message {i}",
                    args=(),
                    exc_info=None
                )
                await handler.emit_async(record)
            
            # Wait for processing
            await asyncio.sleep(0.5)
            
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            # Should process quickly
            assert processing_time < 2.0
            
        finally:
            await handler.stop()
    
    @pytest.mark.asyncio
    async def test_handler_error_recovery(self):
        """Test handler error recovery."""
        error_count = 0
        
        async def error_processor(record):
            nonlocal error_count
            error_count += 1
            if error_count < 3:
                raise Exception("Temporary error")
        
        handler = AsyncStreamHandler()
        handler._process_record_async = error_processor
        await handler.start()
        
        try:
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test message",
                args=(),
                exc_info=None
            )
            
            # Send multiple messages
            for i in range(5):
                await handler.emit_async(record)
            
            await asyncio.sleep(0.2)
            
            # Handler should still be running despite errors
            assert handler._running is True
            
        finally:
            await handler.stop() 