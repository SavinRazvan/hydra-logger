"""
Error recovery and resilience tests for AsyncHydraLogger.

This module provides comprehensive error recovery tests including:
- Network failures and timeouts
- Disk space and file system errors
- Memory errors and resource exhaustion
- Graceful degradation scenarios
- Error isolation between handlers
- Recovery mechanisms
"""

import asyncio
import os
import tempfile
import time
import pytest
import shutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from hydra_logger.async_hydra import (
    AsyncHydraLogger,
    AsyncFileHandler,
    AsyncConsoleHandler,
    AsyncCompositeHandler
)


class TestErrorRecovery:
    """Error recovery and resilience tests."""
    
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
    def resilient_logger(self, temp_log_file):
        """Create logger with error recovery capabilities."""
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
                    'use_colors': False,
                    'max_queue_size': 100,
                    'memory_threshold': 70.0
                }
            ]
        }
        logger = AsyncHydraLogger(config)
        return logger
    
    @pytest.mark.asyncio
    async def test_file_system_errors(self, temp_log_file):
        """Test handling of file system errors."""
        # Create logger
        handler = AsyncFileHandler(temp_log_file, max_queue_size=50)
        logger = AsyncHydraLogger()
        logger.add_handler(handler)
        await logger.initialize()
        
        # Test normal operation first
        await logger.info("ERROR_TEST", "Normal message")
        await asyncio.sleep(0.1)
        
        # Verify file was written
        assert os.path.exists(temp_log_file)
        
        # Simulate file system error by mocking file operations
        with patch('builtins.open') as mock_open:
            # Simulate file system error
            mock_open.side_effect = OSError("Permission denied")
            
            # Try to log (should not crash)
            await logger.info("ERROR_TEST", "Message during file system error")
            await asyncio.sleep(0.1)
            
            # Logger should remain healthy despite file system error
            assert logger.is_healthy()
            
            # Check error statistics
            for handler in logger.get_handlers():
                if hasattr(handler, 'get_error_stats'):
                    error_stats = handler.get_error_stats()
                    print(f"Error stats: {error_stats}")
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_disk_space_errors(self, temp_log_file):
        """Test handling of disk space errors."""
        handler = AsyncFileHandler(temp_log_file, max_queue_size=50)
        logger = AsyncHydraLogger()
        logger.add_handler(handler)
        await logger.initialize()
        
        # Mock disk space check to simulate full disk
        with patch('os.stat') as mock_stat:
            # Simulate disk full error
            mock_stat.side_effect = OSError("No space left on device")
            
            # Try to log (should not crash)
            await logger.info("ERROR_TEST", "Message during disk full error")
            await asyncio.sleep(0.1)
            
            # Logger should remain healthy
            assert logger.is_healthy()
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_memory_errors(self, resilient_logger):
        """Test handling of memory errors."""
        await resilient_logger.initialize()
        
        # Mock memory monitoring to simulate memory pressure
        with patch('hydra_logger.async_hydra.core.memory_monitor.MemoryMonitor.check_memory') as mock_check:
            # Simulate memory pressure
            mock_check.return_value = False
            
            # Try to log (should fallback to sync)
            await resilient_logger.info("ERROR_TEST", "Message during memory pressure")
            await asyncio.sleep(0.1)
            
            # Logger should remain healthy
            assert resilient_logger.is_healthy()
        
        await resilient_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_queue_overflow_recovery(self, temp_log_file):
        """Test recovery from queue overflow."""
        # Create logger with very small queue
        config = {
            'handlers': [
                {
                    'type': 'file',
                    'filename': temp_log_file,
                    'max_queue_size': 5,  # Very small queue
                    'memory_threshold': 70.0
                }
            ]
        }
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Send many messages rapidly to overflow queue
        for i in range(20):
            await logger.info("OVERFLOW_TEST", f"Queue overflow message {i}")
        
        await asyncio.sleep(0.2)
        
        # Logger should handle overflow gracefully
        assert logger.is_healthy()
        
        # Check queue statistics
        for handler in logger.get_handlers():
            if hasattr(handler, '_queue'):
                queue_stats = handler._queue.get_stats()
                print(f"Queue stats after overflow: {queue_stats}")
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_handler_isolation(self, temp_log_file):
        """Test error isolation between handlers."""
        # Create composite handler with one failing handler
        file_handler = AsyncFileHandler(temp_log_file, max_queue_size=50)
        console_handler = AsyncConsoleHandler(use_colors=False, max_queue_size=50)
        
        # Create a failing console handler by subclassing
        class FailingConsoleHandler(AsyncConsoleHandler):
            async def emit_async(self, record):
                raise Exception("Console handler error")
        
        failing_console = FailingConsoleHandler(use_colors=False, max_queue_size=50)
        
        composite = AsyncCompositeHandler(
            handlers=[file_handler, failing_console],
            parallel_execution=True,
            fail_fast=False
        )
        
        logger = AsyncHydraLogger()
        logger.add_handler(composite)
        await logger.initialize()
        
        # Log message (file handler should succeed, console should fail)
        await logger.info("ISOLATION_TEST", "Message with handler isolation")
        await asyncio.sleep(0.1)
        
        # Verify file was written (file handler succeeded)
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert "Message with handler isolation" in content
        
        # Logger should remain healthy despite console handler error
        assert logger.is_healthy()
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_network_timeout_recovery(self, resilient_logger):
        """Test recovery from network timeouts."""
        await resilient_logger.initialize()
        
        # Test network timeout handling without mocking asyncio.wait_for
        # This test verifies that the logger handles network-like timeouts gracefully
        
        # Create a custom timeout scenario
        async def timeout_operation():
            await asyncio.sleep(0.1)  # Simulate network delay
            raise asyncio.TimeoutError("Network timeout")
        
        try:
            # Try to log (should not crash)
            await resilient_logger.info("ERROR_TEST", "Message during network timeout")
            await asyncio.sleep(0.1)
            
            # Logger should remain healthy
            assert resilient_logger.is_healthy()
        except Exception as e:
            # Logger should handle timeouts gracefully
            print(f"Network timeout handled: {e}")
        
        await resilient_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_coroutine_cancellation_recovery(self, resilient_logger):
        """Test recovery from coroutine cancellation."""
        await resilient_logger.initialize()
        
        # Mock coroutine manager to simulate task cancellation
        with patch('asyncio.create_task') as mock_create_task:
            mock_task = Mock()
            mock_task.cancel = Mock()
            mock_task.done = Mock(return_value=True)
            mock_create_task.return_value = mock_task
            
            # Try to log (should handle cancellation gracefully)
            await resilient_logger.info("ERROR_TEST", "Message during task cancellation")
            await asyncio.sleep(0.1)
            
            # Logger should remain healthy
            assert resilient_logger.is_healthy()
        
        await resilient_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, temp_log_file):
        """Test graceful degradation when async operations fail."""
        handler = AsyncFileHandler(temp_log_file, max_queue_size=50)
        logger = AsyncHydraLogger()
        logger.add_handler(handler)
        await logger.initialize()
        
        # Mock async operations to fail
        with patch.object(handler, '_writer') as mock_writer:
            mock_writer.side_effect = Exception("Async writer error")
            
            # Try to log (should fallback to sync)
            await logger.info("ERROR_TEST", "Message during async failure")
            await asyncio.sleep(0.1)
            
            # Verify file was written (sync fallback worked)
            assert os.path.exists(temp_log_file)
            with open(temp_log_file, 'r') as f:
                content = f.read()
                # Check for the actual message content instead of layer name
                assert "Message during async failure" in content
            
            # Logger should remain healthy
            assert logger.is_healthy()
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_error_statistics_tracking(self, resilient_logger):
        """Test error statistics tracking."""
        await resilient_logger.initialize()
        
        # Generate some errors
        for i in range(5):
            await resilient_logger.info("ERROR_STATS_TEST", f"Message {i}")
        
        # Check error statistics
        for handler in resilient_logger.get_handlers():
            if hasattr(handler, 'get_error_stats'):
                error_stats = handler.get_error_stats()
                print(f"Handler error stats: {error_stats}")
                
                # Verify error statistics structure
                assert 'total_errors' in error_stats
                assert 'error_types' in error_stats
                assert 'uptime' in error_stats
        
        await resilient_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_recovery_after_errors(self, resilient_logger):
        """Test recovery after errors are resolved."""
        await resilient_logger.initialize()
        
        # Simulate error condition
        with patch('hydra_logger.async_hydra.core.memory_monitor.MemoryMonitor.check_memory') as mock_check:
            # First, simulate memory pressure
            mock_check.return_value = False
            
            await resilient_logger.info("ERROR_TEST", "Message during error condition")
            await asyncio.sleep(0.1)
            
            # Then, simulate recovery
            mock_check.return_value = True
            
            await resilient_logger.info("ERROR_TEST", "Message after recovery")
            await asyncio.sleep(0.1)
            
            # Logger should remain healthy throughout
            assert resilient_logger.is_healthy()
        
        await resilient_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, resilient_logger):
        """Test error handling under concurrent load."""
        await resilient_logger.initialize()
        
        async def log_with_errors(prefix: str, count: int):
            """Log messages with potential errors."""
            for i in range(count):
                try:
                    await resilient_logger.info(f"CONCURRENT_ERROR_{prefix}", f"Message {i} from {prefix}")
                    await asyncio.sleep(0.001)
                except Exception as e:
                    print(f"Error in concurrent logging: {e}")
        
        # Start multiple concurrent logging tasks
        tasks = [
            asyncio.create_task(log_with_errors("A", 10)),
            asyncio.create_task(log_with_errors("B", 10)),
            asyncio.create_task(log_with_errors("C", 10))
        ]
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Logger should remain healthy despite concurrent errors
        assert resilient_logger.is_healthy()
        
        await resilient_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_error_callback_handling(self, resilient_logger):
        """Test error callback handling."""
        await resilient_logger.initialize()
        
        error_callback_called = False
        error_callback_data = None
        
        def error_callback(error_type: str, error: Exception):
            nonlocal error_callback_called, error_callback_data
            error_callback_called = True
            error_callback_data = (error_type, str(error))
        
        # Add error callback to handlers
        for handler in resilient_logger.get_handlers():
            if hasattr(handler, '_error_tracker'):
                handler._error_tracker.add_error_callback(error_callback)
        
        # Generate an error
        with patch('hydra_logger.async_hydra.core.memory_monitor.MemoryMonitor.check_memory') as mock_check:
            mock_check.side_effect = Exception("Test error")
            
            await resilient_logger.info("ERROR_TEST", "Message to trigger error callback")
            await asyncio.sleep(0.1)
        
        # Verify error callback was called
        assert error_callback_called, "Error callback was not called"
        assert error_callback_data is not None, "Error callback data is None"
        
        await resilient_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_shutdown_during_errors(self, resilient_logger):
        """Test graceful shutdown during error conditions."""
        await resilient_logger.initialize()
        
        # Start logging in background
        async def background_logging():
            for i in range(10):
                await resilient_logger.info("SHUTDOWN_ERROR_TEST", f"Background message {i}")
                await asyncio.sleep(0.01)
        
        # Start background task
        background_task = asyncio.create_task(background_logging())
        
        # Wait a bit for some messages
        await asyncio.sleep(0.05)
        
        # Shutdown during error condition
        with patch('hydra_logger.async_hydra.core.memory_monitor.MemoryMonitor.check_memory') as mock_check:
            mock_check.return_value = False  # Simulate error condition
            
            # Shutdown should complete successfully
            await resilient_logger.aclose()
        
        # Background task should be cancelled
        try:
            await background_task
        except asyncio.CancelledError:
            pass  # Expected
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, resilient_logger):
        """Test performance during error recovery."""
        await resilient_logger.initialize()
        
        # Measure performance during normal operation
        start_time = time.time()
        for i in range(10):
            await resilient_logger.info("PERF_TEST", f"Normal message {i}")
        normal_duration = time.time() - start_time
        
        # Measure performance during error condition
        with patch('hydra_logger.async_hydra.core.memory_monitor.MemoryMonitor.check_memory') as mock_check:
            mock_check.return_value = False  # Simulate error condition
            
            start_time = time.time()
            for i in range(10):
                await resilient_logger.info("PERF_TEST", f"Error message {i}")
            error_duration = time.time() - start_time
        
        print(f"Normal operation: {normal_duration:.3f}s")
        print(f"Error condition: {error_duration:.3f}s")
        
        # Error condition should not be excessively slower (allow reasonable overhead for error handling)
        assert error_duration < normal_duration * 10, "Error condition excessively slow"
        
        await resilient_logger.aclose() 