#!/usr/bin/env python3
"""
Advanced HydraLogger Example with High-Performance Fallbacks

This example demonstrates advanced usage patterns including:
- Multiple layers with different formats
- Performance monitoring
- Error recovery scenarios
- Complex data processing with fallbacks
"""

import time
import threading
import os
from pathlib import Path
from hydra_logger import HydraLogger, LoggingConfig, LogLayer, LogDestination
from hydra_logger.fallbacks import (
    FallbackHandler, DataSanitizer, CorruptionDetector,
    safe_write_json, safe_write_csv, safe_read_json, safe_read_csv,
    get_performance_stats, clear_all_caches
)


def generate_complex_data(size: int = 100) -> list:
    """Generate complex test data with various data types."""
    return [
        {
            'id': i,
            'name': f'User_{i}',
            'email': f'user{i}@example.com',
            'data': {
                'nested': {
                    'deep': f'value_{i}',
                    'list': list(range(i % 10)),
                    'dict': {f'key_{j}': f'value_{j}' for j in range(i % 5)}
                },
                'bytes': b'binary_data',
                'complex': 1 + 2j if i % 2 == 0 else None,
                'set': {1, 2, 3, i},
                'tuple': (1, 2, 3, i),
                'boolean': i % 2 == 0,
                'float': 3.14159 * i,
                'none': None
            },
            'metadata': {
                'created_at': time.time(),
                'version': '1.0.0',
                'tags': ['tag1', 'tag2', f'tag{i}']
            }
        }
        for i in range(size)
    ]


def performance_monitor(logger: HydraLogger, stop_event: threading.Event):
    """Monitor performance statistics."""
    while not stop_event.is_set():
        stats = get_performance_stats()
        logger.info("PERFORMANCE", f"Cache stats: {stats}")
        time.sleep(10)  # Monitor every 10 seconds


def data_processor(worker_id: int, data: list, logger: HydraLogger):
    """Process data with fallback protection."""
    try:
        # Log processing start
        logger.info("DATA_PROCESSOR", f"Worker {worker_id} processing {len(data)} records")
        
        # Write to multiple formats with fallbacks
        json_file = f'examples/output/processed_data_{worker_id}.json'
        csv_file = f'examples/output/processed_data_{worker_id}.csv'
        
        # Use fallback functions for robust writing
        json_success = safe_write_json(data, json_file)
        csv_success = safe_write_csv(data, csv_file)
        
        if json_success and csv_success:
            logger.info("DATA_PROCESSOR", f"Worker {worker_id} wrote data successfully")
        else:
            logger.error("DATA_PROCESSOR", f"Worker {worker_id} had write failures")
        
        # Read data back to verify
        json_data = safe_read_json(json_file)
        csv_data = safe_read_csv(csv_file)
        
        if json_data:
            logger.info("DATA_PROCESSOR", f"Worker {worker_id} verified {len(json_data)} JSON records")
        
        if csv_data:
            logger.info("DATA_PROCESSOR", f"Worker {worker_id} verified {len(csv_data)} CSV records")
        
        return len(data)
        
    except Exception as e:
        logger.error("DATA_PROCESSOR", f"Worker {worker_id} failed: {e}")
        return 0


