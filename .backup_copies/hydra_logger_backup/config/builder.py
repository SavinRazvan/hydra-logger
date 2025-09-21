"""
Hydra-Logger Configuration Builder

This module provides a fluent, builder-pattern interface for creating
logging configurations programmatically. It follows Python logging standards
exactly, making it familiar to users while providing powerful configuration
capabilities.

FEATURES:
- Fluent builder pattern for intuitive configuration creation
- Python logging compatibility (logger.setLevel(), handler.setLevel())
- Support for all destination types (console, file, async_file, cloud)
- Pre-built configuration templates for common use cases
- Type-safe configuration with automatic validation
- Performance-first defaults with optional security features

ARCHITECTURE:
The builder system uses a three-tier approach:

1. ConfigurationBuilder - Root configuration builder
   - Manages global settings and security features
   - Creates and manages layer builders
   - Builds the final LoggingConfig

2. LayerBuilder - Logger configuration builder
   - Equivalent to Python's Logger class
   - Manages destinations (handlers) for the layer
   - Supports layer-specific settings and colors

3. DestinationBuilder - Handler configuration builder
   - Equivalent to Python's Handler class
   - Supports all destination types and formats
   - Manages destination-specific settings

USAGE EXAMPLES:

Basic Configuration:
    from hydra_logger.config import ConfigurationBuilder
    
    config = (ConfigurationBuilder()
              .setLevel("INFO")
              .add_layer_builder("app")
              .setLevel("DEBUG")
              .add_console(format="colored", use_colors=True)
              .add_file("app.log", format="json-lines")
              .build())

Production Configuration:
    config = (ConfigurationBuilder()
              .setLevel("WARNING")
              .enable_security(True)
              .enable_sanitization(True)
              .add_layer_builder("app")
              .setLevel("INFO")
              .add_file("app.log", format="json-lines")
              .add_async_cloud("aws_cloudwatch", credentials={...})
              .build())

Performance-Optimized Configuration:
    config = (ConfigurationBuilder()
              .setLevel("INFO")
              .enable_security(False)  # Disabled for maximum performance
              .enable_sanitization(False)
              .enable_plugins(False)
              .enable_performance_monitoring(False)
              .add_layer_builder("app")
              .add_console(format="plain-text")
              .add_file("app.log", format="json-lines")
              .build())
"""

from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from .models import LoggingConfig, LogLayer, LogDestination


