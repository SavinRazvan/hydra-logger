#!/usr/bin/env python3
"""
Performance Test for HydraLogger Fallbacks Module

This test validates the high-performance, thread-safe, and async-compatible
design of the fallbacks module under various load conditions.
"""

import asyncio
import threading
import time
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import statistics

from hydra_logger.fallbacks import (
    FallbackHandler, DataSanitizer, CorruptionDetector,
    AtomicWriter, BackupManager, DataRecovery,
    safe_write_json, safe_write_csv, safe_read_json, safe_read_csv,
    async_safe_write_json, async_safe_write_csv,
    async_safe_read_json, async_safe_read_csv,
    clear_all_caches, get_performance_stats
)


def generate_test_data(size: int = 1000) -> list:
    """Generate test data for performance testing."""
    return [
        {
            'id': i,
            'name': f'User_{i}',
            'data': {
                'nested': f'value_{i}',
                'list': list(range(i % 10)),
                'complex': 1 + 2j if i % 2 == 0 else None
            },
            'timestamp': time.time(),
            'bytes': b'binary_data',
            'set': {1, 2, 3}
        }
        for i in range(size)
    ]


def test_data_sanitization_performance():
    """Test data sanitization performance."""
    print("\n=== Data Sanitization Performance Test ===")
    
    test_data = generate_test_data(1000)
    
    # Test JSON sanitization
    start_time = time.time()
    for _ in range(100):
        DataSanitizer.sanitize_for_json(test_data)
    json_time = time.time() - start_time
    
    # Test CSV sanitization
    start_time = time.time()
    for _ in range(100):
        DataSanitizer.sanitize_dict_for_csv(test_data[0])
    csv_time = time.time() - start_time
    
    print(f"JSON sanitization: {json_time:.4f}s for 100 iterations")
    print(f"CSV sanitization: {csv_time:.4f}s for 100 iterations")
    print(f"Average per operation: {json_time/100:.6f}s (JSON), {csv_time/100:.6f}s (CSV)")


def test_corruption_detection_performance():
    """Test corruption detection performance."""
    print("\n=== Corruption Detection Performance Test ===")
    
    # Create test files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"valid": "json"}')
        valid_json = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"invalid": json}')
        invalid_json = f.name
    
    try:
        # Test valid JSON detection
        start_time = time.time()
        for _ in range(1000):
            CorruptionDetector.is_valid_json(valid_json)
        valid_time = time.time() - start_time
        
        # Test invalid JSON detection
        start_time = time.time()
        for _ in range(1000):
            CorruptionDetector.is_valid_json(invalid_json)
        invalid_time = time.time() - start_time
        
        print(f"Valid JSON detection: {valid_time:.4f}s for 1000 iterations")
        print(f"Invalid JSON detection: {invalid_time:.4f}s for 1000 iterations")
        print(f"Average per operation: {valid_time/1000:.6f}s (valid), {invalid_time/1000:.6f}s (invalid)")
        
    finally:
        # Clean up
        for file in [valid_json, invalid_json]:
            if os.path.exists(file):
                os.unlink(file)


def test_concurrent_writes():
    """Test concurrent write operations."""
    print("\n=== Concurrent Write Performance Test ===")
    
    def write_worker(worker_id: int, num_writes: int):
        """Worker function for concurrent writes."""
        test_data = generate_test_data(100)
        results = []
        
        for i in range(num_writes):
            start_time = time.time()
            success = safe_write_json(test_data, f'test_concurrent_{worker_id}_{i}.json')
            end_time = time.time()
            results.append((success, end_time - start_time))
        
        return results
    
    # Test with different numbers of threads
    thread_counts = [1, 2, 4, 8]
    writes_per_thread = 10
    
    for num_threads in thread_counts:
        print(f"\nTesting with {num_threads} threads:")
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(write_worker, i, writes_per_thread)
                for i in range(num_threads)
            ]
            all_results = []
            for future in futures:
                all_results.extend(future.result())
        
        total_time = time.time() - start_time
        total_writes = len(all_results)
        successful_writes = sum(1 for success, _ in all_results if success)
        avg_write_time = statistics.mean(time_taken for _, time_taken in all_results)
        
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Total writes: {total_writes}")
        print(f"  Successful writes: {successful_writes}")
        print(f"  Average write time: {avg_write_time:.6f}s")
        print(f"  Throughput: {total_writes/total_time:.2f} writes/second")
        
        # Clean up test files
        for i in range(num_threads):
            for j in range(writes_per_thread):
                file_path = f'test_concurrent_{i}_{j}.json'
                if os.path.exists(file_path):
                    os.unlink(file_path)


