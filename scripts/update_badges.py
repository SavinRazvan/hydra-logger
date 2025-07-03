#!/usr/bin/env python3
"""
Badge Update Script for Hydra-Logger

This script automatically updates the README.md badges with current test and coverage statistics.
It can be run manually or as part of CI/CD workflows.

Usage:
    python scripts/update_badges.py
    python scripts/update_badges.py --dry-run
    python scripts/update_badges.py --readme-path path/to/README.md
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional


def run_command(cmd: list, capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=capture_output, 
            text=True, 
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_test_count() -> int:
    """Get the total number of tests."""
    cmd = ["python", "-m", "pytest", "--collect-only", "-q"]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"Warning: Could not get test count: {stderr}")
        return 0
    
    # Look for the test count in the output
    match = re.search(r'(\d+) tests collected', stdout)
    if match:
        return int(match.group(1))
    
    # Fallback: count test functions
    cmd = ["grep", "-r", "def test_", "tests/"]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code == 0:
        return len(stdout.strip().split('\n'))
    
    print("Warning: Could not determine test count")
    return 0


def get_coverage_percentage() -> float:
    """Get the current coverage percentage."""
    cmd = ["python", "-m", "pytest", "--cov=hydra_logger", "--cov-report=term-missing", "-q"]
    exit_code, stdout, stderr = run_command(cmd)
    
    if exit_code != 0:
        print(f"Warning: Could not get coverage: {stderr}")
        return 0.0
    
    # Look for the coverage percentage in the output
    match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', stdout)
    if match:
        return float(match.group(1))
    
    print("Warning: Could not determine coverage percentage")
    return 0.0


def update_readme_badges(readme_path: Path, test_count: int, coverage_percentage: float, dry_run: bool = False) -> bool:
    """Update the badges in the README file."""
    if not readme_path.exists():
        print(f"Error: README file not found at {readme_path}")
        return False
    
    # Read the current README content
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the badge patterns
    test_badge_pattern = r'\[!\[Tests\]\(https://img\.shields\.io/badge/tests-\d+%20passed-[^)]+\)\]\([^)]+\)'
    coverage_badge_pattern = r'\[!\[Coverage\]\(https://img\.shields\.io/badge/coverage-\d+%25-[^)]+\)\]\([^)]+\)'
    
    # Create new badge URLs
    test_badge = f'[![Tests](https://img.shields.io/badge/tests-{test_count}%20passed-darkgreen.svg)](https://github.com/SavinRazvan/hydra-logger)'
    coverage_badge = f'[![Coverage](https://img.shields.io/badge/coverage-{int(coverage_percentage)}%25-darkgreen.svg)](https://github.com/SavinRazvan/hydra-logger)'
    
    # Replace the badges
    new_content = re.sub(test_badge_pattern, test_badge, content)
    new_content = re.sub(coverage_badge_pattern, coverage_badge, new_content)
    
    if dry_run:
        print("=== DRY RUN - Changes that would be made ===")
        print(f"Test badge: {test_count} tests")
        print(f"Coverage badge: {int(coverage_percentage)}%")
        return True
    
    # Write the updated content back
    if new_content != content:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Updated badges in {readme_path}")
        print(f"   Tests: {test_count}")
        print(f"   Coverage: {int(coverage_percentage)}%")
        return True
    else:
        print("ℹ️  No changes needed - badges are already up to date")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Update README badges with current test and coverage stats")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--readme-path", type=Path, default=Path("README.md"), help="Path to README.md file")
    parser.add_argument("--test-count", type=int, help="Override test count (useful for CI)")
    parser.add_argument("--coverage-percentage", type=float, help="Override coverage percentage (useful for CI)")
    
    args = parser.parse_args()
    
    print("🔍 Gathering current statistics...")
    
    # Get current statistics
    test_count = args.test_count if args.test_count is not None else get_test_count()
    coverage_percentage = args.coverage_percentage if args.coverage_percentage is not None else get_coverage_percentage()
    
    print(f"📊 Current stats: {test_count} tests, {coverage_percentage:.1f}% coverage")
    
    # Update the README
    success = update_readme_badges(args.readme_path, test_count, coverage_percentage, args.dry_run)
    
    if success:
        print("✅ Badge update completed successfully")
        return 0
    else:
        print("❌ Badge update failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 