#!/usr/bin/env python3
"""
🎨 Console Log Levels: Different log levels for console

What you'll learn:
- Understanding log levels
- Level filtering
- Level-specific behavior
- Level best practices

Time: 10 minutes
Difficulty: Beginner
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_console_levels():
    """Step-by-step console log levels guide."""
    print("🎨 Console Log Levels")
    print("=" * 40)
    
    # Step 1: Understanding log levels
    print("\n📊 Step 1: Understanding Log Levels")
    print("Log levels in order of severity (lowest to highest):")
    print("  🔍 DEBUG   - Detailed information for debugging")
    print("  ℹ️  INFO    - General information about program execution")
    print("  ⚠️  WARNING - Something unexpected happened, but the program can continue")
    print("  ❌ ERROR   - A more serious problem occurred")
    print("  🚨 CRITICAL - A critical error that may prevent the program from running")
    
    # Step 2: DEBUG level console
    print("\n🔍 Step 2: DEBUG Level Console")
    print("Creating console configuration with DEBUG level...")
    
    debug_config = LoggingConfig(
        layers={
            "DEBUG": LogLayer(
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
    
    debug_logger = HydraLogger(debug_config)
    
    print("✅ DEBUG configuration created!")
    print("   - Shows ALL log levels (DEBUG and above)")
    print("   - Perfect for development and debugging")
    
    # Step 3: Log with DEBUG level
    print("\n📝 Step 3: Log with DEBUG Level")
    print("Logging messages at all levels (all will show)...")
    
    debug_logger.debug("DEBUG", "Debug message - detailed debugging info")
    debug_logger.info("DEBUG", "Info message - general information")
    debug_logger.warning("DEBUG", "Warning message - something to watch")
    debug_logger.error("DEBUG", "Error message - something went wrong")
    debug_logger.critical("DEBUG", "Critical message - system failure")
    
    print("✅ All messages logged (DEBUG level shows everything)!")
    
    # Step 4: INFO level console
    print("\nℹ️  Step 4: INFO Level Console")
    print("Creating console configuration with INFO level...")
    
    info_config = LoggingConfig(
        layers={
            "INFO": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        level="INFO",
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
    
    # Step 5: Log with INFO level
    print("\n📝 Step 5: Log with INFO Level")
    print("Logging messages (DEBUG won't show)...")
    
    info_logger.debug("INFO", "Debug message - won't show (level too low)")
    info_logger.info("INFO", "Info message - will show")
    info_logger.warning("INFO", "Warning message - will show")
    info_logger.error("INFO", "Error message - will show")
    info_logger.critical("INFO", "Critical message - will show")
    
    print("✅ Messages logged (INFO level filters out DEBUG)!")
    
    # Step 6: ERROR level console
    print("\n❌ Step 6: ERROR Level Console")
    print("Creating console configuration with ERROR level...")
    
    error_config = LoggingConfig(
        layers={
            "ERROR": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="console",
                        level="ERROR",
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
    print("How level filtering works:")
    print("  🔍 DEBUG level: Shows DEBUG, INFO, WARNING, ERROR, CRITICAL")
    print("  ℹ️  INFO level:  Shows INFO, WARNING, ERROR, CRITICAL")
    print("  ⚠️  WARNING level: Shows WARNING, ERROR, CRITICAL")
    print("  ❌ ERROR level:  Shows ERROR, CRITICAL")
    print("  🚨 CRITICAL level: Shows CRITICAL only")
    
    # Step 9: Best practices
    print("\n🎯 Step 9: Best Practices")
    print("Log level best practices:")
    print("  ✅ Use DEBUG for development and debugging")
    print("  ✅ Use INFO for general program flow")
    print("  ✅ Use WARNING for unexpected but non-critical issues")
    print("  ✅ Use ERROR for problems that need attention")
    print("  ✅ Use CRITICAL for system-threatening issues")
    print("  ✅ Choose appropriate levels for production vs development")
    
    # Step 10: Next steps
    print("\n🎯 Step 10: Next Steps")
    print("You've learned console log levels!")
    print("\nNext modules to try:")
    print("  🌈 04_console_colors.py - Custom colors")
    print("  📄 05_console_formats.py - Different formats")
    
    print("\n🎉 Console log levels completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_console_levels() 