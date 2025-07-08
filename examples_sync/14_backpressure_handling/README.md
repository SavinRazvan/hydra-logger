# 14 - Backpressure Handling

## 🎯 Overview

This example demonstrates how Hydra-Logger handles backpressure when log production exceeds processing speed. It shows:
- What happens when logs are produced faster than they can be processed
- How the logger handles queue overflow
- Strategies for managing high-throughput logging
- Performance implications of backpressure

## 🚀 Running the Example

```bash
python main.py
```

## 📊 Expected Output

```
💥 Backpressure Handling Demo
========================================
✅ Backpressure demo complete! Check logs/backpressure/burst.log.
```

### Generated Log File
Check `logs/backpressure/burst.log` for the burst of log messages.

## 🔑 Key Concepts

### **What is Backpressure?**
- Backpressure occurs when log production exceeds processing capacity
- The logger's internal queue becomes full
- New log messages may be dropped or blocked
- System performance can be affected

### **Backpressure Scenarios**
- High-frequency logging (e.g., debug logs in tight loops)
- Multiple threads logging simultaneously
- Slow I/O destinations (network, disk)
- Large log messages

### **Handling Strategies**
- **Drop**: Lose some logs to maintain performance
- **Block**: Wait for queue space (can slow application)
- **Throttle**: Reduce logging frequency
- **Async**: Use background processing

## 🎨 Code Example

```python
import threading
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def burst_logger(logger, n):
    """Simulate a burst of log messages."""
    for i in range(n):
        logger.info("BACKPRESSURE", f"Burst log {i+1}")
        # No sleep: simulate burst

def main():
    # Configure logger for backpressure testing
    config = LoggingConfig(layers={
        "BACKPRESSURE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/backpressure/burst.log",
                    format="text"
                )
            ]
        )
    })
    
    logger = HydraLogger(config)
    
    # Simulate a burst from multiple threads
    threads = []
    for _ in range(5):
        t = threading.Thread(target=burst_logger, args=(logger, 100))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
```

## 🧪 Testing Backpressure

### **Basic Backpressure Test**
```python
def test_backpressure():
    logger = HydraLogger()
    
    # Rapid logging to trigger backpressure
    for i in range(10000):
        logger.info("TEST", f"Rapid log {i}")
        # No delay to create backpressure
```

### **Controlled Backpressure Test**
```python
import time

def controlled_backpressure_test():
    logger = HydraLogger()
    
    start_time = time.time()
    for i in range(1000):
        logger.info("CONTROLLED", f"Log {i}")
        if i % 100 == 0:
            time.sleep(0.1)  # Brief pause
    
    end_time = time.time()
    print(f"Logging took {end_time - start_time:.2f} seconds")
```

### **Memory Usage Test**
```python
import psutil
import os

def memory_test():
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    logger = HydraLogger()
    for i in range(10000):
        logger.info("MEMORY", f"Log {i}")
    
    final_memory = process.memory_info().rss
    print(f"Memory increase: {(final_memory - initial_memory) / 1024 / 1024:.2f} MB")
```

## 📚 Use Cases

### **High-Frequency Events**
```python
def high_frequency_logging():
    logger = HydraLogger()
    
    # Simulate high-frequency events
    for event in range(10000):
        logger.info("EVENT", f"Event {event}", 
                   timestamp=time.time(),
                   event_type="user_action")
```

### **Debug Logging in Loops**
```python
def debug_loop_logging():
    logger = HydraLogger()
    
    # Debug logging in tight loop
    for i in range(100000):
        logger.debug("DEBUG", f"Loop iteration {i}")
        # Process data
        if i % 1000 == 0:
            logger.info("INFO", f"Processed {i} items")
```

### **Network Logging**
```python
def network_logging_simulation():
    logger = HydraLogger()
    
    # Simulate slow network destination
    for i in range(1000):
        logger.info("NETWORK", f"Network log {i}")
        # Simulate network delay
        time.sleep(0.001)
```

## ⚡ Performance Strategies

