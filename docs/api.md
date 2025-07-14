# Hydra-Logger API Reference

This document provides a comprehensive reference for the Hydra-Logger API, including all classes, methods, and configuration options.

## Table of Contents

- [HydraLogger](#hydralogger)
- [create_logger](#create_logger)
- [AsyncHydraLogger](#asynchydralogger)
- [Configuration Models](#configuration-models)
- [Log Formats](#log-formats)
- [Compatibility Functions](#compatibility-functions)
- [Examples](#examples)

## HydraLogger

The main logging class that provides multi-layered logging capabilities with support for multiple formats and destinations.

### Constructor

```python
HydraLogger(config: Optional[LoggingConfig] = None)
```

**Parameters:**
- `config` (Optional[LoggingConfig]): Configuration object. If None, uses default configuration.

**Example:**
```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig

# With custom configuration
config = LoggingConfig(layers={...})
logger = HydraLogger(config)

# With default configuration
logger = HydraLogger()
```

### Class Methods

#### `from_config(config_path: str) -> HydraLogger`

Create a HydraLogger instance from a configuration file.

**Parameters:**
- `config_path` (str): Path to the configuration file (YAML or TOML)

**Returns:**
- `HydraLogger`: Configured logger instance

**Example:**
```python
from hydra_logger import HydraLogger

logger = HydraLogger.from_config("hydra_logging.yaml")
```

### Instance Methods

#### `log(level: str, message: str, layer: str = "DEFAULT", extra: Optional[Dict[str, Any]] = None) -> None`

Log a message to a specific layer with the specified level.

**Parameters:**
- `level` (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message` (str): The log message
- `layer` (str): The logging layer name (default: "DEFAULT")
- `extra` (Optional[Dict[str, Any]]): Additional data to include in the log

**Example:**
```python
logger.log("INFO", "Request processed successfully", "API")
logger.log("ERROR", "Database connection failed", "DB", extra={"error_code": 500})
```

#### `debug(message: str, layer: str = "DEFAULT", **kwargs) -> None`

Log a debug message to the specified layer.

**Parameters:**
- `message` (str): The debug message
- `layer` (str): The logging layer name (default: "DEFAULT")
- `**kwargs`: Additional data passed to the `extra` parameter

**Example:**
```python
logger.debug("User authentication attempt", "AUTH", extra={"user_id": 12345})
```

#### `info(message: str, layer: str = "DEFAULT", **kwargs) -> None`

Log an info message to the specified layer.

**Parameters:**
- `message` (str): The info message
- `layer` (str): The logging layer name (default: "DEFAULT")
- `**kwargs`: Additional data passed to the `extra` parameter

**Example:**
```python
logger.info("Application started successfully", "APP", extra={"version": "1.0.0"})
```

#### `warning(message: str, layer: str = "DEFAULT", **kwargs) -> None`

Log a warning message to the specified layer.

**Parameters:**
- `message` (str): The warning message
- `layer` (str): The logging layer name (default: "DEFAULT")
- `**kwargs`: Additional data passed to the `extra` parameter

**Example:**
```python
logger.warning("Response time exceeded threshold", "PERF", extra={"response_time_ms": 1500})
```

#### `error(message: str, layer: str = "DEFAULT", **kwargs) -> None`

Log an error message to the specified layer.

**Parameters:**
- `message` (str): The error message
- `layer` (str): The logging layer name (default: "DEFAULT")
- `**kwargs`: Additional data passed to the `extra` parameter

**Example:**
```python
logger.error("Database connection failed", "DB", extra={"error_code": 500, "retry_count": 3})
```

#### `critical(message: str, layer: str = "DEFAULT", **kwargs) -> None`

Log a critical message to the specified layer.

**Parameters:**
- `message` (str): The critical message
- `layer` (str): The logging layer name (default: "DEFAULT")
- `**kwargs`: Additional data passed to the `extra` parameter

**Example:**
```python
logger.critical("System shutdown required", "SYSTEM", extra={"reason": "memory_exhaustion"})
```

#### `get_logger(layer: str) -> logging.Logger`

Get the underlying Python logging.Logger for a specific layer.

**Parameters:**
- `layer` (str): The logging layer name

**Returns:**
- `logging.Logger`: The underlying logger instance

**Example:**
```python
import logging
logger_instance = logger.get_logger("API")
logger_instance.setLevel(logging.DEBUG)
```

#### `get_performance_metrics() -> Dict[str, Any]`

Get performance metrics for the logger.

**Returns:**
- `Dict[str, Any]`: Dictionary containing performance metrics

**Example:**
```python
metrics = logger.get_performance_metrics()
print(f"Total logs: {metrics['total_logs']}")
print(f"Average latency: {metrics['avg_latency_ms']}ms")
```

## create_logger

A convenience function for creating HydraLogger instances with default configuration.

### Function Signature

```python
create_logger(
    config: Optional[dict] = None,
    enable_security: bool = True,
    enable_sanitization: bool = True,
    enable_plugins: bool = True
) -> HydraLogger
```

**Parameters:**
- `config` (Optional[dict]): Optional configuration dictionary
- `enable_security` (bool): Enable security validation (default: True)
- `enable_sanitization` (bool): Enable data sanitization (default: True)
- `enable_plugins` (bool): Enable plugin system (default: True)

**Returns:**
- `HydraLogger`: Configured logger instance

**Example:**
```python
from hydra_logger import create_logger

# Simplest way to get started
logger = create_logger()
logger.info("Application started")

# Disable security features for performance
logger = create_logger(enable_security=False)

# Disable plugins for simpler setup
logger = create_logger(enable_plugins=False)

# Custom configuration with some features disabled
logger = create_logger(
    config={"layers": {"app": {"level": "DEBUG"}}},
    enable_sanitization=False,
    enable_plugins=False
)
```

## AsyncHydraLogger

Professional async logger with world-class reliability and context management.

### Constructor

```python
AsyncHydraLogger(config=None, **kwargs)
```

**Parameters:**
- `config`: Logging configuration (dict or None)
- `**kwargs`: Additional configuration options

**Example:**
```python
from hydra_logger.async_hydra import AsyncHydraLogger

logger = AsyncHydraLogger({
    'handlers': [
        {'type': 'file', 'filename': 'mylog.log'},
        {'type': 'console', 'use_colors': True}
    ]
})
```

### Async Methods

#### `async log(layer: str, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None`

Log a message asynchronously to a specific layer.

**Parameters:**
- `layer` (str): The logging layer name
- `level` (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message` (str): The log message
- `extra` (Optional[Dict[str, Any]]): Additional data to include in the log

**Example:**
```python
await logger.log("API", "INFO", "Request processed successfully")
await logger.log("DB", "ERROR", "Database connection failed", extra={"error_code": 500})
```

#### `async info(layer_or_message: str, message: Optional[str] = None) -> None`

Log an info message asynchronously.

**Parameters:**
- `layer_or_message` (str): Layer name or message (if message is None)
- `message` (Optional[str]): The info message (if layer_or_message is layer)

**Example:**
```python
await logger.info("API", "Request processed successfully")
await logger.info("Application started")  # Uses default layer
```

#### `async debug(layer_or_message: str, message: Optional[str] = None) -> None`

Log a debug message asynchronously.

**Parameters:**
- `layer_or_message` (str): Layer name or message (if message is None)
- `message` (Optional[str]): The debug message (if layer_or_message is layer)

**Example:**
```python
await logger.debug("AUTH", "User authentication attempt")
await logger.debug("Debug information")  # Uses default layer
```

#### `async warning(layer_or_message: str, message: Optional[str] = None) -> None`

Log a warning message asynchronously.

**Parameters:**
- `layer_or_message` (str): Layer name or message (if message is None)
- `message` (Optional[str]): The warning message (if layer_or_message is layer)

**Example:**
```python
await logger.warning("PERF", "Response time exceeded threshold")
await logger.warning("Performance warning")  # Uses default layer
```

#### `async error(layer_or_message: str, message: Optional[str] = None) -> None`

Log an error message asynchronously.

**Parameters:**
- `layer_or_message` (str): Layer name or message (if message is None)
- `message` (Optional[str]): The error message (if layer_or_message is layer)

**Example:**
```python
await logger.error("DB", "Database connection failed")
await logger.error("Critical error occurred")  # Uses default layer
```

#### `async critical(layer_or_message: str, message: Optional[str] = None) -> None`

Log a critical message asynchronously.

**Parameters:**
- `layer_or_message` (str): Layer name or message (if message is None)
- `message` (Optional[str]): The critical message (if layer_or_message is layer)

**Example:**
```python
await logger.critical("SYSTEM", "System shutdown required")
await logger.critical("System failure")  # Uses default layer
```

#### `async initialize() -> None`

Initialize the async logger.

**Example:**
```python
await logger.initialize()
```

#### `async aclose() -> None`

Close the async logger gracefully.

**Example:**
```python
await logger.aclose()
```

#### `get_health_status() -> Dict[str, Any]`

Get health status of the async logger.

**Returns:**
- `Dict[str, Any]`: Health status information

**Example:**
```python
health = logger.get_health_status()
print(f"Healthy: {health['is_healthy']}")
```

#### `get_performance_metrics() -> Dict[str, Any]`

Get performance metrics for the async logger.

**Returns:**
- `Dict[str, Any]`: Performance metrics

**Example:**
```python
metrics = logger.get_performance_metrics()
print(f"Total async logs: {metrics['total_logs']}")
```

## Configuration Models

### LoggingConfig

Main configuration container that holds all logging layers and their settings.

```python
class LoggingConfig(BaseModel):
    layers: Dict[str, LogLayer]
```

**Example:**
```python
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

config = LoggingConfig(
    layers={
        "API": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/api/requests.json",
                    format="json"
                )
            ]
        )
    }
)
```

### LogLayer

Configuration for a single logging layer.

```python
class LogLayer(BaseModel):
    level: str = Field(default="INFO", description="Default level for this layer")
    destinations: List[LogDestination] = Field(
        default_factory=list, description="Destinations for this layer"
    )
```

### LogDestination

Configuration for a single log destination.

```python
class LogDestination(BaseModel):
    type: Literal["file", "console", "async_http", "async_database", "async_queue", "async_cloud"]
    level: str = Field(default="INFO", description="Logging level for this destination")
    path: Optional[str] = Field(default=None, description="File path (required for file type)")
    format: str = Field(default="plain-text", description="Log format")
    color_mode: Literal["auto", "always", "never"] = Field(default="auto", description="Color mode")
```

## Log Formats

Hydra-Logger supports multiple log formats:

### Plain Text Format
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "console", "format": "plain-text"}
            ]
        }
    }
}
```

### JSON Format
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/app.json", "format": "json"}
            ]
        }
    }
}
```

### CSV Format
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/app.csv", "format": "csv"}
            ]
        }
    }
}
```

### Syslog Format
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/app.log", "format": "syslog"}
            ]
        }
    }
}
```

