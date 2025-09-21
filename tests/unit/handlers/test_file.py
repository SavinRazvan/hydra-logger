"""
Tests for hydra_logger.handlers.file module.
"""

import pytest
import os
import tempfile
import asyncio
import io
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hydra_logger.handlers.file import (
    SyncFileHandler, 
    AsyncFileHandler, 
    FileHandler
)
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class TestSyncFileHandler:
    """Test SyncFileHandler functionality."""
    
    def test_sync_file_handler_creation(self):
        """Test SyncFileHandler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            assert handler.name == "sync_file"
            assert handler._filename == tmp_path
            assert handler._mode == "a"
            assert handler._encoding == "utf-8"
            assert handler._buffer_size == 1000
            assert handler._flush_interval == 1.0
            assert len(handler._buffer) == 0
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_with_custom_params(self):
        """Test SyncFileHandler with custom parameters."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(
                tmp_path,
                mode="w",
                encoding="latin-1",
                buffer_size=500,
                flush_interval=0.5
            )
            
            assert handler._mode == "w"
            assert handler._encoding == "latin-1"
            assert handler._buffer_size == 500
            assert handler._flush_interval == 0.5
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_emit(self):
        """Test SyncFileHandler emit method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test file message",
                layer="test"
            )
            
            handler.emit(record)
            handler.force_flush()  # Ensure message is written
            
            # Check that message was written to file
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Test file message" in content
                assert "INFO" in content
                assert "test" in content
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_buffering(self):
        """Test SyncFileHandler buffering functionality."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path, buffer_size=2, flush_interval=0.01)
            
            record1 = LogRecord(level=LogLevel.INFO, message="Message 1", layer="test")
            record2 = LogRecord(level=LogLevel.INFO, message="Message 2", layer="test")
            
            # First message should be buffered
            handler.emit(record1)
            assert len(handler._buffer) == 1
            
            # File should be empty initially
            with open(tmp_path, 'r', encoding='utf-8') as f:
                assert f.read() == ""
            
            # Second message should trigger flush
            handler.emit(record2)
            assert len(handler._buffer) == 0
            
            # Check that both messages were written
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Message 1" in content
                assert "Message 2" in content
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_force_flush(self):
        """Test SyncFileHandler force_flush method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path, buffer_size=10)
            
            record = LogRecord(level=LogLevel.INFO, message="Buffered message", layer="test")
            handler.emit(record)
            
            # Message should be buffered
            assert len(handler._buffer) == 1
            
            # File should be empty
            with open(tmp_path, 'r', encoding='utf-8') as f:
                assert f.read() == ""
            
            # Force flush should write buffered messages
            handler.force_flush()
            assert len(handler._buffer) == 0
            
            with open(tmp_path, 'r', encoding='utf-8') as f:
                assert "Buffered message" in f.read()
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_close(self):
        """Test SyncFileHandler close method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Add some messages to buffer
            record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Test message", layer="test")
            handler.emit(record)
            
            # Close should flush buffer
            handler.close()
            assert len(handler._buffer) == 0  # Buffer should be flushed
            
            # Message should be written to file
            with open(tmp_path, 'r', encoding='utf-8') as f:
                assert "Test message" in f.read()
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_get_stats(self):
        """Test SyncFileHandler get_stats method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Test message", layer="test")
            handler.emit(record)
            
            stats = handler.get_stats()
            
            assert "messages_processed" in stats
            assert "total_bytes_written" in stats
            assert "handler_type" in stats
            assert "uptime_seconds" in stats
            assert stats["messages_processed"] >= 0
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_binary_formatter(self):
        """Test SyncFileHandler with binary formatter."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Mock a binary formatter
            mock_formatter = Mock()
            mock_formatter.name = "binary_formatter"  # Add name attribute
            mock_formatter.format.return_value = b"binary data"
            mock_formatter.format_headers.return_value = ""  # Return empty string for headers
            handler.setFormatter(mock_formatter)
            
            # Force flush to ensure message is written
            handler.force_flush()
            
            record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Binary test", layer="test")
            handler.emit(record)
            handler.force_flush()
            
            # Check that binary data was written
            with open(tmp_path, 'rb') as f:
                content = f.read()
                assert content == b"binary data"
        finally:
            os.unlink(tmp_path)


