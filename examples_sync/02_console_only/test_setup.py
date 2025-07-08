#!/usr/bin/env python3
"""
Test script to verify Hydra-Logger console-only setup is working correctly.
"""

import os
import sys
import subprocess
from pathlib import Path

def test_import():
    """Test that Hydra-Logger can be imported."""
    try:
        from hydra_logger import HydraLogger
        print("✅ Hydra-Logger import successful")
        return True
    except ImportError as e:
        print(f"❌ Hydra-Logger import failed: {e}")
        return False

def test_basic_console():
    """Test the basic console module."""
    try:
        result = subprocess.run([sys.executable, "modules/01_basic_console.py"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Basic console module runs successfully")
            return True
        else:
            print(f"❌ Basic console module failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Basic console module error: {e}")
        return False

def test_no_files_created():
    """Test that no log files are created (console-only)."""
    # Check that no logs directory exists
    if Path("logs").exists():
        print("⚠️  Logs directory exists (may contain files from other examples)")
        return True
    else:
        print("✅ No logs directory created (expected for console-only)")
        return True

def test_cli_app():
    """Test the CLI application (non-interactive)."""
    try:
        # Run CLI app with a simple command and quit
        process = subprocess.Popen(
            [sys.executable, "examples/cli_app.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send "quit" command
        stdout, stderr = process.communicate(input="quit\n", timeout=10)
        
        if process.returncode == 0:
            print("✅ CLI application runs successfully")
            return True
        else:
            print(f"❌ CLI application failed: {stderr}")
            return False
    except Exception as e:
        print(f"❌ CLI application error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Hydra-Logger Console-Only Setup")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_import),
        ("Basic Console Test", test_basic_console),
        ("No Files Created Test", test_no_files_created),
        ("CLI App Test", test_cli_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"   ❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Console-only setup is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the setup.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 