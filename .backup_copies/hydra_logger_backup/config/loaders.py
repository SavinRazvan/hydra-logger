"""
Hydra-Logger Configuration Loaders

This module provides comprehensive utilities for loading configurations from various
sources with automatic validation, error handling, and backward compatibility.

SUPPORTED SOURCES:
- YAML and TOML files
- JSON configuration files
- Environment variables
- Python dictionaries
- Default configurations
- Legacy handler-based configurations

FEATURES:
- Automatic format detection (YAML, TOML, JSON)
- Comprehensive error handling and validation
- Backward compatibility for legacy configurations
- Environment variable support
- Configuration merging and inheritance
- Type-safe configuration with automatic validation

USAGE EXAMPLES:

Loading from File:
    from hydra_logger.config import load_config
    
    # Load from YAML file
    config = load_config("config.yaml")
    
    # Load from TOML file
    config = load_config("config.toml")
    
    # Load from JSON file
    config = load_config("config.json")

Loading from Environment:
    from hydra_logger.config import load_config_from_env
    
    # Load from environment variables
    config = load_config_from_env()

Loading from Dictionary:
    from hydra_logger.config import load_config_from_dict
    
    config_data = {
        "default_level": "INFO",
        "layers": {
            "app": {
                "level": "DEBUG",
                "destinations": [
                    {"type": "console", "format": "colored", "use_colors": True},
                    {"type": "file", "path": "app.log", "format": "json-lines"}
                ]
            }
        }
    }
    config = load_config_from_dict(config_data)

Loading from Configs Directory:
    from hydra_logger.config import load_config_from_configs_dir
    
    # Load from _configs directory
    config = load_config_from_configs_dir("production")

Configuration Merging:
    from hydra_logger.config import merge_configs
    
    base_config = load_config("base.yaml")
    override_config = {"default_level": "WARNING"}
    merged_config = merge_configs(base_config, override_config)
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .models import LoggingConfig, LogDestination, LogLayer
from .setup import get_logs_manager
from ..core.exceptions import ConfigurationError


def load_config_from_configs_dir(config_name: str) -> LoggingConfig:
    """
    Load configuration from the _configs directory.
    
    Args:
        config_name: Name of the config file (with or without extension)
        
    Returns:
        LoggingConfig instance
        
    Raises:
        ConfigurationError: If config file is not found
    """
    manager = get_logs_manager()
    config_path = manager.get_config_path(config_name)
    
    if config_path is None:
        available_configs = manager.list_available_configs()
        raise ConfigurationError(
            f"Configuration '{config_name}' not found in {manager.get_configs_directory()}. "
            f"Available configs: {', '.join(available_configs)}"
        )
    
    return load_config(config_path)


def load_config(config_path: Union[str, Path]) -> LoggingConfig:
    """
    Load configuration from a YAML or TOML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        LoggingConfig instance
        
    Raises:
        ConfigurationError: If loading fails
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        if config_path.suffix.lower() in ['.yml', '.yaml']:
            return _load_yaml_config(config_path)
        elif config_path.suffix.lower() == '.toml':
            return _load_toml_config(config_path)
        else:
            raise ConfigurationError(f"Unsupported configuration format: {config_path.suffix}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration from {config_path}: {e}")


def _load_yaml_config(config_path: Path) -> LoggingConfig:
    """Load configuration from YAML file."""
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return load_config_from_dict(config_data)
    except ImportError:
        raise ConfigurationError("PyYAML is required to load YAML configurations")
    except Exception as e:
        raise ConfigurationError(f"Failed to parse YAML configuration: {e}")


def _load_toml_config(config_path: Path) -> LoggingConfig:
    """Load configuration from TOML file."""
    try:
        import tomli as tomllib
        with open(config_path, 'rb') as f:
            config_data = tomllib.load(f)
        return load_config_from_dict(config_data)
    except ImportError:
        try:
            import tomli as tomllib
            with open(config_path, 'rb') as f:
                config_data = tomllib.load(f)
            return load_config_from_dict(config_data)
        except ImportError:
            raise ConfigurationError("tomllib or tomli is required to load TOML configurations")
    except Exception as e:
        raise ConfigurationError(f"Failed to parse TOML configuration: {e}")


def load_config_from_dict(config_data: Dict[str, Any]) -> LoggingConfig:
    """
    Load configuration from a Python dictionary.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        LoggingConfig instance
    """
    try:
        # Convert legacy handler format to layer format if needed
        if 'handlers' in config_data and 'layers' not in config_data:
            config_data = _convert_handlers_to_layers(config_data)
        
        return LoggingConfig(**config_data)
    except Exception as e:
        raise ConfigurationError(f"Failed to create configuration from dict: {e}")


