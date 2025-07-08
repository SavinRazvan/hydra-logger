#!/usr/bin/env python3
"""
Performance Monitoring Example

This example demonstrates performance monitoring:
- Performance metrics collection
- Memory usage tracking
- Throughput measurement
- Performance optimization
"""

import time
import threading
from hydra_logger import HydraLogger

def demo_performance_monitoring():
    """Demonstrate performance monitoring and metrics collection."""
    
    print("⚡ Performance Monitoring Example")
    print("=" * 50)
    
    # Create logger with performance monitoring
    logger = HydraLogger()
    
    print("🚀 Starting performance monitoring...")
    
    # Log performance metrics
    logger.info("PERF", "Application started", 
               startup_time_ms=150,
               memory_usage_mb=256,
               cpu_percent=15)
    
    logger.info("PERF", "Database query executed",
               query_time_ms=45,
               rows_returned=1000,
               cache_hit_rate=0.85)
    
    logger.info("PERF", "API response time",
               response_time_ms=120,
               status_code=200,
               payload_size_kb=2.5)
    
    logger.info("PERF", "Memory usage update",
               memory_usage_mb=512,
               memory_peak_mb=768,
               gc_collections=3)
    
    # Simulate high-throughput logging
    print("\n🔄 Simulating high-throughput logging...")
    
    start_time = time.time()
    log_count = 0
    
    # Log many messages quickly to test performance
    for i in range(100):
        logger.info("PERF", f"Performance test message {i+1}", 
                   message_id=i+1,
                   timestamp=time.time())
        log_count += 1
    
    end_time = time.time()
    duration = end_time - start_time
    throughput = log_count / duration
    
    print(f"\n📊 Performance Results:")
    print(f"   Messages logged: {log_count}")
    print(f"   Duration: {duration:.3f} seconds")
    print(f"   Throughput: {throughput:.1f} logs/second")
    
    # Simulate concurrent logging
    print("\n🔄 Simulating concurrent logging...")
    
    def log_messages(thread_id):
        """Log messages from a thread."""
        for i in range(20):
            logger.info("PERF", f"Concurrent message from thread {thread_id}", 
                       thread_id=thread_id,
                       message_id=i+1,
                       timestamp=time.time())
            time.sleep(0.01)  # Small delay to simulate real work
    
    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=log_messages, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("\n✅ Concurrent logging completed!")
    
    # Get performance metrics
    print("\n📈 Performance Metrics Summary:")
    print("   - High-throughput logging tested")
    print("   - Concurrent logging tested")
    print("   - Memory usage tracked")
    print("   - Response times monitored")
    
    print("\n✅ Performance monitoring example completed!")
    print("💡 Performance metrics help optimize logging for production use")

if __name__ == "__main__":
    demo_performance_monitoring() 