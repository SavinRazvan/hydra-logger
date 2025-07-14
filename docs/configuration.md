# Configuration Guide

This guide covers all configuration options for Hydra-Logger, from basic setup to advanced features.

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [Layer Configuration](#layer-configuration)
3. [Destination Types](#destination-types)
4. [Format Options](#format-options)
5. [Color Mode Control](#color-mode-control)
6. [Async Configuration](#async-configuration)
7. [Security Configuration](#security-configuration)
8. [Performance Configuration](#performance-configuration)
9. [Environment Variables](#environment-variables)
10. [Configuration Files](#configuration-files)
11. [Advanced Features](#advanced-features)

## Basic Configuration

### Simple Configuration

```python
from hydra_logger import HydraLogger

# Minimal configuration
config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text"}
            ]
        }
    }
}

logger = HydraLogger(config)
```

### Default Configuration

```python
from hydra_logger import HydraLogger

# Uses default configuration
logger = HydraLogger()
```

## Layer Configuration

### Layer Structure

```python
config = {
    "layers": {
        "LAYER_NAME": {
            "level": "INFO",  # Log level for this layer
            "destinations": [
                # List of destinations
            ]
        }
    }
}
```

### Multiple Layers

```python
config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text"},
                {"type": "file", "path": "logs/app.log", "format": "json"}
            ]
        },
        "API": {
            "level": "DEBUG",
            "destinations": [
                {"type": "file", "path": "logs/api/requests.json", "format": "json"}
            ]
        },
        "ERRORS": {
            "level": "ERROR",
            "destinations": [
                {"type": "file", "path": "logs/errors.log", "format": "plain-text"},
                {"type": "console", "level": "CRITICAL", "format": "gelf"}
            ]
        }
    }
}
```

## Destination Types

### Console Destination

```python
{
    "type": "console",
    "level": "INFO",
    "format": "plain-text",
    "color_mode": "auto"  # auto, always, never
}
```

### File Destination

```python
{
    "type": "file",
    "path": "logs/app.log",
    "level": "INFO",
    "format": "json",
    "max_size": "10MB",
    "backup_count": 5,
    "color_mode": "never"
}
```

### Async HTTP Destination

```python
{
    "type": "async_http",
    "url": "https://logs.example.com/api/logs",
    "level": "INFO",
    "format": "json",
    "retry_count": 3,
    "retry_delay": 1.0,
    "timeout": 30.0,
    "max_connections": 10,
    "credentials": {
        "api_key": "your-api-key"
    }
}
```

### Async Database Destination

```python
{
    "type": "async_database",
    "connection_string": "postgresql://user:pass@localhost/logs",
    "level": "INFO",
    "format": "json",
    "retry_count": 3,
    "retry_delay": 1.0,
    "timeout": 30.0,
    "max_connections": 10
}
```

### Async Queue Destination

```python
{
    "type": "async_queue",
    "queue_url": "redis://localhost:6379/0",
    "level": "INFO",
    "format": "json",
    "retry_count": 3,
    "retry_delay": 1.0,
    "timeout": 30.0,
    "max_connections": 10
}
```

### Async Cloud Destination

```python
{
    "type": "async_cloud",
    "service_type": "aws_cloudwatch",
    "level": "INFO",
    "format": "json",
    "retry_count": 3,
    "retry_delay": 1.0,
    "timeout": 30.0,
    "max_connections": 10,
    "credentials": {
        "access_key": "your-access-key",
        "secret_key": "your-secret-key",
        "region": "us-west-2"
    }
}
```

## Format Options

### Plain Text Format

```python
{
    "type": "console",
    "format": "plain-text",
    "color_mode": "always"
}
```

**Output:**
```
2024-01-15 10:30:45 - INFO - [APP] Application started
```

### JSON Format

```python
{
    "type": "file",
    "path": "logs/app.json",
    "format": "json"
}
```

**Output:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "APP",
  "message": "Application started",
  "filename": "logger.py",
  "lineno": 483
}
```

### CSV Format

```python
{
    "type": "file",
    "path": "logs/metrics.csv",
    "format": "csv"
}
```

**Output:**
```csv
timestamp,level,logger,message,filename,lineno
2024-01-15T10:30:45.123Z,INFO,APP,Application started,logger.py,483
```

### Syslog Format

```python
{
    "type": "file",
    "path": "logs/system.log",
    "format": "syslog"
}
```

**Output:**
```
<134>hostname APP: Application started
```

### GELF Format

```python
{
    "type": "file",
    "path": "logs/graylog.gelf",
    "format": "gelf"
}
```

**Output:**
```json
{
  "version": "1.1",
  "host": "hostname",
  "short_message": "Application started",
  "level": 6,
  "_logger": "APP"
}
```

## Color Mode Control

### Color Mode Options

- `auto`: Automatic detection (default)
- `always`: Force colors on
- `never`: Force colors off

### Per-Destination Color Control

```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {
                    "type": "console",
                    "format": "plain-text",
                    "color_mode": "always"  # Colored console
                },
                {
                    "type": "file",
                    "path": "logs/app.log",
                    "format": "plain-text",
                    "color_mode": "never"   # Plain file
                }
            ]
        }
    }
}
```

## Async Configuration

### Async Logger Setup

```python
from hydra_logger.async_hydra import AsyncHydraLogger

config = {
    "handlers": [
        {
            "type": "file",
            "filename": "logs/async.log",
            "max_queue_size": 1000,
            "memory_threshold": 70.0
        },
        {
            "type": "console",
            "use_colors": True,
            "max_queue_size": 500
        }
    ]
}

logger = AsyncHydraLogger(config)
```

### Async Context Management

```python
from hydra_logger.async_hydra.context import async_context, trace_context

async with AsyncHydraLogger() as logger:
    async with async_context(context_id="request-123"):
        await logger.info("REQUEST", "Processing request")
    
    async with trace_context(trace_id="trace-456"):
        await logger.info("TRACE", "Request traced")
```

### Async Performance Monitoring

```python
from hydra_logger.async_hydra.performance import get_performance_monitor

monitor = get_performance_monitor()
async with monitor.async_timer("operation"):
    await logger.info("PERF", "Operation completed")

stats = monitor.get_async_statistics()
print(f"Average operation time: {stats['average_duration']}ms")
```

## Security Configuration

### Security Features

```python
from hydra_logger import HydraLogger

# Enable security features
logger = HydraLogger(
    enable_security=True,
    enable_sanitization=True
)

# Sensitive data will be automatically masked
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})
# Output: email=***@***.com password=***
```

### Custom Security Patterns

```python
from hydra_logger.data_protection import DataSanitizer

sanitizer = DataSanitizer()
sanitizer.add_pattern("custom_pattern", r"custom_sensitive_data")

# Use in logger
logger = HydraLogger(enable_sanitization=True)
```

### Security Validation

```python
from hydra_logger.data_protection import SecurityValidator

validator = SecurityValidator()
result = validator.validate_input("SELECT * FROM users")

if result["is_safe"]:
    logger.info("SAFE", "Input validated")
else:
    logger.warning("SECURITY", f"Potential threat: {result['threats']}")
```

## Performance Configuration

### Performance Modes

```python
# Minimal features mode for maximum performance
logger = HydraLogger.for_minimal_features()

# Bare metal mode for ultimate performance
logger = HydraLogger.for_bare_metal()

# Production mode with balanced features
logger = HydraLogger.for_production()
```

### Buffer Configuration

```python
logger = HydraLogger(
    buffer_size=8192,      # Buffer size for file handlers
    flush_interval=1.0     # Flush interval in seconds
)
```

### Memory Monitoring

```python
from hydra_logger.async_hydra.core import MemoryMonitor

monitor = MemoryMonitor(max_percent=70.0, check_interval=5.0)

if monitor.check_memory():
    logger.warning("MEMORY", "Memory usage high")
```

## Environment Variables

### Configuration via Environment

```bash
# Set environment variables
export HYDRA_LOG_DATE_FORMAT="%Y-%m-%d %H:%M:%S"
export HYDRA_LOG_MESSAGE_FORMAT="[{level}] {message}"
export HYDRA_LOG_LOGGER_NAME_FORMAT="[{name}]"
export HYDRA_LOG_TIME_FORMAT="%H:%M:%S"
```

### Environment Variable Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `HYDRA_LOG_DATE_FORMAT` | Date format | `%Y-%m-%d` |
| `HYDRA_LOG_TIME_FORMAT` | Time format | `%H:%M:%S` |
| `HYDRA_LOG_LOGGER_NAME_FORMAT` | Logger name format | `[{name}]` |
| `HYDRA_LOG_MESSAGE_FORMAT` | Message format | `{level}: {message}` |

## Configuration Files

### YAML Configuration

**hydra_logging.yaml:**
```yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: console
        format: plain-text
        color_mode: always
      - type: file
        path: logs/app.log
        format: json
        max_size: 10MB
        backup_count: 5
  
  API:
    level: DEBUG
    destinations:
      - type: file
        path: logs/api/requests.json
        format: json
        max_size: 100MB
        backup_count: 2
  
  ERRORS:
    level: ERROR
    destinations:
      - type: file
        path: logs/errors.log
        format: plain-text
      - type: console
        level: CRITICAL
        format: gelf
```

### TOML Configuration

**hydra_logging.toml:**
```toml
[layers.APP]
level = "INFO"
destinations = [
    { type = "console", format = "plain-text", color_mode = "always" },
    { type = "file", path = "logs/app.log", format = "json", max_size = "10MB", backup_count = 5 }
]

[layers.API]
level = "DEBUG"
destinations = [
    { type = "file", path = "logs/api/requests.json", format = "json", max_size = "100MB", backup_count = 2 }
]

[layers.ERRORS]
level = "ERROR"
destinations = [
    { type = "file", path = "logs/errors.log", format = "plain-text" },
    { type = "console", level = "CRITICAL", format = "gelf" }
]
```

### Loading Configuration Files

```python
from hydra_logger import HydraLogger

# Load from YAML
logger = HydraLogger.from_config("hydra_logging.yaml")

# Load from TOML
logger = HydraLogger.from_config("hydra_logging.toml")
```

## Advanced Features

### Data Loss Protection

```python
from hydra_logger.data_protection import DataLossProtection

protection = DataLossProtection(backup_dir=".hydra_backup")
await protection.backup_message("critical log message", "error_queue")

# Restore messages after failure
restored_messages = await protection.restore_messages("error_queue")
```

### Atomic File Operations

```python
from hydra_logger.data_protection import FallbackHandler

handler = FallbackHandler()
handler.safe_write_json(data, "logs/critical.json")
handler.safe_write_csv(records, "logs/data.csv")

# Safe reading with corruption detection
data = handler.safe_read_json("logs/critical.json")
records = handler.safe_read_csv("logs/data.csv")
```

### Corruption Detection

```python
from hydra_logger.data_protection import CorruptionDetector

detector = CorruptionDetector()
is_valid = detector.is_valid_json("logs/data.json")
is_csv_valid = detector.is_valid_csv("logs/data.csv")

# Detect corruption by format
is_corrupted = detector.detect_corruption("logs/data.json", "json")
```

### Plugin Configuration

```python
from hydra_logger import HydraLogger, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        return {"processed": True}
    
    def get_insights(self):
        return {"custom_metric": 42}

logger = HydraLogger(enable_plugins=True)
logger.add_plugin("custom_analytics", CustomAnalytics())
```

### Magic Configurations

```python
from hydra_logger import HydraLogger

# Production configuration
logger = HydraLogger.for_production()

# Development configuration
logger = HydraLogger.for_development()

# Testing configuration
logger = HydraLogger.for_testing()

# Microservice configuration
logger = HydraLogger.for_microservice()

# Web app configuration
logger = HydraLogger.for_web_app()

# API service configuration
logger = HydraLogger.for_api_service()

# Background worker configuration
logger = HydraLogger.for_background_worker()
```

### Custom Magic Configurations

```python
from hydra_logger import HydraLogger

@HydraLogger.register_magic("my_app", "Custom configuration for my app")
def my_app_config():
    return {
        "layers": {
            "APP": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "format": "plain-text"},
                    {"type": "file", "path": "logs/my_app.log", "format": "json"}
                ]
            }
        }
    }

