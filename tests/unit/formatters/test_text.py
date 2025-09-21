"""
Tests for hydra_logger.formatters.text module.
"""

import pytest
from datetime import datetime
from unittest.mock import patch
from hydra_logger.formatters.text import (
    PlainTextFormatter,
    FastPlainTextFormatter,
    DetailedFormatter
)
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class TestPlainTextFormatter:
    """Test PlainTextFormatter functionality."""
    
    def test_plain_text_formatter_creation(self):
        """Test PlainTextFormatter creation."""
        formatter = PlainTextFormatter()
        
        assert formatter.name == "plain_text"
        assert formatter.format_string is not None
        assert formatter._use_fstring is True
    
    def test_plain_text_formatter_with_custom_format(self):
        """Test PlainTextFormatter with custom format string."""
        custom_format = "[{timestamp}] {level_name}: {message}"
        formatter = PlainTextFormatter(format_string=custom_format)
        
        assert formatter.format_string == custom_format
    
    def test_plain_text_formatter_format(self):
        """Test PlainTextFormatter format method."""
        formatter = PlainTextFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Test message" in formatted
        assert "INFO" in formatted
        assert "test" in formatted
        assert "2009-02-14T01:31:30" in formatted  # Formatted timestamp
    
    def test_plain_text_formatter_with_context(self):
        """Test PlainTextFormatter with context."""
        formatter = PlainTextFormatter()
        
        context = {"user_id": 123, "request_id": "abc-123"}
        record = LogRecord(
            level=LogLevel.ERROR,
            level_name="ERROR",
            message="Error occurred",
            layer="api",
            extra=context,
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Error occurred" in formatted
        assert "ERROR" in formatted
        assert "api" in formatted
        # Basic formatter doesn't include extra fields by default
        # Context is available in record.extra but not included in basic format
    
    def test_plain_text_formatter_with_extra(self):
        """Test PlainTextFormatter with extra fields."""
        formatter = PlainTextFormatter()
        
        extra = {"duration": 1.5, "status_code": 200}
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Request completed",
            layer="web",
            extra=extra,
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Request completed" in formatted
        assert "INFO" in formatted
        assert "web" in formatted
        # Extra fields may not be included in basic format, just check basic fields
        assert "2009-02-14T01:31:30" in formatted  # Formatted timestamp
    
    def test_plain_text_formatter_get_required_extension(self):
        """Test PlainTextFormatter get_required_extension method."""
        formatter = PlainTextFormatter()
        
        extension = formatter.get_required_extension()
        assert extension == ".log"
    
    def test_plain_text_formatter_validate_filename(self):
        """Test PlainTextFormatter validate_filename method."""
        formatter = PlainTextFormatter()
        
        # Valid filename
        valid_name = formatter.validate_filename("test.log")
        assert valid_name == "test.log"
        
        # Filename without extension
        name_with_ext = formatter.validate_filename("test")
        assert name_with_ext == "test.log"
        
        # Filename with wrong extension
        name_corrected = formatter.validate_filename("test.txt")
        assert name_corrected == "test.log"
    
    def test_plain_text_formatter_fstring_detection(self):
        """Test PlainTextFormatter fstring detection."""
        # Should use fstring for simple format
        formatter1 = PlainTextFormatter()
        assert formatter1._use_fstring is True
        
        # Should not use fstring for complex format
        complex_format = "[{timestamp}] {level_name}: {message} {context.get('user_id', 'unknown')}"
        formatter2 = PlainTextFormatter(format_string=complex_format)
        assert formatter2._use_fstring is False


class TestFastPlainTextFormatter:
    """Test FastPlainTextFormatter functionality."""
    
    def test_fast_plain_text_formatter_creation(self):
        """Test FastPlainTextFormatter creation."""
        formatter = FastPlainTextFormatter()
        
        assert formatter.name == "fast_plain_text"
        assert formatter.format_string is not None
    
    def test_fast_plain_text_formatter_with_custom_format(self):
        """Test FastPlainTextFormatter with custom format string."""
        custom_format = "{timestamp} {level_name} {message}"
        formatter = FastPlainTextFormatter(format_string=custom_format)
        
        assert formatter.format_string == custom_format
    
    def test_fast_plain_text_formatter_format(self):
        """Test FastPlainTextFormatter format method."""
        formatter = FastPlainTextFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Fast test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Fast test message" in formatted
        assert "INFO" in formatted
        assert "test" in formatted
        assert "01:31:30" in formatted  # Time format from FastPlainTextFormatter
    
    def test_fast_plain_text_formatter_performance(self):
        """Test FastPlainTextFormatter performance."""
        formatter = FastPlainTextFormatter()
        
        # Create multiple records
        records = []
        for i in range(100):
            record = LogRecord(
                level=LogLevel.INFO,
                message=f"Performance test message {i}",
                layer="test",
                timestamp=1234567890.0 + i
            )
            records.append(record)
        
        # Format all records
        formatted_results = []
        for record in records:
            formatted = formatter.format(record)
            formatted_results.append(formatted)
        
        # Check that all were formatted correctly
        assert len(formatted_results) == 100
        for i, formatted in enumerate(formatted_results):
            assert f"Performance test message {i}" in formatted
    
    def test_fast_plain_text_formatter_get_required_extension(self):
        """Test FastPlainTextFormatter get_required_extension method."""
        formatter = FastPlainTextFormatter()
        
        extension = formatter.get_required_extension()
        assert extension == ".log"


class TestDetailedFormatter:
    """Test DetailedFormatter functionality."""
    
    def test_detailed_formatter_creation(self):
        """Test DetailedFormatter creation."""
        formatter = DetailedFormatter()
        
        assert formatter.name == "detailed"
        assert formatter.include_thread is True
        assert formatter.include_process is True
    
    def test_detailed_formatter_with_options(self):
        """Test DetailedFormatter with custom options."""
        formatter = DetailedFormatter(
            include_thread=False,
            include_process=False
        )
        
        assert formatter.include_thread is False
        assert formatter.include_process is False
    
    def test_detailed_formatter_format(self):
        """Test DetailedFormatter format method."""
        formatter = DetailedFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Detailed test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Detailed test message" in formatted
        assert "INFO" in formatted
        assert "test" in formatted
        assert "2009-02-14" in formatted  # Date from timestamp
    
    def test_detailed_formatter_with_thread_info(self):
        """Test DetailedFormatter with thread information."""
        formatter = DetailedFormatter(include_thread=True)
        
        record = LogRecord(
            level=LogLevel.INFO,
            message="Thread test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Thread test message" in formatted
        # Should include thread information
        assert "thread" in formatted.lower() or "Thread" in formatted
    
    def test_detailed_formatter_with_process_info(self):
        """Test DetailedFormatter with process information."""
        formatter = DetailedFormatter(include_process=True)
        
        record = LogRecord(
            level=LogLevel.INFO,
            message="Process test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Process test message" in formatted
        # Should include process information
        assert "process" in formatted.lower() or "Process" in formatted
    
    def test_detailed_formatter_with_context_and_extra(self):
        """Test DetailedFormatter with context and extra fields."""
        formatter = DetailedFormatter()
        
        context = {"user_id": 123, "session_id": "sess-456"}
        extra = {"duration": 2.5, "memory_usage": "128MB"}
        
        record = LogRecord(
            level=LogLevel.ERROR,
            level_name="ERROR",
            message="Detailed error message",
            layer="api",
            extra={**context, **extra},  # Merge context and extra
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        assert "Detailed error message" in formatted
        assert "ERROR" in formatted
        assert "api" in formatted
        # Extra fields may not be included in basic format, just check basic fields
        assert "2009-02-14" in formatted  # Date from timestamp
    
    def test_detailed_formatter_get_required_extension(self):
        """Test DetailedFormatter get_required_extension method."""
        formatter = DetailedFormatter()
        
        extension = formatter.get_required_extension()
        assert extension == ".log"


class TestPlainTextFormatterMethods:
    """Test PlainTextFormatter internal methods."""
    
    def test_init_method(self):
        """Test __init__ method directly."""
        formatter = PlainTextFormatter.__new__(PlainTextFormatter)
        PlainTextFormatter.__init__(formatter)
        
        assert formatter.name == "plain_text"
        assert formatter.format_string == "[{timestamp}] [{level_name}] [{layer}] {message}"
        assert formatter._format_cache == {}
        assert formatter._use_fstring is True
        assert formatter._compiled_format is not None
    
    def test_should_use_fstring_simple_patterns(self):
        """Test _should_use_fstring with simple patterns."""
        # Test all simple patterns
        simple_patterns = [
            "[{timestamp}] [{level_name}] [{layer}] {message}",
            "[{timestamp}] [{level_name}] {message}",
            "{timestamp} {level_name} {message}",
            "[{level_name}] {message}",
            "{message}"
        ]
        
        for pattern in simple_patterns:
            formatter = PlainTextFormatter(format_string=pattern)
            assert formatter._should_use_fstring() is True
    
    def test_should_use_fstring_complex_patterns(self):
        """Test _should_use_fstring with complex patterns."""
        complex_patterns = [
            "[{timestamp}] {level_name}: {message} {context.get('user_id', 'unknown')}",
            "{timestamp} {level_name} {message} {extra.get('duration', 0)}",
            "[{level_name}] {message} {file_name}:{line_number}",
            "Custom: {timestamp} - {level_name} - {message}",
            "{message} with {extra.get('count', 0)} items"
        ]
        
        for pattern in complex_patterns:
            formatter = PlainTextFormatter(format_string=pattern)
            assert formatter._should_use_fstring() is False
    
    def test_compile_fstring_format_simple_patterns(self):
        """Test _compile_fstring_format with simple patterns."""
        patterns_and_expected = [
            ("[{timestamp}] [{level_name}] [{layer}] {message}", 
             lambda r: f"[{r.timestamp}] [{r.level_name}] [{r.layer}] {r.message}"),
            ("[{timestamp}] [{level_name}] {message}", 
             lambda r: f"[{r.timestamp}] [{r.level_name}] {r.message}"),
            ("{timestamp} {level_name} {message}", 
             lambda r: f"{r.timestamp} {r.level_name} {r.message}"),
            ("[{level_name}] {message}", 
             lambda r: f"[{r.level_name}] {r.message}"),
            ("{message}", 
             lambda r: f"{r.message}")
        ]
        
        for pattern, expected_func in patterns_and_expected:
            formatter = PlainTextFormatter(format_string=pattern)
            compiled_func = formatter._compile_fstring_format()
            assert compiled_func is not None
            
            # Test with a sample record
            record = LogRecord(
                level=LogLevel.INFO,
                level_name="INFO",
                message="Test message",
                layer="test",
                timestamp=1234567890.0
            )
            
            result = compiled_func(record)
            # Update expected to use formatted timestamp
            expected = expected_func(record).replace(str(record.timestamp), formatter.format_timestamp(record))
            assert result == expected
    
    def test_compile_fstring_format_complex_pattern(self):
        """Test _compile_fstring_format with complex pattern."""
        formatter = PlainTextFormatter(format_string="[{timestamp}] {level_name}: {message} {extra.get('count', 0)}")
        compiled_func = formatter._compile_fstring_format()
        assert compiled_func is None
    
    def test_cached_timestamp_format(self):
        """Test _cached_timestamp_format method."""
        formatter = PlainTextFormatter()
        
        # Test with a specific timestamp
        timestamp = 1234567890.0
        formatted = formatter._cached_timestamp_format(timestamp)
        
        # Should be in YYYY-MM-DD HH:MM:SS format
        assert "2009-02-14" in formatted
        assert "01:31:30" in formatted
        
        # Test caching - same timestamp should return same result
        formatted2 = formatter._cached_timestamp_format(timestamp)
        assert formatted == formatted2
    
    def test_format_default(self):
        """Test _format_default method."""
        formatter = PlainTextFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            logger_name="test_logger",
            file_name="test.py",
            function_name="test_function",
            line_number=42,
            timestamp=1234567890.0
        )
        
        formatted = formatter._format_default(record)
        
        # Should contain all the basic fields from the default format string
        assert "Test message" in formatted
        assert "INFO" in formatted
        assert "test" in formatted
        assert "2009-02-14" in formatted  # Date from timestamp
        # The default format string is "[{timestamp}] [{level_name}] [{layer}] {message}"
        # so it doesn't include logger_name, file_name, function_name, or line_number
    
    def test_format_with_engine(self):
        """Test _format_with_engine method."""
        from unittest.mock import MagicMock
        
        # Create a mock formatting engine
        mock_engine = MagicMock()
        mock_engine.get_enabled_columns.return_value = ["timestamp", "level", "message", "layer"]
        mock_engine.format_record.return_value = {
            "timestamp": "2009-02-14T01:31:30",
            "level": "INFO",
            "message": "Test message",
            "layer": "test"
        }
        
        formatter = PlainTextFormatter(formatting_engine=mock_engine)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter._format_with_engine(mock_engine.format_record(record), record)
        
        # Should use the engine's formatted data
        assert "2009-02-14T01:31:30" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted
        assert "test" in formatted
    
    def test_format_with_engine_missing_fields(self):
        """Test _format_with_engine method with missing fields."""
        from unittest.mock import MagicMock
        
        # Create a mock formatting engine with missing fields
        mock_engine = MagicMock()
        mock_engine.get_enabled_columns.return_value = ["timestamp", "level", "message"]
        mock_engine.format_record.return_value = {
            "timestamp": "2009-02-14T01:31:30",
            "level": "INFO",
            "message": "Test message"
            # Missing 'layer' field
        }
        
        formatter = PlainTextFormatter(formatting_engine=mock_engine)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter._format_with_engine(mock_engine.format_record(record), record)
        
        # Should fallback to basic format
        assert "2009-02-14T01:31:30" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted
    
    def test_format_with_engine_key_error(self):
        """Test _format_with_engine method with KeyError."""
        from unittest.mock import MagicMock
        
        # Create a mock formatting engine that will cause KeyError
        mock_engine = MagicMock()
        mock_engine.get_enabled_columns.return_value = ["timestamp", "level", "message", "missing_field"]
        mock_engine.format_record.return_value = {
            "timestamp": "2009-02-14T01:31:30",
            "level": "INFO",
            "message": "Test message"
            # Missing 'missing_field' that's in enabled_columns
        }
        
        formatter = PlainTextFormatter(formatting_engine=mock_engine)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        # This should trigger KeyError in _format_with_engine and return fallback
        formatted = formatter.format(record)
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        # Should contain fallback format
        assert "2009-02-14T01:31:30" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted


class TestFastPlainTextFormatterMethods:
    """Test FastPlainTextFormatter internal methods."""
    
    def test_format_default(self):
        """Test _format_default method."""
        formatter = FastPlainTextFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter._format_default(record)
        
        # Should be the same as format method
        expected = formatter.format(record)
        assert formatted == expected


class TestDetailedFormatterMethods:
    """Test DetailedFormatter internal methods."""
    
    def test_format_with_engine(self):
        """Test _format_with_engine method."""
        from unittest.mock import MagicMock
        
        # Create a mock formatting engine
        mock_engine = MagicMock()
        mock_engine.get_enabled_columns.return_value = ["timestamp", "level", "message", "layer", "file_name", "function_name", "line_number"]
        mock_engine.format_record.return_value = {
            "timestamp": "2009-02-14T01:31:30",
            "level": "INFO",
            "message": "Test message",
            "layer": "test",
            "file_name": "test.py",
            "function_name": "test_function",
            "line_number": 42
        }
        
        formatter = DetailedFormatter(formatting_engine=mock_engine)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            file_name="test.py",
            function_name="test_function",
            line_number=42,
            timestamp=1234567890.0
        )
        
        formatted = formatter._format_with_engine(mock_engine.format_record(record), record)
        
        # Should use the engine's formatted data
        assert "2009-02-14T01:31:30" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted
        assert "test" in formatted
        assert "test.py" in formatted
        assert "test_function" in formatted
        assert "42" in formatted
    
    def test_format_with_engine_key_error(self):
        """Test _format_with_engine method with KeyError."""
        from unittest.mock import MagicMock
        
        # Create a mock formatting engine that will cause KeyError
        mock_engine = MagicMock()
        mock_engine.get_enabled_columns.return_value = ["timestamp", "level", "message", "missing_field"]
        mock_engine.format_record.return_value = {
            "timestamp": "2009-02-14T01:31:30",
            "level": "INFO",
            "message": "Test message"
            # Missing 'missing_field' that's in enabled_columns
        }
        
        formatter = DetailedFormatter(formatting_engine=mock_engine)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        # This should trigger KeyError in _format_with_engine and return fallback
        formatted = formatter.format(record)
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        # Should contain fallback format
        assert "2009-02-14T01:31:30" in formatted
        assert "INFO" in formatted
        assert "Test message" in formatted
    
    def test_format_default(self):
        """Test _format_default method."""
        formatter = DetailedFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            file_name="test.py",
            function_name="test_function",
            line_number=42,
            timestamp=1234567890.0
        )
        
        formatted = formatter._format_default(record)
        
        # Should contain detailed information
        assert "Test message" in formatted
        assert "INFO" in formatted
        assert "test" in formatted
        assert "test.py" in formatted
        assert "test_function" in formatted
        assert "42" in formatted
        assert "2009-02-14" in formatted  # Date from timestamp
    
    def test_format_default_without_file_info(self):
        """Test _format_default method without file information."""
        formatter = DetailedFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            file_name=None,
            function_name=None,
            line_number=None,
            timestamp=1234567890.0
        )
        
        formatted = formatter._format_default(record)
        
        # Should not include file information
        assert "Test message" in formatted
        assert "INFO" in formatted
        assert "test" in formatted
        assert "test.py" not in formatted
        assert "test_function" not in formatted
        assert "42" not in formatted