### GELF Format
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/app.gelf", "format": "gelf"}
            ]
        }
    }
}
```

## Compatibility Functions

### Magic Configuration Methods

#### `for_production(**kwargs) -> HydraLogger`

Create a production-ready logger.

**Example:**
```python
logger = HydraLogger.for_production()
```

#### `for_development(**kwargs) -> HydraLogger`

Create a development-friendly logger.

**Example:**
```python
logger = HydraLogger.for_development()
```

#### `for_testing(**kwargs) -> HydraLogger`

Create a testing-focused logger.

**Example:**
```python
logger = HydraLogger.for_testing()
```

#### `for_microservice(**kwargs) -> HydraLogger`

Create a microservice-optimized logger.

**Example:**
```python
logger = HydraLogger.for_microservice()
```

#### `for_web_app(**kwargs) -> HydraLogger`

Create a web application logger.

**Example:**
```python
logger = HydraLogger.for_web_app()
```

#### `for_api_service(**kwargs) -> HydraLogger`

Create an API service logger.

**Example:**
```python
logger = HydraLogger.for_api_service()
```

#### `for_background_worker(**kwargs) -> HydraLogger`

Create a background worker logger.

**Example:**
```python
logger = HydraLogger.for_background_worker()
```

#### `for_minimal_features(**kwargs) -> HydraLogger`

Create a logger with minimal features for maximum performance.

**Example:**
```python
logger = HydraLogger.for_minimal_features()
```

#### `for_bare_metal(**kwargs) -> HydraLogger`

Create a bare metal logger for maximum performance.

**Example:**
```python
logger = HydraLogger.for_bare_metal()
```

### Plugin System

#### `add_plugin(name: str, plugin: Any) -> None`

Add a plugin to the logger.

**Parameters:**
- `name` (str): Plugin name
- `plugin` (Any): Plugin instance

**Example:**
```python
from hydra_logger import HydraLogger, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        return {"processed": True}

