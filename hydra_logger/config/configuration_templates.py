"""
Hydra-Logger Configuration Templates System

This module provides a registry system for predefined logging configurations
that can be applied with simple method calls. It provides a centralized
system for managing common configuration patterns and templates.

FEATURES:
- Registry system for predefined logging configurations
- Simple method calls for configuration application
- Built-in configurations for common use cases
- Type-safe configuration with automatic validation
- Performance-oriented defaults with optional features
- Easy custom configuration registration

BUILT-IN CONFIGURATIONS:
- "default": Default configuration with performance focus
- "development": Development-friendly configuration with debug output
- "production": Production-ready configuration with security and monitoring
- "custom": Customizable configuration with user-specified features

USAGE EXAMPLES:

Using Built-in Configurations:
    from hydra_logger.config import get_configuration_template

    # Get default configuration
    config = get_configuration_template("default")

    # Get production configuration
    config = get_configuration_template("production")

    # Get development configuration
    config = get_configuration_template("development")

Registering Custom Configurations:
    from hydra_logger.config import register_configuration_template

    @register_configuration_template("my_app", "Custom configuration for my application")
    def my_app_config():
        return LoggingConfig(
            default_level="INFO",
            layers={
                "app": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(type="console", format="colored", use_colors=True),
                        LogDestination(type="file", path="my_app.log", format="json-lines")
                    ]
                )
            }
        )

    # Use the custom configuration
    config = get_configuration_template("my_app")

Listing Available Configurations:
    from hydra_logger.config import list_configuration_templates

    configs = list_configuration_templates()
    print(configs)  # {'default': 'Optimized default...', 'production': '...', ...}
"""

from typing import Dict, Callable
from .models import LoggingConfig
# from .defaults import ConfigurationTemplates as DefaultConfigurationTemplates  # unused
from ..core.exceptions import HydraLoggerError


class ConfigurationTemplates:
    """
    Registry for predefined logging configuration templates.

    This class provides a registry system for logging configurations that can be
    applied with simple method calls. It provides a centralized system for
    managing common configuration patterns and templates.

    Features:
    - Built-in configurations for common use cases
    - Custom configuration template registration
    - Type-safe configuration with automatic validation
    - Performance-oriented defaults with optional features
    - Easy template management and discovery

    Built-in Configurations:
    - "default": Default configuration with performance focus
    - "development": Development-friendly configuration with debug output
    - "production": Production-ready configuration with security and monitoring
    - "custom": Customizable configuration with user-specified features

    Examples:
        # Get built-in configuration template
        config = configuration_templates.get_template("production")

        # Register custom configuration template
        @configuration_templates.register_template("my_app", "Custom configuration for my application")
        def my_app_config():
            return LoggingConfig(...)

        # List available configuration templates
        templates = configuration_templates.list_templates()
    """

    def __init__(self):
        self._configs: Dict[str, Callable[[], LoggingConfig]] = {}
        self._descriptions: Dict[str, str] = {}
        self._setup_builtin_configs()

    def _setup_builtin_configs(self):
        """Setup built-in configuration templates using the unified system."""
        # Use the unified ConfigurationTemplates for all built-in configs
        from .defaults import (
            get_default_config,
            get_development_config,
            get_production_config,
            get_custom_config,
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

    def register_template(self, name: str, description: str = "") -> Callable:
        """
        Register a custom configuration template.

        Args:
            name: The name of the configuration template
            description: Optional description of the template

        Returns:
            Decorator function that registers the template
        """
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
        """
        Get all available configuration templates including built-ins and custom ones.

        Returns:
            Dictionary mapping template names to descriptions
        """
        return self._descriptions.copy()

    def validate_template(self, name: str) -> bool:
        """
        Validate a configuration template by name.

        Args:
            name: Name of the template to validate

        Returns:
            True if valid

        Raises:
            HydraLoggerError: If validation fails
        """
        try:
            config = self.get_template(name)
            return config.validate_configuration()
        except Exception as e:
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
