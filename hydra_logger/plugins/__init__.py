"""
Plugin system for Hydra-Logger.

This module provides the plugin architecture for extending Hydra-Logger
functionality with custom analytics, formatters, and handlers.
"""

from hydra_logger.plugins.registry import (
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

__all__ = [
    "register_plugin",
    "get_plugin",
    "list_plugins",
    "unregister_plugin",
    "load_plugin_from_path",
    "clear_plugins",
    "AnalyticsPlugin",
    "FormatterPlugin",
    "HandlerPlugin",
    "SecurityPlugin",
    "PerformancePlugin"
]
