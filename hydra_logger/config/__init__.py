"""
Role: Public exports for hydra_logger.config; no runtime logic besides import wiring.
Used By:
 - Importers of `hydra_logger.config` public API.
Depends On:
 - hydra_logger
Notes:
 - Re-exports the hydra_logger.config public API with stable import paths.
"""

from .destinations import LogDestination
from .layers import LogLayer
from .configuration_templates import (
    configuration_templates,
    get_configuration_template,
    has_configuration_template,
    list_configuration_templates,
    register_configuration_template,
    validate_configuration_template,
)
from .runtime import LoggingConfig
from .defaults import (
    ConfigurationTemplates,
    get_custom_config,
    get_default_config,
    get_development_config,
    get_named_config,
    get_production_config,
    list_available_configs,
    templates,
)
from .models import (
    ConsoleHandlerConfig,
    FileHandlerConfig,
    HandlerConfig,
    MemoryHandlerConfig,
    ModularConfig,
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
