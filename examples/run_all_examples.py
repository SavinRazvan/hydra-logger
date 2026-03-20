#!/usr/bin/env python3
"""
Role: Runnable example for run all examples.
Used By:
 - Developers running examples manually and `examples/run_all_examples.py`.
Depends On:
 - pathlib
 - subprocess
 - sys
 - time
 - typing
Notes:
 - Demonstrates run all examples usage patterns for manual verification and onboarding.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"


def colorize(text: str, color: str) -> str:
    """Apply color to text if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.RESET}"
    return text


def run_example(filepath: Path) -> Tuple[bool, str, str, float, Dict[str, Any]]:
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
        "has_errors": False,
    }

    try:
        result = subprocess.run(
            [sys.executable, str(filepath)], capture_output=True, text=True, timeout=30
        )
        duration = time.time() - start_time
        metadata["duration"] = duration
        metadata["return_code"] = result.returncode
        metadata["has_output"] = bool(result.stdout.strip())
        metadata["has_errors"] = bool(result.stderr.strip())

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
    logs_dir = Path("examples/logs/tutorials")
    if not logs_dir.exists():
        return [], []

    example_num = example_name.split("_")[0] if "_" in example_name else ""
    example_base = example_name.replace(".py", "")

    patterns = [
        f"{example_base}.log",
        f"{example_base}.jsonl",
        f"{example_base}_*.log",
        f"{example_base}_*.jsonl",
    ]

    found_files = []

    all_files = list(logs_dir.glob(f"{example_base}*"))

    if example_num and example_num.isdigit():
        prefix_files = list(logs_dir.glob(f"{example_num}_*"))
        all_files.extend(prefix_files)

    seen = set()
    for file in all_files:
        if file.is_file() and file.name not in seen:
            file_name = file.name
            if file_name.startswith(example_base) or (
                example_num and file_name.startswith(f"{example_num}_")
            ):
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
    print(colorize(" Hydra-Logger Tutorials Test Runner", Colors.BOLD + Colors.CYAN))
    print(colorize("=" * 80, Colors.BOLD))
    print()
    print(" Running tests on canonical Python tutorial files...")
    print(" Verifying tutorial artifact creation and completion behavior...")
    print()


def print_example_result(
    example_name: str,
    success: bool,
    stdout: str,
    stderr: str,
    duration: float,
    metadata: Dict,
    found_logs: List[str],
):
    """Print detailed result for a single example."""
    status_icon = "[OK]" if success else "[X]"
    status_text = (
        colorize("PASSED", Colors.GREEN) if success else colorize("FAILED", Colors.RED)
    )

    print(f"  {status_icon} {colorize(example_name, Colors.BOLD)}", end=" ")
    print(f" [{status_text}]", end=" ")
    print(f"{colorize(f'({format_duration(duration)})', Colors.GRAY)}")

    if success and stdout.strip():
        for line in stdout.split("\n"):
            if "completed" in line.lower():
                print(f"     {colorize('→', Colors.GRAY)} {line.strip()}")

    if found_logs:
        print(f"     {colorize('Log files:', Colors.CYAN)} {', '.join(found_logs)}")
    elif success:
        print(f"     {colorize('No log files detected', Colors.YELLOW)}")

    if stderr.strip() and not success:
        error_preview = stderr.strip().split("\n")[:2]
        for line in error_preview:
            if line.strip():
                print(f"     {colorize('ERROR:', Colors.RED)} {line.strip()[:100]}")
        if "No module named 'hydra_logger'" in stderr:
            print(
                "     "
                + colorize(
                    "Hint: run with `.hydra_env/bin/python examples/run_all_examples.py`.",
                    Colors.YELLOW,
                )
            )


def print_summary(
    results: List[Tuple[str, bool, float, List[str]]], total_duration: float
):
    """Print summary."""
    print()
    print(colorize("=" * 80, Colors.BOLD))
    print(colorize(" Test Summary", Colors.BOLD + Colors.CYAN))
    print(colorize("=" * 80, Colors.BOLD))
    print()

    passed = sum(1 for _, success, _, _ in results if success)
    failed = len(results) - passed
    total_files = sum(len(logs) for _, _, _, logs in results)

    if failed == 0:
        print(
            f"  {colorize('All Tutorials:', Colors.GREEN + Colors.BOLD)} "
            f"{passed}/{len(results)} passed"
        )
    else:
        print(
            f"  {colorize('Results:', Colors.RED + Colors.BOLD)} "
            f"{passed} passed, {failed} failed"
        )

    print(f"  {colorize('Log Files Created:', Colors.CYAN)} {total_files}")
    print(
        f"  {colorize('Total Duration:', Colors.BLUE)} {format_duration(total_duration)}"
    )
    print()

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

    if failed > 0:
        print(f"  {colorize('Failed Tutorials:', Colors.RED)}")
        for name, success, duration, logs in results:
            if not success:
                print(f"     • {name} ({format_duration(duration)})")
        print()

    if failed == 0:
        print(
            f"  {colorize('All tutorials executed successfully!', Colors.GREEN + Colors.BOLD)}"
        )
        print(
            f"  {colorize('Check examples/logs/tutorials/ for generated artifacts.', Colors.CYAN)}"
        )
        print()


def main():
    """Run all examples and report results."""
    start_time = time.time()

    examples_dir = Path(__file__).parent / "tutorials" / "python"
    example_files = sorted(examples_dir.glob("t*.py"))

    if not example_files:
        print(colorize("No tutorial files found!", Colors.RED))
        return 1

    print_header()

    results = []
    for example_file in example_files:
        success, stdout, stderr, duration, metadata = run_example(example_file)

        # Some async tutorial flows flush on shutdown; a short delay avoids false negatives.
        is_async_example = "async" in example_file.name.lower()
        if is_async_example and success:
            time.sleep(0.5)

        found_logs, _ = verify_log_files(example_file.name)

        print_example_result(
            example_file.name, success, stdout, stderr, duration, metadata, found_logs
        )

        results.append((example_file.name, success, duration, found_logs))

    total_duration = time.time() - start_time
    print_summary(results, total_duration)

    failed = sum(1 for _, success, _, _ in results if not success)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
