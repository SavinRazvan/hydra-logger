#!/usr/bin/env python3
"""
HydraLogger Async Performance Benchmark

This is the canonical async benchmark file for HydraLogger.

- Runs all major async logging performance tests (including corrected message counting for concurrency)
- Covers single-threaded, concurrent, and fast-path async logging
- Reports throughput, latency, memory usage, and leak detection
- Results are printed to the console and saved to benchmarks/results/

How to run:
    python benchmarks/hydra_async_bench.py

Results:
    - Console output: summary and per-test results
    - CSV/JSON: benchmarks/results/async_results.csv, benchmarks/results/async_results.json
    - Log: logs/async_benchmark.log

Test Categories:
    1. Standard async console logging
    2. Corrected concurrent async logging (proper message counting)
    3. Fast async logger (minimal overhead)

All logic is self-contained in this file. No references to deleted/renamed files remain.
"""

import asyncio
import time
import psutil
import os
import sys
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hydra_logger.async_hydra import AsyncHydraLogger

def get_realistic_message(i):
    """Generate realistic log messages for testing."""
    messages = [
        f"User john.doe{i}@example.com logged in from IP 192.168.1.{i%255}",
        f"Order #{10000+i} processed for user john.doe{i}@example.com (amount: ${100+i}.00)",
        f"DB connection pool at {70+i%30}% utilization (query: SELECT * FROM users WHERE id={i})",
        f"Failed login attempt for user admin{i} from IP 10.0.0.{i%255}",
        f"API request GET /api/users/{i} completed in {150+i%100}ms",
        f"Cache miss for key 'user_profile_{i}' - fetching from database",
        f"Payment processed for order #{20000+i} via Stripe (amount: ${50+i}.99)",
        f"Email sent to user{i}@example.com (template: welcome_email)",
        f"Background job 'process_images_{i}' started at {time.time()}",
        f"Security alert: Multiple failed login attempts for user admin{i}"
    ]
    return messages[i % len(messages)]

def get_realistic_layer(i):
    """Generate realistic layer names for testing."""
    layers = [
        "FRONTEND", "BACKEND", "DATABASE", "SECURITY", "API", 
        "CACHE", "PAYMENT", "EMAIL", "BACKGROUND", "ALERT",
        "AUTH", "USER", "ORDER", "INVENTORY", "SHIPPING"
    ]
    return layers[i % len(layers)]


