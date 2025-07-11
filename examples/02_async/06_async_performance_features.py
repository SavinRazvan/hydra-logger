#!/usr/bin/env python3
"""
Async Performance Features Example

This example demonstrates performance optimizations:
- Object pooling for LogRecord instances
- Zero-copy batching
- High-throughput logging
- Performance monitoring
- Memory efficiency
"""

import asyncio
import time
import psutil
import gc
from hydra_logger.async_hydra.async_logger import AsyncHydraLogger
from hydra_logger.config.loaders import load_config_from_dict

# Shared config for all async performance demos
SHARED_CONFIG = {
    "default_level": "INFO",
    "layers": {
        "DEFAULT": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "TEST": {
            "level": "DEBUG",
            "destinations": [
                {"type": "console", "level": "DEBUG", "format": "plain-text"}
            ]
        },
        "PERFORMANCE": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "MEMORY": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "BATCH": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "MONITOR": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "ZERO_COPY": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "STRESS": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "WORKER_0": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "WORKER_1": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "WORKER_2": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "WORKER_3": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        },
        "WORKER_4": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "level": "INFO", "format": "plain-text"}
            ]
        }
    }
}

async def object_pooling_demo():
    """Demonstrate object pooling benefits."""
    print("\n=== Object Pooling Demo ===")
    
    # Test without object pooling
    print("Testing without object pooling...")
    start_time = time.time()
    logger_no_pool = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_object_pooling=False,
        test_mode=True
    )
    await logger_no_pool.initialize()
    
    for i in range(1000):
        await logger_no_pool.info("TEST", f"Message {i}")
    
    time_without_pool = time.time() - start_time
    print(f"Time without pooling: {time_without_pool:.3f}s")
    
    # Test with object pooling
    print("Testing with object pooling...")
    start_time = time.time()
    logger_with_pool = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_object_pooling=True,
        pool_size=1000,
        test_mode=True
    )
    await logger_with_pool.initialize()
    
    for i in range(1000):
        await logger_with_pool.info("TEST", f"Message {i}")
    
    time_with_pool = time.time() - start_time
    print(f"Time with pooling: {time_with_pool:.3f}s")
    
    # Calculate improvement
    improvement = ((time_without_pool - time_with_pool) / time_without_pool) * 100
    print(f"Performance improvement: {improvement:.1f}%")


async def high_throughput_demo():
    """Demonstrate high-throughput logging."""
    print("\n=== High-Throughput Demo ===")
    
    logger = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_object_pooling=True,
        pool_size=10000,
        queue_size=10000,
        batch_size=1000,
        batch_timeout=0.001,
        test_mode=True
    )
    await logger.initialize()
    
    # Log messages at high rate
    start_time = time.time()
    tasks = []
    
    print("Creating 10,000 async logging tasks...")
    for i in range(10000):
        task = asyncio.create_task(
            logger.info("PERFORMANCE", f"High throughput message {i}")
        )
        tasks.append(task)
    
    print("Waiting for all tasks to complete...")
    await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    throughput = 10000 / total_time
    
    print(f"Total time: {total_time:.3f}s")
    print(f"Throughput: {throughput:.0f} messages/second")
    
    if throughput > 1000:
        print("High throughput achieved!")
    else:
        print("Throughput below target")


async def memory_efficiency_demo():
    """Demonstrate memory efficiency."""
    print("\n=== Memory Efficiency Demo ===")
    
    # Force garbage collection
    gc.collect()
    initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"Initial memory usage: {initial_memory:.1f} MB")
    
    # Create logger with object pooling
    logger = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_object_pooling=True,
        pool_size=1000,
        test_mode=True
    )
    await logger.initialize()
    
    # Log many messages
    print("Logging 5,000 messages...")
    for i in range(5000):
        await logger.info("MEMORY", f"Memory test message {i}")
    
    # Force garbage collection
    gc.collect()
    final_memory = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"Final memory usage: {final_memory:.1f} MB")
    
    memory_increase = final_memory - initial_memory
    print(f"Memory increase: {memory_increase:.1f} MB")
    
    if memory_increase < 50:  # Less than 50MB increase
        print("Memory efficient!")
    else:
        print("High memory usage")


