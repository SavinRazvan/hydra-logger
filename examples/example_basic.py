#!/usr/bin/env python3
"""
Basic HydraLogger Example with High-Performance Fallbacks

This example demonstrates basic usage of HydraLogger with the new
high-performance fallbacks module for robust data handling.
"""

import os
from hydra_logger import HydraLogger, LoggingConfig, LogLayer, LogDestination
from hydra_logger.fallbacks import (
    safe_write_json, safe_write_csv, safe_read_json, safe_read_csv,
    get_performance_stats, clear_all_caches
)


def main():
    """Basic example with high-performance fallbacks."""
    print("Basic HydraLogger with High-Performance Fallbacks")
    print("=" * 50)
    
    # Clear caches for clean start
    clear_all_caches()
    
    # Create necessary directories
    os.makedirs("examples/logs/basic", exist_ok=True)
    os.makedirs("examples/output", exist_ok=True)
    
    # Simple configuration with fallback support
    config = LoggingConfig(
        layers={
            "BASIC": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/basic/app.log",
                        format="json"  # Uses JSONArrayHandler with fallbacks
                    ),
                    LogDestination(
                        type="console",
                        format="text"
                    )
                ]
            ),
            "DATA": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="examples/logs/basic/data.csv",
                        format="csv"  # Uses CSVHandler with fallbacks
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(config)
    
    # Basic logging
    logger.info("BASIC", "Application started with fallback support")
    logger.info("BASIC", "This message will be logged with robust data handling")
    
    # Demonstrate fallback data handling
    test_data = [
        {
            'id': 1,
            'name': 'Alice',
            'data': {
                'nested': 'value',
                'list': [1, 2, 3],
                'bytes': b'binary_data',
                'complex': 1 + 2j
            }
        },
        {
            'id': 2,
            'name': 'Bob',
            'data': {
                'nested': 'another_value',
                'set': {1, 2, 3},
                'none': None
            }
        }
    ]
    
    # Log data processing
    logger.info("DATA", f"Processing {len(test_data)} records with fallback support")
    
    # Use fallback functions for robust data handling
    json_success = safe_write_json(test_data, 'examples/output/data.json')
    csv_success = safe_write_csv(test_data, 'examples/output/data.csv')
    
    if json_success:
        logger.info("DATA", "JSON data written successfully with fallback protection")
    else:
        logger.error("DATA", "JSON write failed, fallback mechanisms activated")
    
    if csv_success:
        logger.info("DATA", "CSV data written successfully with fallback protection")
    else:
        logger.error("DATA", "CSV write failed, fallback mechanisms activated")
    
    # Read data back using fallbacks
    json_data = safe_read_json('examples/output/data.json')
    csv_data = safe_read_csv('examples/output/data.csv')
    
    if json_data:
        logger.info("DATA", f"Successfully read {len(json_data)} JSON records")
    
    if csv_data:
        logger.info("DATA", f"Successfully read {len(csv_data)} CSV records")
    
    # Show performance statistics
    stats = get_performance_stats()
    logger.info("BASIC", f"Performance stats: {stats}")
    
    # Demonstrate error handling
    logger.warning("BASIC", "This is a warning message")
    logger.error("BASIC", "This is an error message")
    
    print("\nBasic example completed!")
    print("Check the examples/logs directory for output files")
    print("Performance statistics:", stats)


if __name__ == "__main__":
    main() 