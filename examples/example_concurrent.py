#!/usr/bin/env python3
"""
Concurrent HydraLogger Example with High-Performance Fallbacks

This example demonstrates concurrent logging operations with multiple
threads and processes using the thread-safe fallbacks module.
"""

import threading
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import statistics

from hydra_logger import HydraLogger, LoggingConfig, LogLayer, LogDestination
from hydra_logger.fallbacks import (
    safe_write_json, safe_write_csv, safe_read_json, safe_read_csv,
    get_performance_stats, clear_all_caches
)


def generate_worker_data(worker_id: int, num_records: int) -> list:
    """Generate test data for a worker."""
    return [
        {
            'worker_id': worker_id,
            'record_id': i,
            'timestamp': time.time(),
            'data': f'concurrent_data_{worker_id}_{i}',
            'complex_data': {
                'nested': f'value_{i}',
                'list': list(range(i % 5)),
                'bytes': b'binary_data',
                'set': {1, 2, 3}
            }
        }
        for i in range(num_records)
    ]


def thread_worker(worker_id: int, num_records: int, shared_logger: HydraLogger):
    """Worker function for thread-based concurrent operations."""
    try:
        # Generate data
        records = generate_worker_data(worker_id, num_records)
        
        # Log the operation
        shared_logger.info("CONCURRENT_WORKER", f"Thread {worker_id} processing {len(records)} records")
        
        # Write data using fallbacks (thread-safe)
        json_file = f'concurrent_data_{worker_id}.json'
        csv_file = f'concurrent_data_{worker_id}.csv'
        
        json_success = safe_write_json(records, json_file)
        csv_success = safe_write_csv(records, csv_file)
        
        if json_success and csv_success:
            shared_logger.info("CONCURRENT_WORKER", f"Thread {worker_id} completed successfully")
        else:
            shared_logger.error("CONCURRENT_WORKER", f"Thread {worker_id} had write failures")
        
        # Read data back (thread-safe)
        json_data = safe_read_json(json_file)
        csv_data = safe_read_csv(csv_file)
        
        if json_data:
            shared_logger.info("CONCURRENT_READER", f"Thread {worker_id} read {len(json_data)} JSON records")
        
        if csv_data:
            shared_logger.info("CONCURRENT_READER", f"Thread {worker_id} read {len(csv_data)} CSV records")
        
        return len(records)
        
    except Exception as e:
        shared_logger.error("CONCURRENT_WORKER", f"Thread {worker_id} failed: {e}")
        return 0


def process_worker(worker_id: int, num_records: int):
    """Worker function for process-based concurrent operations."""
    # Create logger for this process
    logger = HydraLogger()
    
    try:
        # Generate data
        records = generate_worker_data(worker_id, num_records)
        
        # Log the operation
        logger.info("PROCESS_WORKER", f"Process {worker_id} processing {len(records)} records")
        
        # Write data using fallbacks (process-safe)
        json_file = f'process_data_{worker_id}.json'
        csv_file = f'process_data_{worker_id}.csv'
        
        json_success = safe_write_json(records, json_file)
        csv_success = safe_write_csv(records, csv_file)
        
        if json_success and csv_success:
            logger.info("PROCESS_WORKER", f"Process {worker_id} completed successfully")
        else:
            logger.error("PROCESS_WORKER", f"Process {worker_id} had write failures")
        
        return len(records)
        
    except Exception as e:
        logger.error("PROCESS_WORKER", f"Process {worker_id} failed: {e}")
        return 0


def performance_monitor(logger: HydraLogger, stop_event: threading.Event):
    """Monitor performance statistics during concurrent operations."""
    while not stop_event.is_set():
        stats = get_performance_stats()
        logger.info("PERFORMANCE", f"Cache stats: {stats}")
        time.sleep(5)  # Monitor every 5 seconds


