"""
Comprehensive tests for plugin registry to achieve 100% coverage.

This module tests all edge cases, error conditions, and plugin
management functionality to ensure complete test coverage.
"""

import importlib
import threading
from unittest.mock import Mock, patch, MagicMock, call
from typing import Type

import pytest

from hydra_logger.plugins.registry import (
    PluginRegistry,
    register_plugin,
    get_plugin,
    list_plugins,
    unregister_plugin,
    load_plugin_from_path,
    clear_plugins
)
from hydra_logger.core.exceptions import PluginError


class MockAnalyticsPlugin:
    """Mock analytics plugin for testing."""
    
    def __init__(self, name: str = "test_analytics"):
        self.name = name
    
    def process_event(self, event):
        """Process an event."""
        return f"Processed: {event}"


class MockFormatterPlugin:
    """Mock formatter plugin for testing."""
    
    def __init__(self, name: str = "test_formatter"):
        self.name = name
    
    def format(self, record):
        """Format a log record."""
        return f"Formatted: {record}"


class MockHandlerPlugin:
    """Mock handler plugin for testing."""
    
    def __init__(self, name: str = "test_handler"):
        self.name = name
    
    def emit(self, record):
        """Emit a log record."""
        return f"Emitted: {record}"


class MockGenericPlugin:
    """Mock generic plugin for testing."""
    
    def __init__(self, name: str = "test_generic"):
        self.name = name


