#!/usr/bin/env python3
"""
Comprehensive Project Cleaner for Hydra-Logger

This script removes all types of residual files from the project including:
- Python cache files (__pycache__, .pyc, .pyo)
- Coverage files and reports
- Temporary files and directories
- IDE-specific files
- Build artifacts
- Test artifacts
- Log files (optional)
- Backup files
- OS-specific files

Usage:
    python _cleaner.py [options]

Options:
    --dry-run          Show what would be deleted without actually deleting
    --include-logs     Also clean log files (default: exclude)
    --include-backups  Also clean backup files (default: exclude)
    --verbose          Show detailed output
    --help            Show this help message
"""

import os
import sys
import shutil
import argparse
import glob
from pathlib import Path
from typing import List, Set, Tuple
import time


class ProjectCleaner:
    """Comprehensive project cleaner for removing residual files."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """
        Initialize the cleaner.
        
        Args:
            dry_run: If True, show what would be deleted without actually deleting
            verbose: If True, show detailed output
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.deleted_files = []
        self.deleted_dirs = []
        self.errors = []
        
        # Patterns to always clean
        self.always_clean_patterns = [
            # Python cache files
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
            
            # Coverage files
            "**/.coverage",
            "**/coverage.xml",
            "**/.coverage.*",
            "**/htmlcov",
            "**/.pytest_cache",
            "**/.mypy_cache",
            "**/.coverage.*",
            "**/coverage_html",
            "**/.coveragerc",
            "**/coverage.json",
            "**/coverage.info",
            "**/.coverage.*.tmp",
            "**/coverage_data",
            "**/coverage_report",
            
            # Temporary files
            "**/*.tmp",
            "**/*.temp",
            "**/*.swp",
            "**/*.swo",
            "**/*~",
            "**/.#*",
            "**/#*#",
            
            # IDE files
            "**/.vscode",
            "**/.idea",
            "**/*.sublime-*",
            "**/.DS_Store",
            "**/Thumbs.db",
            
            # Build artifacts
            "**/build",
            "**/dist",
            "**/*.egg-info",
            "**/.eggs",
            "**/__pycache__",
            
            # Test artifacts
            "**/.pytest_cache",
            "**/.tox",
            "**/.cache",
            "**/test-results",
            "**/test-output",
            "**/.pytest_cache/**",
            "**/pytest_cache",
            "**/.nose2",
            "**/.nose",
            "**/test_cache",
            "**/test_cache/**",
            "**/.test_cache",
            "**/.test_cache/**",
            "**/test_output",
            "**/test_results",
            "**/.test_output",
            "**/.test_results",
            "**/MagicMock*",
            "**/_tests_logs*",
            "**/_tests_*",
            "**/tests_*",
            "**/hydra_*_test_*",
            "**/hydra_test_*",
            
            # OS-specific files
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/desktop.ini",
            "**/*.zone",
            "**/*:Zone.Identifier",
            "**/*:Zone.Identifier:$DATA",
            
            # Backup files (optional)
            "**/*.bak",
            "**/*.backup",
            "**/*.old",
            
            # Log files (optional)
            "**/*.log",
            "**/logs",
        ]
        
        # Directories to always clean
        self.always_clean_dirs = [
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "htmlcov",
            "build",
            "dist",
            ".eggs",
            ".tox",
            ".cache",
            "test-results",
            "test-output",
            ".vscode",
            ".idea",
            "pytest_cache",
            ".nose2",
            ".nose",
            "test_cache",
            ".test_cache",
            "test_output",
            "test_results",
            ".test_output",
            ".test_results",
            "coverage_html",
            "coverage_data",
            "coverage_report",
            ".coverage.*",
            ".hydra_backup",
        ]
        
        # Files to always clean
        self.always_clean_files = [
            ".coverage",
            "coverage.xml",
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
            ".coveragerc",
            "coverage.json",
            "coverage.info",
            ".coverage.*.tmp",
            "pytest.ini",
            "tox.ini",
            ".pytest_cache",
            ".mypy_cache",
            "*.zone",
            "*:Zone.Identifier",
            "*:Zone.Identifier:$DATA",
        ]
    
    def find_files(self, patterns: List[str]) -> Set[Path]:
        """
        Find files matching the given patterns.
        
        Args:
            patterns: List of glob patterns
            
        Returns:
            Set of matching file paths
        """
        files = set()
        
        for pattern in patterns:
            try:
                matches = self.project_root.glob(pattern)
                for match in matches:
                    if match.is_file():
                        files.add(match)
                    elif match.is_dir():
                        # Add all files in directory
                        for file_path in match.rglob("*"):
                            if file_path.is_file():
                                files.add(file_path)
            except Exception as e:
                self.errors.append(f"Error finding files with pattern '{pattern}': {e}")
        
        return files
    
    def find_directories(self, dir_names: List[str]) -> Set[Path]:
        """
        Find directories with the given names.
        
        Args:
            dir_names: List of directory names to find
            
        Returns:
            Set of matching directory paths
        """
        dirs = set()
        
        for dir_name in dir_names:
            try:
                for root, dirs_list, files in os.walk(self.project_root):
                    if dir_name in dirs_list:
                        dir_path = Path(root) / dir_name
                        dirs.add(dir_path)
            except Exception as e:
                self.errors.append(f"Error finding directory '{dir_name}': {e}")
        
        return dirs
    
    def clean_files(self, files: Set[Path]) -> None:
        """
        Clean the given files.
        
        Args:
            files: Set of file paths to delete
        """
        for file_path in files:
            try:
                if self.verbose:
                    print(f"  📄 {file_path}")
                
                if not self.dry_run:
                    # Check if file still exists before trying to delete
                    if file_path.exists():
                        file_path.unlink()
                        self.deleted_files.append(str(file_path))
                    else:
                        # File was already deleted, this is normal
                        if self.verbose:
                            print(f"    ⚠️  File already deleted: {file_path}")
                else:
                    print(f"    Would delete: {file_path}")
                    
            except FileNotFoundError:
                # File was already deleted, this is normal
                if self.verbose:
                    print(f"    ⚠️  File already deleted: {file_path}")
            except Exception as e:
                error_msg = f"Error deleting file '{file_path}': {e}"
                self.errors.append(error_msg)
                if self.verbose:
                    print(f"    ❌ {error_msg}")
    
    def clean_directories(self, dirs: Set[Path]) -> None:
        """
        Clean the given directories.
        
        Args:
            dirs: Set of directory paths to delete
        """
        for dir_path in dirs:
            try:
                if self.verbose:
                    print(f"  📁 {dir_path}")
                
                if not self.dry_run:
                    # Check if directory still exists before trying to delete
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                        self.deleted_dirs.append(str(dir_path))
                    else:
                        # Directory was already deleted, this is normal
                        if self.verbose:
                            print(f"    ⚠️  Directory already deleted: {dir_path}")
                else:
                    print(f"    Would delete directory: {dir_path}")
                    
            except FileNotFoundError:
                # Directory was already deleted, this is normal
                if self.verbose:
                    print(f"    ⚠️  Directory already deleted: {dir_path}")
            except Exception as e:
                error_msg = f"Error deleting directory '{dir_path}': {e}"
                self.errors.append(error_msg)
                if self.verbose:
                    print(f"    ❌ {error_msg}")
    
    def clean_python_cache(self) -> None:
        """Clean Python cache files."""
        print("🧹 Cleaning Python cache files...")
        
        # Find all __pycache__ directories
        pycache_dirs = set()
        for root, dirs, files in os.walk(self.project_root):
            if "__pycache__" in dirs:
                pycache_dirs.add(Path(root) / "__pycache__")
        
        # Find all .pyc, .pyo files
        pyc_files = set()
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(('.pyc', '.pyo', '.pyd')):
                    pyc_files.add(Path(root) / file)
        
        self.clean_directories(pycache_dirs)
        self.clean_files(pyc_files)
    
    def clean_coverage_files(self) -> None:
        """Clean coverage files."""
        print("📊 Cleaning coverage files...")
        
        coverage_patterns = [
            "**/.coverage*",
            "**/coverage.xml",
            "**/htmlcov",
            "**/.pytest_cache",
            "**/.coveragerc",
            "**/coverage.json",
            "**/coverage.info",
            "**/.coverage.*.tmp",
            "**/coverage_html",
            "**/coverage_data",
            "**/coverage_report",
            "**/coverage_html/**",
            "**/coverage_data/**",
            "**/coverage_report/**",
        ]
        
        files = self.find_files(coverage_patterns)
        self.clean_files(files)
    
    def clean_test_cache(self) -> None:
        """Clean test cache files."""
        print("🧪 Cleaning test cache files...")
        
        test_cache_patterns = [
            "**/.pytest_cache",
            "**/.pytest_cache/**",
            "**/pytest_cache",
            "**/.nose2",
            "**/.nose",
            "**/test_cache",
            "**/test_cache/**",
            "**/.test_cache",
            "**/.test_cache/**",
            "**/test_output",
            "**/test_results",
            "**/.test_output",
            "**/.test_results",
            "**/pytest.ini",
            "**/tox.ini",
            "**/.mypy_cache",
        ]
        
        files = self.find_files(test_cache_patterns)
        self.clean_files(files)
    
    def clean_specific_directories(self) -> None:
        """Clean specific directories that are commonly problematic."""
        print("🎯 Cleaning specific directories...")
        
        specific_dirs = [
            ".hydra_backup",
            ".pytest_cache", 
            "htmlcov",
        ]
        
        dirs = self.find_directories(specific_dirs)
        self.clean_directories(dirs)
    
    def clean_zone_identifiers(self) -> None:
        """Clean zone identifier files."""
        print("🔒 Cleaning zone identifier files...")
        
        zone_patterns = [
            "**/*.zone",
            "**/*:Zone.Identifier",
            "**/*:Zone.Identifier:$DATA",
        ]
        
        files = self.find_files(zone_patterns)
        self.clean_files(files)
    
    def clean_build_artifacts(self) -> None:
        """Clean build artifacts."""
        print("🔨 Cleaning build artifacts...")
        
        build_patterns = [
            "**/build",
            "**/dist",
            "**/*.egg-info",
            "**/.eggs",
            "**/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
            "**/*.pyd",
        ]
        
        files = self.find_files(build_patterns)
        self.clean_files(files)
    
    def clean_ide_files(self) -> None:
        """Clean IDE-specific files."""
        print("💻 Cleaning IDE files...")
        
        ide_patterns = [
            "**/.vscode",
            "**/.idea",
            "**/*.sublime-*",
            "**/.DS_Store",
            "**/Thumbs.db",
        ]
        
        files = self.find_files(ide_patterns)
        self.clean_files(files)
    
    def clean_temp_files(self) -> None:
        """Clean temporary files."""
        print("🗑️  Cleaning temporary files...")
        
        temp_patterns = [
            "**/*.tmp",
            "**/*.temp",
            "**/*.swp",
            "**/*.swo",
            "**/*~",
            "**/.#*",
            "**/#*#",
        ]
        
        files = self.find_files(temp_patterns)
        self.clean_files(files)
    
    def clean_log_files(self) -> None:
        """Clean log files."""
        print("📝 Cleaning log files...")
        
        log_patterns = [
            "**/*.log",
            "**/logs",
        ]
        
        files = self.find_files(log_patterns)
        self.clean_files(files)
    
    def clean_backup_files(self) -> None:
        """Clean backup files."""
        print("💾 Cleaning backup files...")
        
        backup_patterns = [
            "**/*.bak",
            "**/*.backup",
            "**/*.old",
        ]
        
        files = self.find_files(backup_patterns)
        self.clean_files(files)
    

    
    def clean_all(self, include_logs: bool = False, include_backups: bool = False) -> None:
        """
        Clean all residual files.
        
        Args:
            include_logs: Whether to include log files
            include_backups: Whether to include backup files
        """
        print("🚀 Starting comprehensive project cleanup...")
        print(f"📁 Project root: {self.project_root}")
        print(f"🔍 Dry run: {'Yes' if self.dry_run else 'No'}")
        print(f"📝 Include logs: {'Yes' if include_logs else 'No'}")
        print(f"💾 Include backups: {'Yes' if include_backups else 'No'}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Clean Python cache
        self.clean_python_cache()
        
        # Clean coverage files
        self.clean_coverage_files()
        
        # Clean test cache files
        self.clean_test_cache()
        
        # Clean specific directories
        self.clean_specific_directories()
        
        # Clean build artifacts
        self.clean_build_artifacts()
        
        # Clean IDE files
        self.clean_ide_files()
        
        # Clean temporary files
        self.clean_temp_files()
        
        # Optional cleaning
        if include_logs:
            self.clean_log_files()
        
        if include_backups:
            self.clean_backup_files()
        
        # Print summary
        self.print_summary(start_time)
    
    def print_summary(self, start_time: float) -> None:
        """
        Print cleanup summary.
        
        Args:
            start_time: Start time of cleanup
        """
        duration = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 CLEANUP SUMMARY")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 DRY RUN - No files were actually deleted")
        
        # Count actual errors (not FileNotFoundError which are normal)
        actual_errors = [e for e in self.errors if "FileNotFoundError" not in e and "No such file or directory" not in e]
        
        print(f"📄 Files processed: {len(self.deleted_files)}")
        print(f"📁 Directories processed: {len(self.deleted_dirs)}")
        print(f"⚠️  Already deleted: {len(self.errors) - len(actual_errors)}")
        print(f"❌ Actual errors: {len(actual_errors)}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if actual_errors:
            print(f"\n❌ Actual errors:")
            for error in actual_errors:
                print(f"  - {error}")
        elif self.errors:
            print(f"\n⚠️  Note: {len(self.errors)} files/directories were already deleted (this is normal)")
        
        if self.verbose and self.deleted_files:
            print(f"\n📄 Deleted files:")
            for file_path in self.deleted_files[:10]:  # Show first 10
                print(f"  - {file_path}")
            if len(self.deleted_files) > 10:
                print(f"  ... and {len(self.deleted_files) - 10} more")
        
        if self.verbose and self.deleted_dirs:
            print(f"\n📁 Deleted directories:")
            for dir_path in self.deleted_dirs[:10]:  # Show first 10
                print(f"  - {dir_path}")
            if len(self.deleted_dirs) > 10:
                print(f"  ... and {len(self.deleted_dirs) - 10} more")
        
        print("\n✅ Cleanup completed!")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive project cleaner for Hydra-Logger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python _cleaner.py                    # Clean all files (excluding logs/backups)
    python _cleaner.py --dry-run         # Show what would be deleted
    python _cleaner.py --include-logs    # Also clean log files
    python _cleaner.py --verbose         # Show detailed output
    python _cleaner.py --include-logs --include-backups --verbose  # Full cleanup
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    
    parser.add_argument(
        "--include-logs",
        action="store_true",
        help="Also clean log files (default: exclude)"
    )
    
    parser.add_argument(
        "--include-backups",
        action="store_true",
        help="Also clean backup files (default: exclude)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    # Create cleaner and run
    cleaner = ProjectCleaner(dry_run=args.dry_run, verbose=args.verbose)
    cleaner.clean_all(
        include_logs=args.include_logs,
        include_backups=args.include_backups
    )


if __name__ == "__main__":
    main()
