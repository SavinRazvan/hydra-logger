"""
Comprehensive tests for plugins base module.

This module tests all functionality in hydra_logger.plugins.base
to achieve 100% coverage.
"""

import pytest
from unittest.mock import patch, MagicMock

from hydra_logger.plugins.base import (
    AnalyticsPlugin,
    FormatterPlugin,
    HandlerPlugin,
    SecurityPlugin,
    PerformancePlugin
)


class TestAnalyticsPlugin:
    """Test AnalyticsPlugin base class."""

    def test_analytics_plugin_init_default(self):
        """Test AnalyticsPlugin initialization with default config."""
        plugin = AnalyticsPlugin()
        assert plugin.config == {}
        assert plugin._enabled is True

    def test_analytics_plugin_init_custom(self):
        """Test AnalyticsPlugin initialization with custom config."""
        config = {"setting": "value"}
        plugin = AnalyticsPlugin(config)
        assert plugin.config == config

    def test_analytics_plugin_enable_disable(self):
        """Test enabling and disabling plugin."""
        plugin = AnalyticsPlugin()
        
        assert plugin.is_enabled() is True
        
        plugin.disable()
        assert plugin.is_enabled() is False
        
        plugin.enable()
        assert plugin.is_enabled() is True

    def test_analytics_plugin_reset(self):
        """Test plugin reset."""
        plugin = AnalyticsPlugin()
        plugin.reset()  # Should not raise any error


class TestFormatterPlugin:
    """Test FormatterPlugin base class."""

    def test_formatter_plugin_init_default(self):
        """Test FormatterPlugin initialization with default config."""
        plugin = FormatterPlugin()
        assert plugin.config == {}

    def test_formatter_plugin_init_custom(self):
        """Test FormatterPlugin initialization with custom config."""
        config = {"format": "json"}
        plugin = FormatterPlugin(config)
        assert plugin.config == config

    def test_formatter_plugin_get_format_name(self):
        """Test getting format name."""
        plugin = FormatterPlugin()
        format_name = plugin.get_format_name()
        assert format_name == "formatter"


class TestHandlerPlugin:
    """Test HandlerPlugin base class."""

    def test_handler_plugin_init_default(self):
        """Test HandlerPlugin initialization with default config."""
        plugin = HandlerPlugin()
        assert plugin.config == {}
        assert plugin._enabled is True

    def test_handler_plugin_init_custom(self):
        """Test HandlerPlugin initialization with custom config."""
        config = {"level": "INFO"}
        plugin = HandlerPlugin(config)
        assert plugin.config == config

    def test_handler_plugin_enable_disable(self):
        """Test enabling and disabling handler."""
        plugin = HandlerPlugin()
        
        assert plugin.is_enabled() is True
        
        plugin.disable()
        assert plugin.is_enabled() is False
        
        plugin.enable()
        assert plugin.is_enabled() is True

    def test_handler_plugin_flush_close(self):
        """Test handler flush and close."""
        plugin = HandlerPlugin()
        plugin.flush()  # Should not raise any error
        plugin.close()  # Should not raise any error


class TestSecurityPlugin:
    """Test SecurityPlugin class."""

    def test_security_plugin_init_default(self):
        """Test SecurityPlugin initialization with default config."""
        plugin = SecurityPlugin()
        assert plugin.config == {}
        assert plugin._enabled is True
        assert plugin._security_events == []
        assert plugin._threat_patterns is not None

    def test_security_plugin_init_custom(self):
        """Test SecurityPlugin initialization with custom config."""
        config = {"sensitivity": "high"}
        plugin = SecurityPlugin(config)
        assert plugin.config == config

    def test_security_plugin_get_threat_patterns(self):
        """Test getting threat patterns."""
        plugin = SecurityPlugin()
        patterns = plugin._get_threat_patterns()
        assert "sql_injection" in patterns
        assert "xss" in patterns
        assert "path_traversal" in patterns
        assert "command_injection" in patterns

    def test_security_plugin_process_event_enabled(self):
        """Test processing event when enabled."""
        plugin = SecurityPlugin()
        event = {"message": "test message", "level": "INFO"}
        
        result = plugin.process_event(event)
        assert "threats_detected" in result
        assert "suspicious_patterns" in result
        assert "security_score" in result

    def test_security_plugin_process_event_disabled(self):
        """Test processing event when disabled."""
        plugin = SecurityPlugin()
        plugin.disable()
        
        event = {"message": "test message", "level": "INFO"}
        result = plugin.process_event(event)
        assert result == {}

    def test_security_plugin_get_insights(self):
        """Test getting security insights."""
        plugin = SecurityPlugin()
        insights = plugin.get_insights()
        assert "security_events_count" in insights
        assert "threat_level" in insights
        assert "security_recommendations" in insights

    def test_security_plugin_detect_threats(self):
        """Test threat detection."""
        plugin = SecurityPlugin()
        event = {"message": "SELECT * FROM users", "level": "INFO"}
        threats = plugin._detect_threats(event)
        assert isinstance(threats, list)

    def test_security_plugin_find_suspicious_patterns(self):
        """Test finding suspicious patterns."""
        plugin = SecurityPlugin()
        event = {"message": "test message", "level": "INFO"}
        patterns = plugin._find_suspicious_patterns(event)
        assert isinstance(patterns, list)

    def test_security_plugin_calculate_security_score(self):
        """Test calculating security score."""
        plugin = SecurityPlugin()
        event = {"message": "test message", "level": "INFO"}
        score = plugin._calculate_security_score(event)
        assert isinstance(score, float)

    def test_security_plugin_calculate_threat_level(self):
        """Test calculating threat level."""
        plugin = SecurityPlugin()
        level = plugin._calculate_threat_level()
        assert isinstance(level, str)

    def test_security_plugin_get_security_recommendations(self):
        """Test getting security recommendations."""
        plugin = SecurityPlugin()
        recommendations = plugin._get_security_recommendations()
        assert isinstance(recommendations, list)