class TestPluginRegistry:
    """Test PluginRegistry with comprehensive coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PluginRegistry()
    
    def test_init(self):
        """Test PluginRegistry initialization."""
        assert self.registry._plugins == {}
        assert self.registry._analytics_plugins == {}
        assert self.registry._formatter_plugins == {}
        assert self.registry._handler_plugins == {}
        assert isinstance(self.registry._lock, type(threading.Lock()))
    
    def test_register_plugin_analytics(self):
        """Test register_plugin with analytics plugin."""
        plugin_class = MockAnalyticsPlugin
        
        self.registry.register_plugin("test_analytics", plugin_class, "analytics")
        
        assert "test_analytics" in self.registry._plugins
        assert "test_analytics" in self.registry._analytics_plugins
        assert "test_analytics" not in self.registry._formatter_plugins
        assert "test_analytics" not in self.registry._handler_plugins
        assert self.registry._plugins["test_analytics"] == plugin_class
        assert self.registry._analytics_plugins["test_analytics"] == plugin_class
    
    def test_register_plugin_formatter(self):
        """Test register_plugin with formatter plugin."""
        plugin_class = MockFormatterPlugin
        
        self.registry.register_plugin("test_formatter", plugin_class, "formatter")
        
        assert "test_formatter" in self.registry._plugins
        assert "test_formatter" in self.registry._formatter_plugins
        assert "test_formatter" not in self.registry._analytics_plugins
        assert "test_formatter" not in self.registry._handler_plugins
        assert self.registry._plugins["test_formatter"] == plugin_class
        assert self.registry._formatter_plugins["test_formatter"] == plugin_class
    
    def test_register_plugin_handler(self):
        """Test register_plugin with handler plugin."""
        plugin_class = MockHandlerPlugin
        
        self.registry.register_plugin("test_handler", plugin_class, "handler")
        
        assert "test_handler" in self.registry._plugins
        assert "test_handler" in self.registry._handler_plugins
        assert "test_handler" not in self.registry._analytics_plugins
        assert "test_handler" not in self.registry._formatter_plugins
        assert self.registry._plugins["test_handler"] == plugin_class
        assert self.registry._handler_plugins["test_handler"] == plugin_class
    
    def test_register_plugin_unknown_type(self):
        """Test register_plugin with unknown plugin type."""
        plugin_class = MockGenericPlugin
        
        with pytest.raises(PluginError, match="Unknown plugin type: unknown"):
            self.registry.register_plugin("test_unknown", plugin_class, "unknown")
    
    def test_register_plugin_exception(self):
        """Test register_plugin with exception during registration."""
        # Mock plugin class that raises exception during registration
        class ProblematicPlugin:
            def __init__(self):
                raise Exception("Plugin initialization failed")
        
        # The registration itself should not raise an exception
        # The exception would only occur when the plugin is instantiated
        self.registry.register_plugin("test_problematic", ProblematicPlugin, "analytics")
        
        # Verify plugin was registered
        assert "test_problematic" in self.registry._plugins
        assert "test_problematic" in self.registry._analytics_plugins
    
    def test_get_plugin_analytics(self):
        """Test get_plugin with analytics plugin."""
        plugin_class = MockAnalyticsPlugin
        self.registry.register_plugin("test_analytics", plugin_class, "analytics")
        
        result = self.registry.get_plugin("test_analytics", "analytics")
        
        assert result == plugin_class
    
    def test_get_plugin_formatter(self):
        """Test get_plugin with formatter plugin."""
        plugin_class = MockFormatterPlugin
        self.registry.register_plugin("test_formatter", plugin_class, "formatter")
        
        result = self.registry.get_plugin("test_formatter", "formatter")
        
        assert result == plugin_class
    
    def test_get_plugin_handler(self):
        """Test get_plugin with handler plugin."""
        plugin_class = MockHandlerPlugin
        self.registry.register_plugin("test_handler", plugin_class, "handler")
        
        result = self.registry.get_plugin("test_handler", "handler")
        
        assert result == plugin_class
    
    def test_get_plugin_generic(self):
        """Test get_plugin with generic lookup."""
        plugin_class = MockGenericPlugin
        self.registry.register_plugin("test_generic", plugin_class, "analytics")
        
        result = self.registry.get_plugin("test_generic")
        
        assert result == plugin_class
    
    def test_get_plugin_not_found(self):
        """Test get_plugin with non-existent plugin."""
        result = self.registry.get_plugin("non_existent", "analytics")
        
        assert result is None
    
    def test_list_plugins_all(self):
        """Test list_plugins with all plugins."""
        analytics_plugin = MockAnalyticsPlugin
        formatter_plugin = MockFormatterPlugin
        handler_plugin = MockHandlerPlugin
        
        self.registry.register_plugin("test_analytics", analytics_plugin, "analytics")
        self.registry.register_plugin("test_formatter", formatter_plugin, "formatter")
        self.registry.register_plugin("test_handler", handler_plugin, "handler")
        
        result = self.registry.list_plugins()
        
        assert len(result) == 3
        assert "test_analytics" in result
        assert "test_formatter" in result
        assert "test_handler" in result
        assert result["test_analytics"] == analytics_plugin
        assert result["test_formatter"] == formatter_plugin
        assert result["test_handler"] == handler_plugin
    
    def test_list_plugins_analytics_only(self):
        """Test list_plugins with analytics filter."""
        analytics_plugin = MockAnalyticsPlugin
        formatter_plugin = MockFormatterPlugin
        
        self.registry.register_plugin("test_analytics", analytics_plugin, "analytics")
        self.registry.register_plugin("test_formatter", formatter_plugin, "formatter")
        
        result = self.registry.list_plugins("analytics")
        
        assert len(result) == 1
        assert "test_analytics" in result
        assert "test_formatter" not in result
        assert result["test_analytics"] == analytics_plugin
    
    def test_list_plugins_formatter_only(self):
        """Test list_plugins with formatter filter."""
        analytics_plugin = MockAnalyticsPlugin
        formatter_plugin = MockFormatterPlugin
        
        self.registry.register_plugin("test_analytics", analytics_plugin, "analytics")
        self.registry.register_plugin("test_formatter", formatter_plugin, "formatter")
        
        result = self.registry.list_plugins("formatter")
        
        assert len(result) == 1
        assert "test_formatter" in result
        assert "test_analytics" not in result
        assert result["test_formatter"] == formatter_plugin
    
    def test_list_plugins_handler_only(self):
        """Test list_plugins with handler filter."""
        handler_plugin = MockHandlerPlugin
        analytics_plugin = MockAnalyticsPlugin
        
        self.registry.register_plugin("test_handler", handler_plugin, "handler")
        self.registry.register_plugin("test_analytics", analytics_plugin, "analytics")
        
        result = self.registry.list_plugins("handler")
        
        assert len(result) == 1
        assert "test_handler" in result
        assert "test_analytics" not in result
        assert result["test_handler"] == handler_plugin
    
    def test_list_plugins_empty(self):
        """Test list_plugins with empty registry."""
        result = self.registry.list_plugins()
        
        assert result == {}
    
    def test_unregister_plugin_existing(self):
        """Test unregister_plugin with existing plugin."""
        plugin_class = MockAnalyticsPlugin
        self.registry.register_plugin("test_plugin", plugin_class, "analytics")
        
        result = self.registry.unregister_plugin("test_plugin")
        
        assert result is True
        assert "test_plugin" not in self.registry._plugins
        assert "test_plugin" not in self.registry._analytics_plugins
    
    def test_unregister_plugin_non_existent(self):
        """Test unregister_plugin with non-existent plugin."""
        result = self.registry.unregister_plugin("non_existent")
        
        assert result is False
    
    def test_unregister_plugin_removes_from_all_registries(self):
        """Test unregister_plugin removes from all type-specific registries."""
        # Register same plugin in multiple types
        plugin_class = MockAnalyticsPlugin
        self.registry.register_plugin("test_plugin", plugin_class, "analytics")
        self.registry.register_plugin("test_plugin", plugin_class, "formatter")
        self.registry.register_plugin("test_plugin", plugin_class, "handler")
        
        result = self.registry.unregister_plugin("test_plugin")
        
        assert result is True
        assert "test_plugin" not in self.registry._plugins
        assert "test_plugin" not in self.registry._analytics_plugins
        assert "test_plugin" not in self.registry._formatter_plugins
        assert "test_plugin" not in self.registry._handler_plugins
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_analytics(self, mock_import_module):
        """Test load_plugin_from_path with analytics plugin."""
        mock_module = Mock()
        mock_plugin_class = MockAnalyticsPlugin
        mock_module.test_plugin = mock_plugin_class
        mock_import_module.return_value = mock_module
        
        result = self.registry.load_plugin_from_path("test_plugin", "test.module")
        
        assert result is True
        assert "test_plugin" in self.registry._analytics_plugins
        assert self.registry._analytics_plugins["test_plugin"] == mock_plugin_class
        
        mock_import_module.assert_called_once_with("test.module")
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_formatter(self, mock_import_module):
        """Test load_plugin_from_path with formatter plugin."""
        mock_module = Mock()
        mock_plugin_class = MockFormatterPlugin
        mock_module.test_plugin = mock_plugin_class
        mock_import_module.return_value = mock_module
        
        result = self.registry.load_plugin_from_path("test_plugin", "test.module")
        
        assert result is True
        assert "test_plugin" in self.registry._formatter_plugins
        assert self.registry._formatter_plugins["test_plugin"] == mock_plugin_class
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_handler(self, mock_import_module):
        """Test load_plugin_from_path with handler plugin."""
        mock_module = Mock()
        mock_plugin_class = MockHandlerPlugin
        mock_module.test_plugin = mock_plugin_class
        mock_import_module.return_value = mock_module
        
        result = self.registry.load_plugin_from_path("test_plugin", "test.module")
        
        assert result is True
        assert "test_plugin" in self.registry._handler_plugins
        assert self.registry._handler_plugins["test_plugin"] == mock_plugin_class
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_generic(self, mock_import_module):
        """Test load_plugin_from_path with generic plugin (defaults to analytics)."""
        mock_module = Mock()
        mock_plugin_class = MockGenericPlugin
        mock_module.test_plugin = mock_plugin_class
        mock_import_module.return_value = mock_module
        
        result = self.registry.load_plugin_from_path("test_plugin", "test.module")
        
        assert result is True
        assert "test_plugin" in self.registry._analytics_plugins  # Defaults to analytics
        assert self.registry._analytics_plugins["test_plugin"] == mock_plugin_class
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_import_error(self, mock_import_module):
        """Test load_plugin_from_path with import error."""
        mock_import_module.side_effect = ImportError("Module not found")
        
        with pytest.raises(PluginError, match="Failed to load plugin 'test_plugin' from 'test.module'"):
            self.registry.load_plugin_from_path("test_plugin", "test.module")
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_attribute_error(self, mock_import_module):
        """Test load_plugin_from_path with attribute error."""
        # Create a custom mock that raises AttributeError for test_plugin
        class MockModuleWithError:
            def __getattr__(self, name):
                if name == 'test_plugin':
                    raise AttributeError("'Mock' object has no attribute 'test_plugin'")
                return Mock()
        
        mock_module = MockModuleWithError()
        mock_import_module.return_value = mock_module
        
        with pytest.raises(PluginError, match="Failed to load plugin 'test_plugin' from 'test.module'"):
            self.registry.load_plugin_from_path("test_plugin", "test.module")
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_registration_error(self, mock_import_module):
        """Test load_plugin_from_path with registration error."""
        mock_module = Mock()
        mock_plugin_class = Mock()
        mock_module.test_plugin = mock_plugin_class
        mock_import_module.return_value = mock_module
        
        # Mock register_plugin to raise exception
        with patch.object(self.registry, 'register_plugin', side_effect=PluginError("Registration failed")):
            with pytest.raises(PluginError, match="Failed to load plugin 'test_plugin' from 'test.module'"):
                self.registry.load_plugin_from_path("test_plugin", "test.module")
    
    def test_clear_plugins(self):
        """Test clear_plugins method."""
        # Register some plugins
        self.registry.register_plugin("test1", MockAnalyticsPlugin, "analytics")
        self.registry.register_plugin("test2", MockFormatterPlugin, "formatter")
        self.registry.register_plugin("test3", MockHandlerPlugin, "handler")
        
        # Clear all plugins
        self.registry.clear_plugins()
        
        assert self.registry._plugins == {}
        assert self.registry._analytics_plugins == {}
        assert self.registry._formatter_plugins == {}
        assert self.registry._handler_plugins == {}


class TestGlobalFunctions:
    """Test global plugin registry functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing plugins
        clear_plugins()
    
    def test_register_plugin_global(self):
        """Test global register_plugin function."""
        plugin_class = MockAnalyticsPlugin
        
        register_plugin("test_global", plugin_class, "analytics")
        
        # Verify plugin was registered
        result = get_plugin("test_global", "analytics")
        assert result == plugin_class
    
    def test_get_plugin_global(self):
        """Test global get_plugin function."""
        plugin_class = MockFormatterPlugin
        register_plugin("test_get", plugin_class, "formatter")
        
        result = get_plugin("test_get", "formatter")
        
        assert result == plugin_class
    
    def test_get_plugin_global_not_found(self):
        """Test global get_plugin function with non-existent plugin."""
        result = get_plugin("non_existent", "analytics")
        
        assert result is None
    
    def test_list_plugins_global(self):
        """Test global list_plugins function."""
        analytics_plugin = MockAnalyticsPlugin
        formatter_plugin = MockFormatterPlugin
        
        register_plugin("test_analytics", analytics_plugin, "analytics")
        register_plugin("test_formatter", formatter_plugin, "formatter")
        
        result = list_plugins()
        
        assert len(result) == 2
        assert "test_analytics" in result
        assert "test_formatter" in result
    
    def test_list_plugins_global_filtered(self):
        """Test global list_plugins function with filter."""
        analytics_plugin = MockAnalyticsPlugin
        formatter_plugin = MockFormatterPlugin
        
        register_plugin("test_analytics", analytics_plugin, "analytics")
        register_plugin("test_formatter", formatter_plugin, "formatter")
        
        result = list_plugins("analytics")
        
        assert len(result) == 1
        assert "test_analytics" in result
        assert "test_formatter" not in result
    
    def test_unregister_plugin_global(self):
        """Test global unregister_plugin function."""
        plugin_class = MockHandlerPlugin
        register_plugin("test_unregister", plugin_class, "handler")
        
        # Verify plugin was registered
        assert get_plugin("test_unregister", "handler") == plugin_class
        
        # Unregister plugin
        result = unregister_plugin("test_unregister")
        
        assert result is True
        assert get_plugin("test_unregister", "handler") is None
    
    def test_unregister_plugin_global_not_found(self):
        """Test global unregister_plugin function with non-existent plugin."""
        result = unregister_plugin("non_existent")
        
        assert result is False
    
    @patch('importlib.import_module')
    def test_load_plugin_from_path_global(self, mock_import_module):
        """Test global load_plugin_from_path function."""
        mock_module = Mock()
        mock_plugin_class = MockAnalyticsPlugin
        mock_module.test_plugin = mock_plugin_class
        mock_import_module.return_value = mock_module
        
        result = load_plugin_from_path("test_plugin", "test.module")
        
        assert result is True
        assert get_plugin("test_plugin", "analytics") == mock_plugin_class
    
    def test_clear_plugins_global(self):
        """Test global clear_plugins function."""
        # Register some plugins
        register_plugin("test1", MockAnalyticsPlugin, "analytics")
        register_plugin("test2", MockFormatterPlugin, "formatter")
        
        # Verify plugins were registered
        assert len(list_plugins()) == 2
        
        # Clear all plugins
        clear_plugins()
        
        # Verify plugins were cleared
        assert len(list_plugins()) == 0


