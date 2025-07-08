#!/usr/bin/env python3
"""
🧪 Test Setup: Verify simple configuration setup

This script tests that the simple configuration example is properly configured
and can run successfully.

Run this script to verify your setup:
python test_setup.py
"""

import os
import sys
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from hydra_logger import HydraLogger
        from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
        print("✅ Hydra-Logger imports successful")
        return True
    except ImportError as e:
        print(f"❌ Hydra-Logger import failed: {e}")
        return False


def test_modules():
    """Test that all modules can be imported."""
    print("\n📚 Testing module imports...")
    
    modules_dir = Path(__file__).parent / "modules"
    if not modules_dir.exists():
        print(f"❌ Modules directory not found: {modules_dir}")
        return False
    
    # Add modules directory to path
    sys.path.insert(0, str(modules_dir))
    
    module_files = [
        "01_basic_config.py",
        "02_yaml_config.py", 
        "03_toml_config.py",
        "04_env_config.py",
        "05_config_validation.py"
    ]
    
    for module_file in module_files:
        module_path = modules_dir / module_file
        if not module_path.exists():
            print(f"❌ Module file not found: {module_file}")
            return False
        
        try:
            module_name = module_file.replace(".py", "")
            __import__(module_name)
            print(f"✅ {module_file} imported successfully")
        except Exception as e:
            print(f"❌ Failed to import {module_file}: {e}")
            return False
    
    return True


def test_examples():
    """Test that example files exist."""
    print("\n💼 Testing example files...")
    
    examples_dir = Path(__file__).parent / "examples"
    if not examples_dir.exists():
        print(f"❌ Examples directory not found: {examples_dir}")
        return False
    
    example_files = [
        "config_manager.py"
    ]
    
    for example_file in example_files:
        example_path = examples_dir / example_file
        if not example_path.exists():
            print(f"❌ Example file not found: {example_file}")
            return False
        else:
            print(f"✅ {example_file} found")
    
    return True


def test_directories():
    """Test that required directories can be created."""
    print("\n📁 Testing directory creation...")
    
    test_dirs = [
        "logs",
        "logs/examples",
        "config_examples"
    ]
    
    for test_dir in test_dirs:
        try:
            os.makedirs(test_dir, exist_ok=True)
            print(f"✅ {test_dir} created/verified")
        except Exception as e:
            print(f"❌ Failed to create {test_dir}: {e}")
            return False
    
    return True


def test_basic_configuration():
    """Test basic configuration functionality."""
    print("\n📝 Testing basic configuration...")
    
    try:
        from hydra_logger import HydraLogger
        from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
        
        # Create a simple test configuration
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path="logs/test_setup.log",
                            format="text"
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        logger.info("TEST", "Test message from setup verification")
        
        # Check if file was created
        if os.path.exists("logs/test_setup.log"):
            print("✅ Basic configuration test successful")
            return True
        else:
            print("❌ Log file not created")
            return False
            
    except Exception as e:
        print(f"❌ Basic configuration test failed: {e}")
        return False


def test_yaml_configuration():
    """Test YAML configuration functionality."""
    print("\n📄 Testing YAML configuration...")
    
    try:
        import yaml
        
        # Create a simple YAML config
        yaml_config = {
            "layers": {
                "TEST": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "logs/test_yaml.log",
                            "format": "text"
                        }
                    ]
                }
            }
        }
        
        with open("config_examples/test.yaml", "w") as f:
            yaml.dump(yaml_config, f, default_flow_style=False, indent=2)
        
        # Test loading from YAML
        logger = HydraLogger.from_config("config_examples/test.yaml")
        logger.info("TEST", "Test message from YAML configuration")
        
        if os.path.exists("logs/test_yaml.log"):
            print("✅ YAML configuration test successful")
            return True
        else:
            print("❌ YAML log file not created")
            return False
            
    except Exception as e:
        print(f"❌ YAML configuration test failed: {e}")
        return False


def run_tests():
    """Run all tests."""
    print("🧪 Simple Configuration Setup Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Module Test", test_modules),
        ("Example Test", test_examples),
        ("Directory Test", test_directories),
        ("Basic Configuration Test", test_basic_configuration),
        ("YAML Configuration Test", test_yaml_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup is ready.")
        print("\n🚀 You can now run:")
        print("  python main.py - Complete tutorial")
        print("  python modules/01_basic_config.py - Start with basics")
        print("  python examples/config_manager.py - Real application")
    else:
        print("⚠️  Some tests failed. Please check the setup.")
        print("\n🔧 Common fixes:")
        print("  - Install Hydra-Logger: pip install hydra-logger")
        print("  - Install PyYAML: pip install pyyaml")
        print("  - Check Python version (3.7+)")
        print("  - Ensure write permissions in current directory")


if __name__ == "__main__":
    run_tests() 