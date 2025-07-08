#!/usr/bin/env python3
"""
Performance Benchmark: HydraLogger Performance Analysis

Tests:
- Console logging (HydraLogger Sync Default/High Performance/Ultra Fast, HydraLogger Async Default/High Performance/Ultra Fast, Loguru)
- File logging (HydraLogger Sync Default/High Performance/Ultra Fast, HydraLogger Async Default/High Performance/Ultra Fast, Loguru)
- Parameter grid search for HydraLogger Async batch settings

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
from hydra_logger import HydraLogger, AsyncHydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from loguru import logger as loguru_logger

# Parameter grid for async
ITERATIONS = 10000
STRESS_ITERATIONS = 50000  # For stress testing
CONCURRENT_TESTS = 1000    # For concurrent testing

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
    log_path = "logs/comprehensive_benchmark.log"
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

# Async benchmarks - Default
async def benchmark_hydra_async_default_console():
    """Benchmark HydraLogger async default mode for console logging."""
    try:
        logger = AsyncHydraLogger(
            config=create_console_config(),
            queue_size=10000,
            batch_size=100,
            batch_timeout=1.0
        )
        await logger.initialize()
        # Warm up
        for i in range(100):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.05)
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.2)
        end = time.perf_counter()
        await logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Async Default Console: {e}")
        return float('inf')

async def benchmark_hydra_async_default_file():
    """Benchmark HydraLogger async default mode for file logging."""
    try:
        logger = AsyncHydraLogger(
            config=create_file_config(),
            queue_size=10000,
            batch_size=100,
            batch_timeout=1.0
        )
        await logger.initialize()
        # Warm up
        for i in range(100):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.05)
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.2)
        end = time.perf_counter()
        await logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Async Default File: {e}")
        return float('inf')

# Async benchmarks - High Performance
async def benchmark_hydra_async_high_performance_console():
    """Benchmark HydraLogger async high performance mode for console logging."""
    try:
        logger = AsyncHydraLogger.for_high_performance()
        await logger.initialize()
        # Warm up
        for i in range(100):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.05)
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.2)
        end = time.perf_counter()
        await logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Async High Performance Console: {e}")
        return float('inf')

async def benchmark_hydra_async_high_performance_file():
    """Benchmark HydraLogger async high performance mode for file logging."""
    try:
        logger = AsyncHydraLogger.for_high_performance()
        await logger.initialize()
        # Warm up
        for i in range(100):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.05)
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.2)
        end = time.perf_counter()
        await logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Async High Performance File: {e}")
        return float('inf')

# Async benchmarks - Ultra Fast
async def benchmark_hydra_async_ultra_fast_console():
    """Benchmark HydraLogger async ultra fast mode for console logging."""
    try:
        logger = AsyncHydraLogger.for_ultra_fast()
        await logger.initialize()
        # Warm up
        for i in range(100):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.05)
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.2)
        end = time.perf_counter()
        await logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Async Ultra Fast Console: {e}")
        return float('inf')

async def benchmark_hydra_async_ultra_fast_file():
    """Benchmark HydraLogger async ultra fast mode for file logging."""
    try:
        logger = AsyncHydraLogger.for_ultra_fast()
        await logger.initialize()
        # Warm up
        for i in range(100):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.05)
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            await logger.info("DEFAULT", get_message(i))
        await asyncio.sleep(0.2)
        end = time.perf_counter()
        await logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Async Ultra Fast File: {e}")
        return float('inf')

# Loguru benchmarks
def benchmark_loguru_console():
    """Benchmark Loguru for console logging."""
    try:
        loguru_logger.remove()
        loguru_logger.add(lambda msg: print(msg, end=""), format="{message}", level="INFO")
        # Warm up
        for i in range(100):
            loguru_logger.info(get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            loguru_logger.info(get_message(i))
        end = time.perf_counter()
        loguru_logger.remove()
        return end - start
    except Exception as e:
        print(f"ERROR in Loguru Console: {e}")
        return float('inf')

def benchmark_loguru_file():
    """Benchmark Loguru for file logging."""
    try:
        loguru_logger.remove()
        loguru_logger.add("logs/loguru_comprehensive.log", format="{message}", level="INFO")
        # Warm up
        for i in range(100):
            loguru_logger.info(get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            loguru_logger.info(get_message(i))
        end = time.perf_counter()
        loguru_logger.remove()
        return end - start
    except Exception as e:
        print(f"ERROR in Loguru File: {e}")
        return float('inf')

# Additional test configurations
def create_debug_config():
    """Create configuration for DEBUG level testing."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_error_config():
    """Create configuration for ERROR level testing."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    )
                ]
            )
        }
    )

def create_multi_destination_config():
    """Create configuration for multi-destination testing."""
    return LoggingConfig(
        layers={
            "DEFAULT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="never"
                    ),
                    LogDestination(
                        type="file",
                        path="logs/multi_destination.log",
                        format="plain-text",
                        color_mode="never",
                        max_size="50MB",
                        backup_count=1
                    )
                ]
            )
        }
    )

# Additional benchmark functions
def benchmark_hydra_sync_debug_console():
    """Test HydraLogger sync with DEBUG level."""
    try:
        logger = HydraLogger(config=create_debug_config())
        # Warm up
        for i in range(100):
            logger.debug("DEFAULT", get_debug_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.debug("DEFAULT", get_debug_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Debug Console: {e}")
        return float('inf')

def benchmark_hydra_sync_error_console():
    """Test HydraLogger sync with ERROR level."""
    try:
        logger = HydraLogger(config=create_error_config())
        # Warm up
        for i in range(100):
            logger.error("DEFAULT", get_error_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.error("DEFAULT", get_error_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Error Console: {e}")
        return float('inf')

def benchmark_hydra_sync_large_messages():
    """Test HydraLogger sync with large messages."""
    try:
        logger = HydraLogger(config=create_console_config())
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_large_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            logger.info("DEFAULT", get_large_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in HydraLogger Sync Large Messages: {e}")
        return float('inf')

def benchmark_hydra_sync_multi_destination():
    """Test HydraLogger sync with multiple destinations."""
    try:
        logger = HydraLogger(config=create_multi_destination_config())
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
        print(f"ERROR in HydraLogger Sync Multi Destination: {e}")
        return float('inf')

def benchmark_stress_test():
    """Stress test with higher iterations."""
    try:
        logger = HydraLogger.for_high_performance()
        # Warm up
        for i in range(100):
            logger.info("DEFAULT", get_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(STRESS_ITERATIONS):
            logger.info("DEFAULT", get_message(i))
        end = time.perf_counter()
        logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Stress Test: {e}")
        return float('inf')

async def benchmark_concurrent_logging():
    """Test concurrent logging with multiple async tasks."""
    try:
        logger = AsyncHydraLogger.for_high_performance()
        await logger.initialize()
        
        async def log_task(task_id):
            for i in range(CONCURRENT_TESTS):
                await logger.info("DEFAULT", f"Task {task_id}: {get_message(i)}")
        
        # Create multiple concurrent tasks
        tasks = [log_task(i) for i in range(5)]  # 5 concurrent tasks
        
        start = time.perf_counter()
        await asyncio.gather(*tasks)
        end = time.perf_counter()
        
        await logger.close()
        return end - start
    except Exception as e:
        print(f"ERROR in Concurrent Logging: {e}")
        return float('inf')

def benchmark_loguru_large_messages():
    """Test Loguru with large messages."""
    try:
        loguru_logger.remove()
        loguru_logger.add(lambda msg: print(msg, end=""), format="{message}", level="INFO")
        # Warm up
        for i in range(100):
            loguru_logger.info(get_large_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            loguru_logger.info(get_large_message(i))
        end = time.perf_counter()
        loguru_logger.remove()
        return end - start
    except Exception as e:
        print(f"ERROR in Loguru Large Messages: {e}")
        return float('inf')

def benchmark_loguru_debug():
    """Test Loguru with DEBUG level."""
    try:
        loguru_logger.remove()
        loguru_logger.add(lambda msg: print(msg, end=""), format="{message}", level="DEBUG")
        # Warm up
        for i in range(100):
            loguru_logger.debug(get_debug_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            loguru_logger.debug(get_debug_message(i))
        end = time.perf_counter()
        loguru_logger.remove()
        return end - start
    except Exception as e:
        print(f"ERROR in Loguru Debug: {e}")
        return float('inf')

def benchmark_loguru_error():
    """Test Loguru with ERROR level."""
    try:
        loguru_logger.remove()
        loguru_logger.add(lambda msg: print(msg, end=""), format="{message}", level="ERROR")
        # Warm up
        for i in range(100):
            loguru_logger.error(get_error_message(i))
        # Benchmark
        start = time.perf_counter()
        for i in range(ITERATIONS):
            loguru_logger.error(get_error_message(i))
        end = time.perf_counter()
        loguru_logger.remove()
        return end - start
    except Exception as e:
        print(f"ERROR in Loguru Error: {e}")
        return float('inf')

async def run_test_with_memory_check(test_func, test_name, *args, **kwargs):
    """Run a test with memory monitoring and cleanup."""
    print(f"\n🧪 Running: {test_name}")
    
    # Clean memory before test
    clean_memory()
    memory_before = get_memory_usage()
    
    # Run test
    if asyncio.iscoroutinefunction(test_func):
        # For async functions, await them directly
        duration = await test_func(*args, **kwargs)
    else:
        # For sync functions, run them normally
        duration = test_func(*args, **kwargs)
    
    # Clean memory after test
    clean_memory()
    memory_after = get_memory_usage()
    
    # Check for memory leaks
    leak_info = check_memory_leak(memory_before, memory_after, test_name)
    
    # Wait 1 second between tests
    print(f"⏳ Waiting 1 second before next test...")
    time.sleep(1.0)
    
    return duration, leak_info

def clean_all_log_files():
    """Remove all relevant log files before running benchmarks."""
    log_files = [
        "logs/comprehensive_benchmark.log",
        "logs/loguru_comprehensive.log",
        "logs/multi_destination.log"
    ]
    for path in log_files:
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Warning: Could not remove {path}: {e}")

async def main():
    # Clean up all log files before running any tests
    clean_all_log_files()
    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    memory_leaks: List[Dict[str, Any]] = []
    
    print("=" * 60)
    print("COMPREHENSIVE PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"Testing {ITERATIONS:,} logs per configuration")
    print("Features: Memory cleaning, leak detection, 1s isolation")
    print("=" * 60)
    
    # Console benchmarks
    print("\n" + "=" * 40)
    print("CONSOLE LOGGING TESTS")
    print("=" * 40)
    
    # Test configurations
    console_tests = [
        ("HydraLogger Sync Default Console", benchmark_hydra_sync_default_console),
        ("HydraLogger Sync High Performance Console", benchmark_hydra_sync_high_performance_console),
        ("HydraLogger Sync Ultra Fast Console", benchmark_hydra_sync_ultra_fast_console),
        ("HydraLogger Async Default Console", benchmark_hydra_async_default_console),
        ("HydraLogger Async High Performance Console", benchmark_hydra_async_high_performance_console),
        ("HydraLogger Async Ultra Fast Console", benchmark_hydra_async_ultra_fast_console),
        ("Loguru Console", benchmark_loguru_console),
    ]
    
    for test_name, test_func in console_tests:
        try:
            duration, leak_info = await run_test_with_memory_check(test_func, test_name)
            
            logs_per_sec = ITERATIONS / duration if duration > 0 and duration != float('inf') else 0
            
            # Determine logger type and variant
            if "HydraLogger" in test_name:
                if "Sync" in test_name:
                    mode = "sync"
                else:
                    mode = "async"
                
                if "Default" in test_name:
                    variant = "default"
                elif "High Performance" in test_name:
                    variant = "high_performance"
                elif "Ultra Fast" in test_name:
                    variant = "ultra_fast"
                else:
                    variant = "default"
            else:
                mode = "sync"
                variant = "default"
            
            results.append({
                "logger": "HydraLogger" if "HydraLogger" in test_name else "Loguru",
                "mode": mode,
                "variant": variant,
                "destination": "console",
                "batch_size": None,
                "batch_timeout": None,
                "duration": duration,
                "logs_per_sec": logs_per_sec,
                "error": None,
                "memory_before_mb": leak_info["memory_before_mb"],
                "memory_after_mb": leak_info["memory_after_mb"],
                "memory_diff_mb": leak_info["memory_diff_mb"],
                "potential_leak": leak_info["potential_leak"]
            })
            
            print(f"✅ {test_name}: {logs_per_sec:,.0f} logs/sec ({duration:.3f}s)")
            if leak_info["potential_leak"]:
                print(f"⚠️  Potential memory leak: {leak_info['memory_diff_mb']:.2f}MB")
                memory_leaks.append(leak_info)
                
        except Exception as e:
            tb = traceback.format_exc()
            failures.append({"test": test_name, "error": str(e), "traceback": tb})
            print(f"❌ ERROR in {test_name}: {e}")
    
    # File benchmarks
    print("\n" + "=" * 40)
    print("FILE LOGGING TESTS")
    print("=" * 40)
    
    file_tests = [
        ("HydraLogger Sync Default File", benchmark_hydra_sync_default_file),
        ("HydraLogger Sync High Performance File", benchmark_hydra_sync_high_performance_file),
        ("HydraLogger Sync Ultra Fast File", benchmark_hydra_sync_ultra_fast_file),
        ("HydraLogger Async Default File", benchmark_hydra_async_default_file),
        ("HydraLogger Async High Performance File", benchmark_hydra_async_high_performance_file),
        ("HydraLogger Async Ultra Fast File", benchmark_hydra_async_ultra_fast_file),
        ("Loguru File", benchmark_loguru_file),
    ]
    
    for test_name, test_func in file_tests:
        try:
            duration, leak_info = await run_test_with_memory_check(test_func, test_name)
            
            logs_per_sec = ITERATIONS / duration if duration > 0 and duration != float('inf') else 0
            
            # Determine logger type and variant
            if "HydraLogger" in test_name:
                if "Sync" in test_name:
                    mode = "sync"
                else:
                    mode = "async"
                
                if "Default" in test_name:
                    variant = "default"
                elif "High Performance" in test_name:
                    variant = "high_performance"
                elif "Ultra Fast" in test_name:
                    variant = "ultra_fast"
                else:
                    variant = "default"
            else:
                mode = "sync"
                variant = "default"
            
            results.append({
                "logger": "HydraLogger" if "HydraLogger" in test_name else "Loguru",
                "mode": mode,
                "variant": variant,
                "destination": "file",
                "batch_size": None,
                "batch_timeout": None,
                "duration": duration,
                "logs_per_sec": logs_per_sec,
                "error": None,
                "memory_before_mb": leak_info["memory_before_mb"],
                "memory_after_mb": leak_info["memory_after_mb"],
                "memory_diff_mb": leak_info["memory_diff_mb"],
                "potential_leak": leak_info["potential_leak"]
            })
            
            print(f"✅ {test_name}: {logs_per_sec:,.0f} logs/sec ({duration:.3f}s)")
            if leak_info["potential_leak"]:
                print(f"⚠️  Potential memory leak: {leak_info['memory_diff_mb']:.2f}MB")
                memory_leaks.append(leak_info)
                
        except Exception as e:
            tb = traceback.format_exc()
            failures.append({"test": test_name, "error": str(e), "traceback": tb})
            print(f"❌ ERROR in {test_name}: {e}")
    
    # Additional tests
    print("\n" + "=" * 40)
    print("ADDITIONAL TESTS")
    print("=" * 40)
    
    additional_tests = [
        ("HydraLogger Sync Debug Console", benchmark_hydra_sync_debug_console),
        ("HydraLogger Sync Error Console", benchmark_hydra_sync_error_console),
        ("HydraLogger Sync Large Messages", benchmark_hydra_sync_large_messages),
        ("HydraLogger Sync Multi Destination", benchmark_hydra_sync_multi_destination),
        ("Stress Test", benchmark_stress_test),
        ("Concurrent Logging", benchmark_concurrent_logging),
        ("Loguru Large Messages", benchmark_loguru_large_messages),
        ("Loguru Debug", benchmark_loguru_debug),
        ("Loguru Error", benchmark_loguru_error),
    ]
    
    for test_name, test_func in additional_tests:
        try:
            duration, leak_info = await run_test_with_memory_check(test_func, test_name)
            
            logs_per_sec = ITERATIONS / duration if duration > 0 and duration != float('inf') else 0
            
            # Determine logger type and variant
            if "HydraLogger" in test_name:
                if "Sync" in test_name:
                    mode = "sync"
                else:
                    mode = "async"
                
                if "Default" in test_name:
                    variant = "default"
                elif "High Performance" in test_name:
                    variant = "high_performance"
                elif "Ultra Fast" in test_name:
                    variant = "ultra_fast"
                else:
                    variant = "default"
            else:
                mode = "sync"
                variant = "default"
            
            results.append({
                "logger": "HydraLogger" if "HydraLogger" in test_name else "Loguru",
                "mode": mode,
                "variant": variant,
                "destination": "console",
                "batch_size": None,
                "batch_timeout": None,
                "duration": duration,
                "logs_per_sec": logs_per_sec,
                "error": None,
                "memory_before_mb": leak_info["memory_before_mb"],
                "memory_after_mb": leak_info["memory_after_mb"],
                "memory_diff_mb": leak_info["memory_diff_mb"],
                "potential_leak": leak_info["potential_leak"]
            })
            
            print(f"✅ {test_name}: {logs_per_sec:,.0f} logs/sec ({duration:.3f}s)")
            if leak_info["potential_leak"]:
                print(f"⚠️  Potential memory leak: {leak_info['memory_diff_mb']:.2f}MB")
                memory_leaks.append(leak_info)
                
        except Exception as e:
            tb = traceback.format_exc()
            failures.append({"test": test_name, "error": str(e), "traceback": tb})
            print(f"❌ ERROR in {test_name}: {e}")
    
    # Final cleanup
    clean_memory()
    
    # Analysis and Results Display
    print("\n" + "=" * 60)
    print("COMPREHENSIVE RESULTS ANALYSIS")
    print("=" * 60)
    
    # Find best in each category
    console_results = [r for r in results if r["destination"] == "console" and not r["error"]]
    file_results = [r for r in results if r["destination"] == "file" and not r["error"]]
    
    if console_results:
        best_console = max(console_results, key=lambda x: x["logs_per_sec"])
        print(f"🏆 Best Console: {best_console['logger']} {best_console['mode']} {best_console['variant']} ({best_console['logs_per_sec']:,.0f} logs/sec)")
    else:
        print("❌ No successful console results.")
    
    if file_results:
        best_file = max(file_results, key=lambda x: x["logs_per_sec"])
        print(f"🏆 Best File: {best_file['logger']} {best_file['mode']} {best_file['variant']} ({best_file['logs_per_sec']:,.0f} logs/sec)")
    else:
        print("❌ No successful file results.")
    
    # Overall winner
    successful_results = [r for r in results if not r["error"]]
    if successful_results:
        best_overall = max(successful_results, key=lambda x: x["logs_per_sec"])
        print(f"\n🏆 FASTEST OVERALL: {best_overall['logger']} {best_overall['mode']} {best_overall['variant']} {best_overall['destination']} ({best_overall['logs_per_sec']:,.0f} logs/sec)")
    else:
        print("❌ No successful runs.")
    
    # Memory leak summary
    if memory_leaks:
        print(f"\n⚠️  MEMORY LEAK SUMMARY ({len(memory_leaks)} potential leaks):")
        for leak in memory_leaks:
            print(f"   {leak['test_name']}: {leak['memory_diff_mb']:.2f}MB")
    else:
        print(f"\n✅ No memory leaks detected!")
    
    # Performance summary by logger
    print(f"\n📊 PERFORMANCE SUMMARY BY LOGGER:")
    logger_summary = {}
    for result in successful_results:
        logger_key = f"{result['logger']} {result['mode']} {result['variant']}"
        if logger_key not in logger_summary:
            logger_summary[logger_key] = []
        logger_summary[logger_key].append(result['logs_per_sec'])
    
    for logger, performances in logger_summary.items():
        avg_performance = sum(performances) / len(performances)
        max_performance = max(performances)
        print(f"   {logger}: Avg {avg_performance:,.0f} logs/sec, Max {max_performance:,.0f} logs/sec")
    
    # Save results
    outdir = Path("benchmarks")
    outdir.mkdir(exist_ok=True)
    
    # CSV
    csv_path = outdir / "comprehensive_results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    # JSON
    json_path = outdir / "comprehensive_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Memory leak report
    if memory_leaks:
        leak_path = outdir / "memory_leaks.json"
        with open(leak_path, "w") as f:
            json.dump(memory_leaks, f, indent=2)
        print(f"\n📊 Results saved to: {csv_path}, {json_path}, and {leak_path}")
    else:
        print(f"\n📊 Results saved to: {csv_path} and {json_path}")
    
    # Print summary of failures
    if failures:
        print(f"\n❌ FAILURE SUMMARY ({len(failures)} failures):")
        for fail in failures:
            print(f"   {fail['test']}: {fail['error']}")
    else:
        print(f"\n✅ All {len(results)} tests completed successfully!")
    
    print(f"\n🎯 BENCHMARK COMPLETED:")
    print(f"   Total tests: {len(results)}")
    print(f"   Successful: {len(successful_results)}")
    print(f"   Failed: {len(failures)}")
    print(f"   Memory leaks: {len(memory_leaks)}")

if __name__ == "__main__":
    asyncio.run(main()) 