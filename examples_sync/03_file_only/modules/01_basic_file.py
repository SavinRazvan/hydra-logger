#!/usr/bin/env python3
"""
📁 Basic File Logging: Get file-only logging working in 5 minutes

What you'll learn:
- Simple file-only setup
- Basic log levels
- File output
- No console clutter

Time: 5 minutes
Difficulty: Beginner
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_basic_file():
    """Step-by-step basic file logging guide."""
    print("📁 Basic File Logging")
    print("=" * 40)
    
    # Step 1: Create file-only configuration
    print("\n📦 Step 1: File-Only Configuration")
    print("Creating configuration for file output only...")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    config = LoggingConfig(
        layers={
            "FILE": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/file_only.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    print("✅ Configuration created!")
    print("   - Destination: file only (no console)")
    print("   - Path: logs/file_only.log")
    print("   - Format: text")
    print("   - Level: DEBUG (all levels)")
    
    # Step 2: Initialize logger
    print("\n📝 Step 2: Initialize Logger")
    print("Setting up Hydra-Logger with file-only configuration...")
    
    logger = HydraLogger(config)
    
    print("✅ Logger initialized!")
    
    # Step 3: Log messages at different levels
    print("\n📝 Step 3: Log Messages")
    print("Logging messages at different levels (no console output)...")
    
    logger.debug("FILE", "Debug message - detailed information for debugging")
    logger.info("FILE", "Info message - general application information")
    logger.warning("FILE", "Warning message - something to watch out for")
    logger.error("FILE", "Error message - something went wrong")
    logger.critical("FILE", "Critical message - system failure")
    
    print("✅ Messages logged to file!")
    
    # Step 4: Verify file-only behavior
    print("\n🔍 Step 4: Verify File-Only Behavior")
    print("Checking that logs were written to file...")
    
    log_file_path = "logs/file_only.log"
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            content = f.read()
            print(f"✅ Log file created: {log_file_path}")
            print(f"📄 File size: {len(content)} characters")
            print(f"📊 Lines written: {len(content.splitlines())}")
    else:
        print("❌ Log file not found")
    
    # Step 5: Benefits explained
    print("\n💡 Step 5: File-Only Benefits")
    print("Why file-only logging is useful:")
    print("  ✅ Persistent storage - logs saved for later analysis")
    print("  ✅ Production ready - perfect for production environments")
    print("  ✅ No console clutter - clean console output")
    print("  ✅ Structured data - can include additional context")
    print("  ✅ Compliance ready - meets regulatory requirements")
    
    # Step 6: Check file content
    print("\n📄 Step 6: Check File Content")
    print("Recent log entries:")
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:  # Show last 5 lines
                print(f"   {line.strip()}")
    
    # Step 7: Next steps
    print("\n🎯 Step 7: Next Steps")
    print("You've successfully set up file-only logging!")
    print("\nNext modules to try:")
    print("  📚 02_file_config.py - Configure file options")
    print("  🎨 03_file_levels.py - Different log levels")
    print("  📄 04_file_formats.py - Different file formats")
    print("  🗂️  05_file_organization.py - Organize logs by purpose")
    
    print("\n🎉 Basic file logging completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_basic_file() 