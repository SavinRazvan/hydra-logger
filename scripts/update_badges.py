#!/usr/bin/env python3
"""
Badge Update Script for Hydra-Logger

This script automatically updates the README.md coverage badge as a fallback when Codecov is down.
The primary coverage badge is now handled by Codecov dynamically.

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
from typing import Tuple


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


def update_readme_badges(readme_path: Path, coverage_percentage: float, dry_run: bool = False) -> bool:
    """Update the coverage badge in the README file (fallback when Codecov is down)."""
    if not readme_path.exists():
        print(f"Error: README file not found at {readme_path}")
        return False
    
    # Read the current README content
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the badge pattern for the old static coverage badge
    coverage_badge_pattern = r'\[!\[Coverage\]\(https://img\.shields\.io/badge/coverage-\d+%25-[^)]+\)\]\([^)]+\)'
    
    # Create new badge URL (static fallback in case Codecov is down)
    coverage_badge = f'[![Coverage](https://img.shields.io/badge/coverage-{int(coverage_percentage)}%25-darkgreen.svg)](https://github.com/SavinRazvan/hydra-logger)'
    
    # Replace the badge
    new_content = re.sub(coverage_badge_pattern, coverage_badge, content)
    
    if dry_run:
        print("=== DRY RUN - Changes that would be made ===")
        print(f"Coverage badge: {int(coverage_percentage)}%")
        return True
    
    # Write the updated content back
    if new_content != content:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Updated coverage badge in {readme_path}")
        print(f"   Coverage: {int(coverage_percentage)}%")
        return True
    else:
        print("ℹ️  No changes needed - coverage badge is already up to date")
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Update README coverage badge with current stats")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--readme-path", type=Path, default=Path("README.md"), help="Path to README.md file")
    parser.add_argument("--coverage-percentage", type=float, help="Override coverage percentage (useful for CI)")
    
    args = parser.parse_args()
    
    print("🔍 Gathering current coverage statistics...")
    
    # Get current statistics
    coverage_percentage = args.coverage_percentage if args.coverage_percentage is not None else get_coverage_percentage()
    
    print(f"📊 Current coverage: {coverage_percentage:.1f}%")
    
    # Update the README
    success = update_readme_badges(args.readme_path, coverage_percentage, args.dry_run)
    
    if success:
        print("✅ Coverage badge update completed successfully")
        return 0
    else:
        print("❌ Coverage badge update failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 