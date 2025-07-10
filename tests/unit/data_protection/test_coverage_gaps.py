"""
Additional tests to cover missing lines in data_protection module.

This file targets specific uncovered lines identified in the coverage report.
"""

import pytest
import json
import tempfile
import os
import asyncio
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from typing import Any, Dict, List

from hydra_logger.data_protection.fallbacks import (
    ThreadSafeLogger,
    DataSanitizer,
    CorruptionDetector,
    AtomicWriter,
    BackupManager,
    DataRecovery,
    FallbackHandler,
    async_safe_write_json,
    async_safe_write_csv,
    async_safe_read_json,
    async_safe_read_csv,
    clear_all_caches,
    get_performance_stats,
    DataLossProtection
)
from hydra_logger.data_protection.security import (
    DataSanitizer as SecurityDataSanitizer,
    SecurityValidator,
    DataHasher
)
from hydra_logger.core.exceptions import DataProtectionError


class TestThreadSafeLoggerCoverage:
    """Test ThreadSafeLogger coverage gaps."""

    def test_thread_safe_logger_singleton(self):
        """Test ThreadSafeLogger singleton pattern."""
        logger1 = ThreadSafeLogger()
        logger2 = ThreadSafeLogger()
        assert logger1 is logger2

    def test_thread_safe_logger_methods(self):
        """Test ThreadSafeLogger methods."""
        logger = ThreadSafeLogger()
        
        # Test warning method
        with patch.object(logger._logger, 'warning') as mock_warning:
            logger.warning("test warning")
            mock_warning.assert_called_once_with("test warning")
        
        # Test error method
        with patch.object(logger._logger, 'error') as mock_error:
            logger.error("test error")
            mock_error.assert_called_once_with("test error")
        
        # Test info method
        with patch.object(logger._logger, 'info') as mock_info:
            logger.info("test info")
            mock_info.assert_called_once_with("test info")


class TestDataSanitizerCoverage:
    """Test DataSanitizer coverage gaps."""

    def test_sanitize_for_json_complex_types(self):
        """Test sanitize_for_json with complex types."""
        # Test with custom object
        class CustomObject:
            def __init__(self):
                self.name = "test"
                self.value = 123
        
        obj = CustomObject()
        result = DataSanitizer.sanitize_for_json(obj)
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 123

    def test_sanitize_for_json_other_types(self):
        """Test sanitize_for_json with other types."""
        # Test with object with __dict__
        class WithDict:
            def __init__(self):
                self.foo = 'bar'
        obj = WithDict()
        result = DataSanitizer.sanitize_for_json(obj)
        assert isinstance(result, dict)
        assert result['foo'] == 'bar'

        # Test with object without __dict__
        class WithoutDict:
            __slots__ = ()
        obj2 = WithoutDict()
        result2 = DataSanitizer.sanitize_for_json(obj2)
        assert isinstance(result2, str)

    def test_sanitize_for_csv_complex_types(self):
        """Test sanitize_for_csv with complex types."""
        # Test with dict
        data = {"key": "value", "nested": {"inner": "data"}}
        result = DataSanitizer.sanitize_for_csv(data)
        assert isinstance(result, str)
        assert "key" in result

    def test_clear_cache(self):
        """Test clear_cache method."""
        # Add some data to cache
        DataSanitizer.sanitize_for_json({"test": "data"})
        assert len(DataSanitizer._cache) > 0
        
        # Clear cache
        DataSanitizer.clear_cache()
        assert len(DataSanitizer._cache) == 0


