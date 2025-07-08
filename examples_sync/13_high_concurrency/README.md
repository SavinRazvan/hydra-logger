# 13 - High Concurrency Logging

## 🎯 Overview

This example demonstrates how to use Hydra-Logger in high-concurrency scenarios. It shows:
- Thread-safe logging across multiple threads
- Log integrity under concurrent access
- Performance considerations for high-throughput logging
- Best practices for concurrent logging

## 🚀 Running the Example

```bash
python main.py
```

## 📊 Expected Output

```
🔀 High Concurrency Logging Demo
========================================
✅ High concurrency logging complete! Check logs/high_concurrency/threaded.log.
```

### Generated Log File
Check `logs/high_concurrency/threaded.log` for interleaved log messages from multiple threads.

## 🔑 Key Concepts

### **Thread Safety**
- Hydra-Logger is designed to be thread-safe
- Multiple threads can log simultaneously without data corruption
- No manual synchronization required

### **Concurrent Access**
- Each thread can log independently
- Log messages maintain their order within each thread
- Interleaving of messages from different threads is normal

### **Performance Considerations**
- High concurrency may impact performance
- Consider using async logging for very high throughput
- Monitor memory usage with many concurrent loggers

## 🎨 Code Example

```python
import threading
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def log_worker(logger, thread_id, n):
    """Worker function that logs from a thread."""
    for i in range(n):
        logger.info("CONCURRENCY", f"Thread {thread_id} log {i+1}")
        time.sleep(0.01)  # Simulate work

def main():
    # Configure logger for high concurrency
    config = LoggingConfig(layers={
        "CONCURRENCY": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/high_concurrency/threaded.log",
                    format="text"
                )
            ]
        )
    })
    
    logger = HydraLogger(config)
    
    # Create multiple threads
    threads = []
    for t in range(10):
        thread = threading.Thread(
            target=log_worker, 
            args=(logger, t+1, 20)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
```

## 🧪 Testing Thread Safety

### **Basic Thread Safety Test**
```python
import threading
from hydra_logger import HydraLogger

def test_thread_safety():
    logger = HydraLogger()
    
    def worker(thread_id):
        for i in range(100):
            logger.info("TEST", f"Thread {thread_id} - Message {i}")
    
    threads = []
    for t in range(5):
        thread = threading.Thread(target=worker, args=(t,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
```

### **Stress Test**
```python
def stress_test():
    logger = HydraLogger()
    
    def stress_worker(thread_id):
        for i in range(1000):
            logger.info("STRESS", f"Thread {thread_id} - Stress {i}")
    
    threads = []
    for t in range(20):  # 20 threads
        thread = threading.Thread(target=stress_worker, args=(t,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
```

## 📚 Use Cases

### **Web Applications**
```python
# Multiple request handlers logging simultaneously
def handle_request(request_id):
    logger.info("REQUEST", f"Request {request_id} started")
    # Process request
    logger.info("REQUEST", f"Request {request_id} completed")

# Multiple threads handling requests
for request_id in range(100):
    thread = threading.Thread(
        target=handle_request, 
        args=(request_id,)
    )
    thread.start()
```

### **Background Workers**
```python
def background_worker(worker_id):
    logger.info("WORKER", f"Worker {worker_id} started")
    while True:
        # Process tasks
        logger.info("WORKER", f"Worker {worker_id} processed task")
        time.sleep(1)

# Start multiple background workers
for worker_id in range(5):
    thread = threading.Thread(
        target=background_worker, 
        args=(worker_id,)
    )
    thread.start()
```

### **Data Processing Pipelines**
```python
def data_processor(processor_id, data_chunk):
    logger.info("PROCESSOR", f"Processor {processor_id} started")
    # Process data
    logger.info("PROCESSOR", f"Processor {processor_id} completed")

# Process data in parallel
for i, chunk in enumerate(data_chunks):
    thread = threading.Thread(
        target=data_processor, 
        args=(i, chunk)
    )
    thread.start()
```

## ⚡ Performance Tips

### **1. Use Appropriate Log Levels**
```python
# In production, use higher log levels
logger = HydraLogger()
logger.set_level("INFO")  # Reduce DEBUG logs in high concurrency
```

### **2. Consider Async Logging**
```python
# For very high throughput, consider async logging
from hydra_logger.async_logger import AsyncHydraLogger

async_logger = AsyncHydraLogger(config)
await async_logger.info("ASYNC", "High throughput logging")
```

### **3. Batch Logging**
```python
# For very high frequency logging, consider batching
def batch_logger(logger, messages):
    for message in messages:
        logger.info("BATCH", message)
```

### **4. Monitor Performance**
```python
import time

def performance_test():
    start_time = time.time()
    # Run your concurrent logging
    end_time = time.time()
    print(f"Logging took {end_time - start_time:.2f} seconds")
```

## 🔍 Debugging Concurrent Logging

### **Thread Identification**
```python
import threading

def log_with_thread_id(logger):
    thread_id = threading.current_thread().ident
    logger.info("THREAD", f"Log from thread {thread_id}")
```

### **Log Correlation**
```python
import uuid

def correlated_logging(logger):
    correlation_id = str(uuid.uuid4())
    logger.info("CORRELATED", "Start operation", correlation_id=correlation_id)
    # Do work
    logger.info("CORRELATED", "End operation", correlation_id=correlation_id)
```

## 📚 Best Practices

### **1. Avoid Blocking Operations**
```python
# Good: Non-blocking logging
logger.info("INFO", "Quick log message")

# Avoid: Blocking operations in logging
logger.info("INFO", "Heavy computation result", result=heavy_computation())
```

### **2. Use Structured Logging**
```python
# Good: Structured logging
logger.info("USER", "User action", 
           user_id=123, 
           action="login", 
           timestamp=time.time())

# Avoid: String concatenation
logger.info("USER", f"User {user_id} performed {action}")
```

### **3. Monitor Resource Usage**
```python
import psutil
import threading

def monitor_resources():
    while True:
        memory = psutil.virtual_memory()
        logger.info("MONITOR", "Memory usage", 
                   memory_percent=memory.percent)
        time.sleep(60)
```

## 📚 Next Steps

After understanding this example, try:
- **14_backpressure_handling** - Handle high throughput scenarios
- **17_real_time_monitoring** - Monitor system performance
- **18_distributed_systems** - Multi-node logging scenarios 