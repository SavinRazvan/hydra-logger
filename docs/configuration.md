# Configuration Guide

This comprehensive guide covers all configuration options for Hydra-Logger, including file formats, programmatic configuration, log formats, and best practices for enterprise environments.

## Table of Contents

- [Configuration Methods](#configuration-methods)
- [Programmatic Configuration](#programmatic-configuration)
- [YAML Configuration Files](#yaml-configuration-files)
- [TOML Configuration Files](#toml-configuration-files)
- [Log Formats](#log-formats)
- [Configuration Options](#configuration-options)
- [Best Practices](#best-practices)
- [Environment Variables](#environment-variables)
- [Validation and Error Handling](#validation-and-error-handling)

## Configuration Methods

Hydra-Logger supports multiple configuration methods to suit different deployment scenarios:

1. **Programmatic Configuration** - Define configuration in Python code
2. **YAML Configuration Files** - Use YAML files for configuration
3. **TOML Configuration Files** - Use TOML files for configuration
4. **Environment Variables** - Override configuration with environment variables
5. **Default Configuration** - Use built-in defaults for quick setup

## Programmatic Configuration

### Basic Configuration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create a simple configuration
config = LoggingConfig(
    default_level="INFO",
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file", 
                    path="logs/app.log",
                    format="text"
                ),
                LogDestination(
                    type="console", 
                    level="WARNING",
                    format="json"
                )
            ]
        )
    }
)

logger = HydraLogger(config)
```

### Advanced Configuration with Multiple Formats

```python
config = LoggingConfig(
    default_level="INFO",
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app/main.log",
                    format="text",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    level="WARNING",
                    format="json"
                )
            ]
        ),
        "API": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/api/requests.json",
                    format="json",
                    max_size="50MB",
                    backup_count=3
                ),
                LogDestination(
                    type="file",
                    path="logs/api/errors.log",
                    format="text",
                    max_size="2MB",
                    backup_count=10
                )
            ]
        ),
        "SECURITY": LogLayer(
            level="ERROR",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/security/auth.log",
                    format="syslog",
                    max_size="1MB",
                    backup_count=20
                )
            ]
        ),
        "ANALYTICS": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/analytics/metrics.csv",
                    format="csv"
                )
            ]
        ),
        "MONITORING": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/monitoring/alerts.gelf",
                    format="gelf"
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
default_level: INFO

layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        max_size: 10MB
        backup_count: 5
        format: text
      - type: console
        level: WARNING
        format: json
  
  DEBUG:
    level: DEBUG
    destinations:
      - type: file
        path: logs/debug.log
        max_size: 5MB
        backup_count: 3
        format: text
```

### Advanced YAML Configuration with Multiple Formats

```yaml
default_level: INFO

layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app/main.log
        max_size: 10MB
        backup_count: 5
        format: text
      - type: console
        level: WARNING
        format: json
  
  API:
    level: INFO
    destinations:
      - type: file
        path: logs/api/requests.json
        max_size: 50MB
        backup_count: 5
        format: json
      - type: file
        path: logs/api/errors.log
        max_size: 2MB
        backup_count: 3
        format: text
      - type: console
        level: ERROR
        format: json
  
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: logs/security/auth.log
        max_size: 1MB
        backup_count: 10
        format: syslog
      - type: console
        level: CRITICAL
        format: text
  
  DATABASE:
    level: DEBUG
    destinations:
      - type: file
        path: logs/database/queries.log
        max_size: 5MB
        backup_count: 3
        format: text
  
  PERFORMANCE:
    level: INFO
    destinations:
      - type: file
        path: logs/performance/metrics.csv
        format: csv
  
  MONITORING:
    level: INFO
    destinations:
      - type: file
        path: logs/monitoring/alerts.gelf
        format: gelf
```

### Using YAML Configuration

```python
from hydra_logger import HydraLogger

# Load from YAML file
logger = HydraLogger.from_config("hydra_logging.yaml")

