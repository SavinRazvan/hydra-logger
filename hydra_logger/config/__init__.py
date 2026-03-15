"""
Public configuration exports for Hydra-Logger.

This module exposes pydantic models plus template-based helpers for building
validated `LoggingConfig` instances.
"""

from .models import (
    LoggingConfig,
    LogLayer,
    LogDestination,
    HandlerConfig,
    FileHandlerConfig,
    ConsoleHandlerConfig,
    MemoryHandlerConfig,
    ModularConfig,
)

from .defaults import (
    ConfigurationTemplates,
    get_default_config,
    get_custom_config,
    get_development_config,
    get_production_config,
    get_named_config,
    list_available_configs,
    templates,
)

from .configuration_templates import (
    configuration_templates,
    register_configuration_template,
    get_configuration_template,
    list_configuration_templates,
    has_configuration_template,
    validate_configuration_template,
)


__all__ = [
    # Models
    "LoggingConfig",
    "LogLayer",
    "LogDestination",
    "HandlerConfig",
    "FileHandlerConfig",
    "ConsoleHandlerConfig",
    "MemoryHandlerConfig",
    "ModularConfig",
    # Templates
    "ConfigurationTemplates",
    "get_default_config",
    "get_custom_config",
    "get_development_config",
    "get_production_config",
    "get_named_config",
    "list_available_configs",
    "templates",
    # Configuration Templates
    "configuration_templates",
    "register_configuration_template",
    "get_configuration_template",
    "list_configuration_templates",
    "has_configuration_template",
    "validate_configuration_template",
]
