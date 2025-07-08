# HydraLogger Fallbacks Module

The `fallbacks` module provides **high-performance, thread-safe, and async-compatible** data processing fallback mechanisms for JSON, CSV, and other structured data formats. It's designed for enterprise-grade applications with:

- **Thread-safe concurrent operations** - Multiple HydraLogger instances can run simultaneously
- **Async/await support** - Non-blocking operations for async applications
- **High-performance caching** - Intelligent caching for repeated operations
- **Singleton patterns** - Resource-efficient shared instances
- **File-level locking** - Concurrent access to the same files
- **Memory optimization** - Minimal memory footprint with automatic cleanup

## Overview

The fallbacks module is designed for **enterprise-grade performance** with data integrity and graceful degradation. It's optimized for:

- **High-concurrency environments** - Multiple threads/processes accessing the same files
- **Async applications** - Non-blocking operations for web servers and microservices
- **Memory-constrained systems** - Efficient caching with automatic cleanup
- **Production workloads** - Robust error handling and recovery mechanisms

The module uses **singleton patterns** to ensure resource efficiency and **file-level locking** to prevent data corruption during concurrent access.

## Key Components

### 1. DataSanitizer

High-performance data sanitizer with intelligent caching.

**Performance Features:**
- LRU-style caching for repeated operations
- Thread-safe cache management
- Memory-efficient object ID-based caching
- Automatic cache cleanup to prevent memory leaks

```python
from hydra_logger.fallbacks import DataSanitizer

# Sanitize data for JSON
data = {
    'string': 'Hello',
    'bytes': b'binary',
    'complex': 1+2j,
    'set': {1, 2, 3}
}
sanitized = DataSanitizer.sanitize_for_json(data)

# Sanitize data for CSV
sanitized_csv = DataSanitizer.sanitize_dict_for_csv(data)
```

**Features:**
- Converts non-serializable objects to strings
- Handles bytes, complex numbers, sets, and custom objects
- Ensures data can be safely stored in target format
- Preserves data structure while making it compatible

### 2. CorruptionDetector

High-performance corruption detector with time-based caching.

**Performance Features:**
- TTL-based caching (60-second cache lifetime)
- Thread-safe cache operations
- Fast validation for repeated checks
- Minimal I/O overhead for cached results

```python
from hydra_logger.fallbacks import CorruptionDetector

# Check if files are valid
is_valid_json = CorruptionDetector.is_valid_json('data.json')
is_valid_csv = CorruptionDetector.is_valid_csv('data.csv')
is_valid_json_lines = CorruptionDetector.is_valid_json_lines('data.jsonl')

# Detect corruption in any format
is_corrupted = CorruptionDetector.detect_corruption('data.json', 'json')
```

**Supported Formats:**
- JSON (including JSON arrays)
- JSON Lines
- CSV
- Generic file validation

### 3. AtomicWriter

Provides atomic write operations to prevent data corruption.

```python
from hydra_logger.fallbacks import AtomicWriter

# Atomic JSON write
success = AtomicWriter.write_json_atomic(data, 'output.json')

# Atomic CSV write
success = AtomicWriter.write_csv_atomic(records, 'output.csv')

# Atomic JSON Lines write
success = AtomicWriter.write_json_lines_atomic(records, 'output.jsonl')
```

**Features:**
- Uses temporary files and atomic rename operations
- Prevents partial writes during system failures
- Automatic cleanup of temporary files on failure
- Thread-safe operations

### 4. BackupManager

Manages backup files for data recovery.

```python
from hydra_logger.fallbacks import BackupManager

# Create backup manager with custom directory
backup_manager = BackupManager(backup_dir='/path/to/backups')

# Create backup of existing file
backup_path = backup_manager.create_backup('data.json')

# Restore from backup
success = backup_manager.restore_from_backup('data.json', backup_path)
```

**Features:**
- Automatic timestamp-based backup naming
- Configurable backup directory
- Safe restore operations
- Backup verification

### 5. DataRecovery

Recovers data from corrupted files.

```python
from hydra_logger.fallbacks import DataRecovery

recovery = DataRecovery()

# Recover JSON data
recovered_data = recovery.recover_json_file('corrupted.json')

# Recover CSV data
recovered_data = recovery.recover_csv_file('corrupted.csv')
```

