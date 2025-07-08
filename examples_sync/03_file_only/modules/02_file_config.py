#!/usr/bin/env python3
"""
📚 File Configuration: Configure file output options

What you'll learn:
- File configuration options
- Different file settings
- Custom file behavior
- Configuration best practices

Time: 10 minutes
Difficulty: Beginner
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_file_config():
    """Step-by-step file configuration guide."""
    print("📚 File Configuration")
    print("=" * 40)
    
    # Step 1: Basic file configuration
    print("\n📦 Step 1: Basic File Configuration")
    print("Creating a basic file configuration...")
    
    os.makedirs("logs/config", exist_ok=True)
    
    basic_config = LoggingConfig(
        layers={
            "CONFIG": LogLayer(
                level="INFO",  # Only INFO and above
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/config/app.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    logger = HydraLogger(basic_config)
    
    print("✅ Basic configuration created!")
    print("   - Level: INFO (only INFO and above)")
    print("   - Path: logs/config/app.log")
    print("   - Format: text")
    print("   - Destination: file only")
    
    # Step 2: Log with basic config
    print("\n📝 Step 2: Log with Basic Config")
    print("Logging messages (DEBUG won't show due to INFO level)...")
    
    logger.debug("CONFIG", "This debug message won't show (level too low)")
    logger.info("CONFIG", "This info message will show")
    logger.warning("CONFIG", "This warning message will show")
    logger.error("CONFIG", "This error message will show")
    
    print("✅ Messages logged!")
    
    # Step 3: Advanced file configuration
    print("\n⚙️  Step 3: Advanced File Configuration")
    print("Creating an advanced file configuration...")
    
    os.makedirs("logs/config", exist_ok=True)
    
    advanced_config = LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/config/app.log",
                        format="text"
                    )
                ]
            ),
            "ERRORS": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/config/errors.log",
                        format="text"
                    )
                ]
            ),
            "DEBUG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/config/debug.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    advanced_logger = HydraLogger(advanced_config)
    
    print("✅ Advanced configuration created!")
    print("   - Multiple layers: APP, ERRORS, DEBUG")
    print("   - Each layer has its own file")
    print("   - Different levels for different purposes")
    
    # Step 4: Log with advanced config
    print("\n📝 Step 4: Log with Advanced Config")
    print("Logging messages to different layers...")
    
    advanced_logger.info("APP", "Application started")
    advanced_logger.debug("DEBUG", "Debug message to DEBUG layer")
    advanced_logger.error("ERRORS", "Error message to ERRORS layer")
    advanced_logger.info("APP", "Application running normally")
    
    print("✅ Messages logged to different files!")
    
    # Step 5: Configuration options explained
    print("\n💡 Step 5: Configuration Options")
    print("File configuration options:")
    print("  📊 Level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    print("  📄 Format: text, json, csv, syslog, gelf")
    print("  📍 Path: Custom file paths")
    print("  🔄 Rotation: File size limits and backup counts")
    print("  🏷️  Layers: Multiple layers for organization")
    
    # Step 6: Check generated files
    print("\n📁 Step 6: Check Generated Files")
    print("Files created:")
    
    files_to_check = [
        "logs/config/app.log",
        "logs/config/errors.log", 
        "logs/config/debug.log"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(f"   ✅ {file_path}: {len(lines)} lines")
        else:
            print(f"   ❌ {file_path}: Not found")
    
    # Step 7: Best practices
    print("\n🎯 Step 7: Best Practices")
    print("File logging best practices:")
    print("  ✅ Use appropriate log levels")
    print("  ✅ Organize logs by purpose")
    print("  ✅ Use meaningful file names")
    print("  ✅ Consider log rotation")
    print("  ✅ Plan for log analysis")
    
    # Step 8: Next steps
    print("\n🎯 Step 8: Next Steps")
    print("You've learned file configuration!")
    print("\nNext modules to try:")
    print("  🎨 03_file_levels.py - Different log levels")
    print("  📄 04_file_formats.py - Different file formats")
    print("  🗂️  05_file_organization.py - Organize logs by purpose")
    
    print("\n🎉 File configuration completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_file_config() 