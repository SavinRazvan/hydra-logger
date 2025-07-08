#!/usr/bin/env python3
"""
Basic HydraLogger Usage Example

This example demonstrates the simplest possible usage of HydraLogger.
Zero configuration required - it just works!
"""

from hydra_logger import HydraLogger


def main():
    print("=== Basic HydraLogger Usage ===")
    print("Zero configuration required - it just works!\n")
    
    # Create logger with default configuration
    logger = HydraLogger()
    
    # Centralized logging (no layers)
    logger.info("Application started")
    logger.debug("Configuration loaded")
    logger.warning("High memory usage detected")
    logger.error("Authentication failed")
    logger.critical("System shutdown initiated")
    
    print("\n=== Custom Layer Names ===")
    # Custom layer names (your choice)
    logger.info("FRONTEND", "User interface updated")
    logger.info("BACKEND", "API endpoint called")
    logger.info("DATABASE", "Query executed")
    logger.info("PAYMENT", "Payment processed")
    
    print("\n✅ Basic example completed!")
    print("Check the console output above to see the logs.")


if __name__ == "__main__":
    main() 