"""
Hydra-Logger Default Configurations

This module provides default configurations with a performance-oriented approach.
It offers pre-built configurations for common use cases while maintaining the flexibility
to customize as needed.

PHILOSOPHY:
- Performance-oriented: All features disabled by default for speed
- Clear trade-offs: Users can enable features as needed, trading performance for functionality
- Python logging compatibility: Follows standard logging patterns and conventions
- Minimal configuration: Simple, clean defaults that work out of the box

FEATURES:
- Default configuration with performance focus
- Custom configuration builder for specific use cases
- Pre-built templates for development, production, and testing
- Color system integration for console destinations
- Security and monitoring features available when needed
- Type-safe configuration with automatic validation

PERFORMANCE OPTIMIZATIONS:
- Security features disabled by default (enable_security=False)
- Sanitization disabled by default (enable_sanitization=False)
- Plugin system disabled by default (enable_plugins=False)
- Performance monitoring disabled by default (enable_performance_monitoring=False)
- Optimized buffering and flush intervals
- Minimal memory footprint with efficient data structures

USAGE EXAMPLES:

Default Configuration:
    from hydra_logger.config import get_default_config

    config = get_default_config()

Custom Configuration (Balanced Performance):
    from hydra_logger.config import get_custom_config

    config = get_custom_config(
        enable_security=True,  # Enable security features
        enable_sanitization=True,  # Enable data sanitization
        console_enabled=True,
        file_enabled=True,
        file_path="app.log"
    )

Production Configuration:
    from hydra_logger.config import get_production_config

    config = get_production_config()  # Pre-built production config

Development Configuration:
    from hydra_logger.config import get_development_config

    config = get_development_config()  # Pre-built development config
"""

from typing import Dict, Optional
from pathlib import Path
from .models import LoggingConfig, LogLayer, LogDestination


