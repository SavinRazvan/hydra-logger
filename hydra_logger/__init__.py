"""
Hydra-Logger: Advanced Python Logging with Data Protection and Analytics

A comprehensive logging library with built-in data protection, security validation,
plugin support, and analytics capabilities.

Features:
- Multi-layered logging system
- Data sanitization and security validation
- Plugin architecture for extensibility
- Performance monitoring and analytics
- Fallback mechanisms for data protection
- Async support for high-performance applications
"""

__version__ = "0.4.0"
__author__ = "Savin Ionut Razvan"

# Core imports
from hydra_logger.core.logger import HydraLogger
from hydra_logger.async_hydra.async_logger import AsyncHydraLogger
from hydra_logger.core.constants import (
    LOG_LEVELS,
    VALID_FORMATS,
    VALID_DESTINATION_TYPES,
    DEFAULT_CONFIG,
    Colors,
    NAMED_COLORS,
    DEFAULT_COLORS,
    PERFORMANCE_SETTINGS,
    FILE_SETTINGS,
    ASYNC_SETTINGS,
    PLUGIN_SETTINGS,
    ANALYTICS_SETTINGS,
    ENV_VARS,
    DEFAULT_FORMATS,
    PII_PATTERNS,
    FRAMEWORK_PATTERNS,
    CLOUD_PROVIDER_PATTERNS
)

# Configuration imports
from hydra_logger.config.loaders import (
    load_config,
    load_config_from_dict,
    load_config_from_env,
    get_default_config,
    get_async_default_config,
    create_log_directories,
    validate_config,
    merge_configs
)

# Plugin system imports
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

# Data protection imports
from hydra_logger.data_protection.fallbacks import FallbackHandler
from hydra_logger.data_protection.security import (
    DataSanitizer,
    SecurityValidator,
    DataHasher
)

# Error handling imports
from hydra_logger.core.error_handler import (
    get_error_tracker,
    track_error,
    track_hydra_error,
    track_configuration_error,
    track_validation_error,
    track_plugin_error,
    track_async_error,
    track_performance_error,
    track_runtime_error,
    error_context,
    get_error_stats,
    clear_error_stats,
    close_error_tracker
)

# Exception imports
from hydra_logger.core.exceptions import (
    HydraLoggerError,
    ConfigurationError,
    ValidationError,
    HandlerError,
    FormatterError,
    AsyncError,
    PluginError,
    DataProtectionError,
    AnalyticsError,
    CompatibilityError,
    PerformanceError
)

# Backward compatibility imports
try:
    from hydra_logger.config.models import LoggingConfig
except ImportError:
    # Fallback for older versions
    LoggingConfig = None

# Main logger class for easy access
__all__ = [
    # Core
    "HydraLogger",
    "AsyncHydraLogger",
    
    # Configuration
    "LoggingConfig",
    "load_config",
    "load_config_from_dict",
    "load_config_from_env",
    "get_default_config",
    "get_async_default_config",
    "create_log_directories",
    "validate_config",
    "merge_configs",
    
    # Plugin system
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
    "PerformancePlugin",
    
    # Data protection
    "FallbackHandler",
    "DataSanitizer",
    "SecurityValidator",
    "DataHasher",
    
    # Error handling
    "get_error_tracker",
    "track_error",
    "track_hydra_error",
    "track_configuration_error",
    "track_validation_error",
    "track_plugin_error",
    "track_async_error",
    "track_performance_error",
    "track_runtime_error",
    "error_context",
    "get_error_stats",
    "clear_error_stats",
    "close_error_tracker",
    
    # Exceptions
    "HydraLoggerError",
    "ConfigurationError",
    "ValidationError",
    "HandlerError",
    "FormatterError",
    "AsyncError",
    "PluginError",
    "DataProtectionError",
    "AnalyticsError",
    "CompatibilityError",
    "PerformanceError",
    
    # Constants
    "LOG_LEVELS",
    "VALID_FORMATS",
    "VALID_DESTINATION_TYPES",
    "DEFAULT_CONFIG",
    "Colors",
    "NAMED_COLORS",
    "DEFAULT_COLORS",
    "PERFORMANCE_SETTINGS",
    "FILE_SETTINGS",
    "ASYNC_SETTINGS",
    "PLUGIN_SETTINGS",
    "ANALYTICS_SETTINGS",
    "ENV_VARS",
    "DEFAULT_FORMATS",
    "PII_PATTERNS",
    "FRAMEWORK_PATTERNS",
    "CLOUD_PROVIDER_PATTERNS"
]

# Convenience function for quick setup
from typing import Optional
def create_logger(
    config: Optional[dict] = None,
    enable_security: bool = True,
    enable_sanitization: bool = True,
    enable_plugins: bool = True
) -> HydraLogger:
    """
    Create a HydraLogger instance with default configuration.
    
    Args:
        config: Optional configuration dictionary
        enable_security: Enable security validation
        enable_sanitization: Enable data sanitization
        enable_plugins: Enable plugin system
        
    Returns:
        HydraLogger instance
    """
    return HydraLogger(
        config=config,
        enable_security=enable_security,
        enable_sanitization=enable_sanitization,
        enable_plugins=enable_plugins
    )

# Add convenience function to __all__
__all__.append("create_logger")
