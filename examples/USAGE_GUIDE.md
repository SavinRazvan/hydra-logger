# HydraLogger Fallbacks - User Data Processing Guide

The HydraLogger fallbacks module provides **high-performance, thread-safe data processing** that you can use for your own applications, separate from logging.

## 🎯 **Dual-Purpose Design**

The fallbacks module serves two purposes:

1. **Internal Use**: HydraLogger uses it to write log files safely
2. **External Use**: You can use it for your own data processing needs

## 🚀 **Quick Start**

```python
from hydra_logger.fallbacks import (
    safe_write_json, safe_write_csv, 
    safe_read_json, safe_read_csv,
    get_performance_stats
)

# Write data safely
users = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
success = safe_write_json(users, 'users.json')

# Read data safely
data = safe_read_json('users.json')

# Check performance
stats = get_performance_stats()
```

## 📊 **Key Features**

### **Safe Data Writing**
- **Atomic Operations**: Uses temporary files and rename for data integrity
- **Data Sanitization**: Handles problematic data types (bytes, sets, complex numbers)
- **Error Recovery**: Graceful fallback to JSON Lines format on failure
- **Thread Safety**: Multiple threads can write to the same file safely

### **Robust Data Reading**
- **Corruption Detection**: Automatically detects and handles corrupted files
- **Data Recovery**: Recovers valid data from partially corrupted files
- **Backup Support**: Falls back to backup files if primary files are corrupted
- **Memory Efficient**: Streams large files without loading everything into memory

### **High Performance**
- **Intelligent Caching**: Caches sanitization results for 2.5x+ speedup
- **Thread-Safe**: Concurrent access with file-level locking
- **Async Compatible**: Non-blocking operations for web applications
- **Memory Optimized**: Automatic cleanup prevents memory leaks

## 🔧 **Common Use Cases**

### **1. User Data Processing**
```python
from hydra_logger.fallbacks import safe_write_json, safe_read_json

# Process user data safely
users = [
    {'id': 1, 'name': 'Alice', 'data': {'nested': 'value', 'bytes': b'binary'}},
    {'id': 2, 'name': 'Bob', 'data': {'set': {1, 2, 3}, 'complex': 1 + 2j}}
]

# Write with fallback protection
success = safe_write_json(users, 'users.json')

# Read with corruption detection
data = safe_read_json('users.json')
```

### **2. Batch Processing**
```python
def process_batch(batch_data, batch_id):
    """Process data in batches with safe handling."""
    filename = f'batch_{batch_id:03d}.json'
    success = safe_write_json(batch_data, filename)
    
    if success:
        print(f"✓ Batch {batch_id}: {len(batch_data)} records written")
    else:
        print(f"✗ Batch {batch_id}: Write failed")

# Process large datasets in batches
for i, batch in enumerate(batches):
    process_batch(batch, i)
```

### **3. Concurrent Processing**
```python
import threading
from hydra_logger.fallbacks import safe_write_json

def worker(worker_id, data_chunk):
    """Thread-safe worker function."""
    filename = f'worker_{worker_id:02d}.json'
    success = safe_write_json(data_chunk, filename)
    
    if success:
        print(f"✓ Worker {worker_id}: {len(data_chunk)} records")
    else:
        print(f"✗ Worker {worker_id}: Failed")

# Process data with multiple threads
threads = []
for i, chunk in enumerate(data_chunks):
    thread = threading.Thread(target=worker, args=(i, chunk))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
```

### **4. Data Recovery**
```python
from hydra_logger.fallbacks import safe_read_json, CorruptionDetector

# Try to read potentially corrupted data
data = safe_read_json('possibly_corrupted.json')

if data:
    print(f"✓ Recovered {len(data)} records")
else:
    print("✗ Data recovery failed")

# Check if file is corrupted
is_corrupted = CorruptionDetector.detect_corruption('file.json', 'json')
if is_corrupted:
    print("File is corrupted, attempting recovery...")
```

