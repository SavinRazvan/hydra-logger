"""
Plugin System for Hydra-Logger

This module provides a comprehensive plugin system for extending logging
functionality with custom formatters, handlers, security features, performance
monitoring, and analytics. It includes automatic discovery, management,
and analysis capabilities.

FEATURES:
- Base plugin classes for different plugin types
- Automatic plugin discovery and loading
- Plugin registry and lifecycle management
- Plugin analysis and compatibility checking
- Background processing support

PLUGIN TYPES:
- FormatterPlugin: Custom log formatters
- HandlerPlugin: Custom log handlers
- SecurityPlugin: Security and threat detection
- PerformancePlugin: Performance monitoring
- AnalyticsPlugin: Analytics and insights

USAGE:
    from hydra_logger.plugins import PluginManager, FormatterPlugin
    
    # Create plugin manager
    manager = PluginManager()
    
    # Create custom formatter plugin
    class MyFormatter(FormatterPlugin):
        def format(self, record):
            return f"[{record.level}] {record.message}"
    
    # Register and use plugin
    formatter = MyFormatter("custom_formatter", "my_format")
    manager.register_plugin(formatter)
"""

from .base import BasePlugin, AnalyticsPlugin, FormatterPlugin, HandlerPlugin, SecurityPlugin, PerformancePlugin
from .registry import PluginRegistry
from .manager import PluginManager
from .discovery import PluginDiscovery
from .analyzer import PluginAnalyzer

__all__ = [
    # Base plugin classes
    "BasePlugin",
    "AnalyticsPlugin", 
    "FormatterPlugin",
    "HandlerPlugin",
    "SecurityPlugin",
    "PerformancePlugin",
    
    # Plugin management
    "PluginRegistry",
    "PluginManager",
    "PluginDiscovery",
    "PluginAnalyzer",
]