class DestinationBuilder:
    """
    Builder for individual log destinations (handlers).
    
    This class provides a fluent interface for creating LogDestination configurations.
    It follows Python logging standards exactly, making it familiar to users.
    
    Features:
    - Fluent method chaining for intuitive configuration
    - Support for all destination types (console, file, async_file, cloud)
    - Python logging compatibility (handler.setLevel())
    - Type-safe configuration with automatic validation
    - Performance-first defaults with optional optimizations
    
    Examples:
        # Console destination with colors
        console_dest = (DestinationBuilder("console")
                       .setLevel("INFO")
                       .format("colored")
                       .color_mode("always")
                       .build())
        
        # File destination with rotation
        file_dest = (DestinationBuilder("file")
                    .path("app.log")
                    .format("json-lines")
                    .max_size("10MB")
                    .backup_count(5)
                    .build())
        
        # Async cloud destination
        cloud_dest = (DestinationBuilder("async_cloud")
                     .service_type("aws_cloudwatch")
                     .credentials({"access_key": "...", "secret_key": "..."})
                     .retry_count(3)
                     .timeout(30.0)
                     .build())
    """
    
    def __init__(self, dest_type: str):
        self._type = dest_type
        self._level = None  # Handler level (like handler.setLevel())
        self._path: Optional[str] = None
        self._max_size = "5MB"
        self._backup_count = 3
        self._format = "plain-text"
        self._color_mode = "auto"
        self._url: Optional[str] = None
        self._connection_string: Optional[str] = None
        self._queue_url: Optional[str] = None
        self._service_type: Optional[str] = None
        self._credentials: Optional[Dict[str, str]] = None
        self._retry_count = 3
        self._retry_delay = 1.0
        self._timeout = 30.0
        self._max_connections = 10
        self._extra: Optional[Dict[str, Any]] = None
    
    def setLevel(self, level: str) -> 'DestinationBuilder':
        """
        Set the log level for this destination (handler).
        
        This follows Python logging standard: handler.setLevel(logging.INFO)
        """
        self._level = level.upper()
        return self
    
    def path(self, path: Union[str, Path]) -> 'DestinationBuilder':
        """Set the file path for file destinations."""
        self._path = str(path)
        return self
    
    def max_size(self, size: str) -> 'DestinationBuilder':
        """Set the maximum file size for rotation."""
        self._max_size = size
        return self
    
    def backup_count(self, count: int) -> 'DestinationBuilder':
        """Set the number of backup files to keep."""
        self._backup_count = count
        return self
    
    def format(self, fmt: str) -> 'DestinationBuilder':
        """Set the log format."""
        self._format = fmt
        return self
    
    def color_mode(self, mode: str) -> 'DestinationBuilder':
        """Set the color mode."""
        self._color_mode = mode
        return self
    
    def url(self, url: str) -> 'DestinationBuilder':
        """Set the URL for async HTTP destinations."""
        self._url = url
        return self
    
    def connection_string(self, conn_str: str) -> 'DestinationBuilder':
        """Set the connection string for async database destinations."""
        self._connection_string = conn_str
        return self
    
    def queue_url(self, queue_url: str) -> 'DestinationBuilder':
        """Set the queue URL for async queue destinations."""
        self._queue_url = queue_url
        return self
    
    def service_type(self, service_type: str) -> 'DestinationBuilder':
        """Set the service type for async cloud destinations."""
        self._service_type = service_type
        return self
    
    def credentials(self, credentials: Dict[str, str]) -> 'DestinationBuilder':
        """Set credentials for async destinations."""
        self._credentials = credentials
        return self
    
    def retry_count(self, count: int) -> 'DestinationBuilder':
        """Set the number of retries for async operations."""
        self._retry_count = count
        return self
    
    def retry_delay(self, delay: float) -> 'DestinationBuilder':
        """Set the delay between retries in seconds."""
        self._retry_delay = delay
        return self
    
    def timeout(self, timeout: float) -> 'DestinationBuilder':
        """Set the timeout for async operations in seconds."""
        self._timeout = timeout
        return self
    
    def max_connections(self, max_conn: int) -> 'DestinationBuilder':
        """Set the maximum connections for async sinks."""
        self._max_connections = max_conn
        return self
    
    def extra(self, extra_params: Dict[str, Any]) -> 'DestinationBuilder':
        """Set extra parameters for handler configuration."""
        self._extra = extra_params
        return self
    
    def build(self) -> LogDestination:
        """Build the LogDestination instance."""
        return LogDestination(
            type=self._type,
            level=self._level,
            path=self._path,
            max_size=self._max_size,
            backup_count=self._backup_count,
            format=self._format,
            color_mode=self._color_mode,
            url=self._url,
            connection_string=self._connection_string,
            queue_url=self._queue_url,
            service_type=self._service_type,
            credentials=self._credentials,
            retry_count=self._retry_count,
            retry_delay=self._retry_delay,
            timeout=self._timeout,
            max_connections=self._max_connections,
            extra=self._extra
        )


