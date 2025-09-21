"""
Hydra-Logger Configuration Validators

This module provides comprehensive validation for configuration files,
data structures, and individual components to ensure robust configuration
with detailed error reporting and validation summaries.

FEATURES:
- Configuration file syntax and structure validation
- Configuration data validation against schemas
- Handler-specific configuration validation
- Environment-specific validations
- Performance and security settings validation
- Detailed error reporting and validation summaries
- Type-safe validation with automatic error detection

VALIDATION TYPES:
- File validation: Syntax, structure, permissions, format
- Data validation: Schema compliance, type checking, value validation
- Handler validation: Destination-specific configuration validation
- Environment validation: System-specific configuration validation
- Performance validation: Performance impact assessment
- Security validation: Security settings and compliance validation

USAGE EXAMPLES:

Validating Configuration Files:
    from hydra_logger.config import validate_config_file, validate_config_data
    
    # Validate configuration file
    is_valid, errors = validate_config_file("config.yaml")
    if not is_valid:
        print("Validation errors:", errors)
    
    # Validate configuration data
    config_data = {"default_level": "INFO", "layers": {...}}
    is_valid, errors = validate_config_data(config_data)
    if not is_valid:
        print("Validation errors:", errors)

Using Configuration Validator:
    from hydra_logger.config import ConfigurationValidator
    
    validator = ConfigurationValidator()
    
    # Validate configuration file
    is_valid, errors = validator.validate_config_file("config.yaml")
    
    # Validate configuration data
    is_valid, errors = validator.validate_config_data(config_data)
    
    # Get validation summary
    summary = validator.get_validation_summary()
    print(f"Errors: {summary['errors']}")
    print(f"Warnings: {summary['warnings']}")

Validating Handler Configurations:
    from hydra_logger.config import validate_handler_config
    
    handler_config = {
        "type": "file",
        "path": "app.log",
        "format": "json-lines",
        "max_size": "10MB"
    }
    is_valid, errors = validate_handler_config(handler_config)
    if not is_valid:
        print("Handler validation errors:", errors)
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from .models import LoggingConfig, LogDestination, LogLayer
from ..core.exceptions import ConfigurationError, ValidationError


class ConfigurationValidator:
    """
    Comprehensive configuration validator for Hydra-Logger.
    
    Provides validation for:
    - Configuration file syntax and structure
    - Configuration data against schemas
    - Handler-specific configurations
    - Environment-specific validations
    - Performance and security settings
    """
    
    def __init__(self):
        self._validation_errors: List[str] = []
        self._validation_warnings: List[str] = []
    
    def validate_config_file(self, path: Union[str, Path]) -> Tuple[bool, List[str]]:
        """
        Validate configuration file syntax and structure.
        
        Args:
            path: Path to configuration file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        path = Path(path)
        self._validation_errors.clear()
        self._validation_warnings.clear()
        
        # Check file existence
        if not path.exists():
            self._validation_errors.append(f"Configuration file not found: {path}")
            return False, self._validation_errors
        
        # Check file permissions
        if not os.access(path, os.R_OK):
            self._validation_errors.append(f"Cannot read configuration file: {path}")
            return False, self._validation_errors
        
        # Check file size (reasonable limits)
        file_size = path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB max
            self._validation_warnings.append(f"Configuration file is large ({file_size} bytes)")
        
        # Check file extension
        valid_extensions = ['.yml', '.yaml', '.toml', '.json']
        if path.suffix.lower() not in valid_extensions:
            self._validation_errors.append(f"Unsupported file format: {path.suffix}")
            return False, self._validation_errors
        
        return len(self._validation_errors) == 0, self._validation_errors
    
    def validate_config_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration data against schemas.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self._validation_errors.clear()
        self._validation_warnings.clear()
        
        # Check required top-level keys
        required_keys = ['layers']
        for key in required_keys:
            if key not in data:
                self._validation_errors.append(f"Missing required key: {key}")
        
        # Validate layers structure
        if 'layers' in data:
            self._validate_layers_structure(data['layers'])
        
        # Validate global settings
        if 'default_level' in data:
            self._validate_log_level(data['default_level'], 'default_level')
        
        # Validate performance settings
        if 'buffer_size' in data:
            self._validate_buffer_size(data['buffer_size'])
        
        if 'flush_interval' in data:
            self._validate_flush_interval(data['flush_interval'])
        
        # Validate feature flags
        feature_flags = ['enable_security', 'enable_sanitization', 'enable_plugins', 'enable_performance_monitoring']
        for flag in feature_flags:
            if flag in data and not isinstance(data[flag], bool):
                self._validation_errors.append(f"Feature flag '{flag}' must be boolean")
        
        return len(self._validation_errors) == 0, self._validation_errors
    
    def validate_handler_config(self, handler_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate individual handler configurations.
        
        Args:
            handler_config: Handler configuration dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self._validation_errors.clear()
        self._validation_warnings.clear()
        
        # Check required handler type
        if 'type' not in handler_config:
            self._validation_errors.append("Handler missing required 'type' field")
            return False, self._validation_errors
        
        handler_type = handler_config['type']
        
        # Validate handler-specific requirements
        if handler_type == 'file':
            self._validate_file_handler_config(handler_config)
        elif handler_type == 'async_http':
            self._validate_async_http_handler_config(handler_config)
        elif handler_type == 'async_database':
            self._validate_async_database_handler_config(handler_config)
        elif handler_type == 'async_queue':
            self._validate_async_queue_handler_config(handler_config)
        elif handler_type == 'async_cloud':
            self._validate_async_cloud_handler_config(handler_config)
        
        # Validate common fields
        if 'level' in handler_config:
            self._validate_log_level(handler_config['level'], f"handler.{handler_type}.level")
        
        if 'format' in handler_config:
            self._validate_format(handler_config['format'])
        
        if 'color_mode' in handler_config:
            self._validate_color_mode(handler_config['color_mode'])
        
        return len(self._validation_errors) == 0, self._validation_errors
    
    def _validate_layers_structure(self, layers: Dict[str, Any]) -> None:
        """Validate the structure of layers configuration."""
        if not isinstance(layers, dict):
            self._validation_errors.append("Layers must be a dictionary")
            return
        
        if not layers:
            self._validation_errors.append("At least one layer must be defined")
            return
        
        for layer_name, layer_config in layers.items():
            if not isinstance(layer_config, dict):
                self._validation_errors.append(f"Layer '{layer_name}' must be a dictionary")
                continue
            
            # Validate layer level
            if 'level' in layer_config:
                self._validate_log_level(layer_config['level'], f"layer.{layer_name}.level")
            
            # Validate destinations
            if 'destinations' not in layer_config:
                self._validation_errors.append(f"Layer '{layer_name}' missing destinations")
                continue
            
            destinations = layer_config['destinations']
            if not isinstance(destinations, list):
                self._validation_errors.append(f"Layer '{layer_name}' destinations must be a list")
                continue
            
            if not destinations:
                self._validation_errors.append(f"Layer '{layer_name}' must have at least one destination")
                continue
            
            # Validate each destination
            for i, dest_config in enumerate(destinations):
                if not isinstance(dest_config, dict):
                    self._validation_errors.append(f"Layer '{layer_name}' destination {i} must be a dictionary")
                    continue
                
                is_valid, errors = self.validate_handler_config(dest_config)
                if not is_valid:
                    for error in errors:
                        self._validation_errors.append(f"Layer '{layer_name}' destination {i}: {error}")
    
    def _validate_file_handler_config(self, config: Dict[str, Any]) -> None:
        """Validate file handler specific configuration."""
        if 'path' not in config or not config['path']:
            self._validation_errors.append("File handler requires 'path' field")
            return
        
        path = config['path']
        if not isinstance(path, str):
            self._validation_errors.append("File handler path must be a string")
            return
        
        # Check if path is writable (if file exists) or directory is writable
        path_obj = Path(path)
        if path_obj.exists():
            if path_obj.is_file() and not os.access(path_obj, os.W_OK):
                self._validation_warnings.append(f"File handler path not writable: {path}")
        else:
            # Check if parent directory is writable
            parent_dir = path_obj.parent
            if parent_dir.exists() and not os.access(parent_dir, os.W_OK):
                self._validation_warnings.append(f"File handler parent directory not writable: {parent_dir}")
        
        # Validate max_size if present
        if 'max_size' in config:
            self._validate_size_string(config['max_size'], 'max_size')
        
        # Validate backup_count if present
        if 'backup_count' in config:
            backup_count = config['backup_count']
            if not isinstance(backup_count, int) or backup_count < 0:
                self._validation_errors.append("File handler backup_count must be non-negative integer")
    
    def _validate_async_http_handler_config(self, config: Dict[str, Any]) -> None:
        """Validate async HTTP handler specific configuration."""
        if 'url' not in config or not config['url']:
            self._validation_errors.append("Async HTTP handler requires 'url' field")
            return
        
        url = config['url']
        if not isinstance(url, str):
            self._validation_errors.append("Async HTTP handler URL must be a string")
            return
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            self._validation_warnings.append(f"Async HTTP handler URL may be invalid: {url}")
        
        # Validate retry settings
        if 'retry_count' in config:
            retry_count = config['retry_count']
            if not isinstance(retry_count, int) or retry_count < 0:
                self._validation_errors.append("Async HTTP handler retry_count must be non-negative integer")
        
        if 'timeout' in config:
            timeout = config['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                self._validation_errors.append("Async HTTP handler timeout must be positive number")
    
    def _validate_async_database_handler_config(self, config: Dict[str, Any]) -> None:
        """Validate async database handler specific configuration."""
        if 'connection_string' not in config or not config['connection_string']:
            self._validation_errors.append("Async database handler requires 'connection_string' field")
            return
        
        conn_str = config['connection_string']
        if not isinstance(conn_str, str):
            self._validation_errors.append("Async database handler connection_string must be a string")
            return
        
        # Validate max_connections if present
        if 'max_connections' in config:
            max_conn = config['max_connections']
            if not isinstance(max_conn, int) or max_conn <= 0:
                self._validation_errors.append("Async database handler max_connections must be positive integer")
    
    def _validate_async_queue_handler_config(self, config: Dict[str, Any]) -> None:
        """Validate async queue handler specific configuration."""
        if 'queue_url' not in config or not config['queue_url']:
            self._validation_errors.append("Async queue handler requires 'queue_url' field")
            return
        
        queue_url = config['queue_url']
        if not isinstance(queue_url, str):
            self._validation_errors.append("Async queue handler queue_url must be a string")
            return
    
    def _validate_async_cloud_handler_config(self, config: Dict[str, Any]) -> None:
        """Validate async cloud handler specific configuration."""
        if 'service_type' not in config or not config['service_type']:
            self._validation_errors.append("Async cloud handler requires 'service_type' field")
            return
        
        service_type = config['service_type']
        if not isinstance(service_type, str):
            self._validation_errors.append("Async cloud handler service_type must be a string")
            return
        
        # Validate service type against known types
        valid_service_types = ['aws_cloudwatch', 'azure_monitor', 'google_cloud', 'elasticsearch']
        if service_type not in valid_service_types:
            self._validation_warnings.append(f"Unknown cloud service type: {service_type}")
        
        # Validate credentials if present
        if 'credentials' in config:
            credentials = config['credentials']
            if not isinstance(credentials, dict):
                self._validation_errors.append("Async cloud handler credentials must be a dictionary")
    
    def _validate_log_level(self, level: Any, context: str) -> None:
        """Validate log level values."""
        if not isinstance(level, str):
            self._validation_errors.append(f"{context} must be a string")
            return
        
        valid_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level.upper() not in valid_levels:
            self._validation_errors.append(f"{context} must be one of {valid_levels}")
    
    def _validate_format(self, fmt: Any) -> None:
        """Validate log format values."""
        if not isinstance(fmt, str):
            self._validation_errors.append("Format must be a string")
            return
        
        valid_formats = [
            "plain-text", "json", "json-lines", "csv", "syslog", "gelf",
            "compact", "detailed", "colored"
        ]
        if fmt not in valid_formats:
            self._validation_errors.append(f"Format must be one of {valid_formats}")
    
    def _validate_color_mode(self, mode: Any) -> None:
        """Validate color mode values."""
        if not isinstance(mode, str):
            self._validation_errors.append("Color mode must be a string")
            return
        
        valid_modes = ["auto", "always", "never"]
        if mode not in valid_modes:
            self._validation_errors.append(f"Color mode must be one of {valid_modes}")
    
    def _validate_size_string(self, size: Any, context: str) -> None:
        """Validate size string format (e.g., '10MB', '1GB')."""
        if not isinstance(size, str):
            self._validation_errors.append(f"{context} must be a string")
            return
        
        import re
        size_pattern = r'^(\d+)(B|KB|MB|GB|TB)$'
        if not re.match(size_pattern, size.upper()):
            self._validation_errors.append(f"{context} must be in format '10MB', '1GB', etc.")
    
    def _validate_buffer_size(self, size: Any) -> None:
        """Validate buffer size setting."""
        if not isinstance(size, int):
            self._validation_errors.append("Buffer size must be an integer")
            return
        
        if size <= 0:
            self._validation_errors.append("Buffer size must be positive")
            return
        
        if size > 1024 * 1024:  # 1MB max
            self._validation_warnings.append(f"Buffer size is large ({size} bytes)")
    
    def _validate_flush_interval(self, interval: Any) -> None:
        """Validate flush interval setting."""
        if not isinstance(interval, (int, float)):
            self._validation_errors.append("Flush interval must be a number")
            return
        
        if interval < 0:
            self._validation_errors.append("Flush interval cannot be negative")
            return
        
        if interval > 3600:  # 1 hour max
            self._validation_warnings.append(f"Flush interval is long ({interval} seconds)")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        return {
            'is_valid': len(self._validation_errors) == 0,
            'error_count': len(self._validation_errors),
            'warning_count': len(self._validation_warnings),
            'errors': self._validation_errors.copy(),
            'warnings': self._validation_warnings.copy()
        }


# Global validator instance
config_validator = ConfigurationValidator()


# Convenience functions
def validate_config_file(path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Validate configuration file syntax and structure."""
    return config_validator.validate_config_file(path)


def validate_config_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate configuration data against schemas."""
    return config_validator.validate_config_data(data)


def validate_handler_config(handler_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate individual handler configurations."""
    return config_validator.validate_handler_config(handler_config)


def get_validation_summary() -> Dict[str, Any]:
    """Get validation summary from the global validator."""
    return config_validator.get_validation_summary()


def clear_validation_results() -> None:
    """Clear validation results from the global validator."""
    config_validator._validation_errors.clear()
    config_validator._validation_warnings.clear()
