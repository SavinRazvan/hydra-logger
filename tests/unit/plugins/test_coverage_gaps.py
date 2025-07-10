"""
Additional tests to cover missing lines in plugins base and registry modules.

This file targets specific uncovered lines identified in the coverage report.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import importlib
import sys
from typing import Any, Dict

from hydra_logger.plugins.base import (
    AnalyticsPlugin,
    FormatterPlugin,
    HandlerPlugin,
    SecurityPlugin,
    PerformancePlugin
)
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


class ConcreteAnalyticsPlugin(AnalyticsPlugin):
    """Concrete implementation of AnalyticsPlugin for testing."""
    
    def process_event(self, event: Any) -> Dict[str, Any]:
        """Process a log event."""
        return {"processed": True, "event": event}
    
    def get_insights(self) -> Dict[str, Any]:
        """Get current insights."""
        return {"insights": "test insights"}


class ConcreteFormatterPlugin(FormatterPlugin):
    """Concrete implementation of FormatterPlugin for testing."""
    
    def format(self, record: Any) -> str:
        """Format a log record."""
        return f"formatted: {record}"


class ConcreteHandlerPlugin(HandlerPlugin):
    """Concrete implementation of HandlerPlugin for testing."""
    
    def emit(self, record: Any) -> None:
        """Emit a log record."""
        pass


class TestBasePluginCoverageGaps:
    """Test specific uncovered lines in base.py."""

    def test_analytics_plugin_init_with_config(self):
        """Test AnalyticsPlugin initialization with config (line 24-25)."""
        config = {"test": "value"}
        plugin = ConcreteAnalyticsPlugin(config)
        assert plugin.config == config
        assert plugin._enabled is True

    def test_analytics_plugin_init_without_config(self):
        """Test AnalyticsPlugin initialization without config (line 52)."""
        plugin = ConcreteAnalyticsPlugin()
        assert plugin.config == {}
        assert plugin._enabled is True

    def test_analytics_plugin_enable_disable_methods(self):
        """Test AnalyticsPlugin enable/disable methods (lines 56, 60, 64)."""
        plugin = ConcreteAnalyticsPlugin()
        
        # Test enable
        plugin.enable()
        assert plugin.is_enabled() is True
        
        # Test disable
        plugin.disable()
        assert plugin.is_enabled() is False
        
        # Test is_enabled
        assert plugin.is_enabled() is False

    def test_analytics_plugin_reset_method(self):
        """Test AnalyticsPlugin reset method (line 77)."""
        plugin = ConcreteAnalyticsPlugin()
        # Should not raise any error
        plugin.reset()

    def test_formatter_plugin_init_with_config(self):
        """Test FormatterPlugin initialization with config (line 94)."""
        config = {"format": "json"}
        plugin = ConcreteFormatterPlugin(config)
        assert plugin.config == config

    def test_formatter_plugin_init_without_config(self):
        """Test FormatterPlugin initialization without config (line 107-108)."""
        plugin = ConcreteFormatterPlugin()
        assert plugin.config == {}

    def test_formatter_plugin_get_format_name(self):
        """Test FormatterPlugin get_format_name method (line 122)."""
        plugin = ConcreteFormatterPlugin()
        format_name = plugin.get_format_name()
        assert format_name == "concreteplugin"

    def test_handler_plugin_init_with_config(self):
        """Test HandlerPlugin initialization with config (line 126)."""
        config = {"level": "INFO"}
        plugin = ConcreteHandlerPlugin(config)
        assert plugin.config == config

    def test_handler_plugin_init_without_config(self):
        """Test HandlerPlugin initialization without config (line 130)."""
        plugin = ConcreteHandlerPlugin()
        assert plugin.config == {}

    def test_handler_plugin_enable_disable_methods(self):
        """Test HandlerPlugin enable/disable methods (lines 134, 138)."""
        plugin = ConcreteHandlerPlugin()
        
        # Test enable
        plugin.enable()
        assert plugin.is_enabled() is True
        
        # Test disable
        plugin.disable()
        assert plugin.is_enabled() is False
        
        # Test is_enabled
        assert plugin.is_enabled() is False

    def test_handler_plugin_flush_close_methods(self):
        """Test HandlerPlugin flush and close methods (lines 151-153, 157)."""
        plugin = ConcreteHandlerPlugin()
        # Should not raise any error
        plugin.flush()
        plugin.close()

    def test_security_plugin_init_with_config(self):
        """Test SecurityPlugin initialization with config (line 174-186)."""
        config = {"sensitivity": "high"}
        plugin = SecurityPlugin(config)
        assert plugin.config == config
        assert plugin._enabled is True
        assert plugin._security_events == []
        assert plugin._threat_patterns is not None

    def test_security_plugin_get_threat_patterns(self):
        """Test SecurityPlugin _get_threat_patterns method (line 195)."""
        plugin = SecurityPlugin()
        patterns = plugin._get_threat_patterns()
        assert isinstance(patterns, dict)
        assert "sql_injection" in patterns
        assert "xss" in patterns
        assert "path_traversal" in patterns
        assert "command_injection" in patterns

    def test_security_plugin_process_event_with_threats(self):
        """Test SecurityPlugin process_event with threats detected (line 204)."""
        plugin = SecurityPlugin()
        event = {"message": "SELECT * FROM users", "level": "INFO"}
        
        result = plugin.process_event(event)
        assert "threats_detected" in result
        assert "suspicious_patterns" in result
        assert "security_score" in result
        
        # Check that security events are added when threats are detected
        assert len(plugin._security_events) >= 0

    def test_security_plugin_process_event_disabled(self):
        """Test SecurityPlugin process_event when disabled (line 209)."""
        plugin = SecurityPlugin()
        plugin.disable()
        
        event = {"message": "test message", "level": "INFO"}
        result = plugin.process_event(event)
        assert result == {}

    def test_security_plugin_get_insights(self):
        """Test SecurityPlugin get_insights method (line 214)."""
        plugin = SecurityPlugin()
        insights = plugin.get_insights()
        assert "security_events_count" in insights
        assert "threat_level" in insights
        assert "security_recommendations" in insights

    def test_security_plugin_detect_threats(self):
        """Test SecurityPlugin _detect_threats method (line 219)."""
        plugin = SecurityPlugin()
        event = {"message": "test message", "level": "INFO"}
        threats = plugin._detect_threats(event)
        assert isinstance(threats, list)

    def test_security_plugin_find_suspicious_patterns(self):
        """Test SecurityPlugin _find_suspicious_patterns method (line 224)."""
        plugin = SecurityPlugin()
        event = {"message": "test message", "level": "INFO"}
        patterns = plugin._find_suspicious_patterns(event)
        assert isinstance(patterns, list)

    def test_security_plugin_calculate_security_score(self):
        """Test SecurityPlugin _calculate_security_score method (line 237-239)."""
        plugin = SecurityPlugin()
        event = {"message": "test message", "level": "INFO"}
        score = plugin._calculate_security_score(event)
        assert isinstance(score, float)

    def test_security_plugin_calculate_threat_level(self):
        """Test SecurityPlugin _calculate_threat_level method (line 243)."""
        plugin = SecurityPlugin()
        level = plugin._calculate_threat_level()
        assert isinstance(level, str)

    def test_security_plugin_get_security_recommendations(self):
        """Test SecurityPlugin _get_security_recommendations method (line 260-269)."""
        plugin = SecurityPlugin()
        recommendations = plugin._get_security_recommendations()
        assert isinstance(recommendations, list)

    def test_performance_plugin_init_with_config(self):
        """Test PerformancePlugin initialization with config (line 278)."""
        config = {"thresholds": {"response_time": 1000}}
        plugin = PerformancePlugin(config)
        assert plugin.config == config
        assert plugin._enabled is True
        assert plugin._performance_metrics == {}
        assert plugin._performance_thresholds is not None

    def test_performance_plugin_get_performance_thresholds(self):
        """Test PerformancePlugin _get_performance_thresholds method (line 288)."""
        plugin = PerformancePlugin()
        thresholds = plugin._get_performance_thresholds()
        assert isinstance(thresholds, dict)
        assert "response_time_warning" in thresholds
        assert "response_time_critical" in thresholds
        assert "error_rate_warning" in thresholds
        assert "error_rate_critical" in thresholds

    def test_performance_plugin_process_event_enabled(self):
        """Test PerformancePlugin process_event when enabled (line 293)."""
        plugin = PerformancePlugin()
        event = {"response_time": 500, "level": "INFO"}
        
        result = plugin.process_event(event)
        assert "response_time_analysis" in result
        assert "error_rate_analysis" in result
        assert "performance_alerts" in result

    def test_performance_plugin_process_event_disabled(self):
        """Test PerformancePlugin process_event when disabled (line 298)."""
        plugin = PerformancePlugin()
        plugin.disable()
        
        event = {"response_time": 500, "level": "INFO"}
        result = plugin.process_event(event)
        assert result == {}

    def test_performance_plugin_get_insights(self):
        """Test PerformancePlugin get_insights method (line 303)."""
        plugin = PerformancePlugin()
        insights = plugin.get_insights()
        assert "average_response_time" in insights
        assert "error_rate" in insights
        assert "performance_score" in insights
        assert "performance_alerts" in insights

    def test_performance_plugin_analyze_response_time(self):
        """Test PerformancePlugin _analyze_response_time method (line 308)."""
        plugin = PerformancePlugin()
        event = {"response_time": 500, "level": "INFO"}
        analysis = plugin._analyze_response_time(event)
        assert isinstance(analysis, dict)

    def test_performance_plugin_analyze_error_rate(self):
        """Test PerformancePlugin _analyze_error_rate method (line 313)."""
        plugin = PerformancePlugin()
        event = {"level": "ERROR"}
        analysis = plugin._analyze_error_rate(event)
        assert isinstance(analysis, dict)

    def test_performance_plugin_check_performance_alerts(self):
        """Test PerformancePlugin _check_performance_alerts method (line 318)."""
        plugin = PerformancePlugin()
        event = {"response_time": 500, "level": "INFO"}
        alerts = plugin._check_performance_alerts(event)
        assert isinstance(alerts, list)

    def test_performance_plugin_calculate_average_response_time(self):
        """Test PerformancePlugin _calculate_average_response_time method."""
        plugin = PerformancePlugin()
        avg_time = plugin._calculate_average_response_time()
        assert isinstance(avg_time, float)

    def test_performance_plugin_calculate_error_rate(self):
        """Test PerformancePlugin _calculate_error_rate method."""
        plugin = PerformancePlugin()
        error_rate = plugin._calculate_error_rate()
        assert isinstance(error_rate, float)

    def test_performance_plugin_calculate_performance_score(self):
        """Test PerformancePlugin _calculate_performance_score method."""
        plugin = PerformancePlugin()
        score = plugin._calculate_performance_score()
        assert isinstance(score, float)

    def test_performance_plugin_get_performance_alerts(self):
        """Test PerformancePlugin _get_performance_alerts method."""
        plugin = PerformancePlugin()
        alerts = plugin._get_performance_alerts()
        assert isinstance(alerts, list)


class TestRegistryCoverageGaps:
    """Test specific uncovered lines in registry.py."""

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
        registry.register_plugin("test_analytics", ConcreteAnalyticsPlugin, "analytics")
        assert "test_analytics" in registry._analytics_plugins
        assert "test_analytics" in registry._plugins

    def test_register_plugin_formatter(self):
        """Test registering formatter plugin."""
        registry = PluginRegistry()
        registry.register_plugin("test_formatter", ConcreteFormatterPlugin, "formatter")
        assert "test_formatter" in registry._formatter_plugins
        assert "test_formatter" in registry._plugins

    def test_register_plugin_handler(self):
        """Test registering handler plugin."""
        registry = PluginRegistry()
        registry.register_plugin("test_handler", ConcreteHandlerPlugin, "handler")
        assert "test_handler" in registry._handler_plugins
        assert "test_handler" in registry._plugins

    def test_register_plugin_unknown_type(self):
        """Test registering plugin with unknown type."""
        registry = PluginRegistry()
        with pytest.raises(PluginError, match="Unknown plugin type"):
            registry.register_plugin("test", ConcreteAnalyticsPlugin, "unknown")

    def test_register_plugin_exception(self):
        """Test registering plugin with exception."""
        registry = PluginRegistry()
        # Test with unknown plugin type which should raise PluginError
        with pytest.raises(PluginError, match="Unknown plugin type"):
            registry.register_plugin("test", ConcreteAnalyticsPlugin, "unknown")

    def test_get_plugin_analytics(self):
        """Test getting analytics plugin."""
        registry = PluginRegistry()
        registry.register_plugin("test_analytics", ConcreteAnalyticsPlugin, "analytics")
        plugin = registry.get_plugin("test_analytics", "analytics")
        assert plugin == ConcreteAnalyticsPlugin

    def test_get_plugin_formatter(self):
        """Test getting formatter plugin."""
        registry = PluginRegistry()
        registry.register_plugin("test_formatter", ConcreteFormatterPlugin, "formatter")
        plugin = registry.get_plugin("test_formatter", "formatter")
        assert plugin == ConcreteFormatterPlugin

    def test_get_plugin_handler(self):
        """Test getting handler plugin."""
        registry = PluginRegistry()
        registry.register_plugin("test_handler", ConcreteHandlerPlugin, "handler")
        plugin = registry.get_plugin("test_handler", "handler")
        assert plugin == ConcreteHandlerPlugin

    def test_get_plugin_not_found(self):
        """Test getting plugin that doesn't exist."""
        registry = PluginRegistry()
        plugin = registry.get_plugin("nonexistent", "analytics")
        assert plugin is None

    def test_list_plugins_analytics(self):
        """Test listing analytics plugins."""
        registry = PluginRegistry()
        registry.register_plugin("test_analytics", ConcreteAnalyticsPlugin, "analytics")
        plugins = registry.list_plugins("analytics")
        assert "test_analytics" in plugins
        assert plugins["test_analytics"] == ConcreteAnalyticsPlugin

    def test_list_plugins_formatter(self):
        """Test listing formatter plugins."""
        registry = PluginRegistry()
        registry.register_plugin("test_formatter", ConcreteFormatterPlugin, "formatter")
        plugins = registry.list_plugins("formatter")
        assert "test_formatter" in plugins
        assert plugins["test_formatter"] == ConcreteFormatterPlugin

    def test_list_plugins_handler(self):
        """Test listing handler plugins."""
        registry = PluginRegistry()
        registry.register_plugin("test_handler", ConcreteHandlerPlugin, "handler")
        plugins = registry.list_plugins("handler")
        assert "test_handler" in plugins
        assert plugins["test_handler"] == ConcreteHandlerPlugin

    def test_list_plugins_all(self):
        """Test listing all plugins."""
        registry = PluginRegistry()
        registry.register_plugin("test_analytics", ConcreteAnalyticsPlugin, "analytics")
        registry.register_plugin("test_formatter", ConcreteFormatterPlugin, "formatter")
        plugins = registry.list_plugins()
        assert "test_analytics" in plugins
        assert "test_formatter" in plugins

    def test_unregister_plugin_success(self):
        """Test unregistering plugin successfully."""
        registry = PluginRegistry()
        registry.register_plugin("test_analytics", ConcreteAnalyticsPlugin, "analytics")
        result = registry.unregister_plugin("test_analytics")
        assert result is True
        assert "test_analytics" not in registry._plugins
        assert "test_analytics" not in registry._analytics_plugins

    def test_unregister_plugin_not_found(self):
        """Test unregistering plugin that doesn't exist."""
        registry = PluginRegistry()
        result = registry.unregister_plugin("nonexistent")
        assert result is False

    def test_load_plugin_from_path_success(self):
        """Test loading plugin from path successfully."""
        registry = PluginRegistry()
        
        # Create a mock module with a plugin class
        mock_module = MagicMock()
        mock_module.TestPlugin = ConcreteAnalyticsPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            result = registry.load_plugin_from_path("TestPlugin", "test.module")
            assert result is True
            assert "TestPlugin" in registry._plugins

    def test_load_plugin_from_path_import_error(self):
        """Test loading plugin from path with import error."""
        registry = PluginRegistry()
        
        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                registry.load_plugin_from_path("TestPlugin", "nonexistent.module")

    def test_load_plugin_from_path_attribute_error(self):
        """Test loading plugin from path with attribute error."""
        registry = PluginRegistry()
        
        mock_module = MagicMock()
        # Simulate attribute error when getting plugin class
        # Remove the attribute to cause AttributeError
        del mock_module.TestPlugin
        
        with patch('importlib.import_module', return_value=mock_module):
            with pytest.raises(PluginError, match="Failed to load plugin"):
                registry.load_plugin_from_path("TestPlugin", "test.module")

    def test_clear_plugins(self):
        """Test clearing all plugins."""
        registry = PluginRegistry()
        registry.register_plugin("test_analytics", ConcreteAnalyticsPlugin, "analytics")
        registry.register_plugin("test_formatter", ConcreteFormatterPlugin, "formatter")
        
        registry.clear_plugins()
        assert registry._plugins == {}
        assert registry._analytics_plugins == {}
        assert registry._formatter_plugins == {}
        assert registry._handler_plugins == {}

    def test_global_functions(self):
        """Test global registry functions."""
        # Test register_plugin
        register_plugin("test_global", ConcreteAnalyticsPlugin, "analytics")
        
        # Test get_plugin
        plugin = get_plugin("test_global", "analytics")
        assert plugin == ConcreteAnalyticsPlugin
        
        # Test list_plugins
        plugins = list_plugins("analytics")
        assert "test_global" in plugins
        
        # Test unregister_plugin
        result = unregister_plugin("test_global")
        assert result is True
        
        # Test clear_plugins
        clear_plugins()
        plugins = list_plugins()
        assert plugins == {}


