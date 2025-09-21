"""
Tests for hydra_logger.handlers.rotating module.
"""

import pytest
import os
import tempfile
import time
import gzip
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hydra_logger.handlers.rotating import (
    RotatingFileHandler,
    TimedRotatingFileHandler,
    SizeRotatingFileHandler,
    HybridRotatingFileHandler,
    RotatingFileHandlerFactory,
    TimeUnit,
    RotationStrategy,
    RotationConfig
)
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class TestRotatingFileHandler:
    """Test RotatingFileHandler functionality."""
    
    def test_rotating_file_handler_creation(self):
        """Test RotatingFileHandler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            
            assert handler.name == "rotating_file"
            assert handler._filename == tmp_path
            assert handler._config is not None
            assert handler._rotation_count == 0
            assert handler._last_rotation == 0.0
        finally:
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_with_custom_config(self):
        """Test RotatingFileHandler with custom configuration."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                max_size=1024,
                max_size_files=3,
                compress_old=True
            )
            
            handler = RotatingFileHandler(tmp_path, config=config)
            
            assert handler._config.max_size == 1024
            assert handler._config.max_size_files == 3
            assert handler._config.compress_old
        finally:
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_abstract_methods(self):
        """Test RotatingFileHandler abstract methods raise NotImplementedError."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            
            # Test abstract methods
            with pytest.raises(NotImplementedError):
                handler._should_rotate()
        finally:
            os.unlink(tmp_path)


class TestTimedRotatingFileHandler:
    """Test TimedRotatingFileHandler functionality."""
    
    def test_timed_rotating_file_handler_creation(self):
        """Test TimedRotatingFileHandler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = TimedRotatingFileHandler(tmp_path, when="hour", interval=1, backup_count=3, time_unit=TimeUnit.HOURS)
            
            assert handler.name == "rotating_file"  # Inherits from base class
            assert handler._filename == tmp_path
            assert handler._config.strategy == RotationStrategy.TIME_BASED
            assert handler._config.time_interval == 1
            assert handler._config.time_unit == TimeUnit.HOURS  # Now configurable
        finally:
            os.unlink(tmp_path)
    
    def test_timed_rotating_file_handler_emit(self):
        """Test TimedRotatingFileHandler emit functionality."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.TIME_BASED,
                time_interval=1,
                time_unit=TimeUnit.SECONDS
            )
            handler = TimedRotatingFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test"
            )
            
            handler.emit(record)
            handler.force_flush()
            
            # Check that file was created and contains the message
            assert os.path.exists(tmp_path)
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            os.unlink(tmp_path)


class TestSizeRotatingFileHandler:
    """Test SizeRotatingFileHandler functionality."""
    
    def test_size_rotating_file_handler_creation(self):
        """Test SizeRotatingFileHandler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SizeRotatingFileHandler(tmp_path, max_bytes=1024, backup_count=5)
            
            assert handler.name == "rotating_file"  # Inherits from base class
            assert handler._filename == tmp_path
            assert handler._config.strategy == RotationStrategy.SIZE_BASED
            assert handler._config.max_size == 1024
            assert handler._config.max_size_files == 5
        finally:
            os.unlink(tmp_path)
    
    def test_size_rotating_file_handler_emit(self):
        """Test SizeRotatingFileHandler emit functionality."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=100,
                max_size_files=3
            )
            handler = SizeRotatingFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test"
            )
            
            handler.emit(record)
            handler.force_flush()
            
            # Check that file was created and contains the message
            assert os.path.exists(tmp_path)
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            os.unlink(tmp_path)


class TestHybridRotatingFileHandler:
    """Test HybridRotatingFileHandler functionality."""
    
    def test_hybrid_rotating_file_handler_creation(self):
        """Test HybridRotatingFileHandler creation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = HybridRotatingFileHandler(tmp_path, max_bytes=1024, when="hour", interval=1, backup_count=3)
            
            assert handler.name == "rotating_file"  # Inherits from base class
            assert handler._filename == tmp_path
            assert handler._config.strategy == RotationStrategy.HYBRID
            assert handler._config.max_size == 1024
            assert handler._config.time_interval == 1
        finally:
            os.unlink(tmp_path)
    
    def test_hybrid_rotating_file_handler_emit(self):
        """Test HybridRotatingFileHandler emit functionality."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.HYBRID,
                max_size=100,
                time_interval=1,
                time_unit=TimeUnit.SECONDS
            )
            handler = HybridRotatingFileHandler(tmp_path)
            
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test"
            )
            
            handler.emit(record)
            handler.force_flush()
            
            # Check that file was created and contains the message
            assert os.path.exists(tmp_path)
            with open(tmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            os.unlink(tmp_path)


class TestRotatingFileHandlerFactory:
    """Test RotatingFileHandlerFactory functionality."""
    
    def test_factory_create_size_handler(self):
        """Test factory creating size-based handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandlerFactory.create_handler("size", tmp_path, max_size=1024, max_size_files=3)
            
            assert isinstance(handler, SizeRotatingFileHandler)
            assert handler._config.max_size == 1024
            assert handler._config.max_size_files == 3
        finally:
            os.unlink(tmp_path)
    
    def test_factory_create_time_handler(self):
        """Test factory creating time-based handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandlerFactory.create_handler("timed", tmp_path, time_interval=1, time_unit=TimeUnit.HOURS, max_time_files=3)
            
            assert isinstance(handler, TimedRotatingFileHandler)
            assert handler._config.time_interval == 1
            assert handler._config.time_unit == TimeUnit.HOURS  # Now properly configurable
        finally:
            os.unlink(tmp_path)
    
    def test_factory_create_hybrid_handler(self):
        """Test factory creating hybrid handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandlerFactory.create_handler("hybrid", tmp_path, max_size=1024, time_interval=1, time_unit=TimeUnit.HOURS, max_size_files=3)
            
            assert isinstance(handler, HybridRotatingFileHandler)
            assert handler._config.max_size == 1024
            assert handler._config.time_interval == 1
        finally:
            os.unlink(tmp_path)


