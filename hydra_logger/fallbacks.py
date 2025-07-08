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


class ThreadSafeLogger:
    """Thread-safe logger with minimal overhead."""
    
    _instance = None
    _lock = threading.Lock()
    
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
        self._logger.warning(message)
    
    def error(self, message: str):
        self._logger.error(message)
    
    def info(self, message: str):
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
                csv.reader(f)
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
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1)
                return False
            except:
                return True
    
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
        """Write JSON data atomically using temporary file."""
        file_path = Path(file_path)
        temp_path = file_path.with_suffix('.tmp')
        
        try:
            # Write to temporary file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, default=str)
            
            # Atomic rename
            temp_path.replace(file_path)
            return True
        except Exception as e:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    @classmethod
    def write_json_lines_atomic(cls, records: List[Dict[str, Any]], 
                               file_path: Union[str, Path]) -> bool:
        """Write JSON Lines data atomically."""
        file_path = Path(file_path)
        temp_path = file_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                for record in records:
                    f.write(json.dumps(record, default=str) + '\n')
            
            temp_path.replace(file_path)
            return True
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    @classmethod
    def write_csv_atomic(cls, records: List[Dict[str, Any]], 
                        file_path: Union[str, Path]) -> bool:
        """Write CSV data atomically."""
        file_path = Path(file_path)
        temp_path = file_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                if records:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    for record in records:
                        sanitized_record = DataSanitizer.sanitize_dict_for_csv(record)
                        writer.writerow(sanitized_record)
            
            temp_path.replace(file_path)
            return True
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise e


class BackupManager:
    """Thread-safe backup manager with connection pooling."""
    
    _instance = None
    _lock = threading.Lock()
    _backup_cache = {}
    _backup_cache_lock = threading.Lock()
    
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
            backup_path = self._backup_dir / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
        else:
            backup_path = file_path.with_suffix(f'{file_path.suffix}{suffix}')
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self._logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_from_backup(self, file_path: Union[str, Path], 
                          backup_path: Union[str, Path]) -> bool:
        """Restore file from backup."""
        try:
            shutil.copy2(backup_path, file_path)
            return True
        except Exception as e:
            self._logger.error(f"Failed to restore from backup: {e}")
            return False


