#!/usr/bin/env python3
"""
🎯 Basic Console Logging: Get console-only logging working in 5 minutes

What you'll learn:
- Simple console-only setup
- Basic log levels
- Colored output
- No file I/O

Time: 5 minutes
Difficulty: Beginner
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_basic_console():
    """Step-by-step basic console logging guide."""
    print("🚀 Basic Console Logging")
    print("=" * 40)
    
    # Step 1: Create console-only configuration
    print("\n📦 Step 1: Console-Only Configuration")
    print("Creating configuration for console output only...")
    
    config = LoggingConfig(
        layers={
            "CONSOLE": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        level="DEBUG",
                        format="text"
                    )
                ]
            )
        }
    )
    
    print("✅ Configuration created!")
    
    # Step 2: Initialize logger
    print("\n📝 Step 2: Initialize Logger")
    print("Setting up Hydra-Logger with console-only configuration...")
    
    logger = HydraLogger(config)
    
    print("✅ Logger initialized!")
    
    # Step 3: Log messages at different levels
    print("\n🎨 Step 3: Log Messages")
    print("Logging messages at different levels (notice the colors)...")
    
    logger.debug("CONSOLE", "Debug message - only visible in debug mode")
    logger.info("CONSOLE", "Info message - general information")
    logger.warning("CONSOLE", "Warning message - something to watch out for")
    logger.error("CONSOLE", "Error message - something went wrong")
    logger.critical("CONSOLE", "Critical message - system failure")
    
    print("✅ Messages logged!")
    
    # Step 4: Verify console-only behavior
    print("\n🔍 Step 4: Verify Console-Only Behavior")
    print("Checking that no files were created...")
    
    import os
    if not os.path.exists("logs"):
        print("✅ No logs directory created (expected for console-only)")
    else:
        print("⚠️  Logs directory exists (may contain files from other examples)")
    
    # Step 5: Benefits explained
    print("\n💡 Step 5: Console-Only Benefits")
    print("Why console-only logging is useful:")
    print("  ✅ No file I/O - faster execution")
    print("  ✅ Immediate feedback - see logs instantly")
    print("  ✅ Development friendly - perfect for debugging")
    print("  ✅ No file clutter - no log files to manage")
    print("  ✅ Portable - works anywhere with a terminal")
    
    # Step 6: Next steps
    print("\n🎯 Step 6: Next Steps")
    print("You've successfully set up console-only logging!")
    print("\nNext modules to try:")
    print("  📚 02_console_config.py - Configure console options")
    print("  🎨 03_console_levels.py - Different log levels")
    print("  🌈 04_console_colors.py - Custom colors")
    print("  📄 05_console_formats.py - Different formats")
    
    print("\n🎉 Basic console logging completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_basic_console() 