"""
Comprehensive tests for plugin registry to achieve 100% coverage.

This module provides complete test coverage for hydra_logger.plugins.registry
including all edge cases, error conditions, and global functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from typing import Type
import re

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


class TestPlugin:
    """Test plugin class for testing."""
    pass


class TestAnalyticsPlugin:
    """Test analytics plugin with process_event method."""
    def process_event(self, event):
        return {"processed": True}


class TestFormatterPlugin:
    """Test formatter plugin with format method."""
    def format(self, record):
        return "formatted"


class TestHandlerPlugin:
    """Test handler plugin with emit method."""
    def emit(self, record):
        return True


class TestPluginRegistryComprehensive:
    """Comprehensive tests for PluginRegistry to achieve 100% coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PluginRegistry()
    
    def test_registry_initialization(self):
        """Test PluginRegistry initialization."""
        assert self.registry is not None
        assert hasattr(self.registry, '_plugins')
        assert hasattr(self.registry, '_analytics_plugins')
        assert hasattr(self.registry, '_formatter_plugins')
        assert hasattr(self.registry, '_handler_plugins')
        assert hasattr(self.registry, '_lock')
    
    def test_register_plugin_all_types(self):
        """Test registering plugins of all types."""
        # Test analytics plugin
        self.registry.register_plugin("analytics_test", TestPlugin, "analytics")
        assert "analytics_test" in self.registry._analytics_plugins
        
        # Test formatter plugin
        self.registry.register_plugin("formatter_test", TestPlugin, "formatter")
        assert "formatter_test" in self.registry._formatter_plugins
        
        # Test handler plugin
        self.registry.register_plugin("handler_test", TestPlugin, "handler")
        assert "handler_test" in self.registry._handler_plugins
        
        # Test that all are in main registry
        assert "analytics_test" in self.registry._plugins
        assert "formatter_test" in self.registry._plugins
        assert "handler_test" in self.registry._plugins
    
    def test_register_plugin_invalid_type(self):
        """Test registering plugin with invalid type."""
        with pytest.raises(PluginError, match="Unknown plugin type: invalid"):
            self.registry.register_plugin("test", TestPlugin, "invalid")
    
    def test_register_plugin_exception_handling(self):
        """Test exception handling during plugin registration."""
        # Mock the analytics_plugins dict to raise an exception when setting an item
        original_analytics_plugins = self.registry._analytics_plugins
        mock_analytics_plugins = MagicMock()
        mock_analytics_plugins.__setitem__ = MagicMock(side_effect=Exception("Test error"))
        self.registry._analytics_plugins = mock_analytics_plugins
        
        try:
            with pytest.raises(PluginError, match="Failed to register plugin 'test': Test error"):
                self.registry.register_plugin("test", TestPlugin, "analytics")
        finally:
            # Restore original
            self.registry._analytics_plugins = original_analytics_plugins
    
    def test_get_plugin_all_types(self):
        """Test getting plugins of all types."""
        # Set up test data
        self.registry._analytics_plugins["analytics_test"] = TestPlugin
        self.registry._formatter_plugins["formatter_test"] = TestPlugin
        self.registry._handler_plugins["handler_test"] = TestPlugin
        self.registry._plugins["general_test"] = TestPlugin
        
        # Test getting by specific type
        assert self.registry.get_plugin("analytics_test", "analytics") == TestPlugin
        assert self.registry.get_plugin("formatter_test", "formatter") == TestPlugin
        assert self.registry.get_plugin("handler_test", "handler") == TestPlugin
        
        # Test fallback to main registry
        assert self.registry.get_plugin("general_test", "unknown") == TestPlugin
        
        # Test non-existent plugin
        assert self.registry.get_plugin("nonexistent", "analytics") is None
    
    def test_list_plugins_all_types(self):
        """Test listing plugins of all types."""
        # Set up test data
        self.registry._analytics_plugins["analytics1"] = TestPlugin
        self.registry._analytics_plugins["analytics2"] = TestPlugin
        self.registry._formatter_plugins["formatter1"] = TestPlugin
        self.registry._handler_plugins["handler1"] = TestPlugin
        self.registry._plugins["general1"] = TestPlugin
        
        # Test listing analytics plugins
        analytics_plugins = self.registry.list_plugins("analytics")
        assert len(analytics_plugins) == 2
        assert "analytics1" in analytics_plugins
        assert "analytics2" in analytics_plugins
        
        # Test listing formatter plugins
        formatter_plugins = self.registry.list_plugins("formatter")
        assert len(formatter_plugins) == 1
        assert "formatter1" in formatter_plugins
        
        # Test listing handler plugins
        handler_plugins = self.registry.list_plugins("handler")
        assert len(handler_plugins) == 1
        assert "handler1" in handler_plugins
        
        # Test listing all plugins
        all_plugins = self.registry.list_plugins()
        assert len(all_plugins) == 1  # Only general1 is in the main registry
        assert "general1" in all_plugins
    
    def test_unregister_plugin_success(self):
        """Test successful plugin unregistration."""
        # Set up test data
        self.registry._plugins["test"] = TestPlugin
        self.registry._analytics_plugins["test"] = TestPlugin
        self.registry._formatter_plugins["test"] = TestPlugin
        self.registry._handler_plugins["test"] = TestPlugin
        
        # Unregister plugin
        result = self.registry.unregister_plugin("test")
        assert result is True
        
        # Verify plugin is removed from all registries
        assert "test" not in self.registry._plugins
        assert "test" not in self.registry._analytics_plugins
        assert "test" not in self.registry._formatter_plugins
        assert "test" not in self.registry._handler_plugins
    
    def test_unregister_plugin_not_found(self):
        """Test unregistering non-existent plugin."""
        result = self.registry.unregister_plugin("nonexistent")
        assert result is False
    
    def test_clear_plugins(self):
        """Test clearing all plugins."""
        # Set up test data
        self.registry._plugins["test1"] = TestPlugin
        self.registry._analytics_plugins["test2"] = TestPlugin
        self.registry._formatter_plugins["test3"] = TestPlugin
        self.registry._handler_plugins["test4"] = TestPlugin
        
        # Clear all plugins
        self.registry.clear_plugins()
        
        # Verify all registries are empty
        assert len(self.registry._plugins) == 0
        assert len(self.registry._analytics_plugins) == 0
        assert len(self.registry._formatter_plugins) == 0
        assert len(self.registry._handler_plugins) == 0
    
    def test_load_plugin_from_path_analytics(self):
        """Test loading analytics plugin from path."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestAnalyticsPlugin = TestAnalyticsPlugin
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestAnalyticsPlugin", "test.module")
            
            assert result is True
            assert "TestAnalyticsPlugin" in self.registry._analytics_plugins
            mock_import.assert_called_once_with("test.module")
    
    def test_load_plugin_from_path_formatter(self):
        """Test loading formatter plugin from path."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestFormatterPlugin = TestFormatterPlugin
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestFormatterPlugin", "test.module")
            
            assert result is True
            assert "TestFormatterPlugin" in self.registry._formatter_plugins
            mock_import.assert_called_once_with("test.module")
    
    def test_load_plugin_from_path_handler(self):
        """Test loading handler plugin from path."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestHandlerPlugin = TestHandlerPlugin
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestHandlerPlugin", "test.module")
            
            assert result is True
            assert "TestHandlerPlugin" in self.registry._handler_plugins
            mock_import.assert_called_once_with("test.module")
    
    def test_load_plugin_from_path_default(self):
        """Test loading plugin with default type detection."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestPlugin = TestPlugin  # No specific methods
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestPlugin", "test.module")
            
            assert result is True
            assert "TestPlugin" in self.registry._analytics_plugins  # Default to analytics
            mock_import.assert_called_once_with("test.module")
    
    def test_load_plugin_from_path_import_error(self):
        """Test loading plugin with import error."""
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            with pytest.raises(PluginError, match="Failed to load plugin 'TestPlugin' from 'test.module': Module not found"):
                self.registry.load_plugin_from_path("TestPlugin", "test.module")
    
    def test_load_plugin_from_path_attribute_error(self):
        """Test loading plugin with attribute error."""
        with patch('importlib.import_module') as mock_import:
            # Create a custom mock that raises AttributeError when getattr is called
            class MockModule:
                def __getattr__(self, name):
                    raise AttributeError("No attribute")
            
            mock_module = MockModule()
            mock_import.return_value = mock_module
            
            with pytest.raises(PluginError, match="Failed to load plugin 'TestPlugin' from 'test.module': No attribute"):
                self.registry.load_plugin_from_path("TestPlugin", "test.module")
    
    def test_load_plugin_from_path_general_exception(self):
        """Test loading plugin with general exception."""
        with patch('importlib.import_module') as mock_import:
            # Create a custom mock that raises Exception when getattr is called
            class MockModule:
                def __getattr__(self, name):
                    raise Exception("General error")
            
            mock_module = MockModule()
            mock_import.return_value = mock_module
            
            with pytest.raises(PluginError, match="Failed to load plugin 'TestPlugin' from 'test.module': General error"):
                self.registry.load_plugin_from_path("TestPlugin", "test.module")
    
    def test_load_plugin_with_complex_exception(self):
        """Test loading plugin with complex exception message."""
        with patch('importlib.import_module') as mock_import:
            complex_error = ValueError("Complex error with special chars: !@#$%^&*()")
            
            # Create a custom mock that raises the complex exception when getattr is called
            class MockModule:
                def __getattr__(self, name):
                    raise complex_error
            
            mock_module = MockModule()
            mock_import.return_value = mock_module
            
            with pytest.raises(PluginError, match=re.escape(f"Failed to load plugin 'TestPlugin' from 'test.module': {complex_error}")):
                self.registry.load_plugin_from_path("TestPlugin", "test.module")
    
    def test_thread_safety(self):
        """Test thread safety of plugin registry."""
        import threading
        
        def register_plugins():
            for i in range(10):
                self.registry.register_plugin(f"plugin_{i}", TestPlugin, "analytics")
        
        def unregister_plugins():
            for i in range(10):
                self.registry.unregister_plugin(f"plugin_{i}")
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            t1 = threading.Thread(target=register_plugins)
            t2 = threading.Thread(target=unregister_plugins)
            threads.extend([t1, t2])
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # Registry should still be functional
        assert hasattr(self.registry, '_plugins')


