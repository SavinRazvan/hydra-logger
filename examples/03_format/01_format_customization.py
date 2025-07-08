#!/usr/bin/env python3
"""
Format Customization Demo

This example demonstrates the new format customization features:
- Custom date/time formats
- Custom logger name formats
- Custom message formats
- Color mode control
- Environment variable support
"""

import os
from hydra_logger import HydraLogger

def demo_format_customization():
    """Demonstrate format customization features."""
    
    print("🎨 Hydra-Logger Format Customization Demo")
    print("=" * 50)
    
    # Example 1: Basic format customization
    print("\n1️⃣ Basic Format Customization:")
    logger1 = HydraLogger(
        date_format="%Y-%m-%d %H:%M:%S",
        logger_name_format="%(name)s",
        message_format="%(levelname)s - %(message)s"
    )
    
    logger1.info("FRONTEND", "Custom format message")
    
    # Example 2: Color mode control
    print("\n2️⃣ Color Mode Control:")
    config = {
        "layers": {
            "FRONTEND": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "console",
                        "format": "plain-text",
                        "level": "INFO",
                        "color_mode": "always"  # Force colors
                    }
                ]
            }
        }
    }
    
    logger2 = HydraLogger(config=config)
    logger2.info("FRONTEND", "Forced color mode")
    
    # Example 3: Environment variable support
    print("\n3️⃣ Environment Variable Support:")
    # Set environment variables
    os.environ["HYDRA_LOG_DATE_FORMAT"] = "%Y-%m-%d %H:%M:%S"
    os.environ["HYDRA_LOG_LOGGER_NAME_FORMAT"] = "%(name)s"
    os.environ["HYDRA_LOG_MESSAGE_FORMAT"] = "%(levelname)s - %(message)s"
    
    logger3 = HydraLogger()  # Uses environment variables
    logger3.info("BACKEND", "Environment variable format")
    
    # Example 4: No colors for files
    print("\n4️⃣ File Output (No Colors):")
    config_no_colors = {
        "layers": {
            "DATABASE": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "examples/logs/no_colors.log",
                        "format": "plain-text",
                        "level": "INFO",
                        "color_mode": "never"  # No colors for files
                    }
                ]
            }
        }
    }
    
    logger4 = HydraLogger(config=config_no_colors)
    logger4.info("DATABASE", "File output without colors")
    
    # Example 5: Multiple destinations with different color modes
    print("\n5️⃣ Multiple Destinations:")
    config_multi = {
        "layers": {
            "PAYMENT": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "console",
                        "format": "plain-text",
                        "level": "INFO",
                        "color_mode": "always"  # Colored console
                    },
                    {
                        "type": "file",
                        "path": "examples/logs/plain.log",
                        "format": "plain-text",
                        "level": "INFO",
                        "color_mode": "never"  # Plain file
                    }
                ]
            }
        }
    }
    
    logger5 = HydraLogger(config=config_multi)
    logger5.info("PAYMENT", "Multiple destinations with different color modes")
    
    print("\n✅ Format customization demo completed!")
    print("Check the log files in examples/logs/ for file output examples.")

if __name__ == "__main__":
    demo_format_customization() 