class LayerBuilder:
    """
    Builder for logging layers (loggers).
    
    This class provides a fluent interface for creating LogLayer configurations.
    It follows Python logging standards exactly, making it familiar to users.
    
    Features:
    - Fluent method chaining for intuitive configuration
    - Python logging compatibility (logger.setLevel())
    - Support for multiple destinations (handlers) per layer
    - Custom colors and layer-specific settings
    - Type-safe configuration with automatic validation
    
    Examples:
        # Basic layer with console and file destinations
        layer = (LayerBuilder("app")
                .setLevel("DEBUG")
                .add_console(format="colored", use_colors=True)
                .add_file("app.log", format="json-lines")
                .build())
        
        # Layer with custom color
        colored_layer = (LayerBuilder("api")
                        .setLevel("INFO")
                        .color("\033[36m")  # Cyan
                        .add_console(format="colored", use_colors=True)
                        .build())
        
        # Layer with async cloud destination
        cloud_layer = (LayerBuilder("production")
                      .setLevel("WARNING")
                      .add_file("prod.log", format="json-lines")
                      .add_async_cloud("aws_cloudwatch", credentials={...})
                      .build())
    """
    
    def __init__(self, name: str):
        self._name = name
        self._level = None  # Logger level (like logger.setLevel())
        self._destinations: List[LogDestination] = []
    
    def setLevel(self, level: str) -> 'LayerBuilder':
        """
        Set the log level for this layer (logger).
        
        This follows Python logging standard: logger.setLevel(logging.INFO)
        """
        self._level = level.upper()
        return self
    
    def add_destination(self, destination: LogDestination) -> 'LayerBuilder':
        """Add a destination to this layer."""
        self._destinations.append(destination)
        return self
    
    def add_console(self, level: str = None, format: str = "colored", color_mode: str = "auto") -> 'LayerBuilder':
        """Add a console destination to this layer."""
        dest = DestinationBuilder("console").format(format).color_mode(color_mode)
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def add_file(self, path: Union[str, Path], level: str = None, format: str = "json", 
                 max_size: str = "10MB", backup_count: int = 5) -> 'LayerBuilder':
        """Add a file destination to this layer."""
        dest = (DestinationBuilder("file")
                .path(path)
                .format(format)
                .max_size(max_size)
                .backup_count(backup_count))
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def add_async_console(self, level: str = None, format: str = "json") -> 'LayerBuilder':
        """Add an async console destination to this layer."""
        dest = DestinationBuilder("async_console").format(format)
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def add_async_file(self, path: Union[str, Path], level: str = None, format: str = "json",
                       max_size: str = "10MB", backup_count: int = 5) -> 'LayerBuilder':
        """Add an async file destination to this layer."""
        dest = (DestinationBuilder("async_file")
                .path(path)
                .format(format)
                .max_size(max_size)
                .backup_count(backup_count))
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def add_async_http(self, url: str, level: str = None, format: str = "json",
                       retry_count: int = 3, timeout: float = 30.0) -> 'LayerBuilder':
        """Add an async HTTP destination to this layer."""
        dest = (DestinationBuilder("async_http")
                .url(url)
                .format(format)
                .retry_count(retry_count)
                .timeout(timeout))
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def add_async_database(self, connection_string: str, level: str = None, format: str = "json",
                          retry_count: int = 3, timeout: float = 30.0) -> 'LayerBuilder':
        """Add an async database destination to this layer."""
        dest = (DestinationBuilder("async_database")
                .connection_string(connection_string)
                .format(format)
                .retry_count(retry_count)
                .timeout(timeout))
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def add_async_queue(self, queue_url: str, level: str = None, format: str = "json",
                       retry_count: int = 3, timeout: float = 30.0) -> 'LayerBuilder':
        """Add an async queue destination to this layer."""
        dest = (DestinationBuilder("async_queue")
                .queue_url(queue_url)
                .format(format)
                .retry_count(retry_count)
                .timeout(timeout))
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def add_async_cloud(self, service_type: str, level: str = None, format: str = "json",
                        credentials: Optional[Dict[str, str]] = None,
                        retry_count: int = 3, timeout: float = 30.0) -> 'LayerBuilder':
        """Add an async cloud destination to this layer."""
        dest = (DestinationBuilder("async_cloud")
                .service_type(service_type)
                .format(format)
                .credentials(credentials)
                .retry_count(retry_count)
                .timeout(timeout))
        if level:
            dest.setLevel(level)
        return self.add_destination(dest.build())
    
    def build(self) -> LogLayer:
        """Build the LogLayer instance."""
        return LogLayer(
            level=self._level or "INFO",  # Default to INFO if no level set
            destinations=self._destinations
        )


