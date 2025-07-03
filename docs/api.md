# API Reference

This document provides a complete reference for the Hydra-Logger API.

## HydraLogger

The main class for creating and managing multi-layered loggers.

### Constructor

```python
HydraLogger(config: Optional[LoggingConfig] = None)
```

**Parameters:**
- `config` (Optional[LoggingConfig]): Configuration object. If None, uses default configuration.

### Methods

#### `info(layer: str, message: str, *args, **kwargs)`
Log an info message to the specified layer.

**Parameters:**
- `layer` (str): The logging layer name
- `message` (str): The message to log
- `*args, **kwargs`: Additional arguments passed to the logger

#### `debug(layer: str, message: str, *args, **kwargs)`
Log a debug message to the specified layer.

#### `warning(layer: str, message: str, *args, **kwargs)`
Log a warning message to the specified layer.

#### `error(layer: str, message: str, *args, **kwargs)`
Log an error message to the specified layer.

#### `critical(layer: str, message: str, *args, **kwargs)`
Log a critical message to the specified layer.

#### `from_config(config_path: str) -> HydraLogger`
Create a HydraLogger instance from a configuration file.

**Parameters:**
- `config_path` (str): Path to the configuration file (YAML or TOML)

**Returns:**
- `HydraLogger`: Configured logger instance

### Class Methods

#### `get_logger(layer: str) -> logging.Logger`
Get the underlying logging.Logger for a specific layer.

**Parameters:**
- `layer` (str): The logging layer name

**Returns:**
- `logging.Logger`: The logger instance for the layer

## LoggingConfig

Configuration class for defining logging layers and destinations.

### Constructor

```python
LoggingConfig(layers: Dict[str, LogLayer])
```

**Parameters:**
- `layers` (Dict[str, LogLayer]): Dictionary mapping layer names to LogLayer configurations

### Example

```python
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/app.log"),
                LogDestination(type="console", level="WARNING")
            ]
        )
    }
)
```

## LogLayer

Configuration for a single logging layer.

### Constructor

```python
LogLayer(level: str, destinations: List[LogDestination])
```

**Parameters:**
- `level` (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `destinations` (List[LogDestination]): List of destinations for this layer

## LogDestination

Configuration for a single logging destination.

### Constructor

```python
LogDestination(
    type: str,
    level: Optional[str] = None,
    path: Optional[str] = None,
    max_size: Optional[str] = None,
    backup_count: Optional[int] = None
)
```

**Parameters:**
- `type` (str): Destination type ("file" or "console")
- `level` (Optional[str]): Override level for this destination
- `path` (Optional[str]): File path (required for file destinations)
- `max_size` (Optional[str]): Maximum file size (e.g., "10MB", "1GB")
- `backup_count` (Optional[int]): Number of backup files to keep

### Example

```python
# File destination
file_dest = LogDestination(
    type="file",
    path="logs/app.log",
    max_size="10MB",
    backup_count=5
)

# Console destination
console_dest = LogDestination(
    type="console",
    level="WARNING"
)
```

## Backward Compatibility Functions

### `setup_logging`

```python
setup_logging(
    enable_file_logging: bool = True,
    console_level: int = logging.INFO,
    log_file_path: str = "logs/app.log",
    max_size: str = "10MB",
    backup_count: int = 5
)
```

Legacy function for backward compatibility with existing code.

### `migrate_to_hydra`

```python
migrate_to_hydra(
    enable_file_logging: bool = True,
    console_level: int = logging.INFO,
    log_file_path: str = "logs/app.log",
    max_size: str = "10MB",
    backup_count: int = 5
) -> HydraLogger
```

Migrate from legacy logging to HydraLogger with custom configuration.

## Configuration File Formats

### YAML Format

```yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        max_size: 10MB
        backup_count: 5
      - type: console
        level: WARNING
  
  DEBUG:
    level: DEBUG
    destinations:
      - type: file
        path: logs/debug.log
        max_size: 5MB
        backup_count: 3
```

### TOML Format

```toml
[layers.APP]
level = "INFO"

[[layers.APP.destinations]]
type = "file"
path = "logs/app.log"
max_size = "10MB"
backup_count = 5

[[layers.APP.destinations]]
type = "console"
level = "WARNING"

[layers.DEBUG]
level = "DEBUG"

[[layers.DEBUG.destinations]]
type = "file"
path = "logs/debug.log"
max_size = "5MB"
backup_count = 3
```

## Error Handling

The HydraLogger gracefully handles various error conditions:

- **Invalid configuration**: Raises `ValidationError` with detailed error messages
- **File permission errors**: Falls back to console logging
- **Directory creation failures**: Attempts to create parent directories
- **Invalid log levels**: Uses default level (INFO)

## Thread Safety

All HydraLogger operations are thread-safe and can be used in multi-threaded applications without additional synchronization. 