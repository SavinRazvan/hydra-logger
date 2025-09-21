#!/usr/bin/env python3
"""
Hydra-Logger Test Runner for hydra_logger module tests.

This script runs all tests for the hydra_logger module with comprehensive coverage reporting.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests(test_category=None, verbose=False, coverage=False, parallel=False, test_files=None):
    """Run hydra_logger tests with specified options."""
    
    # Base command
    cmd = [sys.executable, '-m', 'pytest']
    
    # Add test files or directories
    if test_files:
        cmd.extend(test_files)
    elif test_category:
        # Add specific category directory
        tests_dir = os.path.join(os.path.dirname(__file__), test_category)
        if os.path.exists(tests_dir):
            cmd.append(tests_dir)
        else:
            print(f"❌ Test category directory not found: {tests_dir}")
            return 1
    else:
        # Add all tests directory
        tests_dir = os.path.dirname(__file__)
        cmd.append(tests_dir)
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            '--cov=hydra_logger',
            '--cov-report=html:coverage/html',
            '--cov-report=term-missing',
            '--cov-report=xml:coverage/coverage.xml'
        ])
    
    # Add parallel execution if requested
    if parallel:
        cmd.extend(['-n', 'auto'])
    
    # Add other useful options
    cmd.extend([
        '--tb=short',
        '--strict-markers',
        '--disable-warnings'
    ])
    
    print(f"🔍 Running tests with command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(__file__)))
        return result.returncode
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def discover_tests():
    """Discover all available test files."""
    tests_dir = Path(__file__).parent
    
    if not tests_dir.exists():
        print("❌ Tests directory not found")
        return []
    
    # Use glob patterns for comprehensive discovery
    import glob
    test_patterns = [
        'tests/**/test_*.py',
        'tests/**/*_test.py'
    ]
    
    test_files = []
    for pattern in test_patterns:
        # Adjust pattern for current working directory
        adjusted_pattern = str(tests_dir.parent / pattern)
        test_files.extend(glob.glob(adjusted_pattern, recursive=True))
    
    # Filter out non-test files
    exclude_dirs = ['__pycache__', 'fixtures', 'utils', 'docs', 'coverage']
    filtered_tests = []
    
    for test_file in test_files:
        # Check if any exclude directory is in the path
        if not any(exclude_dir in test_file for exclude_dir in exclude_dirs):
            # Convert to relative path from tests directory
            try:
                rel_path = os.path.relpath(test_file, tests_dir)
                filtered_tests.append(rel_path)
            except ValueError:
                # If relative path fails, use absolute path
                filtered_tests.append(test_file)
    
    return sorted(filtered_tests)

def list_test_categories():
    """List all available test categories."""
    tests_dir = Path(__file__).parent / 'unit'
    
    if not tests_dir.exists():
        print("❌ Tests directory not found")
        return {}
    
    categories = {}
    for category_dir in tests_dir.iterdir():
        if category_dir.is_dir() and category_dir.name != '__pycache__':
            test_files = list(category_dir.glob('test_*.py'))
            if test_files:
                categories[category_dir.name] = [f.name for f in test_files]
    
    return categories

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Hydra-Logger Test Runner")
    parser.add_argument('--discover', action='store_true', help='Discover and list test files')
    parser.add_argument('--list-categories', action='store_true', help='List available test categories')
    parser.add_argument('--category', help='Run tests from specific category (unit, integration, performance, etc.)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('files', nargs='*', help='Specific test files to run')
    
    args = parser.parse_args()
    
    if args.discover:
        test_files = discover_tests()
        print("🔍 DISCOVERED HYDRA_LOGGER TESTS")
        print("=" * 50)
        
        if test_files:
            # Group by category
            categories = {}
            for test_file in test_files:
                parts = test_file.split('/')
                if len(parts) >= 2:  # category/file.py
                    category = parts[0]
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(test_file)
            
            for category, files in categories.items():
                print(f"\n📁 {category.upper()} ({len(files)} tests):")
                for test_file in files:
                    print(f"  • {test_file}")
            
            print(f"\n📊 Total: {len(test_files)} test files")
        else:
            print("❌ No test files found")
        return 0
    
    if args.list_categories:
        categories = list_test_categories()
        print("📁 AVAILABLE TEST CATEGORIES")
        print("=" * 50)
        
        if categories:
            for category, files in categories.items():
                print(f"\n📂 {category.upper()} ({len(files)} tests):")
                for test_file in files:
                    print(f"  • {test_file}")
            
            total_tests = sum(len(files) for files in categories.values())
            print(f"\n📊 Total: {total_tests} test files across {len(categories)} categories")
        else:
            print("❌ No test categories found")
        return 0
    
    # Run tests
    return run_tests(
        test_category=args.category,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
        test_files=args.files if args.files else None
    )

if __name__ == "__main__":
    sys.exit(main())