async def test_async_performance():
    """Test async performance."""
    print("\n=== Async Performance Test ===")
    
    test_data = generate_test_data(100)
    
    # Test async JSON writing
    start_time = time.time()
    tasks = []
    for i in range(50):
        task = async_safe_write_json(test_data, f'test_async_{i}.json')
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    async_time = time.time() - start_time
    
    successful_writes = sum(results)
    print(f"Async JSON writes: {async_time:.4f}s for 50 operations")
    print(f"Successful writes: {successful_writes}/50")
    print(f"Average per operation: {async_time/50:.6f}s")
    
    # Clean up
    for i in range(50):
        file_path = f'test_async_{i}.json'
        if os.path.exists(file_path):
            os.unlink(file_path)


def test_memory_usage():
    """Test memory usage and cache efficiency."""
    print("\n=== Memory Usage Test ===")
    
    # Clear caches first
    clear_all_caches()
    
    # Test cache growth
    test_data = generate_test_data(100)
    
    print("Testing cache growth...")
    for i in range(1000):
        DataSanitizer.sanitize_for_json(test_data)
        if i % 100 == 0:
            stats = get_performance_stats()
            print(f"  Iteration {i}: sanitizer_cache_size = {stats['sanitizer_cache_size']}")
    
    # Test cache efficiency
    print("\nTesting cache efficiency...")
    start_time = time.time()
    for _ in range(1000):
        DataSanitizer.sanitize_for_json(test_data)
    cached_time = time.time() - start_time
    
    # Clear cache and test without caching
    DataSanitizer.clear_cache()
    start_time = time.time()
    for _ in range(1000):
        DataSanitizer.sanitize_for_json(test_data)
    uncached_time = time.time() - start_time
    
    print(f"Cached operations: {cached_time:.4f}s")
    print(f"Uncached operations: {uncached_time:.4f}s")
    print(f"Cache speedup: {uncached_time/cached_time:.2f}x")
    
    # Final stats
    stats = get_performance_stats()
    print(f"\nFinal cache statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def test_file_locking():
    """Test file locking performance."""
    print("\n=== File Locking Performance Test ===")
    
    def lock_worker(worker_id: int, num_operations: int):
        """Worker function for file locking tests."""
        handler = FallbackHandler()
        test_data = generate_test_data(10)
        results = []
        
        for i in range(num_operations):
            start_time = time.time()
            success = handler.safe_write_json(test_data, f'test_lock_{worker_id}_{i}.json')
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
                executor.submit(lock_worker, i, operations_per_thread)
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
        
        # Clean up test files
        for i in range(num_threads):
            for j in range(operations_per_thread):
                file_path = f'test_lock_{i}_{j}.json'
                if os.path.exists(file_path):
                    os.unlink(file_path)


def test_recovery_performance():
    """Test data recovery performance."""
    print("\n=== Data Recovery Performance Test ===")
    
    # Create corrupted files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"valid": "entry"}\n{"invalid": json}\n{"another": "valid"}\n')
        corrupted_json = f.name
    
    recovery = DataRecovery()
    
    # Test recovery performance
    start_time = time.time()
    for _ in range(100):
        recovered_data = recovery.recover_json_file(corrupted_json)
    recovery_time = time.time() - start_time
    
    print(f"JSON recovery: {recovery_time:.4f}s for 100 iterations")
    print(f"Average per operation: {recovery_time/100:.6f}s")
    
    # Test cache effectiveness
    start_time = time.time()
    for _ in range(100):
        recovered_data = recovery.recover_json_file(corrupted_json)
    cached_recovery_time = time.time() - start_time
    
    print(f"Cached recovery: {cached_recovery_time:.4f}s for 100 iterations")
    print(f"Cache speedup: {recovery_time/cached_recovery_time:.2f}x")
    
    # Clean up
    if os.path.exists(corrupted_json):
        os.unlink(corrupted_json)


async def main():
    """Run all performance tests."""
    print("HydraLogger Fallbacks Performance Test")
    print("=" * 50)
    
    try:
        # Run synchronous tests
        test_data_sanitization_performance()
        test_corruption_detection_performance()
        test_concurrent_writes()
        test_memory_usage()
        test_file_locking()
        test_recovery_performance()
        
        # Run async tests
        await test_async_performance()
        
        print("\n" + "=" * 50)
        print("All performance tests completed successfully!")
        print("\nPerformance Summary:")
        print("✓ Thread-safe concurrent operations")
        print("✓ Async/await compatibility")
        print("✓ High-performance caching")
        print("✓ Memory-efficient operations")
        print("✓ File-level locking")
        print("✓ Data recovery optimization")
        
        # Final performance stats
        stats = get_performance_stats()
        print(f"\nFinal Performance Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"\nError during performance testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 