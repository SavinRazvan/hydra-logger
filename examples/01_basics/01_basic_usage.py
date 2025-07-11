#!/usr/bin/env python3
"""
Basic Usage Example

This example demonstrates zero-configuration usage of Hydra-Logger:
- Minimal setup required
- Auto-detection of environment
- Sensible defaults
- Works out of the box
"""

from hydra_logger import HydraLogger

def demo_basic_usage():
    """Demonstrate basic zero-configuration usage."""
    
    print("Hydra-Logger Basic Usage Example")
    print("=" * 50)
    
    # Zero configuration - works immediately
    logger = HydraLogger()
    
    print("Logger created with zero configuration")
    print("Auto-detected environment and defaults")
    print("Starting to log...")
    print()
    
    # Start logging immediately
    logger.info("APP", "Application started")
    logger.debug("CONFIG", "Configuration loaded")
    logger.warning("PERF", "High memory usage detected")
    logger.error("SECURITY", "Authentication failed")
    
    # Log with additional context
    logger.info("DATABASE", "Query executed")
    logger.info("API", "Request processed")
    logger.warning("PERF", "Performance alert")
    logger.error("SECURITY", "Login attempt failed")
    
    print()
    print("Basic usage example completed!")
    print("Notice how easy it is to start logging with zero configuration")
    print("The logger automatically:")
    print("   - Detects your environment")
    print("   - Sets sensible defaults")
    print("   - Provides colored console output")
    print("   - Handles different log levels")

if __name__ == "__main__":
    demo_basic_usage() 