### **1. Use Appropriate Log Levels**
```python
# In production, avoid DEBUG level for high-frequency events
logger = HydraLogger()
logger.set_level("INFO")  # Skip DEBUG logs

# Use DEBUG only when needed
if debug_enabled:
    logger.debug("DEBUG", "Detailed debug info")
```

### **2. Batch Logging**
```python
def batch_logging():
    logger = HydraLogger()
    batch = []
    
    for i in range(1000):
        batch.append(f"Log message {i}")
        
        if len(batch) >= 100:
            # Log batch
            logger.info("BATCH", f"Batch of {len(batch)} messages", 
                       messages=batch)
            batch = []
```

### **3. Throttled Logging**
```python
import time

class ThrottledLogger:
    def __init__(self, logger, max_per_second=100):
        self.logger = logger
        self.max_per_second = max_per_second
        self.last_log_time = 0
        self.log_count = 0
    
    def info(self, layer, message, **kwargs):
        current_time = time.time()
        
        if current_time - self.last_log_time >= 1:
            # Reset counter for new second
            self.log_count = 0
            self.last_log_time = current_time
        
        if self.log_count < self.max_per_second:
            self.logger.info(layer, message, **kwargs)
            self.log_count += 1
        else:
            # Skip this log due to throttling
            pass
```

### **4. Async Logging**
```python
# For very high throughput, use async logging
from hydra_logger.async_logger import AsyncHydraLogger

async def async_logging():
    logger = AsyncHydraLogger()
    
    for i in range(10000):
        await logger.info("ASYNC", f"Async log {i}")
```

## 🔍 Monitoring Backpressure

### **Queue Size Monitoring**
```python
def monitor_queue_size(logger):
    # This would require access to internal queue
    # In practice, monitor system performance
    import psutil
    
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    
    logger.info("MONITOR", "System metrics",
               cpu_percent=cpu_percent,
               memory_percent=memory_percent)
```

### **Log Drop Detection**
```python
class DropDetectingLogger:
    def __init__(self, logger):
        self.logger = logger
        self.dropped_count = 0
    
    def info(self, layer, message, **kwargs):
        try:
            self.logger.info(layer, message, **kwargs)
        except Exception as e:
            self.dropped_count += 1
            # Log the drop
            print(f"Log dropped: {message}")
```

## 📚 Best Practices

### **1. Use Structured Logging**
```python
# Good: Structured logging with context
logger.info("USER", "User action",
           user_id=123,
           action="login",
           timestamp=time.time())

# Avoid: String concatenation in high-frequency scenarios
logger.info("USER", f"User {user_id} performed {action}")
```

### **2. Implement Circuit Breaker**
```python
class CircuitBreakerLogger:
    def __init__(self, logger, threshold=1000):
        self.logger = logger
        self.threshold = threshold
        self.log_count = 0
        self.circuit_open = False
    
    def info(self, layer, message, **kwargs):
        if self.circuit_open:
            return  # Skip logging
        
        self.log_count += 1
        if self.log_count > self.threshold:
            self.circuit_open = True
            return
        
        self.logger.info(layer, message, **kwargs)
```

### **3. Use Sampling for High-Frequency Events**
```python
import random

def sampled_logging(logger, message, sample_rate=0.1):
    """Log only a sample of high-frequency events."""
    if random.random() < sample_rate:
        logger.info("SAMPLE", message)
```

## 📚 Configuration Options

### **Queue Size Configuration**
```python
# Configure larger queue for high-throughput scenarios
config = LoggingConfig(
    queue_size=10000,  # Larger queue
    layers={
        "HIGH_THROUGHPUT": LogLayer(
            level="INFO",
            destinations=[...]
        )
    }
)
```

### **Async Configuration**
```python
# Use async logging for high throughput
config = LoggingConfig(
    async_mode=True,
    layers={...}
)
```

## 📚 Next Steps

After understanding this example, try:
- **13_high_concurrency** - Thread-safe logging
- **17_real_time_monitoring** - Monitor system performance
- **18_queue_based** - Queue-based logging patterns 