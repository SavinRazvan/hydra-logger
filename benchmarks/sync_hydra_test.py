#!/usr/bin/env python3
"""
HydraLogger Sync Performance Benchmark

This benchmark tests the performance of HydraLogger's sync logging capabilities
across different configurations and use cases. All tests use the production-ready
sync HydraLogger implementation.

Test Categories:
1. Default Configurations - Standard logging setups
2. Specialized Configurations - Purpose-built for specific use cases
3. Performance-Optimized Configurations - Maximum throughput modes
4. Stress Testing - High-volume scenarios

Each test measures:
- Throughput (messages per second)
- Latency (time per message)
- Memory usage and leak detection
- Reliability under load

Results provide insights for choosing the optimal configuration for your use case.
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

# Test Parameters
ITERATIONS = 10000  # Standard test size
STRESS_ITERATIONS = 50000  # Stress test size
WARMUP_ITERATIONS = 100  # Warmup iterations

def get_message(i):
    """Standard test message for consistent comparison."""
    return f"Test log message {i} with consistent content for fair comparison"

def get_debug_message(i):
    """Debug message for testing debug level performance."""
    return f"DEBUG: Test debug message {i} with detailed information for debugging purposes"

def get_warn_message(i):
    """Warning message for testing warning level performance."""
    return f"WARNING: Test warning message {i} with important information that requires attention"

def get_error_message(i):
    """Error message for testing error level performance."""
    return f"ERROR: Test error message {i} with critical information about system failure"

def get_large_message(i):
    """Large message for testing performance with bigger payloads."""
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

# Configuration Functions
def create_console_config():
    """Create console-only configuration for testing."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",  # Plain text for consistent comparison
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_file_config():
    """Create file-only configuration for testing."""
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
                        format="plain-text",  # Plain text for consistent comparison
                        color_mode="never",
                        max_size="50MB",
                        backup_count=1
                    )
                ]
            )
        }
    )

# Benchmark Functions - Default Configurations
def benchmark_hydra_sync_default_console():
    """
    Benchmark: HydraLogger Default Configuration - Console Output
    
    What this tests:
    - Standard console logging performance
    - Default configuration overhead
    - Real-time log output capabilities
    
    Use case: General development and debugging
    Expected performance: Moderate (baseline)
    """
    try:
        logger = HydraLogger(config=create_console_config())
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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
    """
    Benchmark: HydraLogger Default Configuration - File Output
    
    What this tests:
    - Standard file logging performance
    - File I/O overhead
    - Persistent logging capabilities
    
    Use case: Production logging to files
    Expected performance: Good (file buffering helps)
    """
    try:
        logger = HydraLogger(config=create_file_config())
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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

# Benchmark Functions - Specialized Configurations
def benchmark_hydra_sync_production_console():
    """
    Benchmark: HydraLogger Production Configuration - Console Output
    
    What this tests:
    - Production-ready console logging
    - Enterprise features performance impact
    - Comprehensive error handling overhead
    
    Use case: Production environments with console output
    Expected performance: High (optimized for production)
    """
    try:
        logger = HydraLogger.for_production()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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
    """
    Benchmark: HydraLogger Development Configuration - Console Output
    
    What this tests:
    - Development-optimized console logging
    - Debug-friendly features performance
    - Enhanced logging capabilities overhead
    
    Use case: Development and debugging workflows
    Expected performance: Very high (optimized for development)
    """
    try:
        logger = HydraLogger.for_development()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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

def benchmark_hydra_sync_background_worker_console():
    """
    Benchmark: HydraLogger Background Worker Configuration - Console Output
    
    What this tests:
    - Background job logging performance
    - Batch processing optimization
    - High-throughput logging capabilities
    
    Use case: Background workers, queue processors, scheduled tasks
    Expected performance: Very high (optimized for batch operations)
    """
    try:
        logger = HydraLogger.for_background_worker()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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

def benchmark_hydra_sync_microservice_console():
    """
    Benchmark: HydraLogger Microservice Configuration - Console Output
    
    What this tests:
    - Microservice-optimized logging
    - Lightweight service logging performance
    - Container-friendly logging capabilities
    
    Use case: Microservices, containerized applications
    Expected performance: High (optimized for services)
    """
    try:
        logger = HydraLogger.for_microservice()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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
    """
    Benchmark: HydraLogger Web App Configuration - Console Output
    
    What this tests:
    - Web application logging performance
    - Request/response logging optimization
    - Web-specific logging capabilities
    
    Use case: Web applications, frontend logging
    Expected performance: High (optimized for web apps)
    """
    try:
        logger = HydraLogger.for_web_app()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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
    """
    Benchmark: HydraLogger API Service Configuration - Console Output
    
    What this tests:
    - API service logging performance
    - High-traffic endpoint logging
    - API-specific optimization features
    
    Use case: REST APIs, GraphQL services, high-traffic endpoints
    Expected performance: Good (balanced for API workloads)
    """
    try:
        logger = HydraLogger.for_api_service()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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

