"""
Role: Implements hydra_logger.config.configuration_templates functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - hydra_logger
 - typing
Notes:
 - Stores reusable configuration templates selected by name.
"""

import logging
from typing import Callable, Dict

# from .defaults import ConfigurationTemplates as
# DefaultConfigurationTemplates  # unused
from ..core.exceptions import HydraLoggerError
from .models import LoggingConfig

_logger = logging.getLogger(__name__)


class ConfigurationTemplates:
    """Registry for built-in and custom logging configuration templates."""

    def __init__(self):
        self._configs: Dict[str, Callable[[], LoggingConfig]] = {}
        self._descriptions: Dict[str, str] = {}
        self._setup_builtin_configs()

    def _setup_builtin_configs(self):
        """Setup built-in configuration templates using the unified system."""
        try:
            from .defaults import (
                get_custom_config,
                get_default_config,
                get_development_config,
                get_production_config,
            )

            self.register_template(
                "default", "Default configuration with performance focus"
            )(get_default_config)
            self.register_template(
                "development", "Development-friendly configuration with debug output"
            )(get_development_config)
            self.register_template(
                "production", "Production-ready configuration with security and monitoring"
            )(get_production_config)
            self.register_template(
                "custom", "Custom configuration with user-specified features"
            )(get_custom_config)
        except Exception as exc:
            _logger.exception("Failed to setup built-in configuration templates: %s", exc)
            raise

    def register_template(self, name: str, description: str = "") -> Callable:
        """Register a named template and return a decorator for its factory."""
        if not isinstance(name, str) or not name.strip():
            raise HydraLoggerError(
                "Configuration template name must be a non-empty string"
            )

        def decorator(func: Callable[[], LoggingConfig]) -> Callable[[], LoggingConfig]:
            if not callable(func):
                raise HydraLoggerError(
                    f"Configuration template '{name}' must be a callable function"
                )

            self._configs[name] = func
            self._descriptions[name] = description
            return func

        return decorator

    def has_template(self, name: str) -> bool:
        """Check if a configuration template exists."""
        return name in self._configs

    def get_template(self, name: str) -> LoggingConfig:
        """Get a configuration template by name."""
        if name not in self._configs:
            raise HydraLoggerError(f"Unknown configuration template: {name}")

        try:
            return self._configs[name]()
        except Exception as e:
            _logger.exception("Failed creating configuration template '%s': %s", name, e)
            raise HydraLoggerError(
                f"Failed to create configuration template '{name}': {e}"
            )

    def list_templates(self) -> Dict[str, str]:
        """List all available configuration templates."""
        return self._descriptions.copy()

    def remove_template(self, name: str) -> None:
        """Remove a configuration template."""
        if name in self._configs:
            del self._configs[name]
            del self._descriptions[name]

    def clear_custom_templates(self) -> None:
        """Clear all custom configuration templates (keep built-ins)."""
        builtin_names = {"default", "development", "production", "custom"}

        custom_names = [
            name for name in self._configs.keys() if name not in builtin_names
        ]
        for name in custom_names:
            self.remove_template(name)

    def get_available_templates(self) -> Dict[str, str]:
        """Return all registered template names with their descriptions."""
        return self._descriptions.copy()

    def validate_template(self, name: str) -> bool:
        """Build and validate the named template configuration."""
        try:
            config = self.get_template(name)
            return config.validate_configuration()
        except Exception as e:
            _logger.exception("Configuration template validation failed for '%s': %s", name, e)
            raise HydraLoggerError(
                f"Configuration template validation failed for '{name}': {e}"
            )


# Global instance
configuration_templates = ConfigurationTemplates()


# Convenience functions
def register_configuration_template(name: str, description: str = "") -> Callable:
    """Register a configuration template."""
    return configuration_templates.register_template(name, description)


def get_configuration_template(name: str) -> LoggingConfig:
    """Get a configuration template by name."""
    return configuration_templates.get_template(name)


def list_configuration_templates() -> Dict[str, str]:
    """List all available configuration templates."""
    return configuration_templates.list_templates()


def has_configuration_template(name: str) -> bool:
    """Check if a configuration template exists."""
    return configuration_templates.has_template(name)


def validate_configuration_template(name: str) -> bool:
    """Validate a configuration template."""
    return configuration_templates.validate_template(name)
