"""
Comprehensive tests for data protection fallbacks module.

This module tests all functionality in hydra_logger.data_protection.fallbacks
to achieve 100% coverage.
"""

import os
import json
import csv
import tempfile
import shutil
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

from hydra_logger.data_protection.fallbacks import (
    ThreadSafeLogger,
    DataSanitizer,
    CorruptionDetector,
    AtomicWriter,
    BackupManager,
    DataRecovery,
    FallbackHandler,
    DataLossProtection,
    async_safe_write_json,
    async_safe_write_csv,
    async_safe_read_json,
    async_safe_read_csv,
    clear_all_caches,
    get_performance_stats
)


class TestThreadSafeLogger:
    """Test ThreadSafeLogger class."""

    def test_thread_safe_logger_singleton(self):
        """Test that ThreadSafeLogger is a singleton."""
        logger1 = ThreadSafeLogger()
        logger2 = ThreadSafeLogger()
        assert logger1 is logger2

    def test_thread_safe_logger_warning(self):
        """Test warning method."""
        logger = ThreadSafeLogger()
        logger.warning("Test warning")

    def test_thread_safe_logger_error(self):
        """Test error method."""
        logger = ThreadSafeLogger()
        logger.error("Test error")

    def test_thread_safe_logger_info(self):
        """Test info method."""
        logger = ThreadSafeLogger()
        logger.info("Test info")


class TestDataSanitizer:
    """Test DataSanitizer class."""

    def test_sanitize_for_json_basic_types(self):
        """Test sanitizing basic types for JSON."""
        sanitizer = DataSanitizer()
        
        # Test string
        result = sanitizer.sanitize_for_json("test")
        assert result == "test"
        
        # Test int
        result = sanitizer.sanitize_for_json(123)
        assert result == 123
        
        # Test float
        result = sanitizer.sanitize_for_json(3.14)
        assert result == 3.14
        
        # Test bool
        result = sanitizer.sanitize_for_json(True)
        assert result is True
        
        # Test None
        result = sanitizer.sanitize_for_json(None)
        assert result is None

    def test_sanitize_for_json_list(self):
        """Test sanitizing list for JSON."""
        sanitizer = DataSanitizer()
        data = [1, "test", {"key": "value"}, [1, 2, 3]]
        result = sanitizer.sanitize_for_json(data)
        assert result == [1, "test", {"key": "value"}, [1, 2, 3]]

    def test_sanitize_for_json_dict(self):
        """Test sanitizing dict for JSON."""
        sanitizer = DataSanitizer()
        data = {"key1": "value1", "key2": 123, "key3": {"nested": "value"}}
        result = sanitizer.sanitize_for_json(data)
        assert result == {"key1": "value1", "key2": 123, "key3": {"nested": "value"}}

    def test_sanitize_for_json_object_with_dict(self):
        """Test sanitizing object with __dict__ for JSON."""
        class TestObject:
            def __init__(self):
                self.attr1 = "value1"
                self.attr2 = 123
        
        sanitizer = DataSanitizer()
        obj = TestObject()
        result = sanitizer.sanitize_for_json(obj)
        assert result == {"attr1": "value1", "attr2": 123}

    def test_sanitize_for_json_other_object(self):
        """Test sanitizing other object types for JSON."""
        sanitizer = DataSanitizer()
        result = sanitizer.sanitize_for_json(object())
        assert isinstance(result, str)

    def test_sanitize_for_csv_basic(self):
        """Test sanitizing basic types for CSV."""
        sanitizer = DataSanitizer()
        
        # Test string
        result = sanitizer.sanitize_for_csv("test")
        assert result == "test"
        
        # Test None
        result = sanitizer.sanitize_for_csv(None)
        assert result == ""

    def test_sanitize_for_csv_dict(self):
        """Test sanitizing dict for CSV."""
        sanitizer = DataSanitizer()
        data = {"key": "value", "number": 123}
        result = sanitizer.sanitize_for_csv(data)
        assert isinstance(result, str)
        assert "key" in result

    def test_sanitize_for_csv_list(self):
        """Test sanitizing list for CSV."""
        sanitizer = DataSanitizer()
        data = [1, 2, 3, "test"]
        result = sanitizer.sanitize_for_csv(data)
        assert isinstance(result, str)
        assert "1" in result

    def test_sanitize_dict_for_csv(self):
        """Test sanitizing dict for CSV."""
        sanitizer = DataSanitizer()
        data = {"key1": "value1", "key2": 123, "key3": {"nested": "value"}}
        result = sanitizer.sanitize_dict_for_csv(data)
        assert isinstance(result, dict)
        assert all(isinstance(v, str) for v in result.values())

    def test_clear_cache(self):
        """Test clearing sanitization cache."""
        DataSanitizer.clear_cache()
        # Should not raise any error


