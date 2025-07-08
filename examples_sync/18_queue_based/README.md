# 18 - Queue-Based Logging

## 🎯 Overview

This example demonstrates how to implement queue-based logging patterns with Hydra-Logger. It shows:
- Asynchronous logging using queues
- Producer-consumer logging patterns
- Queue overflow handling
- Batch processing of log messages
- Performance optimization through queuing

## 🚀 Running the Example

```bash
python main.py
```

## 📊 Expected Output

```
📦 Queue-Based Logging Demo
========================================
✅ Queue-based logging demo complete! Check logs/queue_based/queued.log.
```

### Generated Log File
Check `logs/queue_based/queued.log` for queued log messages.

## 🔑 Key Concepts

### **Queue-Based Logging Benefits**
- **Non-blocking**: Application doesn't wait for logging to complete
- **Performance**: Logging doesn't impact application performance
- **Reliability**: Logs are buffered and processed asynchronously
- **Scalability**: Can handle high-volume logging efficiently
- **Batching**: Multiple logs can be processed together

### **Queue Architecture**
- **Producer**: Application code that generates log messages
- **Queue**: Buffer that holds log messages
- **Consumer**: Background process that processes queued logs
- **Handler**: Destination where processed logs are sent

### **Queue Considerations**
- **Queue Size**: How many messages can be buffered
- **Processing Speed**: How fast logs are consumed
- **Overflow Handling**: What happens when queue is full
- **Thread Safety**: Ensuring thread-safe operations

## 🎨 Code Example

```python
import threading
import time
import queue
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

class QueueLogger:
    def __init__(self, config, queue_size=1000):
        self.logger = HydraLogger(config)
        self.queue = queue.Queue(maxsize=queue_size)
        self.running = True
        self.consumer_thread = threading.Thread(target=self._consumer)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
    
    def _consumer(self):
        """Background consumer that processes queued logs."""
        while self.running:
            try:
                # Get log entry from queue with timeout
                log_entry = self.queue.get(timeout=1)
                if log_entry is None:  # Shutdown signal
                    break
                
                # Process the log entry
                level, layer, message, kwargs = log_entry
                getattr(self.logger, level)(layer, message, **kwargs)
                
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing log: {e}")
    
    def info(self, layer, message, **kwargs):
        """Queue an info log message."""
        try:
            self.queue.put(("info", layer, message, kwargs), timeout=0.1)
        except queue.Full:
            print("Queue full, dropping log message")
    
    def error(self, layer, message, **kwargs):
        """Queue an error log message."""
        try:
            self.queue.put(("error", layer, message, kwargs), timeout=0.1)
        except queue.Full:
            print("Queue full, dropping log message")
    
    def shutdown(self):
        """Shutdown the queue logger."""
        self.running = False
        self.queue.put(None)  # Signal shutdown
        self.consumer_thread.join()

def main():
    # Configure logger for queue-based logging
    config = LoggingConfig(layers={
        "QUEUE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/queue_based/queued.log",
                    format="text"
                )
            ]
        )
    })
    
    # Create queue-based logger
    queue_logger = QueueLogger(config)
    
    # Simulate high-volume logging
    for i in range(100):
        queue_logger.info("QUEUE", f"Queued log message {i+1}")
        time.sleep(0.01)  # Simulate work
    
    # Shutdown gracefully
    queue_logger.shutdown()
```

## 🧪 Queue Patterns

