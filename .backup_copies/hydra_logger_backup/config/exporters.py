"""
Hydra-Logger Configuration Exporters

This module provides comprehensive utilities for saving and exporting configurations
to various formats with automatic validation and error handling.

SUPPORTED FORMATS:
- YAML files (with PyYAML)
- TOML files (with tomli/toml)
- JSON files (with built-in json)
- Python dictionaries
- Configuration registry management

FEATURES:
- Automatic format detection and conversion
- Comprehensive error handling and validation
- Configuration registry for sharing and reusing configs
- Type-safe configuration with automatic validation
- Support for all major configuration formats
- Metadata and tagging for configuration management

USAGE EXAMPLES:

Saving to Files:
    from hydra_logger.config import save_config_to_yaml, save_config_to_toml, save_config_to_json
    
    # Save to YAML file
    save_config_to_yaml(config, "config.yaml")
    
    # Save to TOML file
    save_config_to_toml(config, "config.toml")
    
    # Save to JSON file
    save_config_to_json(config, "config.json")

Exporting to Strings:
    from hydra_logger.config import config_to_yaml_string, config_to_toml_string, config_to_json_string
    
    # Export to YAML string
    yaml_str = config_to_yaml_string(config)
    
    # Export to TOML string
    toml_str = config_to_toml_string(config)
    
    # Export to JSON string
    json_str = config_to_json_string(config)

Configuration Registry:
    from hydra_logger.config import config_registry
    
    # Save configuration to registry
    config_registry.save_config(
        "my_app",
        config,
        description="Custom configuration for my application",
        tags=["production", "web"]
    )
    
    # Load configuration from registry
    loaded_config = config_registry.load_config("my_app")
    
    # List available configurations
    configs = config_registry.list_configs()

Converting to Dictionary:
    from hydra_logger.config import config_to_dict
    
    # Convert to dictionary
    config_dict = config_to_dict(config)
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime

from .models import LoggingConfig
from ..core.exceptions import ConfigurationError


def save_config_to_yaml(config: LoggingConfig, file_path: Union[str, Path]) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: LoggingConfig instance to save
        file_path: Path where to save the YAML file
        
    Raises:
        ConfigurationError: If saving fails
    """
    try:
        import yaml
    except ImportError:
        raise ConfigurationError("PyYAML is required to save YAML configurations. Install with: pip install PyYAML")
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config_dict = config.model_dump()
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2, sort_keys=False)
    except Exception as e:
        raise ConfigurationError(f"Failed to save configuration to {file_path}: {e}")


def save_config_to_toml(config: LoggingConfig, file_path: Union[str, Path]) -> None:
    """
    Save configuration to a TOML file.
    
    Args:
        config: LoggingConfig instance to save
        file_path: Path where to save the TOML file
        
    Raises:
        ConfigurationError: If saving fails
    """
    try:
        import tomli_w
    except ImportError:
        raise ConfigurationError("tomli-w is required to save TOML configurations. Install with: pip install tomli-w")
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config_dict = config.model_dump()
        with open(file_path, 'wb') as f:
            tomli_w.dump(config_dict, f)
    except Exception as e:
        raise ConfigurationError(f"Failed to save configuration to {file_path}: {e}")


def save_config_to_json(config: LoggingConfig, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: LoggingConfig instance to save
        file_path: Path where to save the JSON file
        indent: JSON indentation level
        
    Raises:
        ConfigurationError: If saving fails
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config_dict = config.model_dump()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=indent, ensure_ascii=False, sort_keys=False)
    except Exception as e:
        raise ConfigurationError(f"Failed to save configuration to {file_path}: {e}")


def config_to_dict(config: LoggingConfig) -> Dict[str, Any]:
    """
    Convert configuration to a Python dictionary.
    
    Args:
        config: LoggingConfig instance to convert
        
    Returns:
        Dictionary representation of the configuration
    """
    return config.model_dump()