class TestGlobalRegistryFunctions:
    """Test global registry functions to achieve 100% coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing plugins
        clear_plugins()
    
    def test_register_plugin_global(self):
        """Test global register_plugin function."""
        register_plugin("test_plugin", TestPlugin, "analytics")
        
        # Verify plugin is registered
        plugin = get_plugin("test_plugin", "analytics")
        assert plugin == TestPlugin
    
    def test_get_plugin_global(self):
        """Test global get_plugin function."""
        # Register a plugin
        register_plugin("test_plugin", TestPlugin, "analytics")
        
        # Get the plugin
        plugin = get_plugin("test_plugin", "analytics")
        assert plugin == TestPlugin
        
        # Test non-existent plugin
        plugin = get_plugin("nonexistent", "analytics")
        assert plugin is None
    
    def test_list_plugins_global(self):
        """Test global list_plugins function."""
        # Register plugins
        register_plugin("plugin1", TestPlugin, "analytics")
        register_plugin("plugin2", TestPlugin, "formatter")
        
        # List all plugins
        all_plugins = list_plugins()
        assert len(all_plugins) == 2
        assert "plugin1" in all_plugins
        assert "plugin2" in all_plugins
        
        # List by type
        analytics_plugins = list_plugins("analytics")
        assert len(analytics_plugins) == 1
        assert "plugin1" in analytics_plugins
        
        formatter_plugins = list_plugins("formatter")
        assert len(formatter_plugins) == 1
        assert "plugin2" in formatter_plugins
    
    def test_unregister_plugin_global(self):
        """Test global unregister_plugin function."""
        # Register a plugin
        register_plugin("test_plugin", TestPlugin, "analytics")
        
        # Unregister the plugin
        result = unregister_plugin("test_plugin")
        assert result is True
        
        # Verify plugin is unregistered
        plugin = get_plugin("test_plugin", "analytics")
        assert plugin is None
        
        # Test unregistering non-existent plugin
        result = unregister_plugin("nonexistent")
        assert result is False
    
    def test_load_plugin_from_path_global(self):
        """Test global load_plugin_from_path function."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestPlugin = TestAnalyticsPlugin
            mock_import.return_value = mock_module
            
            result = load_plugin_from_path("TestPlugin", "test.module")
            
            assert result is True
            plugin = get_plugin("TestPlugin", "analytics")
            assert plugin == TestAnalyticsPlugin
    
    def test_clear_plugins_global(self):
        """Test global clear_plugins function."""
        # Register some plugins
        register_plugin("plugin1", TestPlugin, "analytics")
        register_plugin("plugin2", TestPlugin, "formatter")
        
        # Clear all plugins
        clear_plugins()
        
        # Verify all plugins are cleared
        all_plugins = list_plugins()
        assert len(all_plugins) == 0
        
        analytics_plugins = list_plugins("analytics")
        assert len(analytics_plugins) == 0
        
        formatter_plugins = list_plugins("formatter")
        assert len(formatter_plugins) == 0