### **Producer-Consumer Pattern**
```python
import threading
import queue
import time

class ProducerConsumerLogger:
    def __init__(self, logger, num_consumers=3):
        self.logger = logger
        self.queue = queue.Queue(maxsize=1000)
        self.consumers = []
        self.running = True
        
        # Start consumer threads
        for i in range(num_consumers):
            consumer = threading.Thread(target=self._consumer, args=(i,))
            consumer.daemon = True
            consumer.start()
            self.consumers.append(consumer)
    
    def _consumer(self, consumer_id):
        """Consumer thread that processes logs."""
        while self.running:
            try:
                log_entry = self.queue.get(timeout=1)
                if log_entry is None:
                    break
                
                level, layer, message, kwargs = log_entry
                getattr(self.logger, level)(layer, message, 
                                         consumer_id=consumer_id, **kwargs)
                
                self.queue.task_done()
                
            except queue.Empty:
                continue
    
    def log(self, level, layer, message, **kwargs):
        """Add log message to queue."""
        try:
            self.queue.put((level, layer, message, kwargs), timeout=0.1)
        except queue.Full:
            print(f"Queue full, dropping {level} log")
    
    def shutdown(self):
        """Shutdown all consumers."""
        self.running = False
        for _ in self.consumers:
            self.queue.put(None)
        
        for consumer in self.consumers:
            consumer.join()

# Usage
logger = HydraLogger()
pc_logger = ProducerConsumerLogger(logger)

# Multiple producers
for i in range(10):
    threading.Thread(target=lambda: pc_logger.log("info", "PRODUCER", f"Message {i}")).start()

pc_logger.shutdown()
```

### **Batch Processing Pattern**
```python
class BatchQueueLogger:
    def __init__(self, logger, batch_size=50, flush_interval=5):
        self.logger = logger
        self.queue = queue.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch = []
        self.last_flush = time.time()
        self.running = True
        
        self.consumer_thread = threading.Thread(target=self._batch_consumer)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
    
    def _batch_consumer(self):
        """Consumer that processes logs in batches."""
        while self.running:
            try:
                # Get log entry with timeout
                log_entry = self.queue.get(timeout=1)
                if log_entry is None:
                    self._flush_batch()
                    break
                
                self.batch.append(log_entry)
                
                # Flush if batch is full or time has elapsed
                current_time = time.time()
                if (len(self.batch) >= self.batch_size or 
                    current_time - self.last_flush >= self.flush_interval):
                    self._flush_batch()
                
                self.queue.task_done()
                
            except queue.Empty:
                # Flush any remaining logs
                if self.batch:
                    self._flush_batch()
    
    def _flush_batch(self):
        """Flush current batch to logger."""
        if not self.batch:
            return
        
        # Log batch summary
        self.logger.info("BATCH", f"Processing batch of {len(self.batch)} logs",
                        batch_size=len(self.batch),
                        timestamp=time.time())
        
        # Process each log in batch
        for level, layer, message, kwargs in self.batch:
            getattr(self.logger, level)(layer, message, **kwargs)
        
        self.batch = []
        self.last_flush = time.time()
    
    def log(self, level, layer, message, **kwargs):
        """Add log message to batch queue."""
        try:
            self.queue.put((level, layer, message, kwargs), timeout=0.1)
        except queue.Full:
            print(f"Queue full, dropping {level} log")
    
    def shutdown(self):
        """Shutdown and flush remaining logs."""
        self.running = False
        self.queue.put(None)
        self.consumer_thread.join()

# Usage
logger = HydraLogger()
batch_logger = BatchQueueLogger(logger)

for i in range(100):
    batch_logger.log("info", "BATCH", f"Batch message {i}")

batch_logger.shutdown()
```

### **Priority Queue Pattern**
```python
import heapq

class PriorityQueueLogger:
    def __init__(self, logger, max_size=1000):
        self.logger = logger
        self.queue = []
        self.max_size = max_size
        self.lock = threading.Lock()
        self.running = True
        
        self.consumer_thread = threading.Thread(target=self._priority_consumer)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
    
    def _priority_consumer(self):
        """Consumer that processes logs by priority."""
        while self.running:
            with self.lock:
                if self.queue:
                    # Get highest priority log (lowest number = highest priority)
                    priority, timestamp, log_entry = heapq.heappop(self.queue)
                    level, layer, message, kwargs = log_entry
                    getattr(self.logger, level)(layer, message, **kwargs)
                else:
                    time.sleep(0.1)
    
    def log(self, level, layer, message, priority=5, **kwargs):
        """Add log message with priority."""
        with self.lock:
            if len(self.queue) >= self.max_size:
                # Remove lowest priority log if queue is full
                heapq.heappop(self.queue)
            
            # Add new log with priority
            heapq.heappush(self.queue, (priority, time.time(), (level, layer, message, kwargs)))
    
    def shutdown(self):
        """Shutdown and process remaining logs."""
        self.running = False
        self.consumer_thread.join()

# Usage
logger = HydraLogger()
priority_logger = PriorityQueueLogger(logger)

# Log with different priorities
priority_logger.log("error", "PRIORITY", "Critical error", priority=1)
priority_logger.log("warning", "PRIORITY", "Warning message", priority=3)
priority_logger.log("info", "PRIORITY", "Info message", priority=5)
priority_logger.log("debug", "PRIORITY", "Debug message", priority=7)

priority_logger.shutdown()
```