class ConfigurationTemplates:
    """
    Configuration template system.

    This class provides pre-built configuration templates for common use cases.
    It follows a performance-oriented philosophy while offering flexibility for
    users who need specific features.

    Philosophy:
    - Default: Performance focus, minimal features
    - Custom: Let users enable features as needed, trading performance for functionality
    - Clear trade-offs: Users understand the performance impact of each feature
    - Python logging compatibility: Follows standard logging patterns

    Available Templates:
    - get_default_config(): Default configuration with performance focus
    - get_custom_config(): Customizable configuration with feature toggles
    - get_development_config(): Development-friendly configuration
    - get_production_config(): Production-ready configuration with security
    - get_testing_config(): Testing configuration with minimal overhead

    Examples:
        # Default configuration
        config = ConfigurationTemplates.get_default_config()

        # Custom configuration with security
        config = ConfigurationTemplates.get_custom_config(
            enable_security=True,
            enable_sanitization=True,
            console_enabled=True,
            file_enabled=True
        )

        # Production configuration
        config = ConfigurationTemplates.get_production_config()
    """

    @staticmethod
    def get_default_config() -> LoggingConfig:
        """
        Get the default configuration with performance focus.

        Features:
        - INFO level
        - Performance-heavy features disabled by default
        - Console + file output
        - Fast formatting
        - Optimized buffering
        """
        return LoggingConfig(
            # All features disabled by default
            default_level="INFO",
            enable_security=False,
            enable_sanitization=False,
            enable_plugins=False,
            enable_performance_monitoring=False,
            # Fast buffering and flushing
            buffer_size=8192,
            flush_interval=1.0,
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="console", format="colored", use_colors=True
                        ),
                        LogDestination(
                            type="file",
                            path="app.log",
                            format="json-lines",  # Fast JSON format
                            max_size="10MB",
                            backup_count=5,
                        ),
                    ],
                )
            },
        )

    @staticmethod
    def get_custom_config(
        # Performance vs Features trade-offs
        enable_security: bool = False,
        enable_sanitization: bool = False,
        enable_plugins: bool = False,
        enable_performance_monitoring: bool = False,
        # Log level (affects performance)
        default_level: str = "INFO",
        # Output destinations
        console_enabled: bool = True,
        file_enabled: bool = True,
        file_path: str = "logs/app.log",
        file_format: str = "json-lines",
        # Performance settings
        buffer_size: int = 8192,
        flush_interval: float = 1.0,
        # Additional layers (unlimited)
        error_layer: bool = False,
        debug_layer: bool = False,
        warning_layer: bool = False,
        info_layer: bool = False,
        critical_layer: bool = False,
        custom_layers: Optional[Dict[str, LogLayer]] = None,
        **extra_options,
    ) -> LoggingConfig:
        """
        Create a custom configuration with user-specified features.

        This allows users to trade performance for functionality by enabling
        specific features as needed. Supports UNLIMITED layers and configurations.

        Args:
            enable_security: Enable security features (reduces performance)
            enable_sanitization: Enable data sanitization (reduces performance)
            enable_plugins: Enable plugin system (reduces performance)
            enable_performance_monitoring: Enable performance monitoring (reduces performance)
            default_level: Log level (DEBUG reduces performance)
            console_enabled: Enable console output
            file_enabled: Enable file output
            file_path: Path for file output
            file_format: Format for file output
            buffer_size: Buffer size (larger = better performance)
            flush_interval: Flush interval (larger = better performance)
            error_layer: Add dedicated error layer
            debug_layer: Add dedicated debug layer
            warning_layer: Add dedicated warning layer
            info_layer: Add dedicated info layer
            critical_layer: Add dedicated critical layer
            custom_layers: Dictionary of custom layers (UNLIMITED)
            **extra_options: Additional configuration options

        Returns:
            LoggingConfig with specified features enabled and unlimited layers
        """
        # Build destinations based on user preferences
        destinations = []

        if console_enabled:
            destinations.append(
                LogDestination(type="console", format="colored", use_colors=True)
            )

        if file_enabled:
            # Extract just the filename from the path to avoid nested directories
            filename = Path(file_path).name if file_path else "app.log"
            destinations.append(
                LogDestination(
                    type="file",
                    path=filename,
                    format=file_format,
                    max_size="10MB",
                    backup_count=5,
                )
            )

        if not destinations:
            # Fallback to console if no destinations specified
            destinations.append(
                LogDestination(type="console", format="colored", use_colors=True)
            )

        # Build layers
        layers = {"default": LogLayer(level=default_level, destinations=destinations)}

        # Add error layer if requested
        if error_layer:
            layers["error"] = LogLayer(
                level="ERROR",
                destinations=[
                    LogDestination(
                        type="file",
                        path="error.log",
                        format="json-lines",
                        max_size="5MB",
                        backup_count=3,
                    )
                ],
            )

        # Add debug layer if requested
        if debug_layer:
            layers["debug"] = LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="debug.log",
                        format="fast-plain",
                        max_size="5MB",
                        backup_count=2,
                    )
                ],
            )

        # Add warning layer if requested
        if warning_layer:
            layers["warning"] = LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="file",
                        path="warning.log",
                        format="json-lines",
                        max_size="5MB",
                        backup_count=3,
                    )
                ],
            )

        # Add info layer if requested
        if info_layer:
            layers["info"] = LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="info.log",
                        format="json-lines",
                        max_size="10MB",
                        backup_count=5,
                    )
                ],
            )

        # Add critical layer if requested
        if critical_layer:
            layers["critical"] = LogLayer(
                level="CRITICAL",
                destinations=[
                    LogDestination(
                        type="file",
                        path="critical.log",
                        format="json-lines",
                        max_size="2MB",
                        backup_count=10,
                    ),
                    LogDestination(type="console", format="colored", use_colors=True),
                ],
            )

        # Add custom layers (UNLIMITED)
        if custom_layers:
            layers.update(custom_layers)

        return LoggingConfig(
            default_level=default_level,
            enable_security=enable_security,
            enable_sanitization=enable_sanitization,
            enable_plugins=enable_plugins,
            enable_performance_monitoring=enable_performance_monitoring,
            buffer_size=buffer_size,
            flush_interval=flush_interval,
            layers=layers,
            **extra_options,
        )

    @staticmethod
    def get_development_config() -> LoggingConfig:
        """
        Get a development-friendly configuration.

        Trade-offs:
        - DEBUG level for detailed logging
        - Fast flush for immediate feedback
        - Performance monitoring disabled for speed
        """
        return ConfigurationTemplates.get_custom_config(
            default_level="DEBUG",
            flush_interval=0.1,  # Fast feedback
            debug_layer=True,  # Dedicated debug output
            file_format="fast-plain",  # Faster formatting
        )

    @staticmethod
    def get_production_config() -> LoggingConfig:
        """
        Get a production-ready configuration.

        Trade-offs:
        - Security and monitoring enabled
        - Larger buffers for performance
        - Dedicated error layer
        """
        return ConfigurationTemplates.get_custom_config(
            enable_security=True,
            enable_sanitization=True,
            enable_performance_monitoring=True,
            buffer_size=32768,  # Larger buffer
            flush_interval=2.0,  # Slower flush for throughput
            error_layer=True,  # Dedicated error logging
            file_format="json-lines",  # Structured logging
        )


# Global instance for easy access
templates = ConfigurationTemplates()


# Convenience functions
def get_default_config() -> LoggingConfig:
    """Get the default configuration with performance focus."""
    return templates.get_default_config()


def get_custom_config(**options) -> LoggingConfig:
    """Create a custom configuration with user-specified features."""
    return templates.get_custom_config(**options)


def get_development_config() -> LoggingConfig:
    """Get a development-friendly configuration."""
    return templates.get_development_config()


def get_production_config() -> LoggingConfig:
    """Get a production-ready configuration."""
    return templates.get_production_config()


# Configuration registry for backward compatibility
DEFAULT_CONFIGS: Dict[str, callable] = {
    "default": get_default_config,
    "development": get_development_config,
    "production": get_production_config,
    "custom": get_custom_config,
}


def get_named_config(name: str, **options) -> LoggingConfig:
    """
    Get a named configuration.

    Args:
        name: Configuration name ("default", "development", "production", "custom")
        **options: Additional options for custom configuration

    Returns:
        LoggingConfig instance
    """
    if name not in DEFAULT_CONFIGS:
        raise ValueError(
            f"Unknown configuration name: {name}. Available: {list(DEFAULT_CONFIGS.keys())}"
        )

    if name == "custom":
        return DEFAULT_CONFIGS[name](**options)
    else:
        return DEFAULT_CONFIGS[name]()


def list_available_configs() -> Dict[str, str]:
    """List all available configurations."""
    return {
        "default": "Default configuration with performance focus",
        "development": "Development-friendly configuration with debug output",
        "production": "Production-ready configuration with security and monitoring",
        "custom": "Custom configuration with user-specified features",
    }