class TestRegistryEdgeCases:
    """Test edge cases and error conditions for 100% coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PluginRegistry()
    
    def test_register_plugin_with_exception_in_registration(self):
        """Test registration when an exception occurs during the registration process."""
        # Create a mock that raises an exception when __setitem__ is called
        original_dict = self.registry._analytics_plugins
        mock_dict = MagicMock()
        mock_dict.__setitem__ = MagicMock(side_effect=Exception("Registration failed"))
        mock_dict.__getitem__ = original_dict.__getitem__
        mock_dict.get = original_dict.get
        mock_dict.copy = original_dict.copy
        mock_dict.clear = original_dict.clear
        
        with patch.object(self.registry, '_analytics_plugins', mock_dict):
            with pytest.raises(PluginError, match="Failed to register plugin 'test': Registration failed"):
                self.registry.register_plugin("test", TestPlugin, "analytics")
    
    def test_get_plugin_with_unknown_type(self):
        """Test getting plugin with unknown type."""
        # Register a plugin in the main registry
        self.registry._plugins["test"] = TestPlugin
        
        # Get plugin with unknown type (should fall back to main registry)
        plugin = self.registry.get_plugin("test", "unknown")
        assert plugin == TestPlugin
    
    def test_list_plugins_with_unknown_type(self):
        """Test listing plugins with unknown type."""
        # Register plugins
        self.registry._plugins["test1"] = TestPlugin
        self.registry._plugins["test2"] = TestPlugin
        
        # List plugins with unknown type (should return all plugins)
        plugins = self.registry.list_plugins("unknown")
        assert len(plugins) == 2
        assert "test1" in plugins
        assert "test2" in plugins
    
    def test_unregister_plugin_partial_registration(self):
        """Test unregistering plugin that exists in main registry but not in type-specific registry."""
        # Register only in main registry
        self.registry._plugins["test"] = TestPlugin
        
        # Unregister should succeed
        result = self.registry.unregister_plugin("test")
        assert result is True
        assert "test" not in self.registry._plugins
    
    def test_concurrent_access_simulation(self):
        """Test concurrent access simulation for thread safety."""
        import threading
        import time
        
        results = []
        
        def worker(worker_id):
            """Worker function for concurrent access testing."""
            try:
                # Register a plugin
                self.registry.register_plugin(f"worker_{worker_id}", TestPlugin, "analytics")
                time.sleep(0.01)  # Simulate work
                
                # Get the plugin
                plugin = self.registry.get_plugin(f"worker_{worker_id}", "analytics")
                results.append(plugin is not None)
                
                # Unregister the plugin
                self.registry.unregister_plugin(f"worker_{worker_id}")
                
            except Exception as e:
                results.append(False)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for all threads to complete
        for t in threads:
            t.join()
        
        # All operations should have succeeded
        assert all(results)
        assert len(results) == 10 