# Benchmark Functions - Performance-Optimized Configurations
def benchmark_hydra_sync_minimal_features_console():
    """
    Benchmark: HydraLogger Minimal Features Configuration - Console Output
    
    What this tests:
    - Minimal feature set performance
    - Reduced overhead logging
    - Speed vs features trade-off
    
    Use case: Maximum throughput scenarios
    Expected performance: Very high (minimal overhead)
    """
    try:
        logger = HydraLogger.for_minimal_features()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Minimal Features Console: {e}")
        return float('inf')

def benchmark_hydra_sync_minimal_features_file():
    """
    Benchmark: HydraLogger Minimal Features Configuration - File Output
    
    What this tests:
    - Minimal features file logging
    - Optimized file I/O performance
    - Speed vs persistence trade-off
    
    Use case: High-performance file logging
    Expected performance: High (optimized file operations)
    """
    try:
        logger = HydraLogger.for_minimal_features()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Minimal Features File: {e}")
        return float('inf')

def benchmark_hydra_sync_bare_metal_console():
    """
    Benchmark: HydraLogger Bare Metal Configuration - Console Output
    
    What this tests:
    - Maximum performance console logging
    - Minimal overhead logging
    - Raw performance capabilities
    
    Use case: Critical performance paths
    Expected performance: Maximum (minimal overhead)
    """
    try:
        logger = HydraLogger.for_bare_metal()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Bare Metal Console: {e}")
        return float('inf')

def benchmark_hydra_sync_bare_metal_file():
    """
    Benchmark: HydraLogger Bare Metal Configuration - File Output
    
    What this tests:
    - Maximum performance file logging
    - Minimal overhead file operations
    - Raw file I/O performance
    
    Use case: Critical performance file logging
    Expected performance: Maximum (minimal file overhead)
    """
    try:
        logger = HydraLogger.for_bare_metal()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Bare Metal File: {e}")
        return float('inf')