class AsyncBenchmark:
    """Async benchmark suite for HydraLogger."""
    
    def __init__(self):
        self.results = {}
        self.test_config = {
            'iterations': 10000,
            'warmup_iterations': 100,
            'concurrent_tasks': 10
        }
        self.logs_folder = None
        self.results_folder = None
    
    def create_benchmark_folders(self):
        """Create folders for logs and results - one per benchmark run."""
        benchmark_name = "hydra_async"  # Based on file name
        
        # Create logs folder in benchmarks directory
        self.logs_folder = f"benchmarks/logs/{benchmark_name}"
        os.makedirs(self.logs_folder, exist_ok=True)
        
        # Create results folder in benchmarks directory
        self.results_folder = f"benchmarks/results/{benchmark_name}"
        os.makedirs(self.results_folder, exist_ok=True)
        
        return self.logs_folder, self.results_folder

    def take_memory_snapshot(self, test_name: str) -> Dict[str, Any]:
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                'test_name': test_name,
                'memory_before_mb': memory_info.rss / (1024 * 1024),
                'memory_after_mb': memory_info.rss / (1024 * 1024),
                'memory_diff_mb': 0.0,
                'potential_leak': False,
                'leak_threshold_mb': 10.0
            }
        except Exception as e:
            return {
                'test_name': test_name,
                'error': str(e),
                'potential_leak': False
            }

    async def benchmark_console(self, test_name: str, description: str) -> Dict[str, Any]:
        print(f"\n🔄 Running: {test_name}")
        print(f"📝 Description: {description}")
        
        # Create timestamped folders if not already created
        if not self.logs_folder:
            self.create_benchmark_folders()
        
        # Generate log filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{self.logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        memory_before = self.take_memory_snapshot(test_name)
        logger = AsyncHydraLogger({'handlers': [{'type': 'console', 'use_colors': True}]})
        await logger.initialize()
        
        for i in range(self.test_config['warmup_iterations']):
            layer = get_realistic_layer(i)
            await logger.info(get_realistic_message(i), layer)
        start_time = time.time()
        for i in range(self.test_config['iterations']):
            layer = get_realistic_layer(i)
            await logger.info(get_realistic_message(i), layer)
        end_time = time.time()
        duration = end_time - start_time
        memory_after = self.take_memory_snapshot(test_name)
        memory_after['memory_before_mb'] = memory_before['memory_before_mb']
        memory_after['memory_diff_mb'] = memory_after['memory_after_mb'] - memory_before['memory_before_mb']
        memory_after['potential_leak'] = abs(memory_after['memory_diff_mb']) > memory_after['leak_threshold_mb']
        messages_per_sec = self.test_config['iterations'] / duration
        latency_ms = (duration / self.test_config['iterations']) * 1000
        result = {
            'test_name': test_name,
            'description': description,
            'duration': duration,
            'messages_per_sec': messages_per_sec,
            'latency_ms': latency_ms,
            'success': True,
            'memory_info': memory_after,
            'total_messages': self.test_config['iterations'],
            'log_file': log_filename
        }
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Description: {description}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.6f}s\n")
                f.write(f"Success: {result['success']}\n")
                f.write(f"Memory Before: {memory_before['memory_before_mb']:.2f}MB\n")
                f.write(f"Memory After: {memory_after['memory_after_mb']:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after['memory_diff_mb']:.2f}MB\n")
                f.write(f"Memory Leak: {memory_after['potential_leak']}\n")
                f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Total Messages: {self.test_config['iterations']}\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        print(f"  ⚡ Performance: {messages_per_sec:.2f} messages/sec")
        print(f"  ⏱️  Duration: {duration:.6f}s")
        print(f"  📊 Latency: {latency_ms:.6f}ms")
        print(f"  📈 Total Messages: {self.test_config['iterations']}")
        print(f"  💾 Memory: {memory_after['memory_diff_mb']:.2f}MB diff")
        print(f"  ✅ Success: {result['success']}")
        print(f"  🚨 Memory Leak: {'Yes' if memory_after['potential_leak'] else 'No'}")
        print(f"  📄 Log File: {log_filename}")
        
        await logger.aclose()
        return result

    async def benchmark_concurrent(self, test_name: str, description: str) -> Dict[str, Any]:
        print(f"\n🔄 Running: {test_name}")
        print(f"📝 Description: {description}")
        
        # Create timestamped folders if not already created
        if not self.logs_folder:
            self.create_benchmark_folders()
        
        # Generate log filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{self.logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        memory_before = self.take_memory_snapshot(test_name)
        logger = AsyncHydraLogger({'handlers': [{'type': 'console', 'use_colors': True}]})
        await logger.initialize()
        
        total_messages = self.test_config['iterations'] * self.test_config['concurrent_tasks']
        messages_per_task = self.test_config['iterations']
        async def log_task(task_id: int):
            for i in range(messages_per_task):
                layer = get_realistic_layer(i)
                await logger.info(f"Task {task_id} - {get_realistic_message(i)}", layer)
        warmup_tasks = [log_task(i) for i in range(min(5, self.test_config['concurrent_tasks']))]
        await asyncio.gather(*warmup_tasks)
        start_time = time.time()
        tasks = [log_task(i) for i in range(self.test_config['concurrent_tasks'])]
        await asyncio.gather(*tasks)
        end_time = time.time()
        duration = end_time - start_time
        memory_after = self.take_memory_snapshot(test_name)
        memory_after['memory_before_mb'] = memory_before['memory_before_mb']
        memory_after['memory_diff_mb'] = memory_after['memory_after_mb'] - memory_before['memory_before_mb']
        memory_after['potential_leak'] = abs(memory_after['memory_diff_mb']) > memory_after['leak_threshold_mb']
        messages_per_sec = total_messages / duration
        latency_ms = (duration / total_messages) * 1000
        result = {
            'test_name': test_name,
            'description': description,
            'duration': duration,
            'messages_per_sec': messages_per_sec,
            'latency_ms': latency_ms,
            'success': True,
            'memory_info': memory_after,
            'total_messages': total_messages,
            'concurrent_tasks': self.test_config['concurrent_tasks'],
            'messages_per_task': messages_per_task,
            'log_file': log_filename
        }
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Description: {description}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.6f}s\n")
                f.write(f"Success: {result['success']}\n")
                f.write(f"Memory Before: {memory_before['memory_before_mb']:.2f}MB\n")
                f.write(f"Memory After: {memory_after['memory_after_mb']:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after['memory_diff_mb']:.2f}MB\n")
                f.write(f"Memory Leak: {memory_after['potential_leak']}\n")
                f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Total Messages: {total_messages}\n")
                f.write(f"Concurrent Tasks: {self.test_config['concurrent_tasks']}\n")
                f.write(f"Messages per Task: {messages_per_task}\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        print(f"  ⚡ Performance: {messages_per_sec:.2f} messages/sec")
        print(f"  ⏱️  Duration: {duration:.6f}s")
        print(f"  📊 Latency: {latency_ms:.6f}ms")
        print(f"  📈 Total Messages: {total_messages}")
        print(f"  🔄 Concurrent Tasks: {self.test_config['concurrent_tasks']}")
        print(f"  📝 Messages per Task: {messages_per_task}")
        print(f"  💾 Memory: {memory_after['memory_diff_mb']:.2f}MB diff")
        print(f"  ✅ Success: {result['success']}")
        print(f"  🚨 Memory Leak: {'Yes' if memory_after['potential_leak'] else 'No'}")
        print(f"  📄 Log File: {log_filename}")
        
        await logger.aclose()
        return result

    async def benchmark_security_features(self, test_name: str, description: str) -> Dict[str, Any]:
        print(f"\n🔄 Running: {test_name}")
        print(f"📝 Description: {description}")
        
        # Create timestamped folders if not already created
        if not self.logs_folder:
            self.create_benchmark_folders()
        
        # Generate log filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{self.logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        memory_before = self.take_memory_snapshot(test_name)
        logger = AsyncHydraLogger({'handlers': [{'type': 'console', 'use_colors': False}], 'enable_security': True})
        await logger.initialize()
        
        # Warm up with sensitive messages
        for i in range(self.test_config['warmup_iterations']):
            layer = get_realistic_layer(i)
            await logger.info(f"User login attempt {i} with email=user{i}@example.com and password=secret{i}123", layer)
        
        start_time = time.time()
        for i in range(self.test_config['iterations']):
            layer = get_realistic_layer(i)
            await logger.info(f"User login attempt {i} with email=user{i}@example.com and password=secret{i}123", layer)
        end_time = time.time()
        duration = end_time - start_time
        memory_after = self.take_memory_snapshot(test_name)
        memory_after['memory_before_mb'] = memory_before['memory_before_mb']
        memory_after['memory_diff_mb'] = memory_after['memory_after_mb'] - memory_before['memory_before_mb']
        memory_after['potential_leak'] = abs(memory_after['memory_diff_mb']) > memory_after['leak_threshold_mb']
        messages_per_sec = self.test_config['iterations'] / duration
        latency_ms = (duration / self.test_config['iterations']) * 1000
        result = {
            'test_name': test_name,
            'description': description,
            'duration': duration,
            'messages_per_sec': messages_per_sec,
            'latency_ms': latency_ms,
            'success': True,
            'memory_info': memory_after,
            'total_messages': self.test_config['iterations'],
            'log_file': log_filename
        }
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Description: {description}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.6f}s\n")
                f.write(f"Success: {result['success']}\n")
                f.write(f"Memory Before: {memory_before['memory_before_mb']:.2f}MB\n")
                f.write(f"Memory After: {memory_after['memory_after_mb']:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after['memory_diff_mb']:.2f}MB\n")
                f.write(f"Memory Leak: {memory_after['potential_leak']}\n")
                f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Total Messages: {self.test_config['iterations']}\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        print(f"  ⚡ Performance: {messages_per_sec:.2f} messages/sec")
        print(f"  ⏱️  Duration: {duration:.6f}s")
        print(f"  📊 Latency: {latency_ms:.6f}ms")
        print(f"  📈 Total Messages: {self.test_config['iterations']}")
        print(f"  💾 Memory: {memory_after['memory_diff_mb']:.2f}MB diff")
        print(f"  ✅ Success: {result['success']}")
        print(f"  🚨 Memory Leak: {'Yes' if memory_after['potential_leak'] else 'No'}")
        print(f"  📄 Log File: {log_filename}")
        
        await logger.aclose()
        return result

    async def benchmark_multi_layer(self, test_name: str, description: str) -> Dict[str, Any]:
        print(f"\n🔄 Running: {test_name}")
        print(f"📝 Description: {description}")
        
        # Create timestamped folders if not already created
        if not self.logs_folder:
            self.create_benchmark_folders()
        
        # Generate log filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{self.logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        memory_before = self.take_memory_snapshot(test_name)
        config = {
            'layers': {
                'FRONTEND': {'level': 'INFO', 'destinations': [{'type': 'console', 'use_colors': False}]},
                'BACKEND': {'level': 'DEBUG', 'destinations': [{'type': 'console', 'use_colors': False}]},
                'DATABASE': {'level': 'WARNING', 'destinations': [{'type': 'console', 'use_colors': False}]},
                'SECURITY': {'level': 'ERROR', 'destinations': [{'type': 'console', 'use_colors': False}]}
            }
        }
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Warm up with multi-layer messages
        for i in range(self.test_config['warmup_iterations']):
            await logger.info(f"[FRONTEND] Test message {i} for FRONTEND layer", "FRONTEND")
            await logger.debug(f"[BACKEND] Test message {i} for BACKEND layer", "BACKEND")
            await logger.warning(f"[DATABASE] Test message {i} for DATABASE layer", "DATABASE")
            await logger.error(f"[SECURITY] Test message {i} for SECURITY layer", "SECURITY")
        
        start_time = time.time()
        for i in range(self.test_config['iterations']):
            await logger.info(f"[FRONTEND] Test message {i} for FRONTEND layer", "FRONTEND")
            await logger.debug(f"[BACKEND] Test message {i} for BACKEND layer", "BACKEND")
            await logger.warning(f"[DATABASE] Test message {i} for DATABASE layer", "DATABASE")
            await logger.error(f"[SECURITY] Test message {i} for SECURITY layer", "SECURITY")
        end_time = time.time()
        duration = end_time - start_time
        memory_after = self.take_memory_snapshot(test_name)
        memory_after['memory_before_mb'] = memory_before['memory_before_mb']
        memory_after['memory_diff_mb'] = memory_after['memory_after_mb'] - memory_before['memory_before_mb']
        memory_after['potential_leak'] = abs(memory_after['memory_diff_mb']) > memory_after['leak_threshold_mb']
        total_messages = self.test_config['iterations'] * 4  # 4 layers
        messages_per_sec = total_messages / duration
        latency_ms = (duration / total_messages) * 1000
        result = {
            'test_name': test_name,
            'description': description,
            'duration': duration,
            'messages_per_sec': messages_per_sec,
            'latency_ms': latency_ms,
            'success': True,
            'memory_info': memory_after,
            'total_messages': total_messages,
            'layers': 4,
            'log_file': log_filename
        }
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Description: {description}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.6f}s\n")
                f.write(f"Success: {result['success']}\n")
                f.write(f"Memory Before: {memory_before['memory_before_mb']:.2f}MB\n")
                f.write(f"Memory After: {memory_after['memory_after_mb']:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after['memory_diff_mb']:.2f}MB\n")
                f.write(f"Memory Leak: {memory_after['potential_leak']}\n")
                f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Total Messages: {total_messages}\n")
                f.write(f"Layers: 4\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        print(f"  ⚡ Performance: {messages_per_sec:.2f} messages/sec")
        print(f"  ⏱️  Duration: {duration:.6f}s")
        print(f"  📊 Latency: {latency_ms:.6f}ms")
        print(f"  📈 Total Messages: {total_messages}")
        print(f"  🔄 Layers: 4")
        print(f"  💾 Memory: {memory_after['memory_diff_mb']:.2f}MB diff")
        print(f"  ✅ Success: {result['success']}")
        print(f"  🚨 Memory Leak: {'Yes' if memory_after['potential_leak'] else 'No'}")
        print(f"  📄 Log File: {log_filename}")
        
        await logger.aclose()
        return result

    async def benchmark_large_messages(self, test_name: str, description: str) -> Dict[str, Any]:
        print(f"\n🔄 Running: {test_name}")
        print(f"📝 Description: {description}")
        
        # Create timestamped folders if not already created
        if not self.logs_folder:
            self.create_benchmark_folders()
        
        # Generate log filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{self.logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        memory_before = self.take_memory_snapshot(test_name)
        logger = AsyncHydraLogger({'handlers': [{'type': 'console', 'use_colors': False}]})
        await logger.initialize()
        
        # Warm up with large messages
        for i in range(self.test_config['warmup_iterations']):
            large_msg = f"Test log message {i} with very long content that includes additional details about the system state, user actions, and various parameters that might be logged in a real application scenario. This message is designed to test how the logger handles larger payloads and whether it affects performance significantly. The message includes: timestamp={i}, user_id=user_{i}, action=test_action_{i}, status=active, priority=normal, category=benchmark, source=test_suite, version=1.0.0, environment=development, and various other metadata fields that might be present in production logging scenarios."
            await logger.info(large_msg, "WARMUP")
        
        start_time = time.time()
        for i in range(self.test_config['iterations']):
            large_msg = f"Test log message {i} with very long content that includes additional details about the system state, user actions, and various parameters that might be logged in a real application scenario. This message is designed to test how the logger handles larger payloads and whether it affects performance significantly. The message includes: timestamp={i}, user_id=user_{i}, action=test_action_{i}, status=active, priority=normal, category=benchmark, source=test_suite, version=1.0.0, environment=development, and various other metadata fields that might be present in production logging scenarios."
            await logger.info(large_msg, "BENCHMARK")
        end_time = time.time()
        duration = end_time - start_time
        memory_after = self.take_memory_snapshot(test_name)
        memory_after['memory_before_mb'] = memory_before['memory_before_mb']
        memory_after['memory_diff_mb'] = memory_after['memory_after_mb'] - memory_before['memory_before_mb']
        memory_after['potential_leak'] = abs(memory_after['memory_diff_mb']) > memory_after['leak_threshold_mb']
        messages_per_sec = self.test_config['iterations'] / duration
        latency_ms = (duration / self.test_config['iterations']) * 1000
        result = {
            'test_name': test_name,
            'description': description,
            'duration': duration,
            'messages_per_sec': messages_per_sec,
            'latency_ms': latency_ms,
            'success': True,
            'memory_info': memory_after,
            'total_messages': self.test_config['iterations'],
            'message_type': 'large',
            'log_file': log_filename
        }
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Description: {description}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.6f}s\n")
                f.write(f"Success: {result['success']}\n")
                f.write(f"Memory Before: {memory_before['memory_before_mb']:.2f}MB\n")
                f.write(f"Memory After: {memory_after['memory_after_mb']:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after['memory_diff_mb']:.2f}MB\n")
                f.write(f"Memory Leak: {memory_after['potential_leak']}\n")
                f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Total Messages: {self.test_config['iterations']}\n")
                f.write(f"Message Type: Large\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        print(f"  ⚡ Performance: {messages_per_sec:.2f} messages/sec")
        print(f"  ⏱️  Duration: {duration:.6f}s")
        print(f"  📊 Latency: {latency_ms:.6f}ms")
        print(f"  📈 Total Messages: {self.test_config['iterations']}")
        print(f"  📝 Message Type: Large")
        print(f"  💾 Memory: {memory_after['memory_diff_mb']:.2f}MB diff")
        print(f"  ✅ Success: {result['success']}")
        print(f"  🚨 Memory Leak: {'Yes' if memory_after['potential_leak'] else 'No'}")
        print(f"  📄 Log File: {log_filename}")
        
        await logger.aclose()
        return result

    async def benchmark_fast_async(self, test_name: str, description: str) -> Dict[str, Any]:
        print(f"\n🔄 Running: {test_name}")
        print(f"📝 Description: {description}")
        
        # Create timestamped folders if not already created
        if not self.logs_folder:
            self.create_benchmark_folders()
        
        # Generate log filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")
        log_filename = f"{self.logs_folder}/{safe_test_name}_{timestamp}.txt"
        
        memory_before = self.take_memory_snapshot(test_name)
        logger = AsyncHydraLogger({'handlers': [{'type': 'console', 'use_colors': True}]})
        await logger.initialize()
        
        for i in range(self.test_config['warmup_iterations']):
            await logger.info(f"Warmup message {i}", "WARMUP")
        start_time = time.time()
        for i in range(self.test_config['iterations']):
            await logger.info(f"Test log message {i} with consistent content for fair comparison", "BENCHMARK")
        end_time = time.time()
        duration = end_time - start_time
        memory_after = self.take_memory_snapshot(test_name)
        memory_after['memory_before_mb'] = memory_before['memory_before_mb']
        memory_after['memory_diff_mb'] = memory_after['memory_after_mb'] - memory_before['memory_before_mb']
        memory_after['potential_leak'] = abs(memory_after['memory_diff_mb']) > memory_after['leak_threshold_mb']
        messages_per_sec = self.test_config['iterations'] / duration
        latency_ms = (duration / self.test_config['iterations']) * 1000
        result = {
            'test_name': test_name,
            'description': description,
            'duration': duration,
            'messages_per_sec': messages_per_sec,
            'latency_ms': latency_ms,
            'success': True,
            'memory_info': memory_after,
            'total_messages': self.test_config['iterations'],
            'log_file': log_filename
        }
        
        # Save test results to log file
        try:
            with open(log_filename, "w") as f:
                f.write(f"Test: {test_name}\n")
                f.write(f"Description: {description}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Duration: {duration:.6f}s\n")
                f.write(f"Success: {result['success']}\n")
                f.write(f"Memory Before: {memory_before['memory_before_mb']:.2f}MB\n")
                f.write(f"Memory After: {memory_after['memory_after_mb']:.2f}MB\n")
                f.write(f"Memory Diff: {memory_after['memory_diff_mb']:.2f}MB\n")
                f.write(f"Memory Leak: {memory_after['potential_leak']}\n")
                f.write(f"Messages/sec: {messages_per_sec:.2f}\n")
                f.write(f"Latency: {latency_ms:.6f}ms\n")
                f.write(f"Total Messages: {self.test_config['iterations']}\n")
                f.write(f"Log File: {log_filename}\n")
        except Exception as log_error:
            print(f"Warning: Could not write log file {log_filename}: {log_error}")
        
        print(f"  ⚡ Performance: {messages_per_sec:.2f} messages/sec")
        print(f"  ⏱️  Duration: {duration:.6f}s")
        print(f"  📊 Latency: {latency_ms:.6f}ms")
        print(f"  📈 Total Messages: {self.test_config['iterations']}")
        print(f"  💾 Memory: {memory_after['memory_diff_mb']:.2f}MB diff")
        print(f"  ✅ Success: {result['success']}")
        print(f"  🚨 Memory Leak: {'Yes' if memory_after['potential_leak'] else 'No'}")
        print(f"  📄 Log File: {log_filename}")
        
        await logger.aclose()
        return result

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        print("🚀 Starting HydraLogger Async Benchmark")
        print("=" * 60)
        print("🔧 All async benchmarks use corrected message counting and modern async patterns")
        print("=" * 60)
        os.makedirs('benchmarks/logs', exist_ok=True)
        benchmarks = [
            (self.benchmark_console, "AsyncHydraLogger Console", "Standard async console logging - single-threaded"),
            (self.benchmark_concurrent, "AsyncHydraLogger Concurrent", "Concurrent async logging - proper message counting"),
            (self.benchmark_fast_async, "AsyncHydraLogger Console (Optimized)", "Optimized async console logging - minimal overhead"),
            (self.benchmark_security_features, "AsyncHydraLogger Security Features", "Async security features - PII detection and sanitization"),
            (self.benchmark_multi_layer, "AsyncHydraLogger Multi-Layer", "Async multi-layer logging - multiple functional layers"),
            (self.benchmark_large_messages, "AsyncHydraLogger Large Messages", "Async large message handling - big payload performance"),
        ]
        for benchmark_func, test_name, description in benchmarks:
            try:
                result = await benchmark_func(test_name, description)
                self.results[test_name] = result
            except Exception as e:
                print(f"❌ Benchmark failed: {test_name} - {e}")
                self.results[test_name] = {
                    'test_name': test_name,
                    'description': description,
                    'success': False,
                    'error': str(e)
                }
        return self.results

    def print_summary(self):
        print("\n" + "=" * 60)
        print("📊 ASYNC BENCHMARK SUMMARY")
        print("=" * 60)
        successful_tests = [r for r in self.results.values() if r.get('success', False)]
        failed_tests = [r for r in self.results.values() if not r.get('success', False)]
        if successful_tests:
            performances = [r['messages_per_sec'] for r in successful_tests]
            durations = [r['duration'] for r in successful_tests]
            total_messages = [r.get('total_messages', 0) for r in successful_tests]
            print(f"✅ Successful Tests: {len(successful_tests)}")
            print(f"❌ Failed Tests: {len(failed_tests)}")
            print(f"🏆 Best Performance: {max(performances):.2f} messages/sec")
            print(f"📉 Worst Performance: {min(performances):.2f} messages/sec")
            print(f"📊 Average Performance: {sum(performances)/len(performances):.2f} messages/sec")
            print(f"⚡ Best Duration: {min(durations):.6f}s")
            print(f"🐌 Worst Duration: {max(durations):.6f}s")
            print(f"📈 Average Duration: {sum(durations)/len(durations):.6f}s")
            print(f"📝 Total Messages Logged: {sum(total_messages):,}")
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test.get('error', 'Unknown error')}")
        print("\n🎯 Performance Comparison:")
        print("  - Sync: ~97,000 messages/sec")
        print("  - Async: see above")
        print("\n🔧 All benchmarks use the latest async implementation and message counting fixes.")
        
        # Save results
        try:
            import json
            import csv
            
            # Create timestamped folders if not already created
            if not self.results_folder:
                self.create_benchmark_folders()
            
            # Save JSON results
            with open(f"{self.results_folder}/results.json", "w") as f:
                json.dump({
                    "results": self.results,
                    "timestamp": time.time(),
                    "test_config": self.test_config
                }, f, indent=2)
            
            # Save CSV results
            with open(f"{self.results_folder}/results.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Test Name", "Description", "Duration (s)", "Messages/sec", 
                    "Latency (ms)", "Success", "Total Messages", "Memory Leak"
                ])
                
                for test_name, result in self.results.items():
                    duration = result.get('duration', 0)
                    messages_per_sec = result.get('messages_per_sec', 0)
                    latency_ms = result.get('latency_ms', 0)
                    success = result.get('success', False)
                    total_messages = result.get('total_messages', 0)
                    memory_leak = result.get('memory_info', {}).get('potential_leak', False)
                    
                    writer.writerow([
                        test_name, result.get('description', ''), duration, messages_per_sec,
                        latency_ms, success, total_messages, memory_leak
                    ])
            
            print(f"\n💾 Results saved to:")
            print(f"  - {self.results_folder}/results.json")
            print(f"  - {self.results_folder}/results.csv")
            print(f"  - Individual test logs in: {self.logs_folder}/")
            
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

async def main():
    benchmark = AsyncBenchmark()
    results = await benchmark.run_all_benchmarks()
    benchmark.print_summary()
    return results

if __name__ == "__main__":
    asyncio.run(main())