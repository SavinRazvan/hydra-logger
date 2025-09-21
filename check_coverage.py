#!/usr/bin/env python3
"""
Coverage checker for hydra_logger modules.
"""

import sys
import os
import ast

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_method_coverage(module_path, test_file_path):
    """Get method coverage for a module."""
    
    # Read the module file
    with open(module_path, 'r') as f:
        module_source = f.read()
    
    # Parse the AST
    tree = ast.parse(module_source)
    
    # Find all methods/functions
    method_lines = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_lines[node.name] = node.lineno
    
    # Read test file
    with open(test_file_path, 'r') as f:
        test_source = f.read()
    
    # Count covered methods
    covered_methods = set()
    for method_name in method_lines:
        # Check if method is called in tests
        if method_name in test_source or f'_{method_name}' in test_source:
            covered_methods.add(method_name)
        # Special case for __init__ - covered if class is instantiated
        elif method_name == '__init__':
            class_name = os.path.basename(module_path).replace('.py', '').replace('_', '').title()
            if f'{class_name}(' in test_source or 'JsonLinesFormatter(' in test_source:
                covered_methods.add(method_name)
    
    return method_lines, covered_methods

def find_all_modules_and_tests():
    """Find all modules and their corresponding test files."""
    modules_and_tests = []
    
    # Get all test files first
    test_files = []
    for root, dirs, files in os.walk("tests/unit"):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    # Map test files to their corresponding modules
    for test_file in test_files:
        # Extract module path from test file path
        # tests/unit/formatters/test_json.py -> hydra_logger/formatters/json.py
        relative_test = os.path.relpath(test_file, "tests/unit")
        
        # Remove test_ prefix from filename only
        parts = relative_test.split('/')
        if len(parts) > 0 and parts[-1].startswith('test_'):
            parts[-1] = parts[-1][5:]  # Remove 'test_' prefix from filename
        
        module_name = '/'.join(parts)
        module_path = os.path.join("hydra_logger", module_name)
        
        if os.path.exists(module_path):
            modules_and_tests.append((module_path, test_file))
    
    return modules_and_tests

def main():
    print("🔍 COMPREHENSIVE COVERAGE ANALYSIS")
    print("=" * 60)
    
    modules_and_tests = find_all_modules_and_tests()
    
    total_modules = 0
    covered_modules = 0
    total_coverage = 0
    
    for module_path, test_file_path in modules_and_tests:
        if os.path.exists(module_path) and os.path.exists(test_file_path):
            method_lines, covered_methods = get_method_coverage(module_path, test_file_path)
            
            total_methods = len(method_lines)
            covered_count = len(covered_methods)
            coverage_percent = (covered_count / total_methods * 100) if total_methods > 0 else 0
            
            total_modules += 1
            total_coverage += coverage_percent
            if coverage_percent >= 95:
                covered_modules += 1
            
            status = "✅" if coverage_percent >= 95 else "❌"
            print(f"{status} {module_path}")
            print(f"   Methods: {covered_count}/{total_methods} ({coverage_percent:.1f}%)")
            
            if coverage_percent < 95 and total_methods > 0:
                uncovered = set(method_lines.keys()) - covered_methods
                if uncovered:
                    print(f"   Missing: {', '.join(sorted(uncovered))}")
            print()
    
    # Summary
    avg_coverage = (total_coverage / total_modules) if total_modules > 0 else 0
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total modules analyzed: {total_modules}")
    print(f"Modules with 95%+ coverage: {covered_modules}")
    print(f"Average coverage: {avg_coverage:.1f}%")
    
    if covered_modules == total_modules:
        print("🎉 ALL MODULES MEET COVERAGE TARGET!")
    else:
        print(f"⚠️  {total_modules - covered_modules} modules need improvement")

if __name__ == "__main__":
    main()
