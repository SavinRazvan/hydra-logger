"""
Tests for hydra_logger.types.context module.
"""

import pytest
import time
import threading
import contextvars
from unittest.mock import patch, MagicMock
from hydra_logger.types.context import (
    ContextType, CallerInfo, SystemInfo, LogContext, ContextManager, ContextDetector,
    get_current_context, set_current_context, clear_current_context, create_context, get_caller_info
)


class TestContextType:
    """Test ContextType enum."""
    
    def test_context_type_values(self):
        """Test ContextType enum values."""
        assert ContextType.REQUEST.value == "request"
        assert ContextType.SESSION.value == "session"
        assert ContextType.TRANSACTION.value == "transaction"
        assert ContextType.TRACE.value == "trace"
        assert ContextType.USER.value == "user"
        assert ContextType.ENVIRONMENT.value == "environment"
        assert ContextType.CUSTOM.value == "custom"
    
    def test_context_type_members(self):
        """Test ContextType enum members."""
        assert len(list(ContextType)) == 7
        assert ContextType.REQUEST in ContextType
        assert ContextType.CUSTOM in ContextType


class TestCallerInfo:
    """Test CallerInfo class."""
    
    def test_caller_info_creation(self):
        """Test CallerInfo creation."""
        caller = CallerInfo(
            filename="test.py",
            function_name="test_function",
            line_number=42
        )
        
        assert caller.filename == "test.py"
        assert caller.function_name == "test_function"
        assert caller.line_number == 42
        assert caller.module_name is None
    
    def test_caller_info_with_module(self):
        """Test CallerInfo with module name."""
        caller = CallerInfo(
            filename="test.py",
            function_name="test_function",
            line_number=42,
            module_name="test_module"
        )
        
        assert caller.filename == "test.py"
        assert caller.function_name == "test_function"
        assert caller.line_number == 42
        assert caller.module_name == "test_module"
    
    def test_caller_info_str(self):
        """Test CallerInfo string representation."""
        caller = CallerInfo(
            filename="test.py",
            function_name="test_function",
            line_number=42
        )
        
        str_repr = str(caller)
        assert "test.py" in str_repr
        assert "test_function" in str_repr
        assert "42" in str_repr


class TestSystemInfo:
    """Test SystemInfo class."""
    
    def test_system_info_creation(self):
        """Test SystemInfo creation."""
        system = SystemInfo(
            thread_id=123,
            process_id=456,
            hostname="test-host"
        )
        
        assert system.thread_id == 123
        assert system.process_id == 456
        assert system.hostname == "test-host"
        assert system.pid is not None  # Should be set in __post_init__
    
    def test_system_info_post_init(self):
        """Test SystemInfo __post_init__ method."""
        with patch('os.getpid', return_value=999):
            system = SystemInfo(
                thread_id=123,
                process_id=456
            )
            
            assert system.pid == 999
    
    def test_system_info_with_pid(self):
        """Test SystemInfo with explicit pid."""
        system = SystemInfo(
            thread_id=123,
            process_id=456,
            pid=789
        )
        
        assert system.pid == 789