# Use the logger with different layers and formats
logger.info("APP", "Application started")
logger.debug("API", "API request processed")
logger.error("SECURITY", "Authentication failed")
logger.info("PERFORMANCE", "Response time: 150ms")
logger.warning("MONITORING", "High memory usage detected")
```

## TOML Configuration Files

### Basic TOML Configuration

Create a file named `hydra_logging.toml`:

```toml
default_level = "INFO"

[layers.APP]
level = "INFO"
destinations = [
    { type = "file", path = "logs/app.log", max_size = "10MB", backup_count = 5, format = "text" },
    { type = "console", level = "WARNING", format = "json" }
]

[layers.DEBUG]
level = "DEBUG"
destinations = [
    { type = "file", path = "logs/debug.log", max_size = "5MB", backup_count = 3, format = "text" }
]
```

### Advanced TOML Configuration

```toml
default_level = "INFO"

[layers.APP]
level = "INFO"
destinations = [
    { type = "file", path = "logs/app/main.log", max_size = "10MB", backup_count = 5, format = "text" },
    { type = "console", level = "WARNING", format = "json" }
]

[layers.API]
level = "INFO"
destinations = [
    { type = "file", path = "logs/api/requests.json", max_size = "50MB", backup_count = 5, format = "json" },
    { type = "file", path = "logs/api/errors.log", max_size = "2MB", backup_count = 3, format = "text" },
    { type = "console", level = "ERROR", format = "json" }
]

[layers.SECURITY]
level = "ERROR"
destinations = [
    { type = "file", path = "logs/security/auth.log", max_size = "1MB", backup_count = 10, format = "syslog" },
    { type = "console", level = "CRITICAL", format = "text" }
]

[layers.ANALYTICS]
level = "INFO"
destinations = [
    { type = "file", path = "logs/analytics/metrics.csv", format = "csv" }
]
```

## Log Formats

Hydra-Logger supports multiple log formats, each optimized for different use cases:

### Text Format (default)
Traditional plain text logging with timestamps and log levels.

**Use Cases:**
- Human-readable logs
- Traditional logging systems
- Debugging and development
- Simple log analysis

**Configuration:**
```yaml
destinations:
  - type: file
    path: logs/app.log
    format: text
```

**Example Output:**
```
2024-01-15 10:30:45 - hydra.APP - INFO - logger.py:123 - Application started successfully
```

### JSON Format
Structured JSON format for log aggregation and analysis.

**Use Cases:**
- Log aggregation systems (ELK stack, Splunk)
- Machine-readable logs
- Structured data analysis
- API logging

**Configuration:**
```yaml
destinations:
  - type: file
    path: logs/api/requests.json
    format: json
```

**Example Output:**
```json
{"timestamp": "2024-01-15T10:30:45Z", "level": "INFO", "logger": "hydra.APP", "message": "Application started successfully"}
```

### CSV Format
Comma-separated values for analytics and data processing.

**Use Cases:**
- Data analysis and reporting
- Spreadsheet integration
- Performance metrics
- Business intelligence

**Configuration:**
```yaml
destinations:
  - type: file
    path: logs/analytics/metrics.csv
    format: csv
```

**Example Output:**
```
2024-01-15 10:30:45,hydra.APP,INFO,logger.py,123,Application started successfully
```

### Syslog Format
System integration format for enterprise environments.

**Use Cases:**
- System monitoring tools
- Security information and event management (SIEM)
- Enterprise logging infrastructure
- Compliance requirements

**Configuration:**
```yaml
destinations:
  - type: file
    path: logs/security/auth.log
    format: syslog
```

**Example Output:**
```
hydra.APP[12345]: INFO: Application started successfully
```

### GELF Format
Graylog Extended Log Format for centralized logging.

**Use Cases:**
- Graylog integration
- Centralized logging systems
- Microservices logging
- Distributed systems

**Configuration:**
```yaml
destinations:
  - type: file
    path: logs/monitoring/alerts.gelf
    format: gelf
