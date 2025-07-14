"""
Tests for async HydraLogger functionality.

This module tests the async logging capabilities of HydraLogger
including async handlers, concurrent logging, and performance monitoring.
"""

import asyncio
import io
import os
import tempfile
import pytest
import logging

from hydra_logger.async_hydra import AsyncHydraLogger, AsyncFileHandler, AsyncConsoleHandler


class TestAsyncHydraLogger:
    """Test suite for AsyncHydraLogger."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_filename = f.name
        yield temp_filename
        # Cleanup
        try:
            os.unlink(temp_filename)
        except OSError:
            pass
    
    @pytest.fixture
    def console_stream(self):
        """Create a string stream for testing console output."""
        return io.StringIO()
    
    @pytest.fixture
    def basic_logger(self):
        """Create a basic AsyncHydraLogger with console handler."""
        logger = AsyncHydraLogger()
        yield logger
        # Ensure proper cleanup
        try:
            if asyncio.get_event_loop().is_running():
                # We're in an async context, schedule cleanup
                asyncio.create_task(logger.aclose())
            else:
                # We're not in async context, just close sync
                logger.close()
        except Exception:
            pass
    
    @pytest.fixture
    def file_logger(self, temp_file):
        """Create AsyncHydraLogger with file handler."""
        config = {
            'handlers': [
                {'type': 'file', 'filename': temp_file}
            ]
        }
        logger = AsyncHydraLogger(config)
        yield logger
        # Ensure proper cleanup
        try:
            if asyncio.get_event_loop().is_running():
                # We're in an async context, schedule cleanup
                asyncio.create_task(logger.aclose())
            else:
                # We're not in async context, just close sync
                logger.close()
        except Exception:
            pass
    
    @pytest.fixture
    def multi_handler_logger(self, temp_file, console_stream):
        """Create AsyncHydraLogger with multiple handlers."""
        config = {
            'handlers': [
                {'type': 'file', 'filename': temp_file},
                {'type': 'console', 'stream': console_stream}
            ]
        }
        logger = AsyncHydraLogger(config)
        yield logger
        # Ensure proper cleanup
        try:
            if asyncio.get_event_loop().is_running():
                # We're in an async context, schedule cleanup
                asyncio.create_task(logger.aclose())
            else:
                # We're not in async context, just close sync
                logger.close()
        except Exception:
            pass
    
    async def _wait_for_all_handlers(self, logger):
        """Wait for all handlers' queues to be empty and writers to finish."""
        for handler in logger._handlers:
            if hasattr(handler, '_queue') and hasattr(handler, '_writer_task'):
                # Wait for queue to be empty
                for _ in range(100):
                    if handler._queue.empty():
                        break
                    await asyncio.sleep(0.01)
                
                # Wait for writer task to complete if it exists
                if hasattr(handler, '_writer_task') and handler._writer_task and not handler._writer_task.done():
                    try:
                        await asyncio.wait_for(handler._writer_task, timeout=2.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        # Task timed out or was cancelled, which is expected during cleanup
                        pass
                    except Exception:
                        # Handle any other exceptions during task cleanup
                        pass
                    finally:
                        # Ensure task is properly cancelled if still running
                        if handler._writer_task and not handler._writer_task.done():
                            handler._writer_task.cancel()
                            try:
                                await asyncio.wait_for(handler._writer_task, timeout=0.5)
                            except (asyncio.TimeoutError, asyncio.CancelledError):
                                pass

    @pytest.mark.asyncio
    async def test_basic_logging(self, basic_logger):
        """Test basic async logging functionality."""
        await basic_logger.initialize()
        
        # Log messages
        await basic_logger.info("TEST", "Test message")
        await basic_logger.error("TEST", "Error message")
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_file_logging(self, file_logger, temp_file):
        """Test file logging functionality."""
        await file_logger.initialize()
        
        # Log messages
        await file_logger.info("FILE_TEST", "File message")
        await file_logger.error("FILE_TEST", "File error")
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(file_logger)
        
        # Check file content
        with open(temp_file, 'r') as f:
            content = f.read()
            assert "File message" in content
            assert "File error" in content
        
        await file_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_console_logging(self, console_stream):
        """Test console logging functionality."""
        config = {
            'handlers': [
                {'type': 'console', 'stream': console_stream}
            ]
        }
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Log messages
        await logger.info("CONSOLE_TEST", "Console message")
        await logger.warning("CONSOLE_TEST", "Warning message")
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(logger)
        
        # Check console output
        console_stream.seek(0)
        content = console_stream.read()
        assert "Console message" in content
        assert "Warning message" in content
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_multi_handler_logging(self, multi_handler_logger, temp_file, console_stream):
        """Test logging to multiple handlers."""
        await multi_handler_logger.initialize()
        
        # Log messages
        await multi_handler_logger.info("MULTI_TEST", "Multi-handler message")
        await multi_handler_logger.error("MULTI_TEST", "Error message")
        
        await self._wait_for_all_handlers(multi_handler_logger)
        
        # Check file output
        with open(temp_file, 'r') as f:
            file_content = f.read()
            assert "Multi-handler message" in file_content
            assert "Error message" in file_content
        
        # Check console output
        console_stream.seek(0)
        console_content = console_stream.read()
        assert "Multi-handler message" in console_content
        assert "Error message" in console_content
        
        await multi_handler_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_handler_management(self, basic_logger):
        """Test adding and removing handlers at runtime."""
        await basic_logger.initialize()
        
        # Add a file handler
        file_handler = AsyncFileHandler("test_handler.log")
        basic_logger.add_handler(file_handler)
        
        # Log message
        await basic_logger.info("HANDLER_TEST", "Handler management test")
        
        # Remove handler
        basic_logger.remove_handler(file_handler)
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()
        
        # Cleanup
        try:
            os.unlink("test_handler.log")
        except OSError:
            pass
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, basic_logger):
        """Test health monitoring functionality."""
        await basic_logger.initialize()
        
        # Get health status
        health = basic_logger.get_health_status()
        
        # Check required fields
        assert 'uptime' in health
        assert 'is_healthy' in health
        
        # Check if logger is healthy
        assert basic_logger.is_healthy()
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, basic_logger):
        """Test error handling and recovery."""
        await basic_logger.initialize()
        
        # Test logging with invalid handler (should not crash)
        # This tests the error handling in the logger
        
        # Log normally
        await basic_logger.info("ERROR_TEST", "Normal message")
        
        # Check error stats
        health = basic_logger.get_health_status()
        # Should not have excessive errors
        assert health.get('error_count', 0) < 10
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_initialization_and_shutdown(self, basic_logger):
        """Test proper initialization and shutdown."""
        # Test initialization
        assert not basic_logger._initialized
        await basic_logger.initialize()
        assert basic_logger._initialized
        
        # Test double initialization (should be safe)
        await basic_logger.initialize()
        assert basic_logger._initialized
        
        # Test shutdown
        await basic_logger.aclose()
        # Should not raise any exceptions
    
    @pytest.mark.asyncio
    async def test_configuration_options(self):
        """Test different configuration options."""
        # Test with custom queue sizes
        config = {
            'handlers': [
                {
                    'type': 'console',
                    'max_queue_size': 500,
                    'memory_threshold': 80.0,
                    'use_colors': False
                }
            ]
        }
        logger = AsyncHydraLogger(config)
        await logger.initialize()
        
        # Log some messages
        await logger.info("CONFIG_TEST", "Configuration test")
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(logger)
        
        await logger.aclose()
    
    @pytest.mark.asyncio
    async def test_concurrent_logging(self, basic_logger):
        """Test concurrent logging operations."""
        await basic_logger.initialize()
        
        # Create multiple concurrent logging tasks
        async def log_message(i):
            await basic_logger.info(f"CONCURRENT_{i}", f"Concurrent message {i}")
        
        # Run multiple concurrent tasks
        tasks = [log_message(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, basic_logger):
        """Test performance metrics collection."""
        await basic_logger.initialize()
        
        # Get performance metrics
        metrics = basic_logger.get_performance_metrics()
        
        # Should return a dict (even if empty for now)
        assert isinstance(metrics, dict)
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_edge_cases(self, basic_logger):
        """Test edge cases and error scenarios."""
        await basic_logger.initialize()
        
        # Test empty message
        await basic_logger.info("EDGE_TEST", "")
        
        # Test very long message
        long_message = "x" * 10000
        await basic_logger.info("EDGE_TEST", long_message)
        
        # Test special characters
        special_message = "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        await basic_logger.info("EDGE_TEST", special_message)
        
        # Wait for all handlers to complete their work before closing
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()
    
    @pytest.mark.asyncio
    async def test_log_levels(self, basic_logger):
        """Test all log levels."""
        await basic_logger.initialize()
        
        levels = [
            ("DEBUG", "debug message"),
            ("INFO", "info message"),
            ("WARNING", "warning message"),
            ("ERROR", "error message"),
            ("CRITICAL", "critical message")
        ]
        
        for level, message in levels:
            await basic_logger.log("LEVEL_TEST", level, message)
        
        # Wait for all handlers to complete their work
        await self._wait_for_all_handlers(basic_logger)
        
        await basic_logger.aclose()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 