def error_recovery_test(logger: HydraLogger):
    """Test error recovery scenarios."""
    logger.info("ERROR_RECOVERY", "Starting error recovery tests")
    
    # Test with problematic data
    problematic_data = [
        {
            'id': 1,
            'data': {
                'nested': 'value',
                'bytes': b'binary_data',
                'complex': 1 + 2j,
                'set': {1, 2, 3},
                'custom_object': type('TestClass', (), {'attr': 'value'})()
            }
        }
    ]
    
    # This should handle problematic data gracefully
    success = safe_write_json(problematic_data, 'examples/output/test_problematic.json')
    if success:
        logger.info("ERROR_RECOVERY", "Successfully handled problematic data")
        
        # Read it back
        recovered_data = safe_read_json('examples/output/test_problematic.json')
        if recovered_data:
            logger.info("ERROR_RECOVERY", "Successfully recovered problematic data")
    
    # Test corruption detection
    test_file = 'examples/output/test_corruption.json'
    with open(test_file, 'w') as f:
        f.write('{"valid": "json"}\n{"invalid": json}\n{"another": "valid"}')
    
    # Check if corruption is detected
    is_corrupted = CorruptionDetector.detect_corruption(test_file, 'json')
    if is_corrupted:
        logger.warning("ERROR_RECOVERY", "Corruption detected in test file")
        
        # Try to recover data
        recovered_data = safe_read_json(test_file)
        if recovered_data:
            logger.info("ERROR_RECOVERY", f"Recovered {len(recovered_data)} records from corrupted file")
    
    # Clean up test files
    for file in ['examples/output/test_problematic.json', 'examples/output/test_corruption.json']:
        if Path(file).exists():
            Path(file).unlink()


def main():
    """Advanced example with high-performance fallbacks."""
    print("Advanced HydraLogger with High-Performance Fallbacks")
    print("=" * 60)
    
    # Clear caches for clean start
    clear_all_caches()
    
    # Create necessary directories
    os.makedirs("examples/logs/advanced", exist_ok=True)
    os.makedirs("examples/output", exist_ok=True)
    
    # Advanced configuration with multiple layers
    config = LoggingConfig(
        layers={
            "APPLICATION": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/advanced/app.log",
                        format="json"
                    ),
                    LogDestination(
                        type="console",
                        format="text"
                    )
                ]
            ),
            "DATA_PROCESSOR": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/advanced/processor.log",
                        format="json"
                    )
                ]
            ),
            "ERROR_RECOVERY": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/advanced/errors.log",
                        format="json"
                    ),
                    LogDestination(
                        type="console",
                        format="text"
                    )
                ]
            ),
            "PERFORMANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/advanced/performance.log",
                        format="json"
                    )
                ]
            ),
            "ANALYTICS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/advanced/analytics.csv",
                        format="csv"
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(config)
    logger.info("APPLICATION", "Starting advanced example with fallback support")
    
    # Start performance monitoring
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=performance_monitor,
        args=(logger, stop_event)
    )
    monitor_thread.start()
    
    # Generate complex test data
    complex_data = generate_complex_data(50)
    logger.info("APPLICATION", f"Generated {len(complex_data)} complex records")
    
    # Process data with multiple workers
    workers = []
    for worker_id in range(3):
        worker_data = complex_data[worker_id * 16:(worker_id + 1) * 16]
        worker_thread = threading.Thread(
            target=data_processor,
            args=(worker_id, worker_data, logger)
        )
        workers.append(worker_thread)
        worker_thread.start()
    
    # Wait for all workers to complete
    for worker in workers:
        worker.join()
    
    # Test error recovery scenarios
    error_recovery_test(logger)
    
    # Write analytics data
    analytics_data = [
        {
            'timestamp': time.time(),
            'total_records': len(complex_data),
            'workers': 3,
            'cache_hits': get_performance_stats()['sanitizer_cache_size'],
            'status': 'completed'
        }
    ]
    
    csv_success = safe_write_csv(analytics_data, 'examples/logs/advanced/analytics.csv')
    if csv_success:
        logger.info("ANALYTICS", "Analytics data written successfully")
    
    # Stop performance monitoring
    stop_event.set()
    monitor_thread.join()
    
    # Final performance statistics
    final_stats = get_performance_stats()
    logger.info("PERFORMANCE", f"Final performance stats: {final_stats}")
    
    print("\nAdvanced example completed!")
    print("Check the examples/logs directory for output files")
    print("Final performance statistics:", final_stats)
    
    # Clean up processed data files
    for i in range(3):
        for suffix in ['.json', '.csv']:
            file_path = f'examples/output/processed_data_{i}{suffix}'
            if Path(file_path).exists():
                Path(file_path).unlink()


if __name__ == "__main__":
    main() 