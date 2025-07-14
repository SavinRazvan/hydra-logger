#!/usr/bin/env python3
"""
GELF Format Example

This example demonstrates logging in GELF (Graylog Extended Log Format).
GELF is useful for Graylog integration and centralized logging systems.
"""

import os
from hydra_logger import HydraLogger

def demo_gelf_format():
    """Demonstrate GELF format logging."""
    
    print("GELF Format Example")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Configuration with GELF format
    config = {
        "layers": {
            "APPLICATION": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/application.gelf",
                        "format": "gelf",
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
    
    # Create logger with GELF format
    logger = HydraLogger(config=config)
    
    # Log application events
    logger.info("Application started", "APPLICATION", extra={"version": "1.2.3", "environment": "production"})
    logger.info("User action", "APPLICATION", extra={"action": "login", "user_id": 12345, "session_id": "sess_abc123"})
    logger.warning("Performance degradation", "APPLICATION", extra={"component": "database", "response_time": 2.5})
    logger.error("Critical error", "APPLICATION", extra={"error_code": "E1001", "component": "payment_processor"})
    
    # Log monitoring events
    logger.info("Health check", "MONITORING", extra={"service": "api", "status": "healthy", "response_time": 0.05})
    logger.info("Resource usage", "MONITORING", extra={"cpu": 45.2, "memory": 67.8, "disk": 23.1})
    logger.warning("High load detected", "MONITORING", extra={"load_average": 4.5, "threshold": 3.0})
    logger.error("Service unavailable", "MONITORING", extra={"service": "database", "duration": 300})
    
    print("\nGELF format example completed!")
    print("Check the following files:")
    print("   - examples/logs/application.gelf (Application events)")
    print("   - examples/logs/monitoring.gelf (Monitoring events)")

if __name__ == "__main__":
    demo_gelf_format() 