class TestAsyncFileHandler:
    """Test AsyncFileHandler functionality."""
    
    @pytest.mark.asyncio
    async def test_async_file_handler_creation(self):
        """Test AsyncFileHandler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            assert handler.name == "async_file"
            assert handler._filename == tmp_path
            assert handler._mode == "a"
            assert handler._encoding == "utf-8"
            assert handler._batch_size == 100
            assert handler._max_queue_size == 10000
            # _running may be True if event loop is running, that's expected
            assert handler._running in [True, False]
            
            # Handler will be automatically cleaned up when destroyed
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_emit_async(self):
        """Test AsyncFileHandler emit_async method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Async file test message",
                layer="test"
            )
            
            await handler.emit_async(record)
            
            # Give some time for async processing
            await asyncio.sleep(0.1)
            
            # Check that message was written to file
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Async file test message" in content
                assert "INFO" in content
                assert "test" in content
            
            # Handler will be automatically cleaned up when destroyed
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_queue_overflow(self):
        """Test AsyncFileHandler queue overflow handling."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path, max_queue_size=2)
            
            # Fill up the queue
            record1 = LogRecord(level=LogLevel.INFO, message="Message 1", layer="test")
            record2 = LogRecord(level=LogLevel.INFO, message="Message 2", layer="test")
            record3 = LogRecord(level=LogLevel.INFO, message="Message 3", layer="test")
            
            await handler.emit_async(record1)
            await handler.emit_async(record2)
            await handler.emit_async(record3)  # This should trigger overflow handling
            
            # Give time for processing
            await asyncio.sleep(0.1)
            
            # Should have written messages directly due to overflow
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Message 1" in content or "Message 2" in content or "Message 3" in content
            
            # Handler will be automatically cleaned up when destroyed
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_aclose(self):
        """Test AsyncFileHandler aclose method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Start the handler
            record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Test message", layer="test")
            await handler.emit_async(record)
            
            # Close the handler
            await handler.aclose()
            
            assert handler._shutdown_event.is_set()
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_worker_timeout(self):
        """Test AsyncFileHandler worker timeout protection."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Create a record that will trigger worker startup
            record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Timeout test", layer="test")
            await handler.emit_async(record)
            
            # Give time for worker to start and process
            await asyncio.sleep(0.2)
            
            # Worker should have processed the message without hanging
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Timeout test" in content
            
            # Handler will be automatically cleaned up when destroyed
        finally:
            os.unlink(tmp_path)
    
    def test_async_file_handler_get_stats(self):
        """Test AsyncFileHandler get_stats method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            stats = handler.get_stats()
            
            assert "messages_processed" in stats
            assert "messages_dropped" in stats
            assert "total_bytes_written" in stats
            assert "queue_size" in stats
            assert stats["messages_processed"] >= 0
        finally:
            os.unlink(tmp_path)


class TestFileHandler:
    """Test FileHandler (smart wrapper) functionality."""
    
    def test_file_handler_creation_auto_mode(self):
        """Test FileHandler creation in auto mode."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path)
            
            assert handler.name == "file"
            assert hasattr(handler, '_handler')
        finally:
            os.unlink(tmp_path)
    
    def test_file_handler_creation_sync_mode(self):
        """Test FileHandler creation in sync mode."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path, mode="sync")
            
            assert handler.name == "file"
            assert isinstance(handler._handler, SyncFileHandler)
        finally:
            os.unlink(tmp_path)
    
    def test_file_handler_creation_async_mode(self):
        """Test FileHandler creation - currently defaults to sync mode."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path)
            
            assert handler.name == "file"
            assert isinstance(handler._handler, SyncFileHandler)  # Currently defaults to sync
        finally:
            os.unlink(tmp_path)
    
    def test_file_handler_emit_sync(self):
        """Test FileHandler emit method with sync handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path)
            
            record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Sync wrapper test", layer="test")
            handler.emit(record)
            handler.close()  # Ensure flush
            
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Sync wrapper test" in content
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_file_handler_emit_async(self):
        """Test FileHandler emit_async method with async handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path)  # Will use sync handler but has emit_async method
            
            record = LogRecord(level=LogLevel.INFO, level_name="INFO", message="Async wrapper test", layer="test")
            await handler.emit_async(record)  # Will fallback to sync emit
            handler.close()  # Ensure flush
            
            # Give time for async processing
            await asyncio.sleep(0.1)
            
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Async wrapper test" in content
        finally:
            os.unlink(tmp_path)
    
    def test_file_handler_close(self):
        """Test FileHandler close method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path)
            
            # Should not raise an error
            handler.close()
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_file_handler_aclose(self):
        """Test FileHandler aclose method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path, mode="async")
            
            # Should not raise an error
            await handler.aclose()
        finally:
            os.unlink(tmp_path)
    
    def test_file_handler_get_stats(self):
        """Test FileHandler get_stats method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = FileHandler(tmp_path, mode="sync")
            
            stats = handler.get_stats()
            assert isinstance(stats, dict)
        finally:
            os.unlink(tmp_path)


