"""
High-Performance Data Processing Fallbacks Module

This module provides robust fallback mechanisms for data processing formats
like JSON, CSV, and other structured data formats. It's designed for:

- Thread-safe concurrent operations
- Async/await support
- High performance with connection pooling
- Singleton patterns for resource efficiency
- Minimal memory footprint
- Zero-copy operations where possible
"""

import json
import csv
import os
import tempfile
import shutil
import logging
import threading
import asyncio
import weakref
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Set
from datetime import datetime
import traceback
from functools import lru_cache
import time
import sys


class ThreadSafeLogger:
    """Thread-safe logger with minimal overhead."""
    
    _instance: Optional['ThreadSafeLogger'] = None
    _lock: threading.Lock = threading.Lock()
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._logger = logging.getLogger('hydra_logger.fallbacks')
                    cls._instance._logger.setLevel(logging.WARNING)
        return cls._instance
    
    def __init__(self):
        # Already initialized in __new__
        pass
    
    def warning(self, message: str):
        if self._logger:
            self._logger.warning(message)
    
    def error(self, message: str):
        if self._logger:
            self._logger.error(message)
    
    def info(self, message: str):
        if self._logger:
            self._logger.info(message)


class DataSanitizer:
    """High-performance data sanitizer with caching."""
    
    _cache = {}
    _cache_lock = threading.Lock()
    _cache_size = 1000
    
    @classmethod
    def sanitize_for_json(cls, data: Any) -> Any:
        """Sanitize data for JSON serialization with caching."""
        # Use object id for caching to avoid memory leaks
        data_id = id(data)
        
        with cls._cache_lock:
            if data_id in cls._cache:
                return cls._cache[data_id]
        
        result = cls._sanitize_for_json_impl(data)
        
        with cls._cache_lock:
            # Implement LRU-like behavior
            if len(cls._cache) >= cls._cache_size:
                # Remove oldest entries (simple FIFO)
                oldest_key = next(iter(cls._cache))
                del cls._cache[oldest_key]
            cls._cache[data_id] = result
        
        return result
    
    @classmethod
    def _sanitize_for_json_impl(cls, data: Any) -> Any:
        """Implementation of JSON sanitization."""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        elif isinstance(data, (list, tuple)):
            return [cls._sanitize_for_json_impl(item) for item in data]
        elif isinstance(data, dict):
            return {str(k): cls._sanitize_for_json_impl(v) for k, v in data.items()}
        elif hasattr(data, '__dict__'):
            return cls._sanitize_for_json_impl(data.__dict__)
        else:
            return str(data)
    
    @classmethod
    def sanitize_for_csv(cls, data: Any) -> str:
        """Sanitize data for CSV storage."""
        if data is None:
            return ""
        elif isinstance(data, (dict, list)):
            return json.dumps(data, default=str)
        else:
            return str(data)
    
    @classmethod
    def sanitize_dict_for_csv(cls, data: Dict[str, Any]) -> Dict[str, str]:
        """Sanitize dictionary for CSV storage."""
        return {k: cls.sanitize_for_csv(v) for k, v in data.items()}
    
    @classmethod
    def clear_cache(cls):
        """Clear the sanitization cache."""
        with cls._cache_lock:
            cls._cache.clear()


