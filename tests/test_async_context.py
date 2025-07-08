"""
Tests for async context functionality.

This module tests the async context propagation capabilities including
AsyncContextManager, AsyncTraceManager, and AsyncContextSwitcher.
"""

import asyncio
import pytest
import time
import uuid
from unittest.mock import Mock, patch

from hydra_logger.async_hydra.async_context import (
    AsyncContext, AsyncContextManager, AsyncTraceManager, AsyncContextSwitcher,
    get_async_context, set_async_context, clear_async_context,
    get_trace_id, start_trace, set_correlation_id, get_correlation_id,
    detect_context_switch, get_context_switch_count,
    async_context, trace_context, _async_context_switcher
)


class TestAsyncContext:
    """Test AsyncContext dataclass."""
    
    def test_async_context_initialization(self):
        """Test AsyncContext initialization."""
        context = AsyncContext()
        
        assert isinstance(context.trace_id, str)
        assert context.correlation_id is None
        assert context.user_id is None
        assert context.session_id is None
        assert context.request_id is None
        assert context.extra_fields == {}
        assert isinstance(context.created_at, float)
        assert context.context_switches == 0
    
    def test_async_context_with_values(self):
        """Test AsyncContext with custom values."""
        context = AsyncContext(
            trace_id="test-trace-123",
            correlation_id="test-correlation-456",
            user_id="user123",
            session_id="session456",
            request_id="request789",
            extra_fields={"key": "value"},
            context_switches=5
        )
        
        assert context.trace_id == "test-trace-123"
        assert context.correlation_id == "test-correlation-456"
        assert context.user_id == "user123"
        assert context.session_id == "session456"
        assert context.request_id == "request789"
        assert context.extra_fields == {"key": "value"}
        assert context.context_switches == 5


class TestAsyncContextManager:
    """Test AsyncContextManager functionality."""
    
    @pytest.mark.asyncio
    async def test_async_context_manager_initialization(self):
        """Test AsyncContextManager initialization."""
        manager = AsyncContextManager()
        
        assert isinstance(manager.context, AsyncContext)
        assert manager._previous_context is None
    
    @pytest.mark.asyncio
    async def test_async_context_manager_with_custom_context(self):
        """Test AsyncContextManager with custom context."""
        custom_context = AsyncContext(
            trace_id="custom-trace",
            correlation_id="custom-correlation"
        )
        
        manager = AsyncContextManager(context=custom_context)
        
        assert manager.context.trace_id == "custom-trace"
        assert manager.context.correlation_id == "custom-correlation"
    
    @pytest.mark.asyncio
    async def test_async_context_manager_enter_exit(self):
        """Test AsyncContextManager async context manager."""
        manager = AsyncContextManager()
        
        # Enter context
        async with manager:
            # Check context is set
            current_context = AsyncContextManager.get_current_context()
            assert current_context is not None
            assert current_context.trace_id == manager.context.trace_id
        
        # Check context is restored (should be None since no previous context)
        current_context = AsyncContextManager.get_current_context()
        assert current_context is None
    
    @pytest.mark.asyncio
    async def test_async_context_manager_nested_contexts(self):
        """Test nested async context managers."""
        outer_context = AsyncContext(trace_id="outer-trace")
        inner_context = AsyncContext(trace_id="inner-trace")
        
        # Outer context
        async with AsyncContextManager(outer_context):
            current = AsyncContextManager.get_current_context()
            assert current is not None
            assert current.trace_id == "outer-trace"
            
            # Inner context
            async with AsyncContextManager(inner_context):
                current = AsyncContextManager.get_current_context()
                assert current is not None
                assert current.trace_id == "inner-trace"
            
            # Should be back to outer context
            current = AsyncContextManager.get_current_context()
            assert current is not None
            assert current.trace_id == "outer-trace"
        
        # Should be back to no context
        current = AsyncContextManager.get_current_context()
        assert current is None
    
    @pytest.mark.asyncio
    async def test_async_context_manager_get_current_context(self):
        """Test getting current async context."""
        # Initially no context
        context = AsyncContextManager.get_current_context()
        assert context is None
        
        # Set context
        custom_context = AsyncContext(trace_id="test-trace")
        AsyncContextManager.set_current_context(custom_context)
        
        # Get current context
        context = AsyncContextManager.get_current_context()
        assert context is not None
        assert context.trace_id == "test-trace"
    
    @pytest.mark.asyncio
    async def test_async_context_manager_set_clear_context(self):
        """Test setting and clearing async context."""
        custom_context = AsyncContext(trace_id="test-trace")
        
        # Set context
        AsyncContextManager.set_current_context(custom_context)
        
        # Verify context is set
        context = AsyncContextManager.get_current_context()
        assert context is not None
        assert context.trace_id == "test-trace"
        
        # Clear context
        AsyncContextManager.clear_current_context()
        
        # Verify context is cleared
        context = AsyncContextManager.get_current_context()
        assert context is None


