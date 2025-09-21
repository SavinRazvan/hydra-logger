"""
Hydra-Logger Configuration Setup

This module handles automatic setup and configuration management for Hydra-Logger,
including directory structure creation, configuration template management, and
smart configuration detection and loading.

FEATURES:
- Automatic creation of logs directory structure
- Configuration template management and generation
- Smart configuration detection and loading
- Example configuration templates
- Directory structure validation
- Configuration file management

DIRECTORY STRUCTURE:
- logs/ - Main logs directory
- logs/_configs/ - Configuration templates directory
- logs/_configs/example_config.yaml - Example configuration template
- logs/_configs/production.yaml - Production configuration template
- logs/_configs/development.yaml - Development configuration template

USAGE EXAMPLES:

Basic Setup:
    from hydra_logger.config import setup_logs_directory
    
    # Set up logs directory structure
    manager = setup_logs_directory()
    
    # Create example configuration
    manager.create_example_config()

Using Logs Directory Manager:
    from hydra_logger.config import LogsDirectoryManager
    
    # Initialize with custom base path
    manager = LogsDirectoryManager("/path/to/project")
    
    # Set up directory structure
    manager.setup_logs_structure()
    
    # List available configurations
    configs = manager.list_available_configs()
    
    # Get configuration path
    config_path = manager.get_config_path("production")

Configuration Template Management:
    from hydra_logger.config import get_logs_manager
    
    manager = get_logs_manager()
    
    # Create example configuration
    manager.create_example_config()
    
    # Generate detailed YAML template
    yaml_template = manager.generate_detailed_yaml_template(config)
    
    # Save configuration template
    manager.save_config_template("my_config", config)
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from .models import LoggingConfig
from .exporters import config_to_yaml_string


class LogsDirectoryManager:
    """
    Manages the logs directory structure and configuration templates.
    
    This class handles automatic setup and management of the Hydra-Logger
    directory structure, including configuration templates and example files.
    
    Features:
    - Automatic directory structure creation
    - Configuration template management
    - Example configuration generation
    - Smart configuration detection and loading
    - Directory structure validation
    - Configuration file management
    
    Directory Structure:
    - logs/ - Main logs directory
    - logs/_configs/ - Configuration templates directory
    - logs/_configs/example_config.yaml - Example configuration template
    - logs/_configs/production.yaml - Production configuration template
    - logs/_configs/development.yaml - Development configuration template
    
    Examples:
        # Initialize with default base path
        manager = LogsDirectoryManager()
        
        # Initialize with custom base path
        manager = LogsDirectoryManager("/path/to/project")
        
        # Set up directory structure
        manager.setup_logs_structure()
        
        # Create example configuration
        manager.create_example_config()
        
        # List available configurations
        configs = manager.list_available_configs()
        
        # Get configuration path
        config_path = manager.get_config_path("production")
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the logs directory manager.
        
        Args:
            base_path: Base path for logs directory (defaults to current working directory)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.logs_dir = self.base_path / "logs"
        self.configs_dir = self.logs_dir / "_configs"
        self.example_config_path = self.configs_dir / "example_config.yaml"
    
    def setup_logs_structure(self) -> None:
        """
        Set up the logs directory structure if it doesn't exist.
        
        Creates:
        - logs/ directory
        - logs/_configs/ directory  
        - logs/_configs/example_config.yaml template
        """
        # Create logs directory if it doesn't exist
        if not self.logs_dir.exists():
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created logs directory: {self.logs_dir}")
        
        # Create _configs directory if it doesn't exist
        if not self.configs_dir.exists():
            self.configs_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created configs directory: {self.configs_dir}")
        
        # Create example config template if it doesn't exist
        if not self.example_config_path.exists():
            self._create_example_config_template()
            print(f"📄 Created example config template: {self.example_config_path}")
    
    def _create_example_config_template(self) -> None:
        """Create a detailed example configuration template."""
        from .defaults import get_custom_config
        
        # Create a comprehensive example configuration
        example_config = get_custom_config(
            default_level="INFO",
            console_enabled=True,
            file_enabled=True,
            file_path="example_app.log",
            file_format="json-lines",
            enable_security=True,
            error_layer=True,
            debug_layer=True,
            warning_layer=True,
            info_layer=True,
            critical_layer=True,
            custom_layers={
                "database": {
                    "level": "INFO",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "database.log",
                            "format": "json-lines",
                            "max_size": "10MB",
                            "backup_count": 5
                        }
                    ]
                },
                "api": {
                    "level": "DEBUG", 
                    "destinations": [
                        {
                            "type": "file",
                            "path": "api.log",
                            "format": "json-lines"
                        },
                        {
                            "type": "console",
                            "format": "colored"
                        }
                    ]
                },
                "performance": {
                    "level": "WARNING",
                    "destinations": [
                        {
                            "type": "file",
                            "path": "performance.log",
                            "format": "fast-plain",
                            "max_size": "5MB",
                            "backup_count": 3
                        }
                    ]
                }
            }
        )
        
        # Convert to YAML with detailed comments
        yaml_content = self._generate_detailed_yaml_template(example_config)
        
        # Write the template file
        with open(self.example_config_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
    
    def _generate_detailed_yaml_template(self, config: LoggingConfig) -> str:
        """Generate a detailed YAML template with comprehensive comments."""
        template = """# Hydra Logger Configuration Template
# This is a comprehensive example showing all available options
# Copy this file and modify it according to your needs

# =============================================================================
# BASIC SETTINGS
# =============================================================================

# Default log level for all layers (DEBUG, INFO, WARNING, ERROR, CRITICAL)
default_level: INFO

# Performance settings
performance:
  # Buffer size for file operations (bytes)
  buffer_size: 8192
  
  # How often to flush buffers (seconds)
  flush_interval: 1.0
  
  # Enable performance monitoring
  enable_monitoring: false

# Security settings
security:
  # Enable security features (sanitization, validation)
  enabled: true
  
  # Sanitize log messages (remove sensitive data)
  sanitize_messages: true
  
  # Validate log records
  validate_records: true

# =============================================================================
# LAYERS CONFIGURATION
# =============================================================================
# Each layer can have different log levels and destinations
# You can create unlimited custom layers

layers:
  # Default layer - handles all logs
  default:
    level: INFO
    destinations:
      # Console output with colors
      - type: console
        format: colored
        use_colors: true
      
      # File output in JSON Lines format
      - type: file
        path: example_app.log
        format: json-lines
        max_size: 10MB
        backup_count: 5
  
  # Error layer - only ERROR and CRITICAL messages
  error:
    level: ERROR
    destinations:
      - type: file
        path: error.log
        format: json-lines
        max_size: 5MB
        backup_count: 3
  
  # Debug layer - all messages including DEBUG
  debug:
    level: DEBUG
    destinations:
      - type: file
        path: debug.log
        format: fast-plain
        max_size: 5MB
        backup_count: 2
  
  # Warning layer - WARNING, ERROR, CRITICAL messages
  warning:
    level: WARNING
    destinations:
      - type: file
        path: warning.log
        format: json-lines
        max_size: 5MB
        backup_count: 3
  
  # Info layer - INFO, WARNING, ERROR, CRITICAL messages
  info:
    level: INFO
    destinations:
      - type: file
        path: info.log
        format: json-lines
        max_size: 10MB
        backup_count: 5
  
  # Critical layer - only CRITICAL messages
  critical:
    level: CRITICAL
    destinations:
      - type: file
        path: critical.log
        format: json-lines
        max_size: 2MB
        backup_count: 10
      - type: console
        format: colored
        use_colors: true
  
  # =============================================================================
  # CUSTOM LAYERS - UNLIMITED EXAMPLES
  # =============================================================================
  
  # Database operations layer
  database:
    level: INFO
    destinations:
      - type: file
        path: database.log
        format: json-lines
        max_size: 10MB
        backup_count: 5
  
  # API requests layer
  api:
    level: DEBUG
    destinations:
      - type: file
        path: api.log
        format: json-lines
      - type: console
        format: colored
  
  # Performance monitoring layer
  performance:
    level: WARNING
    destinations:
      - type: file
        path: performance.log
        format: fast-plain
        max_size: 5MB
        backup_count: 3

# =============================================================================
# DESTINATION TYPES AND FORMATS
# =============================================================================
# 
# Available destination types:
# - console: Output to console/terminal
# - file: Output to file (synchronous)
# - async_file: Output to file (asynchronous, better performance)
# 
# Available formats by destination type:
# 
# CONSOLE destinations:
# - colored: Colored console output (ANSI colors)
# - plain-text: Standard plain text
# 
# FILE destinations:
# - json-lines: JSON Lines format (recommended for production)
# - fast-plain: Fast plain text format
# - csv: CSV format
# - plain-text: Standard plain text
# 
# File-specific options:
# - max_size: Maximum file size before rotation (e.g., "10MB", "1GB")
# - backup_count: Number of backup files to keep
# 
# Console-specific options:
# - use_colors: Enable colored output (true/false)
# 
# IMPORTANT: Only console destinations can use "colored" format!
# File destinations should use json-lines, fast-plain, csv, or plain-text.
# 
# =============================================================================
# USAGE EXAMPLES
# =============================================================================
# 
# 1. Load this configuration:
#    from hydra_logger.config import load_config
#    config = load_config("logs/_configs/example_config.yaml")
# 
# 2. Create a logger with this config:
#    from hydra_logger import create_sync_logger
#    logger = create_sync_logger(config, name="my_app")
# 
# 3. Use different layers:
#    logger.info("This goes to default layer")
#    logger.error("This goes to error layer")
#    logger.debug("This goes to debug layer")
# 
# 4. Use custom layers:
#    logger.log("database", "INFO", "Database query executed")
#    logger.log("api", "DEBUG", "API request received")
#    logger.log("performance", "WARNING", "Slow query detected")
# 
# 5. Save your custom configuration:
#    from hydra_logger.config import save_config
#    save_config(config, "logs/_configs/my_custom_config.yaml")
# 
# =============================================================================
# PERFORMANCE TIPS
# =============================================================================
# 
# 1. Use "json-lines" format for production (fastest parsing)
# 2. Use "fast-plain" for high-volume logging
# 3. Set appropriate buffer_size for your use case
# 4. Use async_file for high-performance applications
# 5. Set reasonable max_size and backup_count to manage disk space
# 6. Use different layers to separate concerns and improve performance
# 
# =============================================================================
# SECURITY CONSIDERATIONS
# =============================================================================
# 
# 1. Enable security features for production
# 2. Be careful with sensitive data in log messages
# 3. Use appropriate file permissions
# 4. Consider log rotation and cleanup policies
# 5. Monitor log file sizes and disk usage
"""
        return template
    
    def get_configs_directory(self) -> Path:
        """Get the path to the configs directory."""
        return self.configs_dir
    
    def list_available_configs(self) -> list:
        """List all available configuration files in the _configs directory."""
        if not self.configs_dir.exists():
            return []
        
        config_files = []
        for file_path in self.configs_dir.glob("*.yaml"):
            config_files.append(file_path.name)
        for file_path in self.configs_dir.glob("*.yml"):
            config_files.append(file_path.name)
        for file_path in self.configs_dir.glob("*.toml"):
            config_files.append(file_path.name)
        for file_path in self.configs_dir.glob("*.json"):
            config_files.append(file_path.name)
        
        return sorted(config_files)
    
    def get_config_path(self, config_name: str) -> Optional[Path]:
        """
        Get the full path to a configuration file.
        
        Args:
            config_name: Name of the config file (with or without extension)
            
        Returns:
            Path to the config file, or None if not found
        """
        # Add extension if not provided
        if not any(config_name.endswith(ext) for ext in ['.yaml', '.yml', '.toml', '.json']):
            config_name += '.yaml'
        
        config_path = self.configs_dir / config_name
        return config_path if config_path.exists() else None


# Global instance for easy access
_logs_manager = LogsDirectoryManager()


def setup_logs_directory(base_path: Optional[str] = None) -> LogsDirectoryManager:
    """
    Set up the logs directory structure and return the manager.
    
    Args:
        base_path: Base path for logs directory (defaults to current working directory)
        
    Returns:
        LogsDirectoryManager instance
    """
    manager = LogsDirectoryManager(base_path)
    manager.setup_logs_structure()
    return manager


def get_logs_manager() -> LogsDirectoryManager:
    """Get the global logs directory manager instance."""
    return _logs_manager


def ensure_logs_structure() -> None:
    """Ensure the logs directory structure exists (convenience function)."""
    _logs_manager.setup_logs_structure()