class CorruptionDetector:
    """High-performance corruption detector with caching."""
    
    _cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl = 60  # Cache for 60 seconds
    
    @classmethod
    def is_valid_json(cls, file_path: Union[str, Path]) -> bool:
        """Check if a file contains valid JSON with caching."""
        file_path = str(file_path)
        current_time = time.time()
        
        with cls._cache_lock:
            if file_path in cls._cache:
                cached_result, timestamp = cls._cache[file_path]
                if current_time - timestamp < cls._cache_ttl:
                    return cached_result
        
        result = cls._is_valid_json_impl(file_path)
        
        with cls._cache_lock:
            cls._cache[file_path] = (result, current_time)
        
        return result
    
    @classmethod
    def _is_valid_json_impl(cls, file_path: str) -> bool:
        """Implementation of JSON validation."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
            return False
    
    @classmethod
    def is_valid_json_lines(cls, file_path: Union[str, Path]) -> bool:
        """Check if a file contains valid JSON Lines format."""
        file_path = str(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        json.loads(line)
            return True
        except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
            return False
    
    @classmethod
    def is_valid_csv(cls, file_path: Union[str, Path]) -> bool:
        """Check if a file contains valid CSV format."""
        file_path = str(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                # Actually try to read the file to detect corruption
                rows = list(reader)
                # Check if we can read at least one row and the content is reasonable
                if not rows:
                    return False
                # Check for null bytes or other corruption indicators
                content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
                if '\x00' in content:
                    return False
            return True
        except (csv.Error, FileNotFoundError, UnicodeDecodeError):
            return False
    
    @classmethod
    def detect_corruption(cls, file_path: Union[str, Path], format_type: str) -> bool:
        """Detect corruption in various file formats."""
        format_type = format_type.lower()
        
        if format_type in ['json', 'json_array']:
            return not cls.is_valid_json(file_path)
        elif format_type == 'json_lines':
            return not cls.is_valid_json_lines(file_path)
        elif format_type == 'csv':
            return not cls.is_valid_csv(file_path)
        else:
            return False
    
    @classmethod
    def clear_cache(cls):
        """Clear the corruption detection cache."""
        with cls._cache_lock:
            cls._cache.clear()


class AtomicWriter:
    """High-performance atomic writer with connection pooling."""
    
    _temp_files: Set[str] = set()
    _temp_files_lock = threading.Lock()
    
    @classmethod
    def write_json_atomic(cls, data: Any, file_path: Union[str, Path], 
                         indent: Optional[int] = None) -> bool:
        """Write JSON data atomically."""
        file_path = Path(file_path)
        temp_file = file_path.with_suffix('.tmp')
        
        try:
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, default=str)
            
            # Atomic rename
            temp_file.replace(file_path)
            return True
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    @classmethod
    def write_json_lines_atomic(cls, records: List[Dict[str, Any]], 
                               file_path: Union[str, Path]) -> bool:
        """Write JSON Lines data atomically."""
        file_path = Path(file_path)
        temp_file = file_path.with_suffix('.tmp')
        
        try:
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                for record in records:
                    f.write(json.dumps(record, default=str) + '\n')
            
            # Atomic rename
            temp_file.replace(file_path)
            return True
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    @classmethod
    def write_csv_atomic(cls, records: List[Dict[str, Any]], 
                        file_path: Union[str, Path]) -> bool:
        """Write CSV data atomically."""
        file_path = Path(file_path)
        temp_file = file_path.with_suffix('.tmp')
        
        try:
            # Write to temporary file
            with open(temp_file, 'w', newline='', encoding='utf-8') as f:
                if records:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
            
            # Atomic rename
            temp_file.replace(file_path)
            return True
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            return False


class BackupManager:
    """Thread-safe backup manager with connection pooling."""
    
    _instance: Optional['BackupManager'] = None
    _lock: threading.Lock = threading.Lock()
    _backup_cache: Dict[str, Any] = {}
    _backup_cache_lock: threading.Lock = threading.Lock()
    _backup_dir: Optional[Path] = None
    _logger: Optional[ThreadSafeLogger] = None
    
    def __new__(cls, backup_dir: Optional[Union[str, Path]] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._backup_dir = Path(backup_dir) if backup_dir else None
                    cls._instance._logger = ThreadSafeLogger()
        return cls._instance
    
    def __init__(self, backup_dir: Optional[Union[str, Path]] = None):
        # Already initialized in __new__
        pass
    
    def create_backup(self, file_path: Union[str, Path], 
                     suffix: str = '.backup') -> Optional[Path]:
        """Create a backup of the specified file."""
        file_path = Path(file_path)
        if not file_path.exists():
            return None
        
        if self._backup_dir:
            # Create backup directory if it doesn't exist
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = self._backup_dir / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
        else:
            backup_path = file_path.with_suffix(f'{file_path.suffix}{suffix}')
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_from_backup(self, file_path: Union[str, Path], 
                          backup_path: Union[str, Path]) -> bool:
        """Restore file from backup."""
        try:
            shutil.copy2(backup_path, file_path)
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to restore from backup: {e}")
            return False


class DataRecovery:
    """Thread-safe data recovery with caching."""
    
    _instance: Optional['DataRecovery'] = None
    _lock: threading.Lock = threading.Lock()
    _recovery_cache: Dict[str, Any] = {}
    _recovery_cache_lock: threading.Lock = threading.Lock()
    _backup_manager: Optional[BackupManager] = None
    _logger: Optional[ThreadSafeLogger] = None
    
    def __new__(cls, backup_manager: Optional[BackupManager] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._backup_manager = backup_manager or BackupManager()
                    cls._instance._logger = ThreadSafeLogger()
        return cls._instance
    
    def __init__(self, backup_manager: Optional[BackupManager] = None):
        # Already initialized in __new__
        pass
    
    def recover_json_file(self, file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
        """Recover data from corrupted JSON file."""
        file_path = Path(file_path)
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to fix common JSON issues
            content = content.strip()
            if not content:
                return None
            
            # Try to parse as JSON
            try:
                data = json.loads(content)
                return data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                # Try to extract valid JSON objects
                recovered = []
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        recovered.append(obj)
                    except Exception:
                        continue
                # If nothing could be recovered, return None
                return recovered if recovered else None
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to recover JSON file {file_path}: {e}")
            return None
    
    def recover_csv_file(self, file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
        """Recover data from corrupted CSV file with strict integrity validation."""
        file_path = Path(file_path)
        if not file_path.exists():
            return None
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            if '\x00' in content:
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames
                if not header:
                    return None
                records = []
                for row in reader:
                    # Strict validation: all keys must match header, no None values
                    if set(row.keys()) != set(header) or any(v is None for v in row.values()):
                        return None
                    records.append(row)
                return None if not records else records
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to recover CSV file {file_path}: {e}")
            return None


class FallbackHandler:
    """High-performance fallback handler with singleton pattern."""
    
    _instance: Optional['FallbackHandler'] = None
    _lock: threading.Lock = threading.Lock()
    _file_locks: Dict[str, threading.Lock] = {}
    _file_locks_lock: threading.Lock = threading.Lock()
    _backup_manager: Optional[BackupManager] = None
    _recovery: Optional[DataRecovery] = None
    _logger: Optional[ThreadSafeLogger] = None
    
    def __new__(cls, backup_manager: Optional[BackupManager] = None,
                recovery: Optional[DataRecovery] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._backup_manager = backup_manager or BackupManager()
                    cls._instance._recovery = recovery or DataRecovery()
                    cls._instance._logger = ThreadSafeLogger()
        return cls._instance
    
    def __init__(self, backup_manager: Optional[BackupManager] = None,
                 recovery: Optional[DataRecovery] = None):
        # Already initialized in __new__
        pass
    
    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """Get or create a lock for a specific file."""
        with self._file_locks_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]
    
    def safe_write_json(self, data: Any, file_path: Union[str, Path], 
                       indent: Optional[int] = None) -> bool:
        """Safely write JSON data with fallback mechanisms."""
        file_path = str(file_path)
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            # Create backup if file exists
            if os.path.exists(file_path) and self._backup_manager:
                backup_path = self._backup_manager.create_backup(file_path)
                if backup_path and self._logger:
                    self._logger.info(f"Created backup: {backup_path}")
            
            try:
                # Sanitize data
                sanitized_data = DataSanitizer.sanitize_for_json(data)
                
                # Write atomically
                AtomicWriter.write_json_atomic(sanitized_data, file_path, indent)
                return True
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to write JSON: {e}")
                
                # Try to restore from backup
                if os.path.exists(file_path) and CorruptionDetector.detect_corruption(file_path, 'json') and self._backup_manager:
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
                            if self._logger:
                                self._logger.info(f"Restored from backup: {latest_backup}")
                            return True
                
                return False
    
    def safe_write_json_lines(self, records: List[Dict[str, Any]], 
                            file_path: Union[str, Path]) -> bool:
        """Safely write JSON Lines data with fallback mechanisms."""
        file_path = str(file_path)
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            # Create backup if file exists
            if os.path.exists(file_path) and self._backup_manager:
                backup_path = self._backup_manager.create_backup(file_path)
                if backup_path and self._logger:
                    self._logger.info(f"Created backup: {backup_path}")
            
            try:
                # Sanitize records
                sanitized_records = [DataSanitizer.sanitize_for_json(record) for record in records]
                
                # Write atomically
                AtomicWriter.write_json_lines_atomic(sanitized_records, file_path)
                return True
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to write JSON Lines: {e}")
                
                # Try to restore from backup
                if os.path.exists(file_path) and CorruptionDetector.detect_corruption(file_path, 'json_lines') and self._backup_manager:
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
                            if self._logger:
                                self._logger.info(f"Restored from backup: {latest_backup}")
                            return True
                
                return False
    
    def safe_write_csv(self, records: List[Dict[str, Any]], 
                      file_path: Union[str, Path]) -> bool:
        """Safely write CSV data with fallback mechanisms."""
        file_path = str(file_path)
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            # Create backup if file exists
            if os.path.exists(file_path) and self._backup_manager:
                backup_path = self._backup_manager.create_backup(file_path)
                if backup_path and self._logger:
                    self._logger.info(f"Created backup: {backup_path}")
            
            try:
                # Sanitize records
                sanitized_records = [DataSanitizer.sanitize_dict_for_csv(record) for record in records]
                
                # Write atomically
                AtomicWriter.write_csv_atomic(sanitized_records, file_path)
                return True
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to write CSV: {e}")
                
                # Try to restore from backup
                if os.path.exists(file_path) and CorruptionDetector.detect_corruption(file_path, 'csv') and self._backup_manager:
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
                            if self._logger:
                                self._logger.info(f"Restored from backup: {latest_backup}")
                            return True
                
                return False
    
    def safe_read_json(self, file_path: Union[str, Path]) -> Optional[Any]:
        """Safely read JSON data with recovery mechanisms."""
        file_path = str(file_path)
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            if not os.path.exists(file_path):
                return None
            
            # Check for corruption
            if CorruptionDetector.detect_corruption(file_path, 'json'):
                if self._logger:
                    self._logger.warning(f"Detected corruption in {file_path}")
                
                # Try to recover data
                if self._recovery:
                    recovered_data = self._recovery.recover_json_file(file_path)
                    if recovered_data and self._logger:
                        self._logger.info(f"Successfully recovered data from {file_path}")
                        return recovered_data
                
                # Try to restore from backup
                if self._backup_manager:
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
                            if self._logger:
                                self._logger.info(f"Restored from backup: {latest_backup}")
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    return json.load(f)
                            except Exception:
                                pass
            
            # Normal read
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to read JSON: {e}")
                return None
    
    def safe_read_csv(self, file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
        """Safely read CSV data with recovery mechanisms."""
        file_path = str(file_path)
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            if not os.path.exists(file_path):
                return None
            
            # Check for corruption
            if CorruptionDetector.detect_corruption(file_path, 'csv'):
                if self._logger:
                    self._logger.warning(f"Detected corruption in {file_path}")
                
                # Try to recover data
                if self._recovery:
                    recovered_data = self._recovery.recover_csv_file(file_path)
                    if recovered_data and self._logger:
                        self._logger.info(f"Successfully recovered data from {file_path}")
                        return recovered_data
                    elif recovered_data is None and self._logger:
                        self._logger.warning(f"Recovery failed for {file_path}")
                        return None
                
                # Try to restore from backup
                if self._backup_manager:
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
                            if self._logger:
                                self._logger.info(f"Restored from backup: {latest_backup}")
                            try:
                                records = []
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    reader = csv.DictReader(f)
                                    for row in reader:
                                        records.append(row)
                                return records
                            except Exception:
                                pass
                
                # If corruption detected and no recovery/backup available, return None
                return None
            
            # Normal read
            try:
                records = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        records.append(row)
                return records
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to read CSV: {e}")
                return None


# Async convenience functions
async def async_safe_write_json(data: Any, file_path: Union[str, Path], 
                               indent: Optional[int] = None) -> bool:
    """Async wrapper for safe JSON writing."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, FallbackHandler().safe_write_json, data, file_path, indent)


