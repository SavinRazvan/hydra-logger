#!/usr/bin/env python3
"""
Multi-Layer Same File Example

This example demonstrates multiple layers writing to the same file.
Different layers can have different formats and all logs go to the same file.
"""

import os
from hydra_logger import HydraLogger

def demo_multi_layer_same_file():
    """Demonstrate multiple layers writing to the same file."""
    
    print("Multi-Layer Same File Example")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Configuration with multiple layers writing to the same file
    config = {
        "layers": {
            "FRONTEND": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/combined.log",
                        "format": "plain-text",
                        "level": "INFO"
                    }
                ]
            },
            "BACKEND": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/combined.log",
                        "format": "plain-text",
                        "level": "DEBUG"
                    }
                ]
            },
            "DATABASE": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/combined.log",
                        "format": "plain-text",
                        "level": "INFO"
                    }
                ]
            }
        }
    }
    
    # Create logger with multiple layers
    logger = HydraLogger(config=config)
    
    # Log from different layers to the same file
    logger.info("User interface loaded", "FRONTEND")
    logger.info("API request received", "BACKEND", extra={"endpoint": "/api/users", "method": "GET"})
    logger.info("Database query executed", "DATABASE", extra={"table": "users", "rows": 150})
    
    logger.warning("High memory usage", "FRONTEND", extra={"memory_mb": 512})
    logger.warning("Slow API response", "BACKEND", extra={"endpoint": "/api/data", "response_time": 2.5})
    logger.warning("Database connection pool full", "DATABASE", extra={"pool_size": 10, "active": 10})
    
    logger.error("UI component failed to load", "FRONTEND", extra={"component": "chart", "error": "timeout"})
    logger.error("API authentication failed", "BACKEND", extra={"user": "admin", "reason": "invalid_token"})
    logger.error("Database connection lost", "DATABASE", extra={"host": "db.example.com", "port": 5432})
    
    print("\nMulti-layer same file example completed!")
    print("Check the following file:")
    print("   - examples/logs/combined.log (All layers in one file)")

if __name__ == "__main__":
    demo_multi_layer_same_file() 