**Recovery Strategies:**
- **JSON Recovery**: Extracts valid JSON objects from corrupted files
- **CSV Recovery**: Skips invalid rows and recovers valid data
- **Partial Recovery**: Recovers as much data as possible
- **Graceful Degradation**: Returns None if no recovery possible

### 6. FallbackHandler

High-performance fallback handler with singleton pattern and file-level locking.

**Performance Features:**
- Singleton pattern for resource efficiency
- File-level locking for concurrent access
- Thread-safe operations across multiple instances
- Automatic lock management and cleanup

```python
from hydra_logger.fallbacks import FallbackHandler

handler = FallbackHandler()

# Safe write operations
success = handler.safe_write_json(data, 'output.json')
success = handler.safe_write_csv(records, 'output.csv')

# Safe read operations
data = handler.safe_read_json('input.json')
records = handler.safe_read_csv('input.csv')
```

**Features:**
- Automatic corruption detection on startup
- Backup creation before write operations
- Fallback to alternative formats on failure
- Comprehensive error logging
- Data recovery attempts

## Async Support

The module provides async-compatible wrapper functions for non-blocking operations:

```python
from hydra_logger.fallbacks import (
    async_safe_write_json, async_safe_write_csv,
    async_safe_read_json, async_safe_read_csv
)

# Async write operations
success = await async_safe_write_json(data, 'output.json')
success = await async_safe_write_csv(records, 'output.csv')

# Async read operations
data = await async_safe_read_json('input.json')
records = await async_safe_read_csv('input.csv')
```

## Convenience Functions

For simple use cases, the module provides thread-safe convenience functions:

```python
from hydra_logger.fallbacks import (
    safe_write_json, safe_write_csv,
    safe_read_json, safe_read_csv
)

# Simple write operations
success = safe_write_json(data, 'output.json')
success = safe_write_csv(records, 'output.csv')

# Simple read operations
data = safe_read_json('input.json')
records = safe_read_csv('input.csv')
```

## Integration with HydraLogger

The fallbacks module is integrated into HydraLogger's handlers:

### JSONArrayHandler

```python
from hydra_logger import HydraLogger, LoggingConfig, LogLayer, LogDestination

config = LoggingConfig(
    layers={
        'data': LogLayer(
            destinations=[
                LogDestination(
                    type='file',
                    path='logs/data.json',
                    format='json_array'  # Uses JSONArrayHandler with fallbacks
                )
            ]
        )
    }
)

logger = HydraLogger(config)
```

### CSVHandler

```python
config = LoggingConfig(
    layers={
        'analytics': LogLayer(
            destinations=[
                LogDestination(
                    type='file',
                    path='logs/analytics.csv',
                    format='csv'  # Uses CSVHandler with fallbacks
                )
            ]
        )
    }
)
```

## Error Handling and Fallback Strategies

### 1. Data Sanitization
- Converts non-serializable objects to strings
- Handles bytes, complex numbers, and custom objects
- Preserves data structure while ensuring compatibility

### 2. Corruption Detection
- Validates file integrity on startup
- Detects corruption during read operations
- Provides detailed error information

### 3. Atomic Operations
- Uses temporary files for safe writes
- Atomic rename operations prevent partial writes
- Automatic cleanup on failure

### 4. Backup Management
- Creates backups before write operations
- Timestamp-based backup naming
- Safe restore operations

### 5. Data Recovery
- Attempts to recover data from corrupted files
- Partial recovery when full recovery isn't possible
- Graceful degradation to alternative formats

### 6. Fallback Formats
- JSON → JSON Lines
- CSV → JSON Lines
- Comprehensive error logging

## Best Practices

### 1. Regular Backup Verification
```python
from hydra_logger.fallbacks import CorruptionDetector

# Periodically check file integrity
if CorruptionDetector.detect_corruption('data.json', 'json'):
    # Trigger recovery process
    pass
```

### 2. Monitor Error Logs
```python
# Check error logs for issues
with open('data.json.error', 'r') as f:
    errors = f.readlines()
```

### 3. Use Appropriate Formats
```python
# For data analysis
safe_write_csv(records, 'analytics.csv')

# For structured logging
safe_write_json(logs, 'application.json')

# For streaming data
safe_write_json_lines(stream_data, 'stream.jsonl')
```

