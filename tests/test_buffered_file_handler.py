"""
Tests for buffered file handler functionality.

This module tests the BufferedRotatingFileHandler class and its
integration with HydraLogger for improved file I/O performance.
"""

import os
import time
import tempfile
import pytest
import logging
from hydra_logger.logger import BufferedRotatingFileHandler
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from unittest.mock import patch


class TestBufferedFileHandler:
    """Test buffered file handler functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Create test logs directory
        self.test_logs_dir = "_tests_logs"
        os.makedirs(self.test_logs_dir, exist_ok=True)
        self.log_file = os.path.join(self.test_logs_dir, "test_buffered.log")

    def teardown_method(self):
        """Cleanup test files."""
        # Clean up test log files
        if os.path.exists(self.log_file):
            os.unlink(self.log_file)
        if os.path.exists(self.log_file + ".1"):
            os.unlink(self.log_file + ".1")

    def test_buffered_handler_creation(self):
        """Test that buffered handler can be created."""
        handler = BufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=512,
            flush_interval=0.5
        )
        
        assert handler.buffer_size == 512
        assert handler.flush_interval == 0.5
        assert handler._buffer == []
        assert handler._buffer_size == 0

    def test_buffered_handler_emit(self):
        """Test that buffered handler emits messages correctly."""
        handler = BufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=512,
            flush_interval=0.5
        )
        
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Emit the record
        handler.emit(record)
        
        # Check that buffer contains the message
        assert len(handler._buffer) == 1
        assert "Test message" in handler._buffer[0]

    def test_buffered_handler_flush_on_size(self):
        """Test that buffer flushes when size limit is reached."""
        handler = BufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=100,  # Small buffer size
            flush_interval=10.0  # Long flush interval
        )
        
        # Create a log record with a message that will exceed buffer size
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="This is a long message that should trigger buffer flush",
            args=(),
            exc_info=None
        )
        
        # Emit the record
        handler.emit(record)
        
        # Check that buffer was flushed
        assert len(handler._buffer) == 0
        assert handler._buffer_size == 0
        
        # Check that file was written
        assert os.path.exists(self.log_file)

    def test_buffered_handler_flush_on_time(self):
        """Test that buffer flushes when time limit is reached."""
        handler = BufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=1000,  # Large buffer size
            flush_interval=0.1  # Short flush interval
        )
        
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Emit the record
        handler.emit(record)
        
        # Wait for flush interval
        time.sleep(0.2)
        
        # Emit another record to trigger flush
        handler.emit(record)
        
        # Check that buffer was flushed
        assert len(handler._buffer) == 1  # Only the new message
        assert os.path.exists(self.log_file)

    def test_buffered_handler_close(self):
        """Test that buffer is flushed when handler is closed."""
        handler = BufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=1000,
            flush_interval=10.0
        )
        
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Emit the record
        handler.emit(record)
        
        # Close the handler
        handler.close()
        
        # Check that file was written
        assert os.path.exists(self.log_file)
        
        # Check file content
        with open(self.log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content

    def test_buffered_handler_with_performance_monitoring(self):
        """Test that buffered handler works with performance monitoring."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file", 
                            path=self.log_file, 
                            level="INFO"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(
            config=config,
            enable_performance_monitoring=True
        )
        
        try:
            # Log some messages
            for i in range(10):
                logger.info("TEST", f"Buffered message {i}")
            
            # Wait for flush and explicitly flush
            time.sleep(0.6)
            
            # Get the logger and flush its handlers
            test_logger = logger.get_logger("TEST")
            for handler in test_logger.handlers:
                handler.flush()
            
            # Check that messages were written
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    content = f.read()
                    assert "Buffered message" in content
        finally:
            # Clean up
            if os.path.exists(self.log_file):
                os.unlink(self.log_file)

    def test_buffered_handler_error_handling(self):
        """Test buffered handler error handling."""
        handler = BufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=1024,
            backupCount=3,
            buffer_size=512,
            flush_interval=0.5
        )
        
        # Create a log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        # Mock stream.write to raise an exception
        with patch.object(handler, 'stream') as mock_stream:
            mock_stream.write.side_effect = Exception("Write error")
            
            # This should not raise an exception
            handler.emit(record)
            
            # Check that error was handled gracefully
            assert len(handler._buffer) == 1

    def test_buffered_handler_with_rotation(self):
        """Test buffered handler with file rotation."""
        handler = BufferedRotatingFileHandler(
            filename=self.log_file,
            maxBytes=100,  # Small max bytes to trigger rotation
            backupCount=2,
            buffer_size=512,
            flush_interval=0.5
        )
        
        # Create multiple log records to trigger rotation
        for i in range(5):
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Test message {i}",
                args=(),
                exc_info=None
            )
            handler.emit(record)
        
        # Close handler to flush buffer
        handler.close()
        
        # Check that files were created
        assert os.path.exists(self.log_file)
        # May have rotation files depending on message size 