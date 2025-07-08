#!/usr/bin/env python3
"""
Hydra-Logger Console-Only Logging - Progressive Learning Path

This is the main entry point for the console-only logging tutorial.
Run this to learn console-only logging with Hydra-Logger!
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    """Print a beautiful header for the tutorial."""
    print("🐉" + "="*60 + "🐉")
    print("        HYDRA-LOGGER CONSOLE-ONLY LOGGING TUTORIAL")
    print("🐉" + "="*60 + "🐉")
    print()

def print_step(step, title, description):
    """Print a formatted step."""
    print(f"📚 Step {step}: {title}")
    print(f"   {description}")
    print()

def run_module(module_path):
    """Run a module and return success status."""
    try:
        result = subprocess.run([sys.executable, module_path], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {module_path} completed successfully!")
            return True
        else:
            print(f"❌ {module_path} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {module_path} timed out")
        return False
    except Exception as e:
        print(f"❌ {module_path} error: {e}")
        return False

def main():
    """Main tutorial function."""
    print_header()
    
    print("🎯 Welcome to Hydra-Logger Console-Only Logging!")
    print("This tutorial will teach you console-only logging from basics to advanced.")
    print()
    
    # Check if we're in the right directory
    if not Path("modules").exists():
        print("❌ Error: Please run this from the 02_console_only directory")
        print("   cd examples_sync/02_console_only")
        print("   python main.py")
        return
    
    print("🚀 Starting Console-Only Learning Path...")
    print()
    
    # Step 1: Basic Console Logging
    print_step(1, "Basic Console Logging", "Get console-only logging working in 5 minutes")
    if run_module("modules/01_basic_console.py"):
        print("   📁 No files created - all output goes to console!")
        print()
    
    # Step 2: Console Configuration
    print_step(2, "Console Configuration", "Configure console output options")
    if run_module("modules/02_console_config.py"):
        print("   📁 Learn different console configuration options!")
        print()
    
    # Step 3: Console Log Levels
    print_step(3, "Console Log Levels", "Different log levels for console")
    if run_module("modules/03_console_levels.py"):
        print("   📁 Understand level filtering and management!")
        print()
    
    # Step 4: Console Colors
    print_step(4, "Console Colors", "Custom colors and visual appeal")
    if run_module("modules/04_console_colors.py"):
        print("   📁 See beautiful colored output in action!")
        print()
    
    # Step 5: Console Formats
    print_step(5, "Console Formats", "Different output formats (text, JSON, CSV, syslog)")
    if run_module("modules/05_console_formats.py"):
        print("   📁 Explore different output formats!")
        print()
    
    # Step 6: Real Application
    print_step(6, "Real Application", "Interactive CLI application with console logging")
    if run_module("examples/cli_app.py"):
        print("   📁 See console logging in a real application!")
        print()
    
    print("🎉 Tutorial Complete!")
    print()
    print("📚 What you've learned:")
    print("   ✅ Console-only logging setup")
    print("   ✅ Console configuration options")
    print("   ✅ Log level management")
    print("   ✅ Color customization")
    print("   ✅ Different output formats")
    print("   ✅ Real application integration")
    print()
    print("🚀 Next Steps:")
    print("   1. Explore other examples in examples_sync/")
    print("   2. Try file-only logging (03_file_only)")
    print("   3. Learn multi-layer logging (05_multiple_layers)")
    print("   4. Read the main documentation for advanced features")
    print()
    print("🐉 Happy Console Logging!")

if __name__ == "__main__":
    main() 