logger = HydraLogger(enable_plugins=True)
logger.add_plugin("custom_analytics", CustomAnalytics())
```

#### `remove_plugin(name: str) -> bool`

Remove a plugin from the logger.

**Parameters:**
- `name` (str): Plugin name

**Returns:**
- `bool`: True if plugin was removed

**Example:**
```python
removed = logger.remove_plugin("custom_analytics")
```

#### `get_plugin_insights() -> Dict[str, Any]`

Get insights from all plugins.

**Returns:**
- `Dict[str, Any]`: Plugin insights

**Example:**
```python
insights = logger.get_plugin_insights()
```

## Examples

### Basic Usage

```python
from hydra_logger import HydraLogger

# Create logger with default configuration
logger = HydraLogger()

# Log messages to different layers
logger.info("APP", "Application started")
logger.info("API", "Request received")
logger.info("DB", "Query executed")
```

### Advanced Configuration

```python
from hydra_logger import HydraLogger

config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},
                {"type": "file", "path": "logs/app.log", "format": "json"}
            ]
        },
        "API": {
            "level": "DEBUG",
            "destinations": [
                {"type": "file", "path": "logs/api/requests.json", "format": "json"}
            ]
        }
    }
}

logger = HydraLogger(config=config)
```

### Async Logging

```python
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.async_hydra.context import async_context, trace_context

async with AsyncHydraLogger() as logger:
    async with async_context(context_id="request-123"):
        await logger.info("REQUEST", "Processing request")
    
    async with trace_context(trace_id="trace-456"):
        await logger.info("TRACE", "Request traced")
```

### Performance Monitoring

```python
from hydra_logger.async_hydra.performance import get_performance_monitor

monitor = get_performance_monitor()
async with monitor.async_timer("operation"):
    await logger.info("PERF", "Operation completed")

stats = monitor.get_async_statistics()
print(f"Average operation time: {stats['average_duration']}ms")
```

### Data Protection

```python
from hydra_logger.data_protection import FallbackHandler, DataLossProtection

# Atomic file operations
handler = FallbackHandler()
handler.safe_write_json(data, "logs/critical.json")

# Data loss protection
protection = DataLossProtection()
await protection.backup_message("critical message", "error_queue")
``` 