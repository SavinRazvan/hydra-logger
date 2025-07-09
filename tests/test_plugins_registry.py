"""
Comprehensive tests for plugins registry module.

This module tests all functionality in hydra_logger.plugins.registry
to achieve 100% coverage.
"""

import pytest
import importlib
from unittest.mock import patch, MagicMock

from hydra_logger.plugins.registry import (
    PluginRegistry,
    register_plugin,
    get_plugin,
    list_plugins,
    unregister_plugin,
    load_plugin_from_path,
    clear_plugins
)
from hydra_logger.plugins.base import AnalyticsPlugin, FormatterPlugin, HandlerPlugin
from hydra_logger.core.exceptions import PluginError


class TestPluginRegistry:
    """Test PluginRegistry class."""

    def test_plugin_registry_init(self):
        """Test PluginRegistry initialization."""
        registry = PluginRegistry()
        assert registry._plugins == {}
        assert registry._analytics_plugins == {}
        assert registry._formatter_plugins == {}
        assert registry._handler_plugins == {}

    def test_register_plugin_analytics(self):
        """Test registering analytics plugin."""
        registry = PluginRegistry()
        
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        registry.register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        assert "test_analytics" in registry._plugins
        assert "test_analytics" in registry._analytics_plugins

    def test_register_plugin_formatter(self):
        """Test registering formatter plugin."""
        registry = PluginRegistry()
        
        class TestFormatterPlugin(FormatterPlugin):
            def format(self, record):
                return f"TEST: {record}"
        
        registry.register_plugin("test_formatter", TestFormatterPlugin, "formatter")
        assert "test_formatter" in registry._plugins
        assert "test_formatter" in registry._formatter_plugins

    def test_register_plugin_handler(self):
        """Test registering handler plugin."""
        registry = PluginRegistry()
        
        class TestHandlerPlugin(HandlerPlugin):
            def emit(self, record):
                pass
        
        registry.register_plugin("test_handler", TestHandlerPlugin, "handler")
        assert "test_handler" in registry._plugins
        assert "test_handler" in registry._handler_plugins

    def test_register_plugin_unknown_type(self):
        """Test registering plugin with unknown type."""
        registry = PluginRegistry()
        
        class TestPlugin:
            pass
        
        with pytest.raises(PluginError, match="Unknown plugin type"):
            registry.register_plugin("test", TestPlugin, "unknown")

    def test_register_plugin_error(self):
        """Test registering plugin with error."""
        registry = PluginRegistry()
        
        with pytest.raises(PluginError, match="Failed to register plugin"):
            registry.register_plugin("test", None, "analytics")

    def test_get_plugin_analytics(self):
        """Test getting analytics plugin."""
        registry = PluginRegistry()
        
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        registry.register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        plugin = registry.get_plugin("test_analytics", "analytics")
        assert plugin == TestAnalyticsPlugin

    def test_get_plugin_formatter(self):
        """Test getting formatter plugin."""
        registry = PluginRegistry()
        
        class TestFormatterPlugin(FormatterPlugin):
            def format(self, record):
                return f"TEST: {record}"
        
        registry.register_plugin("test_formatter", TestFormatterPlugin, "formatter")
        plugin = registry.get_plugin("test_formatter", "formatter")
        assert plugin == TestFormatterPlugin

    def test_get_plugin_handler(self):
        """Test getting handler plugin."""
        registry = PluginRegistry()
        
        class TestHandlerPlugin(HandlerPlugin):
            def emit(self, record):
                pass
        
        registry.register_plugin("test_handler", TestHandlerPlugin, "handler")
        plugin = registry.get_plugin("test_handler", "handler")
        assert plugin == TestHandlerPlugin

    def test_get_plugin_not_found(self):
        """Test getting non-existent plugin."""
        registry = PluginRegistry()
        plugin = registry.get_plugin("non_existent", "analytics")
        assert plugin is None

    def test_list_plugins_analytics(self):
        """Test listing analytics plugins."""
        registry = PluginRegistry()
        
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        registry.register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        plugins = registry.list_plugins("analytics")
        assert "test_analytics" in plugins
        assert plugins["test_analytics"] == TestAnalyticsPlugin

    def test_list_plugins_formatter(self):
        """Test listing formatter plugins."""
        registry = PluginRegistry()
        
        class TestFormatterPlugin(FormatterPlugin):
            def format(self, record):
                return f"TEST: {record}"
        
        registry.register_plugin("test_formatter", TestFormatterPlugin, "formatter")
        plugins = registry.list_plugins("formatter")
        assert "test_formatter" in plugins
        assert plugins["test_formatter"] == TestFormatterPlugin

    def test_list_plugins_handler(self):
        """Test listing handler plugins."""
        registry = PluginRegistry()
        
        class TestHandlerPlugin(HandlerPlugin):
            def emit(self, record):
                pass
        
        registry.register_plugin("test_handler", TestHandlerPlugin, "handler")
        plugins = registry.list_plugins("handler")
        assert "test_handler" in plugins
        assert plugins["test_handler"] == TestHandlerPlugin

    def test_list_plugins_all(self):
        """Test listing all plugins."""
        registry = PluginRegistry()
        
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        registry.register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        plugins = registry.list_plugins()
        assert "test_analytics" in plugins
        assert plugins["test_analytics"] == TestAnalyticsPlugin

    def test_unregister_plugin_existing(self):
        """Test unregistering existing plugin."""
        registry = PluginRegistry()
        
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        registry.register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        result = registry.unregister_plugin("test_analytics")
        assert result is True
        assert "test_analytics" not in registry._plugins
        assert "test_analytics" not in registry._analytics_plugins

    def test_unregister_plugin_non_existing(self):
        """Test unregistering non-existing plugin."""
        registry = PluginRegistry()
        result = registry.unregister_plugin("non_existent")
        assert result is False

    def test_load_plugin_from_path_success(self):
        """Test loading plugin from path successfully."""
        registry = PluginRegistry()
        
        # Mock the module import
        mock_module = MagicMock()
        mock_plugin_class = MagicMock()
        mock_module.TestPlugin = mock_plugin_class
        
        with patch('importlib.import_module', return_value=mock_module):
            result = registry.load_plugin_from_path("TestPlugin", "test.module")
            assert result is True
            assert "TestPlugin" in registry._plugins

    def test_load_plugin_from_path_import_error(self):
        """Test loading plugin from path with import error."""
        registry = PluginRegistry()
        
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                registry.load_plugin_from_path("TestPlugin", "test.module")

    def test_load_plugin_from_path_attribute_error(self):
        """Test loading plugin from path with attribute error."""
        registry = PluginRegistry()
        
        mock_module = MagicMock()
        # Simulate missing attribute
        del mock_module.TestPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                registry.load_plugin_from_path("TestPlugin", "test.module")

    def test_load_plugin_from_path_analytics_type(self):
        """Test loading analytics plugin from path."""
        registry = PluginRegistry()
        
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        mock_module = MagicMock()
        mock_module.TestAnalyticsPlugin = TestAnalyticsPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            result = registry.load_plugin_from_path("TestAnalyticsPlugin", "test.module")
            assert result is True
            assert "TestAnalyticsPlugin" in registry._analytics_plugins

    def test_load_plugin_from_path_formatter_type(self):
        """Test loading formatter plugin from path."""
        registry = PluginRegistry()
        
        class TestFormatterPlugin(FormatterPlugin):
            def format(self, record):
                return f"TEST: {record}"
        
        mock_module = MagicMock()
        mock_module.TestFormatterPlugin = TestFormatterPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            result = registry.load_plugin_from_path("TestFormatterPlugin", "test.module")
            assert result is True
            assert "TestFormatterPlugin" in registry._formatter_plugins

    def test_load_plugin_from_path_handler_type(self):
        """Test loading handler plugin from path."""
        registry = PluginRegistry()
        
        class TestHandlerPlugin(HandlerPlugin):
            def emit(self, record):
                pass
        
        mock_module = MagicMock()
        mock_module.TestHandlerPlugin = TestHandlerPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            result = registry.load_plugin_from_path("TestHandlerPlugin", "test.module")
            assert result is True
            assert "TestHandlerPlugin" in registry._handler_plugins

    def test_load_plugin_from_path_default_type(self):
        """Test loading plugin from path with default type."""
        registry = PluginRegistry()
        
        class TestPlugin:
            pass
        
        mock_module = MagicMock()
        mock_module.TestPlugin = TestPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            result = registry.load_plugin_from_path("TestPlugin", "test.module")
            assert result is True
            assert "TestPlugin" in registry._analytics_plugins  # Default type

    def test_clear_plugins(self):
        """Test clearing all plugins."""
        registry = PluginRegistry()
        
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        registry.register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        assert len(registry._plugins) > 0
        
        registry.clear_plugins()
        assert len(registry._plugins) == 0
        assert len(registry._analytics_plugins) == 0
        assert len(registry._formatter_plugins) == 0
        assert len(registry._handler_plugins) == 0


