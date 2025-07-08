#!/usr/bin/env python3
"""
🌈 Console Colors: Custom colors and formatting for console

What you'll learn:
- Default color scheme
- Custom color configuration
- Color best practices
- Visual appeal techniques

Time: 15 minutes
Difficulty: Intermediate
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_console_colors():
    """Step-by-step console colors guide."""
    print("🌈 Console Colors")
    print("=" * 40)
    
    # Step 1: Default colors
    print("\n🎨 Step 1: Default Color Scheme")
    print("Hydra-Logger's default professional color scheme:")
    print("  🔍 DEBUG   - Cyan")
    print("  ℹ️  INFO    - Green")
    print("  ⚠️  WARNING - Yellow")
    print("  ❌ ERROR   - Red")
    print("  🚨 CRITICAL - Bright Red")
    print("  🏷️  Layer Names - Magenta")
    
    # Step 2: Default color demo
    print("\n📝 Step 2: Default Color Demo")
    print("Logging with default colors...")
    
    default_config = LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
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
    
    default_logger = HydraLogger(default_config)
    
    default_logger.debug("DEFAULT", "Debug message with default cyan color")
    default_logger.info("DEFAULT", "Info message with default green color")
    default_logger.warning("DEFAULT", "Warning message with default yellow color")
    default_logger.error("DEFAULT", "Error message with default red color")
    default_logger.critical("DEFAULT", "Critical message with default bright red color")
    
    print("✅ Default colors demonstrated!")
    
    # Step 3: Custom colors with environment variables
    print("\n🎨 Step 3: Custom Colors with Environment Variables")
    print("Setting custom colors using environment variables...")
    
    # Set custom colors
    os.environ["HYDRA_LOG_COLOR_ERROR"] = "bright_red"
    os.environ["HYDRA_LOG_COLOR_INFO"] = "bright_green"
    os.environ["HYDRA_LOG_COLOR_DEBUG"] = "bright_cyan"
    os.environ["HYDRA_LOG_LAYER_COLOR"] = "bright_blue"
    
    custom_config = LoggingConfig(
        layers={
            "CUSTOM": LogLayer(
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
    
    custom_logger = HydraLogger(custom_config)
    
    print("✅ Custom colors configured!")
    print("   - ERROR: bright_red")
    print("   - INFO: bright_green")
    print("   - DEBUG: bright_cyan")
    print("   - Layer: bright_blue")
    
    # Step 4: Log with custom colors
    print("\n📝 Step 4: Log with Custom Colors")
    print("Logging with custom colors...")
    
    custom_logger.debug("CUSTOM", "Debug message with custom bright cyan")
    custom_logger.info("CUSTOM", "Info message with custom bright green")
    custom_logger.warning("CUSTOM", "Warning message with default yellow")
    custom_logger.error("CUSTOM", "Error message with custom bright red")
    custom_logger.critical("CUSTOM", "Critical message with default bright red")
    
    print("✅ Custom colors demonstrated!")
    
    # Step 5: Reset to default colors
    print("\n🔄 Step 5: Reset to Default Colors")
    print("Clearing custom colors to return to defaults...")
    
    # Clear custom colors
    for key in ["HYDRA_LOG_COLOR_ERROR", "HYDRA_LOG_COLOR_INFO", 
                "HYDRA_LOG_COLOR_DEBUG", "HYDRA_LOG_LAYER_COLOR"]:
        if key in os.environ:
            del os.environ[key]
    
    reset_config = LoggingConfig(
        layers={
            "RESET": LogLayer(
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
    
    reset_logger = HydraLogger(reset_config)
    
    print("✅ Colors reset to defaults!")
    
    # Step 6: Log with reset colors
    print("\n📝 Step 6: Log with Reset Colors")
    print("Logging with default colors restored...")
    
    reset_logger.debug("RESET", "Debug message with default cyan")
    reset_logger.info("RESET", "Info message with default green")
    reset_logger.warning("RESET", "Warning message with default yellow")
    reset_logger.error("RESET", "Error message with default red")
    reset_logger.critical("RESET", "Critical message with default bright red")
    
    print("✅ Default colors restored!")
    
    # Step 7: Available colors
    print("\n🎨 Step 7: Available Colors")
    print("Hydra-Logger supports these named colors:")
    print("  Basic Colors:")
    print("    - red, green, yellow, blue, magenta, cyan, white")
    print("  Bright Colors:")
    print("    - bright_red, bright_green, bright_yellow, bright_blue")
    print("    - bright_magenta, bright_cyan, bright_white")
    print("  Special Colors:")
    print("    - black, gray, grey")
    
    # Step 8: Color configuration options
    print("\n⚙️  Step 8: Color Configuration Options")
    print("You can customize these color settings:")
    print("  📊 Log Levels:")
    print("    - HYDRA_LOG_COLOR_DEBUG")
    print("    - HYDRA_LOG_COLOR_INFO")
    print("    - HYDRA_LOG_COLOR_WARNING")
    print("    - HYDRA_LOG_COLOR_ERROR")
    print("    - HYDRA_LOG_COLOR_CRITICAL")
    print("  🏷️  Layer Names:")
    print("    - HYDRA_LOG_LAYER_COLOR")
    print("  🚫 Disable Colors:")
    print("    - HYDRA_LOG_NO_COLOR=1")
    
    # Step 9: Color best practices
    print("\n🎯 Step 9: Color Best Practices")
    print("Color usage best practices:")
    print("  ✅ Use consistent colors across your application")
    print("  ✅ Choose colors that work well together")
    print("  ✅ Consider color-blind users (avoid red-green combinations)")
    print("  ✅ Use bright colors sparingly (they can be overwhelming)")
    print("  ✅ Test colors in different terminal environments")
    print("  ✅ Provide a way to disable colors for accessibility")
    
    # Step 10: Advanced color techniques
    print("\n🚀 Step 10: Advanced Color Techniques")
    print("Advanced color customization:")
    print("  🎨 Use ANSI codes for custom colors")
    print("  🌈 Create color themes for different environments")
    print("  📱 Adapt colors for different terminal types")
    print("  ♿ Ensure accessibility with color alternatives")
    
    # Step 11: Next steps
    print("\n🎯 Step 11: Next Steps")
    print("You've learned console color customization!")
    print("\nNext modules to try:")
    print("  📄 05_console_formats.py - Different output formats")
    
    print("\n🎉 Console colors completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_console_colors() 