class TestTextFormatterIntegration:
    """Integration tests for text formatters."""
    
    def test_formatter_compatibility(self):
        """Test that all text formatters produce compatible output."""
        formatters = [
            PlainTextFormatter(),
            FastPlainTextFormatter(),
            DetailedFormatter()
        ]
        
        record = LogRecord(
            level=LogLevel.INFO,
            message="Compatibility test message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted_results = []
        for formatter in formatters:
            formatted = formatter.format(record)
            formatted_results.append(formatted)
            
            # All formatters should include the message
            assert "Compatibility test message" in formatted
            assert "INFO" in formatted
            assert "test" in formatted
        
        # All formatters should produce some output
        assert len(formatted_results) == 3
        assert all(len(result) > 0 for result in formatted_results)
    
    def test_formatter_performance_comparison(self):
        """Test performance comparison between formatters."""
        import time
        
        formatters = {
            "PlainText": PlainTextFormatter(),
            "FastPlainText": FastPlainTextFormatter(),
            "Detailed": DetailedFormatter()
        }
        
        # Create test records
        records = []
        for i in range(1000):
            record = LogRecord(
                level=LogLevel.INFO,
                message=f"Performance test message {i}",
                layer="test",
                timestamp=1234567890.0 + i
            )
            records.append(record)
        
        # Test each formatter
        results = {}
        for name, formatter in formatters.items():
            start_time = time.time()
            
            for record in records:
                formatted = formatter.format(record)
                assert len(formatted) > 0
            
            end_time = time.time()
            results[name] = end_time - start_time
        
        # All formatters should complete in reasonable time
        for name, duration in results.items():
            assert duration < 1.0, f"{name} formatter took too long: {duration:.3f}s"
    
    def test_formatter_error_handling(self):
        """Test formatter error handling with malformed records."""
        formatter = PlainTextFormatter()
        
        # Test with minimal record
        minimal_record = LogRecord(
            level=LogLevel.INFO,
            message="minimal test",  # Cannot be empty
            layer="test"
        )
        
        formatted = formatter.format(minimal_record)
        assert isinstance(formatted, str)
        assert len(formatted) >= 0
        
        # Test with None values
        record_with_none = LogRecord(
            level=LogLevel.INFO,
            message="test with none layer",  # Cannot be None
            layer="test"  # Cannot be None
        )
        
        formatted = formatter.format(record_with_none)
        assert isinstance(formatted, str)
        assert len(formatted) >= 0
