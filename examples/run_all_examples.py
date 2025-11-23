#!/usr/bin/env python3
"""
Hydra-Logger Examples Test Runner

Test runner for all example files with detailed reporting,
log file verification, and professional output formatting.

Features:
- Individual example execution with timeout protection
- Detailed success/failure reporting
- Log file verification for each example
- Performance timing
- Professional formatting with clear status indicators
- Summary statistics and recommendations
"""
import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Tuple, List, Dict, Optional

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    GRAY = '\033[90m'

def colorize(text: str, color: str) -> str:
    """Apply color to text if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text

def run_example(filepath: Path) -> Tuple[bool, str, str, float, Dict[str, any]]:
    """
    Run a single example file and return results.
    
    Returns:
        Tuple of (success, stdout, stderr, duration, metadata)
    """
    start_time = time.time()
    metadata = {
        "example": filepath.name,
        "duration": 0.0,
        "return_code": -1,
        "has_output": False,
        "has_errors": False
    }
    
    try:
        result = subprocess.run(
            [sys.executable, str(filepath)],
            capture_output=True,
            text=True,
            timeout=30
        )
        duration = time.time() - start_time
        metadata["duration"] = duration
        metadata["return_code"] = result.returncode
        metadata["has_output"] = bool(result.stdout.strip())
        metadata["has_errors"] = bool(result.stderr.strip())
        
        # close_async() in examples ensures all writes complete
        # The examples now use async context managers or close_async() which handles cleanup automatically
 
        return result.returncode == 0, result.stdout, result.stderr, duration, metadata
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        metadata["duration"] = duration
        metadata["has_errors"] = True
        return False, "", "Timeout after 30 seconds", duration, metadata
    except Exception as e:
        duration = time.time() - start_time
        metadata["duration"] = duration
        metadata["has_errors"] = True
        return False, "", str(e), duration, metadata

def verify_log_files(example_name: str) -> Tuple[List[str], List[str]]:
    """
    Verify that log files exist for a given example.
    
    Returns:
        Tuple of (found_files, expected_patterns)
    """
    logs_dir = Path("logs/examples")
    if not logs_dir.exists():
        return [], []
    
    # Extract example number prefix (e.g., "15" from "15_eda_microservices_patterns.py")
    example_num = example_name.split("_")[0] if "_" in example_name else ""
    example_base = example_name.replace(".py", "").replace("_", "_")
    
    # Common patterns
    patterns = [
        f"{example_base}.log",
        f"{example_base}.jsonl",
        f"{example_base}_*.log",
        f"{example_base}_*.jsonl",
    ]
    
    # Check for files matching patterns
    found_files = []
    
    # Note: Check multiple patterns to catch all possible log files
    # 1. Exact base match (e.g., 01_format_control.log)
    all_files = list(logs_dir.glob(f"{example_base}*"))
    
    # 2. Example number prefix match (e.g., 15_microservice_auto.jsonl from 15_eda_microservices_patterns.py)
    if example_num and example_num.isdigit():
        prefix_files = list(logs_dir.glob(f"{example_num}_*"))
        all_files.extend(prefix_files)
    
    # Deduplicate and filter to actual files
    seen = set()
    for file in all_files:
        if file.is_file() and file.name not in seen:
            # Only include if it matches our patterns (exclude unrelated files)
            file_name = file.name
            if (file_name.startswith(example_base) or 
                (example_num and file_name.startswith(f"{example_num}_"))):
                found_files.append(file_name)
                seen.add(file_name)
    
    return sorted(found_files), patterns

def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    return f"{seconds:.2f}s"

def print_header():
    """Print professional header."""
    print()
    print(colorize("=" * 80, Colors.BOLD))
    print(colorize(" Hydra-Logger Examples Test Runner", Colors.BOLD + Colors.CYAN))
    print(colorize("=" * 80, Colors.BOLD))
    print()
    print(f" Running tests on all example files...")
    print(f" Verifying log file creation and function tracking...")
    print()

def print_example_result(
    example_name: str,
    success: bool,
    stdout: str,
    stderr: str,
    duration: float,
    metadata: Dict,
    found_logs: List[str]
):
    """Print detailed result for a single example."""
    status_icon = "" if success else ""
    status_text = colorize("PASSED", Colors.GREEN) if success else colorize("FAILED", Colors.RED)
    
    print(f"  {status_icon} {colorize(example_name, Colors.BOLD)}", end=" ")
    print(f" [{status_text}]", end=" ")
    print(f"{colorize(f'({format_duration(duration)})', Colors.GRAY)}")
    
    # Show completion message if available
    if success and "" in stdout:
        for line in stdout.split("\n"):
            if "" in line and "completed" in line:
                print(f"     {colorize('→', Colors.GRAY)} {line.strip()}")
    
    # Show log files if created
    if found_logs:
        print(f"     {colorize('Log files:', Colors.CYAN)} {', '.join(found_logs)}")
    elif success:
        print(f"     {colorize('No log files detected', Colors.YELLOW)}")
    
    # Show errors if any
    if stderr.strip():
        error_preview = stderr.strip().split("\n")[:2]
        for line in error_preview:
            if line.strip() and "" not in line:  # Skip warnings
                print(f"     {colorize('ERROR:', Colors.RED)} {line.strip()[:100]}")

def print_summary(results: List[Tuple[str, bool, float, List[str]]], total_duration: float):
    """Print summary."""
    print()
    print(colorize("=" * 80, Colors.BOLD))
    print(colorize(" Test Summary", Colors.BOLD + Colors.CYAN))
    print(colorize("=" * 80, Colors.BOLD))
    print()
    
    passed = sum(1 for _, success, _, _ in results if success)
    failed = len(results) - passed
    total_files = sum(len(logs) for _, _, _, logs in results)
    
    # Overall status
    if failed == 0:
        print(f"  {colorize('All Examples:', Colors.GREEN + Colors.BOLD)} {passed}/{len(results)} passed")
    else:
        print(f"  {colorize('Results:', Colors.RED + Colors.BOLD)} {passed} passed, {failed} failed")
    
    print(f"  {colorize('Log Files Created:', Colors.CYAN)} {total_files}")
    print(f"  {colorize('Total Duration:', Colors.BLUE)} {format_duration(total_duration)}")
    print()
    
    # Performance metrics
    durations = [dur for _, _, dur, _ in results]
    if durations:
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        print(f"  {colorize('Performance:', Colors.YELLOW)}")
        print(f"     Average: {format_duration(avg_duration)}")
        print(f"     Fastest: {format_duration(min_duration)}")
        print(f"     Slowest: {format_duration(max_duration)}")
        print()
    
    # Failed examples details
    if failed > 0:
        print(f"  {colorize('Failed Examples:', Colors.RED)}")
        for name, success, duration, logs in results:
            if not success:
                print(f"     • {name} ({format_duration(duration)})")
        print()
    
    # Success message
    if failed == 0:
        print(f"  {colorize('All examples executed successfully!', Colors.GREEN + Colors.BOLD)}")
        print(f"  {colorize('Check logs/examples/ for generated log files.', Colors.CYAN)}")
        print()

def main():
    """Run all examples and report results."""
    start_time = time.time()
    
    # Setup
    examples_dir = Path(__file__).parent
    example_files = sorted(examples_dir.glob("*.py"))
    
    # Exclude this script itself
    example_files = [f for f in example_files if f.name != "run_all_examples.py"]
    
    if not example_files:
        print(colorize("No example files found!", Colors.RED))
        return 1
    
    # Print header
    print_header()
    
    # Run all examples
    results = []
    for example_file in example_files:
        success, stdout, stderr, duration, metadata = run_example(example_file)
        
        # Note: For async examples, wait a moment for async file writes to complete
        # Even though close_async() should handle it, filesystem might need a moment
        is_async_example = (
            "async" in example_file.name.lower() or 
            "eda" in example_file.name.lower() or 
            "microservice" in example_file.name.lower() or
            "multi_layer" in example_file.name.lower()  # Example 16
        )
        if is_async_example and success:
            time.sleep(0.5)  # Brief wait for async file I/O to complete
        
        found_logs, _ = verify_log_files(example_file.name)
        
        print_example_result(
            example_file.name,
            success,
            stdout,
            stderr,
            duration,
            metadata,
            found_logs
        )
        
        results.append((example_file.name, success, duration, found_logs))
    
    # Print summary
    total_duration = time.time() - start_time
    print_summary(results, total_duration)
    
    # Return exit code
    failed = sum(1 for _, success, _, _ in results if not success)
    return 1 if failed > 0 else 0

if __name__ == "__main__":
    sys.exit(main())

