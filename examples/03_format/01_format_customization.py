#!/usr/bin/env python3
"""
Format Customization Demo

This example demonstrates the format customization features:
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
    
    print("Hydra-Logger Format Customization Demo")
    print("=" * 50)
    
    # Create logs directory if it doesn't exist
    os.makedirs("examples/logs", exist_ok=True)
    
    # Example 1: Basic format customization
    print("\n1. Basic Format Customization:")
    logger1 = HydraLogger(
        date_format="%Y-%m-%d %H:%M:%S",
        logger_name_format="%(name)s",
        message_format="%(levelname)s - %(message)s"
    )
    
    logger1.info("Custom format message", "FRONTEND")
    
    # Example 2: Color mode control
    print("\n2. Color Mode Control:")
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
    logger2.info("Forced color mode", "FRONTEND")
    
    # Example 3: Environment variable support
    print("\n3. Environment Variable Support:")
    # Set environment variables
    os.environ["HYDRA_LOG_DATE_FORMAT"] = "%Y-%m-%d %H:%M:%S"
    os.environ["HYDRA_LOG_LOGGER_NAME_FORMAT"] = "%(name)s"
    os.environ["HYDRA_LOG_MESSAGE_FORMAT"] = "%(levelname)s - %(message)s"
    
    logger3 = HydraLogger()  # Uses environment variables
    logger3.info("Environment variable format", "BACKEND")
    
    # Example 4: No colors for files
    print("\n4. File Output (No Colors):")
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
    logger4.info("File output without colors", "DATABASE")
    
    # Example 5: Multiple destinations with different color modes
    print("\n5. Multiple Destinations:")
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
    logger5.info("Multiple destinations with different color modes", "PAYMENT")
    
    print("\nFormat customization demo completed!")
    print("Check the log files in examples/logs/ for file output examples.")

if __name__ == "__main__":
    demo_format_customization() 