class TestGlobalFunctions:
    """Test global registry functions."""

    def test_register_plugin_global(self):
        """Test global register_plugin function."""
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        register_plugin("test_global", TestAnalyticsPlugin, "analytics")
        
        # Verify it was registered
        plugin = get_plugin("test_global", "analytics")
        assert plugin == TestAnalyticsPlugin

    def test_get_plugin_global(self):
        """Test global get_plugin function."""
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        register_plugin("test_get", TestAnalyticsPlugin, "analytics")
        plugin = get_plugin("test_get", "analytics")
        assert plugin == TestAnalyticsPlugin

    def test_list_plugins_global(self):
        """Test global list_plugins function."""
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        register_plugin("test_list", TestAnalyticsPlugin, "analytics")
        plugins = list_plugins("analytics")
        assert "test_list" in plugins
        assert plugins["test_list"] == TestAnalyticsPlugin

    def test_unregister_plugin_global(self):
        """Test global unregister_plugin function."""
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        register_plugin("test_unregister", TestAnalyticsPlugin, "analytics")
        
        # Verify it was registered
        plugin = get_plugin("test_unregister", "analytics")
        assert plugin == TestAnalyticsPlugin
        
        # Unregister it
        result = unregister_plugin("test_unregister")
        assert result is True
        
        # Verify it was unregistered
        plugin = get_plugin("test_unregister", "analytics")
        assert plugin is None

    def test_load_plugin_from_path_global(self):
        """Test global load_plugin_from_path function."""
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        mock_module = MagicMock()
        mock_module.TestGlobalPlugin = TestAnalyticsPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            result = load_plugin_from_path("TestGlobalPlugin", "test.module")
            assert result is True
            
            # Verify it was loaded
            plugin = get_plugin("TestGlobalPlugin", "analytics")
            assert plugin == TestAnalyticsPlugin

    def test_clear_plugins_global(self):
        """Test global clear_plugins function."""
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        register_plugin("test_clear", TestAnalyticsPlugin, "analytics")
        
        # Verify it was registered
        plugins = list_plugins("analytics")
        assert "test_clear" in plugins
        
        # Clear all plugins
        clear_plugins()
        
        # Verify they were cleared
        plugins = list_plugins("analytics")
        assert "test_clear" not in plugins


