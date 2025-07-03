#!/usr/bin/env python3
"""
Show Statistics Script for Hydra-Logger

This script displays current test and coverage statistics in a nice format.
"""

import subprocess
import re
import sys


def run_command(cmd):
    """Run a command and return stdout."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None


def get_test_count():
    """Get the total number of tests."""
    output = run_command(["python", "-m", "pytest", "--collect-only", "-q"])
    if output:
        match = re.search(r'(\d+) tests collected', output)
        if match:
            return int(match.group(1))
    
    # Fallback
    output = run_command(["grep", "-r", "def test_", "tests/"])
    if output:
        return len(output.strip().split('\n'))
    
    return 0


def get_coverage_percentage():
    """Get the current coverage percentage."""
    output = run_command(["python", "-m", "pytest", "--cov=hydra_logger", "--cov-report=term-missing", "-q"])
    if output:
        match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
        if match:
            return float(match.group(1))
    return 0.0


def get_test_breakdown():
    """Get breakdown of tests by file."""
    output = run_command(["grep", "-r", "def test_", "tests/"])
    if not output:
        return {}
    
    breakdown = {}
    for line in output.strip().split('\n'):
        if ':' in line:
            filename = line.split(':')[0]
            if filename not in breakdown:
                breakdown[filename] = 0
            breakdown[filename] += 1
    
    return breakdown


def main():
    """Main function."""
    print("🐉 Hydra-Logger Statistics")
    print("=" * 40)
    
    # Get test count
    test_count = get_test_count()
    print(f"📊 Total Tests: {test_count}")
    
    # Get coverage
    coverage = get_coverage_percentage()
    print(f"📈 Coverage: {coverage:.1f}%")
    
    # Get test breakdown
    breakdown = get_test_breakdown()
    if breakdown:
        print(f"\n📁 Test Breakdown:")
        for filename, count in sorted(breakdown.items()):
            print(f"   {filename}: {count} tests")
    
    # Calculate status
    status = "🟢 Excellent" if coverage >= 95 else "🟡 Good" if coverage >= 90 else "🔴 Needs Improvement"
    print(f"\n📋 Status: {status}")
    
    # Show badge URLs
    print(f"\n🔗 Badge URLs:")
    print(f"   Tests: https://img.shields.io/badge/tests-{test_count}%20passed-darkgreen.svg")
    print(f"   Coverage: https://img.shields.io/badge/coverage-{int(coverage)}%25-darkgreen.svg")


if __name__ == "__main__":
    main() 