class TestPerformancePlugin:
    """Test PerformancePlugin class."""

    def test_performance_plugin_init_default(self):
        """Test PerformancePlugin initialization with default config."""
        plugin = PerformancePlugin()
        assert plugin.config == {}
        assert plugin._enabled is True
        assert plugin._performance_metrics == {}
        assert plugin._performance_thresholds is not None

    def test_performance_plugin_init_custom(self):
        """Test PerformancePlugin initialization with custom config."""
        config = {"threshold": 1000}
        plugin = PerformancePlugin(config)
        assert plugin.config == config

    def test_performance_plugin_get_performance_thresholds(self):
        """Test getting performance thresholds."""
        plugin = PerformancePlugin()
        thresholds = plugin._get_performance_thresholds()
        assert "response_time_warning" in thresholds
        assert "response_time_critical" in thresholds
        assert "error_rate_warning" in thresholds
        assert "error_rate_critical" in thresholds

    def test_performance_plugin_process_event_enabled(self):
        """Test processing event when enabled."""
        plugin = PerformancePlugin()
        event = {"response_time": 500, "status": "success"}
        
        result = plugin.process_event(event)
        assert "response_time_analysis" in result
        assert "error_rate_analysis" in result
        assert "performance_alerts" in result

    def test_performance_plugin_process_event_disabled(self):
        """Test processing event when disabled."""
        plugin = PerformancePlugin()
        plugin.disable()
        
        event = {"response_time": 500, "status": "success"}
        result = plugin.process_event(event)
        assert result == {}

    def test_performance_plugin_get_insights(self):
        """Test getting performance insights."""
        plugin = PerformancePlugin()
        insights = plugin.get_insights()
        assert "average_response_time" in insights
        assert "error_rate" in insights
        assert "performance_score" in insights
        assert "performance_alerts" in insights

    def test_performance_plugin_analyze_response_time(self):
        """Test response time analysis."""
        plugin = PerformancePlugin()
        event = {"response_time": 500, "status": "success"}
        analysis = plugin._analyze_response_time(event)
        assert isinstance(analysis, dict)

    def test_performance_plugin_analyze_error_rate(self):
        """Test error rate analysis."""
        plugin = PerformancePlugin()
        event = {"status": "error"}
        analysis = plugin._analyze_error_rate(event)
        assert isinstance(analysis, dict)

    def test_performance_plugin_check_performance_alerts(self):
        """Test checking performance alerts."""
        plugin = PerformancePlugin()
        event = {"response_time": 500, "status": "success"}
        alerts = plugin._check_performance_alerts(event)
        assert isinstance(alerts, list)

    def test_performance_plugin_calculate_average_response_time(self):
        """Test calculating average response time."""
        plugin = PerformancePlugin()
        avg_time = plugin._calculate_average_response_time()
        assert isinstance(avg_time, float)

    def test_performance_plugin_calculate_error_rate(self):
        """Test calculating error rate."""
        plugin = PerformancePlugin()
        error_rate = plugin._calculate_error_rate()
        assert isinstance(error_rate, float)

    def test_performance_plugin_calculate_performance_score(self):
        """Test calculating performance score."""
        plugin = PerformancePlugin()
        score = plugin._calculate_performance_score()
        assert isinstance(score, float)

    def test_performance_plugin_get_performance_alerts(self):
        """Test getting performance alerts."""
        plugin = PerformancePlugin()
        alerts = plugin._get_performance_alerts()
        assert isinstance(alerts, list)