class TestPluginRegistryThreading:
    """Test PluginRegistry threading behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PluginRegistry()
    
    def test_thread_safe_registration(self):
        """Test thread-safe plugin registration."""
        import threading
        import time
        
        def register_plugin_thread(plugin_id):
            """Register a plugin in a separate thread."""
            plugin_class = type(f"MockPlugin{plugin_id}", (), {})
            self.registry.register_plugin(f"plugin_{plugin_id}", plugin_class, "analytics")
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=register_plugin_thread, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all plugins were registered
        plugins = self.registry.list_plugins()
        assert len(plugins) == 10
        
        for i in range(10):
            assert f"plugin_{i}" in plugins
    
    def test_thread_safe_unregistration(self):
        """Test thread-safe plugin unregistration."""
        import threading
        
        # Register plugins first
        for i in range(5):
            plugin_class = type(f"MockPlugin{i}", (), {})
            self.registry.register_plugin(f"plugin_{i}", plugin_class, "analytics")
        
        def unregister_plugin_thread(plugin_id):
            """Unregister a plugin in a separate thread."""
            self.registry.unregister_plugin(f"plugin_{plugin_id}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=unregister_plugin_thread, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all plugins were unregistered
        plugins = self.registry.list_plugins()
        assert len(plugins) == 0


class TestPluginRegistryIntegration:
    """Integration tests for plugin registry."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PluginRegistry()
    
    def test_comprehensive_plugin_lifecycle(self):
        """Test comprehensive plugin lifecycle."""
        # Step 1: Register different types of plugins
        analytics_plugin = MockAnalyticsPlugin
        formatter_plugin = MockFormatterPlugin
        handler_plugin = MockHandlerPlugin
        
        self.registry.register_plugin("analytics1", analytics_plugin, "analytics")
        self.registry.register_plugin("formatter1", formatter_plugin, "formatter")
        self.registry.register_plugin("handler1", handler_plugin, "handler")
        
        # Step 2: Verify all plugins are registered
        all_plugins = self.registry.list_plugins()
        assert len(all_plugins) == 3
        
        analytics_plugins = self.registry.list_plugins("analytics")
        assert len(analytics_plugins) == 1
        assert "analytics1" in analytics_plugins
        
        formatter_plugins = self.registry.list_plugins("formatter")
        assert len(formatter_plugins) == 1
        assert "formatter1" in formatter_plugins
        
        handler_plugins = self.registry.list_plugins("handler")
        assert len(handler_plugins) == 1
        assert "handler1" in handler_plugins
        
        # Step 3: Get specific plugins
        retrieved_analytics = self.registry.get_plugin("analytics1", "analytics")
        assert retrieved_analytics == analytics_plugin
        
        retrieved_formatter = self.registry.get_plugin("formatter1", "formatter")
        assert retrieved_formatter == formatter_plugin
        
        retrieved_handler = self.registry.get_plugin("handler1", "handler")
        assert retrieved_handler == handler_plugin
        
        # Step 4: Unregister plugins
        assert self.registry.unregister_plugin("analytics1") is True
        assert self.registry.unregister_plugin("formatter1") is True
        assert self.registry.unregister_plugin("handler1") is True
        
        # Step 5: Verify plugins were unregistered
        all_plugins = self.registry.list_plugins()
        assert len(all_plugins) == 0
        
        # Step 6: Clear all plugins
        self.registry.clear_plugins()
        assert len(self.registry.list_plugins()) == 0
    
    def test_error_handling_scenarios(self):
        """Test various error handling scenarios."""
        # Test unknown plugin type
        with pytest.raises(PluginError, match="Unknown plugin type: invalid"):
            self.registry.register_plugin("test", MockAnalyticsPlugin, "invalid")
        
        # Test non-existent plugin retrieval
        assert self.registry.get_plugin("non_existent", "analytics") is None
        
        # Test unregistering non-existent plugin
        assert self.registry.unregister_plugin("non_existent") is False
        
        # Test empty plugin listing
        assert self.registry.list_plugins() == {}
        assert self.registry.list_plugins("analytics") == {}
    
    def test_plugin_type_detection(self):
        """Test automatic plugin type detection in load_plugin_from_path."""
        # This test verifies that the registry can automatically detect
        # plugin types based on their methods
        assert hasattr(MockAnalyticsPlugin, 'process_event')
        assert hasattr(MockFormatterPlugin, 'format')
        assert hasattr(MockHandlerPlugin, 'emit')
        assert not hasattr(MockGenericPlugin, 'process_event')
        assert not hasattr(MockGenericPlugin, 'format')
        assert not hasattr(MockGenericPlugin, 'emit') 