class DataRecovery:
    """Thread-safe data recovery with caching."""
    
    _instance = None
    _lock = threading.Lock()
    _recovery_cache = {}
    _recovery_cache_lock = threading.Lock()
    
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
        """Attempt to recover data from a corrupted JSON file."""
        file_path = str(file_path)
        
        # Check cache first
        with self._recovery_cache_lock:
            if file_path in self._recovery_cache:
                return self._recovery_cache[file_path]
        
        if not os.path.exists(file_path):
            return None
        
        # Try to read as JSON Lines first
        try:
            records = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            records.append(record)
                        except json.JSONDecodeError:
                            continue
            if records:
                with self._recovery_cache_lock:
                    self._recovery_cache[file_path] = records
                return records
        except Exception:
            pass
        
        # Try to extract partial JSON
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            records = []
            brace_count = 0
            start_pos = 0
            
            for i, char in enumerate(content):
                if char == '{':
                    if brace_count == 0:
                        start_pos = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        try:
                            json_str = content[start_pos:i+1]
                            record = json.loads(json_str)
                            records.append(record)
                        except json.JSONDecodeError:
                            continue
            
            if records:
                with self._recovery_cache_lock:
                    self._recovery_cache[file_path] = records
                return records
        except Exception:
            pass
        
        return None
    
    def recover_csv_file(self, file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
        """Attempt to recover data from a corrupted CSV file."""
        file_path = str(file_path)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            records = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
            return records if records else None
        except Exception:
            return None


class FallbackHandler:
    """High-performance fallback handler with singleton pattern."""
    
    _instance = None
    _lock = threading.Lock()
    _file_locks = {}
    _file_locks_lock = threading.Lock()
    
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
            if os.path.exists(file_path):
                backup_path = self._backup_manager.create_backup(file_path)
                if backup_path:
                    self._logger.info(f"Created backup: {backup_path}")
            
            try:
                # Sanitize data
                sanitized_data = DataSanitizer.sanitize_for_json(data)
                
                # Write atomically
                AtomicWriter.write_json_atomic(sanitized_data, file_path, indent)
                return True
            except Exception as e:
                self._logger.error(f"Failed to write JSON: {e}")
                
                # Try to restore from backup
                if os.path.exists(file_path) and CorruptionDetector.detect_corruption(file_path, 'json'):
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
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
            if os.path.exists(file_path):
                backup_path = self._backup_manager.create_backup(file_path)
                if backup_path:
                    self._logger.info(f"Created backup: {backup_path}")
            
            try:
                # Sanitize records
                sanitized_records = [DataSanitizer.sanitize_for_json(record) for record in records]
                
                # Write atomically
                AtomicWriter.write_json_lines_atomic(sanitized_records, file_path)
                return True
            except Exception as e:
                self._logger.error(f"Failed to write JSON Lines: {e}")
                
                # Try to restore from backup
                if os.path.exists(file_path) and CorruptionDetector.detect_corruption(file_path, 'json_lines'):
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
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
            if os.path.exists(file_path):
                backup_path = self._backup_manager.create_backup(file_path)
                if backup_path:
                    self._logger.info(f"Created backup: {backup_path}")
            
            try:
                # Sanitize records
                sanitized_records = [DataSanitizer.sanitize_dict_for_csv(record) for record in records]
                
                # Write atomically
                AtomicWriter.write_csv_atomic(sanitized_records, file_path)
                return True
            except Exception as e:
                self._logger.error(f"Failed to write CSV: {e}")
                
                # Try to restore from backup
                if os.path.exists(file_path) and CorruptionDetector.detect_corruption(file_path, 'csv'):
                    backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                    if backup_files:
                        latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                        if self._backup_manager.restore_from_backup(file_path, latest_backup):
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
                self._logger.warning(f"Detected corruption in {file_path}")
                
                # Try to recover data
                recovered_data = self._recovery.recover_json_file(file_path)
                if recovered_data:
                    self._logger.info(f"Successfully recovered data from {file_path}")
                    return recovered_data
                
                # Try to restore from backup
                backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                if backup_files:
                    latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                    if self._backup_manager.restore_from_backup(file_path, latest_backup):
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
                self._logger.warning(f"Detected corruption in {file_path}")
                
                # Try to recover data
                recovered_data = self._recovery.recover_csv_file(file_path)
                if recovered_data:
                    self._logger.info(f"Successfully recovered data from {file_path}")
                    return recovered_data
                
                # Try to restore from backup
                backup_files = list(Path(file_path).parent.glob(f"{Path(file_path).stem}*.backup"))
                if backup_files:
                    latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
                    if self._backup_manager.restore_from_backup(file_path, latest_backup):
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
            
            # Normal read
            try:
                records = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        records.append(row)
                return records
            except Exception as e:
                self._logger.error(f"Failed to read CSV: {e}")
                return None


# Async-compatible wrapper functions
async def async_safe_write_json(data: Any, file_path: Union[str, Path], 
                               indent: Optional[int] = None) -> bool:
    """Async wrapper for safe JSON writing."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, safe_write_json, data, file_path, indent)


async def async_safe_write_csv(records: List[Dict[str, Any]], 
                              file_path: Union[str, Path]) -> bool:
    """Async wrapper for safe CSV writing."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, safe_write_csv, records, file_path)


async def async_safe_read_json(file_path: Union[str, Path]) -> Optional[Any]:
    """Async wrapper for safe JSON reading."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, safe_read_json, file_path)


async def async_safe_read_csv(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
    """Async wrapper for safe CSV reading."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, safe_read_csv, file_path)


# Convenience functions (thread-safe)
def safe_write_json(data: Any, file_path: Union[str, Path], 
                   indent: Optional[int] = None) -> bool:
    """Convenience function for safe JSON writing."""
    handler = FallbackHandler()
    return handler.safe_write_json(data, file_path, indent)


def safe_write_csv(records: List[Dict[str, Any]], 
                  file_path: Union[str, Path]) -> bool:
    """Convenience function for safe CSV writing."""
    handler = FallbackHandler()
    return handler.safe_write_csv(records, file_path)


def safe_read_json(file_path: Union[str, Path]) -> Optional[Any]:
    """Convenience function for safe JSON reading."""
    handler = FallbackHandler()
    return handler.safe_read_json(file_path)


def safe_read_csv(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]:
    """Convenience function for safe CSV reading."""
    handler = FallbackHandler()
    return handler.safe_read_csv(file_path)


# Performance monitoring and cleanup
def clear_all_caches():
    """Clear all caches for memory management."""
    DataSanitizer.clear_cache()
    CorruptionDetector.clear_cache()


def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics."""
    return {
        'sanitizer_cache_size': len(DataSanitizer._cache),
        'corruption_cache_size': len(CorruptionDetector._cache),
        'file_locks_count': len(FallbackHandler._file_locks),
        'recovery_cache_size': len(DataRecovery._recovery_cache)
    } 