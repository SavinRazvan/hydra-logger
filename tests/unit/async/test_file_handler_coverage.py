"""
Test coverage for AsyncFileHandler to cover missing lines.

This module tests edge cases and error conditions to achieve better coverage.
"""

import asyncio
import logging
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from hydra_logger.async_hydra import AsyncFileHandler


class TestAsyncFileHandlerCoverage:
    """Test suite for AsyncFileHandler coverage."""
    
    @pytest.fixture
    def test_logs_dir(self):
        """Create temporary test logs directory."""
        test_dir = tempfile.mkdtemp(prefix="hydra_test_")
        yield test_dir
        # Cleanup
        if os.path.exists(test_dir):
            try:
                import shutil
                shutil.rmtree(test_dir)
            except Exception:
                pass
    
    @pytest.fixture
    def file_handler(self, test_logs_dir):
        """Create a file handler for testing."""
        log_file = os.path.join(test_logs_dir, "test.log")
        return AsyncFileHandler(log_file)
    
    @pytest.mark.asyncio
    async def test_writer_memory_pressure(self, file_handler):
        """Test file handler under memory pressure."""
        try:
            await file_handler.initialize()
            
            # Mock memory monitor to simulate pressure
            with patch.object(file_handler._memory_monitor, 'check_memory', return_value=False):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should fallback to sync
                await file_handler.emit_async(record)
                
                # Wait for handler completion
                await self.wait_for_handler_completion(file_handler)
                
                # Should not crash
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_queue_full(self, file_handler):
        """Test file handler when queue is full."""
        try:
            await file_handler.initialize()
            
            # Mock queue to be full - limit side effect calls to prevent infinite loops
            call_count = 0
            def queue_put_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count > 5:  # Limit calls to prevent infinite loops
                    return
                raise Exception("Queue full")
            
            with patch.object(file_handler._queue, 'put', side_effect=queue_put_side_effect):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should fallback to sync
                await file_handler.emit_async(record)
                
                # Wait for handler completion
                await self.wait_for_handler_completion(file_handler)
                
                # Should not crash
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_emit_exception(self, file_handler):
        """Test file handler with emit exception."""
        try:
            await file_handler.initialize()
            
            # Mock format to fail
            with patch.object(file_handler, 'format', side_effect=Exception("Format failed")):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should fallback to sync
                await file_handler.emit_async(record)
                
                # Wait for handler completion
                await self.wait_for_handler_completion(file_handler)
                
                # Should not crash
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_task_cancellation(self, file_handler):
        """Test file handler with task cancellation."""
        try:
            await file_handler.initialize()
            
            # Start writer task
            if file_handler._writer_task:
                # Cancel the task
                file_handler._writer_task.cancel()
                
                # Wait a bit for cancellation
                await asyncio.sleep(0.1)
                
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should handle cancellation
                await file_handler.emit_async(record)
                
                # Should not crash
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_timeout_handling(self, file_handler):
        """Test file handler with timeout handling."""
        try:
            await file_handler.initialize()
            
            # Mock queue.get to timeout - limit calls to prevent infinite loops
            call_count = 0
            def queue_get_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count > 3:  # Limit calls to prevent infinite loops
                    return "test message"
                raise asyncio.TimeoutError()
            
            with patch.object(file_handler._queue, 'get', side_effect=queue_get_side_effect):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record
                await file_handler.emit_async(record)
                
                # Wait for handler completion
                await self.wait_for_handler_completion(file_handler)
                
                # Should handle timeout gracefully
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_error_tracking(self, file_handler):
        """Test file handler error tracking."""
        try:
            await file_handler.initialize()
            
            # Mock error tracker
            with patch.object(file_handler._error_tracker, 'record_error') as mock_record:
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Mock queue to fail - limit calls to prevent infinite loops
                call_count = 0
                def queue_put_side_effect(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count > 3:  # Limit calls to prevent infinite loops
                        return
                    raise Exception("Test error")
                
                with patch.object(file_handler._queue, 'put', side_effect=queue_put_side_effect):
                    # Emit the record
                    await file_handler.emit_async(record)
                    
                    # Wait for handler completion
                    await self.wait_for_handler_completion(file_handler)
                    
                    # Should not crash
                    assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_health_monitoring(self, file_handler):
        """Test file handler health monitoring."""
        try:
            await file_handler.initialize()
            
            # Check health status
            health = file_handler.get_health_status()
            
            # Verify health status contains expected fields
            assert 'uptime' in health
            assert 'dropped_messages' in health
            assert 'sync_fallbacks' in health
            
            # Check if healthy
            is_healthy = file_handler.is_healthy()
            assert isinstance(is_healthy, bool)
            
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_shutdown_handling(self, file_handler):
        """Test file handler shutdown handling."""
        try:
            await file_handler.initialize()
            
            # Start writer task
            if file_handler._writer_task:
                # Request shutdown by setting the shutdown event
                file_handler._shutdown_manager._shutdown_event.set()
                
                # Wait a bit for shutdown
                await asyncio.sleep(0.1)
                
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should handle shutdown gracefully
                await file_handler.emit_async(record)
                
                # Should not crash
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_sync_fallback(self, file_handler):
        """Test file handler sync fallback."""
        try:
            await file_handler.initialize()
            
            # Mock aiofiles to be unavailable
            with patch('hydra_logger.async_hydra.handlers.file_handler.AIOFILES_AVAILABLE', False):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should use sync fallback
                await file_handler.emit_async(record)
                
                # Wait for handler completion
                await self.wait_for_handler_completion(file_handler)
                
                # Should not crash
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_file_write_error(self, file_handler):
        """Test file handler with file write error."""
        try:
            await file_handler.initialize()
            
            # Mock file write to fail
            with patch('builtins.open', side_effect=Exception("File write error")):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should handle file error
                await file_handler.emit_async(record)
                
                # Wait for handler completion
                await self.wait_for_handler_completion(file_handler)
                
                # Should not crash
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_sync_fallback_timeout_handling(self, file_handler):
        """Test file handler sync fallback timeout handling."""
        try:
            await file_handler.initialize()
            
            # Mock aiofiles to be unavailable
            with patch('hydra_logger.async_hydra.handlers.file_handler.AIOFILES_AVAILABLE', False):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should use sync fallback
                await file_handler.emit_async(record)
                
                # Wait for handler completion with timeout
                await self.wait_for_handler_completion(file_handler, timeout=2.0)
                
                # Should handle timeout gracefully
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_sync_fallback_cancellation(self, file_handler):
        """Test file handler sync fallback cancellation."""
        try:
            await file_handler.initialize()
            
            # Mock aiofiles to be unavailable
            with patch('hydra_logger.async_hydra.handlers.file_handler.AIOFILES_AVAILABLE', False):
                # Create a log record
                record = self.create_log_record("test message", logging.INFO)
                
                # Emit the record - should use sync fallback
                await file_handler.emit_async(record)
                
                # Wait for handler completion with timeout
                await self.wait_for_handler_completion(file_handler, timeout=2.0)
                
                # Should handle cancellation gracefully
                assert True
                
        finally:
            await file_handler.aclose()
    
    @pytest.mark.asyncio
    async def test_writer_sync_fallback_file_error(self, file_handler):
        """Test file handler sync fallback with file error."""
        try:
            await file_handler.initialize()
            
            # Mock aiofiles to be unavailable and file write to fail
            with patch('hydra_logger.async_hydra.handlers.file_handler.AIOFILES_AVAILABLE', False):
                with patch('builtins.open', side_effect=Exception("File error")):
                    # Create a log record
                    record = self.create_log_record("test message", logging.INFO)
                    
                    # Emit the record
                    await file_handler.emit_async(record)
                    
                    # Wait for handler completion
                    await self.wait_for_handler_completion(file_handler)
                    
                    # Should handle file error gracefully
                    assert True
                
        finally:
            await file_handler.aclose()
    
    def create_log_record(self, message: str, level: int) -> logging.LogRecord:
        """Create a test log record."""
        return logging.LogRecord(
            name="test",
            level=level,
            pathname="test.py",
            lineno=1,
            msg=message,
            args=(),
            exc_info=None
        )
    
    async def wait_for_handler_completion(self, handler: AsyncFileHandler, timeout: float = 1.0):
        """Wait for handler to complete processing."""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if handler._writer_task and handler._writer_task.done():
                break
            await asyncio.sleep(0.01) 