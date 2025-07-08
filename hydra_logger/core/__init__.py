"""
Core module for Hydra-Logger.

This module contains the core components of Hydra-Logger including
the main logger class, constants, and exceptions.
"""

from hydra_logger.core.logger import HydraLogger
from hydra_logger.core.constants import *
from hydra_logger.core.exceptions import *

__all__ = [
    "HydraLogger",
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
    "CLOUD_PROVIDER_PATTERNS",
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
    "PerformanceError"
]
