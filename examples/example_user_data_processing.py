#!/usr/bin/env python3
"""
User Data Processing with HydraLogger Fallbacks

This example demonstrates how to use the fallbacks module directly
for your own data processing needs, separate from logging operations.

The fallbacks module provides safe, high-performance data handling
for JSON, CSV, and other formats with robust error recovery.
"""

import time
import threading
import os
from pathlib import Path
from typing import List, Dict, Any
import random

from hydra_logger.fallbacks import (
    safe_write_json, safe_write_csv, safe_read_json, safe_read_csv,
    get_performance_stats, clear_all_caches,
    DataSanitizer, CorruptionDetector, AtomicWriter
)


def generate_user_data(num_users: int = 100) -> List[Dict[str, Any]]:
    """Generate realistic user data for processing."""
    users = []
    for i in range(num_users):
        user = {
            'user_id': f"user_{i:06d}",
            'name': f"User {i}",
            'email': f"user{i}@example.com",
            'profile': {
                'age': random.randint(18, 80),
                'location': f"City {i % 10}",
                'preferences': {
                    'theme': random.choice(['light', 'dark']),
                    'notifications': random.choice([True, False]),
                    'language': random.choice(['en', 'es', 'fr', 'de'])
                },
                'metadata': {
                    'created_at': time.time() - random.randint(0, 86400 * 365),
                    'last_login': time.time() - random.randint(0, 86400 * 30),
                    'login_count': random.randint(1, 1000)
                }
            },
            'subscription': {
                'plan': random.choice(['free', 'basic', 'premium', 'enterprise']),
                'status': random.choice(['active', 'inactive', 'suspended']),
                'billing_info': {
                    'method': random.choice(['credit_card', 'paypal', 'bank_transfer']),
                    'next_billing': time.time() + random.randint(86400, 86400 * 30)
                }
            },
            'activity': {
                'posts': random.randint(0, 500),
                'comments': random.randint(0, 2000),
                'likes': random.randint(0, 10000),
                'followers': random.randint(0, 5000)
            }
        }
        users.append(user)
    return users


def process_user_data_safely(users: List[Dict[str, Any]], output_dir: str = "examples/user_data"):
    """Process user data using safe fallback functions."""
    print(f"Processing {len(users)} users with safe data handling...")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # 1. Write user data to JSON with fallback protection
    json_file = f"{output_dir}/users.json"
    json_success = safe_write_json(users, json_file)
    
    if json_success:
        print(f"✓ Successfully wrote {len(users)} users to {json_file}")
    else:
        print(f"✗ Failed to write users to {json_file}")
        return False
    
    # 2. Create CSV export with safe handling
    csv_file = f"{output_dir}/users.csv"
    csv_success = safe_write_csv(users, csv_file)
    
    if csv_success:
        print(f"✓ Successfully wrote {len(users)} users to {csv_file}")
    else:
        print(f"✗ Failed to write users to {csv_file}")
    
    # 3. Read data back to verify integrity
    print("\nVerifying data integrity...")
    
    json_data = safe_read_json(json_file)
    if json_data:
        print(f"✓ Successfully read {len(json_data)} users from JSON")
    else:
        print(f"✗ Failed to read users from JSON")
    
    csv_data = safe_read_csv(csv_file)
    if csv_data:
        print(f"✓ Successfully read {len(csv_data)} users from CSV")
    else:
        print(f"✗ Failed to read users from CSV")
    
    return True


def batch_process_data(users: List[Dict[str, Any]], batch_size: int = 20):
    """Process data in batches with safe handling."""
    print(f"\nProcessing {len(users)} users in batches of {batch_size}...")
    
    batches = [users[i:i + batch_size] for i in range(0, len(users), batch_size)]
    
    for i, batch in enumerate(batches):
        batch_file = f'examples/user_data/batch_{i:03d}.json'
        
        # Safe write with fallback protection
        success = safe_write_json(batch, batch_file)
        
        if success:
            print(f"✓ Batch {i+1}/{len(batches)}: {len(batch)} users written to {batch_file}")
        else:
            print(f"✗ Batch {i+1}/{len(batches)}: Failed to write {batch_file}")
    
    # Read all batches back
    print("\nReading all batches back...")
    all_batches = []
    
    for i in range(len(batches)):
        batch_file = f'examples/user_data/batch_{i:03d}.json'
        batch_data = safe_read_json(batch_file)
        
        if batch_data:
            all_batches.extend(batch_data)
            print(f"✓ Batch {i+1}: Read {len(batch_data)} users")
        else:
            print(f"✗ Batch {i+1}: Failed to read")
    
    print(f"Total users recovered: {len(all_batches)}")


