#!/usr/bin/env python3
"""
Logger Benchmark Skeleton - Hydra-Logger

A clean, pluggable benchmark framework that can test ANY logger implementation.
This is a skeleton that you can plug any logger into for performance testing.

ARCHITECTURE:
- LoggerBenchmark: Abstract base class for any logger
- BenchmarkRunner: Orchestrates benchmarks with any logger
- Pluggable design: Just implement the interface and plug it in

USAGE:
    # Create your logger implementation
    class MyLogger:
        def __init__(self, **kwargs):
            # Your logger setup
            pass
        
        def log(self, level, message, **kwargs):
            # Your logging implementation
            pass
        
        def log_batch(self, messages):
            # Optional: batch logging for performance
            pass
        
        def close(self):
            # Cleanup
            pass
    
    # Create benchmark runner
    runner = BenchmarkRunner(iterations=50000)
    
    # Test your logger
    result = runner.benchmark_logger(
        logger_class=MyLogger,
        logger_name="MyLogger",
        logger_kwargs={'use_direct_io': True}
    )
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.utils import (
    BenchmarkResult, BenchmarkConfig,
    measure_memory, calculate_performance_metrics, analyze_results,
    validate_file_output, validate_config, validate_benchmark_environment,
    RESULTS_DIR, LOGS_DIR, DEFAULT_ITERATIONS, DEFAULT_WARMUP_ITERATIONS
)

# Import the base class and all plugins
from benchmarks._plugins import (
    LoggerBenchmark,
    # Sync plugins
    HydraSyncFileLogger, HydraSyncConsoleLogger, HydraSyncMemoryLogger, HydraSyncNetworkLogger, 
    HydraSyncDatabaseLogger, HydraSyncCompositeLogger, 
    # Async plugins
    HydraAsyncFileLogger, HydraAsyncConsoleLogger, HydraAsyncMemoryLogger,
    HydraAsyncCompositeLogger, HydraAsyncPlainTextLogger, HydraAsyncJsonLinesLogger, HydraAsyncCsvLogger,
    # Factory and registry
    create_format_logger, FormatSpecificLogger,
    LOGGER_PLUGINS, get_plugin, list_plugins, get_plugin_info
)


class BenchmarkRunner:
    """
    Pluggable benchmark runner - works with ANY logger implementation.
    
    Just provide the logger class and configuration, and it will
    benchmark it automatically.
    """
    
    def __init__(self, iterations: int = 100000, warmup_iterations: int = 0, 
                 custom_logs_dir: Optional[str] = None):
        self.iterations = iterations
        self.warmup_iterations = warmup_iterations
        self.results: List[BenchmarkResult] = []
        
        # Create directories
        self.results_dir = Path(RESULTS_DIR)
        self.logs_dir = Path(custom_logs_dir) if custom_logs_dir else Path(LOGS_DIR)
        
        # Thread-safe directory creation
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate environment
        env_status = validate_benchmark_environment()
        if not env_status["valid"]:
            print("❌ Environment validation failed:")
            for error in env_status["errors"]:
                print(f"   {error}")
            raise RuntimeError("Benchmark environment validation failed")
        
        print(f"🚀 Benchmark Runner initialized")
        print(f"   Iterations: {iterations:,}")
        print(f"   Results: {self.results_dir.absolute()}")
        print(f"   Logs: {self.logs_dir.absolute()}")
        print()
    
    def _extract_logger_metadata(self, logger) -> tuple:
        """
        Extract metadata from logger instance with enhanced error handling.
        
        Returns:
            tuple: (format_type, destination_type, file_created, file_size_bytes, lines_written)
        """
        format_type = "unknown"
        destination_type = "unknown"
        file_created = False
        file_size_bytes = 0
        lines_written = 0
        
        try:
            # Check if logger has log_file attribute (file-based loggers)
            if hasattr(logger, 'log_file') and logger.log_file:
                log_file_path = logger.log_file
                if os.path.exists(log_file_path):
                    file_created = True
                    file_size_bytes = os.path.getsize(log_file_path)
                    
                    # Count lines in the file with better error handling
                    try:
                        with open(log_file_path, 'r', encoding='utf-8') as f:
                            lines_written = sum(1 for _ in f)
                    except (UnicodeDecodeError, PermissionError):
                        # For binary files or permission issues, estimate
                        lines_written = max(1, file_size_bytes // 100)
                    
                    # Determine format from file extension or logger attributes
                    if hasattr(logger, 'format_type'):
                        format_type = logger.format_type
                    elif log_file_path.endswith('.jsonl'):
                        format_type = "json-lines"
                    elif log_file_path.endswith('.json'):
                        format_type = "json"
                    elif log_file_path.endswith('.csv'):
                        format_type = "csv"
                    elif log_file_path.endswith('.log'):
                        format_type = "plain-text"
                    elif log_file_path.endswith('.bin'):
                        format_type = "binary"
                    
                    destination_type = "file"
            
            # Check if logger has underlying logger with config
            elif hasattr(logger, 'logger') and hasattr(logger.logger, '_config'):
                config = logger.logger._config
                if hasattr(config, 'layers'):
                    for layer_name, layer in config.layers.items():
                        if hasattr(layer, 'destinations'):
                            for dest in layer.destinations:
                                if hasattr(dest, 'type'):
                                    destination_type = dest.type
                                if hasattr(dest, 'format'):
                                    format_type = dest.format
                                break
                        break
            
            # Check logger type from class name or attributes
            elif hasattr(logger, 'logger'):
                logger_type = str(type(logger.logger)).lower()
                if 'console' in logger_type:
                    destination_type = "console"
                    format_type = "colored"
                elif 'null' in logger_type:
                    destination_type = "memory"
                    format_type = "null"
                elif 'http' in logger_type:
                    destination_type = "network"
                    format_type = "json-lines"
                elif 'sqlite' in logger_type:
                    destination_type = "database"
                    format_type = "json-lines"
            
        except Exception as e:
            # Log the error for debugging but don't fail the benchmark
            print(f"   ⚠️  Metadata extraction warning: {e}")
        
        return format_type, destination_type, file_created, file_size_bytes, lines_written
    
    def benchmark_logger(self, 
                        logger_class: Type[LoggerBenchmark],
                        logger_name: str,
                        logger_kwargs: Optional[Dict[str, Any]] = None,
                        test_name: Optional[str] = None) -> BenchmarkResult:
        """
        Benchmark ANY logger implementation.
        
        Args:
            logger_class: The logger class to benchmark
            logger_name: Name of the logger for identification
            logger_kwargs: Keyword arguments to pass to logger constructor
            test_name: Optional custom test name
        
        Returns:
            BenchmarkResult with performance metrics
        """
        if logger_kwargs is None:
            logger_kwargs = {}
        
        if test_name is None:
            test_name = f"{logger_name} Performance Test"
        
        print(f"🔄 Testing {logger_name}: {test_name}")
        
        # Measure memory
        memory_start = measure_memory()
        error_count = 0
        
        try:
            # Create logger instance
            logger = logger_class(**logger_kwargs)
            
            # Warmup
            for i in range(self.warmup_iterations):
                logger.log('INFO', f"Warmup message #{i}")
            
            # Performance test
            start_time = time.perf_counter()
            
            # Check if logger supports batch logging
            if hasattr(logger, 'log_batch') and callable(getattr(logger, 'log_batch')):
                # Use batch logging for maximum performance
                batch_size = 10000  # Increased from 1000 to 10000 for better performance
                
                # Pre-generate all messages to avoid string formatting during timing
                all_messages = [('INFO', f"Test message #{i}", {}) for i in range(self.iterations)]
                
                for i in range(0, self.iterations, batch_size):
                    batch = all_messages[i:i + batch_size]
                    logger.log_batch(batch)
            else:
                # Fallback to individual logging - pre-generate messages
                messages = [f"Test message #{i}" for i in range(self.iterations)]
                for message in messages:
                    logger.log('INFO', message)
            
            end_time = time.perf_counter()
            
            # Cleanup
            logger.close()
            
            # Calculate metrics
            total_time = end_time - start_time
            messages_per_second = self.iterations / total_time
            avg_time_per_message = total_time / self.iterations
            memory_end = measure_memory()
            
            # Extract metadata from logger
            format_type, destination_type, file_created, file_size_bytes, lines_written = self._extract_logger_metadata(logger)
            
            # Create result
            result = BenchmarkResult(
                test_name=test_name,
                logger_type=logger_name,
                iterations=self.iterations,
                total_time=total_time,
                messages_per_second=messages_per_second,
                avg_time_per_message=avg_time_per_message,
                memory_start_mb=memory_start,
                memory_end_mb=memory_end,
                memory_delta_mb=memory_end - memory_start,
                format_type=format_type,
                destination_type=destination_type,
                file_created=file_created,
                file_size_bytes=file_size_bytes,
                lines_written=lines_written,
                errors_occurred=error_count > 0,
                error_count=error_count
            )
            
            self.results.append(result)
            
            # Save results automatically
            self.save_results(f"{logger_name.lower()}_results.json")
            
            # Print results
            print(f"   ✅ Time: {total_time:.3f}s")
            print(f"   ✅ Speed: {messages_per_second:,.0f} msg/s")
            print(f"   ✅ Latency: {avg_time_per_message*1000:.3f} ms/msg")
            print(f"   ✅ Memory: {memory_start:.1f} → {memory_end:.1f} MB (Δ: {memory_end - memory_start:+.1f} MB)")
            
            if error_count > 0:
                print(f"   🚨 Errors: {error_count} errors occurred")
            else:
                print(f"   ✅ No errors detected")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Benchmark failed: {e}")
            error_count = 1
            
            # Return error result
            return BenchmarkResult(
                test_name=test_name,
                logger_type=logger_name,
                iterations=self.iterations,
                total_time=0.0,
                messages_per_second=0.0,
                avg_time_per_message=0.0,
                memory_start_mb=memory_start,
                memory_end_mb=measure_memory(),
                memory_delta_mb=0.0,
                format_type="unknown",
                destination_type="unknown",
                errors_occurred=True,
                error_count=error_count
            )
    
    async def benchmark_async_logger(self, 
                                   logger_class: Type[LoggerBenchmark],
                                   logger_name: str,
                                   logger_kwargs: Optional[Dict[str, Any]] = None,
                                   test_name: Optional[str] = None) -> BenchmarkResult:
        """
        Benchmark ANY async logger implementation.
        
        Args:
            logger_class: The async logger class to benchmark
            logger_name: Name of the logger for identification
            logger_kwargs: Keyword arguments to pass to logger constructor
            test_name: Optional custom test name
        
        Returns:
            BenchmarkResult with performance metrics
        """
        if logger_kwargs is None:
            logger_kwargs = {}
        
        if test_name is None:
            test_name = f"{logger_name} Async Performance Test"
        
        print(f"🔄 Testing {logger_name} (Async): {test_name}")
        
        # Measure memory
        memory_start = measure_memory()
        error_count = 0
        
        try:
            # Create logger instance
            logger = logger_class(**logger_kwargs)
            
            # Warmup
            for i in range(self.warmup_iterations):
                if hasattr(logger, 'log') and asyncio.iscoroutinefunction(logger.log):
                    await logger.log('INFO', f"Warmup message #{i}")
                else:
                    logger.log('INFO', f"Warmup message #{i}")
            
            # Performance test
            start_time = time.perf_counter()
            
            # Check if logger supports async batch logging
            if hasattr(logger, 'log_batch') and asyncio.iscoroutinefunction(getattr(logger, 'log_batch')):
                # Use async batch logging for maximum performance
                batch_size = 10000  # Increased from 1000 to 10000 for better performance
                
                # Pre-generate all messages to avoid string formatting during timing
                all_messages = [('INFO', f"Test message #{i}", {}) for i in range(self.iterations)]
                
                try:
                    for i in range(0, self.iterations, batch_size):
                        batch = all_messages[i:i + batch_size]
                        result = logger.log_batch(batch)
                        if result is not None:
                            await result
                except Exception as e:
                    print(f"DEBUG: Error in async batch logging: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            elif hasattr(logger, 'log_batch'):
                # Use batch logging (sync or async)
                batch_size = 10000  # Increased from 1000 to 10000 for better performance
                
                # Pre-generate all messages to avoid string formatting during timing
                all_messages = [('INFO', f"Test message #{i}", {}) for i in range(self.iterations)]
                
                for i in range(0, self.iterations, batch_size):
                    batch = all_messages[i:i + batch_size]
                    if asyncio.iscoroutinefunction(logger.log_batch):
                        await logger.log_batch(batch)
                    else:
                        logger.log_batch(batch)
            else:
                # Fallback to individual logging - pre-generate messages
                messages = [f"Test message #{i}" for i in range(self.iterations)]
                for message in messages:
                    if hasattr(logger, 'log') and asyncio.iscoroutinefunction(logger.log):
                        await logger.log('INFO', message)
                    else:
                        logger.log('INFO', message)
            
            end_time = time.perf_counter()
            
            # Cleanup
            if hasattr(logger, 'close') and asyncio.iscoroutinefunction(logger.close):
                await logger.close()
            elif hasattr(logger, 'aclose'):
                await logger.aclose()
            else:
                logger.close()
            
            # Calculate metrics
            total_time = end_time - start_time
            messages_per_second = self.iterations / total_time
            avg_time_per_message = total_time / self.iterations
            memory_end = measure_memory()
            
            # Extract metadata from logger
            format_type, destination_type, file_created, file_size_bytes, lines_written = self._extract_logger_metadata(logger)
            
            # Create result
            result = BenchmarkResult(
                test_name=test_name,
                logger_type=f"{logger_name}_async",
                iterations=self.iterations,
                total_time=total_time,
                messages_per_second=messages_per_second,
                avg_time_per_message=avg_time_per_message,
                memory_start_mb=memory_start,
                memory_end_mb=memory_end,
                memory_delta_mb=memory_end - memory_start,
                format_type=format_type,
                destination_type=destination_type,
                file_created=file_created,
                file_size_bytes=file_size_bytes,
                lines_written=lines_written,
                errors_occurred=error_count > 0,
                error_count=error_count
            )
            
            self.results.append(result)
            
            # Save results automatically
            self.save_results(f"{logger_name.lower()}_results.json")
            
            # Print results
            print(f"   ✅ Time: {total_time:.3f}s")
            print(f"   ✅ Speed: {messages_per_second:,.0f} msg/s")
            print(f"   ✅ Latency: {avg_time_per_message*1000:.3f} ms/msg")
            print(f"   ✅ Memory: {memory_start:.1f} → {memory_end:.1f} MB (Δ: {memory_end - memory_start:+.1f} MB)")
            
            if error_count > 0:
                print(f"   🚨 Errors: {error_count} errors occurred")
            else:
                print(f"   ✅ No errors detected")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Async benchmark failed: {e}")
            error_count = 1
            
            # Return error result
            return BenchmarkResult(
                test_name=test_name,
                logger_type=f"{logger_name}_async",
                iterations=self.iterations,
                total_time=0.0,
                messages_per_second=0.0,
                avg_time_per_message=0.0,
                memory_start_mb=memory_start,
                memory_end_mb=measure_memory(),
                memory_delta_mb=0.0,
                format_type="unknown",
                destination_type="unknown",
                errors_occurred=True,
                error_count=error_count
            )
    
    def benchmark_all_loggers(self) -> List[BenchmarkResult]:
        """
        Benchmark ALL available logger types comprehensively.
        
        This will test:
        - All 13 format-specific loggers (plain-text, json, csv, binary, etc.)
        - All sync loggers (File, Console, Memory, Network, Database, Composite)
        - All async loggers (File, Console, Memory, Composite)
        - All registered plugins from the plugin system
        
        Returns:
            List of all benchmark results
        """
        print("🚀 COMPREHENSIVE BENCHMARK SUITE")
        print("=" * 80)
        print("Testing ALL available loggers and formats...")
        print()
        
        # Clear previous results
        self.results.clear()
        
        # Test all format-specific loggers
        print("📊 TESTING ALL FORMAT-SPECIFIC LOGGERS:")
        print("-" * 60)
        
        format_loggers = [
            (lambda **kwargs: create_format_logger("plain-text", **kwargs), "PlainText", {}),
            (lambda **kwargs: create_format_logger("fast-plain", **kwargs), "FastPlain", {}),
            (lambda **kwargs: create_format_logger("detailed", **kwargs), "Detailed", {}),
            (lambda **kwargs: create_format_logger("json-lines", **kwargs), "JsonLines", {}),
            (lambda **kwargs: create_format_logger("json", **kwargs), "Json", {}),
            (lambda **kwargs: create_format_logger("csv", **kwargs), "Csv", {}),
            (lambda **kwargs: create_format_logger("syslog", **kwargs), "Syslog", {}),
            (lambda **kwargs: create_format_logger("gelf", **kwargs), "Gelf", {}),
            (lambda **kwargs: create_format_logger("logstash", **kwargs), "Logstash", {}),
            (lambda **kwargs: create_format_logger("binary", **kwargs), "Binary", {}),
            (lambda **kwargs: create_format_logger("binary-compact", **kwargs), "BinaryCompact", {}),
            (lambda **kwargs: create_format_logger("binary-extended", **kwargs), "BinaryExtended", {}),
        ]
        
        for logger_class, name, kwargs in format_loggers:
            try:
                result = self.benchmark_logger(logger_class, name, kwargs)
                print(f"   ✅ {name}: {result.messages_per_second:,.0f} msg/s")
            except Exception as e:
                print(f"   ❌ {name}: Failed - {e}")
        
        # Test console-only loggers
        print("\n📊 TESTING CONSOLE LOGGERS:")
        print("-" * 40)
        
        console_loggers = [
            (lambda **kwargs: create_format_logger("colored", **kwargs), "ColoredConsole", {'use_colors': True}),
            (HydraSyncConsoleLogger, "SyncConsole", {'use_colors': True}),
        ]
        
        for logger_class, name, kwargs in console_loggers:
            try:
                result = self.benchmark_logger(logger_class, name, kwargs)
                print(f"   ✅ {name}: {result.messages_per_second:,.0f} msg/s")
            except Exception as e:
                print(f"   ❌ {name}: Failed - {e}")
        
        # Test specialized sync loggers
        print("\n📊 TESTING SPECIALIZED SYNC LOGGERS:")
        print("-" * 50)
        
        sync_loggers = [
            (HydraSyncFileLogger, "SyncFile", {'name': 'SyncFile', 'log_file': os.path.abspath(os.path.join(os.getcwd(), 'benchmarks', '_logs', 'sync_file.jsonl'))}),
            (HydraSyncMemoryLogger, "SyncMemory", {'name': 'SyncMemory'}),
            (HydraSyncNetworkLogger, "SyncNetwork", {'name': 'SyncNetwork', 'endpoint': 'http://localhost:8080/logs'}),
            (HydraSyncDatabaseLogger, "SyncDatabase", {'name': 'SyncDatabase', 'db_file': os.path.abspath(os.path.join(os.getcwd(), 'benchmarks', '_logs', 'sync_database.jsonl'))}),
            (HydraSyncCompositeLogger, "SyncComposite", {'name': 'SyncComposite'}),
        ]
        
        for logger_class, name, kwargs in sync_loggers:
            try:
                result = self.benchmark_logger(logger_class, name, kwargs)
                print(f"   ✅ {name}: {result.messages_per_second:,.0f} msg/s")
            except Exception as e:
                print(f"   ❌ {name}: Failed - {e}")
        
        # Test async loggers (with proper event loop handling)
        print("\n📊 TESTING ASYNC LOGGERS:")
        print("-" * 40)
        
        async_loggers = [
            (HydraAsyncFileLogger, "AsyncFile", {'name': 'AsyncFile', 'log_file': os.path.abspath(os.path.join(os.getcwd(), 'benchmarks', '_logs', 'async_file.jsonl'))}),
            (HydraAsyncConsoleLogger, "AsyncConsole", {'name': 'AsyncConsole', 'use_colors': True}),
            (HydraAsyncMemoryLogger, "AsyncMemory", {'name': 'AsyncMemory'}),
            (HydraAsyncCompositeLogger, "AsyncComposite", {'name': 'AsyncComposite'}),
        ]
        
        for logger_class, name, kwargs in async_loggers:
            try:
                # Create new event loop for each async logger
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.benchmark_async_logger(logger_class, name, kwargs))
                    print(f"   ✅ {name}: {result.messages_per_second:,.0f} msg/s")
                finally:
                    loop.close()
            except Exception as e:
                print(f"   ❌ {name}: Failed - {e}")
        
        # Test all registered plugins
        print("\n📊 TESTING ALL REGISTERED PLUGINS:")
        print("-" * 50)
        
        for plugin_name, plugin_class in LOGGER_PLUGINS.items():
            try:
                # Skip format-specific loggers already tested above
                if plugin_name in ['plain-text', 'fast-plain', 'detailed', 'json-lines', 'json', 
                                 'csv', 'syslog', 'gelf', 'logstash', 'binary', 'binary-compact', 'binary-extended']:
                    continue
                
                # Test sync plugins
                if not plugin_name.startswith('async'):
                    result = self.benchmark_logger(plugin_class, f"Plugin_{plugin_name}", {})
                    print(f"   ✅ {plugin_name}: {result.messages_per_second:,.0f} msg/s")
                else:
                    # Test async plugins
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(self.benchmark_async_logger(plugin_class, f"Plugin_{plugin_name}", {}))
                        print(f"   ✅ {plugin_name}: {result.messages_per_second:,.0f} msg/s")
                    finally:
                        loop.close()
            except Exception as e:
                print(f"   ❌ {plugin_name}: Failed - {e}")
        
        # Print comprehensive summary
        self.print_summary()
        
        # Save all results
        self.save_results("comprehensive_benchmark_results.json")
        
        return self.results
    
    def benchmark_all_plugins(self) -> List[BenchmarkResult]:
        """
        Benchmark ALL registered plugins systematically.
        
        This tests every single plugin in the LOGGER_PLUGINS registry,
        providing comprehensive coverage of all available loggers.
        
        Returns:
            List of all benchmark results
        """
        print("🚀 COMPREHENSIVE PLUGIN BENCHMARK SUITE")
        print("=" * 80)
        print(f"Testing ALL {len(LOGGER_PLUGINS)} registered plugins...")
        print()
        
        # Clear previous results
        self.results.clear()
        
        # Test all plugins in the registry
        for plugin_name, plugin_class in LOGGER_PLUGINS.items():
            try:
                print(f"🔄 Testing plugin: {plugin_name}")
                
                # Determine if it's an async plugin
                is_async = plugin_name.startswith('async') or 'async' in plugin_name.lower()
                
                if is_async:
                    # Create new event loop for each async plugin
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            self.benchmark_async_logger(plugin_class, f"Plugin_{plugin_name}", {})
                        )
                        print(f"   ✅ {plugin_name}: {result.messages_per_second:,.0f} msg/s")
                    finally:
                        loop.close()
                else:
                    # Test sync plugin
                    result = self.benchmark_logger(plugin_class, f"Plugin_{plugin_name}", {})
                    print(f"   ✅ {plugin_name}: {result.messages_per_second:,.0f} msg/s")
                    
            except Exception as e:
                print(f"   ❌ {plugin_name}: Failed - {e}")
        
        # Print comprehensive summary
        self.print_summary()
        
        # Save all results
        self.save_results("all_plugins_benchmark_results.json")
        
        return self.results
    
    def benchmark_format_comparison(self) -> List[BenchmarkResult]:
        """
        Benchmark all formats side-by-side for comparison.
        
        This tests all 13 supported formats to compare their performance
        characteristics and identify the fastest/slowest formats.
        
        Returns:
            List of all benchmark results
        """
        print("🚀 FORMAT PERFORMANCE COMPARISON")
        print("=" * 80)
        print("Comparing all 13 supported formats...")
        print()
        
        # Clear previous results
        self.results.clear()
        
        # Test all format-specific loggers
        format_loggers = [
            (lambda **kwargs: create_format_logger("plain-text", **kwargs), "PlainText"),
            (lambda **kwargs: create_format_logger("fast-plain", **kwargs), "FastPlain"),
            (lambda **kwargs: create_format_logger("detailed", **kwargs), "Detailed"),
            (lambda **kwargs: create_format_logger("json-lines", **kwargs), "JsonLines"),
            (lambda **kwargs: create_format_logger("json", **kwargs), "Json"),
            (lambda **kwargs: create_format_logger("csv", **kwargs), "Csv"),
            (lambda **kwargs: create_format_logger("syslog", **kwargs), "Syslog"),
            (lambda **kwargs: create_format_logger("gelf", **kwargs), "Gelf"),
            (lambda **kwargs: create_format_logger("logstash", **kwargs), "Logstash"),
            (lambda **kwargs: create_format_logger("binary", **kwargs), "Binary"),
            (lambda **kwargs: create_format_logger("binary-compact", **kwargs), "BinaryCompact"),
            (lambda **kwargs: create_format_logger("binary-extended", **kwargs), "BinaryExtended"),
        ]
        
        for logger_class, name in format_loggers:
            try:
                result = self.benchmark_logger(logger_class, name, {})
                print(f"   ✅ {name}: {result.messages_per_second:,.0f} msg/s")
            except Exception as e:
                print(f"   ❌ {name}: Failed - {e}")
        
        # Print format comparison summary
        self.print_format_comparison()
        
        # Save all results
        self.save_results("format_comparison_results.json")
        
        return self.results
    
    def print_format_comparison(self):
        """Print a detailed format comparison analysis."""
        print("\n" + "="*80)
        print("📊 FORMAT PERFORMANCE COMPARISON ANALYSIS")
        print("="*80)
        
        if not self.results:
            print("❌ No benchmark results available!")
            return
        
        # Group results by format type
        format_results = {}
        for result in self.results:
            if not result.errors_occurred:
                format_type = result.format_type
                if format_type not in format_results:
                    format_results[format_type] = []
                format_results[format_type].append(result)
        
        # Sort formats by average performance
        format_performance = []
        for format_type, results in format_results.items():
            avg_speed = sum(r.messages_per_second for r in results) / len(results)
            format_performance.append((format_type, avg_speed, len(results)))
        
        format_performance.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 FORMAT PERFORMANCE RANKING:")
        print("-" * 60)
        print(f"{'Rank':<4} {'Format':<20} {'Avg Speed (msg/s)':<15} {'Tests':<8}")
        print("-" * 60)
        
        for i, (format_type, avg_speed, test_count) in enumerate(format_performance, 1):
            print(f"{i:<4} {format_type:<20} {avg_speed:>12,.0f} {test_count:>6}")
        
        # Performance categories by format
        high_perf_formats = [f for f, s, _ in format_performance if s >= 50000]
        medium_perf_formats = [f for f, s, _ in format_performance if 10000 <= s < 50000]
        low_perf_formats = [f for f, s, _ in format_performance if s < 10000]
        
        print(f"\n🎯 FORMAT PERFORMANCE CATEGORIES:")
        print(f"   High Performance (50K+ msg/s): {len(high_perf_formats)} formats")
        if high_perf_formats:
            print(f"      {', '.join(high_perf_formats)}")
        print(f"   Medium Performance (10K-50K msg/s): {len(medium_perf_formats)} formats")
        if medium_perf_formats:
            print(f"      {', '.join(medium_perf_formats)}")
        print(f"   Low Performance (<10K msg/s): {len(low_perf_formats)} formats")
        if low_perf_formats:
            print(f"      {', '.join(low_perf_formats)}")
        
        print("="*80)
    
    def benchmark_logger_types(self, logger_types: List[str] = None) -> List[BenchmarkResult]:
        """
        Benchmark specific logger types from the registry.
        
        Args:
            logger_types: List of logger type names to test (e.g., ['file', 'console', 'composite'])
                          If None, tests all available types
        
        Returns:
            List of benchmark results
        """
        if logger_types is None:
            logger_types = list(LOGGER_PLUGINS.keys())
        
        print(f"🚀 BENCHMARKING SPECIFIC LOGGER TYPES: {logger_types}")
        print("=" * 60)
        
        # Clear previous results
        self.results.clear()
        
        for logger_type in logger_types:
            if logger_type not in LOGGER_PLUGINS:
                print(f"   ❌ Unknown logger type: {logger_type}")
                continue
            
            logger_class = LOGGER_PLUGINS[logger_type]
            logger_name = f"Registry_{logger_type.title()}"
            
            try:
                if 'async' in logger_type.lower():
                    result = asyncio.run(self.benchmark_async_logger(logger_class, logger_name))
                else:
                    result = self.benchmark_logger(logger_class, logger_name)
                
                print(f"   ✅ {logger_name}: {result.messages_per_second:,.0f} msg/s")
            except Exception as e:
                print(f"   ❌ {logger_name}: Failed - {e}")
        
        self.print_summary()
        
        # Save all results
        self.save_results("logger_types_results.json")
        
        return self.results
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Save benchmark results to file."""
        filepath = self.results_dir / filename
        
        # Convert to serializable format
        serializable_results = []
        for result in self.results:
            result_dict = asdict(result)
            serializable_results.append(result_dict)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(serializable_results, f, indent=2)
            print(f"✅ Results saved to: {filepath}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    def print_summary(self):
        """Print a comprehensive summary of benchmark results with analysis."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE BENCHMARK ANALYSIS")
        print("="*80)
        
        if not self.results:
            print("❌ No benchmark results available!")
            return
        
        # Sort by performance
        sorted_results = sorted(self.results, key=lambda r: r.messages_per_second, reverse=True)
        successful_results = [r for r in self.results if not r.errors_occurred]
        
        print(f"\n🏆 PERFORMANCE RANKING ({len(sorted_results)} tests):")
        print("-" * 90)
        print(f"{'Rank':<4} {'Logger Name':<25} {'Speed (msg/s)':<12} {'Latency (ms)':<10} {'Memory (MB)':<10} {'Status':<8}")
        print("-" * 90)
        
        for i, result in enumerate(sorted_results, 1):
            status = "✅" if not result.errors_occurred else "❌"
            
            print(f"{i:<4} {result.logger_type:<25} "
                  f"{result.messages_per_second:>10,.0f} "
                  f"{result.avg_time_per_message*1000:>8.3f} "
                  f"{result.memory_delta_mb:>8.1f} "
                  f"{status}")
        
        # Performance analysis
        if successful_results:
            speeds = [r.messages_per_second for r in successful_results]
            latencies = [r.avg_time_per_message * 1000 for r in successful_results]
            memory_usage = [r.memory_delta_mb for r in successful_results]
            
            print(f"\n📈 PERFORMANCE ANALYSIS:")
            print(f"   Average Speed: {sum(speeds)/len(speeds):,.0f} msg/s")
            print(f"   Best Speed: {max(speeds):,.0f} msg/s")
            print(f"   Worst Speed: {min(speeds):,.0f} msg/s")
            print(f"   Average Latency: {sum(latencies)/len(latencies):.3f} ms")
            print(f"   Average Memory: {sum(memory_usage)/len(memory_usage):.1f} MB")
            
            # Performance categories
            high_perf = sum(1 for s in speeds if s >= 50000)
            medium_perf = sum(1 for s in speeds if 10000 <= s < 50000)
            low_perf = sum(1 for s in speeds if s < 10000)
            
            print(f"\n🎯 PERFORMANCE CATEGORIES:")
            print(f"   High Performance (50K+ msg/s): {high_perf} loggers")
            print(f"   Medium Performance (10K-50K msg/s): {medium_perf} loggers")
            print(f"   Low Performance (<10K msg/s): {low_perf} loggers")
            
            # Format analysis
            format_performance = {}
            for result in successful_results:
                fmt = result.format_type
                if fmt not in format_performance:
                    format_performance[fmt] = []
                format_performance[fmt].append(result.messages_per_second)
            
            if len(format_performance) > 1:
                print(f"\n📋 FORMAT PERFORMANCE ANALYSIS:")
                for fmt, speeds in sorted(format_performance.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True):
                    avg_speed = sum(speeds) / len(speeds)
                    print(f"   {fmt:<15}: {avg_speed:>8,.0f} msg/s (avg of {len(speeds)} tests)")
        
        # Summary statistics
        total_tests = len(self.results)
        successful_tests = len(successful_results)
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"   Failed: {total_tests - successful_tests}")
        
        print("="*80)


# Convenience functions for quick testing
def quick_benchmark(logger_class: Type[LoggerBenchmark], 
                   logger_name: str,
                   iterations: int = 100000,
                   **logger_kwargs) -> BenchmarkResult:
    """Quick benchmark for any logger."""
    runner = BenchmarkRunner(iterations=iterations)
    return runner.benchmark_logger(logger_class, logger_name, logger_kwargs)

async def quick_async_benchmark(logger_class: Type[LoggerBenchmark], 
                               logger_name: str,
                               iterations: int = 100000,
                               **logger_kwargs) -> BenchmarkResult:
    """Quick async benchmark for any logger."""
    runner = BenchmarkRunner(iterations=iterations)
    return await runner.benchmark_async_logger(logger_class, logger_name, logger_kwargs)

def benchmark_all_loggers(iterations: int = 100000) -> List[BenchmarkResult]:
    """Quick benchmark for all available loggers."""
    runner = BenchmarkRunner(iterations=iterations)
    return runner.benchmark_all_loggers()

def benchmark_logger_types(logger_types: List[str], iterations: int = 100000) -> List[BenchmarkResult]:
    """Quick benchmark for specific logger types."""
    runner = BenchmarkRunner(iterations=iterations)
    return runner.benchmark_logger_types(logger_types)


# ============================================================================
# MAIN EXECUTION - Run benchmarks when script is executed directly
# ============================================================================

if __name__ == "__main__":
    print("🚀 HYDRA-LOGGER COMPREHENSIVE BENCHMARK SUITE")
    print("=" * 80)
    print("Choose your benchmark type:")
    print("1. All Loggers (comprehensive test of all logger types)")
    print("2. All Plugins (test every registered plugin)")
    print("3. Format Comparison (compare all 13 formats)")
    print("4. Quick Test (basic loggers only)")
    print()
    
    # For now, run the most comprehensive test
    try:
        print("🔄 Running COMPREHENSIVE BENCHMARK...")
        print("This will test ALL available loggers and formats!")
        print()
        
        # Create benchmark runner
        runner = BenchmarkRunner(iterations=5000)  # 5K iterations for comprehensive test
        
        # Run comprehensive benchmark
        results = runner.benchmark_all_loggers()
        
        print(f"\n✅ COMPREHENSIVE BENCHMARK COMPLETED!")
        print(f"   Total tests: {len(results)}")
        print(f"   Results saved to: benchmarks/_results/")
        print(f"   Logs saved to: benchmarks/_logs/")
        print()
        print("💡 To run other benchmark types:")
        print("   - All Plugins: runner.benchmark_all_plugins()")
        print("   - Format Comparison: runner.benchmark_format_comparison()")
        print("   - Quick Test: runner.benchmark_logger_types(['sync_memory', 'sync_console'])")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
