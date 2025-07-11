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
        LogDestination(type="file", path="logs/app.log", format="plain-text"),
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
    color_mode: Optional[str] = None
```

**Parameters:**
- `type` (str): Destination type ("file" or "console")
- `path` (Optional[str]): File path for file destinations
- `level` (Optional[str]): Override log level for this destination
- `max_size` (Optional[str]): Maximum file size (e.g., "10MB", "1GB")
- `backup_count` (Optional[int]): Number of backup files to keep
- `format` (Optional[str]): Log format ("plain-text", "json", "csv", "syslog", "gelf")
- `color_mode` (Optional[str]): Color mode ("auto", "always", "never")

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

# Console destination with plain-text format
console_dest = LogDestination(
    type="console",
    level="WARNING",
    format="plain-text",
    color_mode="always"
)
```

## Log Formats

Hydra-Logger supports multiple log formats for different use cases:

### Plain-Text Format (Default)

Traditional plain text logging with timestamps and log levels.

**Output Example:**
```
2024-01-15 10:30:45 - INFO - [API] Request processed successfully
```

**Configuration:**
```python
LogDestination(type="file", path="logs/app.log", format="plain-text")
```

### JSON Format

Structured JSON format for log aggregation and analysis. Each log entry is a valid JSON object.

**Output Example:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "API",
  "message": "Request processed successfully",
  "filename": "logger.py",
  "lineno": 483
}
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
2024-01-15T10:30:45.123Z,INFO,API,Request processed successfully,logger.py,483
```

**Configuration:**
```python
LogDestination(type="file", path="logs/analytics/metrics.csv", format="csv")
```

### Syslog Format

Standard syslog format for system integration.

**Output Example:**
```
<134>hostname API: Request processed successfully
```

**Configuration:**
```python
LogDestination(type="file", path="logs/system/app.log", format="syslog")
```

### GELF Format

Graylog Extended Log Format for centralized logging systems.

**Output Example:**
```json
{
  "version": "1.1",
  "host": "hostname",
  "short_message": "Request processed successfully",
  "level": 6,
  "_logger": "API"
}
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
logger.info("Application started", "DEFAULT")
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
                LogDestination(type="file", path="logs/app.log", format="plain-text"),
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
                LogDestination(type="file", path="logs/errors.log", format="plain-text"),
                LogDestination(type="console", level="CRITICAL", format="gelf")
            ]
        )
    }
)

logger = HydraLogger(config)

# Log to different layers
logger.info("Application started", "APP")
logger.debug("API request received", "API")
logger.error("Database connection failed", "ERRORS")
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
        format: plain-text
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

logger.info("Application loaded from configuration file", "APP")
logger.debug("API request processed", "API")
logger.info("Performance metric recorded", "ANALYTICS")
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
logger.info("User action completed", "STRUCTURED")
```

This will generate the same log message in four different formats, each optimized for its specific use case.

## Best Practices

### Configuration Best Practices

#### Layer Organization
```python
# Good: Meaningful layer names
config = LoggingConfig(
    layers={
        "APP": LogLayer(...),      # Application logs
        "API": LogLayer(...),      # API request logs
        "DB": LogLayer(...),       # Database logs
        "SECURITY": LogLayer(...), # Security events
        "PERFORMANCE": LogLayer(...) # Performance metrics
    }
)

# Avoid: Generic names
config = LoggingConfig(
    layers={
        "LOG1": LogLayer(...),
        "LOG2": LogLayer(...),
        "LOG3": LogLayer(...)
    }
)
```

#### Format Selection
```python
# Good: Choose formats based on use case
config = LoggingConfig(
    layers={
        "DEBUG": LogLayer(
            destinations=[
                LogDestination(type="file", path="logs/debug.log", format="plain-text")  # Human-readable
            ]
        ),
        "ANALYTICS": LogLayer(
            destinations=[
                LogDestination(type="file", path="logs/analytics.csv", format="csv")  # Data analysis
            ]
        ),
        "MONITORING": LogLayer(
            destinations=[
                LogDestination(type="file", path="logs/monitoring.json", format="json")  # Log aggregation
            ]
        )
    }
)
```

#### File Management
```python
# Good: Appropriate file sizes and backup counts
config = LoggingConfig(
    layers={
        "HIGH_VOLUME": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/high_volume.csv",
                    max_size="100MB",    # Large files for high volume
                    backup_count=2       # Few backups to save space
                )
            ]
        ),
        "CRITICAL": LogLayer(
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/critical.log",
                    max_size="1MB",      # Small files for critical logs
                    backup_count=20      # Many backups for retention
                )
            ]
        )
    }
)
```

### Security Best Practices

#### Sensitive Data Handling
```python
import re
from hydra_logger import HydraLogger

