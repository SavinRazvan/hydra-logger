#!/usr/bin/env python3
"""
Color Mode Control Example

This example demonstrates color mode control for different destinations:
- Console with colors enabled
- File with colors disabled
- Auto color detection
- Per-destination color control
"""

from hydra_logger import HydraLogger

def demo_color_mode_control():
    """Demonstrate color mode control for different destinations."""
    
    print("Color Mode Control Example")
    print("=" * 50)
    
    # Configuration with different color modes per destination
    config = {
        "layers": {
            "APP": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "console",
                        "format": "plain-text",
                        "level": "INFO",
                        "color_mode": "always"  # Force colors on console
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/app_plain.log",
                        "format": "plain-text",
                        "level": "INFO",
                        "color_mode": "never"   # No colors in file
                    }
                ]
            },
            "DEBUG": {
                "level": "DEBUG",
                "destinations": [
                    {
                        "type": "console",
                        "format": "plain-text",
                        "level": "DEBUG",
                        "color_mode": "auto"    # Auto-detect colors
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/debug_plain.log",
                        "format": "plain-text",
                        "level": "DEBUG",
                        "color_mode": "never"   # No colors in file
                    }
                ]
            }
        }
    }
    
    # Create logger with color mode control
    logger = HydraLogger(config=config)
    
    print("Color modes configured:")
    print("   - Console: color_mode='always' (forced colors)")
    print("   - File: color_mode='never' (no colors)")
    print("   - Debug console: color_mode='auto' (auto-detect)")
    
    print("\nLogging with color mode control:")
    
    # Log messages that will appear differently on console vs file
    logger.info("APP", "Application started")
    logger.info("APP", "User logged in", extra={"user_id": 12345})
    logger.warning("APP", "High memory usage detected", extra={"memory_mb": 512})
    logger.error("APP", "Database connection failed", extra={"error_code": 500})
    
    # Debug messages (different color mode)
    logger.debug("DEBUG", "Detailed debug information")
    logger.debug("DEBUG", "Configuration loaded", extra={"config_size": 1024})
    
    print("\nColor mode control example completed!")
    print("Check the following files:")
    print("   - examples/logs/app_plain.log (no colors)")
    print("   - examples/logs/debug_plain.log (no colors)")
    print("   - Console output (with colors)")
    print("\nNotice how console has colors but files are plain text")

if __name__ == "__main__":
    demo_color_mode_control() 