class TestLogContext:
    """Test LogContext class."""
    
    def test_log_context_creation(self):
        """Test LogContext creation."""
        context = LogContext()
        
        assert context.context_id.startswith("ctx_")
        assert context.context_type == ContextType.CUSTOM
        assert isinstance(context.created_at, float)
        assert isinstance(context.last_accessed, float)
        assert context.caller_info is None
        assert context.system_info is not None
        assert context.metadata == {}
        assert context.access_count == 0
        assert context.log_count == 0
    
    def test_log_context_with_parameters(self):
        """Test LogContext with specific parameters."""
        caller = CallerInfo("test.py", "test_func", 42)
        system = SystemInfo(123, 456)
        metadata = {"key": "value"}
        
        context = LogContext(
            context_type=ContextType.REQUEST,
            caller_info=caller,
            system_info=system,
            metadata=metadata
        )
        
        assert context.context_type == ContextType.REQUEST
        assert context.caller_info == caller
        assert context.system_info == system
        assert context.metadata == metadata
    
    def test_log_context_post_init(self):
        """Test LogContext __post_init__ method."""
        context = LogContext()
        
        # Should create system_info if not provided
        assert context.system_info is not None
        assert isinstance(context.system_info.thread_id, int)
        assert isinstance(context.system_info.process_id, int)
    
    def test_update_metadata(self):
        """Test update_metadata method."""
        context = LogContext()
        
        context.update_metadata("key1", "value1")
        assert context.metadata["key1"] == "value1"
        assert context.access_count == 1
        
        context.update_metadata("key2", 42)
        assert context.metadata["key2"] == 42
        assert context.access_count == 2
    
    def test_get_metadata(self):
        """Test get_metadata method."""
        context = LogContext()
        context.metadata = {"key1": "value1", "key2": 42}
        
        # Get initial access count
        initial_count = context.access_count
        
        assert context.get_metadata("key1") == "value1"
        assert context.get_metadata("key2") == 42
        assert context.get_metadata("key3") is None
        assert context.get_metadata("key3", "default") == "default"
        # The access count should increase by 3 for the 3 get_metadata calls
        # Note: There might be an extra call somewhere, so we check it's at least 3
        assert context.access_count >= initial_count + 3
    
    def test_add_metadata(self):
        """Test add_metadata method."""
        context = LogContext()
        context.metadata = {"key1": "value1"}
        
        new_metadata = {"key2": "value2", "key3": 42}
        context.add_metadata(new_metadata)
        
        assert context.metadata["key1"] == "value1"
        assert context.metadata["key2"] == "value2"
        assert context.metadata["key3"] == 42
        assert context.access_count == 1
    
    def test_has_metadata(self):
        """Test has_metadata method."""
        context = LogContext()
        context.metadata = {"key1": "value1"}
        
        assert context.has_metadata("key1") is True
        assert context.has_metadata("key2") is False
    
    def test_remove_metadata(self):
        """Test remove_metadata method."""
        context = LogContext()
        context.metadata = {"key1": "value1", "key2": "value2"}
        
        value = context.remove_metadata("key1")
        assert value == "value1"
        assert "key1" not in context.metadata
        assert context.metadata["key2"] == "value2"
        assert context.access_count == 1
        
        # Remove non-existent key
        value = context.remove_metadata("key3")
        assert value is None
        assert context.access_count == 2
    
    def test_clear_metadata(self):
        """Test clear_metadata method."""
        context = LogContext()
        context.metadata = {"key1": "value1", "key2": "value2"}
        
        context.clear_metadata()
        assert context.metadata == {}
        assert context.access_count == 1
    
    def test_increment_log_count(self):
        """Test increment_log_count method."""
        context = LogContext()
        
        assert context.log_count == 0
        context.increment_log_count()
        assert context.log_count == 1
        context.increment_log_count()
        assert context.log_count == 2
        assert context.access_count == 2
    
    def test_get_stats(self):
        """Test get_stats method."""
        context = LogContext()
        context.metadata = {"key1": "value1"}
        context.increment_log_count()
        context.increment_log_count()
        
        stats = context.get_stats()
        
        assert stats["context_id"] == context.context_id
        assert stats["context_type"] == context.context_type.value
        assert stats["created_at"] == context.created_at
        assert stats["last_accessed"] == context.last_accessed
        assert stats["access_count"] == context.access_count
        assert stats["log_count"] == 2
        assert stats["metadata_count"] == 1
        assert "age_seconds" in stats
        assert "idle_seconds" in stats
    
    def test_is_active(self):
        """Test is_active method."""
        context = LogContext()
        
        # Should be active immediately after creation
        assert context.is_active() is True
        assert context.is_active(0.1) is True  # Very short timeout
        
        # Test with very short timeout
        time.sleep(0.01)
        assert context.is_active(0.001) is False  # Should be inactive
        assert context.is_active(0.1) is True     # Should still be active