class ConfigurationBuilder:
    """
    Main builder for complete logging configurations.
    
    This class provides a fluent interface for creating LoggingConfig configurations.
    It manages global settings, security features, and layer configurations.
    
    Features:
    - Fluent method chaining for intuitive configuration
    - Python logging compatibility (config.setLevel())
    - Support for all security and monitoring features
    - Performance-first defaults with optional optimizations
    - Type-safe configuration with automatic validation
    - Pre-built configuration templates for common use cases
    
    Examples:
        # Basic configuration
        config = (ConfigurationBuilder()
                  .setLevel("INFO")
                  .add_layer_builder("app")
                  .setLevel("DEBUG")
                  .add_console(format="colored", use_colors=True)
                  .add_file("app.log", format="json-lines")
                  .build())
        
        # Production configuration with security
        prod_config = (ConfigurationBuilder()
                      .setLevel("WARNING")
                      .enable_security(True)
                      .enable_sanitization(True)
                      .security_level("high")
                      .add_layer_builder("app")
                      .setLevel("INFO")
                      .add_file("app.log", format="json-lines")
                      .add_async_cloud("aws_cloudwatch", credentials={...})
                      .build())
        
        # Performance-optimized configuration
        fast_config = (ConfigurationBuilder()
                      .setLevel("INFO")
                      .enable_security(False)  # Disabled for maximum performance
                      .enable_sanitization(False)
                      .enable_plugins(False)
                      .enable_performance_monitoring(False)
                      .add_layer_builder("app")
                      .add_console(format="plain-text")
                      .add_file("app.log", format="json-lines")
                      .build())
    """
    
    def __init__(self):
        self._default_level = "INFO"
        self._layers: Dict[str, LogLayer] = {}
        self._layer_colors: Optional[Dict[str, str]] = None
        # PERFORMANCE-FIRST: Disable all features by default for maximum performance
        self._enable_security = False
        self._enable_sanitization = False
        self._enable_plugins = False
        self._enable_performance_monitoring = False
        self._buffer_size = 8192
        self._flush_interval = 1.0
    
    def setLevel(self, level: str) -> 'ConfigurationBuilder':
        """
        Set the default log level for all layers.
        
        This follows Python logging standard: logger.setLevel(logging.INFO)
        """
        self._default_level = level.upper()
        return self
    
    def setDefaultLevel(self, level: str) -> 'ConfigurationBuilder':
        """Alias for setLevel for clarity."""
        return self.setLevel(level)
    
    def enable_security(self, enabled: bool = True) -> 'ConfigurationBuilder':
        """Enable or disable security features."""
        self._enable_security = enabled
        return self
    
    def enable_sanitization(self, enabled: bool = True) -> 'ConfigurationBuilder':
        """Enable or disable data sanitization."""
        self._enable_sanitization = enabled
        return self
    
    def enable_plugins(self, enabled: bool = True) -> 'ConfigurationBuilder':
        """Enable or disable the plugin system."""
        self._enable_plugins = enabled
        return self
    
    def enable_performance_monitoring(self, enabled: bool = True) -> 'ConfigurationBuilder':
        """Enable or disable performance monitoring."""
        self._enable_performance_monitoring = enabled
        return self
    
    def buffer_size(self, size: int) -> 'ConfigurationBuilder':
        """Set the buffer size for file handlers."""
        self._buffer_size = size
        return self
    
    def flush_interval(self, interval: float) -> 'ConfigurationBuilder':
        """Set the flush interval in seconds."""
        self._flush_interval = interval
        return self
    
    def add_layer(self, layer: LogLayer, name: str) -> 'ConfigurationBuilder':
        """Add a layer to the configuration."""
        self._layers[name] = layer
        return self
    
    def add_layer_builder(self, name: str) -> LayerBuilder:
        """Create and return a layer builder for the given name."""
        return LayerBuilder(name)
    
    def layer_colors(self, colors: Dict[str, str]) -> 'ConfigurationBuilder':
        """Set color mapping for different layers in console output."""
        self._layer_colors = colors
        return self
    
    def build(self) -> LoggingConfig:
        """Build the complete LoggingConfig instance."""
        return LoggingConfig(
            default_level=self._default_level,
            layers=self._layers,
            layer_colors=self._layer_colors,
            enable_security=self._enable_security,
            enable_sanitization=self._enable_sanitization,
            enable_plugins=self._enable_plugins,
            enable_performance_monitoring=self._enable_performance_monitoring,
            buffer_size=self._buffer_size,
            flush_interval=self._flush_interval
        )