class TestCorruptionDetector:
    """Test CorruptionDetector class."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.csv_file = os.path.join(self.test_dir, "test.csv")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_is_valid_json_valid(self):
        """Test valid JSON detection."""
        with open(self.json_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        result = CorruptionDetector.is_valid_json(self.json_file)
        assert result is True

    def test_is_valid_json_invalid(self):
        """Test invalid JSON detection."""
        with open(self.json_file, 'w') as f:
            f.write("invalid json content")
        
        result = CorruptionDetector.is_valid_json(self.json_file)
        assert result is False

    def test_is_valid_json_not_found(self):
        """Test JSON detection for non-existent file."""
        result = CorruptionDetector.is_valid_json("nonexistent.json")
        assert result is False

    def test_is_valid_json_lines_valid(self):
        """Test valid JSON Lines detection."""
        with open(self.json_file, 'w') as f:
            f.write('{"line1": "data1"}\n{"line2": "data2"}\n')
        
        result = CorruptionDetector.is_valid_json_lines(self.json_file)
        assert result is True

    def test_is_valid_json_lines_invalid(self):
        """Test invalid JSON Lines detection."""
        with open(self.json_file, 'w') as f:
            f.write('{"line1": "data1"}\ninvalid json\n')
        
        result = CorruptionDetector.is_valid_json_lines(self.json_file)
        assert result is False

    def test_is_valid_csv_valid(self):
        """Test valid CSV detection."""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2"])
            writer.writerow(["data1", "data2"])
        
        result = CorruptionDetector.is_valid_csv(self.csv_file)
        assert result is True

    def test_is_valid_csv_invalid(self):
        """Test invalid CSV detection."""
        with open(self.csv_file, 'w') as f:
            f.write("invalid,csv,content\nwith,unclosed,quote")
        
        result = CorruptionDetector.is_valid_csv(self.csv_file)
        assert result is False

    def test_detect_corruption_json(self):
        """Test corruption detection for JSON."""
        with open(self.json_file, 'w') as f:
            f.write("invalid json")
        
        result = CorruptionDetector.detect_corruption(self.json_file, "json")
        assert result is True

    def test_detect_corruption_json_lines(self):
        """Test corruption detection for JSON Lines."""
        with open(self.json_file, 'w') as f:
            f.write('{"valid": "json"}\ninvalid json\n')
        
        result = CorruptionDetector.detect_corruption(self.json_file, "json_lines")
        assert result is True

    def test_detect_corruption_csv(self):
        """Test corruption detection for CSV."""
        with open(self.csv_file, 'w') as f:
            f.write("invalid,csv,content\nwith,unclosed,quote")
        
        result = CorruptionDetector.detect_corruption(self.csv_file, "csv")
        assert result is True

    def test_detect_corruption_unknown_format(self):
        """Test corruption detection for unknown format."""
        result = CorruptionDetector.detect_corruption(self.json_file, "unknown")
        assert result is False

    def test_clear_cache(self):
        """Test clearing corruption detection cache."""
        CorruptionDetector.clear_cache()
        # Should not raise any error


class TestAtomicWriter:
    """Test AtomicWriter class."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.csv_file = os.path.join(self.test_dir, "test.csv")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_write_json_atomic_success(self):
        """Test successful atomic JSON writing."""
        data = {"test": "data", "number": 123}
        result = AtomicWriter.write_json_atomic(data, self.json_file)
        assert result is True
        
        with open(self.json_file, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == data

    def test_write_json_atomic_with_indent(self):
        """Test atomic JSON writing with indent."""
        data = {"test": "data"}
        result = AtomicWriter.write_json_atomic(data, self.json_file, indent=2)
        assert result is True

    def test_write_json_atomic_error(self):
        """Test atomic JSON writing with error."""
        # Create a directory with the same name as the file to cause an error
        os.makedirs(self.json_file)
        
        data = {"test": "data"}
        result = AtomicWriter.write_json_atomic(data, self.json_file)
        assert result is False

    def test_write_json_lines_atomic_success(self):
        """Test successful atomic JSON Lines writing."""
        records = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        result = AtomicWriter.write_json_lines_atomic(records, self.json_file)
        assert result is True

    def test_write_json_lines_atomic_error(self):
        """Test atomic JSON Lines writing with error."""
        # Create a directory with the same name as the file to cause an error
        os.makedirs(self.json_file)
        
        records = [{"id": 1, "name": "test1"}]
        result = AtomicWriter.write_json_lines_atomic(records, self.json_file)
        assert result is False

    def test_write_csv_atomic_success(self):
        """Test successful atomic CSV writing."""
        records = [{"col1": "data1", "col2": "data2"}, {"col1": "data3", "col2": "data4"}]
        result = AtomicWriter.write_csv_atomic(records, self.csv_file)
        assert result is True

    def test_write_csv_atomic_empty_records(self):
        """Test atomic CSV writing with empty records."""
        records = []
        result = AtomicWriter.write_csv_atomic(records, self.csv_file)
        assert result is True

    def test_write_csv_atomic_error(self):
        """Test atomic CSV writing with error."""
        # Create a directory with the same name as the file to cause an error
        os.makedirs(self.csv_file)
        
        records = [{"col1": "data1"}]
        result = AtomicWriter.write_csv_atomic(records, self.csv_file)
        assert result is False


class TestBackupManager:
    """Test BackupManager class."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backups")
        self.test_file = os.path.join(self.test_dir, "test.txt")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_backup_manager_singleton(self):
        """Test that BackupManager is a singleton."""
        manager1 = BackupManager()
        manager2 = BackupManager()
        assert manager1 is manager2

    def test_create_backup_success(self):
        """Test successful backup creation."""
        with open(self.test_file, 'w') as f:
            f.write("test content")
        
        manager = BackupManager()
        backup_path = manager.create_backup(self.test_file)
        assert backup_path is not None
        assert os.path.exists(backup_path)

    def test_create_backup_file_not_found(self):
        """Test backup creation for non-existent file."""
        manager = BackupManager()
        backup_path = manager.create_backup("nonexistent.txt")
        assert backup_path is None

    def test_create_backup_with_custom_dir(self):
        """Test backup creation with custom directory."""
        with open(self.test_file, 'w') as f:
            f.write("test content")
        
        manager = BackupManager(self.backup_dir)
        backup_path = manager.create_backup(self.test_file)
        assert backup_path is not None
        assert os.path.exists(backup_path)

    def test_restore_from_backup_success(self):
        """Test successful backup restoration."""
        with open(self.test_file, 'w') as f:
            f.write("original content")
        
        manager = BackupManager()
        backup_path = manager.create_backup(self.test_file)
        
        # Modify original file
        with open(self.test_file, 'w') as f:
            f.write("modified content")
        
        # Restore from backup
        result = manager.restore_from_backup(self.test_file, backup_path)
        assert result is True
        
        with open(self.test_file, 'r') as f:
            content = f.read()
        assert content == "original content"

    def test_restore_from_backup_failure(self):
        """Test backup restoration failure."""
        manager = BackupManager()
        result = manager.restore_from_backup("nonexistent.txt", "nonexistent_backup.txt")
        assert result is False


class TestDataRecovery:
    """Test DataRecovery class."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.csv_file = os.path.join(self.test_dir, "test.csv")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_data_recovery_singleton(self):
        """Test that DataRecovery is a singleton."""
        recovery1 = DataRecovery()
        recovery2 = DataRecovery()
        assert recovery1 is recovery2

    def test_recover_json_file_success(self):
        """Test successful JSON file recovery."""
        with open(self.json_file, 'w') as f:
            f.write('{"id": 1, "name": "test1"}\n{"id": 2, "name": "test2"}\n')
        
        recovery = DataRecovery()
        result = recovery.recover_json_file(self.json_file)
        assert result is not None
        assert len(result) == 2

    def test_recover_json_file_not_found(self):
        """Test JSON recovery for non-existent file."""
        recovery = DataRecovery()
        result = recovery.recover_json_file("nonexistent.json")
        assert result is None

    def test_recover_json_file_empty(self):
        """Test JSON recovery for empty file."""
        with open(self.json_file, 'w') as f:
            f.write("")
        
        recovery = DataRecovery()
        result = recovery.recover_json_file(self.json_file)
        assert result == []

    def test_recover_json_file_partial_corruption(self):
        """Test JSON recovery for partially corrupted file."""
        with open(self.json_file, 'w') as f:
            f.write('{"id": 1, "name": "test1"}\ninvalid json\n{"id": 2, "name": "test2"}\n')
        
        recovery = DataRecovery()
        result = recovery.recover_json_file(self.json_file)
        assert result is not None
        assert len(result) == 2

    def test_recover_csv_file_success(self):
        """Test successful CSV file recovery."""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name"])
            writer.writerow(["1", "test1"])
            writer.writerow(["2", "test2"])
        
        recovery = DataRecovery()
        result = recovery.recover_csv_file(self.csv_file)
        assert result is not None
        assert len(result) == 2

    def test_recover_csv_file_not_found(self):
        """Test CSV recovery for non-existent file."""
        recovery = DataRecovery()
        result = recovery.recover_csv_file("nonexistent.csv")
        assert result is None


class TestFallbackHandler:
    """Test FallbackHandler class."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.csv_file = os.path.join(self.test_dir, "test.csv")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_fallback_handler_singleton(self):
        """Test that FallbackHandler is a singleton."""
        handler1 = FallbackHandler()
        handler2 = FallbackHandler()
        assert handler1 is handler2

    def test_safe_write_json_success(self):
        """Test successful safe JSON writing."""
        data = {"test": "data"}
        handler = FallbackHandler()
        result = handler.safe_write_json(data, self.json_file)
        assert result is True

    def test_safe_write_json_with_backup(self):
        """Test safe JSON writing with backup."""
        # Create original file
        with open(self.json_file, 'w') as f:
            json.dump({"original": "data"}, f)
        
        data = {"new": "data"}
        handler = FallbackHandler()
        result = handler.safe_write_json(data, self.json_file)
        assert result is True

    def test_safe_write_json_error(self):
        """Test safe JSON writing with error."""
        # Create a directory with the same name as the file to cause an error
        os.makedirs(self.json_file)
        
        data = {"test": "data"}
        handler = FallbackHandler()
        result = handler.safe_write_json(data, self.json_file)
        assert result is False

    def test_safe_write_json_lines_success(self):
        """Test successful safe JSON Lines writing."""
        records = [{"id": 1, "name": "test1"}]
        handler = FallbackHandler()
        result = handler.safe_write_json_lines(records, self.json_file)
        assert result is True

    def test_safe_write_csv_success(self):
        """Test successful safe CSV writing."""
        records = [{"col1": "data1", "col2": "data2"}]
        handler = FallbackHandler()
        result = handler.safe_write_csv(records, self.csv_file)
        assert result is True

    def test_safe_read_json_success(self):
        """Test successful safe JSON reading."""
        data = {"test": "data"}
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
        
        handler = FallbackHandler()
        result = handler.safe_read_json(self.json_file)
        assert result == data

    def test_safe_read_json_not_found(self):
        """Test safe JSON reading for non-existent file."""
        handler = FallbackHandler()
        result = handler.safe_read_json("nonexistent.json")
        assert result is None

    def test_safe_read_csv_success(self):
        """Test successful safe CSV reading."""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2"])
            writer.writerow(["data1", "data2"])
        
        handler = FallbackHandler()
        result = handler.safe_read_csv(self.csv_file)
        assert result is not None
        assert len(result) == 1


class TestDataLossProtection:
    """Test DataLossProtection class."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = os.path.join(self.test_dir, "backup")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @pytest.mark.asyncio
    async def test_backup_message_success(self):
        """Test successful message backup."""
        protection = DataLossProtection(self.backup_dir)
        message = {"id": 1, "data": "test"}
        
        result = await protection.backup_message(message, "test_queue")
        assert result is True

    @pytest.mark.asyncio
    async def test_backup_message_circuit_breaker(self):
        """Test message backup with circuit breaker."""
        protection = DataLossProtection(self.backup_dir)
        
        # Trigger circuit breaker
        for _ in range(10):
            await protection.backup_message({"test": "data"}, "test_queue")
        
        # Circuit should be open
        result = await protection.backup_message({"test": "data"}, "test_queue")
        assert result is False

    @pytest.mark.asyncio
    async def test_restore_messages_success(self):
        """Test successful message restoration."""
        protection = DataLossProtection(self.backup_dir)
        
        # Backup some messages
        await protection.backup_message({"id": 1, "data": "test1"}, "test_queue")
        await protection.backup_message({"id": 2, "data": "test2"}, "test_queue")
        
        # Restore messages
        result = await protection.restore_messages("test_queue")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_restore_messages_no_backups(self):
        """Test message restoration with no backups."""
        protection = DataLossProtection(self.backup_dir)
        result = await protection.restore_messages("test_queue")
        assert result == []

    def test_get_protection_stats(self):
        """Test getting protection statistics."""
        protection = DataLossProtection(self.backup_dir)
        stats = protection.get_protection_stats()
        assert "circuit_open" in stats
        assert "failure_count" in stats
        assert "backup_files" in stats
        assert "stats" in stats

    @pytest.mark.asyncio
    async def test_should_retry_success(self):
        """Test should_retry with success."""
        protection = DataLossProtection(self.backup_dir)
        result = await protection.should_retry(Exception("test"))
        assert result is True

    @pytest.mark.asyncio
    async def test_should_retry_circuit_open(self):
        """Test should_retry with circuit open."""
        protection = DataLossProtection(self.backup_dir)
        
        # Trigger circuit breaker
        for _ in range(10):
            await protection.should_retry(Exception("test"))
        
        result = await protection.should_retry(Exception("test"))
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self):
        """Test cleanup of old backups."""
        protection = DataLossProtection(self.backup_dir)
        result = await protection.cleanup_old_backups(24)
        assert result == 0


