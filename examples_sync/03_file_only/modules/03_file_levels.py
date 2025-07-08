#!/usr/bin/env python3
"""
🎨 File Log Levels: Different log levels for files

What you'll learn:
- Understanding log levels for files
- Level filtering for files
- Level-specific file behavior
- Level best practices for files

Time: 10 minutes
Difficulty: Beginner
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_file_levels():
    """Step-by-step file log levels guide."""
    print("🎨 File Log Levels")
    print("=" * 40)
    
    # Step 1: Understanding log levels for files
    print("\n📊 Step 1: Understanding Log Levels for Files")
    print("Log levels in order of severity (lowest to highest):")
    print("  🔍 DEBUG   - Detailed information for debugging")
    print("  ℹ️  INFO    - General information about program execution")
    print("  ⚠️  WARNING - Something unexpected happened, but the program can continue")
    print("  ❌ ERROR   - A more serious problem occurred")
    print("  🚨 CRITICAL - A critical error that may prevent the program from running")
    
    # Step 2: DEBUG level file
    print("\n🔍 Step 2: DEBUG Level File")
    print("Creating file configuration with DEBUG level...")
    
    os.makedirs("logs/levels", exist_ok=True)
    
    debug_config = LoggingConfig(
        layers={
            "DEBUG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/levels/debug.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    debug_logger = HydraLogger(debug_config)
    
    print("✅ DEBUG configuration created!")
    print("   - Shows ALL log levels (DEBUG and above)")
    print("   - Perfect for development and debugging")
    print("   - File: logs/levels/debug.log")
    
    # Step 3: Log with DEBUG level
    print("\n📝 Step 3: Log with DEBUG Level")
    print("Logging messages at all levels (all will show)...")
    
    debug_logger.debug("DEBUG", "Debug message - detailed debugging info")
    debug_logger.info("DEBUG", "Info message - general information")
    debug_logger.warning("DEBUG", "Warning message - something to watch")
    debug_logger.error("DEBUG", "Error message - something went wrong")
    debug_logger.critical("DEBUG", "Critical message - system failure")
    
    print("✅ All messages logged (DEBUG level shows everything)!")
    
    # Step 4: INFO level file
    print("\nℹ️  Step 4: INFO Level File")
    print("Creating file configuration with INFO level...")
    
    info_config = LoggingConfig(
        layers={
            "INFO": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/levels/info.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    info_logger = HydraLogger(info_config)
    
    print("✅ INFO configuration created!")
    print("   - Shows INFO and above (no DEBUG)")
    print("   - Perfect for production and general use")
    print("   - File: logs/levels/info.log")
    
    # Step 5: Log with INFO level
    print("\n📝 Step 5: Log with INFO Level")
    print("Logging messages (DEBUG won't show)...")
    
    info_logger.debug("INFO", "Debug message - won't show (level too low)")
    info_logger.info("INFO", "Info message - will show")
    info_logger.warning("INFO", "Warning message - will show")
    info_logger.error("INFO", "Error message - will show")
    info_logger.critical("INFO", "Critical message - will show")
    
    print("✅ Messages logged (INFO level filters out DEBUG)!")
    
    # Step 6: ERROR level file
    print("\n❌ Step 6: ERROR Level File")
    print("Creating file configuration with ERROR level...")
    
    error_config = LoggingConfig(
        layers={
            "ERROR": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/levels/error.log",
                        format="text"
                    )
                ]
            )
        }
    )
    
    error_logger = HydraLogger(error_config)
    
    print("✅ ERROR configuration created!")
    print("   - Shows ERROR and CRITICAL only")
    print("   - Perfect for production error monitoring")
    print("   - File: logs/levels/error.log")
    
    # Step 7: Log with ERROR level
    print("\n📝 Step 7: Log with ERROR Level")
    print("Logging messages (only ERROR and CRITICAL will show)...")
    
    error_logger.debug("ERROR", "Debug message - won't show")
    error_logger.info("ERROR", "Info message - won't show")
    error_logger.warning("ERROR", "Warning message - won't show")
    error_logger.error("ERROR", "Error message - will show")
    error_logger.critical("ERROR", "Critical message - will show")
    
    print("✅ Messages logged (ERROR level shows only errors)!")
    
    # Step 8: Level filtering explained
    print("\n💡 Step 8: Level Filtering Explained")
    print("How level filtering works for files:")
    print("  🔍 DEBUG level: Shows DEBUG, INFO, WARNING, ERROR, CRITICAL")
    print("  ℹ️  INFO level:  Shows INFO, WARNING, ERROR, CRITICAL")
    print("  ⚠️  WARNING level: Shows WARNING, ERROR, CRITICAL")
    print("  ❌ ERROR level:  Shows ERROR, CRITICAL")
    print("  🚨 CRITICAL level: Shows CRITICAL only")
    
    # Step 9: Check file sizes
    print("\n📁 Step 9: Check File Sizes")
    print("File sizes based on log levels:")
    
    files_to_check = [
        ("logs/levels/debug.log", "DEBUG (all levels)"),
        ("logs/levels/info.log", "INFO (no DEBUG)"),
        ("logs/levels/error.log", "ERROR (errors only)")
    ]
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(f"   📄 {file_path}: {len(lines)} lines ({description})")
        else:
            print(f"   ❌ {file_path}: Not found")
    
    # Step 10: Best practices
    print("\n🎯 Step 10: Best Practices")
    print("File log level best practices:")
    print("  ✅ Use DEBUG for development and debugging")
    print("  ✅ Use INFO for general program flow")
    print("  ✅ Use WARNING for unexpected but non-critical issues")
    print("  ✅ Use ERROR for problems that need attention")
    print("  ✅ Use CRITICAL for system-threatening issues")
    print("  ✅ Choose appropriate levels for production vs development")
    
    # Step 11: Next steps
    print("\n🎯 Step 11: Next Steps")
    print("You've learned file log levels!")
    print("\nNext modules to try:")
    print("  📄 04_file_formats.py - Different file formats")
    print("  🗂️  05_file_organization.py - Organize logs by purpose")
    
    print("\n🎉 File log levels completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_file_levels() 