## 📚 Use Cases

### **High-Volume Application Logging**
```python
def high_volume_logging():
    logger = HydraLogger()
    queue_logger = QueueLogger(logger)
    
    # Simulate high-volume application
    for i in range(10000):
        queue_logger.info("HIGH_VOLUME", f"Processing item {i}")
        
        if i % 1000 == 0:
            queue_logger.info("HIGH_VOLUME", f"Processed {i} items")
    
    queue_logger.shutdown()
```

### **Real-Time System Logging**
```python
def real_time_logging():
    logger = HydraLogger()
    queue_logger = QueueLogger(logger)
    
    # Simulate real-time events
    events = ["sensor_reading", "user_action", "system_alert", "data_update"]
    
    for i in range(1000):
        event = events[i % len(events)]
        queue_logger.info("REALTIME", f"Real-time event: {event}",
                        event_type=event,
                        timestamp=time.time(),
                        event_id=i)
    
    queue_logger.shutdown()
```

### **Microservices Communication**
```python
def microservice_logging():
    logger = HydraLogger()
    queue_logger = QueueLogger(logger)
    
    # Simulate microservice communication
    services = ["user-service", "order-service", "payment-service", "inventory-service"]
    
    for i in range(500):
        service = services[i % len(services)]
        queue_logger.info("MICROSERVICE", f"Service communication",
                        service=service,
                        request_id=f"req_{i}",
                        timestamp=time.time())
    
    queue_logger.shutdown()
```

## ⚡ Performance Strategies

### **1. Queue Size Optimization**
```python
def optimize_queue_size():
    # Test different queue sizes
    queue_sizes = [100, 500, 1000, 5000]
    
    for size in queue_sizes:
        logger = HydraLogger()
        queue_logger = QueueLogger(logger, queue_size=size)
        
        start_time = time.time()
        
        # Simulate logging load
        for i in range(10000):
            queue_logger.info("PERFORMANCE", f"Test message {i}")
        
        end_time = time.time()
        print(f"Queue size {size}: {end_time - start_time:.2f}s")
        
        queue_logger.shutdown()
```

### **2. Consumer Thread Optimization**
```python
def optimize_consumers():
    # Test different numbers of consumer threads
    consumer_counts = [1, 2, 4, 8]
    
    for count in consumer_counts:
        logger = HydraLogger()
        pc_logger = ProducerConsumerLogger(logger, num_consumers=count)
        
        start_time = time.time()
        
        # Simulate logging load
        for i in range(10000):
            pc_logger.log("info", "PERFORMANCE", f"Test message {i}")
        
        end_time = time.time()
        print(f"Consumers {count}: {end_time - start_time:.2f}s")
        
        pc_logger.shutdown()
```

### **3. Batch Size Optimization**
```python
def optimize_batch_size():
    # Test different batch sizes
    batch_sizes = [10, 25, 50, 100]
    
    for size in batch_sizes:
        logger = HydraLogger()
        batch_logger = BatchQueueLogger(logger, batch_size=size)
        
        start_time = time.time()
        
        # Simulate logging load
        for i in range(10000):
            batch_logger.log("info", "PERFORMANCE", f"Test message {i}")
        
        end_time = time.time()
        print(f"Batch size {size}: {end_time - start_time:.2f}s")
        
        batch_logger.shutdown()
```

