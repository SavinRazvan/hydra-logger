#!/usr/bin/env python3
"""
📄 TOML Configuration: TOML configuration files

What you'll learn:
- TOML configuration files
- Loading configuration from TOML files
- TOML configuration structure
- TOML configuration best practices

Time: 15 minutes
Difficulty: Beginner
"""

import os
import tomllib
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination


def create_toml_config():
    """Create example TOML configuration files."""
    os.makedirs("config_examples", exist_ok=True)
    
    # Basic TOML configuration
    basic_toml = """[layers.APP]
level = "INFO"
[[layers.APP.destinations]]
type = "file"
path = "logs/toml_config.log"
format = "text"

[[layers.APP.destinations]]
type = "console"
level = "WARNING"
format = "text"

[layers.DEBUG]
level = "DEBUG"
[[layers.DEBUG.destinations]]
type = "file"
path = "logs/debug_toml.log"
format = "text"
"""
    
    with open("config_examples/basic.toml", "w") as f:
        f.write(basic_toml)
    
    # Advanced TOML configuration
    advanced_toml = """[layers.APP]
level = "INFO"
[[layers.APP.destinations]]
type = "file"
path = "logs/app_toml.log"
format = "text"

[[layers.APP.destinations]]
type = "console"
level = "ERROR"
format = "json"

[layers.ERRORS]
level = "ERROR"
[[layers.ERRORS.destinations]]
type = "file"
path = "logs/errors_toml.log"
format = "text"

[layers.PERFORMANCE]
level = "INFO"
[[layers.PERFORMANCE.destinations]]
type = "file"
path = "logs/performance_toml.json"
format = "json"
"""
    
    with open("config_examples/advanced.toml", "w") as f:
        f.write(advanced_toml)


def run_toml_config():
    """Step-by-step TOML configuration guide."""
    print("📄 TOML Configuration")
    print("=" * 40)
    
    # Step 1: Understanding TOML configuration
    print("\n📊 Step 1: Understanding TOML Configuration")
    print("TOML configuration benefits:")
    print("  📝 Simple and readable format")
    print("  🏗️ Table-based structure")
    print("  🔧 Easy to parse")
    print("  📋 Minimal syntax")
    print("  👥 Great for configuration files")
    print("  🧪 Easy to validate")
    
    # Step 2: Create TOML configuration files
    print("\n📦 Step 2: Create TOML Configuration Files")
    print("Creating example TOML configuration files...")
    
    create_toml_config()
    
    print("✅ TOML configuration files created!")
    print("   📄 config_examples/basic.toml - Basic configuration")
    print("   📄 config_examples/advanced.toml - Advanced configuration")
    
    # Step 3: Load basic TOML configuration
    print("\n📝 Step 3: Load Basic TOML Configuration")
    print("Loading configuration from basic.toml...")
    
    try:
        logger = HydraLogger.from_config("config_examples/basic.toml")
        print("✅ Basic TOML configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load TOML configuration: {e}")
        return
    
    # Step 4: Test basic TOML configuration
    print("\n📝 Step 4: Test Basic TOML Configuration")
    print("Logging messages with TOML configuration...")
    
    logger.info("APP", "Application started with TOML config")
    logger.debug("DEBUG", "Debug information")
    logger.warning("APP", "Warning message")
    logger.error("APP", "Error message")
    
    print("✅ Basic TOML configuration tested!")
    
    # Step 5: Load advanced TOML configuration
    print("\n📝 Step 5: Load Advanced TOML Configuration")
    print("Loading configuration from advanced.toml...")
    
    try:
        advanced_logger = HydraLogger.from_config("config_examples/advanced.toml")
        print("✅ Advanced TOML configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load advanced TOML configuration: {e}")
        return
    
    # Step 6: Test advanced TOML configuration
    print("\n📝 Step 6: Test Advanced TOML Configuration")
    print("Logging messages with advanced TOML configuration...")
    
    advanced_logger.info("APP", "Application started with advanced TOML config")
    advanced_logger.error("ERRORS", "Error message to errors log")
    advanced_logger.info("PERFORMANCE", "Performance metric", cpu_usage=30, memory_mb=768)
    
    print("✅ Advanced TOML configuration tested!")
    
    # Step 7: TOML configuration structure
    print("\n🏗️ Step 7: TOML Configuration Structure")
    print("TOML configuration structure:")
    print("  📊 [layers.layer_name] - Layer configuration section")
    print("  📊 level = \"INFO\" - Log level setting")
    print("  📍 [[layers.layer_name.destinations]] - Destination array")
    print("  📄 type = \"file\" - Destination type")
    print("  📍 path = \"logs/file.log\" - File path")
    print("  📄 format = \"text\" - Output format")
    
    # Step 8: Check generated files
    print("\n📁 Step 8: Check Generated Files")
    print("Files created by TOML configurations:")
    
    files_to_check = [
        "logs/toml_config.log",
        "logs/debug_toml.log",
        "logs/app_toml.log",
        "logs/errors_toml.log",
        "logs/performance_toml.json"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                print(f"   📄 {file_path}: {len(lines)} lines")
        else:
            print(f"   ❌ {file_path}: Not found")
    
    # Step 9: TOML vs YAML comparison
    print("\n📊 Step 9: TOML vs YAML Comparison")
    print("TOML advantages:")
    print("  📝 Simpler syntax")
    print("  🔧 Easier to parse")
    print("  📋 Less ambiguous")
    print("  👥 Great for config files")
    print("  🧪 Built-in validation")
    print("  📊 Standard format")
    
    print("\nYAML advantages:")
    print("  📝 More flexible")
    print("  🏗️ Better for complex data")
    print("  📋 More widely used")
    print("  👥 Better tooling support")
    print("  🧪 More features")
    print("  📊 Better for documents")
    
    # Step 10: TOML best practices
    print("\n🎯 Step 10: TOML Best Practices")
    print("TOML configuration best practices:")
    print("  ✅ Use consistent naming")
    print("  ✅ Group related settings")
    print("  ✅ Use meaningful section names")
    print("  ✅ Add comments for clarity")
    print("  ✅ Validate configurations")
    print("  ✅ Document configuration options")
    
    # Step 11: Next steps
    print("\n🎯 Step 11: Next Steps")
    print("You've learned TOML configuration!")
    print("\nNext modules to try:")
    print("  🌍 04_env_config.py - Environment variable substitution")
    print("  ✅ 05_config_validation.py - Configuration validation")
    
    print("\n🎉 TOML configuration completed!")
    print("=" * 40)


if __name__ == "__main__":
    run_toml_config() 