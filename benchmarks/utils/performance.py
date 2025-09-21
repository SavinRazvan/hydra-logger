"""
Performance measurement utilities for benchmarks.
"""

import psutil
import time
from typing import Dict, Any, List, Optional
from .models import BenchmarkResult


def measure_memory() -> float:
    """Measure current memory usage in MB."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # Convert to MB
    except Exception:
        return 0.0


def calculate_performance_metrics(iterations: int, 
                                start_time: float, 
                                end_time: float,
                                memory_start: float,
                                memory_end: float) -> Dict[str, Any]:
    """Calculate performance metrics from timing data."""
    total_time = end_time - start_time
    messages_per_second = iterations / total_time if total_time > 0 else 0
    avg_time_per_message = total_time / iterations if iterations > 0 else 0
    memory_delta = memory_end - memory_start
    
    return {
        'total_time': total_time,
        'messages_per_second': messages_per_second,
        'avg_time_per_message': avg_time_per_message,
        'memory_start_mb': memory_start,
        'memory_end_mb': memory_end,
        'memory_delta_mb': memory_delta
    }


def analyze_results(results: List[BenchmarkResult]) -> Dict[str, Any]:
    """Analyze a list of benchmark results."""
    if not results:
        return {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'success_rate': 0.0,
            'average_speed': 0.0,
            'fastest_speed': 0.0,
            'slowest_speed': 0.0,
            'total_iterations': 0,
            'total_time': 0.0
        }
    
    # Basic statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if not r.errors_occurred)
    failed_tests = total_tests - successful_tests
    success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
    
    # Performance statistics
    speeds = [r.messages_per_second for r in results if not r.errors_occurred]
    average_speed = sum(speeds) / len(speeds) if speeds else 0.0
    fastest_speed = max(speeds) if speeds else 0.0
    slowest_speed = min(speeds) if speeds else 0.0
    
    # Total statistics
    total_iterations = sum(r.iterations for r in results)
    total_time = sum(r.total_time for r in results)
    
    return {
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'failed_tests': failed_tests,
        'success_rate': success_rate,
        'average_speed': average_speed,
        'fastest_speed': fastest_speed,
        'slowest_speed': slowest_speed,
        'total_iterations': total_iterations,
        'total_time': total_time
    }


def format_performance_summary(results: List[BenchmarkResult]) -> str:
    """Format a human-readable performance summary."""
    analysis = analyze_results(results)
    
    summary = []
    summary.append("📊 PERFORMANCE SUMMARY")
    summary.append("=" * 50)
    summary.append(f"Total Tests: {analysis['total_tests']}")
    summary.append(f"Successful: {analysis['successful_tests']} ({analysis['success_rate']:.1%})")
    summary.append(f"Failed: {analysis['failed_tests']}")
    
    if analysis['successful_tests'] > 0:
        summary.append(f"Average Speed: {analysis['average_speed']:,.0f} msg/s")
        summary.append(f"Fastest Speed: {analysis['fastest_speed']:,.0f} msg/s")
        summary.append(f"Slowest Speed: {analysis['slowest_speed']:,.0f} msg/s")
    
    summary.append(f"Total Iterations: {analysis['total_iterations']:,}")
    summary.append(f"Total Time: {analysis['total_time']:.3f}s")
    
    return "\n".join(summary)
