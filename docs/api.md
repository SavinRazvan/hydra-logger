# Hydra-Logger API Reference

This document provides a comprehensive reference for the Hydra-Logger API, including all classes, methods, and configuration options.

## Table of Contents

- [HydraLogger](#hydralogger)
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

#### `log(layer: str, level: str, message: str) -> None`

Log a message to a specific layer with the specified level.

**Parameters:**
- `layer` (str): The logging layer name
- `level` (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `message` (str): The log message

**Example:**
```python
logger.log("API", "INFO", "Request processed successfully")
```

#### `debug(layer: str, message: str) -> None`

Log a debug message to the specified layer.

**Parameters:**
- `layer` (str): The logging layer name
- `message` (str): The debug message

**Example:**
```python
logger.debug("AUTH", "User authentication attempt")
```

#### `info(layer: str, message: str) -> None`

Log an info message to the specified layer.

**Parameters:**
- `layer` (str): The logging layer name
- `message` (str): The info message

**Example:**
```python
logger.info("APP", "Application started successfully")
```

#### `warning(layer: str, message: str) -> None`

Log a warning message to the specified layer.

**Parameters:**
- `layer` (str): The logging layer name
- `message` (str): The warning message

**Example:**
```python
logger.warning("PERF", "Response time exceeded threshold")
```

#### `error(layer: str, message: str) -> None`

Log an error message to the specified layer.

**Parameters:**
- `layer` (str): The logging layer name
- `message` (str): The error message

**Example:**
```python
logger.error("DB", "Database connection failed")
```

#### `critical(layer: str, message: str) -> None`

Log a critical message to the specified layer.

**Parameters:**
- `layer` (str): The logging layer name
- `message` (str): The critical message

**Example:**
```python
logger.critical("SYSTEM", "System shutdown required")
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
    level: str
    destinations: List[LogDestination]
```

**Parameters:**
- `level` (str): Log level for this layer (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `destinations` (List[LogDestination]): List of destinations for this layer

**Example:**
```python
from hydra_logger.config import LogLayer, LogDestination

layer = LogLayer(
    level="INFO",
    destinations=[
        LogDestination(type="file", path="logs/app.log", format="text"),
        LogDestination(type="console", format="json")
    ]
)
```

### LogDestination

Configuration for a single logging destination.

```python
class LogDestination(BaseModel):
    type: str
    path: Optional[str] = None
    level: Optional[str] = None
    max_size: Optional[str] = None
    backup_count: Optional[int] = None
    format: Optional[str] = None
```

**Parameters:**
- `type` (str): Destination type ("file" or "console")
- `path` (Optional[str]): File path for file destinations
- `level` (Optional[str]): Override log level for this destination
- `max_size` (Optional[str]): Maximum file size (e.g., "10MB", "1GB")
- `backup_count` (Optional[int]): Number of backup files to keep
- `format` (Optional[str]): Log format ("text", "json", "csv", "syslog", "gelf")

**Example:**
```python
from hydra_logger.config import LogDestination

# File destination with JSON format
file_dest = LogDestination(
    type="file",
    path="logs/api/requests.json",
    max_size="10MB",
    backup_count=5,
    format="json"
)

# Console destination with text format
console_dest = LogDestination(
    type="console",
    level="WARNING",
    format="text"
)
```

## Log Formats

Hydra-Logger supports multiple log formats for different use cases:

### Text Format (Default)

Traditional plain text logging with timestamps and log levels.

**Output Example:**
```
2025-07-03 14:30:15 INFO [hydra.API] Request processed successfully (logger.py:483)
```

**Configuration:**
```python
LogDestination(type="file", path="logs/app.log", format="text")
```

### JSON Format

Structured JSON format for log aggregation and analysis. Each log entry is a valid JSON object.

**Output Example:**
```json
{"timestamp": "2025-07-03 14:30:15", "level": "INFO", "logger": "hydra.API", "message": "Request processed successfully", "filename": "logger.py", "lineno": 483}
```

**Configuration:**
```python
LogDestination(type="file", path="logs/api/requests.json", format="json")
```

**Fields:**
- `timestamp`: ISO format timestamp
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name with layer prefix
- `message`: The log message
- `filename`: Source file name
- `lineno`: Line number in source file

### CSV Format

Comma-separated values for analytics and data processing.

**Output Example:**
```csv
timestamp,level,logger,message,filename,lineno
2025-07-03 14:30:15,INFO,hydra.API,Request processed successfully,logger.py,483
```

**Configuration:**
```python
LogDestination(type="file", path="logs/analytics/metrics.csv", format="csv")
```

### Syslog Format

Standard syslog format for system integration.

**Output Example:**
```
<134>2025-07-03T14:30:15.123Z hostname hydra.API: Request processed successfully
```

**Configuration:**
```python
LogDestination(type="file", path="logs/system/app.log", format="syslog")
```

### GELF Format

Graylog Extended Log Format for centralized logging systems.

**Output Example:**
```json
{"version": "1.1", "host": "hostname", "short_message": "Request processed successfully", "level": 6, "_logger": "hydra.API"}
```

**Configuration:**
```python
LogDestination(type="file", path="logs/monitoring/alerts.gelf", format="gelf")
```

## Compatibility Functions

### setup_logging

Original flexiai setup_logging function for backward compatibility.

```python
def setup_logging(
    enable_file_logging: bool = True,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_file_path: str = "app.log",
    max_size: str = "10MB",
    backup_count: int = 5
) -> None
```

**Parameters:**
- `enable_file_logging` (bool): Whether to enable file logging
- `console_level` (int): Console log level
- `file_level` (int): File log level
- `log_file_path` (str): Path to log file
- `max_size` (str): Maximum file size
- `backup_count` (int): Number of backup files

**Example:**
```python
from hydra_logger import setup_logging
import logging

setup_logging(
    enable_file_logging=True,
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    log_file_path="logs/app.log"
)
```

### migrate_to_hydra

Migration helper function to convert from setup_logging to HydraLogger.

```python
def migrate_to_hydra(
    enable_file_logging: bool = True,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    log_file_path: str = "app.log",
    max_size: str = "10MB",
    backup_count: int = 5
) -> HydraLogger
```

**Parameters:**
- `enable_file_logging` (bool): Whether to enable file logging
- `console_level` (int): Console log level
- `file_level` (int): File log level
- `log_file_path` (str): Path to log file
- `max_size` (str): Maximum file size
- `backup_count` (int): Number of backup files

**Returns:**
- `HydraLogger`: Configured logger instance

**Example:**
```python
from hydra_logger import migrate_to_hydra
import logging

logger = migrate_to_hydra(
    enable_file_logging=True,
    console_level=logging.INFO,
    file_level=logging.DEBUG,
    log_file_path="logs/custom/app.log"
)

# Use the new logger
logger.info("DEFAULT", "Application started")
```

## Examples

### Basic Multi-Layer Configuration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/app.log", format="text"),
                LogDestination(type="console", format="json")
            ]
        ),
        "API": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/api/requests.json", format="json")
            ]
        ),
        "ERRORS": LogLayer(
            level="ERROR",
            destinations=[
                LogDestination(type="file", path="logs/errors.log", format="text"),
                LogDestination(type="console", level="CRITICAL", format="gelf")
            ]
        )
    }
)

