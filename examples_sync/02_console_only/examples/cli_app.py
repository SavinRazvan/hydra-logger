#!/usr/bin/env python3
"""
💼 CLI Application: Real CLI application with console-only logging

What you'll learn:
- Console logging in real applications
- Interactive user input
- Error handling with console logging
- Performance monitoring with console output

Time: 10 minutes
Difficulty: Intermediate
"""

import time
import random
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def setup_logger():
    """Set up console-only logger for CLI application."""
    config = LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        level="INFO",
                        format="text"
                    )
                ]
            ),
            "USER": LogLayer(
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
            ),
            "PERF": LogLayer(
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
    
    return HydraLogger(config)


def process_command(logger, command):
    """Process a user command with comprehensive logging."""
    start_time = time.time()
    
    logger.info("USER", f"User entered command: {command}")
    
    try:
        if command.lower() == "quit":
            logger.info("APP", "User requested to quit")
            return False
        
        elif command.lower() == "error":
            logger.warning("APP", "User requested error simulation")
            raise ValueError("Simulated error for demonstration")
        
        elif command.lower() == "slow":
            logger.info("PERF", "User requested slow operation")
            logger.info("APP", "Starting slow operation...")
            time.sleep(2)  # Simulate slow processing
            logger.info("PERF", "Slow operation completed")
        
        elif command.lower() == "help":
            logger.info("APP", "User requested help")
            print("\n📚 Available Commands:")
            print("  - Type anything to process it")
            print("  - 'error' - Simulate an error")
            print("  - 'slow' - Simulate slow processing")
            print("  - 'help' - Show this help")
            print("  - 'quit' - Exit the application")
        
        else:
            logger.info("APP", f"Processing command: {command}")
            # Simulate some processing
            time.sleep(0.1)
            result = f"Processed: {command.upper()}"
            logger.info("APP", f"Command processed successfully: {result}")
            print(f"✅ {result}")
        
        processing_time = (time.time() - start_time) * 1000
        logger.info("PERF", f"Command processing time: {processing_time:.2f}ms")
        
        return True
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error("ERROR", f"Error processing command '{command}': {e}")
        logger.info("PERF", f"Error processing time: {processing_time:.2f}ms")
        print(f"❌ Error: {e}")
        return True


def main():
    """Main CLI application with console-only logging."""
    logger = setup_logger()
    
    logger.info("APP", "CLI Application started")
    logger.info("APP", "Console-only logging enabled")
    
    print("🐉 Hydra-Logger CLI Application")
    print("=" * 40)
    print("This application demonstrates console-only logging.")
    print("All output goes to the console - no files are created.")
    print("Type 'help' for available commands.")
    print()
    
    try:
        while True:
            try:
                command = input("🔧 Enter command: ").strip()
                
                if not command:
                    logger.warning("USER", "Empty command entered")
                    print("⚠️  Please enter a command")
                    continue
                
                if not process_command(logger, command):
                    break
                    
            except KeyboardInterrupt:
                logger.info("USER", "User interrupted with Ctrl+C")
                print("\n👋 Goodbye!")
                break
                
    except Exception as e:
        logger.critical("ERROR", f"Application crashed: {e}")
        print(f"💥 Application error: {e}")
    
    finally:
        logger.info("APP", "CLI Application shutting down")
        print("\n🎉 Application completed successfully!")
        print("📝 All logs were displayed in the console above.")


if __name__ == "__main__":
    main() 