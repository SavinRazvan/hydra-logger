#!/usr/bin/env python3
"""
📄 YAML Configuration: YAML configuration files

What you'll learn:
- YAML configuration files
- Loading configuration from files
- YAML configuration structure
- YAML configuration best practices

Time: 15 minutes
Difficulty: Beginner
"""

import os
import yaml
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def create_yaml_config():
    """Create example YAML configuration files."""
    os.makedirs("config_examples", exist_ok=True)
    
    # Basic YAML configuration
    basic_config = {
        "layers": {
            "APP": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "logs/yaml_config.log",
                        "format": "text"
                    },
                    {
                        "type": "console",
                        "level": "WARNING",
                        "format": "text"
                    }
                ]
            },
            "DEBUG": {
                "level": "DEBUG",
                "destinations": [
                    {
                        "type": "file",
                        "path": "logs/debug.log",
                        "format": "text"
                    }
                ]
            }
        }
    }
    
    with open("config_examples/basic.yaml", "w") as f:
        yaml.dump(basic_config, f, default_flow_style=False, indent=2)
    
    # Advanced YAML configuration
    advanced_config = {
        "layers": {
            "APP": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "logs/app.log",
                        "format": "text"
                    },
                    {
                        "type": "console",
                        "level": "ERROR",
                        "format": "json"
                    }
                ]
            },
            "ERRORS": {
                "level": "ERROR",
                "destinations": [
                    {
                        "type": "file",
                        "path": "logs/errors.log",
                        "format": "text"
                    }
                ]
            },
            "PERFORMANCE": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "file",
                        "path": "logs/performance.json",
                        "format": "json"
                    }
                ]
            }
        }
    }
    
    with open("config_examples/advanced.yaml", "w") as f:
        yaml.dump(advanced_config, f, default_flow_style=False, indent=2)


def run_yaml_config():
    """Step-by-step YAML configuration guide."""
    print("📄 YAML Configuration")
    print("=" * 40)
    
    # Step 1: Understanding YAML configuration
    print("\n📊 Step 1: Understanding YAML Configuration")
    print("YAML configuration benefits:")
    print("  📝 Human-readable format")
    print("  🏗️ Hierarchical structure")
    print("  🔧 Easy to modify")
    print("  📋 Version control friendly")
    print("  👥 Team collaboration")
    print("  🧪 Easy to test")
    
    # Step 2: Create YAML configuration files
    print("\n📦 Step 2: Create YAML Configuration Files")
    print("Creating example YAML configuration files...")
    
    create_yaml_config()
    
    print("✅ YAML configuration files created!")
    print("   📄 config_examples/basic.yaml - Basic configuration")
    print("   📄 config_examples/advanced.yaml - Advanced configuration")
    
    # Step 3: Load basic YAML configuration
    print("\n📝 Step 3: Load Basic YAML Configuration")
    print("Loading configuration from basic.yaml...")
    
    try:
        logger = HydraLogger.from_config("config_examples/basic.yaml")
        print("✅ Basic YAML configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load YAML configuration: {e}")
        return
    
    # Step 4: Test basic YAML configuration
    print("\n📝 Step 4: Test Basic YAML Configuration")
    print("Logging messages with YAML configuration...")
    
    logger.info("APP", "Application started with YAML config")
    logger.debug("DEBUG", "Debug information")
    logger.warning("APP", "Warning message")
    logger.error("APP", "Error message")
    
    print("✅ Basic YAML configuration tested!")
    
    # Step 5: Load advanced YAML configuration
    print("\n📝 Step 5: Load Advanced YAML Configuration")
    print("Loading configuration from advanced.yaml...")
    
    try:
        advanced_logger = HydraLogger.from_config("config_examples/advanced.yaml")
        print("✅ Advanced YAML configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load advanced YAML configuration: {e}")
        return
    
    # Step 6: Test advanced YAML configuration
    print("\n📝 Step 6: Test Advanced YAML Configuration")
    print("Logging messages with advanced YAML configuration...")
    
    advanced_logger.info("APP", "Application started with advanced YAML config")
    advanced_logger.error("ERRORS", "Error message to errors log")
    advanced_logger.info("PERFORMANCE", "Performance metric", cpu_usage=25, memory_mb=512)
    
    print("✅ Advanced YAML configuration tested!")
    
    # Step 7: YAML configuration structure
    print("\n🏗️ Step 7: YAML Configuration Structure")
    print("YAML configuration structure:")
    print("  📊 layers - Main configuration section")
    print("  🏷️  layer_name - Named logging layer")
    print("  📊 level - Minimum log level")
    print("  📍 destinations - Where logs go")
    print("  📄 type - Destination type (file, console)")
    print("  📍 path - File path for file destinations")
    print("  📄 format - Output format (text, json, csv)")
    
    # Step 8: Check generated files
    print("\n📁 Step 8: Check Generated Files")
    print("Files created by YAML configurations:")
    
    files_to_check = [
        "logs/yaml_config.log",
        "logs/debug.log",
        "logs/app.log",
        "logs/errors.log",
        "logs/performance.json"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(f"   📄 {file_path}: {len(lines)} lines")
        else:
            print(f"   ❌ {file_path}: Not found")
    
    # Step 9: YAML configuration benefits
    print("\n💡 Step 9: YAML Configuration Benefits")
    print("Benefits of YAML configuration:")
    print("  📝 Readable - Easy to read and understand")
    print("  🔧 Flexible - Easy to modify and extend")
    print("  📋 Structured - Clear hierarchical structure")
    print("  👥 Collaborative - Easy for teams to work with")
    print("  🧪 Testable - Easy to test different configurations")
    print("  📊 Versionable - Easy to track changes")
    
    # Step 10: YAML best practices
    print("\n🎯 Step 10: YAML Best Practices")
    print("YAML configuration best practices:")
    print("  ✅ Use consistent indentation")
    print("  ✅ Use meaningful layer names")
    print("  ✅ Group related configurations")
    print("  ✅ Use comments for clarity")
    print("  ✅ Validate configurations")
    print("  ✅ Document configuration options")
    
    # Step 11: Next steps
    print("\n🎯 Step 11: Next Steps")
    print("You've learned YAML configuration!")
    print("\nNext modules to try:")
    print("  📄 03_toml_config.py - TOML configuration files")
    print("  🌍 04_env_config.py - Environment variable substitution")
    print("  ✅ 05_config_validation.py - Configuration validation")
    
    print("\n🎉 YAML configuration completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_yaml_config() 