def config_to_yaml_string(config: LoggingConfig) -> str:
    """
    Convert configuration to a YAML string.
    
    Args:
        config: LoggingConfig instance to convert
        
    Returns:
        YAML string representation of the configuration
        
    Raises:
        ConfigurationError: If conversion fails
    """
    try:
        import yaml
    except ImportError:
        raise ConfigurationError("PyYAML is required to convert to YAML. Install with: pip install PyYAML")
    
    try:
        config_dict = config.model_dump()
        return yaml.dump(config_dict, default_flow_style=False, indent=2, sort_keys=False)
    except Exception as e:
        raise ConfigurationError(f"Failed to convert configuration to YAML: {e}")


def config_to_toml_string(config: LoggingConfig) -> str:
    """
    Convert configuration to a TOML string.
    
    Args:
        config: LoggingConfig instance to convert
        
    Returns:
        TOML string representation of the configuration
        
    Raises:
        ConfigurationError: If conversion fails
    """
    try:
        import tomli_w
    except ImportError:
        raise ConfigurationError("tomli-w is required to convert to TOML. Install with: pip install tomli-w")
    
    try:
        config_dict = config.model_dump()
        return tomli_w.dumps(config_dict)
    except Exception as e:
        raise ConfigurationError(f"Failed to convert configuration to TOML: {e}")


def config_to_json_string(config: LoggingConfig, indent: int = 2) -> str:
    """
    Convert configuration to a JSON string.
    
    Args:
        config: LoggingConfig instance to convert
        indent: JSON indentation level
        
    Returns:
        JSON string representation of the configuration
    """
    try:
        config_dict = config.model_dump()
        return json.dumps(config_dict, indent=indent, ensure_ascii=False, sort_keys=False)
    except Exception as e:
        raise ConfigurationError(f"Failed to convert configuration to JSON: {e}")


