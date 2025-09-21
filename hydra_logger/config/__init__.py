"""
Hydra-Logger Configuration System

A comprehensive, production-ready configuration system that provides:
- Pydantic-based models with automatic validation and type safety
- Fluent builder pattern for intuitive configuration creation
- Magic configuration system for pre-built setups
- Multi-format configuration loading (YAML, TOML, JSON, environment)
- Configuration validation and error reporting
- Template system for common use cases
- Export capabilities for configuration sharing

ARCHITECTURE OVERVIEW:
The configuration system is built around three core concepts:

1. LoggingConfig - Root configuration container
   - Manages global settings (security, monitoring, performance)
   - Contains named layers (loggers) with their destinations
   - Provides validation and lifecycle management

2. LogLayer - Logger configuration (equivalent to Python's Logger)
   - Defines log level and enabled state
   - Contains list of destinations (handlers)
   - Supports custom colors and layer-specific settings

3. LogDestination - Handler configuration (equivalent to Python's Handler)
   - Defines output destination (console, file, async_file, etc.)
   - Specifies format, level, and destination-specific settings
   - Supports all major output formats and protocols

PYTHON LOGGING COMPATIBILITY:
The system follows Python logging standards exactly:

- Logger Level (LogLayer.level): Controls message acceptance
- Handler Level (LogDestination.level): Controls message processing  
- Global Default (LoggingConfig.default_level): Fallback for unspecified levels
- Inheritance: Child levels inherit from parent when not explicitly set

PERFORMANCE-FIRST DESIGN:
- Security features disabled by default for maximum performance
- Optimized validation with early exit on errors
- LRU caching for frequently accessed configurations
- Minimal memory footprint with efficient data structures
- Background processing for non-critical operations

USAGE EXAMPLES:

Basic Configuration:
    from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
    
    config = LoggingConfig(
        default_level="INFO",
        layers={
            "app": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(type="console", format="colored"),
                    LogDestination(type="file", path="app.log", format="json-lines")
                ]
            )
        }
    )

Using Builder Pattern:
    from hydra_logger.config import ConfigurationBuilder
    
    config = (ConfigurationBuilder()
              .setLevel("INFO")
              .add_layer_builder("app")
              .setLevel("DEBUG")
              .add_console(format="colored")
              .add_file("app.log", format="json-lines")
              .build())

Using Magic Configurations:
    from hydra_logger.config import get_magic_config
    
    config = get_magic_config("production")  # Pre-built production config
"""

from .models import (
    LoggingConfig,
    LogLayer,
    LogDestination,
    HandlerConfig,
    FileHandlerConfig,
    ConsoleHandlerConfig,
    MemoryHandlerConfig,
    ModularConfig
)

from .defaults import (
    ConfigurationTemplates,
    get_default_config,
    get_custom_config,
    get_development_config,
    get_production_config,
    get_named_config,
    list_available_configs,
    templates
)

from .configuration_templates import (
    ConfigurationTemplates,
    magic_configs,
    register_magic_config,
    get_magic_config,
    list_magic_configs,
    has_magic_config,
    validate_magic_config
)

# Builder module removed - simplified architecture

# Loaders module removed - simplified architecture

# Exporters module removed - simplified architecture

# Validators module removed - simplified architecture

# from .validators import (
#     ConfigurationValidator,
#     config_validator,
#     validate_config_file,
#     validate_config_data,
#     validate_handler_config,
#     get_validation_summary,
#     clear_validation_results
# )

# Setup module removed - simplified architecture


__all__ = [
    # Models
    'LoggingConfig',
    'LogLayer',
    'LogDestination',
    'HandlerConfig',
    'FileHandlerConfig',
    'ConsoleHandlerConfig',
    'MemoryHandlerConfig',
    'ModularConfig',
    
    # Templates
    'ConfigurationTemplates',
    'get_default_config',
    'get_custom_config',
    'get_development_config',
    'get_production_config',
    'get_named_config',
    'list_available_configs',
    'templates',
    
    # Magic Configs
    'ConfigurationTemplates',
    'magic_configs',
    'register_magic_config',
    'get_magic_config',
    'list_magic_configs',
    'has_magic_config',
    'validate_magic_config',
    
    # Builder
    'ConfigurationBuilder',
    'LayerBuilder',
    'DestinationBuilder',
    'create_console_config',
    'create_file_config',
    'create_dual_config',
    'create_production_config',
    'create_development_config',
    'create_testing_config',
    'create_python_logging_style_example',
    
    # Loaders
    'load_config',
    'load_config_from_dict',
    'load_config_from_env',
    'load_config_from_configs_dir',
    'create_log_directories',
    'validate_config',
    'merge_configs',
    'create_config_from_template',
    'list_available_templates',
    
    # Exporters
    'save_config_to_yaml',
    'save_config_to_toml',
    'save_config_to_json',
    'config_to_dict',
    'config_to_yaml_string',
    'config_to_toml_string',
    'config_to_json_string',
    'ConfigurationRegistry',
    'config_registry',
    'save_config',
    'export_config',
    
    # Validators
    'ConfigurationValidator',
    'config_validator',
    'validate_config_file',
    'validate_config_data',
    'validate_handler_config',
    'get_validation_summary',
    'clear_validation_results',
    
    # Setup
    'LogsDirectoryManager',
    'setup_logs_directory',
    'get_logs_manager',
    'ensure_logs_structure',

]
