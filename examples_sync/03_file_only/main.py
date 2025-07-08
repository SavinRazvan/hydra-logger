#!/usr/bin/env python3
"""
📁 File-Only Logging Tutorial: Complete Learning Path

This guided tutorial walks you through file-only logging with Hydra-Logger,
from basic setup to advanced features and real applications.

Run this script to complete the entire learning path:
python main.py

Time: 45 minutes total
Difficulty: Progressive (Beginner to Intermediate)
"""

import os
import sys
import time
from pathlib import Path

# Add the modules directory to the path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

# Import all modules
from modules.01_basic_file import run_basic_file
from modules.02_file_config import run_file_config
from modules.03_file_levels import run_file_levels
from modules.04_file_formats import run_file_formats
from modules.05_file_organization import run_file_organization


def run_tutorial():
    """Run the complete file-only logging tutorial."""
    print("📁 File-Only Logging Tutorial")
    print("=" * 50)
    print("Complete learning path for file-only logging with Hydra-Logger")
    print()
    
    # Welcome and overview
    print("🎯 What You'll Learn:")
    print("  ✅ Basic file-only setup")
    print("  ✅ File configuration options")
    print("  ✅ Log levels for files")
    print("  ✅ Different file formats")
    print("  ✅ Professional log organization")
    print("  ✅ Real application examples")
    print()
    
    print("⏱️  Estimated Time: 45 minutes")
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
        ("01_basic_file", "Basic File Logging", run_basic_file),
        ("02_file_config", "File Configuration", run_file_config),
        ("03_file_levels", "File Log Levels", run_file_levels),
        ("04_file_formats", "File Formats", run_file_formats),
        ("05_file_organization", "File Organization", run_file_organization)
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
    print("Running the data processor example...")
    print()
    
    try:
        from examples.data_processor import run_data_processor
        run_data_processor()
        print("✅ Real application example completed!")
    except Exception as e:
        print(f"❌ Error in real application example: {e}")
    
    print()
    
    # Summary and next steps
    print("🎉 Tutorial Completed!")
    print("=" * 50)
    print("Congratulations! You've completed the file-only logging tutorial.")
    print()
    
    print("📊 What You've Learned:")
    print("  ✅ Basic file-only logging setup")
    print("  ✅ File configuration and customization")
    print("  ✅ Log level management for files")
    print("  ✅ Different file formats (text, JSON, CSV)")
    print("  ✅ Professional log organization")
    print("  ✅ Real application integration")
    print()
    
    print("📁 Generated Files:")
    print("Check the following directories for generated log files:")
    print("  📄 logs/ - Basic file logging")
    print("  📁 logs/config/ - Configuration examples")
    print("  📁 logs/levels/ - Log level examples")
    print("  📁 logs/formats/ - Format examples")
    print("  📁 logs/organized/ - Organization examples")
    print("  📁 logs/examples/ - Real application logs")
    print()
    
    print("🎯 Next Steps:")
    print("  1. Explore other examples in this directory")
    print("  2. Try console logging: 02_console_only")
    print("  3. Learn multi-layer logging: 05_multiple_layers")
    print("  4. Study log rotation: 06_rotation")
    print("  5. Read the main documentation for advanced features")
    print()
    
    print("🤝 Need Help?")
    print("  - Check the main README for comprehensive guides")
    print("  - Report issues on GitHub")
    print("  - Join community discussions")
    print()
    
    print("Happy File Logging! 🐉")


if __name__ == "__main__":
    run_tutorial() 