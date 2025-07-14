#!/usr/bin/env python3
"""
Syslog Format Example

This example demonstrates logging in syslog format.
Syslog format is useful for system monitoring and enterprise logging infrastructure.
"""

import os
from hydra_logger import HydraLogger

def demo_syslog_format():
    """Demonstrate syslog format logging."""
    
    print("Syslog Format Example")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Configuration with syslog format
    config = {
        "layers": {
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
            "SECURITY": {
                "level": "WARNING",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/security.syslog",
                        "format": "syslog",
                        "level": "WARNING"
                    }
                ]
            }
        }
    }
    
    # Create logger with syslog format
    logger = HydraLogger(config=config)
    
    # Log system events
    logger.info("System startup completed", "SYSTEM")
    logger.info("Service started", "SYSTEM", extra={"service": "nginx", "port": 80})
    logger.warning("High memory usage", "SYSTEM", extra={"memory_percent": 85})
    logger.error("Service failed to start", "SYSTEM", extra={"service": "database", "error": "connection timeout"})
    
    # Log security events
    logger.warning("Failed login attempt", "SECURITY", extra={"user": "admin", "ip": "192.168.1.100"})
    logger.warning("Suspicious activity detected", "SECURITY", extra={"type": "brute_force", "ip": "10.0.0.50"})
    logger.error("Authentication failure", "SECURITY", extra={"user": "user123", "reason": "invalid_password"})
    logger.error("Access denied", "SECURITY", extra={"resource": "/admin", "user": "guest", "ip": "203.0.113.1"})
    
    print("\nSyslog format example completed!")
    print("Check the following files:")
    print("   - examples/logs/system.syslog (System events)")
    print("   - examples/logs/security.syslog (Security events)")

if __name__ == "__main__":
    demo_syslog_format() 