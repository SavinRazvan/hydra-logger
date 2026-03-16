"""
Role: Implements hydra_logger.config.models functionality for Hydra Logger.
Used By:
 - Internal `hydra_logger` modules importing this component.
Depends On:
 - hydra_logger
 - os
 - pathlib
 - pydantic
 - typing
Notes:
 - Defines configuration models and validation rules for runtime setup.
"""

import logging
import os
from typing import Any, Dict, List, Literal, Optional

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    ValidationInfo,
    field_validator,
    model_validator,
)

_logger = logging.getLogger(__name__)

class LogDestination(BaseModel):
    """Destination-level handler configuration for a logging layer."""

    type: Literal[
        "file", "console", "null", "async_console", "async_file", "async_cloud"
    ] = Field(default="console", description="Type of destination")

    level: Optional[str] = Field(
        default=None,
        description="Logging level for this destination (inherits from layer or global if not set)",
    )
    path: Optional[str] = Field(
        default=None, description="File path (required for file type)"
    )
    max_size: Optional[str] = Field(
        default="5MB", description="Max file size for rotation"
    )
    backup_count: Optional[int] = Field(default=3, description="Number of backup files")
    format: Optional[str] = Field(
        default=None,  # None = auto-detect from extension, explicit value = must match
        description=(
            "Log format: 'plain-text', 'json', 'json-lines', 'csv', 'syslog', "
            "'gelf', 'compact', 'detailed', 'colored'. If None, "
            "auto-detects from file extension."
        ),
    )
    use_colors: bool = Field(
        default=False,
        description="Whether to use colors for this destination (console only)",
    )

    # Async sink specific fields
    url: Optional[str] = Field(
        default=None,
        description="Reserved for custom/roadmap async sink integrations",
    )
    connection_string: Optional[str] = Field(
        default=None,
        description="Reserved for custom/roadmap async sink integrations",
    )
    queue_url: Optional[str] = Field(
        default=None,
        description="Reserved for custom/roadmap async sink integrations",
    )
    service_type: Optional[str] = Field(
        default=None, description="Cloud service type for async cloud sinks"
    )
    credentials: Optional[Dict[str, str]] = Field(
        default=None, description="Credentials for async sinks"
    )
    retry_count: Optional[int] = Field(
        default=3, description="Number of retries for async operations"
    )
    retry_delay: Optional[float] = Field(
        default=1.0, description="Delay between retries in seconds"
    )
    timeout: Optional[float] = Field(
        default=30.0, description="Timeout for async operations in seconds"
    )
    max_connections: Optional[int] = Field(
        default=10, description="Maximum connections for async sinks"
    )

    # Handler-specific configuration
    max_queue_size: Optional[int] = Field(
        default=10000,
        description="Maximum queue size for async handlers before dropping messages",
    )

    # Extra parameters for handler-specific configuration
    extra: Optional[Dict[str, Any]] = Field(
        default=None, description="Extra parameters for handler configuration"
    )

    @field_validator("path")
    @classmethod
    def validate_file_path(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Ensure that file destinations have a path specified."""
        if (
            info.data
            and info.data.get("type") == "file"
            and (not v or (v and not v.strip()))
        ):
            raise ValueError("Path is required for file destinations")
        return v

    @field_validator("service_type")
    @classmethod
    def validate_async_cloud_service(
        cls, v: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        """Ensure that async cloud destinations have a service type specified."""
        if (
            info.data
            and info.data.get("type") == "async_cloud"
            and (not v or (v and not v.strip()))
        ):
            raise ValueError("Service type is required for async cloud destinations")
        return v

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: Optional[str]) -> Optional[str]:
        """Validate log level."""
        if v is None:
            return None  # Allow None for inheritance

        valid_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate log format. None is allowed for auto-detection from extension."""
        if v is None or v == "":
            return None  # Allow None for auto-detection

        valid_formats = [
            # TEXT-BASED FORMATTERS
            "plain-text",
            "fast-plain",
            "detailed",
            # JSON-BASED FORMATTERS
            "json-lines",
            "json",
            # COLORED FORMATTERS
            "colored",
            # STRUCTURED FORMATTERS
            "csv",
            "syslog",
            "gelf",
            "logstash",
            # BINARY FORMATTERS
            "binary",
            "binary-compact",
            "binary-extended",
        ]
        if v not in valid_formats:
            raise ValueError(f"Invalid log format: {v}. Must be one of {valid_formats}")
        return v

    @model_validator(mode="after")
    def validate_destination_configuration(self) -> "LogDestination":
        """
        Post-initialization validation for destinations.

        This method provides additional validation after model initialization
        to ensure that destinations have the required configuration.
        """
        if self.type == "file" and (
            not self.path or (self.path and not self.path.strip())
        ):
            raise ValueError("Path is required for file destinations")

        # Format-extension validation: enforce strict matching for non-.log files
        if self.type == "file" and self.path:
            # Extract file extension
            file_ext = os.path.splitext(self.path.lower())[1]

            # Map extensions to required formats (strict matching)
            extension_format_map = {
                ".jsonl": "json-lines",
                ".json": "json-lines",  # JSON files also use json-lines format
                ".csv": "csv",
                ".bin": "binary-compact",  # Binary files
            }

            # Strict matching for non-.log files
            if file_ext in extension_format_map:
                required_format = extension_format_map[file_ext]

                # Check if format was explicitly set by the user
                format_explicitly_set = self.format is not None
                current_format = self.format if format_explicitly_set else None

                # Validation first: reject explicit format mismatches before
                # auto-setting
                if format_explicitly_set and current_format != required_format:
                    # User explicitly set a format that doesn't match - reject
                    # immediately
                    raise ValueError(
                        f"Format mismatch: File extension '{file_ext}' requires format '{required_format}', "
                        f"but got '{current_format}'. For '{file_ext}' files, format must be '{required_format}'. "
                        f"(Only .log files are flexible and can use any format)"
                    )

                # Auto-set: only if format was NOT explicitly set (None), auto-set to match extension
                # This respects explicit user choices, even if they set "plain-text"
                if not format_explicitly_set:
                    self.format = required_format

            # .log files can use any format - no strict validation needed
            # If format is None for .log files, default to plain-text
            elif file_ext == ".log" and (self.format is None or self.format == ""):
                self.format = "plain-text"

        elif self.type == "async_cloud" and (
            not self.service_type
            or (self.service_type and not self.service_type.strip())
        ):
            raise ValueError("Service type is required for async cloud destinations")

        return self

class LogLayer(BaseModel):
    """Layer-level logger configuration with destinations and level settings."""

    level: str = Field(
        default="INFO",
        description="Log level for this layer (inherits from global if not set)",
    )
    destinations: List[LogDestination] = Field(
        default_factory=list, description="List of destinations for this layer"
    )
    color: Optional[str] = Field(
        default=None,
        description="Custom color for this layer (ANSI color code or color name)",
    )
    enabled: bool = Field(default=True, description="Whether this layer is enabled")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate color value."""
        if v is None:
            return v

        # Allow ANSI color codes
        if v.startswith("\033["):
            return v

        # Allow color names (will be converted to ANSI codes)
        valid_colors = [
            "black",
            "red",
            "green",
            "yellow",
            "blue",
            "magenta",
            "cyan",
            "white",
            "bright_black",
            "bright_red",
            "bright_green",
            "bright_yellow",
            "bright_blue",
            "bright_magenta",
            "bright_cyan",
            "bright_white",
        ]
        if v.lower() in valid_colors:
            return v.lower()

        raise ValueError(
            f"Invalid color: {v}. Must be ANSI code or one of {valid_colors}"
        )

    @model_validator(mode="after")
    def validate_layer_configuration(self) -> "LogLayer":
        """Validate layer configuration."""
        if not self.destinations:
            raise ValueError("Layer must have at least one destination")
        return self

class LoggingConfig(BaseModel):
    """Root logging configuration model used by logger factories and runtimes."""

    default_level: str = Field(
        default="INFO", description="Default log level for all layers"
    )
    layers: Dict[str, LogLayer] = Field(
        default_factory=dict, description="Named layers with their configurations"
    )
    layer_colors: Optional[Dict[str, str]] = Field(
        default=None, description="Color mapping for different layers in console output"
    )

    # Global settings - performance-oriented defaults
    enable_security: bool = Field(
        default=False,
        description="Enable security features (disabled by default)",
    )
    enable_sanitization: bool = Field(
        default=False,
        description="Enable data sanitization (disabled by default)",
    )
    enable_data_protection: bool = Field(
        default=False,
        description="Enable data protection extension (disabled by default)",
    )
    enable_plugins: bool = Field(
        default=False,
        description="Enable plugin system (disabled by default)",
    )
    enable_performance_monitoring: bool = Field(
        default=False,
        description="Enable performance monitoring (disabled by default)",
    )

    # Extension configuration - USER-CONTROLLABLE
    extensions: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Extension configurations. Users can enable/disable and configure individual extensions.",
    )

    # Security configuration
    security_level: Literal["low", "medium", "high", "strict"] = Field(
        default="medium",
        description="Security level: low (basic), medium (standard), high (aggressive), strict (paranoid)",
    )

    # Monitoring configuration
    monitoring_detail_level: Literal["basic", "standard", "detailed"] = Field(
        default="basic",
        description="Monitoring detail: basic (essential), standard (full), detailed (profiling)",
    )
    monitoring_sample_rate: int = Field(
        default=100, description="Sample rate for monitoring metrics (every N logs)"
    )
    monitoring_background: bool = Field(
        default=True,
        description="Use background processing for monitoring (non-blocking)",
    )

    # Log directory configuration
    base_log_dir: Optional[str] = Field(
        default=None,
        description="Base directory for all log files (defaults to ./logs if not set)",
    )
    log_dir_name: Optional[str] = Field(
        default=None,
        description="Subdirectory name for logs within base directory (optional, defaults to no subfolder)",
    )

    # Performance settings
    buffer_size: int = Field(default=8192, description="Buffer size for file handlers")
    flush_interval: float = Field(default=1.0, description="Flush interval in seconds")
    _verbose: bool = PrivateAttr(default=False)

    @field_validator("default_level")
    @classmethod
    def validate_default_level(cls, v: str) -> str:
        """Validate default log level."""
        valid_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid default level: {v}. Must be one of {valid_levels}"
            )
        return v.upper()

    @field_validator("buffer_size")
    @classmethod
    def validate_buffer_size(cls, v: int) -> int:
        """Validate buffer size."""
        if v <= 0:
            raise ValueError("Buffer size must be positive")
        if v > 1024 * 1024:  # 1MB max
            raise ValueError("Buffer size cannot exceed 1MB")
        return v

    @field_validator("flush_interval")
    @classmethod
    def validate_flush_interval(cls, v: float) -> float:
        """Validate flush interval."""
        if v < 0:
            raise ValueError("Flush interval cannot be negative")
        if v > 3600:  # 1 hour max
            raise ValueError("Flush interval cannot exceed 1 hour")
        return v

    @field_validator("monitoring_sample_rate")
    @classmethod
    def validate_monitoring_sample_rate(cls, v: int) -> int:
        """Validate monitoring sample rate."""
        if v < 1:
            raise ValueError("Monitoring sample rate must be at least 1")
        if v > 10000:
            raise ValueError("Monitoring sample rate cannot exceed 10,000")
        return v

    def get_layer_threshold(self, layer_name: str) -> int:
        """
        Get the numeric log level threshold for a layer.

        This follows Python logging standard:
        - Each layer has one level (like a logger)
        - Handlers within the layer can filter by their own level
        - Simple inheritance: layer level or global default
        """
        from ..types.levels import LogLevelManager

        if layer_name not in self.layers:
            return LogLevelManager.get_level(self.default_level)

        layer = self.layers[layer_name]

        # Use layer level if set, otherwise global default (like Python logging)
        if layer.level:
            return LogLevelManager.get_level(layer.level)

        return LogLevelManager.get_level(self.default_level)

    def get_destination_level(self, layer_name: str, destination_index: int = 0) -> int:
        """
        Get the level for a specific destination (handler).

        This follows Python logging standard:
        - Handler level overrides logger level for filtering
        - If no handler level set, use layer level
        """
        from ..types.levels import LogLevelManager

        if layer_name not in self.layers:
            return LogLevelManager.get_level(self.default_level)

        layer = self.layers[layer_name]
        if not layer.destinations or destination_index >= len(layer.destinations):
            return LogLevelManager.get_level(
                layer.level if layer.level else self.default_level
            )

        destination = layer.destinations[destination_index]

        # Handler level (like Python logging handler level)
        if destination.level:
            return LogLevelManager.get_level(destination.level)

        # Fall back to layer level (like Python logging logger level)
        if layer.level:
            return LogLevelManager.get_level(layer.level)

        # Final fallback to global default
        return LogLevelManager.get_level(self.default_level)

    def update_security_level(
        self, level: Literal["low", "medium", "high", "strict"]
    ) -> None:
        """Update security level at runtime."""
        if level not in ["low", "medium", "high", "strict"]:
            raise ValueError(f"Invalid security level: {level}")
        self.security_level = level

    def update_monitoring_config(
        self,
        detail_level: Optional[Literal["basic", "standard", "detailed"]] = None,
        sample_rate: Optional[int] = None,
        background: Optional[bool] = None,
    ) -> None:
        """Update monitoring configuration at runtime."""
        if detail_level is not None:
            if detail_level not in ["basic", "standard", "detailed"]:
                raise ValueError(f"Invalid monitoring detail level: {detail_level}")
            self.monitoring_detail_level = detail_level

        if sample_rate is not None:
            if sample_rate < 1 or sample_rate > 10000:
                raise ValueError(f"Invalid sample rate: {sample_rate}")
            self.monitoring_sample_rate = sample_rate

        if background is not None:
            self.monitoring_background = background

    def toggle_feature(self, feature: str, enabled: bool) -> None:
        """Toggle a feature on/off at runtime."""
        if feature == "security":
            self.enable_security = enabled
        elif feature == "sanitization":
            self.enable_sanitization = enabled
        elif feature == "plugins":
            self.enable_plugins = enabled
        elif feature == "monitoring":
            self.enable_performance_monitoring = enabled
        else:
            raise ValueError(f"Unknown feature: {feature}")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            "security": {
                "enabled": self.enable_security,
                "level": self.security_level,
                "sanitization": self.enable_sanitization,
            },
            "plugins": {"enabled": self.enable_plugins},
            "monitoring": {
                "enabled": self.enable_performance_monitoring,
                "detail_level": self.monitoring_detail_level,
                "sample_rate": self.monitoring_sample_rate,
                "background": self.monitoring_background,
            },
            "performance": {
                "buffer_size": self.buffer_size,
                "flush_interval": self.flush_interval,
            },
            "paths": {
                "base_log_dir": self.base_log_dir or "./logs (default)",
                "log_dir_name": self.log_dir_name or "None (no subfolder)",
                "default_log_path": self.get_default_log_path(),
            },
        }

    def get_default_log_path(self) -> str:
        """Get the default log directory path."""
        from pathlib import Path

        if self.base_log_dir:
            base_path = Path(self.base_log_dir)
            # Only add subfolder if explicitly specified
            if self.log_dir_name:
                base_path = base_path / self.log_dir_name
        else:
            # Simple default: just logs/ folder, no subfolder
            base_path = Path.cwd() / "logs"
            # No subfolder by default

        return str(base_path.absolute())

    def ensure_log_directory(self, directory_path: Optional[str] = None) -> str:
        """Ensure log directory exists and return the path."""
        from pathlib import Path

        if directory_path:
            target_path = Path(directory_path)
        else:
            target_path = Path(self.get_default_log_path())

        # Create directory if it doesn't exist
        target_path.mkdir(parents=True, exist_ok=True)

        return str(target_path.absolute())

    def resolve_log_path(
        self, destination_path: str, format_type: Optional[str] = None
    ) -> str:
        """
        Resolve log file path using base directory and log directory name.

        Args:
            destination_path: Original path from destination configuration
            format_type: Format type to determine file extension

        Returns:
            Resolved absolute path with directories created
        """
        from pathlib import Path

        # If path is already absolute, use it as is
        if os.path.isabs(destination_path):
            final_path = Path(destination_path)
        else:
            # If path starts with ~, expand user home
            if destination_path.startswith("~"):
                destination_path = os.path.expanduser(destination_path)
                if os.path.isabs(destination_path):
                    final_path = Path(destination_path)
                else:
                    # Build path using base_log_dir and log_dir_name
                    if self.base_log_dir:
                        base_path = Path(self.base_log_dir)
                        # Only add subfolder if explicitly specified
                        if self.log_dir_name:
                            base_path = base_path / self.log_dir_name
                    else:
                        # Default: create simple logs folder in current directory
                        base_path = Path.cwd() / "logs"
                        # No subfolder by default - just logs/

                    # Ensure base path is absolute
                    if not base_path.is_absolute():
                        base_path = Path.cwd() / base_path

                    # Combine with destination path
                    final_path = base_path / destination_path
            else:
                # Check if path already starts with 'logs/' - if so, treat as relative
                # to current directory
                if destination_path.startswith("logs/"):
                    # Path already includes logs/ directory, use as relative to current
                    # directory
                    final_path = Path.cwd() / destination_path
                else:
                    # Build path using base_log_dir and log_dir_name
                    if self.base_log_dir:
                        base_path = Path(self.base_log_dir)
                        # Only add subfolder if explicitly specified
                        if self.log_dir_name:
                            base_path = base_path / self.log_dir_name
                    else:
                        # Default: create simple logs folder in current directory
                        base_path = Path.cwd() / "logs"
                        # No subfolder by default - just logs/

                    # Ensure base path is absolute
                    if not base_path.is_absolute():
                        base_path = Path.cwd() / base_path

                    # Combine with destination path
                    final_path = base_path / destination_path

        # Automatically create directories
        try:
            # Create parent directory if it doesn't exist
            final_path.parent.mkdir(parents=True, exist_ok=True)

            # Log directory creation for debugging (only if verbose mode enabled)
            if hasattr(self, "_verbose") and self._verbose:
                _logger.info("Created log directory: %s", final_path.parent)

        except Exception as exc:
            _logger.exception("Primary log directory creation failed; using fallback: %s", exc)
            # Fallback: try to create in current directory
            fallback_path = Path.cwd() / "logs" / destination_path
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            final_path = fallback_path

            if hasattr(self, "_verbose") and self._verbose:
                _logger.warning("Fallback log path created: %s", fallback_path)

        # Override file extension based on format for proper file type identification
        if format_type:
            extension_map = {
                # TEXT-BASED FORMATTERS
                "plain-text": ".log",
                "fast-plain": ".log",
                "detailed": ".log",
                # JSON-BASED FORMATTERS
                "json-lines": ".jsonl",
                # COLORED FORMATTERS
                "colored": ".log",
                # STRUCTURED FORMATTERS
                "csv": ".csv",
                "syslog": ".log",
                "gelf": ".log",
                "logstash": ".log",
                # BINARY FORMATTERS
                "binary-compact": ".bin",
                "binary-extended": ".bin",
            }
            if format_type in extension_map:
                final_path = final_path.with_suffix(extension_map[format_type])

        return str(final_path)

    def add_layer(self, name: str, layer: LogLayer) -> None:
        """Add a new layer to the configuration."""
        self.layers[name] = layer

    def remove_layer(self, name: str) -> None:
        """Remove a layer from the configuration."""
        if name in self.layers:
            del self.layers[name]

    def get_layer_destinations(self, layer_name: str) -> List[LogDestination]:
        """Get destinations for a specific layer."""
        if layer_name in self.layers:
            return self.layers[layer_name].destinations
        return []

    def validate_configuration(self) -> bool:
        """Validate the complete configuration."""
        try:
            # Validate all layers
            for layer_name, layer in self.layers.items():
                if not layer.destinations:
                    raise ValueError(f"Layer '{layer_name}' has no destinations")

                # Validate destinations
                for dest in layer.destinations:
                    if dest.type == "file" and not dest.path:
                        raise ValueError(
                            f"File destination in layer '{layer_name}' missing path"
                        )

            return True
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")

    @model_validator(mode="after")
    def validate_configuration_structure(self) -> "LoggingConfig":
        """
        Post-initialization validation for the complete configuration.

        Ensures that the configuration has at least one layer and validates
        the overall structure.
        """
        if not self.layers:
            # Create a default layer if none specified
            self.layers = {
                "default": LogLayer(
                    level=self.default_level,
                    destinations=[LogDestination(type="console")],
                )
            }

        return self

class HandlerConfig(BaseModel):
    """Base configuration for handlers."""

    type: str = Field(description="Handler type")
    level: str = Field(default="INFO", description="Log level")
    format_type: str = Field(default="plain-text", description="Format type")
    color_mode: Literal["auto", "always", "never"] = Field(
        default="auto", description="Color mode"
    )
    show_context: bool = Field(default=True, description="Show context information")
    file_path: Optional[str] = Field(
        default=None, description="File path for file handlers"
    )

class FileHandlerConfig(HandlerConfig):
    """Configuration for file handlers."""

    type: Literal["file"] = "file"
    file_path: str = Field(default="", description="File path")
    buffering: bool = Field(default=True, description="Enable buffering")
    max_size: str = Field(default="5MB", description="Maximum file size")
    backup_count: int = Field(default=3, description="Number of backup files")

class ConsoleHandlerConfig(HandlerConfig):
    """Configuration for console handlers."""

    type: Literal["console"] = "console"
    stream: Literal["stdout", "stderr"] = Field(
        default="stdout", description="Output stream"
    )

class MemoryHandlerConfig(HandlerConfig):
    """Configuration for memory handlers."""

    type: Literal["memory"] = "memory"
    capacity: int = Field(default=1000, description="Memory capacity")

class ModularConfig(BaseModel):
    """Modular configuration format for backward compatibility."""

    handlers: List[HandlerConfig] = Field(
        default_factory=list, description="List of handlers"
    )
    level: str = Field(default="INFO", description="Default log level")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModularConfig":
        """Create from dictionary."""
        return cls(**data)

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format."""
        return {
            "handlers": [handler.model_dump() for handler in self.handlers],
            "level": self.level,
        }