class TestAsyncTraceManager:
    """Test AsyncTraceManager functionality."""
    
    def test_async_trace_manager_initialization(self):
        """Test AsyncTraceManager initialization."""
        manager = AsyncTraceManager()
        
        assert manager._trace_var is not None
        assert manager._correlation_var is not None
    
    def test_async_trace_manager_start_trace(self):
        """Test starting a new trace."""
        manager = AsyncTraceManager()
        
        # Start trace with custom ID
        trace_id = manager.start_trace("custom-trace-123")
        assert trace_id == "custom-trace-123"
        
        # Get trace ID
        current_trace = manager.get_trace_id()
        assert current_trace == "custom-trace-123"
    
    def test_async_trace_manager_start_trace_auto_generated(self):
        """Test starting trace with auto-generated ID."""
        manager = AsyncTraceManager()
        
        # Start trace without custom ID
        trace_id = manager.start_trace()
        assert isinstance(trace_id, str)
        assert len(trace_id) > 0
        
        # Get trace ID
        current_trace = manager.get_trace_id()
        assert current_trace == trace_id
    
    def test_async_trace_manager_correlation_id(self):
        """Test correlation ID functionality."""
        manager = AsyncTraceManager()
        
        # Set correlation ID
        manager.set_correlation_id("test-correlation")
        
        # Get correlation ID
        correlation_id = manager.get_correlation_id()
        assert correlation_id == "test-correlation"
    
    def test_async_trace_manager_clear_trace(self):
        """Test clearing trace."""
        manager = AsyncTraceManager()
        
        # Start trace and set correlation
        manager.start_trace("test-trace")
        manager.set_correlation_id("test-correlation")
        
        # Verify they are set
        assert manager.get_trace_id() == "test-trace"
        assert manager.get_correlation_id() == "test-correlation"
        
        # Clear trace
        manager.clear_trace()
        
        # Verify they are cleared
        assert manager.get_trace_id() is None
        assert manager.get_correlation_id() is None


class TestAsyncContextSwitcher:
    """Test AsyncContextSwitcher functionality."""
    
    def test_async_context_switcher_initialization(self):
        """Test AsyncContextSwitcher initialization."""
        switcher = AsyncContextSwitcher()
        
        assert switcher._switch_count == 0
        assert switcher._last_context is None
    
    def test_async_context_switcher_detect_context_switch(self):
        """Test context switch detection."""
        switcher = AsyncContextSwitcher()
        
        # First context (no switch)
        context1 = AsyncContext(trace_id="trace-1")
        switched = switcher.detect_context_switch(context1)
        assert switched is False
        assert switcher._switch_count == 0
        
        # Same context (no switch)
        switched = switcher.detect_context_switch(context1)
        assert switched is False
        assert switcher._switch_count == 0
        
        # Different context (switch detected)
        context2 = AsyncContext(trace_id="trace-2")
        switched = switcher.detect_context_switch(context2)
        assert switched is True
        assert switcher._switch_count == 1
        
        # Another different context (switch detected)
        context3 = AsyncContext(trace_id="trace-3")
        switched = switcher.detect_context_switch(context3)
        assert switched is True
        assert switcher._switch_count == 2
    
    def test_async_context_switcher_detect_correlation_switch(self):
        """Test correlation ID switch detection."""
        switcher = AsyncContextSwitcher()
        
        # First context
        context1 = AsyncContext(trace_id="trace-1", correlation_id="corr-1")
        switched = switcher.detect_context_switch(context1)
        assert switched is False
        
        # Same trace, different correlation (switch detected)
        context2 = AsyncContext(trace_id="trace-1", correlation_id="corr-2")
        switched = switcher.detect_context_switch(context2)
        assert switched is True
        assert switcher._switch_count == 1
    
    def test_async_context_switcher_get_switch_count(self):
        """Test getting switch count."""
        switcher = AsyncContextSwitcher()
        
        assert switcher.get_switch_count() == 0
        
        # Trigger some switches
        context1 = AsyncContext(trace_id="trace-1")
        context2 = AsyncContext(trace_id="trace-2")
        
        switcher.detect_context_switch(context1)
        switcher.detect_context_switch(context2)
        
        assert switcher.get_switch_count() == 1
    
    def test_async_context_switcher_reset_switch_count(self):
        """Test resetting switch count."""
        switcher = AsyncContextSwitcher()
        
        # Trigger some switches
        context1 = AsyncContext(trace_id="trace-1")
        context2 = AsyncContext(trace_id="trace-2")
        
        switcher.detect_context_switch(context1)
        switcher.detect_context_switch(context2)
        
        assert switcher.get_switch_count() == 1
        
        # Reset switch count
        switcher.reset_switch_count()
        
        assert switcher.get_switch_count() == 0


