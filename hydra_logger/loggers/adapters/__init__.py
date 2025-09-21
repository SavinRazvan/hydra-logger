"""
Logger Adapters Module for Hydra-Logger

This module provides dedicated adapter modules that can be enabled/disabled/customized
for specific logging scenarios and integrations. Adapters provide specialized functionality
for different use cases while maintaining the core Hydra-Logger interface.

ARCHITECTURE:
- Adapter modules for specific logging scenarios
- Modular design for easy enable/disable functionality
- Consistent interface with core Hydra-Logger components
- Specialized functionality for different use cases

CORE FEATURES:
- Modular adapter system for specialized functionality
- Easy enable/disable/customize capabilities
- Consistent interface with core logging components
- Specialized functionality for different scenarios
- Extensible architecture for custom adapters

ADAPTER TYPES:
- Legacy adapters for migration from other logging systems
- Integration adapters for third-party services
- Specialized adapters for specific use cases
- Custom adapters for unique requirements

USAGE EXAMPLES:

Adapter Discovery:
    from hydra_logger.loggers.adapters import discover_adapters
    
    # Discover available adapters
    adapters = discover_adapters()
    print(f"Available adapters: {adapters}")

Adapter Management:
    from hydra_logger.loggers.adapters import AdapterManager
    
    # Create adapter manager
    manager = AdapterManager()
    
    # Enable specific adapters
    manager.enable_adapter("legacy_migration")
    manager.enable_adapter("cloud_integration")
    
    # Disable adapters
    manager.disable_adapter("debug_adapter")
    
    # Get adapter status
    status = manager.get_adapter_status()
    print(f"Adapter status: {status}")

Custom Adapter Creation:
    from hydra_logger.loggers.adapters import BaseAdapter
    
    class CustomAdapter(BaseAdapter):
        def __init__(self, config=None):
            super().__init__(config)
            self._enabled = False
        
        def enable(self):
            self._enabled = True
        
        def disable(self):
            self._enabled = False
        
        def is_enabled(self):
            return self._enabled
        
        def process_log(self, record):
            if self._enabled:
                # Custom processing logic
                pass

Adapter Configuration:
    from hydra_logger.loggers.adapters import AdapterConfig
    
    # Create adapter configuration
    config = AdapterConfig(
        adapters={
            "legacy_migration": {"enabled": True, "config": {}},
            "cloud_integration": {"enabled": False, "config": {}},
            "debug_adapter": {"enabled": True, "config": {"level": "DEBUG"}}
        }
    )
    
    # Apply configuration
    config.apply()

MODULAR DESIGN:
- Each adapter is a separate module
- Easy to enable/disable individual adapters
- Consistent interface across all adapters
- Minimal dependencies between adapters

EXTENSIBILITY:
- Easy to add new adapters
- Clear interface for custom adapters
- Configuration system for adapter settings
- Plugin-like architecture for adapters

CONFIGURATION:
- Adapter-specific configuration options
- Global adapter management settings
- Runtime enable/disable capabilities
- Configuration validation and error handling

ERROR HANDLING:
- Graceful handling of adapter failures
- Fallback mechanisms for critical adapters
- Error isolation between adapters
- Comprehensive error reporting

BENEFITS:
- Modular architecture for specialized functionality
- Easy configuration and management
- Consistent interface with core components
- Extensible design for custom requirements
- Production-ready with error handling
"""