# Convenience functions following Python logging style
def create_console_config(level: str = "INFO", format: str = "colored") -> LoggingConfig:
    """
    Create a simple console-only configuration.
    
    Args:
        level: Global log level (default: INFO)
        format: Log format (default: colored)
    """
    builder = ConfigurationBuilder().setLevel(level)
    layer = LayerBuilder("default").add_console(format=format).build()
    return builder.add_layer(layer, "default").build()


def create_file_config(path: Union[str, Path], level: str = "INFO", format: str = "json-lines") -> LoggingConfig:
    """
    Create a simple file-only configuration.
    
    Args:
        path: File path for logging
        level: Global log level (default: INFO)
        format: Log format (default: json-lines)
    """
    builder = ConfigurationBuilder().setLevel(level)
    layer = LayerBuilder("default").add_file(path, format=format).build()
    return builder.add_layer(layer, "default").build()


def create_dual_config(console_level: str = None, file_path: Union[str, Path] = "logs/app.log",
                       file_level: str = None, console_format: str = "colored", file_format: str = "json-lines") -> LoggingConfig:
    """
    Create a configuration with both console and file output.
    
    Args:
        console_level: Console log level (None = inherit from global)
        file_path: File path for logging
        file_level: File log level (None = inherit from global)
        console_format: Console format (default: colored)
        file_format: File format (default: json-lines)
        
    Note: Each destination can have its own level, following Python logging handler.setLevel() pattern.
    """
    builder = ConfigurationBuilder().setLevel("INFO")  # Global default
    
    layer = (LayerBuilder("default")
             .add_console(console_level, console_format)
             .add_file(file_path, file_level, file_format)
             .build())
    return builder.add_layer(layer, "default").build()


def create_production_config() -> LoggingConfig:
    """
    Create a production-ready configuration.
    
    Features:
    - Global level: INFO (production standard)
    - App layer: INFO level with file and console
    - Security layer: WARNING level (security events only)
    - Performance layer: INFO level (performance tracking)
    - Error layer: ERROR level (errors only)
    """
    builder = (ConfigurationBuilder()
               .setLevel("INFO")  # Production standard
               .enable_security(True)
               .enable_sanitization(True)
               .enable_plugins(True)
               .enable_performance_monitoring(True)
               .buffer_size(32768)
               .flush_interval(2.0))
    
    # App layer - general application logs
    app_layer = (LayerBuilder("app")
                 .setLevel("INFO")  # Logger level
                 .add_file("logs/app.log", format="json", max_size="100MB", backup_count=10)
                 .add_console(format="compact")
                 .build())
    
    # Security layer - security events only
    security_layer = (LayerBuilder("security")
                      .setLevel("WARNING")  # Logger level
                      .add_file("logs/security.log", format="json", max_size="50MB", backup_count=5)
                      .build())
    
    # Performance layer - performance tracking
    performance_layer = (LayerBuilder("performance")
                         .setLevel("INFO")  # Logger level
                         .add_file("logs/performance.log", format="json", max_size="50MB", backup_count=5)
                         .build())
    
    # Error layer - errors only
    error_layer = (LayerBuilder("error")
                   .setLevel("ERROR")  # Logger level
                   .add_file("logs/error.log", format="json", max_size="50MB", backup_count=5)
                   .build())
    
    return (builder
            .add_layer(app_layer, "app")
            .add_layer(security_layer, "security")
            .add_layer(performance_layer, "performance")
            .add_layer(error_layer, "error")
            .build())


