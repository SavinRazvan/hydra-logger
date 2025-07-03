# Configuration Guide

This guide covers all configuration options for Hydra-Logger, including file formats, programmatic configuration, and best practices.

## Configuration Methods

Hydra-Logger supports three configuration methods:

1. **Programmatic Configuration** - Define configuration in Python code
2. **YAML Configuration Files** - Use YAML files for configuration
3. **TOML Configuration Files** - Use TOML files for configuration

## Programmatic Configuration

### Basic Configuration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create a simple configuration
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

logger = HydraLogger(config)
```

### Advanced Configuration

```python
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app/main.log",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    level="WARNING"
                )
            ]
        ),
        "DEBUG": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/debug/detailed.log",
                    max_size="5MB",
                    backup_count=3
                )
            ]
        ),
        "ERROR": LogLayer(
            level="ERROR",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/errors/critical.log",
                    max_size="1MB",
                    backup_count=10
                ),
                LogDestination(
                    type="console",
                    level="ERROR"
                )
            ]
        )
    }
)
```

## YAML Configuration Files

### Basic YAML Configuration

Create a file named `hydra_logging.yaml`:

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

### Advanced YAML Configuration

```yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app/main.log
        max_size: 10MB
        backup_count: 5
      - type: console
        level: WARNING
  
  API:
    level: INFO
    destinations:
      - type: file
        path: logs/api/requests.log
        max_size: 10MB
        backup_count: 5
      - type: file
        path: logs/api/errors.log
        max_size: 2MB
        backup_count: 3
      - type: console
        level: ERROR
  
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: logs/security/auth.log
        max_size: 1MB
        backup_count: 10
      - type: console
        level: CRITICAL
  
  DEBUG:
    level: DEBUG
    destinations:
      - type: file
        path: logs/debug/detailed.log
        max_size: 5MB
        backup_count: 3
```

### Using YAML Configuration

```python
from hydra_logger import HydraLogger

# Load from YAML file
logger = HydraLogger.from_config("hydra_logging.yaml")

# Use the logger
logger.info("APP", "Application started")
logger.debug("DEBUG", "Debug information")
logger.error("SECURITY", "Security alert")
```

## TOML Configuration Files

### Basic TOML Configuration

Create a file named `hydra_logging.toml`:

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

### Advanced TOML Configuration

```toml
[layers.APP]
level = "INFO"

[[layers.APP.destinations]]
type = "file"
path = "logs/app/main.log"
max_size = "10MB"
backup_count = 5

[[layers.APP.destinations]]
type = "console"
level = "WARNING"

[layers.API]
level = "INFO"

[[layers.API.destinations]]
type = "file"
path = "logs/api/requests.log"
max_size = "10MB"
backup_count = 5

[[layers.API.destinations]]
type = "file"
path = "logs/api/errors.log"
max_size = "2MB"
backup_count = 3

[[layers.API.destinations]]
type = "console"
level = "ERROR"

[layers.SECURITY]
level = "ERROR"

[[layers.SECURITY.destinations]]
type = "file"
path = "logs/security/auth.log"
max_size = "1MB"
backup_count = 10

[[layers.SECURITY.destinations]]
type = "console"
level = "CRITICAL"
```

### Using TOML Configuration

```python
from hydra_logger import HydraLogger

# Load from TOML file
logger = HydraLogger.from_config("hydra_logging.toml")

# Use the logger
logger.info("APP", "Application started")
logger.debug("DEBUG", "Debug information")
logger.error("SECURITY", "Security alert")
```

## Configuration Options

### Log Levels

Available log levels (in order of severity):

- `DEBUG` - Detailed information for debugging
- `INFO` - General information about program execution
- `WARNING` - Warning messages for potentially problematic situations
- `ERROR` - Error messages for serious problems
- `CRITICAL` - Critical errors that may prevent the program from running

### Destination Types

#### File Destinations

```yaml
- type: file
  path: logs/app.log
  max_size: 10MB
  backup_count: 5
```

**Options:**
- `path` (required): File path for the log file
- `max_size` (optional): Maximum file size before rotation (e.g., "10MB", "1GB")
- `backup_count` (optional): Number of backup files to keep

#### Console Destinations

```yaml
- type: console
  level: WARNING
```

**Options:**
- `level` (optional): Override the layer's log level for console output

### File Size Formats

Supported file size formats:

- `"1B"` - 1 byte
- `"1KB"` - 1 kilobyte
- `"1MB"` - 1 megabyte
- `"1GB"` - 1 gigabyte
- `"1TB"` - 1 terabyte

## Environment Variables

You can use environment variables in your configuration files:

```yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: ${LOG_PATH:-logs/app.log}
        max_size: ${LOG_MAX_SIZE:-10MB}
        backup_count: ${LOG_BACKUP_COUNT:-5}
```

## Best Practices

### 1. Organize by Module or Function

```yaml
layers:
  AUTH:
    level: INFO
    destinations:
      - type: file
        path: logs/auth/security.log
  
  API:
    level: INFO
    destinations:
      - type: file
        path: logs/api/requests.log
  
  DATABASE:
    level: DEBUG
    destinations:
      - type: file
        path: logs/database/queries.log
```

### 2. Separate Error Logs

```yaml
layers:
  APP_ERRORS:
    level: ERROR
    destinations:
      - type: file
        path: logs/errors/app.log
        max_size: 1MB
        backup_count: 10
  
  SECURITY_ERRORS:
    level: ERROR
    destinations:
      - type: file
        path: logs/security/errors.log
        max_size: 1MB
        backup_count: 10
```

### 3. Use Appropriate File Sizes

- **Debug logs**: 5-10MB (frequent writes)
- **Info logs**: 10-50MB (moderate writes)
- **Error logs**: 1-5MB (infrequent writes)
- **Security logs**: 1-2MB (critical, keep longer)

### 4. Console Output for Important Events

```yaml
layers:
  CRITICAL:
    level: ERROR
    destinations:
      - type: file
        path: logs/critical.log
      - type: console
        level: CRITICAL
```

### 5. Development vs Production

**Development Configuration:**
```yaml
layers:
  DEBUG:
    level: DEBUG
    destinations:
      - type: console
      - type: file
        path: logs/debug.log
```

**Production Configuration:**
```yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        max_size: 50MB
        backup_count: 10
```

## Validation

Hydra-Logger validates your configuration and provides helpful error messages for:

- Invalid log levels
- Missing required fields
- Invalid file paths
- Invalid file sizes
- Invalid backup counts

Example validation error:

```python
from pydantic import ValidationError

try:
    config = LoggingConfig(layers={...})
except ValidationError as e:
    print(f"Configuration error: {e}")
```

## Default Configuration

If no configuration is provided, Hydra-Logger uses a default configuration:

```python
default_config = LoggingConfig(
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    level="WARNING"
                )
            ]
        )
    }
)
``` 