logger = HydraLogger(config)

# Log to different layers
logger.info("APP", "Application started")
logger.debug("API", "API request received")
logger.error("ERRORS", "Database connection failed")
```

### Configuration File Example

**hydra_logging.yaml:**
```yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: "logs/app.log"
        format: text
      - type: console
        format: json
  
  API:
    level: DEBUG
    destinations:
      - type: file
        path: "logs/api/requests.json"
        max_size: "10MB"
        backup_count: 5
        format: json
  
  ANALYTICS:
    level: INFO
    destinations:
      - type: file
        path: "logs/analytics/metrics.csv"
        format: csv
```

**Usage:**
```python
from hydra_logger import HydraLogger

logger = HydraLogger.from_config("hydra_logging.yaml")

logger.info("APP", "Application started")
logger.debug("API", "API request processed")
logger.info("ANALYTICS", "Performance metric recorded")
```

### Advanced Format Configuration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

config = LoggingConfig(
    layers={
        "STRUCTURED": LogLayer(
            level="INFO",
            destinations=[
                # JSON format for log aggregation
                LogDestination(
                    type="file",
                    path="logs/structured/events.json",
                    format="json"
                ),
                # CSV format for analytics
                LogDestination(
                    type="file",
                    path="logs/structured/metrics.csv",
                    format="csv"
                ),
                # Syslog format for system monitoring
                LogDestination(
                    type="file",
                    path="logs/structured/system.log",
                    format="syslog"
                ),
                # GELF format for Graylog
                LogDestination(
                    type="file",
                    path="logs/structured/graylog.gelf",
                    format="gelf"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Single log message goes to all formats
logger.info("STRUCTURED", "User action completed")
```

This will generate the same log message in four different formats, each optimized for its specific use case. 