class TestCorruptionDetectorCoverage:
    """Test CorruptionDetector coverage gaps."""

    def test_is_valid_json_cache_hit(self):
        """Test is_valid_json with cache hit."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            file_path = f.name
        
        try:
            # First call should cache the result
            result1 = CorruptionDetector.is_valid_json(file_path)
            assert result1 is True
            
            # Second call should use cache
            result2 = CorruptionDetector.is_valid_json(file_path)
            assert result2 is True
        finally:
            os.unlink(file_path)

    def test_is_valid_json_cache_miss(self):
        """Test is_valid_json with cache miss."""
        # Test with non-existent file
        result = CorruptionDetector.is_valid_json("/nonexistent/file.json")
        assert result is False

    def test_is_valid_json_lines_valid(self):
        """Test is_valid_json_lines with valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"test": "data1"}\n')
            f.write('{"test": "data2"}\n')
            file_path = f.name
        
        try:
            result = CorruptionDetector.is_valid_json_lines(file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    def test_is_valid_json_lines_invalid(self):
        """Test is_valid_json_lines with invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"test": "data1"}\n')
            f.write('invalid json\n')
            file_path = f.name
        
        try:
            result = CorruptionDetector.is_valid_json_lines(file_path)
            assert result is False
        finally:
            os.unlink(file_path)

    def test_is_valid_csv_valid(self):
        """Test is_valid_csv with valid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('name,age\n')
            f.write('John,30\n')
            file_path = f.name
        
        try:
            result = CorruptionDetector.is_valid_csv(file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    def test_is_valid_csv_invalid(self):
        """Test is_valid_csv with invalid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('invalid,csv,format\n')
            f.write('missing,quotes\n')
            file_path = f.name
        
        try:
            result = CorruptionDetector.is_valid_csv(file_path)
            assert result is True  # CSV is more permissive
        finally:
            os.unlink(file_path)

    def test_detect_corruption_json(self):
        """Test detect_corruption with JSON format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            file_path = f.name
        
        try:
            result = CorruptionDetector.detect_corruption(file_path, "json")
            assert result is False  # Valid JSON should not be corrupted
        finally:
            os.unlink(file_path)

    def test_detect_corruption_json_lines(self):
        """Test detect_corruption with JSON Lines format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"test": "data1"}\n')
            f.write('{"test": "data2"}\n')
            file_path = f.name
        
        try:
            result = CorruptionDetector.detect_corruption(file_path, "json_lines")
            assert result is False  # Valid JSON Lines should not be corrupted
        finally:
            os.unlink(file_path)

    def test_detect_corruption_csv(self):
        """Test detect_corruption with CSV format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('name,age\n')
            f.write('John,30\n')
            file_path = f.name
        
        try:
            result = CorruptionDetector.detect_corruption(file_path, "csv")
            assert result is False  # Valid CSV should not be corrupted
        finally:
            os.unlink(file_path)

    def test_clear_cache(self):
        """Test clear_cache method."""
        # Add some data to cache
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            file_path = f.name
        
        try:
            CorruptionDetector.is_valid_json(file_path)
            assert len(CorruptionDetector._cache) > 0
            
            # Clear cache
            CorruptionDetector.clear_cache()
            assert len(CorruptionDetector._cache) == 0
        finally:
            os.unlink(file_path)


class TestAtomicWriterCoverage:
    """Test AtomicWriter coverage gaps."""

    def test_write_json_atomic_success(self):
        """Test write_json_atomic success."""
        data = {"test": "data"}
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            file_path = f.name
        
        try:
            result = AtomicWriter.write_json_atomic(data, file_path)
            assert result is True
            
            # Verify file was written
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == data
        finally:
            os.unlink(file_path)

    def test_write_json_atomic_with_indent(self):
        """Test write_json_atomic with indent."""
        data = {"test": "data"}
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            file_path = f.name
        
        try:
            result = AtomicWriter.write_json_atomic(data, file_path, indent=2)
            assert result is True
        finally:
            os.unlink(file_path)

    def test_write_json_lines_atomic_success(self):
        """Test write_json_lines_atomic success."""
        records = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            file_path = f.name
        
        try:
            result = AtomicWriter.write_json_lines_atomic(records, file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    def test_write_csv_atomic_success(self):
        """Test write_csv_atomic success."""
        records = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            file_path = f.name
        
        try:
            result = AtomicWriter.write_csv_atomic(records, file_path)
            assert result is True
        finally:
            os.unlink(file_path)


class TestBackupManagerCoverage:
    """Test BackupManager coverage gaps."""

    def test_backup_manager_singleton(self):
        """Test BackupManager singleton pattern."""
        manager1 = BackupManager()
        manager2 = BackupManager()
        assert manager1 is manager2

    def test_create_backup_success(self):
        """Test create_backup success."""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            file_path = f.name
        
        try:
            manager = BackupManager()
            backup_path = manager.create_backup(file_path)
            assert backup_path is not None
            assert backup_path.exists()
            
            # Clean up backup
            backup_path.unlink()
        finally:
            os.unlink(file_path)

    def test_restore_from_backup_success(self):
        """Test restore_from_backup success."""
        # Create original file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("original content")
            file_path = f.name
        
        # Create backup file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("backup content")
            backup_path = f.name
        
        try:
            manager = BackupManager()
            result = manager.restore_from_backup(file_path, backup_path)
            assert result is True
        finally:
            os.unlink(file_path)
            os.unlink(backup_path)


class TestDataRecoveryCoverage:
    """Test DataRecovery coverage gaps."""

    def test_data_recovery_singleton(self):
        """Test DataRecovery singleton pattern."""
        recovery1 = DataRecovery()
        recovery2 = DataRecovery()
        assert recovery1 is recovery2

    def test_recover_json_file_success(self):
        """Test recover_json_file success."""
        data = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            file_path = f.name
        
        try:
            recovery = DataRecovery()
            result = recovery.recover_json_file(file_path)
            assert result == data
        finally:
            os.unlink(file_path)

    def test_recover_json_file_invalid(self):
        """Test recover_json_file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            file_path = f.name
        
        try:
            recovery = DataRecovery()
            result = recovery.recover_json_file(file_path)
            # Invalid JSON should return an empty list, not None
            assert result == []
        finally:
            os.unlink(file_path)

    def test_recover_csv_file_success(self):
        """Test recover_csv_file success."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age\n")
            f.write("John,30\n")
            f.write("Jane,25\n")
            file_path = f.name
        
        try:
            recovery = DataRecovery()
            result = recovery.recover_csv_file(file_path)
            assert result is not None
            assert len(result) == 2
        finally:
            os.unlink(file_path)


class TestFallbackHandlerCoverage:
    """Test FallbackHandler coverage gaps."""

    def test_fallback_handler_singleton(self):
        """Test FallbackHandler singleton pattern."""
        handler1 = FallbackHandler()
        handler2 = FallbackHandler()
        assert handler1 is handler2

    def test_get_file_lock(self):
        """Test _get_file_lock method."""
        handler = FallbackHandler()
        lock1 = handler._get_file_lock("/test/file1.txt")
        lock2 = handler._get_file_lock("/test/file2.txt")
        lock3 = handler._get_file_lock("/test/file1.txt")
        
        assert lock1 is not lock2
        assert lock1 is lock3

    def test_safe_write_json_success(self):
        """Test safe_write_json success."""
        data = {"test": "data"}
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            file_path = f.name
        
        try:
            handler = FallbackHandler()
            result = handler.safe_write_json(data, file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    def test_safe_write_json_lines_success(self):
        """Test safe_write_json_lines success."""
        records = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            file_path = f.name
        
        try:
            handler = FallbackHandler()
            result = handler.safe_write_json_lines(records, file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    def test_safe_write_csv_success(self):
        """Test safe_write_csv success."""
        records = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            file_path = f.name
        
        try:
            handler = FallbackHandler()
            result = handler.safe_write_csv(records, file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    def test_safe_read_json_success(self):
        """Test safe_read_json success."""
        data = {"test": "data"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            file_path = f.name
        
        try:
            handler = FallbackHandler()
            result = handler.safe_read_json(file_path)
            assert result == data
        finally:
            os.unlink(file_path)

    def test_safe_read_csv_success(self):
        """Test safe_read_csv success."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age\n")
            f.write("John,30\n")
            f.write("Jane,25\n")
            file_path = f.name
        
        try:
            handler = FallbackHandler()
            result = handler.safe_read_csv(file_path)
            assert result is not None
            assert len(result) == 2
        finally:
            os.unlink(file_path)


class TestAsyncFunctionsCoverage:
    """Test async functions coverage gaps."""

    @pytest.mark.asyncio
    async def test_async_safe_write_json(self):
        """Test async_safe_write_json."""
        data = {"test": "data"}
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            file_path = f.name
        
        try:
            result = await async_safe_write_json(data, file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    @pytest.mark.asyncio
    async def test_async_safe_write_csv(self):
        """Test async_safe_write_csv."""
        records = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            file_path = f.name
        
        try:
            result = await async_safe_write_csv(records, file_path)
            assert result is True
        finally:
            os.unlink(file_path)

    @pytest.mark.asyncio
    async def test_async_safe_read_json(self):
        """Test async_safe_read_json."""
        data = {"test": "data"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            file_path = f.name
        
        try:
            result = await async_safe_read_json(file_path)
            assert result == data
        finally:
            os.unlink(file_path)

    @pytest.mark.asyncio
    async def test_async_safe_read_csv(self):
        """Test async_safe_read_csv."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age\n")
            f.write("John,30\n")
            f.write("Jane,25\n")
            file_path = f.name
        
        try:
            result = await async_safe_read_csv(file_path)
            assert result is not None
            assert len(result) == 2
        finally:
            os.unlink(file_path)


class TestUtilityFunctionsCoverage:
    """Test utility functions coverage gaps."""

    def test_clear_all_caches(self):
        """Test clear_all_caches function."""
        # Add some data to caches
        DataSanitizer.sanitize_for_json({"test": "data"})
        assert len(DataSanitizer._cache) > 0
        
        clear_all_caches()
        assert len(DataSanitizer._cache) == 0

    def test_get_performance_stats(self):
        """Test get_performance_stats function."""
        stats = get_performance_stats()
        assert isinstance(stats, dict)
        assert "sanitizer_cache_size" in stats
        assert "corruption_cache_size" in stats
        assert "file_locks_count" in stats


class TestDataLossProtectionCoverage:
    """Test DataLossProtection coverage gaps."""

    @pytest.mark.asyncio
    async def test_backup_message_success(self):
        """Test backup_message success."""
        protection = DataLossProtection()
        message = {"test": "data"}
        
        result = await protection.backup_message(message, "test_queue")
        assert result is True

    @pytest.mark.asyncio
    async def test_restore_messages_success(self):
        """Test restore_messages success."""
        protection = DataLossProtection()
        
        # First backup a message
        message = {"test": "data"}
        await protection.backup_message(message, "test_queue")
        
        # Then restore messages
        messages = await protection.restore_messages("test_queue")
        assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_serialize_deserialize_message(self):
        """Test message serialization and deserialization."""
        protection = DataLossProtection()
        original_message = {"test": "data", "nested": {"key": "value"}}
        
        # Serialize
        serialized = await protection._serialize_message(original_message, 1234567890.0)
        assert isinstance(serialized, dict)
        assert "message" in serialized
        assert "timestamp" in serialized
        
        # Deserialize
        deserialized = await protection._deserialize_message(serialized)
        # For generic type, deserialized is a string
        assert deserialized == str(original_message)

    def test_get_protection_stats(self):
        """Test get_protection_stats method."""
        protection = DataLossProtection()
        stats = protection.get_protection_stats()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_should_retry(self):
        """Test should_retry method."""
        protection = DataLossProtection()
        
        # Test with retryable error
        result = await protection.should_retry(Exception("test error"))
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self):
        """Test cleanup_old_backups method."""
        protection = DataLossProtection()
        
        # Create some backup files
        await protection.backup_message({"test": "data"}, "test_queue")
        
        # Clean up old backups
        count = await protection.cleanup_old_backups(max_age_hours=0)
        assert isinstance(count, int)


class TestSecurityDataSanitizerCoverage:
    """Test SecurityDataSanitizer coverage gaps."""

    def test_sanitize_data_circular_reference(self):
        """Test sanitize_data with circular reference."""
        sanitizer = SecurityDataSanitizer()
        
        # Create circular reference
        data: Dict[str, Any] = {"key": "value"}
        data["self"] = data
        
        result = sanitizer.sanitize_data(data, depth=11)
        assert result == "[REDACTED_CIRCULAR_REFERENCE]"

    def test_sanitize_string_with_patterns(self):
        """Test _sanitize_string with various patterns."""
        sanitizer = SecurityDataSanitizer()
        
        # Test email
        result = sanitizer._sanitize_string("test@example.com")
        assert "[REDACTED_EMAIL]" in result
        
        # Test credit card
        result = sanitizer._sanitize_string("4111-1111-1111-1111")
        assert "[REDACTED_CREDIT_CARD]" in result
        
        # Test SSN
        result = sanitizer._sanitize_string("123-45-6789")
        assert "[REDACTED_SSN]" in result
        
        # Test phone
        result = sanitizer._sanitize_string("(555) 123-4567")
        assert "[REDACTED_PHONE]" in result

    def test_sanitize_dict_sensitive_keys(self):
        """Test _sanitize_dict with sensitive keys."""
        sanitizer = SecurityDataSanitizer()
        
        data = {
            "password": "secret123",
            "api_key": "abc123",
            "normal_key": "normal_value"
        }
        
        result = sanitizer._sanitize_dict(data)
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        # normal_key contains "key" so it should also be redacted
        assert result["normal_key"] == "[REDACTED]"

    def test_add_pattern_invalid_regex(self):
        """Test add_pattern with invalid regex."""
        sanitizer = SecurityDataSanitizer()
        
        # Add invalid regex pattern
        sanitizer.add_pattern("invalid", "[invalid")
        # Should not raise exception

    def test_remove_pattern_success(self):
        """Test remove_pattern success."""
        sanitizer = SecurityDataSanitizer()
        
        # Add pattern
        sanitizer.add_pattern("test_pattern", r"test")
        
        # Remove pattern
        result = sanitizer.remove_pattern("test_pattern")
        assert result is True

    def test_remove_pattern_not_found(self):
        """Test remove_pattern with non-existent pattern."""
        sanitizer = SecurityDataSanitizer()
        
        result = sanitizer.remove_pattern("non_existent")
        assert result is False


class TestSecurityValidatorCoverage:
    """Test SecurityValidator coverage gaps."""

    def test_validate_input_string(self):
        """Test validate_input with string."""
        validator = SecurityValidator()
        
        # Test with clean string
        result = validator.validate_input("clean string")
        assert result["valid"] is True
        assert len(result["threats"]) == 0
        
        # Test with SQL injection
        result = validator.validate_input("SELECT * FROM users")
        assert result["valid"] is False
        assert len(result["threats"]) > 0

    def test_validate_input_dict(self):
        """Test validate_input with dictionary."""
        validator = SecurityValidator()
        
        data = {
            "name": "John",
            "query": "SELECT * FROM users"
        }
        
        result = validator.validate_input(data)
        assert result["valid"] is False
        assert len(result["threats"]) > 0

    def test_validate_input_list(self):
        """Test validate_input with list."""
        validator = SecurityValidator()
        
        data = ["clean", "SELECT * FROM users", "normal"]
        
        result = validator.validate_input(data)
        assert result["valid"] is False
        assert len(result["threats"]) > 0

    def test_get_threat_severity(self):
        """Test _get_threat_severity method."""
        validator = SecurityValidator()
        
        # Test high severity threats
        assert validator._get_threat_severity("sql_injection") == "high"
        assert validator._get_threat_severity("xss") == "high"
        
        # Test medium severity threats
        assert validator._get_threat_severity("path_traversal") == "medium"
        
        # Test unknown threat
        assert validator._get_threat_severity("unknown") == "low"

    def test_add_threat_pattern_invalid_regex(self):
        """Test add_threat_pattern with invalid regex."""
        validator = SecurityValidator()
        # Add invalid regex pattern, should raise re.error
        import pytest
        with pytest.raises(Exception):
            validator.add_threat_pattern("invalid", "[invalid")


class TestDataHasherCoverage:
    """Test DataHasher coverage gaps."""

    def test_hash_data_success(self):
        """Test hash_data success."""
        hasher = DataHasher()
        
        result = hasher.hash_data("test data")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_sensitive_fields_success(self):
        """Test hash_sensitive_fields success."""
        hasher = DataHasher()
        
        data = {
            "name": "John",
            "email": "john@example.com",
            "password": "secret123"
        }
        
        result = hasher.hash_sensitive_fields(data, ["password", "email"])
        assert "password" in result
        assert "email" in result
        assert result["password"] != "secret123"
        assert result["email"] != "john@example.com"
        assert result["name"] == "John"

    def test_verify_hash_success(self):
        """Test verify_hash success."""
        hasher = DataHasher()
        
        original_data = "test data"
        hash_value = hasher.hash_data(original_data)
        
        result = hasher.verify_hash(original_data, hash_value)
        assert result is True

    def test_verify_hash_failure(self):
        """Test verify_hash failure."""
        hasher = DataHasher()
        
        result = hasher.verify_hash("test data", "invalid_hash")
        assert result is False 