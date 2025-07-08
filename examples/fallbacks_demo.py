#!/usr/bin/env python3
"""
Fallbacks Module Demo

This example demonstrates the robust fallback mechanisms for data processing
formats like JSON, CSV, and other structured data formats. It shows:

1. Data sanitization for safe storage
2. Corruption detection and recovery
3. Atomic write operations
4. Backup management
5. Error handling and fallback strategies

The fallbacks module provides:
- DataSanitizer: Sanitizes data for various formats
- CorruptionDetector: Detects and validates file integrity
- AtomicWriter: Provides atomic write operations
- BackupManager: Manages backup files for recovery
- DataRecovery: Recovers data from corrupted files
- FallbackHandler: Main handler coordinating all mechanisms
"""

import os
import tempfile
import json
import csv
from pathlib import Path
from hydra_logger.fallbacks import (
    FallbackHandler, DataSanitizer, CorruptionDetector,
    AtomicWriter, BackupManager, DataRecovery,
    safe_write_json, safe_write_csv, safe_read_json, safe_read_csv
)


def demo_data_sanitization():
    """Demonstrate data sanitization capabilities."""
    print("\n=== Data Sanitization Demo ===")
    
    # Test data with various types
    test_data = {
        'string': 'Hello, World!',
        'number': 42,
        'float': 3.14,
        'boolean': True,
        'none': None,
        'list': [1, 2, 3],
        'dict': {'nested': 'value'},
        'complex_object': type('TestClass', (), {'attr': 'value'})(),
        'bytes': b'binary data',
        'set': {1, 2, 3}
    }
    
    print("Original data:")
    print(json.dumps(test_data, default=str, indent=2))
    
    # Sanitize for JSON
    sanitized_json = DataSanitizer.sanitize_for_json(test_data)
    print("\nSanitized for JSON:")
    print(json.dumps(sanitized_json, indent=2))
    
    # Sanitize for CSV
    sanitized_csv = DataSanitizer.sanitize_dict_for_csv(test_data)
    print("\nSanitized for CSV:")
    for key, value in sanitized_csv.items():
        print(f"  {key}: {value}")


def demo_corruption_detection():
    """Demonstrate corruption detection capabilities."""
    print("\n=== Corruption Detection Demo ===")
    
    # Create temporary files for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"valid": "json"}')
        valid_json_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"invalid": json}')  # Invalid JSON
        invalid_json_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('name,age\nJohn,30\nJane,25')
        valid_csv_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('name,age\nJohn,30\nJane,25,extra')  # Invalid CSV
        invalid_csv_file = f.name
    
    try:
        # Test JSON corruption detection
        print(f"Valid JSON file: {CorruptionDetector.is_valid_json(valid_json_file)}")
        print(f"Invalid JSON file: {CorruptionDetector.is_valid_json(invalid_json_file)}")
        
        # Test CSV corruption detection
        print(f"Valid CSV file: {CorruptionDetector.is_valid_csv(valid_csv_file)}")
        print(f"Invalid CSV file: {CorruptionDetector.is_valid_csv(invalid_csv_file)}")
        
        # Test general corruption detection
        print(f"JSON corruption detected: {CorruptionDetector.detect_corruption(invalid_json_file, 'json')}")
        print(f"CSV corruption detected: {CorruptionDetector.detect_corruption(invalid_csv_file, 'csv')}")
        
    finally:
        # Clean up temporary files
        for file in [valid_json_file, invalid_json_file, valid_csv_file, invalid_csv_file]:
            if os.path.exists(file):
                os.unlink(file)


def demo_atomic_writes():
    """Demonstrate atomic write operations."""
    print("\n=== Atomic Write Demo ===")
    
    test_data = [
        {'id': 1, 'name': 'Alice', 'age': 30},
        {'id': 2, 'name': 'Bob', 'age': 25},
        {'id': 3, 'name': 'Charlie', 'age': 35}
    ]
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        # Test atomic JSON write
        success = AtomicWriter.write_json_atomic(test_data, temp_file)
        print(f"Atomic JSON write successful: {success}")
        
        # Verify the file was written correctly
        with open(temp_file, 'r') as f:
            loaded_data = json.load(f)
        print(f"Data integrity verified: {loaded_data == test_data}")
        
        # Test atomic CSV write
        csv_file = temp_file.replace('.json', '.csv')
        success = AtomicWriter.write_csv_atomic(test_data, csv_file)
        print(f"Atomic CSV write successful: {success}")
        
        # Verify CSV file
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
        print(f"CSV data integrity verified: {len(csv_data) == len(test_data)}")
        
    finally:
        # Clean up
        for file in [temp_file, csv_file]:
            if os.path.exists(file):
                os.unlink(file)


def demo_backup_management():
    """Demonstrate backup management capabilities."""
    print("\n=== Backup Management Demo ===")
    
    # Create a temporary directory for backups
    with tempfile.TemporaryDirectory() as temp_dir:
        backup_manager = BackupManager(backup_dir=temp_dir)
        
        # Create a test file
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # Create backup
        backup_path = backup_manager.create_backup(test_file)
        print(f"Backup created: {backup_path}")
        print(f"Backup exists: {os.path.exists(backup_path)}")
        
        # Corrupt the original file
        with open(test_file, 'w') as f:
            f.write('corrupted content')
        
        # Restore from backup
        success = backup_manager.restore_from_backup(test_file, backup_path)
        print(f"Restore successful: {success}")
        
        # Verify restoration
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"Restored content: {content}")