class TestAsyncFunctions:
    """Test async convenience functions."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.json_file = os.path.join(self.test_dir, "test.json")
        self.csv_file = os.path.join(self.test_dir, "test.csv")

    def teardown_method(self):
        """Cleanup test files."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @pytest.mark.asyncio
    async def test_async_safe_write_json(self):
        """Test async safe JSON writing."""
        data = {"test": "data"}
        result = await async_safe_write_json(data, self.json_file)
        assert result is True

    @pytest.mark.asyncio
    async def test_async_safe_write_csv(self):
        """Test async safe CSV writing."""
        records = [{"col1": "data1", "col2": "data2"}]
        result = await async_safe_write_csv(records, self.csv_file)
        assert result is True

    @pytest.mark.asyncio
    async def test_async_safe_read_json(self):
        """Test async safe JSON reading."""
        data = {"test": "data"}
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
        
        result = await async_safe_read_json(self.json_file)
        assert result == data

    @pytest.mark.asyncio
    async def test_async_safe_read_csv(self):
        """Test async safe CSV reading."""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["col1", "col2"])
            writer.writerow(["data1", "data2"])
        
        result = await async_safe_read_csv(self.csv_file)
        assert result is not None
        assert len(result) == 1


class TestUtilityFunctions:
    """Test utility functions."""

    def test_clear_all_caches(self):
        """Test clearing all caches."""
        clear_all_caches()
        # Should not raise any error

    def test_get_performance_stats(self):
        """Test getting performance statistics."""
        stats = get_performance_stats()
        assert "sanitizer_cache_size" in stats
        assert "corruption_cache_size" in stats 