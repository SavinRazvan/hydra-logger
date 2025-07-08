#!/usr/bin/env python3
"""
Environment Variables Format Example

This example demonstrates format customization using environment variables:
- Setting format parameters via environment variables
- Overriding default formats
- Environment-based configuration
"""

import os
from hydra_logger import HydraLogger

def demo_environment_variables():
    """Demonstrate format customization using environment variables."""
    
    print("🌍 Environment Variables Format Example")
    print("=" * 50)
    
    # Set environment variables for format customization
    os.environ["HYDRA_LOG_DATE_FORMAT"] = "%Y-%m-%d"
    os.environ["HYDRA_LOG_TIME_FORMAT"] = "%H:%M:%S"
    os.environ["HYDRA_LOG_LOGGER_NAME_FORMAT"] = "[{name}]"
    os.environ["HYDRA_LOG_MESSAGE_FORMAT"] = "{level}: {message}"
    
    print("🔧 Environment variables set:")
    print(f"   HYDRA_LOG_DATE_FORMAT: {os.environ.get('HYDRA_LOG_DATE_FORMAT')}")
    print(f"   HYDRA_LOG_TIME_FORMAT: {os.environ.get('HYDRA_LOG_TIME_FORMAT')}")
    print(f"   HYDRA_LOG_LOGGER_NAME_FORMAT: {os.environ.get('HYDRA_LOG_LOGGER_NAME_FORMAT')}")
    print(f"   HYDRA_LOG_MESSAGE_FORMAT: {os.environ.get('HYDRA_LOG_MESSAGE_FORMAT')}")
    
    # Create logger that uses environment variables
    logger = HydraLogger()
    
    print("\n📝 Logging with environment variable formats:")
    
    # Log messages with environment-based formatting
    logger.info("APP", "Application started with environment variables")
    logger.info("CONFIG", "Configuration loaded from environment")
    logger.warning("PERF", "Performance warning detected")
    logger.error("SECURITY", "Security alert triggered")
    
    # Change environment variables and create new logger
    print("\n🔄 Changing environment variables...")
    
    os.environ["HYDRA_LOG_DATE_FORMAT"] = "%Y/%m/%d"
    os.environ["HYDRA_LOG_TIME_FORMAT"] = "%H:%M:%S.%f"
    os.environ["HYDRA_LOG_LOGGER_NAME_FORMAT"] = "({name})"
    os.environ["HYDRA_LOG_MESSAGE_FORMAT"] = "[{level}] {message}"
    
    print("🔧 Updated environment variables:")
    print(f"   HYDRA_LOG_DATE_FORMAT: {os.environ.get('HYDRA_LOG_DATE_FORMAT')}")
    print(f"   HYDRA_LOG_TIME_FORMAT: {os.environ.get('HYDRA_LOG_TIME_FORMAT')}")
    print(f"   HYDRA_LOG_LOGGER_NAME_FORMAT: {os.environ.get('HYDRA_LOG_LOGGER_NAME_FORMAT')}")
    print(f"   HYDRA_LOG_MESSAGE_FORMAT: {os.environ.get('HYDRA_LOG_MESSAGE_FORMAT')}")
    
    # Create new logger with updated environment variables
    logger2 = HydraLogger()
    
    print("\n📝 Logging with updated environment variable formats:")
    
    # Log messages with updated environment-based formatting
    logger2.info("APP", "Application with updated environment format")
    logger2.info("CONFIG", "Configuration with new format")
    logger2.warning("PERF", "Performance with updated format")
    logger2.error("SECURITY", "Security with new format")
    
    print("\n✅ Environment variables format example completed!")
    print("💡 Environment variables allow dynamic format configuration")

if __name__ == "__main__":
    demo_environment_variables() 