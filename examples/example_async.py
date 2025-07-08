#!/usr/bin/env python3
"""
Async HydraLogger Example with High-Performance Fallbacks

This example demonstrates async logging with the new high-performance
fallbacks module, showing concurrent operations and async data processing.
"""

import asyncio
import time
from hydra_logger import HydraLogger, LoggingConfig, LogLayer, LogDestination
from hydra_logger.fallbacks import (
    async_safe_write_json, async_safe_write_csv,
    async_safe_read_json, async_safe_read_csv,
    get_performance_stats
)


async def async_data_processor(worker_id: int, num_records: int):
    """Async data processor that logs and writes data concurrently."""
    logger = HydraLogger()
    
    # Generate test data
    records = [
        {
            'worker_id': worker_id,
            'record_id': i,
            'timestamp': time.time(),
            'data': f'async_data_{worker_id}_{i}',
            'complex_data': {
                'nested': f'value_{i}',
                'list': list(range(i % 5)),
                'bytes': b'binary_data'
            }
        }
        for i in range(num_records)
    ]
    
    # Log the data
    logger.info("ASYNC_PROCESSOR", f"Worker {worker_id} processing {len(records)} records")
    
    # Write data using async fallbacks
    json_file = f'async_data_{worker_id}.json'
    csv_file = f'async_data_{worker_id}.csv'
    
    # Concurrent async writes
    json_task = async_safe_write_json(records, json_file)
    csv_task = async_safe_write_csv(records, csv_file)
    
    # Wait for both operations to complete
    json_success, csv_success = await asyncio.gather(json_task, csv_task)
    
    if json_success and csv_success:
        logger.info("ASYNC_PROCESSOR", f"Worker {worker_id} completed successfully")
    else:
        logger.error("ASYNC_PROCESSOR", f"Worker {worker_id} had write failures")
    
    return len(records)


async def async_data_reader(worker_id: int):
    """Async data reader that reads and processes data."""
    logger = HydraLogger()
    
    json_file = f'async_data_{worker_id}.json'
    csv_file = f'async_data_{worker_id}.csv'
    
    # Concurrent async reads
    json_task = async_safe_read_json(json_file)
    csv_task = async_safe_read_csv(csv_file)
    
    json_data, csv_data = await asyncio.gather(json_task, csv_task)
    
    if json_data:
        logger.info("ASYNC_READER", f"Worker {worker_id} read {len(json_data)} JSON records")
    
    if csv_data:
        logger.info("ASYNC_READER", f"Worker {worker_id} read {len(csv_data)} CSV records")
    
    return json_data, csv_data


async def performance_monitor():
    """Monitor performance statistics during async operations."""
    logger = HydraLogger()
    
    while True:
        stats = get_performance_stats()
        logger.info("PERFORMANCE", f"Cache stats: {stats}")
        await asyncio.sleep(5)  # Monitor every 5 seconds


async def main():
    """Main async example with high-performance fallbacks."""
    print("Async HydraLogger with High-Performance Fallbacks")
    print("=" * 50)
    
    # Configure async-friendly logging
    config = LoggingConfig(
        layers={
            "ASYNC_PROCESSOR": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/async/processor.log",
                        format="json"
                    ),
                    LogDestination(
                        type="console",
                        format="text"
                    )
                ]
            ),
            "ASYNC_READER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/async/reader.log",
                        format="json"
                    )
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/async/performance.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(config)
    logger.info("ASYNC_PROCESSOR", "Starting async data processing with fallbacks")
    
    # Start performance monitoring
    monitor_task = asyncio.create_task(performance_monitor())
    
    # Create multiple async workers
    worker_tasks = []
    for worker_id in range(5):
        # Data processing task
        processor_task = async_data_processor(worker_id, 100)
        worker_tasks.append(processor_task)
        
        # Data reading task (delayed)
        async def delayed_reader(wid):
            await asyncio.sleep(2)  # Wait for processing to complete
            return await async_data_reader(wid)
        
        reader_task = delayed_reader(worker_id)
        worker_tasks.append(reader_task)
    
    # Run all workers concurrently
    start_time = time.time()
    results = await asyncio.gather(*worker_tasks, return_exceptions=True)
    total_time = time.time() - start_time
    
    # Cancel performance monitoring
    monitor_task.cancel()
    
    # Process results
    successful_workers = sum(1 for r in results if not isinstance(r, Exception))
    total_records = sum(r for r in results if isinstance(r, int))
    
    logger.info("ASYNC_PROCESSOR", f"Completed {successful_workers} workers in {total_time:.2f}s")
    logger.info("ASYNC_PROCESSOR", f"Processed {total_records} total records")
    
    # Final performance stats
    final_stats = get_performance_stats()
    logger.info("PERFORMANCE", f"Final performance stats: {final_stats}")
    
    print(f"\nAsync processing completed!")
    print(f"Total time: {total_time:.2f}s")
    print(f"Successful workers: {successful_workers}")
    print(f"Total records processed: {total_records}")
    print(f"Throughput: {total_records/total_time:.2f} records/second")


if __name__ == "__main__":
    asyncio.run(main()) 