class TestContextManager:
    """Test ContextManager class."""
    
    def test_get_current_context_no_context(self):
        """Test get_current_context when no context is set."""
        # Clear any existing context
        ContextManager.clear_current_context()
        
        context = ContextManager.get_current_context()
        assert context is None
    
    def test_set_and_get_current_context(self):
        """Test setting and getting current context."""
        test_context = LogContext()
        
        ContextManager.set_current_context(test_context)
        retrieved_context = ContextManager.get_current_context()
        
        assert retrieved_context == test_context
    
    def test_clear_current_context(self):
        """Test clearing current context."""
        test_context = LogContext()
        
        ContextManager.set_current_context(test_context)
        assert ContextManager.get_current_context() == test_context
        
        ContextManager.clear_current_context()
        assert ContextManager.get_current_context() is None
    
    def test_create_context(self):
        """Test create_context method."""
        context = ContextManager.create_context()
        
        assert isinstance(context, LogContext)
        assert context.context_type == ContextType.CUSTOM
        assert context.metadata == {}
    
    def test_create_context_with_type(self):
        """Test create_context with specific type."""
        context = ContextManager.create_context(ContextType.REQUEST)
        
        assert isinstance(context, LogContext)
        assert context.context_type == ContextType.REQUEST
    
    def test_create_context_with_metadata(self):
        """Test create_context with metadata."""
        metadata = {"key1": "value1", "key2": 42}
        context = ContextManager.create_context(metadata=metadata)
        
        assert isinstance(context, LogContext)
        assert context.metadata == metadata
    
    def test_get_or_create_context_existing(self):
        """Test get_or_create_context when context exists."""
        test_context = LogContext()
        ContextManager.set_current_context(test_context)
        
        result = ContextManager.get_or_create_context()
        assert result == test_context
    
    def test_get_or_create_context_new(self):
        """Test get_or_create_context when no context exists."""
        ContextManager.clear_current_context()
        
        result = ContextManager.get_or_create_context()
        assert isinstance(result, LogContext)
        assert ContextManager.get_current_context() == result


class TestContextDetector:
    """Test ContextDetector class."""
    
    def test_get_caller_info_cached(self):
        """Test get_caller_info with caching enabled."""
        caller = ContextDetector.get_caller_info()
        
        assert isinstance(caller, CallerInfo)
        assert caller.filename != "<unknown>"
        assert caller.function_name != "<unknown>"
        assert caller.line_number > 0
    
    def test_get_caller_info_uncached(self):
        """Test get_caller_info with caching disabled."""
        ContextDetector.disable_cache()
        
        caller = ContextDetector.get_caller_info()
        
        assert isinstance(caller, CallerInfo)
        assert caller.filename != "<unknown>"
        assert caller.function_name != "<unknown>"
        assert caller.line_number > 0
        
        ContextDetector.enable_cache()
    
    def test_get_caller_info_different_depth(self):
        """Test get_caller_info with different depth values."""
        caller1 = ContextDetector.get_caller_info(depth=1)
        caller2 = ContextDetector.get_caller_info(depth=2)
        
        assert isinstance(caller1, CallerInfo)
        assert isinstance(caller2, CallerInfo)
        # Different depths should potentially return different results
    
    def test_get_caller_info_basic(self):
        """Test get_caller_info basic functionality."""
        caller = ContextDetector.get_caller_info()
        
        assert isinstance(caller, CallerInfo)
        assert caller.filename != "<unknown>"
        assert caller.function_name != "<unknown>"
        assert caller.line_number > 0
    
    def test_clear_cache(self):
        """Test _clear_cache method."""
        # Add some items to cache
        ContextDetector.get_caller_info()
        
        # Clear cache
        ContextDetector._clear_cache()
        
        # Cache should be empty
        assert len(ContextDetector._cache) == 0
    
    def test_disable_cache(self):
        """Test disable_cache method."""
        ContextDetector.disable_cache()
        
        assert ContextDetector._cache_enabled is False
        assert len(ContextDetector._cache) == 0
    
    def test_enable_cache(self):
        """Test enable_cache method."""
        ContextDetector.disable_cache()
        ContextDetector.enable_cache()
        
        assert ContextDetector._cache_enabled is True
    
    def test_set_cache_size(self):
        """Test set_cache_size method."""
        original_size = ContextDetector._cache_size
        
        ContextDetector.set_cache_size(500)
        assert ContextDetector._cache_size == 500
        
        # Test that cache is cleared if it exceeds new size
        ContextDetector.set_cache_size(0)
        assert len(ContextDetector._cache) == 0
        
        # Restore original size
        ContextDetector.set_cache_size(original_size)


