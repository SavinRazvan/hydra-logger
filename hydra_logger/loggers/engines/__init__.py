"""
Logger Engines Module for Hydra-Logger

This module provides specialized engines for different aspects of logging
including security and plugins. These engines provide advanced
functionality that can be integrated into logger implementations.

ARCHITECTURE:
- SecurityEngine: Security and validation engine for loggers
- PluginEngine: Plugin management engine for loggers
- Specialized engines for different logging aspects
- Integration with logger implementations

CORE ENGINES:
- SecurityEngine: Data validation, sanitization, and threat detection
- PluginEngine: Plugin discovery, loading, and lifecycle management

USAGE EXAMPLES:

Security Engine:
    from hydra_logger.loggers.engines import SecurityEngine
    
    # Create security engine
    security = SecurityEngine()
    
    # Enable security features
    security.set_security_enabled(True)
    security.set_sanitization_enabled(True)
    security.set_redaction_enabled(True)
    
    # Validate message
    result = security.validate_message("User login: john@example.com")
    print(f"Validation result: {result}")
    
    # Sanitize message
    sanitized = security.sanitize_message("Sensitive data: password123")
    print(f"Sanitized: {sanitized}")
    
    # Get security metrics
    metrics = security.get_security_metrics()
    print(f"Security metrics: {metrics}")

Plugin Engine:
    from hydra_logger.loggers.engines import PluginEngine
    
    # Create plugin engine
    plugins = PluginEngine()
    
    # Enable plugin system
    plugins.set_plugins_enabled(True)
    
    # Discover available plugins
    available_plugins = plugins.discover_plugins()
    print(f"Available plugins: {available_plugins}")
    
    # Load specific plugin
    success = plugins.load_plugin("performance_monitor")
    print(f"Plugin loaded: {success}")
    
    # Get plugin metrics
    metrics = plugins.get_plugin_metrics()
    print(f"Plugin metrics: {metrics}")

Engine Integration:
    from hydra_logger.loggers.engines import SecurityEngine, PluginEngine
    
    # Create all engines
    security = SecurityEngine()
    plugins = PluginEngine()
    
    # Configure engines
    security.set_security_enabled(True)
    plugins.set_plugins_enabled(True)
    
    # Use engines in logger
    # (Engines are typically integrated into logger implementations)

SECURITY FEATURES:
- Data validation and sanitization
- PII detection and redaction
- Security threat detection
- Compliance monitoring
- Configurable security levels

PLUGIN FEATURES:
- Plugin discovery and loading
- Plugin lifecycle management
- Plugin compatibility checking
- Plugin performance optimization
- Plugin error handling


ERROR HANDLING:
- Graceful error handling with fallback mechanisms
- Error isolation between engines
- Comprehensive error reporting
- Automatic resource cleanup
- Silent error handling for maximum performance

BENEFITS:
- Specialized functionality for different logging aspects
- Easy integration with logger implementations
- Comprehensive security features
- Extensible plugin architecture
- Production-ready with error handling
"""

from .security_engine import SecurityEngine

__all__ = [
    "SecurityEngine",
]