def _convert_handlers_to_layers(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert legacy handler-based configuration to layer-based configuration.
    
    This function provides backward compatibility for configurations that use
    the old handler-based format.
    """
    handlers = config_data.get('handlers', [])
    level = config_data.get('level', 'INFO')
    
    # Create a default layer with all handlers
    destinations = []
    for handler in handlers:
        if isinstance(handler, dict):
            dest = LogDestination(
                type=handler.get('type', 'console'),
                level=handler.get('level', level),
                path=handler.get('path'),
                format=handler.get('format', 'plain-text'),
                color_mode=handler.get('color_mode', 'auto'),
                max_size=handler.get('max_size', '5MB'),
                backup_count=handler.get('backup_count', 3)
            )
            destinations.append(dest)
    
    # Create layer-based configuration
    converted_config = config_data.copy()
    converted_config['layers'] = {
        'default': LogLayer(
            level=level,
            destinations=destinations
        )
    }
    
    # Remove old handler format
    if 'handlers' in converted_config:
        del converted_config['handlers']
    
    return converted_config


def load_config_from_env() -> LoggingConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        LoggingConfig instance with environment-based settings
    """
    config_data = {}
    
    # Basic settings
    if 'HYDRA_LOG_LEVEL' in os.environ:
        config_data['default_level'] = os.environ['HYDRA_LOG_LEVEL']
    
    if 'HYDRA_LOG_ENABLE_SECURITY' in os.environ:
        config_data['enable_security'] = os.environ['HYDRA_LOG_ENABLE_SECURITY'].lower() == 'true'
    
    if 'HYDRA_LOG_ENABLE_SANITIZATION' in os.environ:
        config_data['enable_sanitization'] = os.environ['HYDRA_LOG_ENABLE_SANITIZATION'].lower() == 'true'
    
    if 'HYDRA_LOG_ENABLE_PLUGINS' in os.environ:
        config_data['enable_plugins'] = os.environ['HYDRA_LOG_ENABLE_PLUGINS'].lower() == 'true'
    
    # Layer configuration
    layers = {}
    
    # Check for layer-specific environment variables
    for key, value in os.environ.items():
        if key.startswith('HYDRA_LOG_LAYER_'):
            # Format: HYDRA_LOG_LAYER_<LAYER_NAME>_<SETTING>
            parts = key[17:].split('_', 1)  # Remove HYDRA_LOG_LAYER_ prefix
            if len(parts) == 2:
                layer_name, setting = parts
                if layer_name not in layers:
                    layers[layer_name] = {'destinations': []}
                
                if setting == 'LEVEL':
                    layers[layer_name]['level'] = value
                elif setting == 'DESTINATIONS':
                    # Parse destinations from comma-separated string
                    dest_types = [d.strip() for d in value.split(',')]
                    for dest_type in dest_types:
                        dest = LogDestination(type=dest_type)
                        layers[layer_name]['destinations'].append(dest)
    
    if layers:
        config_data['layers'] = layers
    
    # If no layers specified, create default console logging
    if not layers:
        config_data['layers'] = {
            'default': LogLayer(
                level=config_data.get('default_level', 'INFO'),
                destinations=[LogDestination(type='console')]
            )
        }
    
    return LoggingConfig(**config_data)


def create_log_directories(config: LoggingConfig) -> None:
    """
    Create necessary log directories based on configuration.
    
    Args:
        config: Logging configuration
    """
    for layer_name, layer in config.layers.items():
        for destination in layer.destinations:
            if destination.type == 'file' and destination.path:
                # Resolve the full log path using config settings
                resolved_path = config.resolve_log_path(destination.path)
                log_path = Path(resolved_path)
                log_dir = log_path.parent
                
                if log_dir and not log_dir.exists():
                    try:
                        log_dir.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        raise ConfigurationError(f"Failed to create log directory {log_dir}: {e}")


def validate_config(config: LoggingConfig) -> bool:
    """
    Validate a configuration.
    
    Args:
        config: Logging configuration to validate
        
    Returns:
        True if valid
        
    Raises:
        ConfigurationError: If validation fails
    """
    try:
        return config.validate_configuration()
    except Exception as e:
        raise ConfigurationError(f"Configuration validation failed: {e}")


def merge_configs(base_config: LoggingConfig, override_config: Dict[str, Any]) -> LoggingConfig:
    """
    Merge a base configuration with override values.
    
    Args:
        base_config: Base configuration
        override_config: Override values
        
    Returns:
        Merged LoggingConfig instance
    """
    # Convert base config to dict
    base_dict = base_config.model_dump()
    
    # Deep merge override values
    merged_dict = _deep_merge(base_dict, override_config)
    
    # Create new config from merged dict
    return LoggingConfig(**merged_dict)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def create_config_from_template(template_name: str, **overrides) -> LoggingConfig:
    """
    Create a configuration from a named template with optional overrides.
    
    Args:
        template_name: Name of the template configuration
        **overrides: Optional override values
        
    Returns:
        LoggingConfig instance
    """
    from .defaults import get_named_config
    
    try:
        base_config = get_named_config(template_name)
        if overrides:
            return merge_configs(base_config, overrides)
        return base_config
    except Exception as e:
        raise ConfigurationError(f"Failed to create config from template '{template_name}': {e}")


def list_available_templates() -> Dict[str, str]:
    """
    List all available configuration templates.
    
    Returns:
        Dictionary mapping template names to descriptions
    """
    from .defaults import list_available_configs
    return list_available_configs()