def create_development_config() -> LoggingConfig:
    """
    Create a development-friendly configuration.
    
    Features:
    - Global level: DEBUG (development standard)
    - Dev layer: DEBUG level with colored console and file
    - Fast flush for immediate feedback
    """
    builder = (ConfigurationBuilder()
               .setLevel("DEBUG")  # Development standard
               .enable_security(False)
               .enable_sanitization(False)
               .enable_plugins(True)
               .enable_performance_monitoring(True)
               .buffer_size(4096)
               .flush_interval(0.1))
    
    dev_layer = (LayerBuilder("dev")
                 .setLevel("DEBUG")  # Logger level
                 .add_console(format="colored", color_mode="always")
                 .add_file("logs/dev.log", format="detailed", max_size="5MB", backup_count=2)
                 .build())
    
    return builder.add_layer(dev_layer, "dev").build()


def create_testing_config() -> LoggingConfig:
    """
    Create a testing configuration.
    
    Features:
    - Global level: WARNING (minimal logging for tests)
    - Test layer: WARNING level with null handler
    - Minimal overhead for fast test execution
    """
    builder = (ConfigurationBuilder()
               .setLevel("WARNING")  # Testing standard
               .enable_security(False)
               .enable_sanitization(False)
               .enable_plugins(False)
               .enable_performance_monitoring(False)
               .buffer_size(1024)
               .flush_interval(0.0))
    
    test_layer = (LayerBuilder("test")
                  .setLevel("WARNING")  # Logger level
                  .add_destination(DestinationBuilder("null").build())
                  .build())
    
    return builder.add_layer(test_layer, "test").build()


def create_python_logging_style_example() -> LoggingConfig:
    """
    Create an example showing Python logging style configuration.
    
    This demonstrates the familiar Python logging pattern:
    - logger.setLevel(logging.INFO)
    - handler.setLevel(logging.DEBUG)
    - Simple inheritance and overrides
    """
    builder = ConfigurationBuilder().setLevel("INFO")  # Global default
    
    # Main logger - INFO level
    main_logger = (LayerBuilder("main")
                   .setLevel("INFO")  # logger.setLevel(logging.INFO)
                   .add_console()  # Inherits logger level
                   .add_file("logs/main.log", format="json")  # Inherits logger level
                   .build())
    
    # Debug logger - DEBUG level with specific handler levels
    debug_logger = (LayerBuilder("debug")
                    .setLevel("DEBUG")  # logger.setLevel(logging.DEBUG)
                    .add_console("INFO")  # handler.setLevel(logging.INFO) - override
                    .add_file("logs/debug.log", "DEBUG", "detailed")  # handler.setLevel(logging.DEBUG) - override
                    .build())
    
    # Error logger - ERROR level
    error_logger = (LayerBuilder("error")
                    .setLevel("ERROR")  # logger.setLevel(logging.ERROR)
                    .add_file("logs/error.log", format="json")  # Inherits logger level
                    .build())
    
    return (builder
            .add_layer(main_logger, "main")
            .add_layer(debug_logger, "debug")
            .add_layer(error_logger, "error")
            .build())