# Use custom magic configuration
logger = HydraLogger.for_custom("my_app")
```

### Error Tracking

```python
from hydra_logger.core.error_handler import get_error_tracker, track_error

error_tracker = get_error_tracker()

# Track custom errors
track_error("custom_error", Exception("Something went wrong"))

# Get error statistics
stats = error_tracker.get_error_stats()
print(f"Total errors: {stats['total_errors']}")
```

### Health Monitoring

```python
from hydra_logger.async_hydra.core import AsyncHealthMonitor

health_monitor = AsyncHealthMonitor(logger)
status = health_monitor.get_health_status()

if status['is_healthy']:
    print("Logger is healthy")
else:
    print(f"Logger issues: {status['issues']}")
```

### Performance Monitoring

```python
from hydra_logger.async_hydra.performance import get_performance_monitor

monitor = get_performance_monitor()
stats = monitor.get_async_statistics()

print(f"Average operation time: {stats['average_duration']}ms")
print(f"Total operations: {stats['total_operations']}")
print(f"Performance alerts: {stats['alerts']}")
```

## Best Practices

### Layer Organization

```python
# Good: Meaningful layer names
config = {
    "layers": {
        "APP": {...},      # Application logs
        "API": {...},      # API request logs
        "DB": {...},       # Database logs
        "SECURITY": {...}, # Security events
        "PERFORMANCE": {...} # Performance metrics
    }
}
```

### Format Selection

```python
# Choose formats based on use case
config = {
    "layers": {
        "DEBUG": {
            "destinations": [
                {"type": "file", "path": "logs/debug.log", "format": "plain-text"}  # Human-readable
            ]
        },
        "ANALYTICS": {
            "destinations": [
                {"type": "file", "path": "logs/analytics.csv", "format": "csv"}  # Data analysis
            ]
        },
        "MONITORING": {
            "destinations": [
                {"type": "file", "path": "logs/monitoring.json", "format": "json"}  # Log aggregation
            ]
        }
    }
}
```

### Security Configuration

```python
# Always enable security for production
logger = HydraLogger(
    enable_security=True,
    enable_sanitization=True
)

# Sensitive data will be auto-masked
logger.info("AUTH", "Login attempt", 
           extra={"user_id": 12345, "password": "secret", "session_token": "abc123"})
```

### Performance Configuration

```python
# Use appropriate configurations for different environments
if environment == "production":
    logger = HydraLogger.for_production()
elif environment == "development":
    logger = HydraLogger.for_development()
elif environment == "testing":
    logger = HydraLogger.for_testing()
```

### Async Best Practices

```python
# Use context managers for async logging
async with AsyncHydraLogger() as logger:
    async with async_context(context_id="request-123"):
        await logger.info("REQUEST", "Processing request")
    
    # Use tracing for distributed systems
    async with trace_context(trace_id="trace-456"):
        await logger.info("TRACE", "Request traced")
```

### Data Protection Best Practices

```python
# Use atomic operations for critical data
from hydra_logger.data_protection import FallbackHandler

handler = FallbackHandler()
handler.safe_write_json(critical_data, "logs/critical.json")

# Use data loss protection for critical logs
from hydra_logger.data_protection import DataLossProtection

protection = DataLossProtection()
await protection.backup_message("critical message", "error_queue")
``` 