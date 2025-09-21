"""
Configuration Interface for Hydra-Logger

This module defines the abstract interface for configuration components
including loading, validation, and management of logging configurations.
It ensures consistent behavior across all configuration implementations.

ARCHITECTURE:
- ConfigInterface: Abstract interface for all configuration implementations
- Defines contract for configuration loading, validation, and management
- Ensures consistent behavior across different configuration types
- Supports various configuration sources (files, dictionaries, environment variables)

CORE FEATURES:
- Configuration loading from multiple sources
- Configuration validation and error reporting
- Configuration updates and management
- State tracking and status reporting
- Error handling and recovery

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import ConfigInterface
    from typing import Any, Dict, Union, List
    
    class FileConfig(ConfigInterface):
        def __init__(self, file_path: str):
            self.file_path = file_path
            self._config = {}
            self._loaded = False
        
        def load_config(self, source: Union[str, Dict, Any]) -> bool:
            try:
                # Load configuration from file
                with open(source, 'r') as f:
                    self._config = json.load(f)
                self._loaded = True
                return True
            except Exception:
                return False
        
        def get_config(self) -> Dict[str, Any]:
            return self._config.copy()
        
        def update_config(self, updates: Dict[str, Any]) -> bool:
            try:
                self._config.update(updates)
                return True
            except Exception:
                return False
        
        def validate_config(self) -> bool:
            # Implement validation logic
            return True
        
        def get_validation_errors(self) -> List[str]:
            # Return validation errors
            return []
        
        def is_loaded(self) -> bool:
            return self._loaded

Configuration Management:
    from hydra_logger.interfaces import ConfigInterface
    
    def manage_config(config: ConfigInterface, source: str):
        \"\"\"Manage configuration using the interface.\"\"\"
        # Load configuration
        if config.load_config(source):
            print("Configuration loaded successfully")
            
            # Validate configuration
            if config.validate_config():
                print("Configuration is valid")
            else:
                errors = config.get_validation_errors()
                print(f"Configuration errors: {errors}")
            
            # Get current configuration
            current_config = config.get_config()
            print(f"Current config: {current_config}")
        else:
            print("Failed to load configuration")

Polymorphic Usage:
    from hydra_logger.interfaces import ConfigInterface
    
    def process_configs(configs: List[ConfigInterface]):
        \"\"\"Process any configurations that implement ConfigInterface.\"\"\"
        for config in configs:
            if config.is_loaded():
                if config.validate_config():
                    print(f"Config is valid: {config.get_config()}")
                else:
                    errors = config.get_validation_errors()
                    print(f"Config has errors: {errors}")

INTERFACE CONTRACTS:
- load_config(): Load configuration from source
- get_config(): Get current configuration dictionary
- update_config(): Update configuration with new values
- validate_config(): Validate current configuration
- get_validation_errors(): Get list of validation errors
- is_loaded(): Check if configuration is loaded

ERROR HANDLING:
- All methods return boolean success indicators
- Validation errors are collected and reported
- Graceful handling of invalid configurations
- Clear error messages and status reporting

BENEFITS:
- Consistent configuration API across implementations
- Easy testing with mock configurations
- Clear contracts for custom configuration types
- Polymorphic usage without tight coupling
- Better configuration management and validation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List


class ConfigInterface(ABC):
    """
    Abstract interface for all configuration implementations.
    
    This interface defines the contract that all configuration components must implement,
    ensuring consistent behavior across different configuration types.
    """
    
    @abstractmethod
    def load_config(self, source: Union[str, Dict, Any]) -> bool:
        """
        Load configuration from source.
        
        Args:
            source: Configuration source (file path, dict, etc.)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Configuration dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration with new values.
        
        Args:
            updates: Configuration updates
            
        Returns:
            True if updated successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate current configuration.
        
        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_validation_errors(self) -> List[str]:
        """
        Get configuration validation errors.
        
        Returns:
            List of validation error messages
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """
        Check if configuration is loaded.
        
        Returns:
            True if loaded, False otherwise
        """
        raise NotImplementedError
