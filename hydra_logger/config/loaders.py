"""
Configuration loaders for Hydra-Logger.

This module provides configuration loading functionality for YAML, TOML,
and other configuration formats with comprehensive error handling.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import ValidationError

from hydra_logger.config.models import LoggingConfig
from hydra_logger.core.exceptions import ConfigurationError

try:
    import tomllib
    TOMLDecodeError = tomllib.TOMLDecodeError
except ImportError:
    try:
        import tomli as tomllib
        TOMLDecodeError = tomllib.TOMLDecodeError
    except ImportError:
        tomllib = None
        TOMLDecodeError = Exception


def load_config(config_path: Union[str, Path]) -> LoggingConfig:
    """
    Load configuration from a file.
    
    Args:
        config_path: Path to configuration file (YAML or TOML)
        
    Returns:
        LoggingConfig: Loaded configuration
        
    Raises:
        ConfigurationError: If configuration loading fails
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        elif config_path.suffix.lower() == '.toml':
            if tomllib is None:
                raise ConfigurationError("TOML support not available. Install tomli or use Python 3.11+")
            with open(config_path, 'rb') as f:
                config_data = tomllib.load(f)
        else:
            raise ConfigurationError(f"Unsupported configuration format: {config_path.suffix}")
        
        return LoggingConfig(**config_data)
        
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {e}")


def load_config_from_dict(config_data: Dict[str, Any]) -> LoggingConfig:
    """
    Load configuration from a dictionary.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        LoggingConfig: Loaded configuration
        
    Raises:
        ConfigurationError: If configuration loading fails
    """
    try:
        return LoggingConfig(**config_data)
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {e}")


def load_config_from_env() -> LoggingConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        LoggingConfig: Loaded configuration
    """
    # This is a simplified version - in practice, you'd parse environment variables
    # and convert them to the appropriate configuration structure
    config_data = {
        "default_level": os.getenv("HYDRA_LOG_LEVEL", "DEBUG"),
        "layers": {
            "DEFAULT": {
                "level": os.getenv("HYDRA_LOG_LEVEL", "DEBUG"),
                "destinations": [
                    {
                        "type": "console",
                        "level": os.getenv("HYDRA_LOG_LEVEL", "DEBUG"),
                        "format": os.getenv("HYDRA_LOG_FORMAT", "plain-text")
                    }
                ]
            }
        }
    }
    
    return load_config_from_dict(config_data)


def get_default_config() -> LoggingConfig:
    """
    Get the default configuration.
    
    Returns:
        LoggingConfig: Default configuration
    """
    from hydra_logger.core.constants import DEFAULT_CONFIG
    return load_config_from_dict(DEFAULT_CONFIG)


def get_async_default_config() -> LoggingConfig:
    """
    Get the default async configuration.
    
    Returns:
        LoggingConfig: Default async configuration
    """
    config_data = {
        "default_level": "INFO",
        "layers": {
            "DEFAULT": {
                "level": "INFO",
                "destinations": [
                    {
                        "type": "console",
                        "level": "INFO",
                        "format": "plain-text"
                    },
                    {
                        "type": "file",
                        "path": "logs/async.log",
                        "format": "json",
                        "level": "DEBUG"
                    }
                ]
            }
        }
    }
    
    return load_config_from_dict(config_data)


def create_log_directories(config: LoggingConfig) -> None:
    """
    Create log directories for file destinations.
    
    Args:
        config: Logging configuration
    """
    for layer_name, layer_config in config.layers.items():
        for destination in layer_config.destinations:
            if destination.type == "file" and destination.path:
                log_path = Path(destination.path)
                log_path.parent.mkdir(parents=True, exist_ok=True)


def validate_config(config: LoggingConfig) -> bool:
    """
    Validate a configuration.
    
    Args:
        config: Logging configuration to validate
        
    Returns:
        bool: True if configuration is valid
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    try:
        # This will raise ValidationError if invalid
        LoggingConfig(**config.model_dump())
        return True
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed: {e}")


def merge_configs(base_config: LoggingConfig, override_config: Dict[str, Any]) -> LoggingConfig:
    """
    Merge two configurations.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration dictionary
        
    Returns:
        LoggingConfig: Merged configuration
    """
    # Handle None or empty override
    if override_config is None:
        return base_config
    
    base_dict = base_config.model_dump()
    
    # Deep merge the configurations
    def deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    merged_dict = deep_merge(base_dict, override_config)
    return load_config_from_dict(merged_dict) 