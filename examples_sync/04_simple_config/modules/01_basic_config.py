#!/usr/bin/env python3
"""
⚙️ Basic Configuration: Simple configuration setup

What you'll learn:
- Simple configuration setup
- Basic configuration structure
- Configuration benefits
- Configuration best practices

Time: 10 minutes
Difficulty: Beginner
"""

import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def run_basic_config():
    """Step-by-step basic configuration guide."""
    print("⚙️ Basic Configuration")
    print("=" * 40)
    
    # Step 1: Understanding configuration
    print("\n📊 Step 1: Understanding Configuration")
    print("Why use configuration files:")
    print("  🔧 Flexibility - Easy to change logging behavior")
    print("  📝 Maintainability - Separate configuration from code")
    print("  🌍 Environment Support - Different configs for different environments")
    print("  📋 Version Control - Track configuration changes")
    print("  👥 Team Collaboration - Share configurations across team")
    
    # Step 2: Basic configuration structure
    print("\n📦 Step 2: Basic Configuration Structure")
    print("Creating a simple configuration...")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Create basic configuration
    config = LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/basic_config.log",
                        format="text"
                    ),
                    LogDestination(
                        type="console",
                        level="WARNING",
                        format="text"
                    )
                ]
            )
        }
    )
    
    print("✅ Basic configuration created!")
    print("   - Layer: APP")
    print("   - Level: INFO")
    print("   - Destinations: File + Console")
    print("   - File: logs/basic_config.log")
    print("   - Console: WARNING level only")
    
    # Step 3: Initialize logger with configuration
    print("\n📝 Step 3: Initialize Logger with Configuration")
    print("Setting up Hydra-Logger with configuration...")
    
    logger = HydraLogger(config)
    
    print("✅ Logger initialized with configuration!")
    
    # Step 4: Test configuration
    print("\n📝 Step 4: Test Configuration")
    print("Logging messages to test configuration...")
    
    logger.debug("APP", "Debug message - won't show (level too low)")
    logger.info("APP", "Info message - will show in file and console")
    logger.warning("APP", "Warning message - will show in file and console")
    logger.error("APP", "Error message - will show in file and console")
    
    print("✅ Configuration tested!")
    
    # Step 5: Configuration benefits explained
    print("\n💡 Step 5: Configuration Benefits")
    print("Benefits of using configuration:")
    print("  🔧 Easy Changes - Modify behavior without code changes")
    print("  📝 Separation of Concerns - Config separate from logic")
    print("  🌍 Environment Flexibility - Different configs per environment")
    print("  📋 Version Control - Track configuration changes")
    print("  👥 Team Sharing - Share configurations across team")
    print("  🧪 Testing - Test different configurations easily")
    
    # Step 6: Check generated files
    print("\n📁 Step 6: Check Generated Files")
    print("Files created by configuration:")
    
    log_file_path = "logs/basic_config.log"
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            print(f"   📄 {log_file_path}: {len(lines)} lines")
            if lines:
                print(f"   📝 Sample: {lines[0].strip()}")
    else:
        print(f"   ❌ {log_file_path}: Not found")
    
    # Step 7: Configuration structure explained
    print("\n🏗️ Step 7: Configuration Structure")
    print("Configuration components:")
    print("  📊 LoggingConfig - Main configuration container")
    print("  🏷️  Layers - Named logging layers (APP, DEBUG, etc.)")
    print("  📊 LogLayer - Configuration for a specific layer")
    print("  📍 LogDestination - Where logs go (file, console, etc.)")
    print("  📊 Level - Minimum log level (DEBUG, INFO, WARNING, ERROR)")
    print("  📄 Format - Output format (text, json, csv)")
    
    # Step 8: Configuration best practices
    print("\n🎯 Step 8: Configuration Best Practices")
    print("Configuration best practices:")
    print("  ✅ Use meaningful layer names")
    print("  ✅ Choose appropriate log levels")
    print("  ✅ Separate concerns (app, debug, errors)")
    print("  ✅ Use environment-specific configurations")
    print("  ✅ Validate configurations")
    print("  ✅ Document configuration options")
    
    # Step 9: Next steps
    print("\n🎯 Step 9: Next Steps")
    print("You've learned basic configuration!")
    print("\nNext modules to try:")
    print("  📄 02_yaml_config.py - YAML configuration files")
    print("  📄 03_toml_config.py - TOML configuration files")
    print("  🌍 04_env_config.py - Environment variable substitution")
    print("  ✅ 05_config_validation.py - Configuration validation")
    
    print("\n🎉 Basic configuration completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_basic_config() 