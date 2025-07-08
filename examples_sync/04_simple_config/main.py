#!/usr/bin/env python3
"""
⚙️ Simple Configuration Tutorial: Complete Learning Path

This guided tutorial walks you through simple configuration with Hydra-Logger,
from basic setup to advanced features and real applications.

Run this script to complete the entire learning path:
python main.py

Time: 60 minutes total
Difficulty: Progressive (Beginner to Intermediate)
"""

import os
import sys
import time
from pathlib import Path

# Add the modules directory to the path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

# Import all modules
from modules.01_basic_config import run_basic_config
from modules.02_yaml_config import run_yaml_config
from modules.03_toml_config import run_toml_config
from modules.04_env_config import run_env_config
from modules.05_config_validation import run_config_validation


def run_tutorial():
    """Run the complete simple configuration tutorial."""
    print("⚙️ Simple Configuration Tutorial")
    print("=" * 50)
    print("Complete learning path for simple configuration with Hydra-Logger")
    print()
    
    # Welcome and overview
    print("🎯 What You'll Learn:")
    print("  ✅ Basic configuration setup")
    print("  ✅ YAML configuration files")
    print("  ✅ TOML configuration files")
    print("  ✅ Environment variable concepts")
    print("  ✅ Configuration validation")
    print("  ✅ Real application examples")
    print()
    
    print("⏱️  Estimated Time: 60 minutes")
    print("📚 Difficulty: Progressive (Beginner to Intermediate)")
    print()
    
    # Check prerequisites
    print("🔍 Checking Prerequisites...")
    try:
        from hydra_logger import HydraLogger
        from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
        print("✅ Hydra-Logger is available")
    except ImportError as e:
        print(f"❌ Hydra-Logger not found: {e}")
        print("Please install Hydra-Logger first:")
        print("  pip install hydra-logger")
        return
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    print("✅ Logs directory ready")
    print()
    
    # Run modules progressively
    modules = [
        ("01_basic_config", "Basic Configuration", run_basic_config),
        ("02_yaml_config", "YAML Configuration", run_yaml_config),
        ("03_toml_config", "TOML Configuration", run_toml_config),
        ("04_env_config", "Environment Configuration", run_env_config),
        ("05_config_validation", "Configuration Validation", run_config_validation)
    ]
    
    for i, (module_name, title, module_func) in enumerate(modules, 1):
        print(f"📚 Module {i}/{len(modules)}: {title}")
        print("-" * 40)
        
        try:
            module_func()
            print(f"✅ {title} completed successfully!")
        except Exception as e:
            print(f"❌ Error in {title}: {e}")
            print("Continuing with next module...")
        
        print()
        
        # Pause between modules (except for the last one)
        if i < len(modules):
            print("⏸️  Pausing 3 seconds before next module...")
            time.sleep(3)
            print()
    
    # Run real application example
    print("💼 Real Application Example")
    print("-" * 40)
    print("Running the configuration manager example...")
    print()
    
    try:
        from examples.config_manager import run_config_manager
        run_config_manager()
        print("✅ Real application example completed!")
    except Exception as e:
        print(f"❌ Error in real application example: {e}")
    
    print()
    
    # Summary and next steps
    print("🎉 Tutorial Completed!")
    print("=" * 50)
    print("Congratulations! You've completed the simple configuration tutorial.")
    print()
    
    print("📊 What You've Learned:")
    print("  ✅ Basic configuration setup")
    print("  ✅ YAML and TOML configuration files")
    print("  ✅ Environment variable concepts")
    print("  ✅ Configuration validation")
    print("  ✅ Configuration management")
    print("  ✅ Real application integration")
    print()
    
    print("📁 Generated Files:")
    print("Check the following directories for generated files:")
    print("  📄 logs/ - Basic configuration logs")
    print("  📁 logs/config/ - Configuration examples")
    print("  📁 logs/levels/ - Log level examples")
    print("  📁 logs/formats/ - Format examples")
    print("  📁 logs/organized/ - Organization examples")
    print("  📁 logs/examples/ - Real application logs")
    print("  📁 config_examples/ - Configuration files")
    print()
    
    print("🎯 Next Steps:")
    print("  1. Explore other examples in this directory")
    print("  2. Try file-only logging: 03_file_only")
    print("  3. Learn multi-layer logging: 05_multiple_layers")
    print("  4. Study log rotation: 06_rotation")
    print("  5. Read the main documentation for advanced features")
    print()
    
    print("🤝 Need Help?")
    print("  - Check the main README for comprehensive guides")
    print("  - Report issues on GitHub")
    print("  - Join community discussions")
    print()
    
    print("Happy Configuration! 🐉")


if __name__ == "__main__":
    run_tutorial() 