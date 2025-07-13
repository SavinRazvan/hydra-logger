"""
Performance and stress tests for AsyncHydraLogger.

This module provides comprehensive performance and stress tests including:
- High-throughput logging scenarios
- Memory pressure tests
- Concurrent access patterns
- Performance benchmarking
- Stress testing under load
"""

import asyncio
import time
import tempfile
import os
import pytest
import statistics
from typing import List, Dict, Any

from hydra_logger.async_hydra import (
    AsyncHydraLogger,
    AsyncFileHandler,
    AsyncConsoleHandler,
    AsyncCompositeHandler
)


class TestPerformanceAndStress:
    """Performance and stress tests for async logging."""
    
    @pytest.fixture
    def temp_log_file(self):
        """Create temporary log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            temp_file = f.name
        yield temp_file
        # Cleanup
        try:
            os.unlink(temp_file)
        except OSError:
            pass
    
    @pytest.fixture
    def high_perf_logger(self, temp_log_file):
        """Create high-performance logger configuration."""
        config = {
            'handlers': [
                {
                    'type': 'file',
                    'filename': temp_log_file,
                    'max_queue_size': 10000,
                    'memory_threshold': 80.0
                },
                {
                    'type': 'console',
                    'use_colors': False,  # Disable colors for performance
                    'max_queue_size': 10000,
                    'memory_threshold': 80.0
                }
            ]
        }
        logger = AsyncHydraLogger(config)
        return logger
    
    @pytest.mark.asyncio
    async def test_high_throughput_logging(self, high_perf_logger):
        """Test high-throughput logging performance."""
        await high_perf_logger.initialize()
        
        message_count = 1000
        start_time = time.time()
        
        # Log messages rapidly
        for i in range(message_count):
            await high_perf_logger.info("PERF_TEST", f"High throughput message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Calculate throughput
        messages_per_second = message_count / duration
        
        print(f"High throughput test: {message_count} messages in {duration:.3f}s")
        print(f"Throughput: {messages_per_second:.1f} messages/second")
        
        # Performance assertions
        assert messages_per_second > 100, f"Throughput too low: {messages_per_second} msg/s"
        assert duration < 10, f"Test took too long: {duration}s"
        
        # Verify logger remains healthy
        assert high_perf_logger.is_healthy()
        assert high_perf_logger.is_performance_healthy()
        
        await high_perf_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_concurrent_high_throughput(self, high_perf_logger):
        """Test high-throughput logging with concurrent access."""
        await high_perf_logger.initialize()
        
        async def log_batch(batch_id: int, count: int):
            """Log a batch of messages."""
            for i in range(count):
                await high_perf_logger.info(f"BATCH_{batch_id}", f"Concurrent message {i} from batch {batch_id}")
                await asyncio.sleep(0.001)  # Small delay to simulate real usage
        
        # Start multiple concurrent logging tasks
        batch_size = 100
        num_batches = 5
        tasks = []
        
        start_time = time.time()
        
        for batch_id in range(num_batches):
            task = asyncio.create_task(log_batch(batch_id, batch_size))
            tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        total_messages = batch_size * num_batches
        
        messages_per_second = total_messages / duration
        
        print(f"Concurrent throughput test: {total_messages} messages in {duration:.3f}s")
        print(f"Concurrent throughput: {messages_per_second:.1f} messages/second")
        
        # Performance assertions
        assert messages_per_second > 50, f"Concurrent throughput too low: {messages_per_second} msg/s"
        assert duration < 15, f"Concurrent test took too long: {duration}s"
        
        # Verify logger remains healthy
        assert high_perf_logger.is_healthy()
        
        await high_perf_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_memory_pressure_test(self, high_perf_logger):
        """Test logging under memory pressure."""
        await high_perf_logger.initialize()
        
        # Take initial memory snapshot
        initial_snapshot = high_perf_logger.take_memory_snapshot()
        
        # Log many messages to create memory pressure
        message_count = 5000
        start_time = time.time()
        
        for i in range(message_count):
            await high_perf_logger.info("MEMORY_TEST", f"Memory pressure message {i} " * 10)
            
            # Check memory every 100 messages
            if i % 100 == 0:
                memory_stats = high_perf_logger.get_memory_statistics()
                if 'recent_system_memory' in memory_stats:
                    memory_percent = memory_stats['recent_system_memory']['average_percent']
                    if memory_percent > 90:
                        print(f"High memory usage detected: {memory_percent:.1f}%")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Take final memory snapshot
        final_snapshot = high_perf_logger.take_memory_snapshot()
        
        print(f"Memory pressure test: {message_count} messages in {duration:.3f}s")
        
        # Verify logger handles memory pressure gracefully
        assert high_perf_logger.is_healthy()
        
        # Check for memory leaks (process memory shouldn't grow excessively)
        if 'process_memory' in initial_snapshot and 'process_memory' in final_snapshot:
            initial_rss = initial_snapshot['process_memory']['rss_mb']
            final_rss = final_snapshot['process_memory']['rss_mb']
            memory_growth = final_rss - initial_rss
            
            print(f"Memory growth: {memory_growth:.1f} MB")
            # Memory growth should be reasonable (less than 100MB for this test)
            assert memory_growth < 100, f"Excessive memory growth: {memory_growth} MB"
        
        await high_perf_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_queue_backpressure(self, temp_log_file):
        """Test queue backpressure handling."""
        # Create logger with small queue to trigger backpressure
        config = {
            'handlers': [
                {
                    'type': 'file',
                    'filename': temp_log_file,
                    'max_queue_size': 10,  # Very small queue
                    'memory_threshold': 70.0
                }
            ]
        }
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Send messages rapidly to fill queue
        start_time = time.time()
        
        for i in range(100):
            await logger.info("BACKPRESSURE_TEST", f"Backpressure message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Backpressure test: 100 messages in {duration:.3f}s")
        
        # Verify logger handles backpressure gracefully
        assert logger.is_healthy()
        
        # Check queue statistics
        for handler in logger.get_handlers():
            if hasattr(handler, '_queue'):
                queue_stats = handler._queue.get_stats()
                print(f"Queue stats: {queue_stats}")
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self, high_perf_logger):
        """Comprehensive performance benchmark."""
        await high_perf_logger.initialize()
        
        # Benchmark different operations
        benchmarks = {}
        
        # Single message latency
        start_time = time.time()
        await high_perf_logger.info("BENCHMARK", "Single message")
        single_latency = time.time() - start_time
        benchmarks['single_message_latency'] = single_latency
        
        # Batch latency
        batch_size = 100
        start_time = time.time()
        for i in range(batch_size):
            await high_perf_logger.info("BENCHMARK", f"Batch message {i}")
        batch_duration = time.time() - start_time
        benchmarks['batch_latency'] = batch_duration
        benchmarks['batch_throughput'] = batch_size / batch_duration
        
        # Concurrent throughput
        async def concurrent_batch(batch_id: int):
            for i in range(50):
                await high_perf_logger.info("BENCHMARK", f"Concurrent {batch_id}-{i}")
        
        start_time = time.time()
        tasks = [asyncio.create_task(concurrent_batch(i)) for i in range(4)]
        await asyncio.gather(*tasks)
        concurrent_duration = time.time() - start_time
        benchmarks['concurrent_throughput'] = 200 / concurrent_duration
        
        # Print benchmark results
        print("Performance Benchmark Results:")
        for metric, value in benchmarks.items():
            print(f"  {metric}: {value:.6f}")
        
        # Performance assertions
        assert benchmarks['single_message_latency'] < 0.1, "Single message latency too high"
        assert benchmarks['batch_throughput'] > 50, "Batch throughput too low"
        assert benchmarks['concurrent_throughput'] > 100, "Concurrent throughput too low"
        
        await high_perf_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_stress_test_long_running(self, high_perf_logger):
        """Long-running stress test."""
        await high_perf_logger.initialize()
        
        # Run for a longer period to detect issues
        test_duration = 5  # seconds
        start_time = time.time()
        message_count = 0
        
        try:
            while time.time() - start_time < test_duration:
                await high_perf_logger.info("STRESS_TEST", f"Long running stress message {message_count}")
                message_count += 1
                
                # Check health periodically
                if message_count % 100 == 0:
                    assert high_perf_logger.is_healthy(), "Logger became unhealthy during stress test"
                    
                    # Check performance
                    perf_metrics = high_perf_logger.get_performance_metrics()
                    if 'operations' in perf_metrics:
                        log_ops = perf_metrics['operations'].get('log_operation', {})
                        if 'count' in log_ops and log_ops['count'] > 0:
                            avg_time = log_ops.get('average_time', 0)
                            assert avg_time < 0.1, f"Average log time too high: {avg_time}s"
                
                await asyncio.sleep(0.001)  # Small delay
                
        except Exception as e:
            print(f"Stress test failed after {message_count} messages: {e}")
            raise
        
        end_time = time.time()
        actual_duration = end_time - start_time
        messages_per_second = message_count / actual_duration
        
        print(f"Stress test: {message_count} messages in {actual_duration:.3f}s")
        print(f"Stress test throughput: {messages_per_second:.1f} messages/second")
        
        # Verify logger remains healthy after stress test
        assert high_perf_logger.is_healthy()
        assert high_perf_logger.is_performance_healthy()
        
        await high_perf_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, high_perf_logger):
        """Test for memory leaks during extended operation."""
        await high_perf_logger.initialize()
        
        # Take initial memory snapshot
        initial_snapshot = high_perf_logger.take_memory_snapshot()
        
        # Perform multiple cycles of logging
        cycles = 5
        messages_per_cycle = 200
        
        for cycle in range(cycles):
            print(f"Memory leak test cycle {cycle + 1}/{cycles}")
            
            # Log messages
            for i in range(messages_per_cycle):
                await high_perf_logger.info("MEMORY_LEAK_TEST", f"Cycle {cycle} message {i}")
            
            # Take memory snapshot
            cycle_snapshot = high_perf_logger.take_memory_snapshot()
            
            # Check for excessive memory growth
            if 'process_memory' in initial_snapshot and 'process_memory' in cycle_snapshot:
                initial_rss = initial_snapshot['process_memory']['rss_mb']
                cycle_rss = cycle_snapshot['process_memory']['rss_mb']
                memory_growth = cycle_rss - initial_rss
                
                print(f"Cycle {cycle + 1} memory growth: {memory_growth:.1f} MB")
                
                # Memory growth should be reasonable
                assert memory_growth < 50, f"Excessive memory growth in cycle {cycle + 1}: {memory_growth} MB"
            
            # Verify logger remains healthy
            assert high_perf_logger.is_healthy()
        
        # Final memory check
        final_snapshot = high_perf_logger.take_memory_snapshot()
        
        if 'process_memory' in initial_snapshot and 'process_memory' in final_snapshot:
            initial_rss = initial_snapshot['process_memory']['rss_mb']
            final_rss = final_snapshot['process_memory']['rss_mb']
            total_growth = final_rss - initial_rss
            
            print(f"Total memory growth: {total_growth:.1f} MB")
            assert total_growth < 100, f"Total memory growth too high: {total_growth} MB"
        
        await high_perf_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_composite_handler_performance(self, temp_log_file):
        """Test performance of composite handler with multiple sub-handlers."""
        # Create composite handler with multiple file handlers
        handlers = []
        for i in range(3):
            handler = AsyncFileHandler(f"{temp_log_file}.{i}", max_queue_size=1000)
            handlers.append(handler)
        
        composite = AsyncCompositeHandler(
            handlers=handlers,
            parallel_execution=True,
            fail_fast=False
        )
        
        logger = AsyncHydraLogger()
        logger.add_handler(composite)
        
        await logger.initialize()
        
        # Performance test with composite handler
        message_count = 500
        start_time = time.time()
        
        for i in range(message_count):
            await logger.info("COMPOSITE_PERF", f"Composite performance message {i}")
        
        end_time = time.time()
        duration = end_time - start_time
        throughput = message_count / duration
        
        print(f"Composite handler test: {message_count} messages in {duration:.3f}s")
        print(f"Composite throughput: {throughput:.1f} messages/second")
        
        # Performance assertions
        assert throughput > 50, f"Composite handler throughput too low: {throughput} msg/s"
        assert duration < 10, f"Composite handler test took too long: {duration}s"
        
        # Verify all files were written
        for i in range(3):
            file_path = f"{temp_log_file}.{i}"
            assert os.path.exists(file_path), f"File {file_path} was not created"
        
        await logger.aclose()
        
        # Cleanup
        for i in range(3):
            try:
                os.unlink(f"{temp_log_file}.{i}")
            except OSError:
                pass 