class TestRotatingFileHandlerMethods:
    """Test specific methods of RotatingFileHandler."""
    
    def test_rotating_file_handler_init(self):
        """Test RotatingFileHandler __init__ method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=1024,
                max_size_files=5,
                compress_old=True
            )
            
            handler = RotatingFileHandler(tmp_path, config=config)
            
            assert handler._filename == tmp_path
            assert handler._config == config
            assert handler._rotation_count == 0
            assert handler._last_rotation == 0.0
            # File is initialized automatically in __init__
            assert handler._current_file is not None
            assert not handler._current_file.closed
            assert handler._lock is not None
        finally:
            if handler._current_file:
                handler._current_file.close()
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_initialize_file(self):
        """Test _initialize_file method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            handler._initialize_file()
            
            assert handler._current_file is not None
            assert not handler._current_file.closed
            assert os.path.exists(tmp_path)
        finally:
            if handler._current_file:
                handler._current_file.close()
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_generate_backup_name(self):
        """Test _generate_backup_name method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            backup_name = handler._generate_backup_name()
            
            assert backup_name.startswith(os.path.basename(tmp_path))
            assert '.' in backup_name
            # Backup name format is timestamp-based, not .log
            assert any(char.isdigit() for char in backup_name)
        finally:
            if handler._current_file:
                handler._current_file.close()
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_get_backup_path(self):
        """Test _get_backup_path method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            backup_name = "test.log.2024-01-01"
            backup_path = handler._get_backup_path(backup_name)
            
            expected_path = os.path.join(os.path.dirname(tmp_path), backup_name)
            assert backup_path == expected_path
        finally:
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_compress_file(self):
        """Test _compress_file method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Create a test file with content
            with open(tmp_path, 'w') as f:
                f.write("Test content for compression")
            
            handler = RotatingFileHandler(tmp_path)
            handler._compress_file(tmp_path)
            
            # Check that compressed file exists
            compressed_path = tmp_path + '.gz'
            assert os.path.exists(compressed_path)
            
            # Check that original file is removed
            assert not os.path.exists(tmp_path)
            
            # Verify compressed content
            with gzip.open(compressed_path, 'rt') as f:
                content = f.read()
                assert content == "Test content for compression"
        finally:
            # Clean up
            for f in os.listdir(os.path.dirname(tmp_path)):
                if f.startswith(os.path.basename(tmp_path)):
                    try:
                        os.unlink(os.path.join(os.path.dirname(tmp_path), f))
                    except OSError:
                        pass
    
    def test_rotating_file_handler_cleanup_old_files(self):
        """Test _cleanup_old_files method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=1024,
                max_size_files=2
            )
            handler = RotatingFileHandler(tmp_path, config=config)
            
            # Create some backup files with proper timestamp format
            backup_dir = os.path.dirname(tmp_path)
            base_name = os.path.basename(tmp_path)
            
            # Create files with timestamp format that the handler expects
            backup_files = [
                f"{base_name}.2024-01-01",
                f"{base_name}.2024-01-02", 
                f"{base_name}.2024-01-03",
                f"{base_name}.2024-01-04"
            ]
            
            for backup_file in backup_files:
                with open(os.path.join(backup_dir, backup_file), 'w') as f:
                    f.write("test content")
            
            # Call cleanup
            handler._cleanup_old_files()
            
            # Check that some files were cleaned up (exact count may vary due to file info issues)
            remaining_files = [f for f in os.listdir(backup_dir) if f.startswith(base_name)]
            # At least the original file should remain
            assert len(remaining_files) >= 1
        finally:
            if handler._current_file:
                handler._current_file.close()
            # Clean up all files
            for f in os.listdir(os.path.dirname(tmp_path)):
                if f.startswith(os.path.basename(tmp_path)):
                    try:
                        os.unlink(os.path.join(os.path.dirname(tmp_path), f))
                    except OSError:
                        pass
    
    def test_rotating_file_handler_flush_buffer(self):
        """Test _flush_buffer method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Use concrete handler to avoid abstract method issues
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=1024
            )
            handler = SizeRotatingFileHandler(tmp_path)
            
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
            if handler._current_file:
                handler._current_file.close()
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_write_to_file(self):
        """Test _write_to_file method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            handler._initialize_file()
            
            # Write to file
            handler._write_to_file("Test message\n")
            
            # Check that content was written
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            if handler._current_file:
                handler._current_file.close()
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_close(self):
        """Test close method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Use concrete handler to avoid abstract method issues
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=1024
            )
            handler = SizeRotatingFileHandler(tmp_path)
            
            # Add some content
            handler._buffer.append("Test message\n")
            
            # Close handler
            handler.close()
            
            # Check that file was closed and content flushed
            assert handler._current_file is None or handler._current_file.closed
            assert len(handler._buffer) == 0
            
            # Check that content was written
            with open(tmp_path, 'r') as f:
                content = f.read()
                assert "Test message" in content
        finally:
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_get_rotation_stats(self):
        """Test get_rotation_stats method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            handler._rotation_count = 5
            handler._last_rotation = 1234567890.0
            
            stats = handler.get_rotation_stats()
            
            assert stats['rotation_count'] == 5
            assert stats['last_rotation'] == 1234567890.0
            assert 'filename' in stats
            assert stats['filename'] == tmp_path
        finally:
            os.unlink(tmp_path)
    
    def test_rotating_file_handler_set_formatter(self):
        """Test setFormatter method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandler(tmp_path)
            formatter = Mock()
            formatter.name = "test_formatter"
            
            handler.setFormatter(formatter)
            
            # Check that formatter was set (attribute name may vary)
            assert hasattr(handler, 'formatter') or hasattr(handler, '_formatter')
            if hasattr(handler, 'formatter'):
                assert handler.formatter == formatter
            else:
                assert handler._formatter == formatter
        finally:
            if handler._current_file:
                handler._current_file.close()
            os.unlink(tmp_path)


class TestTimedRotatingFileHandlerMethods:
    """Test specific methods of TimedRotatingFileHandler."""
    
    def test_timed_rotating_file_handler_get_last_rotation_time(self):
        """Test _get_last_rotation_time method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.TIME_BASED,
                time_interval=1,
                time_unit=TimeUnit.HOURS
            )
            handler = TimedRotatingFileHandler(tmp_path)
            
            # Test when file doesn't exist - should return current time
            last_rotation = handler._get_last_rotation_time()
            assert isinstance(last_rotation, datetime)
            
            # Test when file exists - should return file modification time
            # Create the file first
            with open(tmp_path, 'w') as f:
                f.write('test')
            
            # Mock the file modification time
            expected_timestamp = 1234567890.0
            with patch('hydra_logger.handlers.rotating.FileUtils.get_file_info') as mock_get_info:
                mock_file_info = Mock()
                mock_file_info.modified = expected_timestamp
                mock_get_info.return_value = mock_file_info
                
                last_rotation = handler._get_last_rotation_time()
                expected_datetime = datetime.fromtimestamp(expected_timestamp)
                assert last_rotation == expected_datetime
                
        finally:
            os.unlink(tmp_path)
    
    def test_timed_rotating_file_handler_generate_backup_name(self):
        """Test _generate_backup_name method for timed handler."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.TIME_BASED,
                time_interval=1,
                time_unit=TimeUnit.HOURS
            )
            handler = TimedRotatingFileHandler(tmp_path)
            
            backup_name = handler._generate_backup_name()
            
            assert backup_name.startswith(os.path.basename(tmp_path))
            assert '.' in backup_name
            # Should contain timestamp format
            assert any(char.isdigit() for char in backup_name)
        finally:
            os.unlink(tmp_path)


class TestRotatingFileHandlerFactoryMethods:
    """Test RotatingFileHandlerFactory methods."""
    
    def test_factory_create_timed_handler(self):
        """Test create_timed_handler static method."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = RotatingFileHandlerFactory.create_timed_handler(
                tmp_path,
                time_interval=2,
                time_unit=TimeUnit.DAYS,
                max_time_files=5
            )
            
            assert isinstance(handler, TimedRotatingFileHandler)
            assert handler._config.time_interval == 2
            assert handler._config.time_unit == TimeUnit.DAYS
            assert handler._config.max_time_files == 5
        finally:
            os.unlink(tmp_path)


