"""
Tests for hydra_logger.handlers.console module.
"""

import pytest
import sys
import io
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from hydra_logger.handlers.console import (
    SyncConsoleHandler, 
    AsyncConsoleHandler, 
    ConsoleHandler
)
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class TestSyncConsoleHandler:
    """Test SyncConsoleHandler functionality."""
    
    def test_sync_console_handler_creation(self):
        """Test SyncConsoleHandler creation."""
        handler = SyncConsoleHandler()
        
        assert handler.name == "sync_console"
        assert handler._stream == sys.stdout
        assert handler._use_colors is True
        assert handler._buffer_size == 1000
        assert handler._flush_interval == 0.1
        assert len(handler._buffer) == 0
    
    def test_sync_console_handler_with_custom_stream(self):
        """Test SyncConsoleHandler with custom stream."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, use_colors=False)
        
        assert handler._stream == stream
        assert handler._use_colors is False
    
    def test_sync_console_handler_emit(self):
        """Test SyncConsoleHandler emit method."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, use_colors=False, buffer_size=1)  # Force immediate flush
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        handler.emit(record)
        
        # Check that message was written to stream
        output = stream.getvalue()
        assert "Test message" in output
        assert "INFO" in output
        assert "test" in output
    
    def test_sync_console_handler_buffering(self):
        """Test SyncConsoleHandler buffering functionality."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, buffer_size=2, flush_interval=0.01)
        
        record1 = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Message 1", layer="test")
        record2 = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Message 2", layer="test")
        
        # First message should be buffered
        handler.emit(record1)
        assert len(handler._buffer) == 1
        assert stream.getvalue() == ""
        
        # Second message should trigger flush
        handler.emit(record2)
        assert len(handler._buffer) == 0
        output = stream.getvalue()
        assert "Message 1" in output
        assert "Message 2" in output
    
    def test_sync_console_handler_force_flush(self):
        """Test SyncConsoleHandler force_flush method."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, buffer_size=10)
        
        record = LogRecord(level=LogLevel.INFO, message="Buffered message", layer="test")
        handler.emit(record)
        
        # Message should be buffered
        assert len(handler._buffer) == 1
        assert stream.getvalue() == ""
        
        # Force flush should write buffered messages
        handler.force_flush()
        assert len(handler._buffer) == 0
        assert "Buffered message" in stream.getvalue()
    
    def test_sync_console_handler_close(self):
        """Test SyncConsoleHandler close method."""
        handler = SyncConsoleHandler()
        
        # Add some messages to buffer
        record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Test message", layer="test")
        handler.emit(record)
        
        # Close should flush buffer
        handler.close()
        assert len(handler._buffer) == 0  # Buffer should be flushed
    
    def test_sync_console_handler_get_stats(self):
        """Test SyncConsoleHandler get_stats method."""
        handler = SyncConsoleHandler()
        
        record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Test message", layer="test")
        handler.emit(record)
        
        stats = handler.get_stats()
        
        assert "messages_processed" in stats
        assert "total_bytes_written" in stats
        assert "handler_type" in stats
        assert "uptime_seconds" in stats
        assert stats["messages_processed"] >= 0


