#!/usr/bin/env python3
"""
📚 Console Configuration: Configure console output options

What you'll learn:
- Console configuration options
- Different console settings
- Custom console behavior
- Configuration best practices

Time: 10 minutes
Difficulty: Beginner
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_console_config():
    """Step-by-step console configuration guide."""
    print("📚 Console Configuration")
    print("=" * 40)
    
    # Step 1: Basic console configuration
    print("\n📦 Step 1: Basic Console Configuration")
    print("Creating a basic console configuration...")
    
    basic_config = LoggingConfig(
        layers={
            "CONSOLE": LogLayer(
                level="INFO",  # Only INFO and above
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
    
    logger = HydraLogger(basic_config)
    
    print("✅ Basic configuration created!")
    print("   - Level: INFO (only INFO and above)")
    print("   - Format: text")
    print("   - Destination: console only")
    
    # Step 2: Log with basic config
    print("\n📝 Step 2: Log with Basic Config")
    print("Logging messages (DEBUG won't show due to INFO level)...")
    
    logger.debug("CONSOLE", "This debug message won't show (level too low)")
    logger.info("CONSOLE", "This info message will show")
    logger.warning("CONSOLE", "This warning message will show")
    logger.error("CONSOLE", "This error message will show")
    
    print("✅ Messages logged!")
    
    # Step 3: Advanced console configuration
    print("\n⚙️  Step 3: Advanced Console Configuration")
    print("Creating an advanced console configuration...")
    
    advanced_config = LoggingConfig(
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
            ),
            "INFO": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        level="INFO",
                        format="text"
                    )
                ]
            ),
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
    
    advanced_logger = HydraLogger(advanced_config)
    
    print("✅ Advanced configuration created!")
    print("   - Multiple layers: DEBUG, INFO, ERROR")
    print("   - Each layer has its own console destination")
    print("   - Different levels for different purposes")
    
    # Step 4: Log with advanced config
    print("\n📝 Step 4: Log with Advanced Config")
    print("Logging messages to different layers...")
    
    advanced_logger.debug("DEBUG", "Debug message to DEBUG layer")
    advanced_logger.info("INFO", "Info message to INFO layer")
    advanced_logger.error("ERROR", "Error message to ERROR layer")
    
    print("✅ Messages logged to different layers!")
    
    # Step 5: Configuration options explained
    print("\n💡 Step 5: Configuration Options")
    print("Console configuration options:")
    print("  📊 Level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    print("  📄 Format: text, json, csv, syslog, gelf")
    print("  🎨 Colors: Automatic or custom")
    print("  📍 Destination: console only")
    print("  🏷️  Layers: Multiple layers for organization")
    
    # Step 6: Best practices
    print("\n🎯 Step 6: Best Practices")
    print("Console logging best practices:")
    print("  ✅ Use appropriate log levels")
    print("  ✅ Keep console output clean")
    print("  ✅ Use colors for visual distinction")
    print("  ✅ Organize with layers")
    print("  ✅ Consider performance (no file I/O)")
    
    # Step 7: Next steps
    print("\n🎯 Step 7: Next Steps")
    print("You've learned console configuration!")
    print("\nNext modules to try:")
    print("  🎨 03_console_levels.py - Different log levels")
    print("  🌈 04_console_colors.py - Custom colors")
    print("  📄 05_console_formats.py - Different formats")
    
    print("\n🎉 Console configuration completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_console_config() 