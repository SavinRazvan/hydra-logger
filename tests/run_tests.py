#!/usr/bin/env python3
"""
Test runner for the modular test structure.

This script runs tests from the organized structure:
- Unit tests by module
- Integration tests
- Registry tests
"""

import sys
import os
import subprocess

def test_imports():
    """Test that all modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import hydra_logger
        print("✅ Main package import OK")
    except ImportError as e:
        print(f"❌ Main package import failed: {e}")
        return False
    
    try:
        from hydra_logger.core.logger import HydraLogger
        print("✅ Core logger import OK")
    except ImportError as e:
        print(f"❌ Core logger import failed: {e}")
        return False
    
    try:
        from hydra_logger.core.constants import LOG_LEVELS
        print("✅ Constants import OK")
    except ImportError as e:
        print(f"❌ Constants import failed: {e}")
        return False
    
    return True

def run_unit_tests():
    """Run unit tests by directory."""
    print("\n🔍 Running unit tests...")
    
    test_dirs = [
        "tests/unit/core",
        "tests/unit/config", 
        "tests/unit/plugins",
        "tests/unit/data_protection",
        "tests/unit/magic",
        "tests/unit/async"
    ]
    
    results = {}
    
    for test_dir in test_dirs:
        if not os.path.exists(test_dir):
            print(f"⚠️  Directory {test_dir} does not exist, skipping")
            results[test_dir] = "SKIP"
            continue
            
        try:
            print(f"\n📋 Testing {test_dir}...")
            result = subprocess.run([
                sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✅ {test_dir} tests passed")
                results[test_dir] = "PASS"
            else:
                print(f"❌ {test_dir} tests failed")
                print(f"Error: {result.stderr}")
                results[test_dir] = "FAIL"
                
        except Exception as e:
            print(f"❌ {test_dir} execution failed: {e}")
            results[test_dir] = "ERROR"
    
    return results

def run_integration_tests():
    """Run integration tests."""
    print("\n🔍 Running integration tests...")
    
    if not os.path.exists("tests/integration"):
        print("⚠️  Integration tests directory does not exist, skipping")
        return "SKIP"
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/integration", "-v"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Integration tests passed")
            return "PASS"
        else:
            print(f"❌ Integration tests failed: {result.stderr}")
            return "FAIL"
    except Exception as e:
        print(f"❌ Integration tests execution failed: {e}")
        return "ERROR"

def run_registry_tests():
    """Run registry tests."""
    print("\n🔍 Running registry tests...")
    
    if not os.path.exists("tests/registry"):
        print("⚠️  Registry tests directory does not exist, skipping")
        return "SKIP"
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/registry", "-v"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Registry tests passed")
            return "PASS"
        else:
            print(f"❌ Registry tests failed: {result.stderr}")
            return "FAIL"
    except Exception as e:
        print(f"❌ Registry tests execution failed: {e}")
        return "ERROR"

def run_coverage_tests():
    """Run tests with coverage."""
    print("\n🔍 Running coverage tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/",
            "--cov=hydra_logger",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-v"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Coverage tests completed")
            # Extract coverage info
            if "TOTAL" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "TOTAL" in line:
                        print(f"📊 Coverage: {line}")
                        break
            return "PASS"
        else:
            print(f"❌ Coverage tests failed: {result.stderr}")
            return "FAIL"
    except Exception as e:
        print(f"❌ Coverage tests execution failed: {e}")
        return "ERROR"

def check_test_discovery():
    """Check that pytest can discover all tests."""
    print("\n🔍 Checking test discovery...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Count test items
            lines = result.stdout.split('\n')
            test_count = 0
            for line in lines:
                if "::test_" in line:
                    test_count += 1
            
            print(f"✅ Test discovery successful: {test_count} tests found")
            return True
        else:
            print(f"❌ Test discovery failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Test discovery execution failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Hydra Logger Tests - Modular Structure")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed. Cannot proceed.")
        return 1
    
    # Check test discovery
    if not check_test_discovery():
        print("❌ Test discovery failed. Cannot proceed.")
        return 1
    
    # Run unit tests
    unit_results = run_unit_tests()
    
    # Run integration tests
    integration_result = run_integration_tests()
    
    # Run registry tests
    registry_result = run_registry_tests()
    
    # Run coverage tests
    coverage_result = run_coverage_tests()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    # Unit test results
    print("\n🔧 Unit Tests:")
    for test_dir, result in unit_results.items():
        if result == "PASS":
            status = "✅ PASS"
        elif result == "FAIL":
            status = "❌ FAIL"
        elif result == "SKIP":
            status = "⚠️ SKIP"
        else:
            status = "⚠️ ERROR"
        print(f"  {test_dir}: {status}")
    
    # Integration tests
    if integration_result == "PASS":
        print(f"\n🔗 Integration Tests: ✅ PASS")
    elif integration_result == "FAIL":
        print(f"\n🔗 Integration Tests: ❌ FAIL")
    else:
        print(f"\n🔗 Integration Tests: ⚠️ SKIP")
    
    # Registry tests
    if registry_result == "PASS":
        print(f"📋 Registry Tests: ✅ PASS")
    elif registry_result == "FAIL":
        print(f"📋 Registry Tests: ❌ FAIL")
    else:
        print(f"📋 Registry Tests: ⚠️ SKIP")
    
    # Coverage tests
    if coverage_result == "PASS":
        print(f"📊 Coverage Tests: ✅ PASS")
    elif coverage_result == "FAIL":
        print(f"📊 Coverage Tests: ❌ FAIL")
    else:
        print(f"📊 Coverage Tests: ⚠️ ERROR")
    
    # Overall result
    all_results = list(unit_results.values()) + [integration_result, registry_result, coverage_result]
    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r == "PASS")
    skipped_tests = sum(1 for r in all_results if r == "SKIP")
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} test suites passed ({skipped_tests} skipped)")
    
    if passed_tests == total_tests - skipped_tests:
        print("🎉 All available tests passed! Your modular structure is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 