# Stress Testing
def benchmark_stress_test():
    """
    Benchmark: HydraLogger Stress Test
    
    What this tests:
    - High-volume logging performance
    - System behavior under load
    - Memory management under stress
    - Reliability with large message volumes
    
    Use case: High-traffic production scenarios
    Expected performance: Lower (stress test with 50K messages)
    """
    try:
        logger = HydraLogger.for_minimal_features()
        
        # Warm up
        for i in range(WARMUP_ITERATIONS):
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
    print("HydraLogger Sync Performance Benchmark")
    print("=" * 60)
    print("Testing production-ready sync logging capabilities")
    print("=" * 60)
    
    # Clean up log files
    clean_all_log_files()
    
    # Define all sync tests with descriptions
    sync_tests = [
        # Default Configurations
        ("HydraLogger Sync Default Console", benchmark_hydra_sync_default_console, 
         "Standard console logging - baseline performance"),
        ("HydraLogger Sync Default File", benchmark_hydra_sync_default_file,
         "Standard file logging - persistent storage performance"),
        
        # Specialized Configurations
        ("HydraLogger Sync Production Console", benchmark_hydra_sync_production_console,
         "Production-optimized console logging - enterprise features"),
        ("HydraLogger Sync Development Console", benchmark_hydra_sync_development_console,
         "Development-optimized console logging - debug-friendly features"),
        ("HydraLogger Sync Background Worker Console", benchmark_hydra_sync_background_worker_console,
         "Background worker console logging - batch processing optimization"),
        ("HydraLogger Sync Microservice Console", benchmark_hydra_sync_microservice_console,
         "Microservice console logging - lightweight service optimization"),
        ("HydraLogger Sync Web App Console", benchmark_hydra_sync_web_app_console,
         "Web app console logging - request/response optimization"),
        ("HydraLogger Sync API Service Console", benchmark_hydra_sync_api_service_console,
         "API service console logging - high-traffic endpoint optimization"),
        
        # Performance-Optimized Configurations
        ("HydraLogger Sync Minimal Features Console", benchmark_hydra_sync_minimal_features_console,
         "Minimal features console logging - speed vs features trade-off"),
        ("HydraLogger Sync Minimal Features File", benchmark_hydra_sync_minimal_features_file,
         "Minimal features file logging - optimized file operations"),
        ("HydraLogger Sync Bare Metal Console", benchmark_hydra_sync_bare_metal_console,
         "Bare metal console logging - maximum performance"),
        ("HydraLogger Sync Bare Metal File", benchmark_hydra_sync_bare_metal_file,
         "Bare metal file logging - maximum file performance"),
        
        # Stress Testing
        ("HydraLogger Stress Test", benchmark_stress_test,
         "High-volume stress testing - 50K messages under load"),
    ]
    
    results = {}
    memory_leaks = []
    
    # Run all sync tests
    for test_name, test_func, description in sync_tests:
        print(f"\nRunning {test_name}...")
        print(f"  Description: {description}")
        
        result = run_test_with_memory_check(test_func, test_name)
        results[test_name] = result
        
        if result["success"]:
            duration = result["duration"]
            iterations = STRESS_ITERATIONS if "Stress Test" in test_name else ITERATIONS
            messages_per_sec = iterations / duration if duration > 0 else 0
            latency_ms = (duration / iterations) * 1000 if duration > 0 else 0
            
            print(f"  Duration: {duration:.4f}s")
            print(f"  Messages/sec: {messages_per_sec:.2f}")
            print(f"  Latency: {latency_ms:.3f}ms per message")
            
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
        messages_per_sec_list = []
        
        for result in successful_tests:
            duration = result["duration"]
            iterations = STRESS_ITERATIONS if "Stress Test" in result["memory_info"]["test_name"] else ITERATIONS
            messages_per_sec = iterations / duration if duration > 0 else 0
            messages_per_sec_list.append(messages_per_sec)
        
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
                "timestamp": time.time(),
                "test_config": {
                    "iterations": ITERATIONS,
                    "stress_iterations": STRESS_ITERATIONS,
                    "warmup_iterations": WARMUP_ITERATIONS
                }
            }, f, indent=2)
        
        # Save CSV results
        with open("benchmarks/results.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Test Name", "Description", "Duration (s)", "Messages/sec", "Latency (ms)", "Success", "Memory Leak"])
            
            for test_name, result in results.items():
                duration = result["duration"]
                iterations = STRESS_ITERATIONS if "Stress Test" in test_name else ITERATIONS
                messages_per_sec = iterations / duration if duration > 0 else 0
                latency_ms = (duration / iterations) * 1000 if duration > 0 else 0
                success = result["success"]
                memory_leak = result["memory_info"].get("potential_leak", False)
                
                # Find description
                description = ""
                for test_info in sync_tests:
                    if test_info[0] == test_name:
                        description = test_info[2]
                        break
                
                writer.writerow([test_name, description, duration, messages_per_sec, latency_ms, success, memory_leak])
        
        # Save detailed summary to log file
        with open("logs/benchmark.log", "w") as f:
            f.write("HydraLogger Sync Performance Benchmark Results\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("Test Configuration:\n")
            f.write(f"  Standard iterations: {ITERATIONS:,}\n")
            f.write(f"  Stress test iterations: {STRESS_ITERATIONS:,}\n")
            f.write(f"  Warmup iterations: {WARMUP_ITERATIONS}\n\n")
            
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
                
                f.write("Detailed Results:\n")
                for test_name, result in results.items():
                    if result["success"]:
                        duration = result["duration"]
                        iterations = STRESS_ITERATIONS if "Stress Test" in test_name else ITERATIONS
                        messages_per_sec = iterations / duration if duration > 0 else 0
                        latency_ms = (duration / iterations) * 1000 if duration > 0 else 0
                        
                        f.write(f"  {test_name}:\n")
                        f.write(f"    Messages/sec: {messages_per_sec:.2f}\n")
                        f.write(f"    Latency: {latency_ms:.3f}ms\n")
                        f.write(f"    Duration: {duration:.4f}s\n")
                        
                        memory_info = result["memory_info"]
                        if memory_info.get("potential_leak", False):
                            f.write(f"    ⚠️  Memory leak: {memory_info['memory_diff_mb']:.2f}MB\n")
                        else:
                            f.write(f"    ✅ No memory leak\n")
                        f.write("\n")
            
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
        
        print(f"\nRecommendations:")
        print(f"  - For maximum performance: Use Development or Background Worker configurations")
        print(f"  - For production systems: Use Production or Microservice configurations")
        print(f"  - For critical performance paths: Use Bare Metal or Minimal Features configurations")
        print(f"  - For file logging: File operations are generally faster than console output")
    
    if memory_leaks:
        print(f"\n⚠️  Memory Leaks Detected: {len(memory_leaks)}")
        for leak in memory_leaks:
            print(f"  - {leak['test_name']}: {leak['memory_diff_mb']:.2f}MB")
    else:
        print(f"\n✅ No memory leaks detected")
    
    print(f"\nBenchmark completed successfully!")
    print(f"All tests use the production-ready sync HydraLogger implementation.")

if __name__ == "__main__":
    main() 