class SecureLogger:
    """Logger with sensitive data filtering."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self.sensitive_patterns = [
            r'password["\']?\s*[:=]\s*["\'][^"\']*["\']',
            r'api_key["\']?\s*[:=]\s*["\'][^"\']*["\']',
            r'token["\']?\s*[:=]\s*["\'][^"\']*["\']',
            r'secret["\']?\s*[:=]\s*["\'][^"\']*["\']'
        ]
    
    def _filter_sensitive_data(self, message):
        """Filter sensitive data from log messages."""
        filtered_message = message
        for pattern in self.sensitive_patterns:
            filtered_message = re.sub(pattern, '[REDACTED]', filtered_message, flags=re.IGNORECASE)
        return filtered_message
    
    def log(self, layer, level, message):
        """Log message with sensitive data filtering."""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.log(level, filtered_message, layer)

# Usage
secure_logger = SecureLogger(config)
secure_logger.log("APP", "INFO", "User login: password=secret123")  # Will be filtered
```

#### File Permissions
```python
import os
from pathlib import Path

# Set secure permissions for log directories
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Set directory permissions (Unix-like systems)
os.chmod(log_dir, 0o750)  # Owner read/write/execute, group read/execute

# Log files will inherit secure permissions
logger = HydraLogger(config)
```

### Performance Best Practices

#### High-Throughput Logging
```python
# Good: Use CSV format for high-volume data
config = LoggingConfig(
    layers={
        "EVENTS": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/events.csv",
                    format="csv",  # Fastest format for high volume
                    max_size="500MB",
                    backup_count=1
                )
            ]
        )
    }
)
```

#### Memory-Efficient Configuration
```python
# Good: Use smaller files for memory-constrained environments
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    max_size="1MB",  # Smaller files
                    backup_count=1   # Fewer backups
                )
            ]
        )
    }
)
```

#### Thread-Safe Logging
```python
import threading
from hydra_logger import HydraLogger

class ThreadSafeLogger:
    """Thread-safe wrapper for HydraLogger."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self._lock = threading.Lock()
    
    def log(self, layer, level, message):
        """Thread-safe logging."""
        with self._lock:
            self.logger.log(level, message, layer)
    
    def info(self, layer, message):
        """Thread-safe info logging."""
        with self._lock:
            self.logger.info(message, layer)

# Usage in multi-threaded applications
thread_safe_logger = ThreadSafeLogger(config)
```

### Architecture Best Practices

#### Environment-Specific Configuration
```python
import os
from hydra_logger import HydraLogger