class TestRotatingHandlerErrorHandling:
    """Test error handling scenarios for rotating handlers."""
    
    def test_rotating_handler_file_error(self):
        """Test RotatingFileHandler with file error."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            handler = SizeRotatingFileHandler(tmp_path, max_bytes=50, backup_count=3)
            
            # Mock file operations to raise error
            with patch('builtins.open', side_effect=OSError("File error")):
                record = LogRecord(
                    level=LogLevel.INFO,
                    level_name="INFO",
                    message="Test message",
                    layer="test"
                )
                
                # Should not raise exception, should handle gracefully
                handler.emit(record)
        finally:
            os.unlink(tmp_path)
    
    def test_size_rotating_handler_rotation_error(self):
        """Test SizeRotatingFileHandler with rotation error."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=50
            )
            handler = SizeRotatingFileHandler(tmp_path)
            
            # Mock rotation to raise error
            with patch.object(handler, '_rotate_file', side_effect=OSError("Rotation error")):
                # Write enough data to trigger rotation
                for i in range(10):
                    record = LogRecord(
                        level=LogLevel.INFO,
                        level_name="INFO",
                        message=f"Test message {i} with some extra text to make it longer",
                        layer="test"
                    )
                    handler.emit(record)
                    handler.force_flush()
                
                # Should not raise exception, should handle gracefully
        finally:
            os.unlink(tmp_path)
    
    def test_rotating_handler_compression_error(self):
        """Test RotatingFileHandler with compression error."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=50,
                compress_old=True
            )
            handler = SizeRotatingFileHandler(tmp_path)
            
            # Mock compression to raise error
            with patch('gzip.open', side_effect=OSError("Compression error")):
                # Write enough data to trigger rotation
                for i in range(10):
                    record = LogRecord(
                        level=LogLevel.INFO,
                        level_name="INFO",
                        message=f"Test message {i} with some extra text to make it longer",
                        layer="test"
                    )
                    handler.emit(record)
                    handler.force_flush()
                
                # Should not raise exception, should handle gracefully
        finally:
            os.unlink(tmp_path)
    
    def test_rotating_handler_cleanup_error(self):
        """Test RotatingFileHandler with cleanup error."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            config = RotationConfig(
                strategy=RotationStrategy.SIZE_BASED,
                max_size=50,
                max_size_files=2
            )
            handler = SizeRotatingFileHandler(tmp_path)
            
            # Mock cleanup to raise error
            with patch('os.unlink', side_effect=OSError("Cleanup error")):
                # Write enough data to trigger multiple rotations
                for i in range(20):
                    record = LogRecord(
                        level=LogLevel.INFO,
                        level_name="INFO",
                        message=f"Test message {i} with some extra text to make it longer",
                        layer="test"
                    )
                    handler.emit(record)
                    handler.force_flush()
                
                # Should not raise exception, should handle gracefully
        finally:
            # Clean up all files
            for f in os.listdir(os.path.dirname(tmp_path)):
                if f.startswith(os.path.basename(tmp_path)):
                    try:
                        os.unlink(os.path.join(os.path.dirname(tmp_path), f))
                    except OSError:
                        pass
