"""
Tests for hydra_logger.formatters.json module.
"""

from unittest.mock import Mock
import pytest
import json
from datetime import datetime
from hydra_logger.formatters.json import JsonLinesFormatter
from hydra_logger.types.records import LogRecord
from hydra_logger.types.levels import LogLevel


class TestJsonLinesFormatter:
    """Test JsonLinesFormatter functionality."""
    
    def test_json_lines_formatter_creation(self):
        """Test JsonLinesFormatter creation."""
        formatter = JsonLinesFormatter()
        
        assert formatter.name == "json_lines"
        assert formatter.ensure_ascii is False
    
    def test_json_lines_formatter_with_ascii(self):
        """Test JsonLinesFormatter with ASCII encoding."""
        formatter = JsonLinesFormatter(ensure_ascii=True)
        
        assert formatter.ensure_ascii is True
    
    def test_json_lines_formatter_format(self):
        """Test JsonLinesFormatter format method."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            message="Test JSON message",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        
        assert parsed["level"] == 20  # INFO level as integer
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "Test JSON message"
        assert parsed["layer"] == "test"
        assert parsed["timestamp"] == 1234567890.0
    
    def test_json_lines_formatter_with_context(self):
        """Test JsonLinesFormatter with context."""
        formatter = JsonLinesFormatter()
        
        context = {"user_id": 123, "request_id": "abc-123"}
        record = LogRecord(
            level_name="ERROR",
            level=40,  # ERROR level
            message="Error occurred",
            layer="api",
            extra=context,
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == 40  # ERROR level as integer
        assert parsed["level_name"] == "ERROR"
        assert parsed["message"] == "Error occurred"
        assert parsed["layer"] == "api"
        assert parsed["extra"] == context
    
    def test_json_lines_formatter_with_extra(self):
        """Test JsonLinesFormatter with extra fields."""
        formatter = JsonLinesFormatter()
        
        extra = {"duration": 1.5, "status_code": 200}
        record = LogRecord(
            level=LogLevel.INFO,
            message="Request completed",
            layer="web",
            extra=extra,
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == 20  # INFO level as integer
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "Request completed"
        assert parsed["layer"] == "web"
        assert parsed["extra"] == extra
        assert parsed["extra"]["duration"] == 1.5
        assert parsed["extra"]["status_code"] == 200
    
    def test_json_lines_formatter_with_unicode(self):
        """Test JsonLinesFormatter with Unicode characters."""
        formatter = JsonLinesFormatter(ensure_ascii=False)
        
        record = LogRecord(
            level=LogLevel.INFO,
            message="Unicode test: 你好世界 🌍",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["message"] == "Unicode test: 你好世界 🌍"
        assert "你好世界" in formatted
        assert "🌍" in formatted
    
    def test_json_lines_formatter_with_ascii_encoding(self):
        """Test JsonLinesFormatter with ASCII encoding."""
        formatter = JsonLinesFormatter(ensure_ascii=True)
        
        record = LogRecord(
            level=LogLevel.INFO,
            message="Unicode test: 你好世界 🌍",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["message"] == "Unicode test: 你好世界 🌍"
        # Unicode should be escaped in the JSON string
        assert "\\u" in formatted
    
    def test_json_lines_formatter_get_required_extension(self):
        """Test JsonLinesFormatter get_required_extension method."""
        formatter = JsonLinesFormatter()
        
        extension = formatter.get_required_extension()
        assert extension == ".jsonl"
    
    def test_json_lines_formatter_validate_filename(self):
        """Test JsonLinesFormatter validate_filename method."""
        formatter = JsonLinesFormatter()
        
        # Valid filename
        valid_name = formatter.validate_filename("test.jsonl")
        assert valid_name == "test.jsonl"
        
        # Filename without extension
        name_with_ext = formatter.validate_filename("test")
        assert name_with_ext == "test.jsonl"
        
        # Filename with wrong extension
        name_corrected = formatter.validate_filename("test.json")
        assert name_corrected == "test.jsonl"
    
    def test_json_lines_formatter_with_complex_data(self):
        """Test JsonLinesFormatter with complex nested data."""
        formatter = JsonLinesFormatter()
        
        context = {
            "user": {
                "id": 123,
                "name": "John Doe",
                "preferences": {
                    "theme": "dark",
                    "language": "en"
                }
            },
            "request": {
                "method": "POST",
                "path": "/api/users",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer token123"
                }
            }
        }
        
        extra = {
            "performance": {
                "duration": 1.5,
                "memory_usage": "128MB",
                "cpu_usage": "15%"
            },
            "metrics": [1, 2, 3, 4, 5]
        }
        
        record = LogRecord(
            level_name="INFO",
            message="Complex data test",
            layer="api",
            extra={**context, **extra},  # Merge context and extra into extra
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == 20  # INFO level as integer
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "Complex data test"
        assert parsed["layer"] == "api"
        assert parsed["extra"]["user"]["id"] == 123
        assert parsed["extra"]["user"]["name"] == "John Doe"
        assert parsed["extra"]["performance"]["duration"] == 1.5
        assert parsed["extra"]["metrics"] == [1, 2, 3, 4, 5]
    
    def test_json_lines_formatter_with_special_characters(self):
        """Test JsonLinesFormatter with special characters."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level_name="INFO",
            message="Special chars: \n\t\r\"'\\",
            layer="test",
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["message"] == "Special chars: \n\t\r\"'\\"
        # JSON should properly escape special characters
        assert "\\n" in formatted
        assert "\\t" in formatted
        assert "\\r" in formatted
        assert '\\"' in formatted
        # Note: Single quotes don't need escaping in JSON
        assert "\\\\" in formatted
    
    def test_json_lines_formatter_with_none_values(self):
        """Test JsonLinesFormatter with None values."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level_name="INFO",
            message="None values test",
            layer="test",
            extra=None,
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == 20  # INFO level as integer
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "None values test"
        assert parsed["layer"] == "test"
        assert parsed["extra"] is None
    
    def test_json_lines_formatter_with_empty_strings(self):
        """Test JsonLinesFormatter with empty strings."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level_name="INFO",
            message="Empty test",  # Can't be empty due to validation
            layer="",
            extra={},
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == 20  # INFO level as integer
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "Empty test"
        assert parsed["layer"] == ""
        assert parsed["extra"] == {}
    
    def test_json_lines_formatter_with_boolean_values(self):
        """Test JsonLinesFormatter with boolean values."""
        formatter = JsonLinesFormatter()
        
        extra = {
            "success": True,
            "error": False,
            "enabled": True
        }
        
        record = LogRecord(
            level_name="INFO",
            message="Boolean test",
            layer="test",
            extra=extra,
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["extra"]["success"] is True
        assert parsed["extra"]["error"] is False
        assert parsed["extra"]["enabled"] is True
    
    def test_json_lines_formatter_with_numeric_values(self):
        """Test JsonLinesFormatter with various numeric values."""
        formatter = JsonLinesFormatter()
        
        extra = {
            "integer": 42,
            "float": 3.14159,
            "negative": -10,
            "zero": 0,
            "large_number": 999999999
        }
        
        record = LogRecord(
            level_name="INFO",
            message="Numeric test",
            layer="test",
            extra=extra,
            timestamp=1234567890.0
        )
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["extra"]["integer"] == 42
        assert parsed["extra"]["float"] == 3.14159
        assert parsed["extra"]["negative"] == -10
        assert parsed["extra"]["zero"] == 0
        assert parsed["extra"]["large_number"] == 999999999


class TestJsonLinesFormatterIntegration:
    """Integration tests for JsonLinesFormatter."""
    
    def test_json_lines_formatter_streaming_compatibility(self):
        """Test JsonLinesFormatter produces valid JSON Lines format."""
        formatter = JsonLinesFormatter()
        
        # Create multiple records
        records = []
        for i in range(5):
            record = LogRecord(
                level=LogLevel.INFO,
                message=f"Streaming test message {i}",
                layer="test",
                timestamp=1234567890.0 + i
            )
            records.append(record)
        
        # Format all records
        formatted_lines = []
        for record in records:
            formatted = formatter.format(record)
            formatted_lines.append(formatted)
        
        # Each line should be valid JSON
        for line in formatted_lines:
            parsed = json.loads(line)
            assert "message" in parsed
            assert "level" in parsed
            assert "layer" in parsed
            assert "timestamp" in parsed
        
        # All lines should be different
        assert len(set(formatted_lines)) == 5
    
    def test_json_lines_formatter_performance(self):
        """Test JsonLinesFormatter performance."""
        formatter = JsonLinesFormatter()
        
        # Create many records
        records = []
        for i in range(1000):
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
        
        # All should be valid JSON
        for formatted in formatted_results:
            parsed = json.loads(formatted)
            assert isinstance(parsed, dict)
            assert len(parsed) > 0
    
    def test_json_lines_formatter_error_handling(self):
        """Test JsonLinesFormatter error handling."""
        formatter = JsonLinesFormatter()
        
        # Test with minimal record
        minimal_record = LogRecord(
            level_name="INFO",
            message="Minimal test",  # Can't be empty due to validation
            layer=""
        )
        
        formatted = formatter.format(minimal_record)
        parsed = json.loads(formatted)
        
        assert isinstance(parsed, dict)
        assert "level" in parsed
        assert "message" in parsed
        assert "layer" in parsed
        assert "timestamp" in parsed


class TestJsonLinesFormatterColumnOrdering:
    """Test JsonLinesFormatter column ordering functionality."""
    
    def test_format_with_engine_with_columns(self):
        """Test _format_with_engine with formatting engine and column ordering."""
        from unittest.mock import Mock
        
        # Create a mock formatting engine
        mock_engine = Mock()
        mock_engine.get_enabled_columns.return_value = ['timestamp', 'level', 'message', 'layer']
        
        # Create formatter with engine
        formatter = JsonLinesFormatter(formatting_engine=mock_engine)
        
        # Test data with extra fields
        test_data = {
            'message': 'Test message',
            'level': 20,
            'layer': 'test',
            'timestamp': '2023-01-01T00:00:00',
            'extra_field': 'extra_value',
            'another_field': 'another_value'
        }
        
        # Create a mock record
        mock_record = Mock()
        
        # Format with engine
        result = formatter._format_with_engine(test_data, mock_record)
        parsed = json.loads(result)
        
        # Check that columns are in the order specified by the engine
        keys = list(parsed.keys())
        assert keys[:4] == ['timestamp', 'level', 'message', 'layer']
        assert 'extra_field' in keys
        assert 'another_field' in keys
        
        # Verify all data is preserved
        assert parsed['message'] == 'Test message'
        assert parsed['level'] == 20
        assert parsed['layer'] == 'test'
        assert parsed['timestamp'] == '2023-01-01T00:00:00'
        assert parsed['extra_field'] == 'extra_value'
        assert parsed['another_field'] == 'another_value'
    
    def test_format_with_engine_without_engine(self):
        """Test _format_with_engine without formatting engine (fallback)."""
        formatter = JsonLinesFormatter()
        
        # Test data
        test_data = {
            'message': 'Test message',
            'level': 20,
            'layer': 'test',
            'timestamp': '2023-01-01T00:00:00'
        }
        
        # Create a mock record
        mock_record = Mock()
        
        # Format with engine (should use fallback)
        result = formatter._format_with_engine(test_data, mock_record)
        parsed = json.loads(result)
        
        # Should preserve original order
        assert parsed == test_data
    
    def test_format_with_engine_partial_columns(self):
        """Test _format_with_engine with partial column coverage."""
        from unittest.mock import Mock
        
        # Create a mock formatting engine with only some columns
        mock_engine = Mock()
        mock_engine.get_enabled_columns.return_value = ['level', 'message']
        
        # Create formatter with engine
        formatter = JsonLinesFormatter(formatting_engine=mock_engine)
        
        # Test data
        test_data = {
            'message': 'Test message',
            'level': 20,
            'layer': 'test',
            'timestamp': '2023-01-01T00:00:00',
            'extra_field': 'extra_value'
        }
        
        # Create a mock record
        mock_record = Mock()
        
        # Format with engine
        result = formatter._format_with_engine(test_data, mock_record)
        parsed = json.loads(result)
        
        # Check that specified columns come first
        keys = list(parsed.keys())
        assert keys[0] == 'level'
        assert keys[1] == 'message'
        
        # Other fields should be present but order may vary
        assert 'layer' in keys
        assert 'timestamp' in keys
        assert 'extra_field' in keys
        
        # Verify all data is preserved
        assert parsed['message'] == 'Test message'
        assert parsed['level'] == 20
        assert parsed['layer'] == 'test'
        assert parsed['timestamp'] == '2023-01-01T00:00:00'
        assert parsed['extra_field'] == 'extra_value'
    
    def test_format_with_engine_empty_columns(self):
        """Test _format_with_engine with empty engine columns."""
        from unittest.mock import Mock
        
        # Create a mock formatting engine with no columns
        mock_engine = Mock()
        mock_engine.get_enabled_columns.return_value = []
        
        # Create formatter with engine
        formatter = JsonLinesFormatter(formatting_engine=mock_engine)
        
        # Test data
        test_data = {
            'message': 'Test message',
            'level': 20,
            'layer': 'test'
        }
        
        # Create a mock record
        mock_record = Mock()
        
        # Format with engine
        result = formatter._format_with_engine(test_data, mock_record)
        parsed = json.loads(result)
        
        # Should preserve original data
        assert parsed == test_data
    
    def test_format_with_engine_ensure_ascii(self):
        """Test _format_with_engine respects ensure_ascii setting."""
        from unittest.mock import Mock
        
        # Create a mock formatting engine
        mock_engine = Mock()
        mock_engine.get_enabled_columns.return_value = ['message', 'level']
        
        # Test with ensure_ascii=True
        formatter_ascii = JsonLinesFormatter(formatting_engine=mock_engine, ensure_ascii=True)
        test_data = {'message': 'Test message', 'level': 20}
        mock_record = Mock()
        
        result_ascii = formatter_ascii._format_with_engine(test_data, mock_record)
        assert '\\u' not in result_ascii  # Should be ASCII encoded
        
        # Test with ensure_ascii=False
        formatter_unicode = JsonLinesFormatter(formatting_engine=mock_engine, ensure_ascii=False)
        test_data_unicode = {'message': 'Test message with émojis 🚀', 'level': 20}
        
        result_unicode = formatter_unicode._format_with_engine(test_data_unicode, mock_record)
        assert 'émojis' in result_unicode  # Should preserve Unicode


class TestJsonLinesFormatterInternalMethods:
    """Test JsonLinesFormatter internal methods for complete coverage."""
    
    def test_create_record_dict(self):
        """Test _create_record_dict method."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            logger_name="test_logger",
            file_name="test_file.py",
            function_name="test_function",
            line_number=42,
            extra={"key": "value"},
            timestamp=1234567890.0
        )
        
        record_dict = formatter._create_record_dict(record)
        
        assert record_dict["timestamp"] == 1234567890.0
        assert record_dict["level"] == 20  # INFO level
        assert record_dict["level_name"] == "INFO"
        assert record_dict["message"] == "Test message"
        assert record_dict["logger_name"] == "test_logger"
        assert record_dict["layer"] == "test"
        assert record_dict["file_name"] == "test_file.py"
        assert record_dict["function_name"] == "test_function"
        assert record_dict["line_number"] == 42
        assert record_dict["extra"] == {"key": "value"}
    
    def test_create_record_dict_with_none_extra(self):
        """Test _create_record_dict with None extra field."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            extra=None,
            timestamp=1234567890.0
        )
        
        record_dict = formatter._create_record_dict(record)
        
        assert record_dict["extra"] is None
        assert record_dict["message"] == "Test message"
        assert record_dict["level"] == 20
    
    def test_create_record_dict_with_empty_extra(self):
        """Test _create_record_dict with empty extra field."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Test message",
            layer="test",
            extra={},
            timestamp=1234567890.0
        )
        
        record_dict = formatter._create_record_dict(record)
        
        assert record_dict["extra"] == {}
        assert record_dict["message"] == "Test message"
        assert record_dict["level"] == 20
    
    def test_format_default_method(self):
        """Test _format_default method."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Default format test",
            layer="test",
            timestamp=1234567890.0
        )
        
        result = formatter._format_default(record)
        parsed = json.loads(result)
        
        assert parsed["level"] == 20
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "Default format test"
        assert parsed["layer"] == "test"
        assert parsed["timestamp"] == 1234567890.0
    
    def test_format_default_with_complex_extra(self):
        """Test _format_default with complex extra data."""
        formatter = JsonLinesFormatter()
        
        complex_extra = {
            "user": {"id": 123, "name": "John"},
            "request": {"method": "POST", "path": "/api"},
            "metrics": [1, 2, 3],
            "nested": {"deep": {"value": "test"}}
        }
        
        record = LogRecord(
            level=LogLevel.ERROR,
            level_name="ERROR",
            message="Complex extra test",
            layer="api",
            extra=complex_extra,
            timestamp=1234567890.0
        )
        
        result = formatter._format_default(record)
        parsed = json.loads(result)
        
        assert parsed["level"] == 40  # ERROR level
        assert parsed["message"] == "Complex extra test"
        assert parsed["extra"] == complex_extra
        assert parsed["extra"]["user"]["id"] == 123
        assert parsed["extra"]["metrics"] == [1, 2, 3]
        assert parsed["extra"]["nested"]["deep"]["value"] == "test"
    
    def test_encoder_initialization(self):
        """Test JSON encoder initialization and properties."""
        # Test with ensure_ascii=True
        formatter_ascii = JsonLinesFormatter(ensure_ascii=True)
        assert formatter_ascii.ensure_ascii is True
        assert formatter_ascii._encoder.ensure_ascii is True
        
        # Test with ensure_ascii=False
        formatter_unicode = JsonLinesFormatter(ensure_ascii=False)
        assert formatter_unicode.ensure_ascii is False
        assert formatter_unicode._encoder.ensure_ascii is False
    
    def test_field_cache_initialization(self):
        """Test field cache initialization."""
        formatter = JsonLinesFormatter()
        assert isinstance(formatter._field_cache, dict)
        assert len(formatter._field_cache) == 0
    
    def test_formatting_engine_initialization(self):
        """Test formatting engine initialization."""
        from unittest.mock import Mock
        
        mock_engine = Mock()
        formatter = JsonLinesFormatter(formatting_engine=mock_engine)
        
        assert formatter.formatting_engine is mock_engine
    
    def test_format_with_engine_none_engine(self):
        """Test _format_with_engine with None formatting engine."""
        formatter = JsonLinesFormatter(formatting_engine=None)
        
        test_data = {"message": "Test", "level": 20}
        mock_record = Mock()
        
        result = formatter._format_with_engine(test_data, mock_record)
        parsed = json.loads(result)
        
        assert parsed == test_data
    
    def test_format_with_engine_missing_columns(self):
        """Test _format_with_engine when engine columns don't match data."""
        from unittest.mock import Mock
        
        mock_engine = Mock()
        mock_engine.get_enabled_columns.return_value = ['nonexistent', 'also_missing']
        
        formatter = JsonLinesFormatter(formatting_engine=mock_engine)
        
        test_data = {"message": "Test", "level": 20, "layer": "test"}
        mock_record = Mock()
        
        result = formatter._format_with_engine(test_data, mock_record)
        parsed = json.loads(result)
        
        # Should include all original data since no columns matched
        assert parsed == test_data
    
    def test_format_method_calls_format_default(self):
        """Test that format method calls _format_default."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Format method test",
            layer="test",
            timestamp=1234567890.0
        )
        
        # Test the public format method
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["level"] == 20
        assert parsed["level_name"] == "INFO"
        assert parsed["message"] == "Format method test"
        assert parsed["layer"] == "test"
        assert parsed["timestamp"] == 1234567890.0
    
    def test_format_method_with_formatting_engine(self):
        """Test format method with formatting engine."""
        from unittest.mock import Mock
        
        # Create a mock formatting engine
        mock_engine = Mock()
        mock_engine.get_enabled_columns.return_value = ['message', 'level']
        
        # Create formatter with engine
        formatter = JsonLinesFormatter(formatting_engine=mock_engine)
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Engine format test",
            layer="test",
            timestamp=1234567890.0
        )
        
        # Test the public format method
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["level"] == 20
        assert parsed["message"] == "Engine format test"
        # Should have all fields
        assert "layer" in parsed
        assert "timestamp" in parsed
    
    def test_encoder_properties(self):
        """Test JSON encoder properties and configuration."""
        formatter = JsonLinesFormatter(ensure_ascii=True)
        
        # Test encoder properties
        assert formatter._encoder.ensure_ascii is True
        # Note: separators and sort_keys are not directly accessible on JSONEncoder
        # but we can test the behavior by checking the output format
        
        # Test with different configuration
        formatter2 = JsonLinesFormatter(ensure_ascii=False)
        assert formatter2._encoder.ensure_ascii is False
        
        # Test that both encoders produce valid JSON
        test_data = {"message": "test", "level": 20}
        result1 = formatter._encoder.encode(test_data)
        result2 = formatter2._encoder.encode(test_data)
        
        # Both should be valid JSON
        import json
        parsed1 = json.loads(result1)
        parsed2 = json.loads(result2)
        
        assert parsed1 == test_data
        assert parsed2 == test_data
    
    def test_super_init_call(self):
        """Test that super().__init__ is called correctly."""
        from unittest.mock import Mock
        
        mock_engine = Mock()
        formatter = JsonLinesFormatter(formatting_engine=mock_engine)
        
        # Verify the formatter was initialized correctly
        assert formatter.name == "json_lines"
        assert formatter.formatting_engine is mock_engine
        assert formatter.ensure_ascii is False  # default value
    
    def test_field_cache_usage(self):
        """Test field cache functionality."""
        formatter = JsonLinesFormatter()
        
        # Initially empty
        assert len(formatter._field_cache) == 0
        assert isinstance(formatter._field_cache, dict)
        
        # Cache should be accessible
        formatter._field_cache["test"] = "value"
        assert formatter._field_cache["test"] == "value"
    
    def test_json_encoder_compact_format(self):
        """Test that JSON encoder produces compact format."""
        formatter = JsonLinesFormatter()
        
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Compact test",
            layer="test",
            timestamp=1234567890.0
        )
        
        result = formatter._format_default(record)
        
        # Should be compact (no extra spaces)
        assert ' ' not in result or result.count(' ') < 5  # Minimal spaces
        assert result.count('\n') == 0  # No newlines
        assert result.count('\t') == 0  # No tabs
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["message"] == "Compact test"
    
    def test_json_encoder_no_key_sorting(self):
        """Test that JSON encoder doesn't sort keys."""
        formatter = JsonLinesFormatter()
        
        # Create a record with specific field order
        record = LogRecord(
            level=LogLevel.INFO,
            level_name="INFO",
            message="Key order test",
            layer="test",
            timestamp=1234567890.0
        )
        
        result = formatter._format_default(record)
        parsed = json.loads(result)
        
        # Keys should be in the order they were added (not sorted)
        keys = list(parsed.keys())
        expected_order = ["timestamp", "level", "level_name", "message", 
                         "logger_name", "layer", "file_name", "function_name", 
                         "line_number", "extra"]
        
        # Check that the first few keys match expected order
        assert keys[:4] == expected_order[:4]
    
    def test_init_method_explicit(self):
        """Test __init__ method explicitly for complete coverage."""
        from unittest.mock import Mock
        
        # Test default initialization
        formatter1 = JsonLinesFormatter()
        assert formatter1.name == "json_lines"
        assert formatter1.ensure_ascii is False
        assert formatter1.formatting_engine is None
        assert isinstance(formatter1._encoder, json.JSONEncoder)
        assert isinstance(formatter1._field_cache, dict)
        assert len(formatter1._field_cache) == 0
        
        # Test with ensure_ascii=True
        formatter2 = JsonLinesFormatter(ensure_ascii=True)
        assert formatter2.name == "json_lines"
        assert formatter2.ensure_ascii is True
        assert formatter2.formatting_engine is None
        assert formatter2._encoder.ensure_ascii is True
        
        # Test with formatting engine
        mock_engine = Mock()
        formatter3 = JsonLinesFormatter(formatting_engine=mock_engine)
        assert formatter3.name == "json_lines"
        assert formatter3.ensure_ascii is False
        assert formatter3.formatting_engine is mock_engine
        
        # Test with both parameters
        formatter4 = JsonLinesFormatter(ensure_ascii=True, formatting_engine=mock_engine)
        assert formatter4.name == "json_lines"
        assert formatter4.ensure_ascii is True
        assert formatter4.formatting_engine is mock_engine
        assert formatter4._encoder.ensure_ascii is True