def concurrent_data_processing(users: List[Dict[str, Any]], num_threads: int = 4):
    """Process data concurrently with thread-safe fallbacks."""
    print(f"\nProcessing data with {num_threads} concurrent threads...")
    
    def worker(worker_id: int, user_chunk: List[Dict[str, Any]]):
        """Worker function for concurrent processing."""
        worker_file = f'examples/user_data/worker_{worker_id:02d}.json'
        
        # Safe write with thread-safe fallbacks
        success = safe_write_json(user_chunk, worker_file)
        
        if success:
            print(f"✓ Worker {worker_id}: Wrote {len(user_chunk)} users")
            
            # Read back to verify
            read_data = safe_read_json(worker_file)
            if read_data:
                print(f"✓ Worker {worker_id}: Verified {len(read_data)} users")
            else:
                print(f"✗ Worker {worker_id}: Failed to verify data")
        else:
            print(f"✗ Worker {worker_id}: Failed to write data")
    
    # Split users among threads
    chunk_size = len(users) // num_threads
    threads = []
    
    for i in range(num_threads):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < num_threads - 1 else len(users)
        user_chunk = users[start_idx:end_idx]
        
        thread = threading.Thread(target=worker, args=(i, user_chunk))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("All concurrent processing completed!")


def data_recovery_demo():
    """Demonstrate data recovery capabilities."""
    print("\n=== Data Recovery Demo ===")
    
    # Create some test data
    test_data = [
        {'id': 1, 'name': 'Alice', 'data': {'nested': 'value', 'bytes': b'binary_data'}},
        {'id': 2, 'name': 'Bob', 'data': {'set': {1, 2, 3}, 'complex': 1 + 2j}}
    ]
    
    # Write data safely
    safe_write_json(test_data, 'examples/user_data/recovery_test.json')
    print("✓ Wrote test data with fallback protection")
    
    # Simulate corruption
    with open('examples/user_data/recovery_test.json', 'a') as f:
        f.write('\n{"corrupted": json}\n')
    
    print("✓ Simulated file corruption")
    
    # Try to read corrupted data
    recovered_data = safe_read_json('examples/user_data/recovery_test.json')
    
    if recovered_data:
        print(f"✓ Successfully recovered {len(recovered_data)} records from corrupted file")
        print("  Data recovery worked!")
    else:
        print("✗ Failed to recover data from corrupted file")
    
    # Check if corruption was detected
    is_corrupted = CorruptionDetector.detect_corruption('examples/user_data/recovery_test.json', 'json')
    if is_corrupted:
        print("✓ Corruption detection worked!")


def performance_analysis():
    """Analyze performance of fallback operations."""
    print("\n=== Performance Analysis ===")
    
    # Get performance statistics
    stats = get_performance_stats()
    
    print("Current Performance Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test write performance
    test_data = generate_user_data(50)
    
    start_time = time.time()
    success = safe_write_json(test_data, 'examples/user_data/performance_test.json')
    write_time = time.time() - start_time
    
    if success:
        print(f"\nWrite Performance:")
        print(f"  Records: {len(test_data)}")
        print(f"  Time: {write_time:.4f}s")
        print(f"  Throughput: {len(test_data)/write_time:.2f} records/second")
    
    # Test read performance
    start_time = time.time()
    read_data = safe_read_json('examples/user_data/performance_test.json')
    read_time = time.time() - start_time
    
    if read_data:
        print(f"\nRead Performance:")
        print(f"  Records: {len(read_data)}")
        print(f"  Time: {read_time:.4f}s")
        print(f"  Throughput: {len(read_data)/read_time:.2f} records/second")


def main():
    """Main example demonstrating user data processing with fallbacks."""
    print("User Data Processing with HydraLogger Fallbacks")
    print("=" * 60)
    
    # Clear caches for clean start
    clear_all_caches()
    
    # Create necessary directories
    os.makedirs("examples/user_data", exist_ok=True)
    
    # Generate realistic user data
    print("Generating realistic user data...")
    users = generate_user_data(100)
    print(f"Generated {len(users)} users with complex data structures")
    
    # 1. Basic safe data processing
    print("\n" + "="*60)
    print("1. Basic Safe Data Processing")
    print("="*60)
    process_user_data_safely(users)
    
    # 2. Batch processing
    print("\n" + "="*60)
    print("2. Batch Processing")
    print("="*60)
    batch_process_data(users, batch_size=25)
    
    # 3. Concurrent processing
    print("\n" + "="*60)
    print("3. Concurrent Processing")
    print("="*60)
    concurrent_data_processing(users, num_threads=4)
    
    # 4. Data recovery demo
    print("\n" + "="*60)
    print("4. Data Recovery Demo")
    print("="*60)
    data_recovery_demo()
    
    # 5. Performance analysis
    print("\n" + "="*60)
    print("5. Performance Analysis")
    print("="*60)
    performance_analysis()
    
    # Final statistics
    final_stats = get_performance_stats()
    print(f"\nFinal Performance Statistics:")
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("User Data Processing Example Completed!")
    print("\nKey Benefits Demonstrated:")
    print("✓ Safe data writing with atomic operations")
    print("✓ Robust data reading with corruption detection")
    print("✓ Thread-safe concurrent processing")
    print("✓ High-performance caching and optimization")
    print("✓ Automatic data recovery from corrupted files")
    print("✓ Memory-efficient operations")
    
    print(f"\nOutput files created in: examples/user_data/")
    print("Check the directory to see the processed data files!")


if __name__ == "__main__":
    main() 