class ConfigurationRegistry:
    """
    Registry for managing saved configurations.
    
    This class provides functionality to save, load, and manage multiple configurations
    with metadata like creation time, description, and tags.
    """
    
    def __init__(self, registry_path: Union[str, Path] = "config_registry.json"):
        self.registry_path = Path(registry_path)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load the configuration registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self._configs = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load configuration registry: {e}")
                self._configs = {}
    
    def _save_registry(self) -> None:
        """Save the configuration registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self._configs, f, indent=2, ensure_ascii=False, sort_keys=True)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration registry: {e}")
    
    def save_config(
        self, 
        name: str, 
        config: LoggingConfig, 
        description: str = "", 
        tags: Optional[list] = None,
        file_format: str = "yaml"
    ) -> None:
        """
        Save a configuration to the registry.
        
        Args:
            name: Unique name for the configuration
            config: LoggingConfig instance to save
            description: Description of the configuration
            tags: List of tags for categorization
            file_format: Format to save the configuration file (yaml, toml, json)
        """
        if name in self._configs:
            raise ConfigurationError(f"Configuration '{name}' already exists. Use update_config() to modify it.")
        
        # Create config directory
        config_dir = self.registry_path.parent / "saved_configs"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension and save method
        if file_format.lower() == "yaml":
            config_file = config_dir / f"{name}.yaml"
            save_config_to_yaml(config, config_file)
        elif file_format.lower() == "toml":
            config_file = config_dir / f"{name}.toml"
            save_config_to_toml(config, config_file)
        elif file_format.lower() == "json":
            config_file = config_dir / f"{name}.json"
            save_config_to_json(config, config_file)
        else:
            raise ConfigurationError(f"Unsupported file format: {file_format}")
        
        # Save metadata
        self._configs[name] = {
            "file_path": str(config_file),
            "file_format": file_format,
            "description": description,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "layers": list(config.layers.keys()),
            "default_level": config.default_level,
            "features": {
                "security": config.enable_security,
                "sanitization": config.enable_sanitization,
                "plugins": config.enable_plugins,
                "performance_monitoring": config.enable_performance_monitoring
            }
        }
        
        self._save_registry()
    
    def load_config(self, name: str) -> LoggingConfig:
        """
        Load a configuration from the registry.
        
        Args:
            name: Name of the configuration to load
            
        Returns:
            LoggingConfig instance
            
        Raises:
            ConfigurationError: If configuration not found or loading fails
        """
        if name not in self._configs:
            raise ConfigurationError(f"Configuration '{name}' not found in registry")
        
        config_info = self._configs[name]
        config_file = Path(config_info["file_path"])
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_file}")
        
        # Load based on file format
        from .loaders import load_config
        return load_config(config_file)
    
    def update_config(
        self, 
        name: str, 
        config: LoggingConfig, 
        description: Optional[str] = None,
        tags: Optional[list] = None
    ) -> None:
        """
        Update an existing configuration in the registry.
        
        Args:
            name: Name of the configuration to update
            config: New LoggingConfig instance
            description: New description (optional)
            tags: New tags (optional)
        """
        if name not in self._configs:
            raise ConfigurationError(f"Configuration '{name}' not found in registry")
        
        config_info = self._configs[name]
        file_format = config_info["file_format"]
        
        # Save the updated configuration
        self.save_config(name, config, description or config_info["description"], tags or config_info["tags"], file_format)
        
        # Update metadata
        self._configs[name]["updated_at"] = datetime.now().isoformat()
        self._configs[name]["layers"] = list(config.layers.keys())
        self._configs[name]["default_level"] = config.default_level
        self._configs[name]["features"] = {
            "security": config.enable_security,
            "sanitization": config.enable_sanitization,
            "plugins": config.enable_plugins,
            "performance_monitoring": config.enable_performance_monitoring
        }
        
        self._save_registry()
    
    def delete_config(self, name: str) -> None:
        """
        Delete a configuration from the registry.
        
        Args:
            name: Name of the configuration to delete
        """
        if name not in self._configs:
            raise ConfigurationError(f"Configuration '{name}' not found in registry")
        
        config_info = self._configs[name]
        config_file = Path(config_info["file_path"])
        
        # Delete the configuration file
        if config_file.exists():
            config_file.unlink()
        
        # Remove from registry
        del self._configs[name]
        self._save_registry()
    
    def list_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        List all configurations in the registry.
        
        Returns:
            Dictionary mapping configuration names to their metadata
        """
        return self._configs.copy()
    
    def search_configs(self, tags: Optional[list] = None, features: Optional[Dict[str, bool]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Search configurations by tags or features.
        
        Args:
            tags: List of tags to search for
            features: Dictionary of features to search for
            
        Returns:
            Dictionary of matching configurations
        """
        results = {}
        
        for name, config_info in self._configs.items():
            match = True
            
            # Search by tags
            if tags:
                config_tags = set(config_info.get("tags", []))
                search_tags = set(tags)
                if not config_tags.intersection(search_tags):
                    match = False
            
            # Search by features
            if features and match:
                config_features = config_info.get("features", {})
                for feature, value in features.items():
                    if config_features.get(feature) != value:
                        match = False
                        break
            
            if match:
                results[name] = config_info
        
        return results
    
    def get_config_info(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific configuration.
        
        Args:
            name: Name of the configuration
            
        Returns:
            Configuration metadata
        """
        if name not in self._configs:
            raise ConfigurationError(f"Configuration '{name}' not found in registry")
        
        return self._configs[name].copy()


# Global registry instance
config_registry = ConfigurationRegistry()


# Convenience functions
def save_config(config: LoggingConfig, file_path: Union[str, Path], format: str = "yaml") -> None:
    """
    Save configuration to a file.
    
    Args:
        config: LoggingConfig instance to save
        file_path: Path where to save the file
        format: File format (yaml, toml, json)
    """
    if format.lower() == "yaml":
        save_config_to_yaml(config, file_path)
    elif format.lower() == "toml":
        save_config_to_toml(config, file_path)
    elif format.lower() == "json":
        save_config_to_json(config, file_path)
    else:
        raise ConfigurationError(f"Unsupported format: {format}")


def export_config(config: LoggingConfig, format: str = "yaml") -> str:
    """
    Export configuration to a string.
    
    Args:
        config: LoggingConfig instance to export
        format: Export format (yaml, toml, json)
        
    Returns:
        String representation of the configuration
    """
    if format.lower() == "yaml":
        return config_to_yaml_string(config)
    elif format.lower() == "toml":
        return config_to_toml_string(config)
    elif format.lower() == "json":
        return config_to_json_string(config)
    else:
        raise ConfigurationError(f"Unsupported format: {format}")
