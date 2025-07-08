#!/usr/bin/env python3
"""
Performance Benchmark: HydraLogger Performance Analysis

Tests:
- Console logging (HydraLogger Sync Default/High Performance/Ultra Fast)
- File logging (HydraLogger Sync Default/High Performance/Ultra Fast)
- Various configurations and message types

Features:
- Memory cleaning between tests
- Leak detection and monitoring
- 1-second wait between tests for isolation
- Comprehensive results display at the end
"""

import asyncio
import time
import csv
import json
import traceback
import gc
import psutil
import os
from typing import List, Dict, Any
from pathlib import Path
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Parameter grid for tests
ITERATIONS = 10000
STRESS_ITERATIONS = 50000  # For stress testing

def get_message(i):
    return f"Test log message {i} with consistent content for fair comparison"

def get_debug_message(i):
    return f"DEBUG: Test debug message {i} with detailed information for debugging purposes"

def get_warn_message(i):
    return f"WARNING: Test warning message {i} with important information that requires attention"

def get_error_message(i):
    return f"ERROR: Test error message {i} with critical information about system failure"

def get_large_message(i):
    return f"Test log message {i} with very long content that includes additional details about the system state, user actions, and various parameters that might be logged in a real application scenario. This message is designed to test how the logger handles larger payloads and whether it affects performance significantly. The message includes: timestamp={i}, user_id=user_{i}, action=test_action_{i}, status=active, priority=normal, category=benchmark, source=test_suite, version=1.0.0, environment=development, and various other metadata fields that might be present in production logging scenarios."

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def clean_memory():
    """Force garbage collection and clean memory."""
    gc.collect()
    time.sleep(0.1)  # Brief pause to allow cleanup

def check_memory_leak(before_mb: float, after_mb: float, test_name: str) -> Dict[str, Any]:
    """Check for potential memory leaks."""
    memory_diff = after_mb - before_mb
    leak_threshold = 10.0  # 10MB threshold for potential leak
    
    return {
        "test_name": test_name,
        "memory_before_mb": before_mb,
        "memory_after_mb": after_mb,
        "memory_diff_mb": memory_diff,
        "potential_leak": memory_diff > leak_threshold,
        "leak_threshold_mb": leak_threshold
    }

# Configs
def create_console_config():
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",  # Plain text format for consistent comparison
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_file_config():
    log_path = "logs/benchmark.log"
    try:
        Path(log_path).unlink()
    except Exception:
        pass
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path=log_path,
                        format="plain-text",  # Plain text format for consistent comparison
                        color_mode="never",
                        max_size="50MB",
                        backup_count=1
                    )
                ]
            )
        }
    )

# Sync benchmarks - Default
def benchmark_hydra_sync_default_console():
    """Benchmark HydraLogger sync default mode for console logging."""
    try:
        logger = HydraLogger(config=create_console_config())
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Default Console: {e}")
        return float('inf')

def benchmark_hydra_sync_default_file():
    """Benchmark HydraLogger sync default mode for file logging."""
    try:
        logger = HydraLogger(config=create_file_config())
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Default File: {e}")
        return float('inf')

# Sync benchmarks - High Performance
def benchmark_hydra_sync_high_performance_console():
    """Benchmark HydraLogger sync high performance mode for console logging."""
    try:
        logger = HydraLogger.for_high_performance()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync High Performance Console: {e}")
        return float('inf')

def benchmark_hydra_sync_high_performance_file():
    """Benchmark HydraLogger sync high performance mode for file logging."""
    try:
        logger = HydraLogger.for_high_performance()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync High Performance File: {e}")
        return float('inf')

# Sync benchmarks - Ultra Fast
def benchmark_hydra_sync_ultra_fast_console():
    """Benchmark HydraLogger sync ultra fast mode for console logging."""
    try:
        logger = HydraLogger.for_ultra_fast()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Ultra Fast Console: {e}")
        return float('inf')

def benchmark_hydra_sync_ultra_fast_file():
    """Benchmark HydraLogger sync ultra fast mode for file logging."""
    try:
        logger = HydraLogger.for_ultra_fast()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Ultra Fast File: {e}")
        return float('inf')

# Additional sync benchmarks
def benchmark_hydra_sync_production_console():
    """Benchmark HydraLogger sync production mode for console logging."""
    try:
        logger = HydraLogger.for_production()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Production Console: {e}")
        return float('inf')

def benchmark_hydra_sync_development_console():
    """Benchmark HydraLogger sync development mode for console logging."""
    try:
        logger = HydraLogger.for_development()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Development Console: {e}")
        return float('inf')

