"""
Role: Implements hydra_logger.config.defaults functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - hydra_logger
 - pathlib
 - typing
Notes:
 - Builds default/development/production configuration profiles.
"""

from pathlib import Path
from typing import Callable, Dict, Optional

from .models import LogDestination, LoggingConfig, LogLayer

class ConfigurationTemplates:
    """Predefined configuration builders for common runtime profiles."""

    @staticmethod
    def get_default_config() -> LoggingConfig:
        """Return the performance-focused default configuration."""
        return LoggingConfig(
            # All features disabled by default
            default_level="INFO",
            enable_security=False,
            enable_sanitization=False,
            enable_plugins=False,
            enable_performance_monitoring=False,

            buffer_size=16384,  # 16K buffer (larger = better performance)
            flush_interval=0.5,  # 0.5s flush (balance between latency and throughput)
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_console",  # Use async for better performance
                            format="plain-text",  # Faster than colored
                            use_colors=False,  # Disable colors for performance
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
        enable_security: bool = False,
        enable_sanitization: bool = False,
        enable_plugins: bool = False,
        enable_performance_monitoring: bool = False,
        default_level: str = "INFO",
        console_enabled: bool = True,
        file_enabled: bool = True,
        file_path: str = "logs/app.log",
        file_format: str = "json-lines",
        buffer_size: int = 8192,
        flush_interval: float = 1.0,
        error_layer: bool = False,
        debug_layer: bool = False,
        warning_layer: bool = False,
        info_layer: bool = False,
        critical_layer: bool = False,
        custom_layers: Optional[Dict[str, LogLayer]] = None,
        **extra_options,
    ) -> LoggingConfig:
        """Build a custom configuration with optional feature toggles and layers."""
        # Build destinations based on user preferences
        destinations = []

        if console_enabled:
            # Use async_console for better performance (non-blocking I/O)
            destinations.append(
                LogDestination(
                    type="async_console", format="plain-text", use_colors=False
                )
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
            # Fallback to async_console if no destinations specified (better
            # performance)
            destinations.append(
                LogDestination(
                    type="async_console", format="plain-text", use_colors=False
                )
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
                    LogDestination(
                        type="async_console", format="plain-text", use_colors=False
                    ),
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
        """Return a development-oriented configuration."""
        config = ConfigurationTemplates.get_custom_config(
            default_level="DEBUG",
            flush_interval=0.1,  # Fast feedback
            debug_layer=True,  # Dedicated debug output
            file_format="fast-plain",  # Faster formatting
        )
        # Config already uses async_console from get_custom_config, no override needed
        return config

    @staticmethod
    def get_production_config() -> LoggingConfig:
        """Return a production-oriented configuration."""
        config = ConfigurationTemplates.get_custom_config(
            enable_security=True,
            enable_sanitization=True,
            enable_performance_monitoring=True,
            buffer_size=32768,  # Larger buffer
            flush_interval=2.0,  # Slower flush for throughput
            error_layer=True,  # Dedicated error logging
            file_format="json-lines",  # Structured logging
        )
        # Override console to use async_console for better performance
        if "default" in config.layers:
            for dest in config.layers["default"].destinations:
                if dest.type == "console":
                    dest.type = "async_console"
                    dest.use_colors = False  # Disable colors in production
        return config

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
DEFAULT_CONFIGS: Dict[str, Callable[..., LoggingConfig]] = {
    "default": get_default_config,
    "development": get_development_config,
    "production": get_production_config,
    "custom": get_custom_config,
}

def get_named_config(name: str, **options) -> LoggingConfig:
    """Resolve a named configuration builder and return its result."""
    if name not in DEFAULT_CONFIGS:
        available = list(DEFAULT_CONFIGS.keys())
        raise ValueError(f"Unknown configuration name: {name}. Available: {available}")

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