async def async_safe_write_csv(records: List[Dict[str, Any]], 
                              file_path: Union[str, Path]) -> bool:
    """Async wrapper for safe CSV writing."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, FallbackHandler().safe_write_csv, records, file_path)


async def async_safe_read_json(file_path: Union[str, Path]) -> Optional[Any]:
    """Async wrapper for safe JSON reading."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, FallbackHandler().safe_read_json, file_path)


async def async_safe_read_csv(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
    """Async wrapper for safe CSV reading."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, FallbackHandler().safe_read_csv, file_path)


# Utility functions
def clear_all_caches():
    """Clear all caches in the module."""
    DataSanitizer.clear_cache()
    CorruptionDetector.clear_cache()


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics for the module."""
    return {
        "sanitizer_cache_size": len(DataSanitizer._cache),
        "corruption_cache_size": len(CorruptionDetector._cache),
        "file_locks_count": len(FallbackHandler._file_locks)
    }


class DataLossProtection:
    """
    High-performance async data loss protection for log messages.
    
    This class provides robust backup and restore functionality for log messages
    with atomic file operations, efficient serialization, and proper error handling.
    
    Features:
    - Async backup and restore operations
    - Atomic file operations for data integrity
    - Efficient JSON serialization
    - Automatic cleanup of backup files
    - Thread-safe operations
    - Performance monitoring and statistics
    """
    
    def __init__(self, backup_dir: str = ".hydra_backup", max_retries: int = 3):
        """
        Initialize data loss protection.
        
        Args:
            backup_dir: Directory for backup files
            max_retries: Maximum retry attempts for operations
        """
        self.backup_dir = Path(backup_dir)
        self.max_retries = max_retries
        self._circuit_open = False
        self._failure_count = 0
        self._last_failure_time = 0
        self._circuit_timeout = 30.0  # 30 seconds
        self._lock = asyncio.Lock()
        self._stats = {
            "backup_attempts": 0,
            "backup_successes": 0,
            "backup_failures": 0,
            "restore_attempts": 0,
            "restore_successes": 0,
            "restore_failures": 0,
            "messages_backed_up": 0,
            "messages_restored": 0
        }
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def backup_message(self, message: Any, queue_name: str = "default") -> bool:
        """
        Backup a message to persistent storage asynchronously.
        
        Args:
            message: Message to backup (LogRecord or generic message)
            queue_name: Name of the queue for organization
            
        Returns:
            bool: True if backup successful
        """
        async with self._lock:
            self._stats["backup_attempts"] += 1
            
            # Check circuit breaker
            if self._circuit_open:
                if time.time() - self._last_failure_time > self._circuit_timeout:
                    self._circuit_open = False
                    self._failure_count = 0
                else:
                    self._stats["backup_failures"] += 1
                    return False
            
            for attempt in range(self.max_retries):
                try:
                    # Create backup file path
                    timestamp = time.time()
                    backup_file = self.backup_dir / f"{queue_name}_{timestamp}_{attempt}.json"
                    
                    # Serialize message
                    serialized = await self._serialize_message(message, timestamp)
                    
                    # Write atomically using async file operations
                    success = await self._write_backup_atomic(serialized, backup_file)
                    
                    if success:
                        self._stats["backup_successes"] += 1
                        self._stats["messages_backed_up"] += 1
                        self._failure_count = 0
                        return True
                    else:
                        raise Exception("Atomic write failed")
                        
                except Exception as e:
                    self._failure_count += 1
                    if attempt == self.max_retries - 1:
                        # Final failure
                        self._stats["backup_failures"] += 1
                        if self._failure_count >= 5:
                            self._circuit_open = True
                            self._last_failure_time = time.time()
                        return False
                    else:
                        # Retry with exponential backoff
                        await asyncio.sleep(0.01 * (2 ** attempt))
            
            return False
    
    async def restore_messages(self, queue_name: str = "default") -> List[Any]:
        """
        Restore messages from backup storage asynchronously.
        
        Args:
            queue_name: Name of the queue to restore from
            
        Returns:
            List[Any]: Restored messages
        """
        async with self._lock:
            self._stats["restore_attempts"] += 1
            
            try:
                # Find backup files for this queue
                backup_files = list(self.backup_dir.glob(f"{queue_name}_*.json"))
                backup_files.sort(key=lambda p: p.stat().st_mtime)  # Sort by modification time
                
                restored_messages = []
                processed_files = []
                
                for backup_file in backup_files:
                    try:
                        # Read and deserialize message
                        message = await self._read_backup_file(backup_file)
                        if message is not None:
                            restored_messages.append(message)
                            processed_files.append(backup_file)
                            
                    except Exception as e:
                        # Log error but continue with other files
                        print(f"Error reading backup file {backup_file}: {e}", file=sys.stderr)
                        continue
                
                # Clean up processed backup files
                for backup_file in processed_files:
                    try:
                        backup_file.unlink()
                    except Exception:
                        pass  # Ignore cleanup errors
                
                self._stats["restore_successes"] += 1
                self._stats["messages_restored"] += len(restored_messages)
                
                return restored_messages
                
            except Exception as e:
                self._stats["restore_failures"] += 1
                print(f"Error during message restoration: {e}", file=sys.stderr)
                return []
    
    async def _serialize_message(self, message: Any, timestamp: float) -> Dict[str, Any]:
        """Serialize a message for backup storage."""
        if isinstance(message, logging.LogRecord):
            return {
                "type": "log_record",
                "name": message.name,
                "level": message.levelname,
                "levelno": message.levelno,
                "message": message.getMessage(),
                "timestamp": timestamp,
                "pathname": message.pathname,
                "lineno": message.lineno,
                "funcName": message.funcName,
                "created": message.created,
                "msecs": message.msecs,
                "relativeCreated": message.relativeCreated,
                "thread": message.thread,
                "threadName": message.threadName,
                "processName": message.processName,
                "process": message.process,
                "args": message.args,
                "exc_info": str(message.exc_info) if message.exc_info else None,
                "exc_text": message.exc_text,
                "stack_info": message.stack_info
            }
        else:
            return {
                "type": "generic",
                "message": str(message),
                "timestamp": timestamp
            }
    
    async def _deserialize_message(self, serialized: Dict[str, Any]) -> Any:
        """Deserialize a message from backup storage."""
        try:
            if serialized["type"] == "log_record":
                # Reconstruct LogRecord
                record = logging.LogRecord(
                    name=serialized["name"],
                    level=serialized["levelno"],
                    pathname=serialized["pathname"],
                    lineno=serialized["lineno"],
                    msg=serialized["message"],
                    args=serialized["args"],
                    exc_info=None  # exc_info is not easily serializable
                )
                # Set additional attributes
                record.funcName = serialized["funcName"]
                record.created = serialized["created"]
                record.msecs = serialized["msecs"]
                record.relativeCreated = serialized["relativeCreated"]
                record.thread = serialized["thread"]
                record.threadName = serialized["threadName"]
                record.processName = serialized["processName"]
                record.process = serialized["process"]
                record.exc_text = serialized["exc_text"]
                record.stack_info = serialized["stack_info"]
                return record
            else:
                # Return generic message
                return serialized.get("data", serialized.get("message", "Unknown message"))
        except Exception as e:
            print(f"Error deserializing message: {e}", file=sys.stderr)
            return None
    
    async def _write_backup_atomic(self, data: Dict[str, Any], file_path: Path) -> bool:
        """Write backup data atomically."""
        try:
            # Use the existing atomic writer in a thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                AtomicWriter.write_json_atomic, 
                data, 
                file_path
            )
        except Exception as e:
            print(f"Error writing backup atomically: {e}", file=sys.stderr)
            return False
    
    async def _read_backup_file(self, file_path: Path) -> Optional[Any]:
        """Read and deserialize a backup file."""
        try:
            # Read file in thread pool
            loop = asyncio.get_event_loop()
            serialized = await loop.run_in_executor(
                None,
                self._read_json_file,
                file_path
            )
            
            if serialized is not None:
                return await self._deserialize_message(serialized)
            return None
            
        except Exception as e:
            print(f"Error reading backup file {file_path}: {e}", file=sys.stderr)
            return None
    
    def _read_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read JSON file synchronously."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def get_protection_stats(self) -> Dict[str, Any]:
        """Get data loss protection statistics."""
        return {
            "circuit_open": self._circuit_open,
            "failure_count": self._failure_count,
            "backup_files": len(list(self.backup_dir.glob("*.json"))),
            "backup_count": len(list(self.backup_dir.glob("*.json"))),
            "stats": self._stats.copy()
        }
    
    async def should_retry(self, error: Exception) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            error: The error that occurred
            
        Returns:
            bool: True if should retry
        """
        # Check circuit breaker
        if self._circuit_open:
            if time.time() - self._last_failure_time > self._circuit_timeout:
                self._circuit_open = False
                self._failure_count = 0
            else:
                return False
        
        # Increment failure count
        self._failure_count += 1
        
        # Open circuit if too many failures
        if self._failure_count >= 5:
            self._circuit_open = True
            self._last_failure_time = time.time()
            return False
        
        return True
    
    async def cleanup_old_backups(self, max_age_hours: int = 24) -> int:
        """
        Clean up old backup files.
        
        Args:
            max_age_hours: Maximum age of backup files in hours
            
        Returns:
            int: Number of files cleaned up
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for backup_file in self.backup_dir.glob("*.json"):
                try:
                    file_age = current_time - backup_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        backup_file.unlink()
                        cleaned_count += 1
                except Exception:
                    pass  # Ignore cleanup errors
            
            return cleaned_count
        except Exception as e:
            print(f"Error cleaning up old backups: {e}", file=sys.stderr)
            return 0 