#!/usr/bin/env python3
"""
Basic Usage Example

This example demonstrates zero-configuration usage of Hydra-Logger:
- Minimal setup required
- Auto-detection of environment
- Sensible defaults
- "It just works" approach
"""

from hydra_logger import HydraLogger

def demo_basic_usage():
    """Demonstrate basic zero-configuration usage."""
    
    print("🚀 Hydra-Logger Basic Usage Example")
    print("=" * 50)
    
    # Zero configuration - it just works!
    logger = HydraLogger()
    
    print("✅ Logger created with zero configuration")
    print("🔧 Auto-detected environment and defaults")
    print("📝 Starting to log...")
    print()
    
    # Start logging immediately
    logger.info("APP", "Application started")
    logger.debug("CONFIG", "Configuration loaded")
    logger.warning("PERF", "High memory usage detected")
    logger.error("SECURITY", "Authentication failed")
    
    # Log with additional context
    logger.info("DATABASE", "Query executed", 
               query_time_ms=150,
               rows_returned=1000)
    
    logger.info("API", "Request processed", 
               endpoint="/users",
               status_code=200,
               response_time_ms=45)
    
    logger.warning("PERF", "Performance alert", 
                  memory_usage_mb=512,
                  cpu_percent=85)
    
    logger.error("SECURITY", "Login attempt failed", 
                user_id=12345,
                ip_address="192.168.1.100",
                reason="Invalid credentials")
    
    print()
    print("✅ Basic usage example completed!")
    print("💡 Notice how easy it is to start logging with zero configuration")
    print("🎯 The logger automatically:")
    print("   - Detects your environment")
    print("   - Sets sensible defaults")
    print("   - Provides colored console output")
    print("   - Handles different log levels")

if __name__ == "__main__":
    demo_basic_usage() 