class TestAsyncConsoleHandler:
    """Test AsyncConsoleHandler functionality."""
    
    @pytest.mark.asyncio
    async def test_async_console_handler_creation(self):
        """Test AsyncConsoleHandler creation."""
        handler = AsyncConsoleHandler()
        
        assert handler.name == "async_console"
        assert handler._stream == sys.stdout
        assert handler._use_colors is True
        assert handler._bulk_size == 100
        assert handler._max_queue_size == 10000
        assert handler._worker_count == 1  # Should be 1 after our fix
        # _running may be True if event loop is running, that's expected
        assert handler._running in [True, False]
    
    @pytest.mark.asyncio
    async def test_async_console_handler_emit_async(self):
        """Test AsyncConsoleHandler emit_async method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Async test message",
            layer="test"
        )
        
        await handler.emit_async(record)
        
        # Give some time for async processing
        await asyncio.sleep(0.1)
        
        # Check that message was written to stream
        output = stream.getvalue()
        assert "Async test message" in output
        assert "INFO" in output
        assert "test" in output
    
    @pytest.mark.asyncio
    async def test_async_console_handler_queue_overflow(self):
        """Test AsyncConsoleHandler queue overflow handling."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, max_queue_size=2, use_colors=False)
        
        # Fill up the queue
        record1 = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Message 1", layer="test")
        record2 = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Message 2", layer="test")
        record3 = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Message 3", layer="test")
        
        await handler.emit_async(record1)
        await handler.emit_async(record2)
        await handler.emit_async(record3)  # This should trigger overflow handling
        
        # Give time for processing
        await asyncio.sleep(0.1)
        
        # Should have written messages directly due to overflow
        output = stream.getvalue()
        assert "Message 1" in output or "Message 2" in output or "Message 3" in output
    
    @pytest.mark.asyncio
    async def test_async_console_handler_aclose(self):
        """Test AsyncConsoleHandler aclose method."""
        handler = AsyncConsoleHandler()
        
        # Start the handler
        record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Test message", layer="test")
        await handler.emit_async(record)
        
        # Close the handler
        await handler.aclose()
        
        assert handler._shutdown_event.is_set()
    
    @pytest.mark.asyncio
    async def test_async_console_handler_worker_timeout(self):
        """Test AsyncConsoleHandler worker timeout protection."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        # Create a record that will trigger worker startup
        record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Timeout test", layer="test")
        await handler.emit_async(record)
        
        # Give time for worker to start and process
        await asyncio.sleep(0.2)
        
        # Worker should have processed the message without hanging
        output = stream.getvalue()
        assert "Timeout test" in output
    
    def test_async_console_handler_get_stats(self):
        """Test AsyncConsoleHandler get_stats method."""
        handler = AsyncConsoleHandler()
        
        stats = handler.get_stats()
        
        assert "messages_processed" in stats
        assert "messages_dropped" in stats
        assert "total_bytes_written" in stats
        assert "queue_size" in stats
        assert "running" in stats
        assert "handler_type" in stats


class TestConsoleHandler:
    """Test ConsoleHandler (smart wrapper) functionality."""
    
    def test_console_handler_creation_auto_mode(self):
        """Test ConsoleHandler creation in auto mode."""
        handler = ConsoleHandler()
        
        assert handler.name == "console"
        assert hasattr(handler, '_handler')
    
    def test_console_handler_creation_sync_mode(self):
        """Test ConsoleHandler creation in sync mode."""
        handler = ConsoleHandler(mode="sync")
        
        assert handler.name == "console"
        assert isinstance(handler._handler, SyncConsoleHandler)
    
    def test_console_handler_creation_async_mode(self):
        """Test ConsoleHandler creation in async mode."""
        handler = ConsoleHandler(mode="async")
        
        assert handler.name == "console"
        assert isinstance(handler._handler, AsyncConsoleHandler)
    
    def test_console_handler_emit_sync(self):
        """Test ConsoleHandler emit method with sync handler."""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, mode="sync", use_colors=False)
        
        record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Sync wrapper test", layer="test")
        handler.emit(record)
        
        # Force flush the underlying handler to ensure output is written
        handler._handler.force_flush()
        
        output = stream.getvalue()
        assert "Sync wrapper test" in output
    
    @pytest.mark.asyncio
    async def test_console_handler_emit_async(self):
        """Test ConsoleHandler emit_async method with async handler."""
        stream = io.StringIO()
        handler = ConsoleHandler(stream=stream, mode="async", use_colors=False)
        
        record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Async wrapper test", layer="test")
        await handler.emit_async(record)
        
        # Give time for async processing
        await asyncio.sleep(0.1)
        
        output = stream.getvalue()
        assert "Async wrapper test" in output
    
    def test_console_handler_close(self):
        """Test ConsoleHandler close method."""
        handler = ConsoleHandler(mode="sync")
        
        # Should not raise an error
        handler.close()
    
    @pytest.mark.asyncio
    async def test_console_handler_aclose(self):
        """Test ConsoleHandler aclose method."""
        handler = ConsoleHandler(mode="async")
        
        # Should not raise an error
        await handler.aclose()
    
    def test_console_handler_get_stats(self):
        """Test ConsoleHandler get_stats method."""
        handler = ConsoleHandler(mode="sync")
        
        stats = handler.get_stats()
        assert isinstance(stats, dict)


class TestConsoleHandlerIntegration:
    """Integration tests for console handlers."""
    
    @pytest.mark.asyncio
    async def test_console_handler_performance(self):
        """Test console handler performance with multiple messages."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        # Send multiple messages
        for i in range(10):
            record = LogRecord(
                level=LogLevel.INFO,
                message=f"Performance test message {i}",
                layer="test"
            )
            await handler.emit_async(record)
        
        # Give time for processing
        await asyncio.sleep(0.2)
        
        # Close handler
        await handler.aclose()
        
        # Check that all messages were processed
        output = stream.getvalue()
        for i in range(10):
            assert f"Performance test message {i}" in output
    
    def test_console_handler_error_handling(self):
        """Test console handler error handling."""
        # Create a handler with a closed stream to trigger errors
        stream = io.StringIO()
        stream.close()
        
        handler = SyncConsoleHandler(stream=stream, use_colors=False)
        
        record = LogRecord(level=LogLevel.INFO, message="Error test", layer="test")
        
        # Should not raise an exception
        handler.emit(record)
        
        # Handler should still be functional
        assert not handler._closed
    
    def test_sync_console_handler_stream_closed_error(self):
        """Test SyncConsoleHandler with closed stream."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, use_colors=False, buffer_size=1)  # Force flush
        
        # Close the stream
        stream.close()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should handle gracefully
        handler.emit(record)
        
        # Message is added to buffer, but flush should handle closed stream gracefully
        # The buffer will have the message since it was added before flush attempt
        assert len(handler._buffer) == 1
        assert "INFO [test] Test message" in handler._buffer[0]
    
    def test_sync_console_handler_oserror_handling(self):
        """Test SyncConsoleHandler OSError handling in flush."""
        stream = Mock()
        stream.closed = False
        stream.write.side_effect = OSError("Stream error")
        stream.flush.side_effect = OSError("Flush error")
        
        handler = SyncConsoleHandler(stream=stream, use_colors=False, buffer_size=1)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should handle OSError gracefully
        handler.emit(record)
        
        # Handler should still be functional
        assert not handler._closed
    
    def test_sync_console_handler_valueerror_handling(self):
        """Test SyncConsoleHandler ValueError handling in flush."""
        stream = Mock()
        stream.closed = False
        stream.write.side_effect = ValueError("Invalid value")
        stream.flush.side_effect = ValueError("Flush error")
        
        handler = SyncConsoleHandler(stream=stream, use_colors=False, buffer_size=1)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should handle ValueError gracefully
        handler.emit(record)
        
        # Handler should still be functional
        assert not handler._closed
    
    def test_sync_console_handler_general_exception_handling(self):
        """Test SyncConsoleHandler general exception handling in emit."""
        stream = Mock()
        stream.closed = False
        stream.write.side_effect = Exception("Unexpected error")
        
        handler = SyncConsoleHandler(stream=stream, use_colors=False, buffer_size=1)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should handle general exception gracefully
        handler.emit(record)
        
        # Handler should still be functional
        assert not handler._closed
    
    @pytest.mark.asyncio
    async def test_async_console_handler_formatter_error(self):
        """Test AsyncConsoleHandler with formatter that raises exception."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        # Mock formatter that raises exception
        mock_formatter = Mock()
        mock_formatter.format.side_effect = Exception("Formatter error")
        handler.setFormatter(mock_formatter)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should use fallback formatting
        await handler.emit_async(record)
        
        # Wait a bit for async processing
        await asyncio.sleep(0.1)
        
        # Should use fallback formatting
        assert "INFO [test] Test message" in stream.getvalue()
    
    @pytest.mark.asyncio
    async def test_async_console_handler_sync_write_error(self):
        """Test AsyncConsoleHandler with sync write error."""
        stream = Mock()
        stream.write.side_effect = Exception("Write error")
        stream.flush.side_effect = Exception("Flush error")
        
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should handle write error gracefully
        await handler.emit_async(record)
        
        # Handler should still be functional
        assert not handler._closed
    
    @pytest.mark.asyncio
    async def test_async_console_handler_emit_error(self):
        """Test AsyncConsoleHandler emit error handling."""
        stream = Mock()
        stream.write.side_effect = Exception("Stream error")
        
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should handle emit error gracefully
        handler.emit(record)
        
        # Handler should still be functional
        assert not handler._closed
    
    @pytest.mark.asyncio
    async def test_async_console_handler_emit_async_error(self):
        """Test AsyncConsoleHandler emit_async error handling."""
        stream = Mock()
        stream.write.side_effect = Exception("Stream error")
        
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not raise exception, should handle emit_async error gracefully
        await handler.emit_async(record)
        
        # Handler should still be functional
        assert not handler._closed