```

**Example Output:**
```
Application started successfully
```

## Configuration Options

### Log Levels
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical error messages for fatal problems

### File Rotation Options
- `max_size`: Maximum file size before rotation (e.g., "10MB", "1GB")
- `backup_count`: Number of backup files to keep

### Destination Types
- `file`: Write logs to a file
- `console`: Write logs to console output

### Format Options
- `text`: Plain text format (default)
- `json`: JSON format
- `csv`: CSV format
- `syslog`: Syslog format
- `gelf`: GELF format

## Best Practices

### Layer Organization
- Use meaningful layer names (e.g., "API", "DB", "SECURITY")
- Group related functionality in the same layer
- Separate concerns into different layers

### Format Selection
- Use **text** format for human-readable logs and debugging
- Use **JSON** format for log aggregation and machine processing
- Use **CSV** format for analytics and data analysis
- Use **syslog** format for system integration and security
- Use **GELF** format for centralized logging systems

### File Management
- Set appropriate file sizes for rotation
- Use different backup counts based on importance
- Implement log file cleanup procedures
- Monitor disk space usage

### Performance Considerations
- Use appropriate log levels to reduce volume
- Consider log level filtering for high-volume layers
- Use efficient formats for high-throughput logging
- Implement log file compression for long-term storage

### Security Considerations
- Set appropriate file permissions
- Use syslog format for security events
- Implement log file encryption if needed
- Monitor log file access and integrity

## Environment Variables

You can override configuration values using environment variables:

```bash
# Set default log level
export HYDRA_DEFAULT_LEVEL=DEBUG

# Set log file path
export HYDRA_LOG_PATH=logs/custom/app.log

# Set file size limit
export HYDRA_MAX_SIZE=20MB
```

## Validation and Error Handling

### Configuration Validation
- All configuration is validated using Pydantic models
- Invalid values are automatically corrected where possible
- Clear error messages for configuration issues
- Type checking for all configuration options

### Error Handling
- Graceful fallback to default configuration
- File permission errors trigger console fallback
- Format errors fall back to text format
- Directory creation failures are handled automatically

### Example Error Handling

```python
from hydra_logger import HydraLogger
from pydantic import ValidationError

try:
    logger = HydraLogger.from_config("config.yaml")
except FileNotFoundError:
    print("Configuration file not found, using defaults")
    logger = HydraLogger()
except ValidationError as e:
    print(f"Configuration validation error: {e}")
    logger = HydraLogger()
except Exception as e:
    print(f"Unexpected error: {e}")
    logger = HydraLogger()
```

## Real-World Configuration Examples

### Web Application Configuration

```yaml
default_level: INFO

layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app/main.log
        format: text
        max_size: 10MB
        backup_count: 5
      - type: console
        level: WARNING
        format: json
  
  API:
    level: DEBUG
    destinations:
      - type: file
        path: logs/api/requests.json
        format: json
        max_size: 50MB
        backup_count: 3
      - type: file
        path: logs/api/errors.log
        format: text
        max_size: 2MB
        backup_count: 10
  
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: logs/security/auth.log
        format: syslog
        max_size: 1MB
        backup_count: 20
  
  PERFORMANCE:
    level: INFO
    destinations:
      - type: file
        path: logs/performance/metrics.csv
        format: csv
```

### Microservices Configuration

```yaml
default_level: INFO

layers:
  SERVICE:
    level: INFO
    destinations:
      - type: file
        path: logs/service.log
        format: text
        max_size: 5MB
        backup_count: 3
      - type: console
        format: json
  
  EXTERNAL:
    level: DEBUG
    destinations:
      - type: file
        path: logs/external.json
        format: json
        max_size: 10MB
        backup_count: 2
  
  MONITORING:
    level: INFO
    destinations:
      - type: file
        path: logs/monitoring.gelf
        format: gelf
```

This configuration guide provides comprehensive coverage of all Hydra-Logger configuration options, helping you create optimal logging setups for any application scenario. 