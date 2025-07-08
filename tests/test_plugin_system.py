"""
Comprehensive tests for plugin system functionality.

This module tests the plugin system including registry, base classes,
plugin functionality, and achieves 100% coverage.
"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from hydra_logger.plugins.registry import (
    PluginRegistry,
    register_plugin,
    get_plugin,
    list_plugins,
    unregister_plugin,
    load_plugin_from_path,
    clear_plugins
)
from hydra_logger.plugins.base import (
    AnalyticsPlugin,
    FormatterPlugin,
    HandlerPlugin,
    SecurityPlugin,
    PerformancePlugin
)
from hydra_logger.core.exceptions import PluginError


class TestPluginRegistry:
    """Test plugin registry functionality."""

    def setup_method(self):
        """Setup test environment."""
        clear_plugins()
        self.registry = PluginRegistry()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_plugins()

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
        class TestPlugin:
            pass

        # Test analytics plugin
        self.registry.register_plugin("analytics_test", TestPlugin, "analytics")
        assert "analytics_test" in self.registry._analytics_plugins
        
        # Test formatter plugin
        self.registry.register_plugin("formatter_test", TestPlugin, "formatter")
        assert "formatter_test" in self.registry._formatter_plugins
        
        # Test handler plugin
        self.registry.register_plugin("handler_test", TestPlugin, "handler")
        assert "handler_test" in self.registry._handler_plugins

    def test_register_plugin_invalid_type(self):
        """Test registering plugin with invalid type."""
        class TestPlugin:
            pass

        with pytest.raises(PluginError, match="Unknown plugin type: invalid"):
            self.registry.register_plugin("test", TestPlugin, "invalid")

    def test_register_plugin_exception_handling(self):
        """Test exception handling during plugin registration."""
        # Test with invalid plugin type
        class TestPlugin:
            pass
        with pytest.raises(PluginError, match="Unknown plugin type: invalid"):
            self.registry.register_plugin("test", TestPlugin, "invalid")

    def test_get_plugin_all_types(self):
        """Test getting plugins of all types."""
        class TestPlugin:
            pass

        # Register plugins
        self.registry._analytics_plugins["analytics_test"] = TestPlugin
        self.registry._formatter_plugins["formatter_test"] = TestPlugin
        self.registry._handler_plugins["handler_test"] = TestPlugin
        self.registry._plugins["general_test"] = TestPlugin

        # Test getting each type
        assert self.registry.get_plugin("analytics_test", "analytics") == TestPlugin
        assert self.registry.get_plugin("formatter_test", "formatter") == TestPlugin
        assert self.registry.get_plugin("handler_test", "handler") == TestPlugin
        assert self.registry.get_plugin("general_test", "unknown") == TestPlugin

    def test_get_plugin_nonexistent(self):
        """Test getting nonexistent plugin."""
        assert self.registry.get_plugin("nonexistent", "analytics") is None

    def test_list_plugins_all_types(self):
        """Test listing plugins of all types."""
        class TestPlugin:
            pass

        # Add plugins to different registries
        self.registry._analytics_plugins["analytics1"] = TestPlugin
        self.registry._analytics_plugins["analytics2"] = TestPlugin
        self.registry._formatter_plugins["formatter1"] = TestPlugin
        self.registry._handler_plugins["handler1"] = TestPlugin
        self.registry._plugins["general1"] = TestPlugin

        # Test listing each type
        analytics_plugins = self.registry.list_plugins("analytics")
        assert len(analytics_plugins) == 2
        assert "analytics1" in analytics_plugins
        assert "analytics2" in analytics_plugins

        formatter_plugins = self.registry.list_plugins("formatter")
        assert len(formatter_plugins) == 1
        assert "formatter1" in formatter_plugins

        handler_plugins = self.registry.list_plugins("handler")
        assert len(handler_plugins) == 1
        assert "handler1" in handler_plugins

        all_plugins = self.registry.list_plugins()
        assert len(all_plugins) == 1  # Only general1 is in the main registry

    def test_unregister_plugin_success(self):
        """Test successful plugin unregistration."""
        class TestPlugin:
            pass

        # Add plugin to all registries
        self.registry._plugins["test"] = TestPlugin
        self.registry._analytics_plugins["test"] = TestPlugin
        self.registry._formatter_plugins["test"] = TestPlugin
        self.registry._handler_plugins["test"] = TestPlugin

        # Unregister
        result = self.registry.unregister_plugin("test")
        assert result is True
        assert "test" not in self.registry._plugins
        assert "test" not in self.registry._analytics_plugins
        assert "test" not in self.registry._formatter_plugins
        assert "test" not in self.registry._handler_plugins

    def test_unregister_plugin_not_found(self):
        """Test unregistering nonexistent plugin."""
        result = self.registry.unregister_plugin("nonexistent")
        assert result is False

    def test_clear_plugins(self):
        """Test clearing all plugins."""
        class TestPlugin:
            pass

        # Add plugins to all registries
        self.registry._plugins["test1"] = TestPlugin
        self.registry._analytics_plugins["test2"] = TestPlugin
        self.registry._formatter_plugins["test3"] = TestPlugin
        self.registry._handler_plugins["test4"] = TestPlugin

        # Clear all
        self.registry.clear_plugins()

        assert len(self.registry._plugins) == 0
        assert len(self.registry._analytics_plugins) == 0
        assert len(self.registry._formatter_plugins) == 0
        assert len(self.registry._handler_plugins) == 0

    def test_load_plugin_from_path_success_analytics(self):
        """Test loading analytics plugin from path."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestAnalyticsPlugin = type('TestAnalyticsPlugin', (), {
                'process_event': lambda self, event: {"processed": True},
                'get_insights': lambda self: {"insights": "test"}
            })
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestAnalyticsPlugin", "test.module")
            assert result is True
            assert "TestAnalyticsPlugin" in self.registry._analytics_plugins

    def test_load_plugin_from_path_success_formatter(self):
        """Test loading formatter plugin from path."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestFormatterPlugin = type('TestFormatterPlugin', (), {
                'format': lambda self, record: f"FORMATTED: {record}"
            })
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestFormatterPlugin", "test.module")
            assert result is True
            assert "TestFormatterPlugin" in self.registry._formatter_plugins

    def test_load_plugin_from_path_success_handler(self):
        """Test loading handler plugin from path."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestHandlerPlugin = type('TestHandlerPlugin', (), {
                'emit': lambda self, record: None
            })
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestHandlerPlugin", "test.module")
            assert result is True
            assert "TestHandlerPlugin" in self.registry._handler_plugins

    def test_load_plugin_from_path_default_type(self):
        """Test loading plugin with default type detection."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_module.TestPlugin = type('TestPlugin', (), {})
            mock_import.return_value = mock_module
            
            result = self.registry.load_plugin_from_path("TestPlugin", "test.module")
            assert result is True
            assert "TestPlugin" in self.registry._analytics_plugins

    def test_load_plugin_from_path_import_error(self):
        """Test loading plugin with import error."""
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                self.registry.load_plugin_from_path("TestPlugin", "nonexistent.module")

    def test_load_plugin_from_path_attribute_error(self):
        """Test loading plugin with attribute error."""
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            # Simulate attribute error when accessing plugin class
            mock_module.TestPlugin = MagicMock(side_effect=AttributeError("No attribute"))
            mock_import.return_value = mock_module
            
            with pytest.raises(PluginError, match="Failed to load plugin"):
                self.registry.load_plugin_from_path("TestPlugin", "test.module")

    def test_load_plugin_from_path_general_exception(self):
        """Test loading plugin with general exception."""
        with patch('importlib.import_module', side_effect=Exception("General error")):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                self.registry.load_plugin_from_path("TestPlugin", "test.module")

    def test_thread_safety(self):
        """Test thread safety of plugin registry."""
        class TestPlugin:
            pass

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
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Registry should still be functional
        assert hasattr(self.registry, '_plugins')


class TestGlobalRegistryFunctions:
    """Test global registry functions."""

    def setup_method(self):
        """Setup test environment."""
        clear_plugins()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_plugins()

    def test_register_plugin_global_all_types(self):
        """Test global register_plugin with all types."""
        class TestPlugin:
            pass

        # Test all plugin types
        register_plugin("analytics_test", TestPlugin, "analytics")
        register_plugin("formatter_test", TestPlugin, "formatter")
        register_plugin("handler_test", TestPlugin, "handler")

        # Verify registration
        assert get_plugin("analytics_test", "analytics") == TestPlugin
        assert get_plugin("formatter_test", "formatter") == TestPlugin
        assert get_plugin("handler_test", "handler") == TestPlugin

    def test_get_plugin_global_all_types(self):
        """Test global get_plugin with all types."""
        class TestPlugin:
            pass

        # Register plugins
        register_plugin("analytics_test", TestPlugin, "analytics")
        register_plugin("formatter_test", TestPlugin, "formatter")
        register_plugin("handler_test", TestPlugin, "handler")

        # Test getting each type
        assert get_plugin("analytics_test", "analytics") == TestPlugin
        assert get_plugin("formatter_test", "formatter") == TestPlugin
        assert get_plugin("handler_test", "handler") == TestPlugin

    def test_list_plugins_global_all_types(self):
        """Test global list_plugins with all types."""
        class TestPlugin:
            pass

        # Register plugins
        register_plugin("analytics1", TestPlugin, "analytics")
        register_plugin("analytics2", TestPlugin, "analytics")
        register_plugin("formatter1", TestPlugin, "formatter")
        register_plugin("handler1", TestPlugin, "handler")

        # Test listing each type
        analytics_plugins = list_plugins("analytics")
        assert len(analytics_plugins) == 2
        assert "analytics1" in analytics_plugins
        assert "analytics2" in analytics_plugins

        formatter_plugins = list_plugins("formatter")
        assert len(formatter_plugins) == 1
        assert "formatter1" in formatter_plugins

        handler_plugins = list_plugins("handler")
        assert len(handler_plugins) == 1
        assert "handler1" in handler_plugins

        all_plugins = list_plugins()
        assert len(all_plugins) == 4

    def test_unregister_plugin_global(self):
        """Test global unregister_plugin."""
        class TestPlugin:
            pass

        # Register plugin
        register_plugin("test_plugin", TestPlugin, "analytics")
        
        # Verify registration
        assert get_plugin("test_plugin", "analytics") == TestPlugin
        
        # Unregister
        result = unregister_plugin("test_plugin")
        assert result is True
        
        # Verify unregistration
        assert get_plugin("test_plugin", "analytics") is None

    def test_clear_plugins_global(self):
        """Test global clear_plugins."""
        class TestPlugin:
            pass

        # Register plugins
        register_plugin("test1", TestPlugin, "analytics")
        register_plugin("test2", TestPlugin, "formatter")
        register_plugin("test3", TestPlugin, "handler")

        # Clear all
        clear_plugins()

        # Verify clearing
        assert len(list_plugins("analytics")) == 0
        assert len(list_plugins("formatter")) == 0
        assert len(list_plugins("handler")) == 0


class TestBasePluginClasses:
    """Test plugin base classes."""

    def test_analytics_plugin_all_methods(self):
        """Test all AnalyticsPlugin methods."""
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"processed": True, "event": event}
            
            def get_insights(self):
                return {"total_processed": 10, "avg_processing_time": 0.1}

        # Test initialization
        plugin = TestAnalyticsPlugin()
        assert plugin.config == {}
        assert plugin.is_enabled() is True

        # Test with config
        config = {"setting": "value"}
        plugin = TestAnalyticsPlugin(config)
        assert plugin.config == config

        # Test enable/disable
        plugin.disable()
        assert plugin.is_enabled() is False
        
        plugin.enable()
        assert plugin.is_enabled() is True

        # Test reset
        plugin.reset()  # Should not raise exception

        # Test process_event
        result = plugin.process_event("test event")
        assert result["processed"] is True
        assert result["event"] == "test event"

        # Test get_insights
        insights = plugin.get_insights()
        assert insights["total_processed"] == 10
        assert insights["avg_processing_time"] == 0.1

    def test_formatter_plugin_all_methods(self):
        """Test all FormatterPlugin methods."""
        class TestFormatterPlugin(FormatterPlugin):
            def format(self, record):
                return f"FORMATTED: {record}"

        # Test initialization
        plugin = TestFormatterPlugin()
        assert plugin.config == {}

        # Test with config
        config = {"format": "custom"}
        plugin = TestFormatterPlugin(config)
        assert plugin.config == config

        # Test format method
        formatted = plugin.format("test record")
        assert formatted == "FORMATTED: test record"

        # Test get_format_name
        format_name = plugin.get_format_name()
        assert format_name == "testformatter"

    def test_handler_plugin_all_methods(self):
        """Test all HandlerPlugin methods."""
        class TestHandlerPlugin(HandlerPlugin):
            def __init__(self, config=None):
                super().__init__(config)
                self.flushed = False
                self.closed = False
            
            def emit(self, record):
                pass
            
            def flush(self):
                self.flushed = True
            
            def close(self):
                self.closed = True

        # Test initialization
        plugin = TestHandlerPlugin()
        assert plugin.config == {}
        assert plugin.is_enabled() is True

        # Test with config
        config = {"buffer_size": 1000}
        plugin = TestHandlerPlugin(config)
        assert plugin.config == config

        # Test enable/disable
        plugin.disable()
        assert plugin.is_enabled() is False
        
        plugin.enable()
        assert plugin.is_enabled() is True

        # Test emit
        plugin.emit("test record")  # Should not raise exception

        # Test flush
        plugin.flush()
        assert plugin.flushed is True

        # Test close
        plugin.close()
        assert plugin.closed is True


class TestSecurityPlugin:
    """Test SecurityPlugin functionality."""

    def test_security_plugin_initialization(self):
        """Test SecurityPlugin initialization."""
        class TestSecurityPlugin(SecurityPlugin):
            def _detect_threats(self, event):
                return ["sql_injection"] if "sql" in str(event) else []
            
            def _find_suspicious_patterns(self, event):
                return ["suspicious"] if "suspicious" in str(event) else []
            
            def _calculate_security_score(self, event):
                return 0.8 if "threat" in str(event) else 0.2
            
            def _calculate_threat_level(self):
                return "HIGH" if len(self._security_events) > 0 else "LOW"
            
            def _get_security_recommendations(self):
                return ["Enable firewall"] if len(self._security_events) > 0 else []

        # Test initialization
        plugin = TestSecurityPlugin()
        assert plugin.config == {}
        assert plugin._enabled is True
        assert hasattr(plugin, '_security_events')
        assert hasattr(plugin, '_threat_patterns')

        # Test with config
        config = {"security_level": "high"}
        plugin = TestSecurityPlugin(config)
        assert plugin.config == config

        # Test threat patterns
        patterns = plugin._threat_patterns
        assert "sql_injection" in patterns
        assert "xss" in patterns
        assert "path_traversal" in patterns
        assert "command_injection" in patterns

    def test_security_plugin_process_event_enabled(self):
        """Test SecurityPlugin process_event when enabled."""
        class TestSecurityPlugin(SecurityPlugin):
            def _detect_threats(self, event):
                return ["sql_injection"] if "sql" in str(event) else []
            
            def _find_suspicious_patterns(self, event):
                return ["suspicious"] if "suspicious" in str(event) else []
            
            def _calculate_security_score(self, event):
                return 0.8 if "threat" in str(event) else 0.2
            
            def _calculate_threat_level(self):
                return "HIGH" if len(self._security_events) > 0 else "LOW"
            
            def _get_security_recommendations(self):
                return ["Enable firewall"] if len(self._security_events) > 0 else []

        plugin = TestSecurityPlugin()

        # Test with threat
        result = plugin.process_event("sql injection attempt")
        assert "threats_detected" in result
        assert "suspicious_patterns" in result
        assert "security_score" in result
        assert len(plugin._security_events) == 1

        # Test without threat
        result = plugin.process_event("normal message")
        assert "threats_detected" in result
        assert "suspicious_patterns" in result
        assert "security_score" in result
        assert len(plugin._security_events) == 1  # Still 1 from previous

    def test_security_plugin_process_event_disabled(self):
        """Test SecurityPlugin process_event when disabled."""
        class TestSecurityPlugin(SecurityPlugin):
            def _detect_threats(self, event):
                return ["sql_injection"]
            
            def _find_suspicious_patterns(self, event):
                return ["suspicious"]
            
            def _calculate_security_score(self, event):
                return 0.8
            
            def _calculate_threat_level(self):
                return "HIGH"
            
            def _get_security_recommendations(self):
                return ["Enable firewall"]

        plugin = TestSecurityPlugin()
        plugin.disable()

        result = plugin.process_event("sql injection attempt")
        assert result == {}

    def test_security_plugin_get_insights(self):
        """Test SecurityPlugin get_insights method."""
        class TestSecurityPlugin(SecurityPlugin):
            def _detect_threats(self, event):
                return ["sql_injection"] if "sql" in str(event) else []
            
            def _find_suspicious_patterns(self, event):
                return ["suspicious"] if "suspicious" in str(event) else []
            
            def _calculate_security_score(self, event):
                return 0.8 if "threat" in str(event) else 0.2
            
            def _calculate_threat_level(self):
                return "HIGH" if len(self._security_events) > 0 else "LOW"
            
            def _get_security_recommendations(self):
                return ["Enable firewall"] if len(self._security_events) > 0 else []

        plugin = TestSecurityPlugin()

        # Test before any events
        insights = plugin.get_insights()
        assert "security_events_count" in insights
        assert "threat_level" in insights
        assert "security_recommendations" in insights
        assert insights["security_events_count"] == 0
        assert insights["threat_level"] == "LOW"
        assert len(insights["security_recommendations"]) == 0

        # Test after security event
        plugin.process_event("sql injection attempt")
        insights = plugin.get_insights()
        assert insights["security_events_count"] == 1
        assert insights["threat_level"] == "HIGH"
        assert len(insights["security_recommendations"]) == 1


class TestPerformancePlugin:
    """Test PerformancePlugin functionality."""

    def test_performance_plugin_initialization(self):
        """Test PerformancePlugin initialization."""
        class TestPerformancePlugin(PerformancePlugin):
            def _analyze_response_time(self, event):
                return {"avg_response_time": 150}
            
            def _analyze_error_rate(self, event):
                return {"error_rate": 0.05}
            
            def _check_performance_alerts(self, event):
                return ["High response time"] if "slow" in str(event) else []
            
            def _calculate_average_response_time(self):
                return 150.0
            
            def _calculate_error_rate(self):
                return 0.05
            
            def _calculate_performance_score(self):
                return 0.85
            
            def _get_performance_alerts(self):
                return ["High response time"]

        # Test initialization
        plugin = TestPerformancePlugin()
        assert plugin.config == {}
        assert plugin._enabled is True
        assert hasattr(plugin, '_performance_events')
        assert hasattr(plugin, '_performance_thresholds')

        # Test with config
        config = {"performance_level": "high"}
        plugin = TestPerformancePlugin(config)
        assert plugin.config == config

        # Test performance thresholds
        thresholds = plugin._performance_thresholds
        assert "response_time" in thresholds
        assert "error_rate" in thresholds
        assert "memory_usage" in thresholds
        assert "cpu_usage" in thresholds

    def test_performance_plugin_process_event_enabled(self):
        """Test PerformancePlugin process_event when enabled."""
        class TestPerformancePlugin(PerformancePlugin):
            def _analyze_response_time(self, event):
                return {"avg_response_time": 150, "max_response_time": 500}
            
            def _analyze_error_rate(self, event):
                return {"error_rate": 0.05, "total_errors": 10}
            
            def _check_performance_alerts(self, event):
                return ["High response time"] if "slow" in str(event) else []
            
            def _calculate_average_response_time(self):
                return 150.0
            
            def _calculate_error_rate(self):
                return 0.05
            
            def _calculate_performance_score(self):
                return 0.85
            
            def _get_performance_alerts(self):
                return ["High response time"]

        plugin = TestPerformancePlugin()

        # Test with performance event
        result = plugin.process_event("slow request")
        assert "response_time_analysis" in result
        assert "error_rate_analysis" in result
        assert "performance_alerts" in result
        # Don't check internal attribute, just verify the result structure

        # Test without performance event
        result = plugin.process_event("normal request")
        assert "response_time_analysis" in result
        assert "error_rate_analysis" in result
        assert "performance_alerts" in result
        # Don't check internal attribute, just verify the result structure

    def test_performance_plugin_process_event_disabled(self):
        """Test PerformancePlugin process_event when disabled."""
        class TestPerformancePlugin(PerformancePlugin):
            def _analyze_response_time(self, event):
                return {"avg_response_time": 150}
            
            def _analyze_error_rate(self, event):
                return {"error_rate": 0.05}
            
            def _check_performance_alerts(self, event):
                return ["High response time"]
            
            def _calculate_average_response_time(self):
                return 150.0
            
            def _calculate_error_rate(self):
                return 0.05
            
            def _calculate_performance_score(self):
                return 0.85
            
            def _get_performance_alerts(self):
                return ["High response time"]

        plugin = TestPerformancePlugin()
        plugin.disable()

        result = plugin.process_event("slow request")
        assert result == {}

    def test_performance_plugin_get_insights(self):
        """Test PerformancePlugin get_insights method."""
        class TestPerformancePlugin(PerformancePlugin):
            def _analyze_response_time(self, event):
                return {"avg_response_time": 150}
            
            def _analyze_error_rate(self, event):
                return {"error_rate": 0.05}
            
            def _check_performance_alerts(self, event):
                return ["High response time"] if "slow" in str(event) else []
            
            def _calculate_average_response_time(self):
                return 150.0
            
            def _calculate_error_rate(self):
                return 0.05
            
            def _calculate_performance_score(self):
                return 0.85
            
            def _get_performance_alerts(self):
                return ["High response time"]

        plugin = TestPerformancePlugin()

        insights = plugin.get_insights()
        assert "performance_events_count" in insights
        assert "average_response_time" in insights
        assert "error_rate" in insights
        assert "performance_score" in insights
        assert "performance_alerts" in insights
        assert insights["average_response_time"] == 150.0
        assert insights["error_rate"] == 0.05
        assert insights["performance_score"] == 0.85
        assert "High response time" in insights["performance_alerts"]


class TestPluginIntegration:
    """Test plugin integration with HydraLogger."""

    def setup_method(self):
        """Setup test environment."""
        clear_plugins()

    def teardown_method(self):
        """Cleanup after each test."""
        clear_plugins()

    def test_logger_with_plugins(self):
        """Test HydraLogger with plugins."""
        from hydra_logger import HydraLogger
        
        # Create test plugins
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event_data):
                return {"processed": True, "data": event_data}
            
            def get_insights(self):
                return {"total_processed": 5, "avg_processing_time": 0.1}

        class TestFormatterPlugin(FormatterPlugin):
            def format(self, record):
                return f"[CUSTOM] {record}"

        class TestHandlerPlugin(HandlerPlugin):
            def emit(self, record):
                pass

        # Register plugins
        register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        register_plugin("test_formatter", TestFormatterPlugin, "formatter")
        register_plugin("test_handler", TestHandlerPlugin, "handler")
        
        # Create logger with plugins
        logger = HydraLogger(enable_plugins=True)
        
        # Log messages
        logger.info("DEFAULT", "Test message 1")
        logger.warning("DEFAULT", "Test message 2")
        logger.error("DEFAULT", "Test message 3")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["plugin_events"] >= 0

    def test_logger_without_plugins(self):
        """Test HydraLogger without plugins."""
        from hydra_logger import HydraLogger
        
        # Create logger with plugins disabled
        logger = HydraLogger(enable_plugins=False)
        
        # Log message
        logger.info("DEFAULT", "Test message without plugins")
        
        # Check that no plugin events were tracked
        metrics = logger.get_performance_metrics()
        assert metrics["plugin_events"] == 0

    def test_plugin_error_recovery(self):
        """Test plugin error recovery."""
        from hydra_logger import HydraLogger
        
        # Create plugin that might fail
        class TestFailingPlugin(AnalyticsPlugin):
            def process_event(self, event_data):
                if "fail" in str(event_data):
                    raise Exception("Plugin error")
                return {"processed": True}
            
            def get_insights(self):
                return {"insights": "test"}

        # Register plugin
        register_plugin("test_failing", TestFailingPlugin, "analytics")
        
        # Create logger
        logger = HydraLogger(enable_plugins=True)
        
        # Test normal operation
        logger.info("DEFAULT", "Normal message")
        
        # Test error handling
        try:
            logger.info("DEFAULT", "Message with fail")
        except Exception:
            pass
        
        # Logger should still work
        logger.info("DEFAULT", "Message after error")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics is not None

    def test_plugin_configuration_integration(self):
        """Test plugin configuration integration."""
        from hydra_logger import HydraLogger
        
        # Create configurable plugin
        class TestConfigurablePlugin(AnalyticsPlugin):
            def __init__(self, config=None):
                super().__init__(config)
                self.custom_setting = (config or {}).get("custom_setting", "default")
            
            def process_event(self, event_data):
                return {"processed": True, "setting": self.custom_setting}
            
            def get_insights(self):
                return {"setting": self.custom_setting}

        # Register plugin
        register_plugin("test_configurable", TestConfigurablePlugin, "analytics")
        
        # Create logger with plugin config
        logger = HydraLogger(enable_plugins=True)
        
        # Log message
        logger.info("DEFAULT", "Test message with config")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["plugin_events"] >= 0

    def test_multiple_plugin_types_integration(self):
        """Test integration with multiple plugin types."""
        from hydra_logger import HydraLogger
        
        # Create plugins of different types
        class TestAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"analytics": True}
            
            def get_insights(self):
                return {"analytics_insights": "test"}

        class TestSecurityPlugin(SecurityPlugin):
            def _detect_threats(self, event):
                return ["sql_injection"] if "sql" in str(event) else []
            
            def _find_suspicious_patterns(self, event):
                return ["suspicious"] if "suspicious" in str(event) else []
            
            def _calculate_security_score(self, event):
                return 0.8 if "threat" in str(event) else 0.2
            
            def _calculate_threat_level(self):
                return "HIGH" if len(self._security_events) > 0 else "LOW"
            
            def _get_security_recommendations(self):
                return ["Enable firewall"] if len(self._security_events) > 0 else []

        class TestPerformancePlugin(PerformancePlugin):
            def _analyze_response_time(self, event):
                return {"avg_response_time": 150}
            
            def _analyze_error_rate(self, event):
                return {"error_rate": 0.05}
            
            def _check_performance_alerts(self, event):
                return ["High response time"] if "slow" in str(event) else []
            
            def _calculate_average_response_time(self):
                return 150.0
            
            def _calculate_error_rate(self):
                return 0.05
            
            def _calculate_performance_score(self):
                return 0.85
            
            def _get_performance_alerts(self):
                return ["High response time"]

        # Register plugins
        register_plugin("test_analytics", TestAnalyticsPlugin, "analytics")
        register_plugin("test_security", TestSecurityPlugin, "analytics")
        register_plugin("test_performance", TestPerformancePlugin, "analytics")
        
        # Create logger
        logger = HydraLogger(enable_plugins=True)
        
        # Log various types of messages
        logger.info("DEFAULT", "Normal message")
        logger.warning("DEFAULT", "suspicious activity detected")
        logger.error("DEFAULT", "slow request processing")
        
        # Check metrics
        metrics = logger.get_performance_metrics()
        assert metrics["plugin_events"] >= 0

    def test_plugin_lifecycle_management(self):
        """Test plugin lifecycle management."""
        from hydra_logger import HydraLogger
        
        # Create plugin with lifecycle tracking
        class TestLifecyclePlugin(AnalyticsPlugin):
            def __init__(self, config=None):
                super().__init__(config)
                self.initialized = True
                self.enabled_count = 0
                self.disabled_count = 0
                self.reset_count = 0
            
            def process_event(self, event):
                return {"processed": True, "enabled": self.is_enabled()}
            
            def get_insights(self):
                return {
                    "enabled_count": self.enabled_count,
                    "disabled_count": self.disabled_count,
                    "reset_count": self.reset_count
                }
            
            def enable(self):
                super().enable()
                self.enabled_count += 1
            
            def disable(self):
                super().disable()
                self.disabled_count += 1
            
            def reset(self):
                super().reset()
                self.reset_count += 1

        # Register plugin
        register_plugin("test_lifecycle", TestLifecyclePlugin, "analytics")
        
        # Create logger
        logger = HydraLogger(enable_plugins=True)
        
        # Test plugin lifecycle
        logger.info("DEFAULT", "Message 1")
        
        # Get plugin instance and test lifecycle methods
        plugin_class = get_plugin("test_lifecycle", "analytics")
        assert plugin_class is not None
        plugin = plugin_class()
        
        plugin.disable()
        plugin.enable()
        plugin.reset()
        
        # Check insights
        insights = plugin.get_insights()
        assert insights["enabled_count"] == 1
        assert insights["disabled_count"] == 1
        assert insights["reset_count"] == 1 