## 🔍 Monitoring Queue Performance

### **Queue Metrics Monitoring**
```python
class QueueMonitor:
    def __init__(self, queue_logger):
        self.queue_logger = queue_logger
        self.metrics = {
            "messages_processed": 0,
            "messages_dropped": 0,
            "queue_size": 0,
            "processing_time": 0
        }
    
    def log_metrics(self):
        """Log current queue metrics."""
        self.queue_logger.logger.info("METRICS", "Queue performance metrics",
                                    **self.metrics)
    
    def update_metrics(self, **kwargs):
        """Update metrics."""
        self.metrics.update(kwargs)

# Usage
logger = HydraLogger()
queue_logger = QueueLogger(logger)
monitor = QueueMonitor(queue_logger)

# Monitor during operation
for i in range(1000):
    queue_logger.info("MONITOR", f"Message {i}")
    
    if i % 100 == 0:
        monitor.update_metrics(
            messages_processed=i,
            queue_size=queue_logger.queue.qsize()
        )
        monitor.log_metrics()
```

### **Queue Health Monitoring**
```python
class QueueHealthMonitor:
    def __init__(self, queue_logger):
        self.queue_logger = queue_logger
        self.last_check = time.time()
    
    def check_health(self):
        """Check queue health and log warnings."""
        current_time = time.time()
        queue_size = self.queue_logger.queue.qsize()
        queue_capacity = self.queue_logger.queue.maxsize
        
        # Check queue utilization
        utilization = queue_size / queue_capacity
        
        if utilization > 0.8:
            self.queue_logger.logger.warning("HEALTH", "Queue utilization high",
                                           utilization=utilization,
                                           queue_size=queue_size,
                                           queue_capacity=queue_capacity)
        
        # Check processing rate
        if current_time - self.last_check > 60:  # Check every minute
            self.queue_logger.logger.info("HEALTH", "Queue health check",
                                        queue_size=queue_size,
                                        utilization=utilization)
            self.last_check = current_time

# Usage
logger = HydraLogger()
queue_logger = QueueLogger(logger)
health_monitor = QueueHealthMonitor(queue_logger)

# Monitor during operation
for i in range(10000):
    queue_logger.info("HEALTH", f"Message {i}")
    
    if i % 1000 == 0:
        health_monitor.check_health()
```

## 📚 Best Practices

### **1. Handle Queue Overflow**
```python
def handle_queue_overflow():
    logger = HydraLogger()
    queue_logger = QueueLogger(logger, queue_size=100)
    
    # Simulate queue overflow
    for i in range(200):  # More than queue size
        try:
            queue_logger.info("OVERFLOW", f"Message {i}")
        except Exception as e:
            print(f"Queue overflow: {e}")
    
    queue_logger.shutdown()
```

### **2. Graceful Shutdown**
```python
def graceful_shutdown():
    logger = HydraLogger()
    queue_logger = QueueLogger(logger)
    
    # Add logs
    for i in range(100):
        queue_logger.info("SHUTDOWN", f"Message {i}")
    
    # Graceful shutdown
    queue_logger.shutdown()
    print("Logger shutdown complete")
```

### **3. Error Handling**
```python
def error_handling():
    logger = HydraLogger()
    queue_logger = QueueLogger(logger)
    
    try:
        # Simulate errors
        for i in range(100):
            if i % 10 == 0:
                queue_logger.error("ERROR", f"Error message {i}")
            else:
                queue_logger.info("INFO", f"Info message {i}")
    except Exception as e:
        print(f"Error in queue logging: {e}")
    finally:
        queue_logger.shutdown()
```

## 📚 Next Steps

After understanding this example, try:
- **13_high_concurrency** - Thread-safe logging
- **14_backpressure_handling** - Handle high throughput scenarios
- **19_monitoring_integration** - Monitoring system integration 