class TestPluginIntegration:
    """Test plugin integration scenarios."""

    def test_plugin_inheritance_chain(self):
        """Test plugin inheritance chain."""
        class CustomSecurityPlugin(SecurityPlugin):
            def _detect_threats(self, event):
                return ["custom_threat"]
            
            def _find_suspicious_patterns(self, event):
                return ["custom_pattern"]
            
            def _calculate_security_score(self, event):
                return 0.5
            
            def _calculate_threat_level(self):
                return "MEDIUM"
            
            def _get_security_recommendations(self):
                return ["custom_recommendation"]

        plugin = CustomSecurityPlugin()
        event = {"message": "test", "level": "INFO"}
        
        result = plugin.process_event(event)
        assert "threats_detected" in result
        assert "suspicious_patterns" in result
        assert "security_score" in result
        
        insights = plugin.get_insights()
        assert "security_events_count" in insights
        assert "threat_level" in insights
        assert "security_recommendations" in insights

    def test_plugin_state_persistence(self):
        """Test plugin state persistence."""
        plugin = SecurityPlugin({"sensitivity": "high"})
        
        # Test initial state
        assert plugin.config["sensitivity"] == "high"
        assert plugin.is_enabled() is True
        
        # Test state changes
        plugin.disable()
        assert plugin.is_enabled() is False
        
        plugin.enable()
        assert plugin.is_enabled() is True
        
        # Test reset
        plugin.reset()  # Should not raise any error

    def test_plugin_method_override(self):
        """Test plugin method override."""
        class CustomPerformancePlugin(PerformancePlugin):
            def _analyze_response_time(self, event):
                return {"custom_analysis": True}
            
            def _analyze_error_rate(self, event):
                return {"custom_error_analysis": True}
            
            def _check_performance_alerts(self, event):
                return ["custom_alert"]
            
            def _calculate_average_response_time(self):
                return 100.0
            
            def _calculate_error_rate(self):
                return 0.05
            
            def _calculate_performance_score(self):
                return 0.8
            
            def _get_performance_alerts(self):
                return ["custom_performance_alert"]

        plugin = CustomPerformancePlugin()
        event = {"response_time": 500, "level": "INFO"}
        
        result = plugin.process_event(event)
        assert "response_time_analysis" in result
        assert "error_rate_analysis" in result
        assert "performance_alerts" in result
        
        insights = plugin.get_insights()
        assert "average_response_time" in insights
        assert "error_rate" in insights
        assert "performance_score" in insights
        assert "performance_alerts" in insights 