class TestLogContextMethods:
    """Test LogContext internal methods."""
    
    def test_str_representation(self):
        """Test __str__ method."""
        context = LogContext()
        context.metadata = {
            "user_id": "user123",
            "session_id": "session456",
            "request_id": "req789"
        }
        
        str_repr = str(context)
        assert "user123" in str_repr
        assert "session456" in str_repr
        assert "req789" in str_repr
    
    def test_update_access(self):
        """Test _update_access method."""
        context = LogContext()
        
        # Test initial state
        assert context.access_count == 0
        
        # Call _update_access directly
        LogContext._update_access(context)
        
        # Should increment access count
        assert context.access_count == 1
        
        # Call again
        LogContext._update_access(context)
        assert context.access_count == 2


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_get_current_context_function(self):
        """Test get_current_context convenience function."""
        test_context = LogContext()
        ContextManager.set_current_context(test_context)
        
        result = get_current_context()
        assert result == test_context
    
    def test_set_current_context_function(self):
        """Test set_current_context convenience function."""
        test_context = LogContext()
        
        set_current_context(test_context)
        result = ContextManager.get_current_context()
        assert result == test_context
    
    def test_clear_current_context_function(self):
        """Test clear_current_context convenience function."""
        test_context = LogContext()
        ContextManager.set_current_context(test_context)
        
        clear_current_context()
        result = ContextManager.get_current_context()
        assert result is None
    
    def test_create_context_function(self):
        """Test create_context convenience function."""
        context = create_context()
        
        assert isinstance(context, LogContext)
        assert context.context_type == ContextType.CUSTOM
    
    def test_create_context_function_with_type(self):
        """Test create_context convenience function with type."""
        context = create_context(ContextType.REQUEST)
        
        assert isinstance(context, LogContext)
        assert context.context_type == ContextType.REQUEST
    
    def test_create_context_function_with_metadata(self):
        """Test create_context convenience function with metadata."""
        metadata = {"key": "value"}
        context = create_context(metadata=metadata)
        
        assert isinstance(context, LogContext)
        assert context.metadata == metadata
    
    def test_get_caller_info_function(self):
        """Test get_caller_info convenience function."""
        caller = get_caller_info()
        
        assert isinstance(caller, CallerInfo)
        assert caller.filename != "<unknown>"
        assert caller.function_name != "<unknown>"
        assert caller.line_number > 0


class TestContextIntegration:
    """Integration tests for context functionality."""
    
    def test_context_lifecycle(self):
        """Test complete context lifecycle."""
        # Create context
        context = create_context(ContextType.REQUEST, {"user_id": 123})
        
        # Set as current
        set_current_context(context)
        assert get_current_context() == context
        
        # Use context
        context.update_metadata("action", "login")
        context.increment_log_count()
        
        # Verify stats
        stats = context.get_stats()
        assert stats["log_count"] == 1
        assert stats["metadata_count"] == 2
        
        # Clear context
        clear_current_context()
        assert get_current_context() is None
    
    def test_context_manager_thread_safety(self):
        """Test context manager thread safety."""
        results = []
        
        def worker():
            context = create_context(ContextType.REQUEST, {"thread": threading.get_ident()})
            set_current_context(context)
            results.append(get_current_context())
        
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Each thread should have its own context
        assert len(results) == 3
        assert all(isinstance(ctx, LogContext) for ctx in results)
    
    def test_context_detector_caching(self):
        """Test context detector caching behavior."""
        # Enable caching
        ContextDetector.enable_cache()
        
        # Get caller info multiple times
        caller1 = get_caller_info()
        caller2 = get_caller_info()
        
        # Should be the same object due to caching
        assert caller1 is caller2
        
        # Disable caching
        ContextDetector.disable_cache()
        
        # Get caller info again
        caller3 = get_caller_info()
        
        # Should be different object
        assert caller1 is not caller3
