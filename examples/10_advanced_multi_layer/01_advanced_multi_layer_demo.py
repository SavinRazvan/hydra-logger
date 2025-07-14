#!/usr/bin/env python3
"""
Advanced Multi-Layer Logging Example

This example demonstrates advanced multi-layer logging scenarios:
- Multiple layers with different formats (JSON, CSV, Plain-text, Syslog)
- Multiple layers writing to the same file
- Multiple layers writing to different files
- Console output with colors
- Structured logging with extra data
- Different log levels for different layers
"""

import os
import time
import random
from datetime import datetime
from hydra_logger import HydraLogger

def create_advanced_config():
    """Create an advanced configuration with multiple layers and formats."""
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs/advanced", exist_ok=True)
    
    return {
        "layers": {
            # FRONTEND: Console + JSON file + CSV file
            "FRONTEND": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "console",
                        "format": "plain-text",
                        "level": "INFO",
                        "color_mode": "always"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/frontend.json",
                        "format": "json",
                        "level": "DEBUG"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/frontend.csv",
                        "format": "csv",
                        "level": "INFO"
                    }
                ]
            },
            
            # BACKEND: Console + Plain text file + Same combined file
            "BACKEND": {
                "level": "DEBUG",
                "destinations": [
                    {
                        "type": "console",
                        "format": "plain-text",
                        "level": "WARNING",
                        "color_mode": "always"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/backend.log",
                        "format": "plain-text",
                        "level": "DEBUG"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/combined.log",
                        "format": "plain-text",
                        "level": "INFO"
                    }
                ]
            },
            
            # DATABASE: Syslog format + Same combined file
            "DATABASE": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/database.syslog",
                        "format": "syslog",
                        "level": "INFO"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/combined.log",
                        "format": "plain-text",
                        "level": "INFO"
                    }
                ]
            },
            
            # PAYMENT: GELF format + JSON file
            "PAYMENT": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/payment.gelf",
                        "format": "gelf",
                        "level": "INFO"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/payment.json",
                        "format": "json",
                        "level": "DEBUG"
                    }
                ]
            },
            
            # SECURITY: Console + JSON file + Same combined file
            "SECURITY": {
                "level": "WARNING",
                "destinations": [
                    {
                        "type": "console",
                        "format": "plain-text",
                        "level": "WARNING",
                        "color_mode": "always"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/security.json",
                        "format": "json",
                        "level": "INFO"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/combined.log",
                        "format": "plain-text",
                        "level": "WARNING"
                    }
                ]
            },
            
            # PERFORMANCE: CSV format + JSON file
            "PERFORMANCE": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/performance.csv",
                        "format": "csv",
                        "level": "INFO"
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/advanced/performance.json",
                        "format": "json",
                        "level": "DEBUG"
                    }
                ]
            }
        }
    }

def simulate_frontend_events(logger):
    """Simulate frontend user interactions."""
    print("\n=== Frontend Events ===")
    
    events = [
        ("User logged in", {"user_id": 12345, "session_id": "sess_abc123", "ip": "192.168.1.100"}),
        ("Page loaded", {"page": "/dashboard", "load_time": 1.2, "browser": "Chrome"}),
        ("Button clicked", {"button": "submit", "form": "contact", "user_id": 12345}),
        ("API call made", {"endpoint": "/api/users", "method": "GET", "status": 200}),
        ("Error occurred", {"error": "timeout", "component": "chart", "user_id": 12345})
    ]
    
    for message, extra in events:
        logger.info(message, "FRONTEND", extra=extra)
        time.sleep(0.1)

def simulate_backend_events(logger):
    """Simulate backend API and service events."""
    print("\n=== Backend Events ===")
    
    events = [
        ("API request received", {"endpoint": "/api/users", "method": "GET", "user_id": 12345}),
        ("Database query executed", {"table": "users", "query_time": 0.05, "rows": 1}),
        ("Cache miss", {"key": "user:12345", "cache": "redis", "action": "fetch_from_db"}),
        ("External API call", {"service": "payment_gateway", "status": 200, "response_time": 0.8}),
        ("Error: Database connection lost", {"host": "db.example.com", "port": 5432, "error": "timeout"})
    ]
    
    for message, extra in events:
        logger.debug(message, "BACKEND", extra=extra)
        time.sleep(0.1)

def simulate_database_events(logger):
    """Simulate database operations."""
    print("\n=== Database Events ===")
    
    events = [
        ("Connection established", {"host": "db.example.com", "port": 5432, "pool_size": 10}),
        ("Query executed", {"sql": "SELECT * FROM users", "execution_time": 0.05, "rows": 150}),
        ("Transaction committed", {"table": "payments", "rows_affected": 1, "transaction_id": "tx_123"}),
        ("Index created", {"table": "users", "index": "idx_email", "size": "2.5MB"}),
        ("Backup completed", {"size": "1.2GB", "duration": "00:05:30", "status": "success"})
    ]
    
    for message, extra in events:
        logger.info(message, "DATABASE", extra=extra)
        time.sleep(0.1)

