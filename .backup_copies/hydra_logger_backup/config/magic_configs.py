"""
Hydra-Logger Magic Configuration System

This module provides a registry system for custom logging configurations
that can be applied with simple method calls like logger.for_production().
It integrates with the unified ConfigurationTemplates system to provide
a single source of truth for all configurations.

FEATURES:
- Registry system for custom logging configurations
- Simple method calls for configuration application
- Built-in configurations for common use cases
- Integration with ConfigurationTemplates system
- Type-safe configuration with automatic validation
- Performance-first defaults with optional optimizations

BUILT-IN CONFIGURATIONS:
- "default": Optimized configuration for maximum performance
- "development": Development-friendly configuration with debug output
- "production": Production-ready configuration with security and monitoring
- "custom": Customizable configuration with user-specified features

USAGE EXAMPLES:

Using Built-in Configurations:
    from hydra_logger.config import get_magic_config
    
    # Get default configuration (maximum performance)
    config = get_magic_config("default")
    
    # Get production configuration
    config = get_magic_config("production")
    
    # Get development configuration
    config = get_magic_config("development")

Registering Custom Configurations:
    from hydra_logger.config import register_magic_config
    
    @register_magic_config("my_app", "Custom configuration for my application")
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
    config = get_magic_config("my_app")

Listing Available Configurations:
    from hydra_logger.config import list_magic_configs
    
    configs = list_magic_configs()
    print(configs)  # {'default': 'Optimized default...', 'production': '...', ...}
"""

from typing import Dict, Callable, Any, Optional, Union
from .models import LoggingConfig, LogDestination, LogLayer
from .defaults import ConfigurationTemplates
from ..core.exceptions import HydraLoggerError


class MagicConfigs:
    """
    Registry for magic configurations.
    
    This class provides a registry system for logging configurations that can be
    applied with simple method calls. It integrates with the unified ConfigurationTemplates
    system to provide a single source of truth for all configurations.
    
    Features:
    - Built-in configurations for common use cases
    - Custom configuration registration
    - Type-safe configuration with automatic validation
    - Performance-first defaults with optional optimizations
    - Integration with ConfigurationTemplates system
    
    Built-in Configurations:
    - "default": Optimized configuration for maximum performance
    - "development": Development-friendly configuration with debug output
    - "production": Production-ready configuration with security and monitoring
    - "custom": Customizable configuration with user-specified features
    
    Examples:
        # Get built-in configuration
        config = magic_configs.get_config("production")
        
        # Register custom configuration
        @magic_configs.register("my_app", "Custom configuration for my application")
        def my_app_config():
            return LoggingConfig(...)
        
        # List available configurations
        configs = magic_configs.list_configs()
    """
    
    def __init__(self):
        self._configs: Dict[str, Callable[[], LoggingConfig]] = {}
        self._descriptions: Dict[str, str] = {}
        self._setup_builtin_configs()
    
    def _setup_builtin_configs(self):
        """Setup built-in magic configurations using the unified system."""
        # Use the unified ConfigurationTemplates for all built-in configs
        templates = ConfigurationTemplates()
        
        self.register("default", "Optimized default configuration for maximum performance")(templates.get_default_config)
        self.register("development", "Development-friendly configuration with debug output")(templates.get_development_config)
        self.register("production", "Production-ready configuration with security and monitoring")(templates.get_production_config)
        self.register("custom", "Custom configuration with user-specified features")(templates.get_custom_config)
    
    def register(self, name: str, description: str = "") -> Callable:
        """
        Register a custom magic configuration.
        
        Args:
            name: The name of the magic config
            description: Optional description of the config
            
        Returns:
            Decorator function that registers the config
        """
        if not isinstance(name, str) or not name.strip():
            raise HydraLoggerError("Magic config name must be a non-empty string")
        
        def decorator(func: Callable[[], LoggingConfig]) -> Callable[[], LoggingConfig]:
            if not callable(func):
                raise HydraLoggerError(f"Magic config '{name}' must be a callable function")
            
            self._configs[name] = func
            self._descriptions[name] = description
            return func
        
        return decorator
    
    def has_config(self, name: str) -> bool:
        """Check if a magic config exists."""
        return name in self._configs
    
    def get_config(self, name: str) -> LoggingConfig:
        """Get a magic configuration by name."""
        if name not in self._configs:
            raise HydraLoggerError(f"Unknown magic config: {name}")
        
        try:
            return self._configs[name]()
        except Exception as e:
            raise HydraLoggerError(f"Failed to create magic config '{name}': {e}")
    
    def list_configs(self) -> Dict[str, str]:
        """List all available magic configurations."""
        return self._descriptions.copy()
    
    def remove_config(self, name: str) -> None:
        """Remove a magic configuration."""
        if name in self._configs:
            del self._configs[name]
            del self._descriptions[name]
    
    def clear_custom_configs(self) -> None:
        """Clear all custom configurations (keep built-ins)."""
        builtin_names = {
            "default", "development", "production", "custom"
        }
        
        custom_names = [name for name in self._configs.keys() if name not in builtin_names]
        for name in custom_names:
            self.remove_config(name)
    
    def get_available_configs(self) -> Dict[str, str]:
        """
        Get all available configurations including built-ins and custom ones.
        
        Returns:
            Dictionary mapping configuration names to descriptions
        """
        return self._descriptions.copy()
    
    def validate_config(self, name: str) -> bool:
        """
        Validate a magic configuration by name.
        
        Args:
            name: Name of the configuration to validate
            
        Returns:
            True if valid
            
        Raises:
            HydraLoggerError: If validation fails
        """
        try:
            config = self.get_config(name)
            return config.validate_configuration()
        except Exception as e:
            raise HydraLoggerError(f"Configuration validation failed for '{name}': {e}")


# Global instance
magic_configs = MagicConfigs()

# Convenience functions
def register_magic_config(name: str, description: str = "") -> Callable:
    """Register a magic configuration."""
    return magic_configs.register(name, description)

def get_magic_config(name: str) -> LoggingConfig:
    """Get a magic configuration by name."""
    return magic_configs.get_config(name)

def list_magic_configs() -> Dict[str, str]:
    """List all available magic configurations."""
    return magic_configs.list_configs()

def has_magic_config(name: str) -> bool:
    """Check if a magic config exists."""
    return magic_configs.has_config(name)

def validate_magic_config(name: str) -> bool:
    """Validate a magic configuration by name."""
    return magic_configs.validate_config(name)
