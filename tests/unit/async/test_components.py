"""
Phase 3 components test suite.

This module tests the advanced async components including:
- Async logger basic functionality
- Async handlers
- Performance monitoring
"""

import asyncio
import logging
import pytest
import tempfile
import os
import shutil
import time
from pathlib import Path

from hydra_logger.async_hydra import (
    AsyncHydraLogger,
    AsyncFileHandler,
    AsyncConsoleHandler,
    get_performance_monitor,
    async_timer
)


class TestAsyncLoggerBasic:
    """Test suite for basic async logger functionality."""
    
    @pytest.fixture
    def test_logs_dir(self):
        """Create temporary test logs directory."""
        test_dir = tempfile.mkdtemp(prefix="hydra_test_")
        yield test_dir
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_async_logger_creation(self):
        """Test async logger creation and basic functionality."""
        logger = AsyncHydraLogger()
        assert logger is not None
        
        # Initialize logger
        await logger.initialize()
        
        # Test basic logging
        await logger.info("TEST", "Async logger test message")
        
        # Cleanup
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_async_logger_with_file_handler(self, test_logs_dir):
        """Test async logger with file handler."""
        test_log_file = os.path.join(test_logs_dir, "test_async.log")
        
        logger = AsyncHydraLogger()
        await logger.initialize()
        
        # Add file handler
        file_handler = AsyncFileHandler(test_log_file)
        await file_handler.initialize()
        logger.add_handler(file_handler)
        
        # Test logging
        await logger.info("TEST", "File handler test message")
        
        # Wait for async operations to complete
        await asyncio.sleep(0.1)
        
        # Check if file was created
        assert os.path.exists(test_log_file)
        
        # Cleanup
        await file_handler.aclose()
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_async_logger_with_console_handler(self):
        """Test async logger with console handler."""
        logger = AsyncHydraLogger()
        await logger.initialize()
        
        # Add console handler
        console_handler = AsyncConsoleHandler()
        await console_handler.initialize()
        logger.add_handler(console_handler)
        
        # Test logging
        await logger.info("TEST", "Console handler test message")
        
        # Wait for async operations to complete
        await asyncio.sleep(0.1)
        
        # Cleanup
        await console_handler.aclose()
        await logger.aclose()


class TestAsyncHandlers:
    """Test suite for async handlers."""
    
    @pytest.fixture
    def test_logs_dir(self):
        """Create temporary test logs directory."""
        test_dir = tempfile.mkdtemp(prefix="hydra_test_")
        yield test_dir
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_async_file_handler(self, test_logs_dir):
        """Test async file handler."""
        test_log_file = os.path.join(test_logs_dir, "test_file_handler.log")
        handler = AsyncFileHandler(test_log_file)
        
        try:
            await handler.initialize()
            
            # Create test record
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg='File handler test',
                args=(),
                exc_info=None
            )
            
            # Test emit
            await handler.emit_async(record)
            
            # Wait for async operations to complete
            await asyncio.sleep(0.1)
            
            # Check if file was created
            assert os.path.exists(test_log_file)
            
        finally:
            await handler.aclose()
    
    @pytest.mark.asyncio
    async def test_async_console_handler(self):
        """Test async console handler."""
        handler = AsyncConsoleHandler()
        
        try:
            await handler.initialize()
            
            # Create test record
            record = logging.LogRecord(
                name='test',
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg='Console handler test',
                args=(),
                exc_info=None
            )
            
            # Test emit
            await handler.emit_async(record)
            
            # Wait for async operations to complete
            await asyncio.sleep(0.1)
            
        finally:
            await handler.aclose()


class TestPerformanceMonitoring:
    """Test suite for performance monitoring."""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create a performance monitor for testing."""
        return get_performance_monitor()
    
    def test_performance_monitor_creation(self, performance_monitor):
        """Test performance monitor creation."""
        assert performance_monitor is not None
        
        # Test initial statistics
        stats = performance_monitor.get_async_statistics()
        assert 'uptime' in stats
        assert 'operations' in stats
        assert 'counters' in stats
    
    def test_performance_timing(self, performance_monitor):
        """Test performance timing functionality."""
        # Test manual timing
        start_time = performance_monitor.start_async_processing_timer('test_operation')
        time.sleep(0.1)  # Simulate work
        duration = performance_monitor.end_async_processing_timer('test_operation', start_time)
        
        assert duration > 0
        assert duration >= 0.1
        
        # Check statistics
        stats = performance_monitor.get_async_statistics()
        assert 'test_operation' in stats['operations']
        assert stats['operations']['test_operation']['count'] == 1
    
    @pytest.mark.asyncio
    async def test_performance_context_manager(self, performance_monitor):
        """Test performance context manager."""
        async with performance_monitor.async_timer('context_test') as start_time:
            await asyncio.sleep(0.1)  # Simulate async work
        
        # Check statistics
        stats = performance_monitor.get_async_statistics()
        assert 'context_test' in stats['operations']
    
    def test_memory_snapshot(self, performance_monitor):
        """Test memory snapshot functionality."""
        snapshot = performance_monitor.take_memory_snapshot()
        assert 'timestamp' in snapshot
        
        # Test memory statistics
        memory_stats = performance_monitor.get_memory_statistics()
        assert 'snapshot_count' in memory_stats
    
    def test_performance_decorator(self):
        """Test performance decorator."""
        @async_timer('decorator_test')
        async def test_function():
            await asyncio.sleep(0.1)
            return "test_result"
        
        # Test the decorated function
        result = asyncio.run(test_function())
        assert result == "test_result"
        
        # Check statistics
        monitor = get_performance_monitor()
        stats = monitor.get_async_statistics()
        assert 'decorator_test' in stats['operations']


class TestAsyncIntegration:
    """Test suite for async integration."""
    
    @pytest.fixture
    def test_logs_dir(self):
        """Create temporary test logs directory."""
        test_dir = tempfile.mkdtemp(prefix="hydra_test_")
        yield test_dir
        # Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_async_logger_integration(self, test_logs_dir):
        """Test async logger integration."""
        test_log_file = os.path.join(test_logs_dir, "test_integration.log")
        
        logger = AsyncHydraLogger()
        await logger.initialize()
        
        # Test basic logging
        await logger.info("TEST", "Integration test message")
        
        # Test health status
        health = logger.get_health_status()
        assert 'is_healthy' in health
        
        # Test performance metrics
        metrics = logger.get_performance_metrics()
        assert 'uptime' in metrics
        
        # Cleanup
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_async_logger_performance_monitoring(self, test_logs_dir):
        """Test async logger performance monitoring integration."""
        test_log_file = os.path.join(test_logs_dir, "test_performance.log")
        
        logger = AsyncHydraLogger()
        await logger.initialize()
        
        # Test performance monitoring
        metrics = logger.get_performance_metrics()
        assert 'uptime' in metrics
        
        # Take a memory snapshot first to ensure we have data
        snapshot = logger.take_memory_snapshot()
        assert 'timestamp' in snapshot
        
        # Test memory statistics after taking snapshot
        memory_stats = logger.get_memory_statistics()
        # Handle both cases: when snapshots are available and when psutil is not available
        assert 'snapshot_count' in memory_stats or 'error' in memory_stats
        
        # Test health checks
        assert logger.is_healthy() is True
        assert logger.is_performance_healthy() is True
        
        # Cleanup
        await logger.aclose()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 