class TestAsyncContextFunctions:
    """Test async context utility functions."""
    
    def test_get_async_context(self):
        """Test get_async_context function."""
        # Initially no context
        context = get_async_context()
        assert context is None
        
        # Set context
        custom_context = AsyncContext(trace_id="test-trace")
        set_async_context(custom_context)
        
        # Get context
        context = get_async_context()
        assert context is not None
        assert context.trace_id == "test-trace"
    
    def test_set_clear_async_context(self):
        """Test set_async_context and clear_async_context functions."""
        custom_context = AsyncContext(trace_id="test-trace")
        
        # Set context
        set_async_context(custom_context)
        
        # Verify context is set
        context = get_async_context()
        assert context is not None
        assert context.trace_id == "test-trace"
        
        # Clear context
        clear_async_context()
        
        # Verify context is cleared
        context = get_async_context()
        assert context is None
    
    def test_trace_functions(self):
        """Test trace-related functions."""
        # Start trace
        trace_id = start_trace("test-trace")
        assert trace_id == "test-trace"
        
        # Get trace ID
        current_trace = get_trace_id()
        assert current_trace == "test-trace"
        
        # Set correlation ID
        set_correlation_id("test-correlation")
        
        # Get correlation ID
        correlation_id = get_correlation_id()
        assert correlation_id == "test-correlation"
    
    def test_context_switch_functions(self):
        """Test context switch functions."""
        # Test context switch detection
        context1 = AsyncContext(trace_id="trace-1")
        context2 = AsyncContext(trace_id="trace-2")
        
        # No switch initially
        switched = detect_context_switch(context1)
        assert switched is False
        
        # Switch detected
        switched = detect_context_switch(context2)
        assert switched is True
        
        # Get switch count
        count = get_context_switch_count()
        assert count == 1


class TestAsyncContextDecorators:
    """Test async context decorators."""
    
    @pytest.mark.asyncio
    async def test_async_context_decorator(self):
        """Test async_context decorator."""
        custom_context = AsyncContext(trace_id="decorator-trace")
        
        async with async_context(custom_context):
            # Check context is set
            context = get_async_context()
            assert context is not None
            assert context.trace_id == "decorator-trace"
        
        # Check context is cleared
        context = get_async_context()
        assert context is None
    
    @pytest.mark.asyncio
    async def test_async_context_decorator_auto_generated(self):
        """Test async_context decorator with auto-generated context."""
        async with async_context():
            # Check context is set
            context = get_async_context()
            assert context is not None
            assert isinstance(context.trace_id, str)
        
        # Check context is cleared
        context = get_async_context()
        assert context is None
    
    @pytest.mark.asyncio
    async def test_trace_context_decorator(self):
        """Test trace_context decorator."""
        async with trace_context("trace-decorator"):
            # Check trace is set
            trace_id = get_trace_id()
            assert trace_id == "trace-decorator"
        
        # Check trace is cleared
        trace_id = get_trace_id()
        assert trace_id is None
    
    @pytest.mark.asyncio
    async def test_trace_context_decorator_auto_generated(self):
        """Test trace_context decorator with auto-generated trace ID."""
        async with trace_context():
            # Check trace is set
            trace_id = get_trace_id()
            assert trace_id is not None
            assert isinstance(trace_id, str)
        
        # Check trace is cleared
        trace_id = get_trace_id()
        assert trace_id is None


