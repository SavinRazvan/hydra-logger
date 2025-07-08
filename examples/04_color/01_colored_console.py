#!/usr/bin/env python3
"""
Colored Console Output Example

This example demonstrates how HydraLogger automatically handles
colored console output based on terminal capabilities.
"""

import os
from hydra_logger import HydraLogger


def main():
    print("=== Colored Console Output Example ===")
    print("HydraLogger automatically detects terminal support and applies colors.\n")
    
    # Create logger with default configuration
    logger = HydraLogger()
    
    # Check what handlers and formatters are being used
    for layer_name, layer_logger in logger._layers.items():
        for handler in layer_logger.handlers:
        print(f"Handler: {type(handler)} | Formatter: {type(handler.formatter)}")
    
    print("\nLogging with forced color output:")
    
    # Log messages with different levels
    logger.debug("DEBUG", "This is a debug message")
    logger.info("DEFAULT", "This is an info message")
    logger.warning("DEFAULT", "This is a warning message")
    logger.error("DEFAULT", "This is an error message")
    logger.critical("DEFAULT", "This is a critical message")
    
    print("\n✅ Colored console example completed!")
    print("Notice how different log levels have different colors.")


if __name__ == "__main__":
    main() 