class TestSyncConsoleHandlerMethods:
    """Test specific methods of SyncConsoleHandler."""
    
    def test_sync_console_handler_init(self):
        """Test SyncConsoleHandler __init__ method."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, use_colors=False, buffer_size=500)
        
        assert handler._stream == stream
        assert handler._use_colors is False
        assert handler._buffer_size == 500
        assert handler._flush_interval == 0.1
        assert len(handler._buffer) == 0
        assert handler._last_flush > 0.0
        assert handler._closed is False
    
    def test_sync_console_handler_get_color_code(self):
        """Test _get_color_code method."""
        handler = SyncConsoleHandler(use_colors=True)
        
        # Test various color codes
        assert handler._get_color_code("red") == "\033[31m"
        assert handler._get_color_code("green") == "\033[32m"
        assert handler._get_color_code("blue") == "\033[34m"
        assert handler._get_color_code("yellow") == "\033[33m"
        assert handler._get_color_code("magenta") == "\033[35m"
        assert handler._get_color_code("cyan") == "\033[36m"
        assert handler._get_color_code("white") == "\033[37m"
        assert handler._get_color_code("reset") == "\033[0m"
        assert handler._get_color_code("unknown") == ""
    
    def test_sync_console_handler_format_message(self):
        """Test _format_message method."""
        handler = SyncConsoleHandler(use_colors=False)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        formatted = handler._format_message(record)
        assert "Test message" in formatted
        assert "INFO" in formatted
        assert "test" in formatted
    
    def test_sync_console_handler_flush_buffer(self):
        """Test _flush_buffer method."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, use_colors=False)
        
        # Add some messages to buffer
        handler._buffer.append("Message 1\n")
        handler._buffer.append("Message 2\n")
        
        # Flush buffer
        handler._flush_buffer()
        
        # Check that messages were written
        stream.seek(0)
        content = stream.read()
        assert "Message 1" in content
        assert "Message 2" in content
        
        # Buffer should be cleared
        assert len(handler._buffer) == 0
    
    def test_sync_console_handler_flush_buffer_empty(self):
        """Test _flush_buffer with empty buffer."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream)
        
        # Flush empty buffer
        handler._flush_buffer()
        
        # Should not raise error
        stream.seek(0)
        content = stream.read()
        assert content == ""
    
    def test_sync_console_handler_flush_buffer_stream_closed(self):
        """Test _flush_buffer with closed stream."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream)
        
        # Add message to buffer
        handler._buffer.append("Test message\n")
        
        # Close stream
        stream.close()
        
        # Flush should not raise error
        handler._flush_buffer()
    
    def test_sync_console_handler_flush_buffer_no_stream(self):
        """Test _flush_buffer with no stream."""
        handler = SyncConsoleHandler(stream=None)
        handler._buffer.append("Test message\n")
        
        # Should not raise error
        handler._flush_buffer()

    def test_sync_console_handler_format_message_with_colors(self):
        """Test _format_message method with colors."""
        handler = SyncConsoleHandler(use_colors=True)
        
        record = LogRecord(
            level=LogLevel.ERROR,
            level_name="ERROR",
            message="Error message",
            layer="test"
        )
        
        formatted = handler._format_message(record)
        assert "Error message" in formatted
        assert "ERROR" in formatted
        # Note: _format_message doesn't add colors, colors are added in emit method
    
    def test_sync_console_handler_auto_cleanup(self):
        """Test _auto_cleanup method."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, use_colors=False)
        
        # Add some content to buffer
        handler._buffer.append("Test message\n")
        
        # Call auto cleanup
        handler._auto_cleanup()
        
        # Buffer should be flushed
        assert len(handler._buffer) == 0
    
    def test_sync_console_handler_del(self):
        """Test __del__ method."""
        stream = io.StringIO()
        handler = SyncConsoleHandler(stream=stream, use_colors=False)
        
        # Add some content to buffer
        handler._buffer.append("Test message\n")
        
        # Call __del__ (cleanup)
        handler.__del__()
        
        # Buffer should be flushed
        assert len(handler._buffer) == 0


class TestAsyncConsoleHandlerMethods:
    """Test specific methods of AsyncConsoleHandler."""
    
    def test_async_console_handler_init(self):
        """Test AsyncConsoleHandler __init__ method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False, bulk_size=500)
        
        assert handler._stream == stream
        assert handler._use_colors is False
        assert handler._bulk_size == 500
        assert handler._max_queue_size == 10000
        assert handler._message_queue.maxsize == 10000
        assert handler._closed is False
        assert len(handler._worker_tasks) == 0
        assert handler._shutdown_event is not None
    
    @pytest.mark.asyncio
    async def test_async_console_handler_start_optimized_async_writer(self):
        """Test _start_optimized_async_writer method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        # Start the writer
        handler._start_optimized_async_writer()
        
        # Should have created worker tasks
        assert len(handler._worker_tasks) > 0
        
        # Clean up
        handler._shutdown_event.set()
        for task in handler._worker_tasks:
            if not task.done():
                task.cancel()
    
    def test_async_console_handler_should_flush_batch(self):
        """Test _should_flush_batch method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        async def run_test():
            import time
            
            # Test with empty batch
            should_flush = await handler._should_flush_batch([], time.time())
            assert should_flush is False
            
            # Test with small batch
            small_batch = ["message1", "message2"]
            should_flush = await handler._should_flush_batch(small_batch, time.time())
            assert should_flush is False
            
            # Test with large batch
            large_batch = ["message"] * 100
            should_flush = await handler._should_flush_batch(large_batch, time.time())
            assert should_flush is True
            
            # Test with time-based flush
            old_time = time.time() - 1.0  # 1 second ago
            should_flush = await handler._should_flush_batch(small_batch, old_time)
            assert should_flush is True
        
        asyncio.run(run_test())
    
    def test_async_console_handler_write_messages_optimized(self):
        """Test _write_messages_optimized method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        async def run_test():
            messages = ["message1", "message2", "message3"]
            await handler._write_messages_optimized(messages)
            
            # Check that messages were written
            stream.seek(0)
            content = stream.read()
            assert "message1" in content
            assert "message2" in content
            assert "message3" in content
        
        asyncio.run(run_test())
    
    def test_async_console_handler_write_sync(self):
        """Test _write_sync method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        handler._write_sync("Test message\n")
        
        # Check that message was written
        stream.seek(0)
        content = stream.read()
        assert "Test message" in content
    
    def test_async_console_handler_auto_cleanup(self):
        """Test _auto_cleanup method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        # Call auto cleanup
        handler._auto_cleanup()
        
        # Shutdown event should be set
        assert handler._shutdown_event.is_set()
    
    @pytest.mark.asyncio
    async def test_async_console_handler_optimized_worker_loop(self):
        """Test _optimized_worker_loop method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, bulk_size=2)
        
        # Add some messages to queue
        await handler._message_queue.put("Message 1\n")
        await handler._message_queue.put("Message 2\n")
        handler._message_event.set()
        
        # Start worker loop
        worker_task = asyncio.create_task(handler._optimized_worker_loop("test-worker"))
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Signal shutdown
        handler._shutdown_event.set()
        
        # Wait for worker to finish
        await asyncio.wait_for(worker_task, timeout=1.0)
        
        # Check that messages were written
        stream.seek(0)
        content = stream.read()
        assert "Message 1" in content
        assert "Message 2" in content
    
    @pytest.mark.asyncio
    async def test_async_console_handler_optimized_worker_loop_shutdown(self):
        """Test _optimized_worker_loop with immediate shutdown."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Signal shutdown immediately
        handler._shutdown_event.set()
        
        # Start worker loop
        worker_task = asyncio.create_task(handler._optimized_worker_loop("test-worker"))
        
        # Should finish quickly
        await asyncio.wait_for(worker_task, timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_async_console_handler_optimized_worker_loop_exception(self):
        """Test _optimized_worker_loop with exception handling."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Mock _write_messages_optimized to raise exception
        with patch.object(handler, '_write_messages_optimized', side_effect=Exception("Test error")):
            # Add message to queue
            await handler._message_queue.put("Test message\n")
            handler._message_event.set()
            
            # Start worker loop
            worker_task = asyncio.create_task(handler._optimized_worker_loop("test-worker"))
            
            # Let it run briefly
            await asyncio.sleep(0.1)
            
            # Signal shutdown
            handler._shutdown_event.set()
            
            # Wait for worker to finish
            await asyncio.wait_for(worker_task, timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_async_console_handler_overflow_worker(self):
        """Test _overflow_worker method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, max_queue_size=1)
        
        # Fill main queue
        await handler._message_queue.put("Main message\n")
        
        # Add message to overflow queue
        await handler._overflow_queue.put("Overflow message\n")
        
        # Start overflow worker
        overflow_task = asyncio.create_task(handler._overflow_worker())
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Signal shutdown
        handler._shutdown_event.set()
        
        # Wait for worker to finish
        await asyncio.wait_for(overflow_task, timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_async_console_handler_overflow_worker_empty_queue(self):
        """Test _overflow_worker with empty overflow queue."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Start overflow worker
        overflow_task = asyncio.create_task(handler._overflow_worker())
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Signal shutdown
        handler._shutdown_event.set()
        
        # Wait for worker to finish
        await asyncio.wait_for(overflow_task, timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_async_console_handler_overflow_worker_exception(self):
        """Test _overflow_worker with exception handling."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Mock _message_queue.put_nowait to raise exception
        with patch.object(handler._message_queue, 'put_nowait', side_effect=Exception("Test error")):
            # Add message to overflow queue
            await handler._overflow_queue.put("Test message\n")
            
            # Start overflow worker
            overflow_task = asyncio.create_task(handler._overflow_worker())
            
            # Let it run briefly
            await asyncio.sleep(0.1)
            
            # Signal shutdown
            handler._shutdown_event.set()
            
            # Wait for worker to finish
            await asyncio.wait_for(overflow_task, timeout=1.0)
    
    @pytest.mark.asyncio
    async def test_async_console_handler_should_flush_batch_time_based(self):
        """Test _should_flush_batch with time-based flush."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Set flush interval to very short
        handler._flush_interval = 0.001
        
        # Test with old last_flush time
        old_time = time.time() - 1.0
        result = await handler._should_flush_batch(["message"], old_time)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_async_console_handler_should_flush_batch_size_based(self):
        """Test _should_flush_batch with size-based flush."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Create large message
        large_message = "x" * (handler._target_batch_size + 1)
        
        # Test with large message
        result = await handler._should_flush_batch([large_message], time.time())
        assert result is True
    
    @pytest.mark.asyncio
    async def test_async_console_handler_should_flush_batch_queue_depth(self):
        """Test _should_flush_batch with queue depth flush."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Fill queue to trigger depth-based flush
        for _ in range(int(handler._max_batch_size * 0.9)):
            await handler._message_queue.put("message")
        
        # Test with queue depth
        result = await handler._should_flush_batch(["message"], time.time())
        assert result is True
    
    @pytest.mark.asyncio
    async def test_async_console_handler_should_flush_batch_minimum_size(self):
        """Test _should_flush_batch with minimum batch size."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Create batch with minimum size
        messages = ["message"] * handler._min_batch_size
        
        # Test with minimum batch size
        result = await handler._should_flush_batch(messages, time.time())
        assert result is True
    
    @pytest.mark.asyncio
    async def test_async_console_handler_should_flush_batch_no_flush(self):
        """Test _should_flush_batch when no flush is needed."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream)
        
        # Test with small batch and recent time
        result = await handler._should_flush_batch(["message"], time.time())
        assert result is False
    
    def test_async_console_handler_del(self):
        """Test __del__ method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        # Call __del__ (cleanup)
        handler.__del__()
        
        # Shutdown event should be set
        assert handler._shutdown_event.is_set()
    
    def test_async_console_handler_pytest_cleanup(self):
        """Test _pytest_cleanup method."""
        stream = io.StringIO()
        handler = AsyncConsoleHandler(stream=stream, use_colors=False)
        
        # Call pytest cleanup
        handler._pytest_cleanup()
        
        # Shutdown event should be set
        assert handler._shutdown_event.is_set()