### **5. Performance Monitoring**
```python
from hydra_logger.fallbacks import get_performance_stats, clear_all_caches

# Get performance statistics
stats = get_performance_stats()
print(f"Cache hits: {stats['sanitizer_cache_size']}")
print(f"File locks: {stats['file_locks_count']}")

# Clear caches if needed
clear_all_caches()
```

## 📈 **Performance Characteristics**

Recent benchmarks show:

- **Write Throughput**: 56,000+ records/second
- **Read Throughput**: 78,000+ records/second  
- **Cache Speedup**: 2.5x+ improvement for repeated operations
- **Memory Efficiency**: Automatic cleanup prevents memory leaks
- **Concurrency**: File-level locking enables safe concurrent access

## 🛡️ **Error Handling**

The fallbacks module provides robust error handling:

### **Write Failures**
- Falls back to JSON Lines format
- Creates backup files automatically
- Returns success/failure status
- Logs detailed error information

### **Read Failures**
- Detects file corruption automatically
- Recovers valid data from corrupted files
- Falls back to backup files
- Returns None on complete failure

### **Data Sanitization**
- Handles bytes, sets, complex numbers
- Converts problematic types to strings
- Maintains data structure integrity
- Caches sanitization results

## 🔄 **Async Support**

For async applications:

```python
import asyncio
from hydra_logger.fallbacks import async_safe_write_json, async_safe_read_json

async def async_data_processor():
    # Async write
    success = await async_safe_write_json(data, 'async_data.json')
    
    # Async read
    data = await async_safe_read_json('async_data.json')
    
    return data

# Run async operations
result = await async_data_processor()
```

## 📁 **File Formats**

### **JSON Format**
- Writes proper JSON arrays (not JSON Lines)
- Handles complex nested data structures
- Atomic write operations with temporary files
- Corruption detection and recovery

### **CSV Format**
- Flattens nested data structures
- Handles complex data types safely
- Thread-safe concurrent access
- Automatic backup creation

## 🎯 **Best Practices**

### **1. Use for Critical Data**
```python
# Good: Use fallbacks for important data
success = safe_write_json(critical_data, 'important.json')

# Bad: Don't use for temporary data
with open('temp.json', 'w') as f:
    json.dump(temp_data, f)
```

### **2. Handle Return Values**
```python
# Always check success status
success = safe_write_json(data, 'file.json')
if not success:
    # Handle failure
    print("Write failed, using fallback...")
```

### **3. Monitor Performance**
```python
# Check performance periodically
stats = get_performance_stats()
if stats['sanitizer_cache_size'] > 1000:
    clear_all_caches()  # Prevent memory leaks
```

### **4. Use Appropriate Batch Sizes**
```python
# For large datasets, process in batches
batch_size = 1000  # Adjust based on your data size
for i in range(0, len(data), batch_size):
    batch = data[i:i + batch_size]
    safe_write_json(batch, f'batch_{i//batch_size}.json')
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **"Failed to write JSON"**
   - Check file permissions
   - Ensure directory exists
   - Verify data is serializable

2. **"Corruption detected"**
   - File was partially written
   - Use backup files if available
   - Check disk space

3. **"Cache size too large"**
   - Call `clear_all_caches()` periodically
   - Monitor memory usage
   - Restart application if needed

### **Debug Information**
```python
from hydra_logger.fallbacks import get_performance_stats

# Get detailed statistics
stats = get_performance_stats()
print(f"Cache stats: {stats}")
```

## 📚 **Examples**

See the following examples for complete implementations:

- **`example_user_data_processing.py`** - Comprehensive user data processing
- **`fallbacks_demo.py`** - All fallback features demonstrated
- **`performance_test.py`** - Performance benchmarking
- **`example_concurrent.py`** - Thread and process safety

The fallbacks module provides **enterprise-grade data processing** with robust error handling, high performance, and thread safety - perfect for production applications that need reliable data handling. 