def get_environment_config():
    """Get configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    configs = {
        "development": {
            "layers": {
                "APP": {
                    "level": "DEBUG",
                    "destinations": [
                        {"type": "file", "path": "logs/dev/app.log", "format": "plain-text"},
                        {"type": "console", "level": "DEBUG", "format": "plain-text"}
                    ]
                }
            }
        },
        "production": {
            "layers": {
                "APP": {
                    "level": "INFO",
                    "destinations": [
                        {"type": "file", "path": "logs/prod/app.log", "format": "json"},
                        {"type": "console", "level": "ERROR", "format": "json"}
                    ]
                }
            }
        }
    }
    
    return configs.get(env, configs["development"])

# Load environment-specific configuration
config = LoggingConfig(**get_environment_config())
logger = HydraLogger(config)
```

#### Modular Configuration
```python
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def create_app_layer():
    """Create application layer configuration."""
    return LogLayer(
        level="INFO",
        destinations=[
            LogDestination(type="file", path="logs/app.log", format="plain-text"),
            LogDestination(type="console", format="json")
        ]
    )

def create_api_layer():
    """Create API layer configuration."""
    return LogLayer(
        level="DEBUG",
        destinations=[
            LogDestination(type="file", path="logs/api/requests.json", format="json")
        ]
    )

def create_security_layer():
    """Create security layer configuration."""
    return LogLayer(
        level="WARNING",
        destinations=[
            LogDestination(type="file", path="logs/security/events.log", format="syslog")
        ]
    )

# Combine layers into configuration
config = LoggingConfig(
    layers={
        "APP": create_app_layer(),
        "API": create_api_layer(),
        "SECURITY": create_security_layer()
    }
)

logger = HydraLogger(config)
```

### Monitoring and Debugging Best Practices

#### Configuration Validation
```python
from hydra_logger.config import LoggingConfig

def validate_config(config_dict):
    """Validate configuration before creating logger."""
    try:
        config = LoggingConfig(**config_dict)
        print("Configuration is valid")
        return config
    except Exception as e:
        print(f"Configuration error: {e}")
        return None

# Test your configuration
test_config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {
                    "type": "file",
                    "path": "logs/app.log",
                    "format": "plain-text"
                }
            ]
        }
    }
}

valid_config = validate_config(test_config)
if valid_config:
    logger = HydraLogger(valid_config)
```

#### Configuration Debugging
```python
def debug_config(config):
    """Debug configuration by printing details."""
    print("Configuration Debug:")
    print(f"  Default Level: {config.default_level}")
    print(f"  Layers: {len(config.layers)}")
    
    for layer_name, layer_config in config.layers.items():
        print(f"  Layer '{layer_name}':")
        print(f"    Level: {layer_config.level}")
        print(f"    Destinations: {len(layer_config.destinations)}")
        
        for i, dest in enumerate(layer_config.destinations):
            print(f"    Destination {i+1}:")
            print(f"      Type: {dest.type}")
            if dest.path:
                print(f"      Path: {dest.path}")
            print(f"      Format: {dest.format}")
            print(f"      Level: {dest.level}")

# Use with your configuration
config = LoggingConfig(layers={...})  # Your config
debug_config(config)
logger = HydraLogger(config)
```

### Production Deployment Best Practices

#### Error Handling
```python
from hydra_logger import HydraLogger
from pydantic import ValidationError

def create_logger_safely(config_path=None):
    """Create logger with comprehensive error handling."""
    try:
        if config_path:
            logger = HydraLogger.from_config(config_path)
        else:
            logger = HydraLogger()  # Use defaults
        
        # Test the logger
        logger.info("Logger initialized successfully", "APP")
        return logger
        
    except FileNotFoundError:
        print("Configuration file not found, using defaults")
        return HydraLogger()
        
    except ValidationError as e:
        print(f"Configuration validation error: {e}")
        return HydraLogger()
        
    except Exception as e:
        print(f"Unexpected error creating logger: {e}")
        return HydraLogger()

# Usage
logger = create_logger_safely("config/logging.yaml")
```

#### Health Checks
```python
def check_logger_health(logger):
    """Check if logger is working properly."""
    try:
        # Test logging to each layer
        for layer_name in logger.config.layers.keys():
            logger.info(f"Health check for {layer_name}", layer_name)
        
        print("Logger health check passed")
        return True
        
    except Exception as e:
        print(f"Logger health check failed: {e}")
        return False

# Usage
logger = HydraLogger(config)
if check_logger_health(logger):
    print("Logger is ready for production use")
```

### Log Analysis Best Practices

#### Structured Logging
```python
import json
from hydra_logger import HydraLogger

class StructuredLogger:
    """Logger that ensures structured data in logs."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
    
    def log_event(self, layer, level, event_type, **kwargs):
        """Log structured event data."""
        structured_message = {
            "event_type": event_type,
            "data": kwargs
        }
        message = json.dumps(structured_message)
        self.logger.log(level, message, layer)
    
    def log_metric(self, layer, metric_name, value, unit=None):
        """Log performance metrics."""
        metric_data = {
            "metric": metric_name,
            "value": value,
            "unit": unit
        }
        message = json.dumps(metric_data)
        self.logger.info(message, layer)

# Usage
structured_logger = StructuredLogger(config)

# Log structured events
structured_logger.log_event("API", "INFO", "user_login", user_id=123, ip="192.168.1.1")

# Log metrics
structured_logger.log_metric("PERFORMANCE", "response_time", 150, "ms")
```

## Format System: `plain-text` and Color Mode

Hydra-Logger supports the `plain-text` format for human-readable output with color control:

- **`plain-text`**: Human-readable text format with color control via `color_mode`
- **Other formats**: `json`, `csv`, `syslog`, `gelf` (all support color_mode for future colored variants)

**Color Mode** (`color_mode`):
- `auto`: Detects if colors should be used (default)
- `always`: Forces colors on
- `never`: Forces colors off

**Example:**
```python
config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},  # Colored console
                {"type": "file", "format": "plain-text", "color_mode": "never"}      # Plain file
            ]
        }
    }
}
logger = HydraLogger(config=config)
logger.info("Colored console, plain file", "APP")
```

## Available Formats
- `plain-text` - Human-readable text (colored in console if color_mode allows)
- `json` - JSON format (structured)
- `csv` - CSV format (tabular)
- `syslog` - Syslog format (system logging)
- `gelf` - GELF format (Graylog)

## Color Mode Options
- `auto` - Automatic detection (default)
- `always` - Force colors on
- `never` - Force colors off 