async def batch_processing_demo():
    """Demonstrate batch processing efficiency."""
    print("\n=== Batch Processing Demo ===")
    
    logger = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        batch_size=100,
        batch_timeout=0.1,
        test_mode=True
    )
    await logger.initialize()
    
    # Log messages in batches
    print("Logging messages in batches...")
    start_time = time.time()
    
    for i in range(1000):
        await logger.info("BATCH", f"Batch message {i}")
    
    # Wait for all batches to be processed
    await logger.await_pending()
    
    total_time = time.time() - start_time
    print(f"Batch processing time: {total_time:.3f}s")
    print(f"Average time per message: {(total_time / 1000) * 1000:.2f}ms")


async def performance_monitoring_demo():
    """Demonstrate performance monitoring."""
    print("\n=== Performance Monitoring Demo ===")
    
    logger = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_performance_monitoring=True,
        test_mode=True
    )
    
    # Initialize the async logger
    await logger.initialize()
    
    # Log messages with performance monitoring
    print("Logging messages with performance monitoring...")
    for i in range(100):
        await logger.info("MONITOR", f"Monitored message {i}")
    
    # Get performance statistics
    stats = await logger.get_async_performance_statistics()
    
    if stats:
        print("Performance Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("No performance statistics available")


async def zero_copy_demo():
    """Demonstrate zero-copy batching."""
    print("\n=== Zero-Copy Batching Demo ===")
    
    logger = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_object_pooling=True,
        test_mode=True
    )
    
    # Test with different batch sizes
    batch_sizes = [10, 50, 100, 500]
    
    for batch_size in batch_sizes:
        print(f"Testing batch size: {batch_size}")
        start_time = time.time()
        
        # Create tasks for batch processing
        tasks = []
        for i in range(1000):
            task = asyncio.create_task(
                logger.info("ZERO_COPY", f"Zero-copy message {i}")
            )
            tasks.append(task)
        
        # Wait for completion
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        throughput = 1000 / total_time
        
        print(f"  Time: {total_time:.3f}s")
        print(f"  Throughput: {throughput:.0f} msg/s")


async def concurrent_logging_demo():
    """Demonstrate concurrent logging capabilities."""
    print("\n=== Concurrent Logging Demo ===")
    
    logger = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_object_pooling=True,
        test_mode=True
    )
    
    async def log_worker(worker_id: int, message_count: int):
        """Worker function for concurrent logging."""
        for i in range(message_count):
            await logger.info(
                f"WORKER_{worker_id}",
                f"Worker {worker_id} message {i}"
            )
    
    # Create multiple concurrent workers
    workers = []
    for i in range(5):
        worker = asyncio.create_task(log_worker(i, 100))
        workers.append(worker)
    
    print("Starting 5 concurrent logging workers...")
    start_time = time.time()
    
    # Wait for all workers to complete
    await asyncio.gather(*workers)
    
    total_time = time.time() - start_time
    total_messages = 5 * 100
    throughput = total_messages / total_time
    
    print(f"Total time: {total_time:.3f}s")
    print(f"Total messages: {total_messages}")
    print(f"Throughput: {throughput:.0f} messages/second")


async def stress_test():
    """Run a stress test with all performance features."""
    print("\n=== Stress Test ===")
    
    logger = AsyncHydraLogger(
        config=load_config_from_dict(SHARED_CONFIG),
        enable_object_pooling=True,
        pool_size=10000,
        queue_size=50000,
        batch_size=1000,
        batch_timeout=0.001,
        enable_performance_monitoring=True,
        test_mode=True
    )
    
    print("Running stress test with 50,000 messages...")
    start_time = time.time()
    
    # Create tasks for stress test
    tasks = []
    for i in range(50000):
        task = asyncio.create_task(
            logger.info("STRESS", f"Stress test message {i}")
        )
        tasks.append(task)
    
    # Wait for completion
    await asyncio.gather(*tasks)
    
    # Wait for all processing to complete
    await logger.await_pending()
    
    total_time = time.time() - start_time
    throughput = 50000 / total_time
    
    print(f"Stress test completed!")
    print(f"Total time: {total_time:.3f}s")
    print(f"Throughput: {throughput:.0f} messages/second")
    
    if throughput > 5000:
        print("Excellent performance!")
    elif throughput > 1000:
        print("Good performance!")
    else:
        print("Performance needs improvement")


async def main():
    """Run all performance feature examples."""
    print("🚀 Async Performance Features Examples")
    print("=" * 50)
    
    await object_pooling_demo()
    await high_throughput_demo()
    await memory_efficiency_demo()
    await batch_processing_demo()
    await performance_monitoring_demo()
    await zero_copy_demo()
    await concurrent_logging_demo()
    await stress_test()
    
    print("\n✅ All performance feature examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 