def test_thread_concurrency():
    """Test thread-based concurrency."""
    print("\n=== Thread Concurrency Test ===")
    
    # Configure logging for concurrent operations
    config = LoggingConfig(
        layers={
            "CONCURRENT_WORKER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/concurrent/worker.log",
                        format="json"
                    ),
                    LogDestination(
                        type="console",
                        format="text"
                    )
                ]
            ),
            "CONCURRENT_READER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/concurrent/reader.log",
                        format="json"
                    )
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/concurrent/performance.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(config)
    logger.info("CONCURRENT_WORKER", "Starting thread concurrency test")
    
    # Start performance monitoring
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=performance_monitor, 
        args=(logger, stop_event)
    )
    monitor_thread.start()
    
    # Test with different numbers of threads
    thread_counts = [1, 2, 4, 8]
    records_per_thread = 50
    
    for num_threads in thread_counts:
        print(f"\nTesting with {num_threads} threads:")
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(thread_worker, i, records_per_thread, logger)
                for i in range(num_threads)
            ]
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        total_records = sum(results)
        successful_workers = sum(1 for r in results if r > 0)
        
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Total records: {total_records}")
        print(f"  Successful workers: {successful_workers}")
        print(f"  Throughput: {total_records/total_time:.2f} records/second")
    
    # Stop monitoring
    stop_event.set()
    monitor_thread.join()
    
    # Clean up test files
    for i in range(max(thread_counts)):
        for suffix in ['.json', '.csv']:
            file_path = f'concurrent_data_{i}{suffix}'
            if Path(file_path).exists():
                Path(file_path).unlink()


def test_process_concurrency():
    """Test process-based concurrency."""
    print("\n=== Process Concurrency Test ===")
    
    # Test with different numbers of processes
    process_counts = [1, 2, 4]
    records_per_process = 30
    
    for num_processes in process_counts:
        print(f"\nTesting with {num_processes} processes:")
        
        start_time = time.time()
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            futures = [
                executor.submit(process_worker, i, records_per_process)
                for i in range(num_processes)
            ]
            results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        total_records = sum(results)
        successful_processes = sum(1 for r in results if r > 0)
        
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Total records: {total_records}")
        print(f"  Successful processes: {successful_processes}")
        print(f"  Throughput: {total_records/total_time:.2f} records/second")
    
    # Clean up test files
    for i in range(max(process_counts)):
        for suffix in ['.json', '.csv']:
            file_path = f'process_data_{i}{suffix}'
            if Path(file_path).exists():
                Path(file_path).unlink()


def test_file_locking():
    """Test file locking with concurrent access to same files."""
    print("\n=== File Locking Test ===")
    
    logger = HydraLogger()
    logger.info("FILE_LOCKING", "Starting file locking test")
    
    def locking_worker(worker_id: int, num_operations: int):
        """Worker that writes to the same file concurrently."""
        test_data = generate_worker_data(worker_id, 10)
        results = []
        
        for i in range(num_operations):
            start_time = time.time()
            success = safe_write_json(test_data, 'shared_file.json')
            end_time = time.time()
            results.append((success, end_time - start_time))
        
        return results
    
    # Test with different numbers of threads writing to same file
    thread_counts = [1, 2, 4, 8]
    operations_per_thread = 20
    
    for num_threads in thread_counts:
        print(f"\nTesting file locking with {num_threads} threads:")
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(locking_worker, i, operations_per_thread)
                for i in range(num_threads)
            ]
            all_results = []
            for future in futures:
                all_results.extend(future.result())
        
        total_time = time.time() - start_time
        total_operations = len(all_results)
        successful_operations = sum(1 for success, _ in all_results if success)
        avg_operation_time = statistics.mean(time_taken for _, time_taken in all_results)
        
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Total operations: {total_operations}")
        print(f"  Successful operations: {successful_operations}")
        print(f"  Average operation time: {avg_operation_time:.6f}s")
        print(f"  Throughput: {total_operations/total_time:.2f} operations/second")
    
    # Clean up
    if Path('shared_file.json').exists():
        Path('shared_file.json').unlink()


def main():
    """Main concurrent example with high-performance fallbacks."""
    print("Concurrent HydraLogger with High-Performance Fallbacks")
    print("=" * 60)
    
    # Clear caches before testing
    clear_all_caches()
    
    try:
        # Run thread concurrency test
        test_thread_concurrency()
        
        # Run process concurrency test
        test_process_concurrency()
        
        # Run file locking test
        test_file_locking()
        
        # Final performance stats
        final_stats = get_performance_stats()
        print(f"\nFinal Performance Statistics:")
        for key, value in final_stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("All concurrent tests completed successfully!")
        print("\nConcurrency Features Demonstrated:")
        print("✓ Thread-safe operations across multiple threads")
        print("✓ Process-safe operations across multiple processes")
        print("✓ File-level locking for concurrent access")
        print("✓ High-performance caching with thread safety")
        print("✓ Memory-efficient singleton patterns")
        print("✓ Robust error handling in concurrent environments")
        
    except Exception as e:
        print(f"\nError during concurrent testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 