#!/usr/bin/env python3
"""
Mixed Formats Example

This example demonstrates multiple layers with different formats writing to different files.
Each layer can have its own format and file, and all logs are written simultaneously.
"""

import os
from hydra_logger import HydraLogger

def demo_mixed_formats():
    """Demonstrate mixed formats with multiple layers."""
    
    print("Mixed Formats Example")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Configuration with mixed formats
    config = {
        "layers": {
            "FRONTEND": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/frontend.json",
                        "format": "json",
                        "level": "INFO"
                    }
                ]
            },
            "BACKEND": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/backend.csv",
                        "format": "csv",
                        "level": "INFO"
                    }
                ]
            },
            "SYSTEM": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/system.syslog",
                        "format": "syslog",
                        "level": "INFO"
                    }
                ]
            },
            "MONITORING": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/monitoring.gelf",
                        "format": "gelf",
                        "level": "INFO"
                    }
                ]
            }
        }
    }
    
    # Create logger with mixed formats
    logger = HydraLogger(config=config)
    
    # Log events to different formats simultaneously
    logger.info("User interface updated", "FRONTEND", extra={"component": "dashboard", "user_id": 12345})
    logger.info("API request processed", "BACKEND", extra={"endpoint": "/api/data", "response_time": 0.125})
    logger.info("System health check", "SYSTEM", extra={"service": "web_server", "status": "healthy"})
    logger.info("Performance metric", "MONITORING", extra={"cpu_usage": 45.2, "memory_usage": 67.8})
    
    logger.warning("High memory usage detected", "FRONTEND", extra={"memory_mb": 512})
    logger.warning("Slow database query", "BACKEND", extra={"query_time": 2.5, "table": "users"})
    logger.warning("Service restart required", "SYSTEM", extra={"service": "cache", "reason": "memory_leak"})
    logger.warning("High load detected", "MONITORING", extra={"load_average": 4.5, "threshold": 3.0})
    
    logger.error("UI component failed", "FRONTEND", extra={"component": "chart", "error": "timeout"})
    logger.error("Database connection failed", "BACKEND", extra={"host": "db.example.com", "error": "connection_refused"})
    logger.error("Critical system error", "SYSTEM", extra={"service": "database", "error": "out_of_memory"})
    logger.error("Service unavailable", "MONITORING", extra={"service": "api", "duration": 300})
    
    print("\nMixed formats example completed!")
    print("Check the following files:")
    print("   - examples/logs/frontend.json (JSON format)")
    print("   - examples/logs/backend.csv (CSV format)")
    print("   - examples/logs/system.syslog (Syslog format)")
    print("   - examples/logs/monitoring.gelf (GELF format)")

if __name__ == "__main__":
    demo_mixed_formats() 