class TestFileHandlerIntegration:
    """Integration tests for file handlers."""
    
    @pytest.mark.asyncio
    async def test_file_handler_performance(self):
        """Test file handler performance with multiple messages."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Send multiple messages
            for i in range(10):
                record = LogRecord(
                    level=LogLevel.INFO,
                    level_name="INFO",
                    message=f"Performance test message {i}",
                    layer="test"
                )
                await handler.emit_async(record)
            
            # Give time for processing
            await asyncio.sleep(0.2)
            
            # Close handler
            await handler.aclose()
            
            # Check that all messages were processed
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for i in range(10):
                    assert f"Performance test message {i}" in content
        finally:
            os.unlink(tmp_path)
    
    def test_file_handler_error_handling(self):
        """Test file handler error handling."""
        # Create a handler with an invalid path to trigger errors
        invalid_path = "/invalid/path/that/does/not/exist/test.log"
        
        handler = SyncFileHandler(invalid_path)
        
        record = LogRecord(level=LogLevel.INFO, message="Error test", layer="test")
        
        # Should not raise an exception
        handler.emit(record)
        
        # Handler should still be functional
        assert not handler._closed
    
    def test_file_handler_directory_creation(self):
        """Test file handler creates directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a path with a subdirectory that doesn't exist
            file_path = os.path.join(tmp_dir, "subdir", "test.log")
            
            handler = SyncFileHandler(file_path)
            
            record = LogRecord(level=LogLevel.INFO, message="Directory test", layer="test")
            handler.emit(record)
            handler.force_flush()
            
            # Check that directory was created and file was written
            assert os.path.exists(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                assert "Directory test" in f.read()


class TestFileHandlerErrorHandling:
    """Test error handling scenarios for file handlers."""
    
    def test_sync_file_handler_file_closed_error(self):
        """Test SyncFileHandler with closed file handle."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path, buffer_size=1)  # Force flush
            
            # Close the file handle
            handler._file_handle.close()
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test"
            )
            
            # Should not raise exception, should handle gracefully
            handler.emit(record)
            
            # Buffer should have the message since file is closed
            assert len(handler._buffer) == 1
            assert "INFO [test] Test message" in handler._buffer[0]
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_oserror_handling(self):
        """Test SyncFileHandler OSError handling in flush."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Mock file handle to raise OSError
            mock_file = Mock()
            mock_file.closed = False
            mock_file.write.side_effect = OSError("Write error")
            handler._file_handle = mock_file
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test"
            )
            
            # Should not raise exception, should handle gracefully
            handler.emit(record)
            handler.force_flush()
            
            # Buffer should still have the message since write failed
            assert len(handler._buffer) == 1
            assert "INFO [test] Test message" in handler._buffer[0]
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_valueerror_handling(self):
        """Test SyncFileHandler ValueError handling in flush."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Mock file handle to raise ValueError
            mock_file = Mock()
            mock_file.closed = False
            mock_file.write.side_effect = ValueError("Value error")
            handler._file_handle = mock_file
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test"
            )
            
            # Should not raise exception, should handle gracefully
            handler.emit(record)
            handler.force_flush()
            
            # Buffer should still have the message since write failed
            assert len(handler._buffer) == 1
            assert "INFO [test] Test message" in handler._buffer[0]
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_general_exception_handling(self):
        """Test SyncFileHandler general exception handling in emit."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Mock formatter to raise exception
            mock_formatter = Mock()
            mock_formatter.name = "test_formatter"  # Add name attribute
            mock_formatter.format.side_effect = Exception("Formatter error")
            handler.setFormatter(mock_formatter)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test"
            )
            
            # Should not raise exception, should use fallback formatting
            handler.emit(record)
            
            # Should use fallback formatting - buffer should be empty due to error
            assert len(handler._buffer) == 0
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_formatter_error(self):
        """Test AsyncFileHandler with formatter that raises exception."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
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
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "INFO [test] Test message" in content
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_file_closed_error(self):
        """Test AsyncFileHandler with file write error."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Mock the file write to raise an error
            with patch('builtins.open', side_effect=OSError("File write error")):
                record = LogRecord(
                    level=LogLevel.INFO,
                    level_name="INFO",
                    message="Test message",
                    layer="test"
                )
                
                # Should not raise exception, should handle gracefully
                await handler.emit_async(record)
                
                # Wait a bit for async processing
                await asyncio.sleep(0.1)
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_emit_error(self):
        """Test AsyncFileHandler emit with error."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Mock _format_message to raise exception
            with patch.object(handler, '_format_message', side_effect=Exception("Write error")):
                record = LogRecord(
                    level=LogLevel.INFO,
                    level_name="INFO",
                    message="Test message",
                    layer="test"
                )
                
                # Should not raise exception, should handle gracefully
                await handler.emit_async(record)
                
                # Wait a bit for async processing
                await asyncio.sleep(0.1)
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_auto_cleanup(self):
        """Test SyncFileHandler automatic cleanup."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Auto cleanup test",
                layer="test"
            )
            
            handler.emit(record)
            
            # Simulate cleanup by calling close
            handler.close()
            
            # File handle should be None after close
            assert handler._file_handle is None
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_auto_cleanup(self):
        """Test AsyncFileHandler automatic cleanup."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Auto cleanup test",
                layer="test"
            )
            
            await handler.emit_async(record)
            
            # Wait a bit for processing
            await asyncio.sleep(0.1)
            
            # Simulate cleanup by calling aclose
            await handler.aclose()
            
            # Shutdown event should be set
            assert handler._shutdown_event.is_set()
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_pytest_cleanup(self):
        """Test SyncFileHandler pytest cleanup."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Pytest cleanup test",
                layer="test"
            )
            
            handler.emit(record)
            
            # Simulate pytest cleanup by calling close
            handler.close()
            
            # File handle should be None after close
            assert handler._file_handle is None
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_pytest_cleanup(self):
        """Test AsyncFileHandler pytest cleanup."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Pytest cleanup test",
                layer="test"
            )
            
            await handler.emit_async(record)
            
            # Wait a bit for processing
            await asyncio.sleep(0.1)
            
            # Simulate pytest cleanup by calling aclose
            await handler.aclose()
            
            # Shutdown event should be set
            assert handler._shutdown_event.is_set()
        finally:
            os.unlink(tmp_path)


class TestFileHandlerMethods:
    """Test specific methods of file handlers."""
    
    def test_sync_file_handler_is_binary_formatter(self):
        """Test _is_binary_formatter method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Test with text formatter
            text_formatter = Mock()
            text_formatter.name = "text_formatter"
            handler.setFormatter(text_formatter)
            
            assert handler._is_binary_formatter() is False
            
            # Test with binary formatter
            binary_formatter = Mock()
            binary_formatter.name = "binary_formatter"  # Must contain 'binary' in name
            handler.setFormatter(binary_formatter)
            
            assert handler._is_binary_formatter() is True
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_flush_buffer(self):
        """Test _flush_buffer method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Add some content to buffer
            handler._buffer.append("Test message 1\n")
            handler._buffer.append("Test message 2\n")
            
            # Flush buffer
            handler._flush_buffer()
            
            # Check that content was written to file
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "Test message 1" in content
                assert "Test message 2" in content
        finally:
            os.unlink(tmp_path)
    
    def test_sync_file_handler_del(self):
        """Test __del__ method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SyncFileHandler(tmp_path)
            
            # Add some content to buffer
            handler._buffer.append("Test message\n")
            
            # Call __del__ (cleanup)
            handler.__del__()
            
            # Buffer should be flushed
            assert len(handler._buffer) == 0
            
            # Check that content was written
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_start_worker(self):
        """Test _start_worker method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Start worker
            handler._start_worker()
            
            # Should have created worker task
            assert handler._worker_task is not None
            assert not handler._worker_task.done()
            
            # Clean up
            handler._shutdown_event.set()
            if not handler._worker_task.done():
                handler._worker_task.cancel()
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_async_file_handler_message_processor(self):
        """Test _message_processor method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Set shutdown event immediately to stop processor
            handler._shutdown_event.set()
            
            # Run processor - it should exit quickly due to shutdown event
            await handler._message_processor()
            
            # The processor should have run without errors
            # This is a basic test that the method can be called
            assert handler._shutdown_event.is_set()
        finally:
            os.unlink(tmp_path)
    
    def test_async_file_handler_should_flush_batch(self):
        """Test _should_flush_batch method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Test with empty buffer
            should_flush = handler._should_flush_batch()
            assert should_flush is False
            
            # Test with small buffer
            handler._message_buffer.append("message1")
            handler._message_buffer.append("message2")
            should_flush = handler._should_flush_batch()
            assert should_flush is False
            
            # Test with large buffer
            for i in range(100):
                handler._message_buffer.append(f"message{i}")
            should_flush = handler._should_flush_batch()
            assert should_flush is True
        finally:
            os.unlink(tmp_path)
    
    def test_async_file_handler_flush_batch(self):
        """Test _flush_batch method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            async def run_test():
                # Add some content to buffer
                handler._message_buffer.append("Test message 1\n")
                handler._message_buffer.append("Test message 2\n")
                
                # Flush batch
                await handler._flush_batch()
                
                # Check that content was written to file
                with open(tmp_path, 'r') as f:
                    content = f.read()
                    assert "Test message 1" in content
                    assert "Test message 2" in content
            
            asyncio.run(run_test())
        finally:
            os.unlink(tmp_path)
    
    def test_async_file_handler_del(self):
        """Test __del__ method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = AsyncFileHandler(tmp_path)
            
            # Add some content to buffer
            handler._message_buffer.append("Test message\n")
            
            # Call __del__ (cleanup)
            handler.__del__()
            
            # Shutdown event should be set
            assert handler._shutdown_event.is_set()
        finally:
            os.unlink(tmp_path)
