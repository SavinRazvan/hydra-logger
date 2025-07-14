#!/usr/bin/env python3
"""
CSV Format Example

This example demonstrates logging in CSV format with proper CSV output.
CSV logs are useful for data analysis and spreadsheet integration.
"""

import os
from hydra_logger import HydraLogger

def demo_csv_format():
    """Demonstrate CSV format logging."""
    
    print("CSV Format Example")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Configuration with CSV format
    config = {
        "layers": {
            "ANALYTICS": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/analytics.csv",
                        "format": "csv",
                        "level": "INFO"
                    }
                ]
            },
            "METRICS": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/performance_metrics.csv",
                        "format": "csv",
                        "level": "INFO"
                    }
                ]
            }
        }
    }
    
    # Create logger with CSV format
    logger = HydraLogger(config=config)
    
    # Log analytics data
    logger.info("User registration", "ANALYTICS", extra={"user_id": 1001, "source": "web", "country": "US"})
    logger.info("Page view", "ANALYTICS", extra={"page": "/home", "duration": 45, "user_id": 1001})
    logger.info("Purchase completed", "ANALYTICS", extra={"order_id": "ORD-123", "amount": 99.99, "currency": "USD"})
    logger.info("Search query", "ANALYTICS", extra={"query": "python logging", "results": 150, "user_id": 1002})
    
    # Log performance metrics
    logger.info("CPU usage", "METRICS", extra={"cpu_percent": 45.2, "memory_percent": 67.8, "timestamp": "2025-07-14T06:15:00"})
    logger.info("Database query", "METRICS", extra={"query_time": 0.125, "rows_returned": 1000, "table": "users"})
    logger.info("API response", "METRICS", extra={"endpoint": "/api/users", "response_time": 0.089, "status_code": 200})
    logger.info("Cache hit", "METRICS", extra={"cache_type": "redis", "hit_rate": 0.92, "keys": 15000})
    
    print("\nCSV format example completed!")
    print("Check the following files:")
    print("   - examples/logs/analytics.csv (Analytics data)")
    print("   - examples/logs/performance_metrics.csv (Performance metrics)")

if __name__ == "__main__":
    demo_csv_format() 