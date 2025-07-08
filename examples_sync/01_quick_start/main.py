#!/usr/bin/env python3
"""
🚀 Quick Start: Get Hydra-Logger Running in 5 Minutes

This example shows the absolute basics of Hydra-Logger:
- Simple setup
- Console and file logging
- Different log levels
- Colored output
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def main():
    print("🚀 Hydra-Logger Quick Start")
    print("=" * 40)
    
    # Step 1: Create logs directory
    os.makedirs("logs", exist_ok=True)
    print("✅ Created logs directory")
    
    # Step 2: Simple configuration
    config = LoggingConfig(
        layers={
            "APP": LogLayer(
                level="DEBUG",  # Show all levels
                destinations=[
                    LogDestination(
                        type="console",
                        format="text"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/app.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    # Step 3: Initialize logger
    logger = HydraLogger(config)
    print("✅ Logger initialized")
    
    # Step 4: Log different levels
    print("\n📝 Logging different levels...")
    
    logger.info("APP", "Application started")
    logger.debug("APP", "Debug information")
    logger.warning("APP", "Warning message")
    logger.error("APP", "Error occurred")
    
    # Step 5: Show results
    print("\n✅ Done! Check the output above and the log file:")
    print("📄 logs/app.log")
    
    # Show file contents
    if os.path.exists("logs/app.log"):
        print("\n📊 Log file contents:")
        with open("logs/app.log", "r") as f:
            print(f.read())

if __name__ == "__main__":
    main() 