class TestPluginIntegration:
    """Test plugin integration scenarios."""

    def test_analytics_plugin_inheritance(self):
        """Test AnalyticsPlugin inheritance."""
        class CustomAnalyticsPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"custom": "insight"}
            
            def get_insights(self):
                return {"custom": "data"}
        
        plugin = CustomAnalyticsPlugin()
        assert plugin.is_enabled() is True
        
        result = plugin.process_event({"test": "event"})
        assert result == {"custom": "insight"}
        
        insights = plugin.get_insights()
        assert insights == {"custom": "data"}

    def test_formatter_plugin_inheritance(self):
        """Test FormatterPlugin inheritance."""
        class CustomFormatterPlugin(FormatterPlugin):
            def format(self, record):
                return f"CUSTOM: {record}"
        
        plugin = CustomFormatterPlugin()
        result = plugin.format("test record")
        assert result == "CUSTOM: test record"
        
        format_name = plugin.get_format_name()
        assert format_name == "customformatter"

    def test_handler_plugin_inheritance(self):
        """Test HandlerPlugin inheritance."""
        class CustomHandlerPlugin(HandlerPlugin):
            def emit(self, record):
                pass  # Custom emit logic
        
        plugin = CustomHandlerPlugin()
        assert plugin.is_enabled() is True
        
        plugin.emit("test record")  # Should not raise any error
        
        plugin.disable()
        assert plugin.is_enabled() is False

    def test_security_plugin_inheritance(self):
        """Test SecurityPlugin inheritance."""
        class CustomSecurityPlugin(SecurityPlugin):
            def _detect_threats(self, event):
                return ["custom_threat"]
            
            def _find_suspicious_patterns(self, event):
                return ["custom_pattern"]
            
            def _calculate_security_score(self, event):
                return 0.8
            
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

    def test_performance_plugin_inheritance(self):
        """Test PerformancePlugin inheritance."""
        class CustomPerformancePlugin(PerformancePlugin):
            def _analyze_response_time(self, event):
                return {"custom": "analysis"}
            
            def _analyze_error_rate(self, event):
                return {"custom": "error_analysis"}
            
            def _check_performance_alerts(self, event):
                return ["custom_alert"]
            
            def _calculate_average_response_time(self):
                return 250.0
            
            def _calculate_error_rate(self):
                return 0.05
            
            def _calculate_performance_score(self):
                return 0.9
            
            def _get_performance_alerts(self):
                return ["custom_performance_alert"]
        
        plugin = CustomPerformancePlugin()
        event = {"response_time": 500, "status": "success"}
        
        result = plugin.process_event(event)
        assert "response_time_analysis" in result
        assert "error_rate_analysis" in result
        assert "performance_alerts" in result
        
        insights = plugin.get_insights()
        assert "average_response_time" in insights
        assert "error_rate" in insights
        assert "performance_score" in insights
        assert "performance_alerts" in insights

    def test_plugin_config_persistence(self):
        """Test that plugin config persists through operations."""
        config = {"setting": "value", "enabled": True}
        
        # Test AnalyticsPlugin
        analytics_plugin = AnalyticsPlugin(config)
        assert analytics_plugin.config == config
        
        # Test FormatterPlugin
        formatter_plugin = FormatterPlugin(config)
        assert formatter_plugin.config == config
        
        # Test HandlerPlugin
        handler_plugin = HandlerPlugin(config)
        assert handler_plugin.config == config
        
        # Test SecurityPlugin
        security_plugin = SecurityPlugin(config)
        assert security_plugin.config == config
        
        # Test PerformancePlugin
        performance_plugin = PerformancePlugin(config)
        assert performance_plugin.config == config

    def test_plugin_state_management(self):
        """Test plugin state management."""
        # Test enable/disable cycle
        plugin = AnalyticsPlugin()
        assert plugin.is_enabled() is True
        
        plugin.disable()
        assert plugin.is_enabled() is False
        
        plugin.enable()
        assert plugin.is_enabled() is True
        
        # Test reset
        plugin.reset()  # Should not change enabled state
        assert plugin.is_enabled() is True

    def test_plugin_method_override(self):
        """Test that plugin methods can be overridden."""
        class TestPlugin(AnalyticsPlugin):
            def process_event(self, event):
                return {"overridden": True}
            
            def get_insights(self):
                return {"overridden": True}
        
        plugin = TestPlugin()
        result = plugin.process_event({"test": "event"})
        assert result == {"overridden": True}
        
        insights = plugin.get_insights()
        assert insights == {"overridden": True} 