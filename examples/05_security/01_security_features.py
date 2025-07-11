#!/usr/bin/env python3
"""
Security Features Example

This example demonstrates security features:
- PII detection and redaction
- Data sanitization
- Sensitive data protection
- Security logging levels
"""

from hydra_logger import HydraLogger

def demo_security_features():
    """Demonstrate security features and data protection."""
    
    print("Security Features Example")
    print("=" * 50)
    
    # Create logger with security features enabled
    logger = HydraLogger(
        enable_security=True,
        enable_sanitization=True
    )
    
    print("Security features enabled:")
    print("   - PII detection and redaction")
    print("   - Data sanitization")
    print("   - Sensitive data protection")
    
    print("\nLogging with sensitive data (will be auto-masked):")
    
    # Log messages with sensitive data that will be automatically masked
    logger.info("AUTH", "User login attempt", 
               extra={"email": "user@example.com", "password": "secret123", "session_token": "abc123xyz789"})
    
    logger.info("PAYMENT", "Credit card transaction",
               extra={"card_number": "1234-5678-9012-3456", "cvv": "123", "expiry": "12/25"})
    
    logger.info("PERSONAL", "User profile update",
               extra={"ssn": "123-45-6789", "phone": "+1-555-123-4567", "address": "123 Main St, City, State 12345"})
    
    logger.info("API", "API request with tokens",
               extra={"api_key": "sk_live_abc123def456ghi789", "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "refresh_token": "rt_1234567890abcdef"})
    
    print("\nLogging with non-sensitive data (will not be masked):")
    
    # Log messages with non-sensitive data
    logger.info("APP", "Application started", 
               extra={"version": "0.4.0", "environment": "production", "uptime_seconds": 3600})
    
    logger.info("PERF", "Performance metrics",
               extra={"response_time_ms": 150, "memory_usage_mb": 512, "cpu_percent": 25})
    
    logger.info("CONFIG", "Configuration loaded",
               extra={"config_size": 1024, "config_version": "0.4.0", "features_enabled": ["async", "security", "plugins"]})
    
    print("\nSecurity features example completed!")
    print("Notice how sensitive data is automatically masked in the output")
    print("Check the console output to see the redaction in action")

if __name__ == "__main__":
    demo_security_features() 