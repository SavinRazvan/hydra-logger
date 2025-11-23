#!/usr/bin/env python3
"""
Hydra-Logger Performance Benchmark Suite

This benchmark suite tests the performance characteristics of Hydra-Logger
implementations. It measures individual logger performance, batch logging
efficiency, memory usage patterns, configuration impact on performance,
and concurrent logging capabilities.

Usage:
    python3 performance_benchmark.py

The benchmark runs various performance tests and provides results showing
messages per second, memory usage, and efficiency metrics.
"""

import asyncio
import sys
import time
import statistics
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from hydra_logger import getLogger, getSyncLogger, getAsyncLogger
from hydra_logger.config import get_default_config, get_development_config, get_production_config
from hydra_logger.core.logger_management import removeLogger, clearLoggers, listLoggers
from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
import tempfile
import os


class HydraLoggerBenchmark:
    """
    Performance benchmark for Hydra-Logger.
    
    Provides performance testing for all logger types, including individual
    message throughput, batch processing efficiency, memory usage analysis,
    and configuration performance comparison.
    """
    
    def __init__(self, save_results: bool = True, results_dir: str = "benchmark_results"):
        self.results = {}
        self.save_results = save_results
        self.results_dir = Path(results_dir)
        # Create results directory if saving
        if self.save_results:
            self.results_dir.mkdir(exist_ok=True)
        
        # Track all created loggers for proper cleanup
        self._created_loggers = []
        
        # Track logger names for cache cleanup
        self._logger_names = []
        
        # Create temporary directory for performance test log files
        self._temp_log_dir = tempfile.mkdtemp(prefix="hydra_logger_perf_")
        
        # Clear any existing loggers from global cache to ensure clean state
        # This prevents state pollution from previous benchmark runs
        try:
            existing_loggers = listLoggers()
            if existing_loggers:
                print(f"Cleaning up {len(existing_loggers)} existing loggers from global cache...")
                for logger_name in existing_loggers:
                    try:
                        removeLogger(logger_name)
                    except Exception:
                        pass
        except Exception:
            pass
        
        # Test configuration parameters
        self.test_config = {
            # Single message logging test parameters
            'typical_single_messages': 100000,
            'small_batch_size': 50,
            'medium_batch_size': 200,
            'large_batch_size': 1000,
            
            # Concurrent logging test parameters
            'concurrent_workers': 8,
            'messages_per_worker': 100,
            
            # Message size characteristics
            'message_size_small': 50,
            'message_size_medium': 150,
            'message_size_large': 500,
            
            # Scenario-based test parameters
            'web_request_logs': 20,
            'database_operation_logs': 10,
            'background_task_logs': 100,
            
            # Stress test parameters
            'stress_test_messages': 100000,
            'stress_concurrent_workers': 50,
        }
    
    def _create_performance_config(self, logger_type: str = "sync") -> LoggingConfig:
        """
        Create a performance-optimized configuration without console handlers.
        
        Console I/O is inherently slow (10-15K msg/s), so for performance tests
        we use file-only handlers to measure true logger performance.
        
        Args:
            logger_type: Type of logger (sync/async) to determine handler type
            
        Returns:
            LoggingConfig optimized for performance testing
        """
        # Use file-only handlers (much faster than console)
        if logger_type in ["async", "composite-async"]:
            file_type = "async_file"
        else:
            file_type = "file"
        
        # Create temporary log file for this test
        temp_file = os.path.join(self._temp_log_dir, f"perf_{id(self)}_{time.time()}.log")
        
        return LoggingConfig(
            default_level="INFO",
            enable_security=False,  # Disable for performance
            enable_sanitization=False,  # Disable for performance
            enable_plugins=False,  # Disable for performance
            enable_performance_monitoring=False,  # Disable for performance
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type=file_type,
                            path=temp_file,
                            format="json-lines",  # Fast format
                        ),
                    ],
                )
            },
        )
    
    def _flush_all_handlers(self, logger):
        """Flush all synchronous handlers in a logger.
        
        Async handlers must be flushed separately using _flush_all_handlers_async.
        """
        try:
            handlers = []
            
            # Collect layer handlers
            if hasattr(logger, '_layer_handlers'):
                for handlers_list in logger._layer_handlers.values():
                    handlers.extend(handlers_list)
            
            # Collect direct handlers
            if hasattr(logger, '_handlers'):
                direct_handlers = logger._handlers
                if isinstance(direct_handlers, dict):
                    handlers.extend(direct_handlers.values())
            
            # Flush synchronous handlers only
            for handler in handlers:
                if hasattr(handler, 'force_flush'):
                    if asyncio.iscoroutinefunction(handler.force_flush):
                        continue  # Skip async handlers
                    handler.force_flush()
                elif hasattr(handler, 'flush'):
                    if asyncio.iscoroutinefunction(handler.flush):
                        continue  # Skip async handlers
                    handler.flush()
        except Exception:
            pass
    
    async def _flush_all_handlers_async(self, logger):
        """Flush all handlers in a logger, including async handlers."""
        try:
            handlers = []
            direct_handlers = getattr(logger, '_handlers', {})
            if isinstance(direct_handlers, dict):
                handlers.extend(direct_handlers.values())
            
            layer_handlers = getattr(logger, '_layer_handlers', {})
            for handlers_list in layer_handlers.values():
                handlers.extend(handlers_list)
            
            # Flush handlers (await async ones)
            flush_tasks = []
            for handler in handlers:
                if hasattr(handler, 'flush'):
                    if asyncio.iscoroutinefunction(handler.flush):
                        flush_tasks.append(handler.flush())
                    else:
                        handler.flush()
                elif hasattr(handler, 'force_flush'):
                    if asyncio.iscoroutinefunction(handler.force_flush):
                        flush_tasks.append(handler.force_flush())
                    else:
                        handler.force_flush()
            
            # Await all async flushes in parallel
            if flush_tasks:
                await asyncio.gather(*flush_tasks, return_exceptions=True)
        except Exception:
            pass
    
    async def _wait_for_async_handlers(self, logger, timeout: float = 2.0) -> None:
        """Wait for async handlers to complete processing.
        
        Uses queue polling and async synchronization. Waits until all message
        queues are empty and handlers are done.
        
        Args:
            logger: Logger instance with async handlers
            timeout: Maximum time to wait (default: 2.0 seconds)
        """
        try:
            handlers = []
            # Collect all handlers
            if hasattr(logger, '_handlers'):
                handlers.extend(logger._handlers.values())
            if hasattr(logger, '_layer_handlers'):
                for handlers_list in logger._layer_handlers.values():
                    handlers.extend(handlers_list)
            
            # Check for async handlers with queues
            async_handlers = []
            for handler in handlers:
                # Check if handler has async queue
                if hasattr(handler, '_message_queue'):
                    async_handlers.append(handler)
                # Also check for worker tasks
                if hasattr(handler, '_worker_tasks') or hasattr(handler, '_worker_task'):
                    async_handlers.append(handler)
            
            if not async_handlers:
                # No async handlers, just flush sync handlers
                self._flush_all_handlers(logger)
                return
            
            # Poll queues until empty or timeout
            start_time = time.perf_counter()
            max_iterations = 100  # Prevent infinite loop
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                elapsed = time.perf_counter() - start_time
                
                if elapsed >= timeout:
                    break
                
                # Check all async handler queues
                all_queues_empty = True
                for handler in async_handlers:
                    queue = getattr(handler, '_message_queue', None)
                    if queue is not None:
                        queue_size = queue.qsize()
                        if queue_size > 0:
                            all_queues_empty = False
                            break
                    
                    # Also check message buffers
                    buffer = getattr(handler, '_message_buffer', None)
                    if buffer and len(buffer) > 0:
                        all_queues_empty = False
                        break
                
                if all_queues_empty:
                    # All queues empty, wait briefly for any final processing
                    await asyncio.sleep(0.01)
                    # Double-check one more time
                    still_empty = True
                    for handler in async_handlers:
                        queue = getattr(handler, '_message_queue', None)
                        if queue and queue.qsize() > 0:
                            still_empty = False
                            break
                    if still_empty:
                        break
                
                # Brief yield to let handlers process
                await asyncio.sleep(0.01)
            
            # Flush async handlers after waiting for queues
            await self._flush_all_handlers_async(logger)
            
        except Exception:
            # Fallback: try to flush if detection fails
            try:
                await self._flush_all_handlers_async(logger)
            except Exception:
                # Last resort: flush sync handlers only
                self._flush_all_handlers(logger)
    
    def _cleanup_logger_cache(self):
        """Remove all benchmark loggers from global cache to prevent state pollution."""
        try:
            for logger_name in self._logger_names:
                try:
                    removeLogger(logger_name)
                except Exception:
                    pass
            self._logger_names.clear()
        except Exception:
            pass
    
    async def _final_cleanup(self):
        """Dynamic cleanup: close all loggers, await all handler tasks, and clear cache."""
        try:
            loop = asyncio.get_running_loop()
            
            # Step 1: Close all tracked loggers properly
            close_tasks = []
            for logger in self._created_loggers:
                try:
                    if hasattr(logger, 'aclose') and asyncio.iscoroutinefunction(logger.aclose):
                        close_tasks.append(logger.aclose())
                    elif hasattr(logger, 'close_async') and asyncio.iscoroutinefunction(logger.close_async):
                        close_tasks.append(logger.close_async())
                    elif hasattr(logger, 'close') and callable(logger.close):
                        if not asyncio.iscoroutinefunction(logger.close):
                            logger.close()
                except Exception:
                    pass
            
            # Wait for all loggers to close
            if close_tasks:
                try:
                    await asyncio.gather(*close_tasks, return_exceptions=True)
                except Exception:
                    pass
            
            # Step 2: Collect all handler worker tasks from all loggers
            handler_tasks = []
            for logger in self._created_loggers:
                try:
                    # Get all handlers from logger
                    handlers = []
                    if hasattr(logger, '_handlers'):
                        handlers.extend(logger._handlers.values())
                    if hasattr(logger, '_console_handler') and logger._console_handler:
                        handlers.append(logger._console_handler)
                    if hasattr(logger, 'components'):
                        for component in logger.components:
                            if hasattr(component, '_handlers'):
                                handlers.extend(component._handlers.values())
                            if hasattr(component, '_console_handler') and component._console_handler:
                                handlers.append(component._console_handler)
                    
                    # Collect worker tasks from handlers
                    for handler in handlers:
                        if hasattr(handler, '_worker_task') and handler._worker_task and not handler._worker_task.done():
                            handler_tasks.append(handler._worker_task)
                        if hasattr(handler, '_worker_tasks') and handler._worker_tasks:
                            handler_tasks.extend([t for t in handler._worker_tasks if not t.done()])
                except Exception:
                    pass
            
            # Step 3: Also collect any remaining tasks in the event loop
            all_loop_tasks = [t for t in asyncio.all_tasks(loop) 
                            if t != asyncio.current_task() and not t.done()]
            
            # Combine and deduplicate
            all_tasks = list(set(handler_tasks + all_loop_tasks))
            
            if not all_tasks:
                return
            
            # Step 4: Adaptive waiting - check completion status dynamically
            max_wait_time = 2.0
            check_interval = 0.05
            elapsed = 0.0
            
            while elapsed < max_wait_time:
                done_tasks = [t for t in all_tasks if t.done()]
                if len(done_tasks) == len(all_tasks):
                    break
                await asyncio.sleep(check_interval)
                elapsed += check_interval
            
            # Step 5: Cancel and await any remaining tasks
            remaining = [t for t in all_tasks if not t.done()]
            if remaining:
                for task in remaining:
                    task.cancel()
                try:
                    await asyncio.wait(remaining, timeout=0.5, return_when=asyncio.ALL_COMPLETED)
                except Exception:
                    pass
                for task in remaining:
                    if not task.done():
                        try:
                            await asyncio.gather(task, return_exceptions=True)
                        except Exception:
                            pass
            
            # Step 6: Remove all loggers from global cache to prevent state pollution
            self._cleanup_logger_cache()
            
            # Step 7: Force garbage collection to free memory
            import gc
            gc.collect()
                            
        except RuntimeError:
            pass
        except Exception:
            pass
        finally:
            # Always cleanup cache, even on error
            self._cleanup_logger_cache()
            
            # Cleanup temporary log directory
            try:
                import shutil
                if hasattr(self, '_temp_log_dir') and os.path.exists(self._temp_log_dir):
                    shutil.rmtree(self._temp_log_dir, ignore_errors=True)
            except Exception:
                pass
        
    def print_header(self):
        """Print benchmark header information."""
        print("=" * 80)
        print("HYDRA-LOGGER PERFORMANCE BENCHMARK")
        print("=" * 80)
        print(f"Test Configuration:")
        print(f"   Typical Single Messages: {self.test_config['typical_single_messages']:,}")
        print(f"   Small Batch Size: {self.test_config['small_batch_size']:,}")
        print(f"   Medium Batch Size: {self.test_config['medium_batch_size']:,}")
        print(f"   Large Batch Size: {self.test_config['large_batch_size']:,}")
        print(f"   Concurrent Workers: {self.test_config['concurrent_workers']}")
        print(f"   Messages per Worker: {self.test_config['messages_per_worker']:,}")
        print(f"   Scenario Parameters:")
        print(f"     - Web Request Logs: {self.test_config['web_request_logs']} msgs/request")
        print(f"     - DB Operation Logs: {self.test_config['database_operation_logs']} msgs/op")
        print(f"     - Background Task Logs: {self.test_config['background_task_logs']} msgs/task")
        print("=" * 80)
        
    def test_sync_logger_performance(self) -> Dict[str, Any]:
        """
        Test synchronous logger performance.
        
        Returns:
            Dict containing performance metrics for sync logger
        """
        print("\nTesting Sync Logger Performance...")
        print("   Testing individual message throughput...")
        
        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_sync_{id(self)}"
        perf_config = self._create_performance_config(logger_type="sync")
        logger = getSyncLogger(logger_name, config=perf_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config['typical_single_messages']
        
        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Processing request {i} for user_id=12345",
                f"Database query completed in {i*0.001:.3f}s, rows={i%100}",
                f"API endpoint /api/v1/users called, response_code=200, duration={i}ms",
                f"Cache hit for key 'user:12345:profile', ttl={i*60}s",
                f"Background job 'process_payment' started, job_id={i}",
                f"Error occurred: Connection timeout after {i*10}ms retries",
            ]
            return patterns[i % len(patterns)]
        
        # Warm-up period to avoid initialization overhead
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        for i in range(warmup_count):
            logger.info(generate_realistic_message(i))
        
        # Force flush before timing starts
        self._flush_all_handlers(logger)
        time.sleep(0.5)  # Pause for file I/O to complete
        
        # Test with realistic messages
        start_time = time.perf_counter()
        for i in range(message_count):
            logger.info(generate_realistic_message(i))
        # Force flush after logging to include I/O in timing
        self._flush_all_handlers(logger)
        # Force OS-level sync to ensure all file I/O completes
        import os as os_module
        try:
            for handler in getattr(logger, '_layer_handlers', {}).get('default', []):
                if hasattr(handler, '_file_handle') and handler._file_handle:
                    try:
                        handler._file_handle.flush()
                        os_module.fsync(handler._file_handle.fileno())
                    except (AttributeError, OSError):
                        pass
        except Exception:
            pass
        # End timing BEFORE sleep to measure actual logging performance (not I/O wait time)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        messages_per_second = message_count / duration
        
        # Wait for file I/O to complete (for accurate byte counting, not performance measurement)
        time.sleep(0.5)
        
        # Cleanup
        try:
            logger.close()
        except Exception:
            pass
        
        result = {
            'logger_type': 'Sync Logger',
            'individual_messages_per_second': messages_per_second,
            'individual_duration': duration,
            'total_messages': message_count,
            'status': 'COMPLETED'
        }
        
        print(f"   Individual Messages: {messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")
        print("   Sync Logger: COMPLETED")
        
        return result
        
    async def test_async_logger_performance(self) -> Dict[str, Any]:
        """
        Test asynchronous logger performance.
        
        Returns:
            Dict containing performance metrics for async logger
        """
        print("\nTesting Async Logger Performance...")
        print("   Testing individual message throughput...")
        
        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_async_{id(self)}"
        perf_config = self._create_performance_config(logger_type="async")
        logger = getAsyncLogger(logger_name, config=perf_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config['typical_single_messages']
        
        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Async task {i} completed: processed {i*10} items",
                f"WebSocket message received: channel='notifications', size={i*50}B",
                f"Event loop processing: {i} pending tasks, queue_size={i%50}",
                f"HTTP client request to api.example.com: GET /users/{i}, status=200",
                f"Async cache operation: key='session:{i}', hit={'true' if i%2==0 else 'false'}",
                f"Background worker processing job batch {i}, progress={i}%",
            ]
            return patterns[i % len(patterns)]
        
        # Warm-up period
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_tasks = []
        for i in range(warmup_count):
            warmup_tasks.append(logger.log("INFO", generate_realistic_message(i)))
        await asyncio.gather(*warmup_tasks)
        
        # Wait for warm-up handlers to complete
        await self._wait_for_async_handlers(logger, timeout=1.0)
        
        # Batch task creation for large message counts
        start_time = time.perf_counter()
        
        # For large batches, create tasks in chunks to reduce overhead
        if message_count > 10000:
            chunk_size = 10000
            for chunk_start in range(0, message_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, message_count)
                tasks = [
                    logger.log("INFO", generate_realistic_message(i))
                    for i in range(chunk_start, chunk_end)
                ]
                await asyncio.gather(*tasks)
        else:
            # Small batches: create all tasks at once
            tasks = [
                logger.log("INFO", generate_realistic_message(i))
                for i in range(message_count)
            ]
            await asyncio.gather(*tasks)
        
        # End timing BEFORE close to measure actual logging performance (not cleanup)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        messages_per_second = message_count / duration
        
        # Close logger after timing (cleanup doesn't affect performance measurement)
        # Standard: use aclose() first (standard async context manager protocol)
        # Fallback: use close_async() for backward compatibility
        if hasattr(logger, 'aclose') and asyncio.iscoroutinefunction(logger.aclose):
            await logger.aclose()
        elif hasattr(logger, 'close_async') and asyncio.iscoroutinefunction(logger.close_async):
            await logger.close_async()
        
        result = {
            'logger_type': 'Async Logger',
            'individual_messages_per_second': messages_per_second,
            'individual_duration': duration,
            'total_messages': message_count,
            'status': 'COMPLETED'
        }
        
        print(f"   Individual Messages: {messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")
        print("   Async Logger: COMPLETED")
        
        return result
        
    def test_composite_logger_performance(self) -> Dict[str, Any]:
        """
        Test composite logger performance.
        
        Returns:
            Dict containing performance metrics for composite logger
        """
        print("\nTesting Composite Logger Performance...")
        print("   Testing individual message throughput...")
        
        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_composite_{id(self)}"
        perf_config = self._create_performance_config(logger_type="sync")
        logger = getLogger(logger_name, logger_type="composite", config=perf_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config['typical_single_messages']
        
        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Composite logger: Processing transaction {i}, amount=${i*10.50:.2f}",
                f"Multi-handler log: User action 'view_profile' by user_id={i}",
                f"Composite output: API rate limit check, remaining={1000-i}",
                f"Multi-destination: Audit log entry {i} for compliance tracking",
                f"Composite sync: Payment processed for order_id={i}, status='completed'",
            ]
            return patterns[i % len(patterns)]
        
        # Warm-up
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        for i in range(warmup_count):
            logger.info(generate_realistic_message(i))
        
        # Flush before timing
        self._flush_all_handlers(logger)
        time.sleep(0.5)
        
        # Test with realistic messages
        start_time = time.perf_counter()
        for i in range(message_count):
            logger.info(generate_realistic_message(i))
        # Flush after logging
        self._flush_all_handlers(logger)
        # Force OS-level sync
        import os as os_module
        try:
            for handler in getattr(logger, '_layer_handlers', {}).get('default', []):
                if hasattr(handler, '_file_handle') and handler._file_handle:
                    try:
                        handler._file_handle.flush()
                        os_module.fsync(handler._file_handle.fileno())
                    except (AttributeError, OSError):
                        pass
        except Exception:
            pass
        # End timing BEFORE sleep to measure actual logging performance (not I/O wait time)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        individual_messages_per_second = message_count / duration
        
        # Wait for file I/O to complete (for accurate byte counting, not performance measurement)
        time.sleep(0.5)
        
        print(f"   Individual Messages: {individual_messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")
        
        # Test with batch sizes
        print("   Testing small batch...")
        batch_size = self.test_config['small_batch_size']
        messages = [("INFO", generate_realistic_message(i), {}) for i in range(batch_size)]
        
        start_time = time.perf_counter()
        logger.log_batch(messages)
        self._flush_all_handlers(logger)
        end_time = time.perf_counter()
        
        small_batch_duration = end_time - start_time
        small_batch_messages_per_second = batch_size / small_batch_duration
        
        print(f"   Small Batch ({batch_size} msgs): {small_batch_messages_per_second:,.0f} msg/s")
        
        # Test medium batch
        print("   Testing medium batch...")
        batch_size = self.test_config['medium_batch_size']
        messages = [("INFO", generate_realistic_message(i), {}) for i in range(batch_size)]
        
        start_time = time.perf_counter()
        logger.log_batch(messages)
        self._flush_all_handlers(logger)
        end_time = time.perf_counter()
        
        batch_duration = end_time - start_time
        batch_messages_per_second = batch_size / batch_duration
        
        # Cleanup
        try:
            logger.close()
        except Exception:
            pass
        
        result = {
            'logger_type': 'Composite Logger',
            'individual_messages_per_second': individual_messages_per_second,
            'small_batch_messages_per_second': small_batch_messages_per_second,
            'batch_messages_per_second': batch_messages_per_second,
            'individual_duration': duration,
            'small_batch_duration': small_batch_duration,
            'batch_duration': batch_duration,
            'total_messages': message_count,
            'small_batch_size': self.test_config['small_batch_size'],
            'batch_size': batch_size,
            'status': 'COMPLETED'
        }
        
        print(f"   Medium Batch Messages: {batch_messages_per_second:,.0f} msg/s")
        print(f"   Medium Batch Duration: {batch_duration:.3f}s")
        print("   Composite Logger: COMPLETED")
        
        return result
        
    async def test_composite_async_logger_performance(self) -> Dict[str, Any]:
        """
        Test composite async logger performance.
        
        Returns:
            Dict containing performance metrics for composite async logger
        """
        print("\nTesting Composite Async Logger Performance...")
        print("   Testing individual message throughput...")
        
        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_composite_async_{id(self)}"
        perf_config = self._create_performance_config(logger_type="async")
        logger = getLogger(logger_name, logger_type="composite-async", config=perf_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config['typical_single_messages']
        
        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Async composite: WebSocket message broadcast to {i} clients",
                f"Multi-handler async: Background job completed, processed {i*5} items",
                f"Async composite: API request routed to service {i%3}, latency={i}ms",
                f"Composite async: Event stream processing, event_id={i}, size={i*100}B",
                f"Multi-destination async: Audit log entry {i} written to multiple targets",
            ]
            return patterns[i % len(patterns)]
        
        # Warm-up period
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_tasks = []
        for i in range(warmup_count):
            warmup_tasks.append(logger.log("INFO", generate_realistic_message(i)))
        await asyncio.gather(*warmup_tasks)
        
        # Wait for warm-up handlers to complete
        await self._wait_for_async_handlers(logger, timeout=1.0)
        
        # Batch task creation for large message counts
        start_time = time.perf_counter()
        
        # For large batches, create tasks in chunks to reduce overhead
        if message_count > 10000:
            chunk_size = 10000
            for chunk_start in range(0, message_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, message_count)
                tasks = [
                    logger.log("INFO", generate_realistic_message(i))
                    for i in range(chunk_start, chunk_end)
                ]
                await asyncio.gather(*tasks)
        else:
            # Small batches: create all tasks at once
            tasks = [
                logger.log("INFO", generate_realistic_message(i))
                for i in range(message_count)
            ]
            await asyncio.gather(*tasks)
        
        # End timing BEFORE close to measure actual logging performance (not cleanup)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        individual_messages_per_second = message_count / duration
        
        print(f"   Individual Messages: {individual_messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")
        
        # Test with batch sizes
        print("   Testing small batch...")
        batch_size = self.test_config['small_batch_size']
        messages = [("INFO", generate_realistic_message(i), {}) for i in range(batch_size)]
        
        start_time = time.perf_counter()
        await logger.log_batch(messages)
        end_time = time.perf_counter()
        
        batch_duration = end_time - start_time
        batch_messages_per_second = batch_size / batch_duration
        
        # Close logger after timing (cleanup doesn't affect performance measurement)
        # Standard: use aclose() first (standard async context manager protocol)
        # Fallback: use close_async() for backward compatibility
        if hasattr(logger, 'aclose') and asyncio.iscoroutinefunction(logger.aclose):
            await logger.aclose()
        elif hasattr(logger, 'close_async') and asyncio.iscoroutinefunction(logger.close_async):
            await logger.close_async()
        
        result = {
            'logger_type': 'Composite Async Logger',
            'individual_messages_per_second': individual_messages_per_second,
            'batch_messages_per_second': batch_messages_per_second,
            'individual_duration': duration,
            'batch_duration': batch_duration,
            'total_messages': message_count,
            'batch_size': batch_size,
            'status': 'COMPLETED'
        }
        
        print(f"   Batch Messages: {batch_messages_per_second:,.0f} msg/s")
        print(f"   Batch Duration: {batch_duration:.3f}s")
        print("   Composite Async Logger: COMPLETED")
        
        return result
        
    def test_file_writing_performance(self) -> Dict[str, Any]:
        """
        Test file writing performance (file handlers only).
        
        Returns:
            Dict containing file writing performance metrics
        """
        print("\nTesting File Writing Performance...")
        print("   Testing file handler I/O performance...")
        
        from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
        import tempfile
        import os
        
        # Create a temporary log file for testing
        temp_dir = tempfile.mkdtemp(prefix="hydra_logger_benchmark_")
        temp_file = os.path.join(temp_dir, "benchmark_file.log")
        
        # Create configuration with FILE ONLY (no console)
        file_only_config = LoggingConfig(
            default_level="INFO",
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=temp_file,
                            format="json-lines",
                        ),
                    ],
                )
            },
        )
        
        # Use unique logger name to avoid cache conflicts
        logger_name = f"benchmark_file_{id(self)}"
        logger = getLogger(logger_name, config=file_only_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config['typical_single_messages']
        
        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"File write test: Processing request {i} for user_id=12345",
                f"File I/O: Database query completed in {i*0.001:.3f}s, rows={i%100}",
                f"File log: API endpoint /api/v1/users called, response_code=200, duration={i}ms",
                f"File write: Cache hit for key 'user:12345:profile', ttl={i*60}s",
                f"File handler: Background job 'process_payment' started, job_id={i}",
                f"File output: Error occurred: Connection timeout after {i*10}ms retries",
            ]
            return patterns[i % len(patterns)]
        
        # Warm-up
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        for i in range(warmup_count):
            logger.info(generate_realistic_message(i))
        
        # Flush before timing
        self._flush_all_handlers(logger)
        time.sleep(0.5)
        
        # Initialize initial_size to avoid undefined variable
        initial_size = 0
        if os.path.exists(temp_file):
            initial_size = os.path.getsize(temp_file)
            print(f"   Warm-up wrote {initial_size:,} bytes to file")
        else:
            print("   Warning: File not created during warm-up, will measure from zero")
        
        # Test file writing performance
        print("   Testing file writing performance...")
        start_time = time.perf_counter()
        for i in range(message_count):
            logger.info(generate_realistic_message(i))
        
        # Flush after logging to ensure all data is written
        self._flush_all_handlers(logger)
        
        # Force OS-level sync and wait for I/O to complete
        import os as os_module
        try:
            for handler in getattr(logger, '_layer_handlers', {}).get('default', []):
                if hasattr(handler, '_file_handle') and handler._file_handle:
                    try:
                        handler._file_handle.flush()
                        os_module.fsync(handler._file_handle.fileno())
                    except (AttributeError, OSError):
                        pass
                # Also check handler stats for bytes written
                if hasattr(handler, 'get_stats'):
                    stats = handler.get_stats()
                    if 'total_bytes_written' in stats:
                        print(f"   Handler reports {stats['total_bytes_written']:,} bytes written")
        except Exception:
            pass
        
        # End timing BEFORE sleep to measure actual logging performance (not I/O wait time)
        end_time = time.perf_counter()
        
        # Wait for file system to sync (for accurate byte counting, not performance measurement)
        time.sleep(0.5)
        
        # Get bytes written from handler stats (more reliable than file size)
        bytes_written = 0
        handler_bytes = 0
        try:
            for handler in getattr(logger, '_layer_handlers', {}).get('default', []):
                if hasattr(handler, 'get_stats'):
                    stats = handler.get_stats()
                    if 'total_bytes_written' in stats:
                        handler_bytes = max(handler_bytes, stats['total_bytes_written'])
        except Exception:
            pass
        
        # Verify file size increased (use handler stats if available, otherwise file size)
        final_size = 0
        if os.path.exists(temp_file):
            final_size = os.path.getsize(temp_file)
            file_bytes = final_size - initial_size
            # Use handler stats if available (more accurate), otherwise use file size
            bytes_written = handler_bytes if handler_bytes > 0 else file_bytes
            print(f"   Initial file size: {initial_size:,} bytes")
            print(f"   Final file size: {final_size:,} bytes")
            print(f"   Handler bytes written: {handler_bytes:,} bytes")
            print(f"   File size increase: {file_bytes:,} bytes")
            print(f"   Total bytes written: {bytes_written:,} bytes")
            if bytes_written <= 0:
                print("   Warning: No bytes written. File I/O may not have completed.")
        else:
            # File doesn't exist, but handler might have stats
            bytes_written = handler_bytes
            if bytes_written > 0:
                print(f"   Handler reports {bytes_written:,} bytes written (file not yet created)")
            else:
                print("   Error: File was not created and handler has no stats")
                bytes_written = 0
        
        duration = end_time - start_time
        messages_per_second = message_count / duration
        bytes_per_second = bytes_written / duration if duration > 0 else 0
        
        # Cleanup
        try:
            logger.close()
        except Exception:
            pass
        
        # Clean up temporary file
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass
        
        result = {
            'logger_type': 'File Handler Only',
            'messages_per_second': messages_per_second,
            'bytes_per_second': bytes_per_second,
            'bytes_written': bytes_written,
            'duration': duration,
            'total_messages': message_count,
            'file_path': temp_file,
            'status': 'COMPLETED'
        }
        
        print(f"   File Writing: {messages_per_second:,.0f} msg/s")
        print(f"   File I/O Speed: {bytes_per_second:,.0f} bytes/s")
        print(f"   Duration: {duration:.3f}s")
        print("   File Writing: COMPLETED")
        
        return result
    
    async def test_async_file_writing_performance(self) -> Dict[str, Any]:
        """
        Test async file writing performance (async file handlers only).
        
        Returns:
            Dict containing async file writing performance metrics
        """
        print("\nTesting Async File Writing Performance...")
        print("   Testing async file handler I/O performance...")
        
        from hydra_logger.config.models import LoggingConfig, LogLayer, LogDestination
        import tempfile
        import os
        
        # Create a temporary log file for testing
        temp_dir = tempfile.mkdtemp(prefix="hydra_logger_benchmark_async_")
        temp_file = os.path.join(temp_dir, "benchmark_async_file.log")
        
        # Create configuration with ASYNC FILE ONLY (no console)
        async_file_only_config = LoggingConfig(
            default_level="INFO",
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_file",
                            path=temp_file,
                            format="json-lines",
                        ),
                    ],
                )
            },
        )
        
        # Use unique logger name to avoid cache conflicts
        logger_name = f"benchmark_async_file_{id(self)}"
        logger = getAsyncLogger(logger_name, config=async_file_only_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config['typical_single_messages']
        
        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Async file write: Processing async task {i}, processed {i*10} items",
                f"Async file I/O: WebSocket message received, channel='notifications', size={i*50}B",
                f"Async file log: Event loop processing: {i} pending tasks, queue_size={i%50}",
                f"Async file handler: HTTP client request to api.example.com: GET /users/{i}, status=200",
                f"Async file output: Background worker processing job batch {i}, progress={i}%",
            ]
            return patterns[i % len(patterns)]
        
        # Warm-up
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_tasks = []
        for i in range(warmup_count):
            warmup_tasks.append(logger.log("INFO", generate_realistic_message(i)))
        await asyncio.gather(*warmup_tasks)
        
        # Wait for warm-up handlers to complete
        await self._wait_for_async_handlers(logger, timeout=1.0)
        
        # Initialize initial_size to avoid undefined variable
        initial_size = 0
        if os.path.exists(temp_file):
            initial_size = os.path.getsize(temp_file)
            print(f"   Warm-up wrote {initial_size:,} bytes to file")
        else:
            print("   Warning: File not created during warm-up, will measure from zero")
        
        # Test async file writing performance
        print("   Testing async file writing performance...")
        start_time = time.perf_counter()
        
        # Batch task creation for efficiency
        if message_count > 10000:
            chunk_size = 10000
            for chunk_start in range(0, message_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, message_count)
                tasks = [
                    logger.log("INFO", generate_realistic_message(i))
                    for i in range(chunk_start, chunk_end)
                ]
                await asyncio.gather(*tasks)
        else:
            tasks = [
                logger.log("INFO", generate_realistic_message(i))
                for i in range(message_count)
            ]
            await asyncio.gather(*tasks)
        
        # End timing BEFORE close/sleep to measure actual logging performance (not cleanup)
        end_time = time.perf_counter()
        
        # Close logger after timing (cleanup doesn't affect performance measurement)
        print("   Finalizing writes...")
        if hasattr(logger, 'close_async'):
            await logger.close_async()
        elif hasattr(logger, 'aclose'):
            await logger.aclose()
        else:
            # Fallback: flush handlers manually
            await self._flush_all_handlers_async(logger)
        
        # Wait for async file operations to complete (for accurate byte counting)
        await asyncio.sleep(0.5)
        
        # Get bytes written from handler stats (more reliable than file size)
        bytes_written = 0
        handler_bytes = 0
        try:
            for handler in getattr(logger, '_layer_handlers', {}).get('default', []):
                if hasattr(handler, 'get_stats'):
                    stats = handler.get_stats()
                    if 'total_bytes_written' in stats:
                        handler_bytes = max(handler_bytes, stats['total_bytes_written'])
        except Exception:
            pass
        
        # Verify file size increased (use handler stats if available, otherwise file size)
        final_size = 0
        if os.path.exists(temp_file):
            final_size = os.path.getsize(temp_file)
            file_bytes = final_size - initial_size
            # Use handler stats if available (more accurate), otherwise use file size
            bytes_written = handler_bytes if handler_bytes > 0 else file_bytes
            print(f"   Initial file size: {initial_size:,} bytes")
            print(f"   Final file size: {final_size:,} bytes")
            print(f"   Handler bytes written: {handler_bytes:,} bytes")
            print(f"   File size increase: {file_bytes:,} bytes")
            print(f"   Total bytes written: {bytes_written:,} bytes")
            if bytes_written <= 0:
                print("   Warning: No bytes written. Async handlers may not have completed.")
        else:
            # File doesn't exist, but handler might have stats
            bytes_written = handler_bytes
            if bytes_written > 0:
                print(f"   Handler reports {bytes_written:,} bytes written (file not yet created)")
            else:
                print("   Error: File was not created and handler has no stats")
                bytes_written = 0
        
        duration = end_time - start_time
        messages_per_second = message_count / duration
        bytes_per_second = bytes_written / duration if duration > 0 else 0
        
        # Clean up temporary file
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception:
            pass
        
        result = {
            'logger_type': 'Async File Handler Only',
            'messages_per_second': messages_per_second,
            'bytes_per_second': bytes_per_second,
            'bytes_written': bytes_written,
            'duration': duration,
            'total_messages': message_count,
            'file_path': temp_file,
            'status': 'COMPLETED'
        }
        
        print(f"   Async File Writing: {messages_per_second:,.0f} msg/s")
        print(f"   Async File I/O Speed: {bytes_per_second:,.0f} bytes/s")
        print(f"   Duration: {duration:.3f}s")
        print("   Async File Writing: COMPLETED")
        
        return result
    
    def test_configuration_performance(self) -> Dict[str, Any]:
        """
        Test performance with different configurations.
        
        Returns:
            Dict containing performance metrics for different configurations
        """
        print("\nTesting Configuration Performance...")
        print("   Testing different configuration impacts...")
        
        configs = {
            'default': get_default_config(),
            'development': get_development_config(),
            'production': get_production_config()
        }
        
        config_results = {}
        message_count = self.test_config['typical_single_messages']
        
        for config_name, config in configs.items():
            print(f"   Testing {config_name.title()} configuration...")
            # Use unique logger name to avoid cache conflicts
            logger_name = f"benchmark_{config_name}_{id(self)}"
            logger = getLogger(logger_name, config=config)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)
            
            # Warm-up
            warmup_count = min(1000, message_count // 100)
            for i in range(warmup_count):
                logger.info(f"Warm-up {i}")
            
            # Flush before timing
            self._flush_all_handlers(logger)
            
            start_time = time.perf_counter()
            for i in range(message_count):
                logger.info(f"{config_name.title()} config benchmark message {i}")
            # Flush after logging
            self._flush_all_handlers(logger)
            end_time = time.perf_counter()
            
            duration = end_time - start_time
            messages_per_second = message_count / duration
            
            # Cleanup
            try:
                logger.close()
            except Exception:
                pass
            
            config_results[config_name] = {
                'messages_per_second': messages_per_second,
                'duration': duration,
                'total_messages': message_count
            }
            
            print(f"   {config_name.title()} Config: {messages_per_second:,.0f} msg/s")
        
        print("   Configuration Performance: COMPLETED")
        return config_results
        
    def test_memory_usage(self) -> Dict[str, Any]:
        """
        Test memory usage patterns.
        
        Returns:
            Dict containing memory usage metrics
        """
        print("\nTesting Memory Usage...")
        print("   Testing memory efficiency...")
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Test with multiple loggers
            loggers = []
            logger_count = 50
            
            for i in range(logger_count):
                # Use unique logger name to avoid cache conflicts
                logger_name = f"memory_test_{i}_{id(self)}"
                logger = getLogger(logger_name)
                loggers.append(logger)
                self._created_loggers.append(logger)
                self._logger_names.append(logger_name)
                logger.info(f"Memory test message {i}")
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            result = {
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase,
                'loggers_created': logger_count,
                'memory_per_logger_mb': memory_increase / logger_count if logger_count > 0 else 0,
                'status': 'COMPLETED'
            }
            
            print(f"   Memory Increase: {memory_increase:.2f} MB for {logger_count} loggers")
            print(f"   Memory per Logger: {result['memory_per_logger_mb']:.4f} MB")
            print("   Memory Usage: COMPLETED")
            
            return result
            
        except ImportError:
            print("   Warning: psutil not available, skipping memory test")
            return {'status': 'SKIPPED', 'reason': 'psutil not available'}
            
    async def test_concurrent_logging(self) -> Dict[str, Any]:
        """
        Test concurrent logging performance using async tasks (not threads).
        
        Using async tasks instead of threads eliminates event loop creation overhead
        and provides better performance for async loggers.
        
        Returns:
            Dict containing concurrent logging metrics
        """
        print("\nTesting Concurrent Logging...")
        print("   Testing async concurrent logging performance...")
        
        num_workers = self.test_config['concurrent_workers']
        messages_per_worker = self.test_config['messages_per_worker']
        
        # Use composite-async logger for better performance (like async_concurrent test)
        # Use unique logger name to avoid cache conflicts
        logger_name = f"concurrent_shared_{id(self)}"
        shared_logger = getLogger(logger_name, logger_type="composite-async")
        self._created_loggers.append(shared_logger)
        self._logger_names.append(logger_name)
        
        async def async_worker(worker_id):
            """Async worker that logs messages concurrently."""
            start_time = time.perf_counter()
            # Use batch logging for better performance (much faster than individual tasks)
            if hasattr(shared_logger, 'log_batch'):
                messages = [
                    ("INFO", f"Worker {worker_id} message {i}", {})
                    for i in range(messages_per_worker)
                ]
                await shared_logger.log_batch(messages)
            else:
                # Fallback: batch create all tasks at once
                tasks = [
                    shared_logger.log("INFO", f"Worker {worker_id} message {i}")
                    for i in range(messages_per_worker)
                ]
                await asyncio.gather(*tasks)
            end_time = time.perf_counter()
            duration = end_time - start_time
            messages_per_second = messages_per_worker / duration if duration > 0 else 0
            return {
                'worker_id': worker_id,
                'duration': duration,
                'messages_per_second': messages_per_second
            }
        
        # Start all workers concurrently using async tasks (much faster than threads)
        start_time = time.perf_counter()
        worker_tasks = [async_worker(i) for i in range(num_workers)]
        worker_results = await asyncio.gather(*worker_tasks)
        
        # End timing BEFORE flush/cleanup to measure actual logging performance
        end_time = time.perf_counter()
        total_duration = end_time - start_time
        
        # Flush after timing (cleanup doesn't affect performance measurement)
        await self._flush_all_handlers_async(shared_logger)
        
        # Calculate total throughput (total messages across all workers / total duration)
        # This is the aggregate throughput, not per-worker
        total_messages = num_workers * messages_per_worker
        total_messages_per_second = total_messages / total_duration
        
        # Calculate per-worker statistics (for comparison)
        worker_speeds = [w['messages_per_second'] for w in worker_results if 'messages_per_second' in w]
        
        # Cleanup
        try:
            if hasattr(shared_logger, 'aclose') and asyncio.iscoroutinefunction(shared_logger.aclose):
                await shared_logger.aclose()
            elif hasattr(shared_logger, 'close_async') and asyncio.iscoroutinefunction(shared_logger.close_async):
                await shared_logger.close_async()
            elif hasattr(shared_logger, 'close'):
                shared_logger.close()
        except Exception:
            pass
        
        # Handle empty results
        if not worker_speeds:
            print("   Warning: No workers completed successfully")
            return {
                'total_duration': total_duration,
                'total_messages_per_second': 0,
                'worker_results': [],
                'num_threads': num_workers,  # Keep for backward compatibility
                'messages_per_thread': messages_per_worker,  # Keep for backward compatibility
                'total_messages': total_messages,
                'avg_thread_speed': 0,
                'min_thread_speed': 0,
                'max_thread_speed': 0,
                'status': 'FAILED'
            }
        
        result = {
            'total_duration': total_duration,
            'total_messages_per_second': total_messages_per_second,
            'thread_results': worker_results,  # Keep key name for backward compatibility
            'num_threads': num_workers,  # Keep for backward compatibility
            'messages_per_thread': messages_per_worker,  # Keep for backward compatibility
            'total_messages': total_messages,
            'avg_thread_speed': statistics.mean(worker_speeds),  # Keep for backward compatibility
            'min_thread_speed': min(worker_speeds),
            'max_thread_speed': max(worker_speeds),
            'status': 'COMPLETED'
        }
        
        print(f"   Total Throughput: {total_messages_per_second:,.0f} msg/s (total aggregate across {num_workers} workers)")
        print(f"   Avg Worker Speed: {result['avg_thread_speed']:,.0f} msg/s (per worker, for reference)")
        print("   Concurrent Logging: COMPLETED")
        
        return result
        
    async def test_advanced_concurrent_logging(self) -> Dict[str, Any]:
        """
        Test advanced concurrent logging scenarios.
        
        Returns:
            Dict containing advanced concurrent logging metrics
        """
        print("\nTesting Advanced Concurrent Logging...")
        print("   Testing multiple concurrent scenarios...")
        
        import threading
        import queue
        import asyncio
        
        results = {}
        
        # Test 1: Shared logger with different thread counts
        print("   Testing shared logger scalability...")
        thread_counts = [1, 2, 5, 10, 20]
        shared_results = {}
        
        for thread_count in thread_counts:
            # Use unique logger name to avoid cache conflicts
            # Use composite-async for better performance (like async_concurrent test)
            logger_name = f"shared_{thread_count}_{id(self)}"
            shared_logger = getLogger(logger_name, logger_type="composite-async")
            self._created_loggers.append(shared_logger)
            self._logger_names.append(logger_name)
            messages_per_worker = 500
            
            async def async_worker(worker_id):
                """Async worker that logs messages concurrently."""
                start_time = time.perf_counter()
                # Use batch logging for better performance (much faster than individual tasks)
                if hasattr(shared_logger, 'log_batch'):
                    messages = [
                        ("INFO", f"Shared Worker {worker_id} message {i}", {})
                        for i in range(messages_per_worker)
                    ]
                    await shared_logger.log_batch(messages)
                else:
                    # Fallback: batch create all tasks at once
                    tasks = [
                        shared_logger.log("INFO", f"Shared Worker {worker_id} message {i}")
                        for i in range(messages_per_worker)
                    ]
                    await asyncio.gather(*tasks)
                end_time = time.perf_counter()
                return end_time - start_time
            
            # Use async tasks instead of threads (much faster - no event loop creation overhead)
            start_time = time.perf_counter()
            worker_tasks = [async_worker(i) for i in range(thread_count)]
            await asyncio.gather(*worker_tasks)
            
            # End timing BEFORE flush/cleanup to measure actual logging performance
            end_time = time.perf_counter()
            total_duration = end_time - start_time
            # Calculate total throughput (total messages across all workers / total duration)
            total_messages = thread_count * messages_per_worker
            messages_per_second = total_messages / total_duration
            
            # Flush and close after timing (cleanup doesn't affect performance measurement)
            await self._flush_all_handlers_async(shared_logger)
            if hasattr(shared_logger, 'aclose') and asyncio.iscoroutinefunction(shared_logger.aclose):
                await shared_logger.aclose()
            elif hasattr(shared_logger, 'close_async') and asyncio.iscoroutinefunction(shared_logger.close_async):
                await shared_logger.close_async()
            elif hasattr(shared_logger, 'close'):
                shared_logger.close()
            
            shared_results[thread_count] = {
                'messages_per_second': messages_per_second,
                'duration': total_duration,
                'efficiency': messages_per_second / thread_count
            }
            
            per_thread = messages_per_second / thread_count
            print(f"   {thread_count:2d} threads: {messages_per_second:>8,.0f} msg/s (total aggregate, {per_thread:>6,.0f} msg/s per thread)")
        
        # Test 2: Async concurrent logging
        print("   Testing async concurrent logging...")
        
        async def async_concurrent_test():
            # Use unique logger name to avoid cache conflicts
            logger_name = f"async_concurrent_{id(self)}"
            async_logger = getLogger(logger_name, logger_type="composite-async")
            self._created_loggers.append(async_logger)
            self._logger_names.append(logger_name)
            messages_per_task = 1000
            num_tasks = 20
            
            async def async_worker(task_id):
                start_time = time.perf_counter()
                tasks = []
                for i in range(messages_per_task):
                    tasks.append(async_logger.log("INFO", f"Async Task {task_id} message {i}"))
                await asyncio.gather(*tasks)
                end_time = time.perf_counter()
                return end_time - start_time
            
            start_time = time.perf_counter()
            worker_tasks = [async_worker(i) for i in range(num_tasks)]
            durations = await asyncio.gather(*worker_tasks)
            
            # End timing BEFORE close to measure actual logging performance (not cleanup)
            end_time = time.perf_counter()
            
            total_duration = end_time - start_time
            total_messages = num_tasks * messages_per_task
            messages_per_second = total_messages / total_duration
            
            # Close logger after timing (cleanup doesn't affect performance measurement)
            if hasattr(async_logger, 'close_async'):
                await async_logger.close_async()
            elif hasattr(async_logger, 'aclose'):
                await async_logger.aclose()
            
            return {
                'messages_per_second': messages_per_second,
                'duration': total_duration,
                'num_tasks': num_tasks,
                'messages_per_task': messages_per_task
            }
        
        # Run async test
        async_result = await async_concurrent_test()
        print(f"   Async {async_result['num_tasks']} tasks: {async_result['messages_per_second']:>8,.0f} msg/s")
        
        # Test 3: Mixed sync/async concurrent
        print("   Testing mixed sync/async concurrent...")
        
        def mixed_worker(thread_id, is_async=False):
            # Use unique logger name to avoid cache conflicts
            # Use file-only config for performance (console I/O is slow)
            logger_name = f"mixed_sync_{thread_id}_{id(self)}"
            perf_config = self._create_performance_config(logger_type="sync")
            logger = getLogger(logger_name, logger_type="composite", config=perf_config)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)
            
            start_time = time.perf_counter()
            # OPTIMIZATION: Use batch logging instead of individual calls (much faster!)
            messages = [
                ("INFO", f"Mixed Thread {thread_id} message {i}", {})
                for i in range(250)
            ]
            # Use batch logging if available (much faster than individual calls)
            if hasattr(logger, 'log_batch'):
                logger.log_batch(messages)
            else:
                # Fallback: individual calls (slower but works)
                for level, msg, kwargs in messages:
                    logger.log(level, msg, **kwargs)
            end_time = time.perf_counter()
            return end_time - start_time
        
        # Create mixed threads
        mixed_threads = []
        start_time = time.perf_counter()
        
        for i in range(10):
            is_async = i % 2 == 0
            thread = threading.Thread(target=mixed_worker, args=(i, is_async))
            mixed_threads.append(thread)
            thread.start()
        
        for thread in mixed_threads:
            thread.join()
        
        # End timing BEFORE cleanup to measure actual logging performance
        end_time = time.perf_counter()
        mixed_duration = end_time - start_time
        mixed_messages = 10 * 250
        mixed_messages_per_second = mixed_messages / mixed_duration
        
        # Close all mixed loggers after timing (cleanup doesn't affect performance measurement)
        # Note: Loggers are already tracked in _created_loggers and _logger_names
        for logger in self._created_loggers:
            try:
                if hasattr(logger, '_logger_name') and f"mixed_sync_" in str(logger):
                    self._flush_all_handlers(logger)
                    if hasattr(logger, 'close'):
                        logger.close()
            except Exception:
                pass
        
        mixed_per_thread = mixed_messages_per_second / 10
        print(f"   Mixed 10 threads: {mixed_messages_per_second:>8,.0f} msg/s (total aggregate, {mixed_per_thread:>6,.0f} msg/s per thread)")
        
        result = {
            'shared_logger_scalability': shared_results,
            'async_concurrent': async_result,
            'mixed_concurrent': {
                'messages_per_second': mixed_messages_per_second,
                'duration': mixed_duration,
                'num_threads': 10
            },
            'status': 'COMPLETED'
        }
        
        print("   Advanced Concurrent Logging: COMPLETED")
        return result
        
    async def test_ultra_high_performance(self) -> Dict[str, Any]:
        """
        Test high performance scenarios.
        
        Returns:
            Dict containing high performance metrics
        """
        print("\nTesting High Performance...")
        print("   Testing composite async logger...")
        
        import asyncio
        import time
        
        async def high_performance_test():
            # Use unique logger name to avoid cache conflicts
            logger_name = f"ultra_high_perf_{id(self)}"
            logger = getLogger(logger_name, logger_type="composite-async")
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)
            
            benchmark_instance = self
            
            total_messages = 100000
            batch_size = 10000
            
            # Warm-up
            print("   Warm-up period...")
            warmup_tasks = []
            for i in range(100):
                warmup_tasks.append(logger.log("INFO", f"Warm-up {i}"))
            await asyncio.gather(*warmup_tasks)
            
            # Wait for warm-up handlers
            await benchmark_instance._wait_for_async_handlers(logger, timeout=0.5)
            
            # Flush async handlers before timing
            await benchmark_instance._flush_all_handlers_async(logger)
            
            # Start timing after warm-up and flush
            start_time = time.perf_counter()
            
            # Track actual messages logged (not total_messages, which is just a target)
            actual_messages_logged = 0
            
            # Test bulk logging if available
            print("   Testing bulk logging performance...")
            remaining = total_messages
            try:
                if hasattr(logger, 'log_bulk'):
                    bulk_messages = [f"Bulk message {i}" for i in range(batch_size)]
                    await logger.log_bulk("INFO", bulk_messages)
                    actual_messages_logged += len(bulk_messages)
                    remaining = total_messages - batch_size
                else:
                    # Fallback: use batch logging
                    batch_messages = [("INFO", f"Bulk message {i}", {}) for i in range(batch_size)]
                    await logger.log_batch(batch_messages)
                    actual_messages_logged += len(batch_messages)
                    remaining = total_messages - batch_size
            except Exception as e:
                print(f"   Warning: Bulk logging not available: {e}, using batch instead")
                batch_size = 0
            
            # Test batch logging
            if remaining > 0:
                print("   Testing batch logging performance...")
                batch_messages = []
                batch_count = min(batch_size, remaining)
                for i in range(batch_count):
                    batch_messages.append(("INFO", f"Batch message {i}", {}))
                await logger.log_batch(batch_messages)
                actual_messages_logged += len(batch_messages)
                remaining -= batch_count
            
            # Test individual async logging
            if remaining > 0:
                individual_count = min(remaining, 10000)
                print(f"   Testing individual async logging performance ({individual_count} messages)...")
                tasks = []
                for i in range(individual_count):
                    tasks.append(logger.log("INFO", f"Individual message {i}"))
                await asyncio.gather(*tasks)
                actual_messages_logged += individual_count
            
            # End timing BEFORE close to measure actual logging performance (not cleanup)
            end_time = time.perf_counter()
            duration = end_time - start_time
            # Use actual messages logged, not total_messages (which is just a target)
            messages_per_second = actual_messages_logged / duration if duration > 0 else float('inf')
            
            # Close logger after timing (cleanup doesn't affect performance measurement)
            print("   Finalizing writes...")
            if hasattr(logger, 'close_async'):
                await logger.close_async()
            elif hasattr(logger, 'aclose'):
                await logger.aclose()
            else:
                # Fallback
                await benchmark_instance._flush_all_handlers_async(logger)
            
            return {
                'messages_per_second': messages_per_second,
                'duration': duration,
                'total_messages': actual_messages_logged,  # Report actual messages logged
                'status': 'COMPLETED'
            }
        
        # Run high performance test
        result = await high_performance_test()
        
        print(f"   High Performance: {result['messages_per_second']:>8,.0f} msg/s")
        print(f"   Total Messages: {result['total_messages']:,}")
        print(f"   Duration: {result['duration']:.3f}s")
        
        if result['messages_per_second'] >= 50000:
            print("   Performance target met: 50K+ msg/s")
        else:
            print("   Performance below 50K msg/s target")
        
        print("   High Performance: COMPLETED")
        return result
        
    def print_detailed_results(self):
        """Print comprehensive performance results."""
        print("\n" + "=" * 80)
        print("DETAILED PERFORMANCE RESULTS")
        print("=" * 80)
        
        # Individual logger performance
        print("\nINDIVIDUAL LOGGER PERFORMANCE")
        print("-" * 60)
        print(f"{'Logger Type':<25} | {'Messages/sec':<15} | {'Duration (s)':<12} | {'Status'}")
        print("-" * 60)
        
        individual_tests = [
            ('sync_logger', 'Sync Logger'),
            ('async_logger', 'Async Logger'),
            ('composite_logger', 'Composite Logger'),
            ('composite_async_logger', 'Composite Async Logger')
        ]
        
        for test_key, test_name in individual_tests:
            if test_key in self.results:
                result = self.results[test_key]
                print(f"{test_name:<25} | {result['individual_messages_per_second']:>13,.0f} | {result['individual_duration']:>10.3f} | {result['status']}")
        
        # Batch logging performance
        print("\nBATCH LOGGING PERFORMANCE")
        print("-" * 60)
        print(f"{'Logger Type':<25} | {'Messages/sec':<15} | {'Duration (s)':<12} | {'Batch Size'}")
        print("-" * 60)
        
        batch_tests = [
            ('composite_logger', 'Composite Logger'),
            ('composite_async_logger', 'Composite Async Logger')
        ]
        
        for test_key, test_name in batch_tests:
            if test_key in self.results and 'batch_messages_per_second' in self.results[test_key]:
                result = self.results[test_key]
                print(f"{test_name:<25} | {result['batch_messages_per_second']:>13,.0f} | {result['batch_duration']:>10.3f} | {result['batch_size']:,}")
        
        # Configuration performance
        if 'configurations' in self.results:
            print("\nCONFIGURATION PERFORMANCE")
            print("-" * 60)
            print(f"{'Configuration':<25} | {'Messages/sec':<15} | {'Duration (s)':<12} | {'Messages'}")
            print("-" * 60)
            
            for config_name, result in self.results['configurations'].items():
                print(f"{config_name.title():<25} | {result['messages_per_second']:>13,.0f} | {result['duration']:>10.3f} | {result['total_messages']:,}")
        
        # File writing performance
        if 'file_writing' in self.results and self.results['file_writing']['status'] == 'COMPLETED':
            print("\nFILE WRITING PERFORMANCE")
            print("-" * 60)
            file_result = self.results['file_writing']
            print(f"Sync File Writing:         {file_result['messages_per_second']:>8,.0f} msg/s")
            print(f"File I/O Speed:            {file_result['bytes_per_second']:>8,.0f} bytes/s")
            print(f"Total Bytes Written:       {file_result['bytes_written']:>8,} bytes")
            print(f"Duration:                   {file_result['duration']:>8.3f} s")
            print(f"Total Messages:             {file_result['total_messages']:>8,}")
        
        if 'async_file_writing' in self.results and self.results['async_file_writing']['status'] == 'COMPLETED':
            print("\nASYNC FILE WRITING PERFORMANCE")
            print("-" * 60)
            async_file_result = self.results['async_file_writing']
            print(f"Async File Writing:         {async_file_result['messages_per_second']:>8,.0f} msg/s")
            print(f"Async File I/O Speed:       {async_file_result['bytes_per_second']:>8,.0f} bytes/s")
            print(f"Total Bytes Written:       {async_file_result['bytes_written']:>8,} bytes")
            print(f"Duration:                   {async_file_result['duration']:>8.3f} s")
            print(f"Total Messages:             {async_file_result['total_messages']:>8,}")
        
        # Memory usage
        if 'memory' in self.results and self.results['memory']['status'] == 'COMPLETED':
            print("\nMEMORY USAGE ANALYSIS")
            print("-" * 60)
            memory = self.results['memory']
            print(f"Initial Memory:           {memory['initial_memory_mb']:>8.2f} MB")
            print(f"Final Memory:             {memory['final_memory_mb']:>8.2f} MB")
            print(f"Memory Increase:          {memory['memory_increase_mb']:>8.2f} MB")
            print(f"Loggers Created:          {memory['loggers_created']:>8d}")
            print(f"Memory per Logger:        {memory['memory_per_logger_mb']:>8.4f} MB")
        
        # Concurrent performance
        if 'concurrent' in self.results:
            print("\nCONCURRENT LOGGING PERFORMANCE")
            print("-" * 60)
            concurrent = self.results['concurrent']
            print(f"Total Throughput:         {concurrent['total_messages_per_second']:>8,.0f} msg/s (total aggregate)")
            print(f"Total Duration:           {concurrent['total_duration']:>8.3f} s")
            print(f"Number of Workers:        {concurrent['num_threads']:>8d}")
            print(f"Messages per Worker:      {concurrent['messages_per_thread']:>8d}")
            print(f"Total Messages:           {concurrent['total_messages']:>8d}")
            print(f"Average Worker Speed:     {concurrent['avg_thread_speed']:>8,.0f} msg/s (per worker, for reference)")
            print(f"Min Worker Speed:         {concurrent['min_thread_speed']:>8,.0f} msg/s")
            print(f"Max Worker Speed:         {concurrent['max_thread_speed']:>8,.0f} msg/s")
        
        # Performance summary
        print("\nPERFORMANCE SUMMARY")
        print("-" * 60)
        
        # Collect all performance metrics
        all_performance_data = []
        performance_threshold = 50000
        
        for test_key, result in self.results.items():
            if isinstance(result, dict):
                # Individual messages
                if 'individual_messages_per_second' in result:
                    all_performance_data.append({
                        'name': f"{result.get('logger_type', test_key)} (Individual)",
                        'speed': result['individual_messages_per_second'],
                        'type': 'individual',
                        'test_key': test_key
                    })
                # Batch messages
                if 'batch_messages_per_second' in result:
                    all_performance_data.append({
                        'name': f"{result.get('logger_type', test_key)} (Batch)",
                        'speed': result['batch_messages_per_second'],
                        'type': 'batch',
                        'test_key': test_key
                    })
                # Total throughput
                if 'total_messages_per_second' in result:
                    all_performance_data.append({
                        'name': f"{test_key.replace('_', ' ').title()} (Total)",
                        'speed': result['total_messages_per_second'],
                        'type': 'total',
                        'test_key': test_key
                    })
                # Configuration results
                if 'configurations' in test_key:
                    for config_name, config_result in result.items():
                        all_performance_data.append({
                            'name': f"Config: {config_name.title()}",
                            'speed': config_result['messages_per_second'],
                            'type': 'config',
                            'test_key': f"{test_key}.{config_name}"
                        })
                # Advanced concurrent results
                if 'advanced_concurrent' in test_key:
                    if 'shared_logger_scalability' in result:
                        for thread_count, thread_result in result['shared_logger_scalability'].items():
                            all_performance_data.append({
                                'name': f"Shared Logger ({thread_count} threads)",
                                'speed': thread_result['messages_per_second'],
                                'type': 'concurrent',
                                'test_key': f"{test_key}.shared.{thread_count}"
                            })
                    if 'async_concurrent' in result:
                        all_performance_data.append({
                            'name': f"Async Concurrent ({result['async_concurrent']['num_tasks']} tasks)",
                            'speed': result['async_concurrent']['messages_per_second'],
                            'type': 'async_concurrent',
                            'test_key': f"{test_key}.async"
                        })
                    if 'mixed_concurrent' in result:
                        all_performance_data.append({
                            'name': "Mixed Sync/Async Concurrent",
                            'speed': result['mixed_concurrent']['messages_per_second'],
                            'type': 'mixed',
                            'test_key': f"{test_key}.mixed"
                        })
                # High performance
                if 'ultra_high_performance' in test_key:
                    all_performance_data.append({
                        'name': "High Performance",
                        'speed': result['messages_per_second'],
                        'type': 'ultra',
                        'test_key': test_key
                    })
        
        if all_performance_data:
            all_speeds = [p['speed'] for p in all_performance_data]
            
            print(f"Fastest Performance:      {max(all_speeds):>8,.0f} msg/s")
            print(f"Slowest Performance:      {min(all_speeds):>8,.0f} msg/s")
            print(f"Average Performance:      {statistics.mean(all_speeds):>8,.0f} msg/s")
            print(f"Performance Range:        {max(all_speeds) - min(all_speeds):>8,.0f} msg/s")
            
            # Identify slow performers (under threshold)
            slow_performers = [p for p in all_performance_data if p['speed'] < performance_threshold]
            
            if slow_performers:
                print("\nLOGGERS BELOW 50K MSG/S THRESHOLD")
                print("-" * 60)
                print(f"{'Logger Name':<40} | {'Speed (msg/s)':<15} | {'Gap to 50K':<15} | {'Type'}")
                print("-" * 60)
                slow_performers.sort(key=lambda x: x['speed'])
                
                for perf in slow_performers:
                    gap = performance_threshold - perf['speed']
                    gap_pct = (gap / performance_threshold) * 100
                    print(f"{perf['name']:<40} | {perf['speed']:>13,.0f} | {gap:>13,.0f} ({gap_pct:.1f}%) | {perf['type']}")
                
                print(f"\nTotal slow performers: {len(slow_performers)} out of {len(all_performance_data)}")
                print(f"Average speed of slow performers: {statistics.mean([p['speed'] for p in slow_performers]):,.0f} msg/s")
            else:
                print("\nAll loggers meet the 50K msg/s threshold")
            
            # Show top performers
            print("\nTOP 5 PERFORMERS")
            print("-" * 60)
            print(f"{'Rank':<6} | {'Logger Name':<40} | {'Speed (msg/s)':<15} | {'Type'}")
            print("-" * 60)
            top_performers = sorted(all_performance_data, key=lambda x: x['speed'], reverse=True)[:5]
            for rank, perf in enumerate(top_performers, 1):
                print(f"{rank:<6} | {perf['name']:<40} | {perf['speed']:>13,.0f} | {perf['type']}")
    
    def save_results_to_file(self):
        """Save benchmark results to JSON file for later analysis.
        
        Creates timestamped files: benchmark_results/benchmark_YYYY-MM-DD_HH-MM-SS.json
        """
        try:
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = self.results_dir / f"benchmark_{timestamp}.json"
            
            # Prepare results for JSON serialization
            def make_serializable(obj):
                """Recursively convert objects to JSON-serializable format."""
                if isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                elif hasattr(obj, '__dict__'):
                    return str(obj)
                else:
                    return str(obj)
            
            json_results = make_serializable(self.results)
            
            # Add metadata
            output = {
                'metadata': {
                    'timestamp': timestamp,
                    'test_config': self.test_config,
                    'python_version': sys.version.split()[0],
                    'platform': sys.platform
                },
                'results': json_results
            }
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            
            print(f"\nResults saved to: {filename}")
            print(f"   You can review results later or compare with previous runs")
            
            # Also create a "latest" copy for easy access
            latest_file = self.results_dir / "benchmark_latest.json"
            try:
                import shutil
                shutil.copy2(filename, latest_file)
            except Exception:
                pass
                
        except Exception as e:
            print(f"\nWarning: Could not save results to file: {e}")
            print(f"   Results are still available in console output above")
        
    async def run_benchmark(self):
        """Run the complete benchmark suite."""
        self.print_header()
        
        try:
            # Run all performance tests
            # Cleanup between tests ensures each test starts with a clean state
            self.results['sync_logger'] = self.test_sync_logger_performance()
            self._cleanup_logger_cache()  # Cleanup after each test
            
            self.results['async_logger'] = await self.test_async_logger_performance()
            self._cleanup_logger_cache()
            
            self.results['composite_logger'] = self.test_composite_logger_performance()
            self._cleanup_logger_cache()
            
            self.results['composite_async_logger'] = await self.test_composite_async_logger_performance()
            self._cleanup_logger_cache()
            
            self.results['configurations'] = self.test_configuration_performance()
            self._cleanup_logger_cache()
            
            self.results['file_writing'] = self.test_file_writing_performance()
            self._cleanup_logger_cache()
            
            self.results['async_file_writing'] = await self.test_async_file_writing_performance()
            self._cleanup_logger_cache()
            
            self.results['memory'] = self.test_memory_usage()
            self._cleanup_logger_cache()
            
            self.results['concurrent'] = await self.test_concurrent_logging()
            self._cleanup_logger_cache()
            
            self.results['advanced_concurrent'] = await self.test_advanced_concurrent_logging()
            self._cleanup_logger_cache()
            
            self.results['ultra_high_performance'] = await self.test_ultra_high_performance()
            self._cleanup_logger_cache()
            
            # Print detailed results
            self.print_detailed_results()
            
            # Save results to JSON file
            if self.save_results:
                self.save_results_to_file()
            
            print("\nBenchmark completed successfully")
            
            # Final cleanup: ensure all async handlers are properly closed
            await self._final_cleanup()
            
            return 0
            
        except Exception as e:
            print(f"\nError during benchmark: {e}")
            import traceback
            traceback.print_exc()
            # Still try to cleanup even on error
            try:
                await self._final_cleanup()
            except Exception:
                pass
            return 1


async def main():
    """Main entry point for the benchmark suite."""
    benchmark = HydraLoggerBenchmark()
    return await benchmark.run_benchmark()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