def demo_data_recovery():
    """Demonstrate data recovery capabilities."""
    print("\n=== Data Recovery Demo ===")
    
    recovery = DataRecovery()
    
    # Create a corrupted JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write('{"valid": "entry"}\n{"invalid": json}\n{"another": "valid"}\n')
        corrupted_json_file = f.name
    
    # Create a corrupted CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('name,age\nJohn,30\nJane,25,extra\nBob,35')
        corrupted_csv_file = f.name
    
    try:
        # Try to recover JSON data
        recovered_json = recovery.recover_json_file(corrupted_json_file)
        print(f"Recovered JSON entries: {len(recovered_json) if recovered_json else 0}")
        if recovered_json:
            print("Recovered JSON data:")
            for entry in recovered_json:
                print(f"  {entry}")
        
        # Try to recover CSV data
        recovered_csv = recovery.recover_csv_file(corrupted_csv_file)
        print(f"Recovered CSV entries: {len(recovered_csv) if recovered_csv else 0}")
        if recovered_csv:
            print("Recovered CSV data:")
            for entry in recovered_csv:
                print(f"  {entry}")
                
    finally:
        # Clean up
        for file in [corrupted_json_file, corrupted_csv_file]:
            if os.path.exists(file):
                os.unlink(file)


def demo_fallback_handler():
    """Demonstrate the main FallbackHandler capabilities."""
    print("\n=== Fallback Handler Demo ===")
    
    handler = FallbackHandler()
    
    # Test data
    test_records = [
        {'id': 1, 'name': 'Alice', 'data': {'nested': 'value'}},
        {'id': 2, 'name': 'Bob', 'data': [1, 2, 3]},
        {'id': 3, 'name': 'Charlie', 'data': None}
    ]
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        json_file = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        csv_file = f.name
    
    try:
        # Test safe JSON writing
        success = handler.safe_write_json(test_records, json_file)
        print(f"Safe JSON write successful: {success}")
        
        # Test safe CSV writing
        success = handler.safe_write_csv(test_records, csv_file)
        print(f"Safe CSV write successful: {success}")
        
        # Test safe reading
        loaded_json = handler.safe_read_json(json_file)
        print(f"JSON read successful: {loaded_json is not None}")
        
        loaded_csv = handler.safe_read_csv(csv_file)
        print(f"CSV read successful: {loaded_csv is not None}")
        
        # Verify data integrity
        print(f"JSON data integrity: {loaded_json == test_records}")
        print(f"CSV data integrity: {len(loaded_csv) == len(test_records) if loaded_csv else False}")
        
    finally:
        # Clean up
        for file in [json_file, csv_file]:
            if os.path.exists(file):
                os.unlink(file)


def demo_convenience_functions():
    """Demonstrate the convenience functions."""
    print("\n=== Convenience Functions Demo ===")
    
    test_data = [
        {'id': 1, 'name': 'Alice', 'score': 95.5},
        {'id': 2, 'name': 'Bob', 'score': 87.2},
        {'id': 3, 'name': 'Charlie', 'score': 92.8}
    ]
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        json_file = f.name
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        csv_file = f.name
    
    try:
        # Test convenience functions
        success = safe_write_json(test_data, json_file)
        print(f"Convenience JSON write: {success}")
        
        success = safe_write_csv(test_data, csv_file)
        print(f"Convenience CSV write: {success}")
        
        loaded_json = safe_read_json(json_file)
        loaded_csv = safe_read_csv(csv_file)
        
        print(f"Convenience JSON read: {loaded_json is not None}")
        print(f"Convenience CSV read: {loaded_csv is not None}")
        
    finally:
        # Clean up
        for file in [json_file, csv_file]:
            if os.path.exists(file):
                os.unlink(file)


def demo_error_scenarios():
    """Demonstrate error handling and fallback scenarios."""
    print("\n=== Error Scenarios Demo ===")
    
    handler = FallbackHandler()
    
    # Test with problematic data
    problematic_data = [
        {'id': 1, 'name': 'Alice', 'data': {'nested': 'value'}},
        {'id': 2, 'name': 'Bob', 'data': type('TestClass', (), {'attr': 'value'})(), 'bytes': b'binary'},
        {'id': 3, 'name': 'Charlie', 'data': {1, 2, 3}, 'complex': 1+2j}
    ]
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        json_file = f.name
    
    try:
        # This should handle problematic data gracefully
        success = handler.safe_write_json(problematic_data, json_file)
        print(f"Problematic data write successful: {success}")
        
        # Read it back
        loaded_data = handler.safe_read_json(json_file)
        print(f"Problematic data read successful: {loaded_data is not None}")
        
        if loaded_data:
            print("Data was sanitized and preserved:")
            for item in loaded_data:
                print(f"  {item}")
                
    finally:
        # Clean up
        if os.path.exists(json_file):
            os.unlink(json_file)


def main():
    """Run all fallback demonstrations."""
    print("HydraLogger Fallbacks Module Demo")
    print("=" * 50)
    
    try:
        demo_data_sanitization()
        demo_corruption_detection()
        demo_atomic_writes()
        demo_backup_management()
        demo_data_recovery()
        demo_fallback_handler()
        demo_convenience_functions()
        demo_error_scenarios()
        
        print("\n" + "=" * 50)
        print("All fallback demonstrations completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✓ Data sanitization for safe storage")
        print("✓ Corruption detection and validation")
        print("✓ Atomic write operations")
        print("✓ Backup management and recovery")
        print("✓ Error handling and fallback strategies")
        print("✓ Convenience functions for easy usage")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 