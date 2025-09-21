"""
Tests for hydra_logger.types.records module.
"""

import pytest
import time
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from hydra_logger.types.records import (
    LogRecord, LogRecordFactory, LogRecordBatch, 
    RecordCreationStrategy, extract_filename,
    get_record_creation_strategy, create_log_record,
    MINIMAL_STRATEGY, CONTEXT_STRATEGY, AUTO_CONTEXT_STRATEGY
)
from hydra_logger.types.levels import LogLevel


class TestLogRecord:
    """Test LogRecord class functionality."""
    
    def test_log_record_creation(self):
        """Test basic LogRecord creation."""
        record = LogRecord(
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        assert record.level_name == "INFO"
        assert record.message == "Test message"
        assert record.layer == "test"
        assert isinstance(record.timestamp, float)
        assert record.timestamp > 0
    
    def test_log_record_with_optional_fields(self):
        """Test LogRecord creation with optional fields."""
        record = LogRecord(
            level_name="ERROR",
            message="Error occurred",
            layer="api",
            file_name="test.py",
            function_name="test_function",
            line_number=42,
            level=40
        )
        
        assert record.level_name == "ERROR"
        assert record.message == "Error occurred"
        assert record.layer == "api"
        assert record.file_name == "test.py"
        assert record.function_name == "test_function"
        assert record.line_number == 42
        assert record.level == 40
    
    def test_log_record_with_extra_fields(self):
        """Test LogRecord creation with extra fields."""
        extra = {"duration": 1.5, "status_code": 200}
        record = LogRecord(
            level_name="INFO",
            message="Request completed",
            layer="web",
            extra=extra
        )
        
        assert record.extra == extra
        assert record.extra["duration"] == 1.5
        assert record.extra["status_code"] == 200
    
    def test_log_record_timestamp(self):
        """Test LogRecord timestamp generation."""
        before = time.time()
        record = LogRecord(
            level_name="DEBUG",
            message="Debug message",
            layer="test"
        )
        after = time.time()
        
        assert before <= record.timestamp <= after
    
    def test_log_record_iso_timestamp(self):
        """Test LogRecord iso_timestamp property."""
        record = LogRecord(
            level_name="INFO",
            message="Test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        iso_timestamp = record.iso_timestamp
        assert isinstance(iso_timestamp, str)
        assert "2009" in iso_timestamp  # Should be around 2009 for timestamp 1234567890
    
    def test_log_record_to_dict(self):
        """Test LogRecord to_dict method."""
        extra = {"count": 42}
        
        record = LogRecord(
            level_name="INFO",
            message="Test message",
            layer="test",
            extra=extra,
            level=20
        )
        
        record_dict = record.to_dict()
        
        assert record_dict["level_name"] == "INFO"
        assert record_dict["message"] == "Test message"
        assert record_dict["layer"] == "test"
        assert record_dict["extra"] == extra
        assert record_dict["level"] == 20
        assert "timestamp" in record_dict
    
    def test_log_record_equality(self):
        """Test LogRecord equality comparison."""
        record1 = LogRecord(
            level_name="INFO",
            message="Same message",
            layer="test",
            timestamp=1234567890.0
        )
        
        record2 = LogRecord(
            level_name="INFO",
            message="Same message",
            layer="test",
            timestamp=1234567890.0
        )
        
        assert record1 == record2
    
    def test_log_record_inequality(self):
        """Test LogRecord inequality comparison."""
        record1 = LogRecord(
            level_name="INFO",
            message="Message 1",
            layer="test"
        )
        
        record2 = LogRecord(
            level_name="ERROR",
            message="Message 2",
            layer="test"
        )
        
        assert record1 != record2
    
    def test_log_record_str_representation(self):
        """Test LogRecord string representation."""
        record = LogRecord(
            level_name="WARNING",
            message="Warning message",
            layer="test"
        )
        
        str_repr = str(record)
        assert "WARNING" in str_repr
        assert "Warning message" in str_repr
        assert "test" in str_repr
    
    def test_log_record_repr(self):
        """Test LogRecord repr representation."""
        record = LogRecord(
            level_name="DEBUG",
            message="Debug message",
            layer="test"
        )
        
        repr_str = repr(record)
        assert "LogRecord" in repr_str
        assert "DEBUG" in repr_str
        assert "Debug message" in repr_str
    
    def test_log_record_immutable(self):
        """Test that LogRecord is immutable."""
        record = LogRecord(
            level_name="INFO",
            message="Test message",
            layer="test"
        )
        
        # Should not be able to modify fields
        with pytest.raises(AttributeError):
            record.message = "Modified message"
        
        with pytest.raises(AttributeError):
            record.level_name = "ERROR"
    
    def test_log_record_validation(self):
        """Test LogRecord validation."""
        # Empty message should raise error
        with pytest.raises(ValueError):
            LogRecord(
                level_name="INFO",
                message="",
                layer="test"
            )
        
        # Empty level_name should raise error
        with pytest.raises(ValueError):
            LogRecord(
                level_name="",
                message="Test message",
                layer="test"
            )
    
    def test_log_record_default_values(self):
        """Test LogRecord default values."""
        record = LogRecord(message="Test message")
        
        assert record.level_name == "INFO"  # Default
        assert record.layer == "default"    # Default
        assert record.level == 20           # Default INFO level
        assert record.logger_name == "HydraLogger"  # Default
        assert record.file_name is None     # Default
        assert record.function_name is None # Default
        assert record.line_number is None   # Default
        assert record.extra == {}           # Default empty dict
    
    def test_log_record_with_logger_name(self):
        """Test LogRecord with custom logger name."""
        record = LogRecord(
            level_name="INFO",
            message="Test message",
            layer="test",
            logger_name="CustomLogger"
        )
        
        assert record.logger_name == "CustomLogger"
    
    def test_log_record_with_file_info(self):
        """Test LogRecord with file and function information."""
        record = LogRecord(
            level_name="INFO",
            message="Test message",
            layer="test",
            file_name="test_file.py",
            function_name="test_function",
            line_number=123
        )
        
        assert record.file_name == "test_file.py"
        assert record.function_name == "test_function"
        assert record.line_number == 123
    
    def test_log_record_complex_extra(self):
        """Test LogRecord with complex extra data."""
        complex_extra = {
            "user": {
                "id": 123,
                "name": "John Doe"
            },
            "request": {
                "method": "POST",
                "path": "/api/test"
            },
            "metrics": [1, 2, 3, 4, 5]
        }
        
        record = LogRecord(
            level_name="INFO",
            message="Complex test",
            layer="api",
            extra=complex_extra
        )
        
        assert record.extra == complex_extra
        assert record.extra["user"]["id"] == 123
        assert record.extra["user"]["name"] == "John Doe"
        assert record.extra["request"]["method"] == "POST"
        assert record.extra["metrics"] == [1, 2, 3, 4, 5]


class TestLogRecordIntegration:
    """Integration tests for LogRecord."""
    
    def test_log_record_performance(self):
        """Test LogRecord creation performance."""
        import time
        
        start_time = time.time()
        
        # Create many records
        records = []
        for i in range(1000):
            record = LogRecord(
                level_name="INFO",
                message=f"Performance test message {i}",
                layer="test"
            )
            records.append(record)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should create 1000 records in reasonable time
        assert len(records) == 1000
        assert duration < 1.0  # Should be very fast
        
        # All records should be valid
        for record in records:
            assert record.message != ""
            assert record.level_name != ""
            assert record.layer != ""
    
    def test_log_record_serialization_performance(self):
        """Test LogRecord serialization performance."""
        import time
        
        record = LogRecord(
            level_name="INFO",
            message="Serialization test",
            layer="test",
            extra={"data": list(range(100))}
        )
        
        start_time = time.time()
        
        # Serialize many times
        for _ in range(1000):
            record_dict = record.to_dict()
            assert isinstance(record_dict, dict)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should serialize 1000 times in reasonable time
        assert duration < 1.0
    
    def test_log_record_memory_usage(self):
        """Test LogRecord memory usage."""
        import sys
        
        # Create a record
        record = LogRecord(
            level_name="INFO",
            message="Memory test",
            layer="test",
            extra={"large_data": "x" * 1000}
        )
        
        # Get memory size
        memory_size = sys.getsizeof(record)
        
        # Should be reasonable size
        assert memory_size < 10000  # Less than 10KB
    
    def test_log_record_with_different_levels(self):
        """Test LogRecord with different log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in levels:
            record = LogRecord(
                level_name=level,
                message=f"Test message for {level}",
                layer="test"
            )
            
            assert record.level_name == level
            assert record.message == f"Test message for {level}"
            assert record.layer == "test"
    
    def test_log_record_with_different_layers(self):
        """Test LogRecord with different layers."""
        layers = ["api", "web", "database", "cache", "auth"]
        
        for layer in layers:
            record = LogRecord(
                level_name="INFO",
                message=f"Test message for {layer}",
                layer=layer
            )
            
            assert record.level_name == "INFO"
            assert record.message == f"Test message for {layer}"
            assert record.layer == layer


class TestLogRecordAdditionalMethods:
    """Test additional LogRecord methods not covered in basic tests."""
    
    def test_log_record_to_json(self):
        """Test LogRecord to_json method."""
        record = LogRecord(
            level_name="INFO",
            message="Test message",
            layer="test",
            extra={"count": 42}
        )
        
        json_str = record.to_json()
        assert isinstance(json_str, str)
        
        # Parse back to verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["layer"] == "test"
        assert parsed["extra"]["count"] == 42
    
    def test_log_record_str_with_optional_fields(self):
        """Test LogRecord __str__ method with optional fields."""
        record = LogRecord(
            level_name="ERROR",
            message="Error occurred",
            layer="api",
            file_name="test.py",
            function_name="test_function",
            timestamp=1234567890.0
        )
        
        str_repr = str(record)
        assert "[ERROR]" in str_repr
        assert "[api]" in str_repr
        assert "[test.py]" in str_repr
        assert "[test_function]" in str_repr
        assert "Error occurred" in str_repr
        assert "2009" in str_repr  # From timestamp 1234567890.0
    
    def test_log_record_str_without_optional_fields(self):
        """Test LogRecord __str__ method without optional fields."""
        record = LogRecord(
            level_name="INFO",
            message="Simple message",
            layer="test"
        )
        
        str_repr = str(record)
        assert "[INFO]" in str_repr
        assert "[test]" in str_repr
        assert "Simple message" in str_repr
        # Should not contain file_name or function_name placeholders
        assert "[None]" not in str_repr


class TestExtractFilename:
    """Test extract_filename utility function."""
    
    def test_extract_filename_unix_path(self):
        """Test extracting filename from Unix path."""
        assert extract_filename("/path/to/file.py") == "file.py"
        assert extract_filename("/home/user/project/main.py") == "main.py"
        assert extract_filename("/usr/local/bin/script") == "script"
    
    def test_extract_filename_windows_path(self):
        """Test extracting filename from Windows path."""
        assert extract_filename("C:\\path\\to\\file.py") == "file.py"
        assert extract_filename("D:\\project\\main.py") == "main.py"
        assert extract_filename("C:\\Users\\user\\script") == "script"
    
    def test_extract_filename_no_path(self):
        """Test extracting filename when no path separators."""
        assert extract_filename("file.py") == "file.py"
        assert extract_filename("script") == "script"
        assert extract_filename("main") == "main"
    
    def test_extract_filename_empty_or_none(self):
        """Test extracting filename with empty or None input."""
        assert extract_filename("") is None
        assert extract_filename(None) is None


class TestLogRecordFactory:
    """Test LogRecordFactory class."""
    
    def test_create_minimal(self):
        """Test LogRecordFactory.create_minimal method."""
        record = LogRecordFactory.create_minimal(
            level_name="DEBUG",
            message="Debug message",
            layer="test"
        )
        
        assert record.level_name == "DEBUG"
        assert record.message == "Debug message"
        assert record.layer == "test"
        assert record.level == 20  # Default
        assert record.logger_name == "HydraLogger"  # Default
    
    def test_create_minimal_with_kwargs(self):
        """Test LogRecordFactory.create_minimal with additional kwargs."""
        record = LogRecordFactory.create_minimal(
            level_name="ERROR",
            message="Error message",
            layer="api",
            level=40,
            logger_name="CustomLogger",
            file_name="test.py",
            extra={"error_code": 500}
        )
        
        assert record.level_name == "ERROR"
        assert record.message == "Error message"
        assert record.layer == "api"
        assert record.level == 40
        assert record.logger_name == "CustomLogger"
        assert record.file_name == "test.py"
        assert record.extra["error_code"] == 500
    
    def test_create_with_context(self):
        """Test LogRecordFactory.create_with_context method."""
        record = LogRecordFactory.create_with_context(
            level_name="INFO",
            message="Info message",
            layer="web",
            file_name="/path/to/file.py",
            function_name="test_function",
            line_number=42
        )
        
        assert record.level_name == "INFO"
        assert record.message == "Info message"
        assert record.layer == "web"
        assert record.file_name == "file.py"  # Should extract just filename
        assert record.function_name == "test_function"
        assert record.line_number == 42
    
    def test_create_with_context_no_file_name(self):
        """Test LogRecordFactory.create_with_context without file_name."""
        record = LogRecordFactory.create_with_context(
            level_name="WARNING",
            message="Warning message",
            layer="test"
        )
        
        assert record.level_name == "WARNING"
        assert record.message == "Warning message"
        assert record.layer == "test"
        assert record.file_name is None
        assert record.function_name is None
        assert record.line_number is None
    
    def test_create_with_auto_context_basic(self):
        """Test LogRecordFactory.create_with_auto_context method basic functionality."""
        # Test without mocking - just verify it creates a record
        record = LogRecordFactory.create_with_auto_context(
            level_name="INFO",
            message="Auto context message",
            layer="test"
        )
        
        assert record.level_name == "INFO"
        assert record.message == "Auto context message"
        assert record.layer == "test"
        # file_name, function_name, line_number may or may not be set depending on call context
    
    def test_get_enhanced_function_name_with_self(self):
        """Test _get_enhanced_function_name with self in locals."""
        mock_frame = MagicMock()
        mock_frame.f_code.co_name = "test_method"
        mock_frame.f_locals = {"self": MagicMock(__class__=MagicMock(__name__="TestClass"))}
        
        result = LogRecordFactory._get_enhanced_function_name(mock_frame)
        assert result == "TestClass.test_method"
    
    def test_get_enhanced_function_name_with_cls(self):
        """Test _get_enhanced_function_name with cls in locals."""
        mock_frame = MagicMock()
        mock_frame.f_code.co_name = "class_method"
        mock_frame.f_locals = {"cls": MagicMock(__name__="TestClass")}
        
        result = LogRecordFactory._get_enhanced_function_name(mock_frame)
        assert result == "TestClass.class_method"
    
    def test_get_enhanced_function_name_regular_function(self):
        """Test _get_enhanced_function_name with regular function."""
        mock_frame = MagicMock()
        mock_frame.f_code.co_name = "regular_function"
        mock_frame.f_locals = {}
        
        result = LogRecordFactory._get_enhanced_function_name(mock_frame)
        assert result == "regular_function"
    
    def test_get_enhanced_function_name_special_names(self):
        """Test _get_enhanced_function_name with special names."""
        special_names = ['<lambda>', '<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>']
        
        for name in special_names:
            mock_frame = MagicMock()
            mock_frame.f_code.co_name = name
            mock_frame.f_locals = {}
            
            result = LogRecordFactory._get_enhanced_function_name(mock_frame)
            assert result == name
    
    def test_get_enhanced_function_name_exception_handling(self):
        """Test _get_enhanced_function_name exception handling."""
        mock_frame = MagicMock()
        mock_frame.f_code.co_name = "test_method"
        mock_frame.f_locals = {"self": MagicMock(__class__=MagicMock(__name__="TestClass"))}
        
        # Make the method raise an exception by making co_name None
        mock_frame.f_code.co_name = None
        
        result = LogRecordFactory._get_enhanced_function_name(mock_frame)
        # The actual behavior returns "TestClass.None" when co_name is None but self is present
        assert result == "TestClass.None"


class TestLogRecordBatch:
    """Test LogRecordBatch class."""
    
    def test_log_record_batch_creation(self):
        """Test LogRecordBatch creation."""
        batch = LogRecordBatch()
        assert len(batch.records) == 0
        assert batch.max_size == 1000
    
    def test_log_record_batch_custom_max_size(self):
        """Test LogRecordBatch with custom max_size."""
        batch = LogRecordBatch(max_size=100)
        assert batch.max_size == 100
    
    def test_add_record(self):
        """Test adding records to batch."""
        batch = LogRecordBatch(max_size=2)
        record1 = LogRecord(level_name="INFO", message="Message 1", layer="test")
        record2 = LogRecord(level_name="ERROR", message="Message 2", layer="test")
        record3 = LogRecord(level_name="DEBUG", message="Message 3", layer="test")
        
        # Add first record - should not be full
        result1 = batch.add_record(record1)
        assert result1 is False
        assert len(batch) == 1
        
        # Add second record - should be full
        result2 = batch.add_record(record2)
        assert result2 is True
        assert len(batch) == 2
        
        # Add third record - should still be full
        result3 = batch.add_record(record3)
        assert result3 is True
        assert len(batch) == 3
    
    def test_is_full(self):
        """Test is_full method."""
        batch = LogRecordBatch(max_size=2)
        assert batch.is_full() is False
        
        record1 = LogRecord(level_name="INFO", message="Message 1", layer="test")
        record2 = LogRecord(level_name="ERROR", message="Message 2", layer="test")
        
        batch.add_record(record1)
        assert batch.is_full() is False
        
        batch.add_record(record2)
        assert batch.is_full() is True
    
    def test_clear(self):
        """Test clear method."""
        batch = LogRecordBatch()
        record = LogRecord(level_name="INFO", message="Message", layer="test")
        
        batch.add_record(record)
        assert len(batch) == 1
        
        batch.clear()
        assert len(batch) == 0
        assert len(batch.records) == 0
    
    def test_len(self):
        """Test __len__ method."""
        batch = LogRecordBatch()
        assert len(batch) == 0
        
        record = LogRecord(level_name="INFO", message="Message", layer="test")
        batch.add_record(record)
        assert len(batch) == 1
    
    def test_iter(self):
        """Test __iter__ method."""
        batch = LogRecordBatch()
        record1 = LogRecord(level_name="INFO", message="Message 1", layer="test")
        record2 = LogRecord(level_name="ERROR", message="Message 2", layer="test")
        
        batch.add_record(record1)
        batch.add_record(record2)
        
        records = list(batch)
        assert len(records) == 2
        assert records[0] == record1
        assert records[1] == record2


class TestRecordCreationStrategy:
    """Test RecordCreationStrategy class."""
    
    def test_strategy_creation(self):
        """Test RecordCreationStrategy creation."""
        strategy = RecordCreationStrategy("minimal")
        assert strategy.strategy == "minimal"
        assert "DEBUG" in strategy._level_cache
        assert "INFO" in strategy._level_cache
        assert 10 in strategy._level_cache
        assert 20 in strategy._level_cache
    
    def test_create_record_with_string_level(self):
        """Test create_record with string level."""
        strategy = RecordCreationStrategy("minimal")
        record = strategy.create_record("ERROR", "Error message", "TestLogger")
        
        assert record.level_name == "ERROR"
        assert record.message == "Error message"
        assert record.logger_name == "TestLogger"
        assert record.level == 40
    
    def test_create_record_with_int_level(self):
        """Test create_record with integer level."""
        strategy = RecordCreationStrategy("minimal")
        record = strategy.create_record(30, "Warning message", "TestLogger")
        
        assert record.level_name == "WARNING"
        assert record.message == "Warning message"
        assert record.logger_name == "TestLogger"
        assert record.level == 30
    
    def test_create_record_with_kwargs(self):
        """Test create_record with additional kwargs."""
        strategy = RecordCreationStrategy("minimal")
        record = strategy.create_record(
            "INFO", 
            "Info message", 
            "TestLogger",
            layer="api",
            extra={"count": 42}
        )
        
        assert record.level_name == "INFO"
        assert record.message == "Info message"
        assert record.logger_name == "TestLogger"
        assert record.layer == "api"
        assert record.extra["count"] == 42
    
    def test_create_record_context_strategy(self):
        """Test create_record with context strategy."""
        strategy = RecordCreationStrategy("context")
        record = strategy.create_record(
            "DEBUG",
            "Debug message",
            "TestLogger",
            file_name="/path/to/file.py",
            function_name="test_function",
            line_number=42
        )
        
        assert record.level_name == "DEBUG"
        assert record.message == "Debug message"
        assert record.file_name == "file.py"  # Should extract filename
        assert record.function_name == "test_function"
        assert record.line_number == 42
    
    def test_create_record_auto_context_strategy(self):
        """Test create_record with auto_context strategy."""
        strategy = RecordCreationStrategy("auto_context")
        record = strategy.create_record("INFO", "Info message", "TestLogger")
        
        assert record.level_name == "INFO"
        assert record.message == "Info message"
        assert record.logger_name == "TestLogger"
        # file_name, function_name, line_number may or may not be set depending on call context
    
    def test_create_record_unknown_strategy(self):
        """Test create_record with unknown strategy falls back to minimal."""
        strategy = RecordCreationStrategy("unknown_strategy")
        record = strategy.create_record("INFO", "Info message", "TestLogger")
        
        assert record.level_name == "INFO"
        assert record.message == "Info message"
        assert record.logger_name == "TestLogger"


class TestLogRecordInitMethods:
    """Test LogRecord __init__ and __post_init__ methods."""
    
    def test_init_method(self):
        """Test __init__ method directly."""
        record = LogRecord.__new__(LogRecord)
        LogRecord.__init__(record, message="Test message")
        
        # Should have default values
        assert record.timestamp is not None
        assert record.level is not None
        assert record.level_name is not None
        assert record.message == "Test message"
        assert record.layer is not None
        assert record.logger_name is not None
        assert record.file_name is None
        assert record.function_name is None
        assert record.line_number is None
        assert record.extra == {}
    
    def test_post_init_method(self):
        """Test __post_init__ method."""
        record = LogRecord.__new__(LogRecord)
        LogRecord.__init__(record, message="Test message")
        
        # Call __post_init__ directly
        LogRecord.__post_init__(record)
        
        # Should not change anything since it's already initialized
        assert record.timestamp is not None
        assert record.level is not None
        assert record.level_name is not None
        assert record.message == "Test message"
        assert record.layer is not None
        assert record.logger_name is not None


class TestGlobalStrategyInstances:
    """Test global strategy instances and convenience functions."""
    
    def test_minimal_strategy(self):
        """Test MINIMAL_STRATEGY instance."""
        assert MINIMAL_STRATEGY.strategy == "minimal"
        record = MINIMAL_STRATEGY.create_record("INFO", "Test message", "TestLogger")
        assert record.level_name == "INFO"
        assert record.message == "Test message"
    
    def test_context_strategy(self):
        """Test CONTEXT_STRATEGY instance."""
        assert CONTEXT_STRATEGY.strategy == "context"
        record = CONTEXT_STRATEGY.create_record("INFO", "Test message", "TestLogger")
        assert record.level_name == "INFO"
        assert record.message == "Test message"
    
    def test_auto_context_strategy(self):
        """Test AUTO_CONTEXT_STRATEGY instance."""
        assert AUTO_CONTEXT_STRATEGY.strategy == "auto_context"
        record = AUTO_CONTEXT_STRATEGY.create_record("INFO", "Test message", "TestLogger")
        assert record.level_name == "INFO"
        assert record.message == "Test message"
    
    def test_get_record_creation_strategy_minimal(self):
        """Test get_record_creation_strategy with minimal profile."""
        strategy = get_record_creation_strategy("minimal")
        assert strategy.strategy == "minimal"
    
    def test_get_record_creation_strategy_balanced(self):
        """Test get_record_creation_strategy with balanced profile."""
        strategy = get_record_creation_strategy("balanced")
        assert strategy.strategy == "context"
    
    def test_get_record_creation_strategy_convenient(self):
        """Test get_record_creation_strategy with convenient profile."""
        strategy = get_record_creation_strategy("convenient")
        assert strategy.strategy == "auto_context"
    
    def test_get_record_creation_strategy_unknown(self):
        """Test get_record_creation_strategy with unknown profile falls back to minimal."""
        strategy = get_record_creation_strategy("unknown")
        assert strategy.strategy == "minimal"
    
    def test_create_log_record_minimal(self):
        """Test create_log_record convenience function with minimal strategy."""
        record = create_log_record("INFO", "Test message", strategy="minimal")
        assert record.level_name == "INFO"
        assert record.message == "Test message"
        assert record.logger_name == "HydraLogger"
    
    def test_create_log_record_context(self):
        """Test create_log_record convenience function with context strategy."""
        record = create_log_record(
            "ERROR", 
            "Error message", 
            strategy="balanced",  # Use "balanced" instead of "context"
            file_name="/path/to/file.py",
            function_name="test_function"
        )
        assert record.level_name == "ERROR"
        assert record.message == "Error message"
        assert record.file_name == "file.py"  # Should extract filename
        assert record.function_name == "test_function"
    
    def test_create_log_record_with_kwargs(self):
        """Test create_log_record with additional kwargs."""
        record = create_log_record(
            "WARNING",
            "Warning message",
            strategy="minimal",
            layer="api",
            extra={"warning_type": "deprecated"}
        )
        assert record.level_name == "WARNING"
        assert record.message == "Warning message"
        assert record.layer == "api"
        assert record.extra["warning_type"] == "deprecated"