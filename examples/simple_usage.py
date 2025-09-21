#!/usr/bin/env python3
"""
Simple usage example for Hydra Logger with automatic setup.

This example demonstrates:
- Automatic logs directory setup
- Using the example configuration template
- Creating custom configurations
- Basic logging operations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from hydra_logger import create_sync_logger
from hydra_logger.config import (
    load_config_from_configs_dir,
    get_custom_config,
    save_config,
    get_logs_manager
)


def main():
    """Simple usage example."""
    print("🚀 Hydra Logger - Simple Usage Example")
    print("=" * 50)
    
    # The logs directory structure is automatically created when you create a logger
    print("📁 Logs directory structure will be created automatically...")
    
    # Method 1: Use the example configuration template
    print("\n1️⃣ Using the example configuration template:")
    try:
        # Load the example configuration (automatically created)
        config = load_config_from_configs_dir("example_config")
        logger = create_sync_logger(config, name="example_app")
        
        # Log some messages
        logger.info("Application started")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        
        # Use custom layers
        logger.log("INFO", "Database connection established", layer="database")
        logger.log("DEBUG", "API request processed", layer="api")
        
        logger.close()
        print("✅ Example configuration test completed")
        
    except Exception as e:
        print(f"❌ Error with example config: {e}")
    
    # Method 2: Create a simple custom configuration
    print("\n2️⃣ Creating a simple custom configuration:")
    try:
        # Create a simple custom config
        custom_config = get_custom_config(
            default_level="INFO",
            console_enabled=True,
            file_enabled=True,
            file_path="my_app.log",
            file_format="json-lines"
        )
        
        # Save it to the _configs directory
        save_config(custom_config, "logs/_configs/simple_config.yaml")
        print("✅ Custom configuration saved to logs/_configs/simple_config.yaml")
        
        # Load and use it
        loaded_config = load_config_from_configs_dir("simple_config")
        logger = create_sync_logger(loaded_config, name="simple_app")
        
        logger.info("Simple app started")
        logger.warning("Simple warning")
        logger.error("Simple error")
        
        logger.close()
        print("✅ Simple custom configuration test completed")
        
    except Exception as e:
        print(f"❌ Error with custom config: {e}")
    
    # Method 3: Use default configuration (no setup needed)
    print("\n3️⃣ Using default configuration:")
    try:
        # Just create a logger with default config
        logger = create_sync_logger(name="default_app")
        
        logger.info("Default app started")
        logger.warning("Default warning")
        logger.error("Default error")
        
        logger.close()
        print("✅ Default configuration test completed")
        
    except Exception as e:
        print(f"❌ Error with default config: {e}")
    
    # Show the directory structure
    print("\n📁 Directory structure created:")
    manager = get_logs_manager()
    print(f"  - {manager.logs_dir}")
    print(f"  - {manager.configs_dir}")
    print(f"  - {manager.example_config_path}")
    
    # List available configurations
    configs = manager.list_available_configs()
    print(f"\n📄 Available configurations: {', '.join(configs)}")
    
    print("\n🎉 Simple usage example completed!")
    print("\n💡 Tips:")
    print("  - Check logs/_configs/example_config.yaml for comprehensive documentation")
    print("  - Create your own configs by copying and modifying the example")
    print("  - Use load_config_from_configs_dir('config_name') to load your configs")
    print("  - The logs directory structure is created automatically")


if __name__ == "__main__":
    main()

