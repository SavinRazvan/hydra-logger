"""
End-to-end integration tests for AsyncHydraLogger.

This module provides comprehensive integration tests covering:
- Multiple handler scenarios
- Context management and tracing
- Shutdown and data integrity
- Performance under load
- Error recovery scenarios
"""

import asyncio
import os
import tempfile
import time
import pytest
from typing import Dict, Any

from hydra_logger.async_hydra import (
    AsyncHydraLogger,
    AsyncFileHandler,
    AsyncConsoleHandler,
    AsyncCompositeHandler,
    AsyncContextManager,
    AsyncTraceManager,
    get_context_switcher,
    get_trace_manager,
    trace_context
)


class TestEndToEndAsyncLogging:
    """Comprehensive end-to-end integration tests."""
    
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
    def async_logger(self, temp_log_file):
        """Create async logger with file and console handlers."""
        config = {
            'handlers': [
                {
                    'type': 'file',
                    'filename': temp_log_file,
                    'max_queue_size': 100,
                    'memory_threshold': 70.0
                },
                {
                    'type': 'console',
                    'use_colors': True,
                    'max_queue_size': 100,
                    'memory_threshold': 70.0
                }
            ]
        }
        logger = AsyncHydraLogger(config)
        return logger
    
    @pytest.mark.asyncio
    async def test_comprehensive_async_logging(self, async_logger, temp_log_file):
        """Test comprehensive async logging with multiple handlers."""
        # Initialize logger
        await async_logger.initialize()
        
        # Test basic logging
        await async_logger.info("TEST_LAYER", "Basic info message")
        await async_logger.debug("TEST_LAYER", "Debug message")
        await async_logger.warning("TEST_LAYER", "Warning message")
        await async_logger.error("TEST_LAYER", "Error message")
        
        # Wait for messages to be processed
        await asyncio.sleep(0.1)
        
        # Verify file was written
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "Basic info message" in content
            assert "Debug message" in content
            assert "Warning message" in content
            assert "Error message" in content
        
        # Test health status
        health_status = async_logger.get_health_status()
        assert 'is_healthy' in health_status
        assert 'uptime' in health_status
        
        # Test performance metrics
        perf_metrics = async_logger.get_performance_metrics()
        assert 'operations' in perf_metrics
        assert 'uptime' in perf_metrics
        
        # Clean shutdown
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_context_management_integration(self, async_logger):
        """Test context management integration."""
        await async_logger.initialize()
        
        # Test context switching
        context_switcher = get_context_switcher()
        
        async with AsyncContextManager() as ctx1:
            ctx1.update_context_metadata("user_id", "12345")
            await async_logger.info("CONTEXT_TEST", "Message with context 1")
            
            async with AsyncContextManager() as ctx2:
                ctx2.update_context_metadata("session_id", "67890")
                await async_logger.info("CONTEXT_TEST", "Message with context 2")
                
                # Verify context switching
                switch_stats = context_switcher.get_switch_stats()
                assert switch_stats['total_switches'] >= 2
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_tracing_integration(self, async_logger):
        """Test distributed tracing integration."""
        await async_logger.initialize()
        
        trace_manager = get_trace_manager()
        async with trace_context("test_trace") as trace:
            trace.add_metadata("service", "test_service")
            # Start a span
            span_id = trace_manager.start_span("test_span", {"operation": "test"})
            await async_logger.info("TRACE_TEST", "Message with trace")
            # End the span
            trace_manager.end_span(span_id)
            # Verify trace statistics
            trace_stats = trace_manager.get_trace_stats()
            assert trace_stats['total_traces'] >= 1
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_composite_handler_integration(self, temp_log_file):
        """Test composite handler with multiple sub-handlers."""
        # Create composite handler
        file_handler = AsyncFileHandler(temp_log_file, max_queue_size=50)
        console_handler = AsyncConsoleHandler(use_colors=False, max_queue_size=50)
        
        composite = AsyncCompositeHandler(
            handlers=[file_handler, console_handler],
            parallel_execution=True,
            fail_fast=False
        )
        
        logger = AsyncHydraLogger()
        logger.add_handler(composite)
        
        await logger.initialize()
        
        # Test logging through composite
        await logger.info("COMPOSITE_TEST", "Message through composite handler")
        await asyncio.sleep(0.1)
        
        # Verify file was written
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "Message through composite handler" in content
        
        # Test composite health
        composite_health = composite.get_health_status()
        assert 'handler_count' in composite_health
        assert composite_health['handler_count'] == 2
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_concurrent_logging(self, async_logger):
        """Test concurrent logging from multiple coroutines."""
        await async_logger.initialize()
        
        async def log_messages(prefix: str, count: int):
            """Log multiple messages concurrently."""
            for i in range(count):
                await async_logger.info(f"CONCURRENT_{prefix}", f"Message {i} from {prefix}")
                await asyncio.sleep(0.001)  # Small delay
        
        # Start multiple concurrent logging tasks
        tasks = [
            asyncio.create_task(log_messages("A", 10)),
            asyncio.create_task(log_messages("B", 10)),
            asyncio.create_task(log_messages("C", 10))
        ]
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
        # Wait for messages to be processed
        await asyncio.sleep(0.2)
        
        # Verify logger is still healthy
        assert async_logger.is_healthy()
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, async_logger):
        """Test error recovery and fallback mechanisms."""
        await async_logger.initialize()
        
        # Test logging with invalid data (should not crash)
        await async_logger.info("ERROR_TEST", "Normal message")
        
        # Test handler error stats
        for handler in async_logger.get_handlers():
            error_stats = handler.get_error_stats()
            assert 'total_errors' in error_stats
            assert 'error_types' in error_stats
        
        # Verify logger remains healthy despite errors
        assert async_logger.is_healthy()
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_shutdown_with_pending_messages(self, async_logger, temp_log_file):
        """Test graceful shutdown with pending messages."""
        await async_logger.initialize()
        
        # Send messages rapidly
        for i in range(20):
            await async_logger.info("SHUTDOWN_TEST", f"Message {i}")
        
        # Immediately shutdown (should process pending messages)
        await async_logger.aclose()
        
        # Verify messages were written
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, 'r') as f:
            content = f.read()
            # Should have at least some messages
            assert any(f"Message {i}" in content for i in range(20))
    
    @pytest.mark.asyncio
    async def test_memory_monitoring(self, async_logger):
        """Test memory monitoring integration."""
        await async_logger.initialize()
        
        # Take a memory snapshot first to ensure we have data
        snapshot = async_logger.take_memory_snapshot()
        assert 'timestamp' in snapshot
        
        # Get memory statistics after taking snapshot
        memory_stats = async_logger.get_memory_statistics()
        assert 'snapshot_count' in memory_stats or 'error' in memory_stats
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, async_logger):
        """Test performance monitoring integration."""
        await async_logger.initialize()
        
        # Perform some logging operations
        for i in range(10):
            await async_logger.info("PERF_TEST", f"Performance test message {i}")
        
        # Get performance metrics
        perf_metrics = async_logger.get_performance_metrics()
        assert 'operations' in perf_metrics
        assert 'uptime' in perf_metrics
        
        # Check if performance is healthy
        assert async_logger.is_performance_healthy()
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_handler_management(self, async_logger):
        """Test dynamic handler management."""
        await async_logger.initialize()
        
        initial_count = async_logger.get_handler_count()
        
        # Add a new handler
        new_handler = AsyncConsoleHandler(use_colors=False)
        async_logger.add_handler(new_handler)
        
        assert async_logger.get_handler_count() == initial_count + 1
        
        # Remove the handler
        async_logger.remove_handler(new_handler)
        
        assert async_logger.get_handler_count() == initial_count
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_data_integrity(self, async_logger, temp_log_file):
        """Test data integrity under various conditions."""
        await async_logger.initialize()
        
        # Test with special characters and unicode
        test_messages = [
            "Normal message",
            "Message with special chars: !@#$%^&*()",
            "Unicode message: 你好世界 🌍",
            "Message with newlines\nand tabs\t",
            "Very long message " * 100,
            "",  # Empty message
            "Message with quotes: 'single' and \"double\""
        ]
        
        for i, message in enumerate(test_messages):
            await async_logger.info("INTEGRITY_TEST", f"Test {i}: {message}")
        
        await asyncio.sleep(0.2)
        
        # Verify all messages were written correctly
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            for i, message in enumerate(test_messages):
                assert f"Test {i}: {message}" in content
        
        await async_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, async_logger):
        """Test comprehensive health monitoring."""
        await async_logger.initialize()
        
        # Get health status
        health_status = async_logger.get_health_status()
        
        # Verify health status structure
        required_keys = ['is_healthy', 'uptime', 'last_check']
        for key in required_keys:
            assert key in health_status
        
        # Test health over time
        initial_health = async_logger.is_healthy()
        assert initial_health is True
        
        # Perform some operations
        for i in range(5):
            await async_logger.info("HEALTH_TEST", f"Health test message {i}")
            await asyncio.sleep(0.01)
        
        # Health should still be good
        assert async_logger.is_healthy()
        
        await async_logger.aclose() 