class TestAsyncContextIntegration:
    """Integration tests for async context components."""
    
    def setup_method(self):
        """Reset global state before each test."""
        # Clear async context
        clear_async_context()
        # Reset context switcher
        _async_context_switcher.reset_switch_count()
        _async_context_switcher._last_context = None
    
    def teardown_method(self):
        """Clean up after each test."""
        # Clear async context
        clear_async_context()
        # Reset context switcher
        _async_context_switcher.reset_switch_count()
        _async_context_switcher._last_context = None
    
    @pytest.mark.asyncio
    async def test_context_propagation_across_async_operations(self):
        """Test context propagation across async operations."""
        custom_context = AsyncContext(
            trace_id="integration-trace",
            correlation_id="integration-correlation",
            user_id="user123"
        )
        
        async def inner_operation():
            # Context should be available in inner operation
            context = get_async_context()
            assert context is not None
            assert context.trace_id == "integration-trace"
            assert context.correlation_id == "integration-correlation"
            assert context.user_id == "user123"
            
            # Create nested context
            nested_context = AsyncContext(trace_id="nested-trace")
            async with AsyncContextManager(nested_context):
                # Should have nested context
                context = get_async_context()
                assert context is not None
                assert context.trace_id == "nested-trace"
            
            # Should be back to original context
            context = get_async_context()
            assert context is not None
            assert context.trace_id == "integration-trace"
        
        async with AsyncContextManager(custom_context):
            # Start inner operation
            await inner_operation()
            
            # Context should still be available
            context = get_async_context()
            assert context is not None
            assert context.trace_id == "integration-trace"
    
    @pytest.mark.asyncio
    async def test_context_switching_detection(self):
        """Test context switching detection in async operations."""
        switcher = AsyncContextSwitcher()
        
        async def operation_with_context(trace_id):
            context = AsyncContext(trace_id=trace_id)
            async with AsyncContextManager(context):
                # Detect switch
                switched = detect_context_switch(context)
                return switched
        
        # First operation
        switched1 = await operation_with_context("trace-1")
        assert switched1 is False
        
        # Second operation (should detect switch)
        switched2 = await operation_with_context("trace-2")
        assert switched2 is True
        
        # Check total switches
        total_switches = get_context_switch_count()
        assert total_switches == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_context_operations(self):
        """Test concurrent async context operations."""
        results = []
        
        async def concurrent_operation(i):
            context = AsyncContext(trace_id=f"trace-{i}")
            async with AsyncContextManager(context):
                await asyncio.sleep(0.01)  # Small delay
                current_context = get_async_context()
                assert current_context is not None
                results.append(current_context.trace_id)
        
        # Run concurrent operations
        tasks = [concurrent_operation(i) for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Check all operations completed
        assert len(results) == 5
        assert "trace-0" in results
        assert "trace-1" in results
        assert "trace-2" in results
        assert "trace-3" in results
        assert "trace-4" in results
    
    @pytest.mark.asyncio
    async def test_context_performance_under_load(self):
        """Test context performance under load."""
        start_time = time.time()
        
        async def fast_context_operation():
            context = AsyncContext(trace_id=str(uuid.uuid4()))
            async with AsyncContextManager(context):
                # Quick operation
                pass
        
        # Run many context operations
        tasks = [fast_context_operation() for _ in range(100)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete quickly
        assert processing_time < 1.0
    
    @pytest.mark.asyncio
    async def test_context_error_handling(self):
        """Test context error handling."""
        async def operation_with_error():
            context = AsyncContext(trace_id="error-trace")
            async with AsyncContextManager(context):
                raise Exception("Test error")
        
        # Should handle error gracefully
        with pytest.raises(Exception):
            await operation_with_error()
        
        # Context should be cleared after error
        current_context = get_async_context()
        assert current_context is None
    
    @pytest.mark.asyncio
    async def test_context_memory_efficiency(self):
        """Test context memory efficiency."""
        # Create many contexts
        contexts = []
        
        for i in range(1000):
            context = AsyncContext(trace_id=f"memory-test-{i}")
            contexts.append(context)
        
        # Use contexts in async operations
        async def use_context(context):
            async with AsyncContextManager(context):
                await asyncio.sleep(0.001)
        
        # Run operations
        tasks = [use_context(context) for context in contexts]
        await asyncio.gather(*tasks)
        
        # Should not consume excessive memory
        # Context should be cleared
        current_context = get_async_context()
        assert current_context is None 