def simulate_payment_events(logger):
    """Simulate payment processing events."""
    print("\n=== Payment Events ===")
    
    events = [
        ("Payment initiated", {"amount": 99.99, "currency": "USD", "payment_method": "credit_card"}),
        ("Payment authorized", {"transaction_id": "tx_abc123", "auth_code": "AUTH123", "amount": 99.99}),
        ("Payment processed", {"transaction_id": "tx_abc123", "status": "completed", "fee": 2.99}),
        ("Refund requested", {"original_tx": "tx_abc123", "refund_amount": 99.99, "reason": "customer_request"}),
        ("Payment failed", {"transaction_id": "tx_def456", "error": "insufficient_funds", "amount": 150.00})
    ]
    
    for message, extra in events:
        logger.info(message, "PAYMENT", extra=extra)
        time.sleep(0.1)

def simulate_security_events(logger):
    """Simulate security-related events."""
    print("\n=== Security Events ===")
    
    events = [
        ("Login attempt", {"user": "admin", "ip": "192.168.1.100", "success": True}),
        ("Failed login", {"user": "admin", "ip": "192.168.1.101", "reason": "invalid_password"}),
        ("Suspicious activity", {"ip": "10.0.0.50", "activity": "multiple_failed_logins", "count": 5}),
        ("Access denied", {"user": "guest", "resource": "/admin", "reason": "insufficient_permissions"}),
        ("Security scan completed", {"vulnerabilities": 0, "scan_duration": "00:02:15", "status": "clean"})
    ]
    
    for message, extra in events:
        logger.warning(message, "SECURITY", extra=extra)
        time.sleep(0.1)

def simulate_performance_events(logger):
    """Simulate performance monitoring events."""
    print("\n=== Performance Events ===")
    
    events = [
        ("Memory usage", {"memory_mb": 512, "memory_percent": 65, "threshold": 80}),
        ("CPU usage", {"cpu_percent": 45, "load_average": 1.2, "cores": 4}),
        ("Response time", {"endpoint": "/api/users", "avg_time": 0.15, "max_time": 0.8, "requests": 1000}),
        ("Database performance", {"query_time": 0.05, "slow_queries": 2, "total_queries": 5000}),
        ("Cache hit rate", {"hit_rate": 85, "miss_rate": 15, "total_requests": 10000})
    ]
    
    for message, extra in events:
        logger.info(message, "PERFORMANCE", extra=extra)
        time.sleep(0.1)

def demonstrate_multi_layer_logging():
    """Demonstrate advanced multi-layer logging scenarios."""
    
    print("Advanced Multi-Layer Logging Demo")
    print("=" * 60)
    print("This example demonstrates:")
    print("- Multiple layers with different formats (JSON, CSV, Plain-text, Syslog, GELF)")
    print("- Multiple layers writing to the same file")
    print("- Multiple layers writing to different files")
    print("- Console output with colors")
    print("- Structured logging with extra data")
    print("- Different log levels for different layers")
    print()
    
    # Create advanced configuration
    config = create_advanced_config()
    
    # Create logger with advanced configuration
    logger = HydraLogger(config=config)
    
    print("Configuration created with the following layers:")
    for layer_name in config["layers"].keys():
        destinations = config["layers"][layer_name]["destinations"]
        print(f"  - {layer_name}: {len(destinations)} destinations")
        for dest in destinations:
            print(f"    * {dest['type']} -> {dest.get('path', 'console')} ({dest['format']})")
    
    print("\nStarting simulation...")
    
    # Simulate events from different layers
    simulate_frontend_events(logger)
    simulate_backend_events(logger)
    simulate_database_events(logger)
    simulate_payment_events(logger)
    simulate_security_events(logger)
    simulate_performance_events(logger)
    
    print("\n" + "=" * 60)
    print("Advanced multi-layer logging demo completed!")
    print("\nGenerated files:")
    print("  📁 examples/logs/advanced/")
    print("    ├── frontend.json (JSON format)")
    print("    ├── frontend.csv (CSV format)")
    print("    ├── backend.log (Plain text)")
    print("    ├── database.syslog (Syslog format)")
    print("    ├── payment.gelf (GELF format)")
    print("    ├── payment.json (JSON format)")
    print("    ├── security.json (JSON format)")
    print("    ├── performance.csv (CSV format)")
    print("    ├── performance.json (JSON format)")
    print("    └── combined.log (Multiple layers in same file)")
    
    print("\nKey features demonstrated:")
    print("  ✅ Multiple formats: JSON, CSV, Plain-text, Syslog, GELF")
    print("  ✅ Same file logging: BACKEND, DATABASE, SECURITY → combined.log")
    print("  ✅ Different file logging: Each layer has its own files")
    print("  ✅ Console output: FRONTEND, BACKEND, SECURITY with colors")
    print("  ✅ Structured logging: Extra data in JSON and CSV formats")
    print("  ✅ Different log levels: DEBUG, INFO, WARNING per layer")

if __name__ == "__main__":
    demonstrate_multi_layer_logging() 