class TestPluginRegistryThreadSafety:
    """Test PluginRegistry thread safety."""

    def test_concurrent_registration(self):
        """Test concurrent plugin registration."""
        import threading
        import time
        
        registry = PluginRegistry()
        results = []
        
        def register_plugin_thread(plugin_id):
            class TestPlugin(AnalyticsPlugin):
                def process_event(self, event):
                    return {"id": plugin_id}
                
                def get_insights(self):
                    return {"id": plugin_id}
            
            try:
                registry.register_plugin(f"plugin_{plugin_id}", TestPlugin, "analytics")
                results.append(f"success_{plugin_id}")
            except Exception as e:
                results.append(f"error_{plugin_id}: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_plugin_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all plugins were registered successfully
        assert len(results) == 5
        assert all("success" in result for result in results)
        
        # Verify all plugins are in the registry
        plugins = registry.list_plugins("analytics")
        assert len(plugins) == 5
        for i in range(5):
            assert f"plugin_{i}" in plugins

    def test_concurrent_access(self):
        """Test concurrent access to plugin registry."""
        import threading
        import time
        
        registry = PluginRegistry()
        
        class TestPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"test": "data"}
            
            def get_insights(self):
                return {"test": "insights"}
        
        # Register a plugin
        registry.register_plugin("test_concurrent", TestPlugin, "analytics")
        
        results = []
        
        def access_plugin_thread(thread_id):
            try:
                # Get plugin
                plugin = registry.get_plugin("test_concurrent", "analytics")
                if plugin:
                    results.append(f"success_get_{thread_id}")
                
                # List plugins
                plugins = registry.list_plugins("analytics")
                if "test_concurrent" in plugins:
                    results.append(f"success_list_{thread_id}")
                
            except Exception as e:
                results.append(f"error_{thread_id}: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=access_plugin_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all accesses were successful
        assert len(results) == 20  # 10 threads * 2 operations each
        assert all("success" in result for result in results)


class TestPluginRegistryErrorHandling:
    """Test PluginRegistry error handling."""

    def test_register_plugin_invalid_class(self):
        """Test registering invalid plugin class."""
        registry = PluginRegistry()
        
        with pytest.raises(PluginError, match="Failed to register plugin"):
            registry.register_plugin("invalid", "not_a_class", "analytics")

    def test_register_plugin_exception(self):
        """Test registering plugin with exception."""
        registry = PluginRegistry()
        
        class ProblematicPlugin:
            def __init__(self):
                raise Exception("Initialization error")
        
        with pytest.raises(PluginError, match="Failed to register plugin"):
            registry.register_plugin("problematic", ProblematicPlugin, "analytics")

    def test_load_plugin_from_path_module_error(self):
        """Test loading plugin with module error."""
        registry = PluginRegistry()
        
        with patch('importlib.import_module', side_effect=ModuleNotFoundError("No module named 'test'")):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                registry.load_plugin_from_path("TestPlugin", "test.module")

    def test_load_plugin_from_path_attribute_error(self):
        """Test loading plugin with attribute error."""
        registry = PluginRegistry()
        
        mock_module = MagicMock()
        # Simulate missing attribute
        del mock_module.TestPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                registry.load_plugin_from_path("TestPlugin", "test.module")

    def test_load_plugin_from_path_general_exception(self):
        """Test loading plugin with general exception."""
        registry = PluginRegistry()
        
        with patch('importlib.import_module', side_effect=Exception("General error")):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                registry.load_plugin_from_path("TestPlugin", "test.module") 