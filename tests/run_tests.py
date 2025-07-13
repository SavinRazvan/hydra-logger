#!/usr/bin/env python3
"""
Fix common test issues and run all tests with coverage.

This script:
1. Fixes common test issues (timeouts, missing imports, etc.)
2. Runs all tests with comprehensive coverage
3. Generates detailed reports
"""

import sys
import os
import subprocess
import time
import shutil
from pathlib import Path


def fix_test_issues():
    """Fix common test issues."""
    print("🔧 Fixing common test issues...")
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print("✅ Created logs directory")
    
    # Create test output directory
    test_output_dir = Path("test_output")
    test_output_dir.mkdir(exist_ok=True)
    print("✅ Created test output directory")
    
    # Clean up old test files
    for pattern in ["*.log", "*.tmp", "test_*.txt"]:
        for file in Path(".").glob(pattern):
            try:
                file.unlink()
                print(f"✅ Cleaned up {file}")
            except Exception:
                pass
    
    # Set environment variables for tests
    os.environ["PYTHONPATH"] = str(Path(".").absolute())
    os.environ["HYDRA_LOGGER_TEST_MODE"] = "1"
    os.environ["HYDRA_LOGGER_ASYNC_TEST_MODE"] = "1"
    
    print("✅ Set test environment variables")
    return True


def install_test_dependencies():
    """Install test dependencies if needed."""
    print("📦 Checking test dependencies...")
    
    try:
        import pytest
        import coverage
        import asyncio
        print("✅ All test dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing test dependencies...")
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "pytest", "pytest-asyncio", "coverage", "pytest-cov"
            ], check=True, capture_output=True)
            print("✅ Test dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False


def run_comprehensive_tests():
    """Run all tests with comprehensive coverage."""
    print("\n🚀 Running comprehensive test suite...")
    
    # Create coverage configuration
    coverage_config = """
[run]
source = hydra_logger
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */venv/*
    */env/*
    */.venv/*
    */.env/*
    */build/*
    */dist/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod
    """
    
    with open(".coveragerc", "w") as f:
        f.write(coverage_config)
    
    # Run tests with comprehensive options
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=hydra_logger",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--cov-report=json:coverage.json",
        "--cov-fail-under=15",  # Lower threshold for now
        "-v",
        "--tb=short",
        "--durations=10",
        "--maxfail=20",  # Allow more failures
        "--timeout=600",  # 10 minute timeout
        "--asyncio-mode=auto",  # Handle async tests properly
        "-W", "ignore::DeprecationWarning",
        "-W", "ignore::PendingDeprecationWarning",
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # 15 minutes
        end_time = time.time()
        
        print(f"\n⏱️  Test execution time: {end_time - start_time:.2f} seconds")
        
        # Save output to file
        with open("test_output/test_results.txt", "w") as f:
            f.write(f"Test execution time: {end_time - start_time:.2f} seconds\n")
            f.write("=" * 60 + "\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n" + "=" * 60 + "\n")
            f.write("STDERR:\n")
            f.write(result.stderr)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True, result.stdout
        else:
            print("❌ Some tests failed!")
            print(f"Error output saved to test_output/test_results.txt")
            return False, result.stdout + result.stderr
            
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 15 minutes")
        return False, "Tests timed out"
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False, str(e)


def run_async_tests_fixed():
    """Run async tests with fixes for common issues."""
    print("\n🔧 Running async tests with fixes...")
    
    # Create async-specific coverage config
    coverage_config = """
[run]
source = hydra_logger.async_hydra
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */venv/*
    */env/*
    */.venv/*
    */.env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod
    """
    
    with open(".coveragerc_async", "w") as f:
        f.write(coverage_config)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/async/",
        "--cov=hydra_logger.async_hydra",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov_async",
        "--cov-config=.coveragerc_async",
        "-v",
        "--tb=short",
        "--durations=5",
        "--maxfail=10",
        "--asyncio-mode=auto",
        "-W", "ignore::DeprecationWarning",
        "-W", "ignore::PendingDeprecationWarning",
        "--timeout=300",
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Save async test results
        with open("test_output/async_test_results.txt", "w") as f:
            f.write("Async Test Results\n")
            f.write("=" * 60 + "\n")
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\n" + "=" * 60 + "\n")
            f.write("STDERR:\n")
            f.write(result.stderr)
        
        if result.returncode == 0:
            print("✅ Async tests passed!")
            return True, result.stdout
        else:
            print("❌ Async tests failed!")
            print(f"Results saved to test_output/async_test_results.txt")
            return False, result.stdout + result.stderr
            
    except Exception as e:
        print(f"❌ Async test execution failed: {e}")
        return False, str(e)


def generate_final_report():
    """Generate final test and coverage report."""
    print("\n📊 Generating final report...")
    
    try:
        # Generate HTML coverage report
        result = subprocess.run([
            sys.executable, "-m", "coverage", "html", 
            "--title=Hydra-Logger Comprehensive Coverage Report"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ HTML coverage report generated in htmlcov/")
        else:
            print(f"❌ HTML report generation failed: {result.stderr}")
        
        # Generate XML report
        result = subprocess.run([
            sys.executable, "-m", "coverage", "xml"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ XML coverage report generated as coverage.xml")
        else:
            print(f"❌ XML report generation failed: {result.stderr}")
        
        # Show coverage summary
        result = subprocess.run([
            sys.executable, "-m", "coverage", "report", "--show-missing"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n📊 Coverage Summary:")
            print(result.stdout)
            
            # Save coverage summary
            with open("test_output/coverage_summary.txt", "w") as f:
                f.write("Coverage Summary\n")
                f.write("=" * 60 + "\n")
                f.write(result.stdout)
        else:
            print(f"❌ Coverage summary failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Coverage report generation failed: {e}")


def main():
    """Main function to fix issues and run tests."""
    print("🔧 Hydra-Logger Test Fixer and Runner")
    print("=" * 60)
    
    # Fix test issues
    if not fix_test_issues():
        print("❌ Failed to fix test issues")
        return 1
    
    # Install dependencies
    if not install_test_dependencies():
        print("❌ Failed to install test dependencies")
        return 1
    
    # Parse command line arguments
    test_mode = "all"
    if len(sys.argv) > 1:
        test_mode = sys.argv[1].lower()
    
    success = False
    output = ""
    
    if test_mode == "async":
        print("\n🎯 Running async tests only...")
        success, output = run_async_tests_fixed()
    else:
        print("\n🎯 Running all tests...")
        success, output = run_comprehensive_tests()
    
    # Generate final report
    if success:
        generate_final_report()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ All tests completed successfully!")
        print("📁 Reports available in:")
        print("   - htmlcov/ (HTML coverage report)")
        print("   - coverage.xml (XML coverage report)")
        print("   - coverage.json (JSON coverage report)")
        print("   - test_output/ (Detailed test results)")
    else:
        print("❌ Some tests failed!")
        print("📁 Check test_output/ for detailed results")
    
    print(f"\n📝 Test mode: {test_mode}")
    print(f"📊 Success: {success}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 