#!/usr/bin/env python3
"""
Multiple Destinations Example

This example demonstrates logging to multiple destinations with different formats:
- Console output with colored text format
- File output with JSON format
- Different log levels for each destination
"""

import os
from hydra_logger import HydraLogger

def demo_multiple_destinations():
    """Demonstrate logging to multiple destinations."""
    
    print("Multiple Destinations Example")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Configuration with multiple destinations
    config = {
        "layers": {
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
                        "path": "examples/logs/frontend.json",
                        "format": "json",
                        "level": "DEBUG"
                    }
                ]
            },
            "BACKEND": {
                "level": "DEBUG",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/backend.log",
                        "format": "plain-text",
                        "level": "DEBUG"
                    }
                ]
            }
        }
    }
    
    # Create logger with multiple destinations
    logger = HydraLogger(config=config)
    
    # Log messages that will go to multiple destinations
    logger.info("User interface updated", "FRONTEND")
    logger.info("User logged in", "FRONTEND", extra={"user_id": 12345, "action": "login"})
    logger.warning("High memory usage detected", "FRONTEND", extra={"memory_mb": 512})
    logger.error("Database connection failed", "FRONTEND", extra={"error_code": 500})
    
    # Backend messages (only to backend file)
    logger.debug("API endpoint called", "BACKEND")
    logger.debug("Configuration loaded", "BACKEND", extra={"config_size": 1024})
    
    print("\nMultiple destinations example completed!")
    print("Check the following files:")
    print("   - examples/logs/frontend.json (JSON format)")
    print("   - examples/logs/backend.log (Text format)")
    print("   - Console output (Colored text)")

if __name__ == "__main__":
    demo_multiple_destinations() 