### 4. Handle Recovery Results
```python
recovered_data = handler.safe_read_json('corrupted.json')
if recovered_data is None:
    # Handle complete failure
    logger.error("Could not recover data from corrupted file")
else:
    # Process recovered data
    process_data(recovered_data)
```

## Performance Considerations

### 1. Memory Usage
- Intelligent caching with automatic cleanup
- LRU-style cache management
- Memory-efficient object ID-based caching
- Singleton patterns reduce memory footprint

### 2. Concurrency
- Thread-safe operations across multiple instances
- File-level locking prevents data corruption
- Async/await support for non-blocking operations
- Concurrent access to different files

### 3. Caching Strategy
- Data sanitization cache (1000 entries max)
- Corruption detection cache (60-second TTL)
- Recovery cache for repeated operations
- Automatic cache cleanup and management

### 4. I/O Operations
- Atomic writes minimize I/O overhead
- Buffered operations for better performance
- Efficient corruption detection with caching
- File-level locking for concurrent access

### 5. Error Recovery
- Fast failure detection with caching
- Minimal overhead for normal operations
- Efficient backup management
- Thread-safe error handling

## Troubleshooting

### Common Issues

1. **File Permission Errors**
   - Ensure write permissions for target directories
   - Check backup directory permissions

2. **Disk Space Issues**
   - Monitor backup directory size
   - Implement backup rotation

3. **Corruption Detection False Positives**
   - Verify file format expectations
   - Check encoding settings

4. **Recovery Failures**
   - Check error logs for details
   - Verify backup file integrity
   - Consider manual recovery procedures

### Debug Information

Enable detailed logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed fallback operations
handler = FallbackHandler()
```

## Examples

See `examples/fallbacks_demo.py` for comprehensive examples demonstrating all features of the fallbacks module.

## API Reference

### DataSanitizer

- `sanitize_for_json(data: Any) -> Any`
- `sanitize_for_csv(data: Any) -> str`
- `sanitize_dict_for_csv(data: Dict[str, Any]) -> Dict[str, str]`

### CorruptionDetector

- `is_valid_json(file_path: Union[str, Path]) -> bool`
- `is_valid_json_lines(file_path: Union[str, Path]) -> bool`
- `is_valid_csv(file_path: Union[str, Path]) -> bool`
- `detect_corruption(file_path: Union[str, Path], format_type: str) -> bool`

### AtomicWriter

- `write_json_atomic(data: Any, file_path: Union[str, Path], indent: Optional[int] = None) -> bool`
- `write_json_lines_atomic(records: List[Dict[str, Any]], file_path: Union[str, Path]) -> bool`
- `write_csv_atomic(records: List[Dict[str, Any]], file_path: Union[str, Path]) -> bool`

### BackupManager

- `create_backup(file_path: Union[str, Path], suffix: str = '.backup') -> Optional[Path]`
- `restore_from_backup(file_path: Union[str, Path], backup_path: Union[str, Path]) -> bool`

### DataRecovery

- `recover_json_file(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]`
- `recover_csv_file(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]`

### FallbackHandler

- `safe_write_json(data: Any, file_path: Union[str, Path], indent: Optional[int] = None) -> bool`
- `safe_write_csv(records: List[Dict[str, Any]], file_path: Union[str, Path]) -> bool`
- `safe_read_json(file_path: Union[str, Path]) -> Optional[Any]`
- `safe_read_csv(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]`

### Convenience Functions

- `safe_write_json(data: Any, file_path: Union[str, Path], indent: Optional[int] = None) -> bool`
- `safe_write_csv(records: List[Dict[str, Any]], file_path: Union[str, Path]) -> bool`
- `safe_read_json(file_path: Union[str, Path]) -> Optional[Any]`
- `safe_read_csv(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]`

### Async Functions

- `async_safe_write_json(data: Any, file_path: Union[str, Path], indent: Optional[int] = None) -> bool`
- `async_safe_write_csv(records: List[Dict[str, Any]], file_path: Union[str, Path]) -> bool`
- `async_safe_read_json(file_path: Union[str, Path]) -> Optional[Any]`
- `async_safe_read_csv(file_path: Union[str, Path]) -> Optional[List[Dict[str, Any]]]`

### Performance Monitoring

- `clear_all_caches() -> None` - Clear all caches for memory management
- `get_performance_stats() -> Dict[str, Any]` - Get performance statistics 