def benchmark_hydra_sync_microservice_console():
    """Benchmark HydraLogger sync microservice mode for console logging."""
    try:
        logger = HydraLogger.for_microservice()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Microservice Console: {e}")
        return float('inf')

def benchmark_hydra_sync_web_app_console():
    """Benchmark HydraLogger sync web app mode for console logging."""
    try:
        logger = HydraLogger.for_web_app()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Web App Console: {e}")
        return float('inf')

def benchmark_hydra_sync_api_service_console():
    """Benchmark HydraLogger sync API service mode for console logging."""
    try:
        logger = HydraLogger.for_api_service()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync API Service Console: {e}")
        return float('inf')

def benchmark_hydra_sync_background_worker_console():
    """Benchmark HydraLogger sync background worker mode for console logging."""
    try:
        logger = HydraLogger.for_background_worker()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Background Worker Console: {e}")
        return float('inf')

def benchmark_stress_test():
    """Stress test with high volume logging."""
    try:
        logger = HydraLogger.for_high_performance()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Stress test
        start = time.perf_counter()
        for i in range(STRESS_ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Stress Test: {e}")
        return float('inf')

def run_test_with_memory_check(test_func, test_name, *args, **kwargs):
    """Run a test with memory leak detection."""
    try:
        clean_memory()
        memory_before = get_memory_usage()
        
        result = test_func(*args, **kwargs)
        
        clean_memory()
        memory_after = get_memory_usage()
        
        memory_info = check_memory_leak(memory_before, memory_after, test_name)
        
        return {
            "duration": result,
            "memory_info": memory_info,
            "success": result != float('inf')
        }
    except Exception as e:
        print(f"ERROR in {test_name}: {e}")
        return {
            "duration": float('inf'),
            "memory_info": {"test_name": test_name, "error": str(e)},
            "success": False
        }

def clean_all_log_files():
    """Clean up all log files before running tests."""
    log_files = [
        "logs/benchmark.log",
        "logs/app.log",
        "logs/error.log",
        "logs/debug.log"
    ]
    
    for log_file in log_files:
        try:
            Path(log_file).unlink()
        except Exception:
            pass

def main():
    """Main benchmark execution."""
    print("HydraLogger Performance Benchmark (Sync Only)")
    print("=" * 60)
    
    # Clean up log files
    clean_all_log_files()
    
    # Define all sync tests
    sync_tests = [
        ("HydraLogger Sync Default Console", benchmark_hydra_sync_default_console),
        ("HydraLogger Sync Default File", benchmark_hydra_sync_default_file),
        ("HydraLogger Sync High Performance Console", benchmark_hydra_sync_high_performance_console),
        ("HydraLogger Sync High Performance File", benchmark_hydra_sync_high_performance_file),
        ("HydraLogger Sync Ultra Fast Console", benchmark_hydra_sync_ultra_fast_console),
        ("HydraLogger Sync Ultra Fast File", benchmark_hydra_sync_ultra_fast_file),
        ("HydraLogger Sync Production Console", benchmark_hydra_sync_production_console),
        ("HydraLogger Sync Development Console", benchmark_hydra_sync_development_console),
        ("HydraLogger Sync Microservice Console", benchmark_hydra_sync_microservice_console),
        ("HydraLogger Sync Web App Console", benchmark_hydra_sync_web_app_console),
        ("HydraLogger Sync API Service Console", benchmark_hydra_sync_api_service_console),
        ("HydraLogger Sync Background Worker Console", benchmark_hydra_sync_background_worker_console),
        ("HydraLogger Stress Test", benchmark_stress_test),
    ]
    
    results = {}
    memory_leaks = []
    
    # Run all sync tests
    for test_name, test_func in sync_tests:
        print(f"\nRunning {test_name}...")
        
        result = run_test_with_memory_check(test_func, test_name)
        results[test_name] = result
        
        if result["success"]:
            duration = result["duration"]
            messages_per_sec = ITERATIONS / duration if duration > 0 else 0
            print(f"  Duration: {duration:.4f}s")
            print(f"  Messages/sec: {messages_per_sec:.2f}")
            
            # Check for memory leaks
            memory_info = result["memory_info"]
            if memory_info.get("potential_leak", False):
                memory_leaks.append(memory_info)
                print(f"  ⚠️  Potential memory leak detected: {memory_info['memory_diff_mb']:.2f}MB")
            else:
                print(f"  ✅ No memory leak detected")
        else:
            print(f"  ❌ Test failed")
        
        # Wait between tests for isolation
        time.sleep(1)
    
    # Calculate summary statistics
    successful_tests = [r for r in results.values() if r["success"]]
    
    if successful_tests:
        durations = [r["duration"] for r in successful_tests]
        messages_per_sec_list = [ITERATIONS / d for d in durations if d > 0]
        
        summary = {
            "total_tests": len(sync_tests),
            "successful_tests": len(successful_tests),
            "failed_tests": len(sync_tests) - len(successful_tests),
            "best_performance": max(messages_per_sec_list) if messages_per_sec_list else 0,
            "worst_performance": min(messages_per_sec_list) if messages_per_sec_list else 0,
            "average_performance": sum(messages_per_sec_list) / len(messages_per_sec_list) if messages_per_sec_list else 0,
            "best_duration": min(durations),
            "worst_duration": max(durations),
            "average_duration": sum(durations) / len(durations)
        }
    else:
        summary = {
            "total_tests": len(sync_tests),
            "successful_tests": 0,
            "failed_tests": len(sync_tests),
            "best_performance": 0,
            "worst_performance": 0,
            "average_performance": 0,
            "best_duration": 0,
            "worst_duration": 0,
            "average_duration": 0
        }
    
    # Save results
    try:
        os.makedirs("benchmarks", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Save JSON results
        with open("benchmarks/results.json", "w") as f:
            json.dump({
                "summary": summary,
                "results": results,
                "memory_leaks": memory_leaks,
                "timestamp": time.time()
            }, f, indent=2)
        
        # Save CSV results
        with open("benchmarks/results.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Duration (s)", "Messages/sec", "Success", "Memory Leak"])
            
            for test_name, result in results.items():
                duration = result["duration"]
                messages_per_sec = ITERATIONS / duration if duration > 0 else 0
                success = result["success"]
                memory_leak = result["memory_info"].get("potential_leak", False)
                
                writer.writerow([test_name, duration, messages_per_sec, success, memory_leak])
        
        # Save summary to log file
        with open("logs/benchmark.log", "w") as f:
            f.write("HydraLogger Performance Benchmark Results\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Successful: {summary['successful_tests']}\n")
            f.write(f"Failed: {summary['failed_tests']}\n\n")
            
            if summary['successful_tests'] > 0:
                f.write("Performance Summary:\n")
                f.write(f"  Best Performance: {summary['best_performance']:.2f} messages/sec\n")
                f.write(f"  Worst Performance: {summary['worst_performance']:.2f} messages/sec\n")
                f.write(f"  Average Performance: {summary['average_performance']:.2f} messages/sec\n\n")
                
                f.write("Duration Summary:\n")
                f.write(f"  Best Duration: {summary['best_duration']:.4f}s\n")
                f.write(f"  Worst Duration: {summary['worst_duration']:.4f}s\n")
                f.write(f"  Average Duration: {summary['average_duration']:.4f}s\n\n")
            
            if memory_leaks:
                f.write("Memory Leaks Detected:\n")
                for leak in memory_leaks:
                    f.write(f"  - {leak['test_name']}: {leak['memory_diff_mb']:.2f}MB\n")
            else:
                f.write("No memory leaks detected.\n")
        
        print(f"\nResults saved to:")
        print(f"  - benchmarks/results.json")
        print(f"  - benchmarks/results.csv")
        print(f"  - logs/benchmark.log")
        
    except Exception as e:
        print(f"Failed to save results: {e}")
    
    # Print final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    
    if summary['successful_tests'] > 0:
        print(f"\nPerformance Summary:")
        print(f"  Best Performance: {summary['best_performance']:.2f} messages/sec")
        print(f"  Worst Performance: {summary['worst_performance']:.2f} messages/sec")
        print(f"  Average Performance: {summary['average_performance']:.2f} messages/sec")
        
        print(f"\nDuration Summary:")
        print(f"  Best Duration: {summary['best_duration']:.4f}s")
        print(f"  Worst Duration: {summary['worst_duration']:.4f}s")
        print(f"  Average Duration: {summary['average_duration']:.4f}s")
    
    if memory_leaks:
        print(f"\n⚠️  Memory Leaks Detected: {len(memory_leaks)}")
        for leak in memory_leaks:
            print(f"  - {leak['test_name']}: {leak['memory_diff_mb']:.2f}MB")
    else:
        print(f"\n✅ No memory leaks detected")
    
    print(f"\nBenchmark completed successfully!")

if __name__ == "__main__":
    main() 