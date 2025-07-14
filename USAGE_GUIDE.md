# Hydra-Logger Usage Guide

**Complete guide to using Hydra-Logger with all features and capabilities.**

## Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Usage](#basic-usage)
3. [Configuration](#configuration)
4. [Layer System](#layer-system)
5. [Format Customization](#format-customization)
6. [Color System](#color-system)
7. [Async Logging](#async-logging)
8. [Security Features](#security-features)
9. [Plugin System](#plugin-system)
10. [Magic Configs](#magic-configs)
11. [Performance Modes](#performance-modes)
12. [Error Tracking & Recovery](#error-tracking--recovery)
13. [Data Protection & Fallback Systems](#data-protection--fallback-systems)
14. [Advanced Async Features](#advanced-async-features)
15. [Health Monitoring](#health-monitoring)
16. [Advanced Configuration Options](#advanced-configuration-options)
17. [Context Manager Usage](#context-manager-usage)
18. [Advanced Security Features](#advanced-security-features)
19. [File Rotation & Backup](#file-rotation--backup)
20. [Advanced Async Handlers](#advanced-async-handlers)
21. [Environment Variables](#environment-variables)
22. [Best Practices](#best-practices)

---

## Quick Start

### **Installation**
```bash
pip install hydra-logger
```

### **Zero Configuration**
```python
from hydra_logger import HydraLogger

# It just works - no configuration needed!
logger = HydraLogger()
logger.info("Application started")
```

### **Quick Setup with create_logger**
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

### **With Layers**
```python
logger = HydraLogger()
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")
```

---

## Basic Usage

### **Log Levels**
```python
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### **With Layers**
```python
logger.debug("FRONTEND", "Component initialized")
logger.info("BACKEND", "Request processed")
logger.warning("DATABASE", "Slow query detected")
logger.error("AUTH", "Authentication failed")
logger.critical("SYSTEM", "System crash")
```

### **Centralized Logging**
```python
# No layer specified - uses centralized logging
logger.info("Application started")
logger.debug("Configuration loaded")
logger.warning("High memory usage")
logger.error("Connection failed")
```

---

## Configuration

### **Basic Configuration**
```python
from hydra_logger import HydraLogger

config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {
                    "type": "console",
                    "format": "plain-text",
                    "color_mode": "always"
                }
            ]
        }
    }
}

logger = HydraLogger(config=config)
```

### **Multiple Destinations**
```python
config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {
                    "type": "console",
                    "format": "plain-text",
                    "color_mode": "always"
                },
                {
                    "type": "file",
                    "path": "logs/app.log",
                    "format": "json",
                    "color_mode": "never"
                }
            ]
        }
    }
}

logger = HydraLogger(config=config)
```

---

## Layer System

### **Custom Layer Names**
```python
logger = HydraLogger()

# Use any layer names you want
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")
logger.info("PAYMENT", "Payment processed")
logger.info("EMAIL", "Email sent")
```

### **Centralized Logging**
```python
logger = HydraLogger()

# No layer specified - uses centralized logging
logger.info("Application started")
logger.debug("Configuration loaded")
logger.warning("High memory usage")
logger.error("Connection failed")
```

### **Layer Fallback Chain**
The logger uses an intelligent fallback chain:
1. Requested layer
2. DEFAULT layer (user-defined)
3. __CENTRALIZED__ layer (reserved)
4. System logger (final fallback)

---

## Format Customization

### **Constructor Parameters**
```python
logger = HydraLogger(
    date_format="%Y-%m-%d",
    time_format="%H:%M:%S",
    logger_name_format="[{name}]",
    message_format="{level}: {message}"
)

logger.info("APP", "Custom format message")
# Output: [APP] INFO: Custom format message
```

### **Environment Variables**
```bash
export HYDRA_LOG_DATE_FORMAT="%Y-%m-%d"
export HYDRA_LOG_TIME_FORMAT="%H:%M:%S"
export HYDRA_LOG_LOGGER_NAME_FORMAT="[{name}]"
export HYDRA_LOG_MESSAGE_FORMAT="{level}: {message}"
```

### **Available Formats**
- `"plain-text"` - Human-readable text (colored in console if color_mode allows)
- `"json"` - JSON format (structured)
- `"csv"` - CSV format (tabular)
- `"syslog"` - Syslog format (system logging)
- `"gelf"` - GELF format (Graylog)

---

## Color System

### **Color Mode Options**
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {
                    "type": "console",
                    "color_mode": "always"  # Force colors
                },
                {
                    "type": "file",
                    "path": "logs/app.log",
                    "color_mode": "never"   # No colors for files
                },
                {
                    "type": "console",
                    "color_mode": "auto"    # Auto-detect
                }
            ]
        }
    }
}
```

### **Color Mode Values**
- `"auto"` - Automatic detection (default)
- `"always"` - Force colors on
- `"never"` - Force colors off

### **Per-Destination Color Control**
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

---

## Async Logging

### **Basic Async Usage**
```python
from hydra_logger.async_hydra import AsyncHydraLogger
import asyncio

async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    await logger.info("ASYNC", "Async message")
    await logger.error("ERROR", "Async error")
    
    await logger.close()

asyncio.run(main())
```

### **Structured Async Logging**
```python
async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    # Structured logging with context
    await logger.log_structured(
        layer="REQUEST",
        level="INFO",
        message="HTTP request processed",
        correlation_id="req-123",
        context={"user_id": "456", "duration": 0.5}
    )
    
    await logger.close()

asyncio.run(main())
```

### **Async Performance Modes**
```python
# Minimal features async logger
logger = AsyncHydraLogger.for_minimal_features()
await logger.initialize()

# Bare metal async logger
logger = AsyncHydraLogger.for_bare_metal()
await logger.initialize()
```

---

## Security Features

### **Enable Security**
```python
logger = HydraLogger(
    enable_security=True,
    enable_sanitization=True,
    redact_sensitive=True
)
```

### **Automatic PII Redaction**
```python
# Sensitive data is automatically redacted
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})
# Output: email=***@***.com password=***
```

### **Security-Specific Logging**
```python
# Security event logging
logger.security("SECURITY", "Suspicious activity detected")

# Audit trail logging
logger.audit("AUDIT", "User action logged")

# Compliance logging
logger.compliance("COMPLIANCE", "GDPR compliance check")
```

### **PII Detection Patterns**
- Email addresses
- Passwords and API keys
- Credit card numbers
- Social Security Numbers
- Phone numbers
- Tokens and secrets

---

## Plugin System

### **Custom Analytics Plugin**
```python
from hydra_logger import HydraLogger, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        # Process log events
        print(f"Analytics: {event['level']} - {event['message']}")
        return {"processed": True}
    
    def get_insights(self):
        # Return analytics insights
        return {"total_events": 100, "error_rate": 0.05}

# Register and use plugin
logger = HydraLogger(enable_plugins=True)
logger.add_plugin("custom_analytics", CustomAnalytics())

# Get plugin insights
insights = logger.get_plugin_insights()
```

### **Plugin Types**
- **AnalyticsPlugin** - Custom analytics processing
- **FormatterPlugin** - Custom formatters
- **SecurityPlugin** - Security features

---

## Magic Configs

### **Built-in Magic Configs**
```python
# Production-ready configuration
logger = HydraLogger.for_production()

# Development with debug output
logger = HydraLogger.for_development()

# Testing environment
logger = HydraLogger.for_testing()

# Microservice-optimized
logger = HydraLogger.for_microservice()

# Web application
logger = HydraLogger.for_web_app()

# API service
logger = HydraLogger.for_api_service()

# Background worker
logger = HydraLogger.for_background_worker()
```

### **Custom Magic Configs**
```python
from hydra_logger import HydraLogger

@HydraLogger.register_magic("my_app")
def my_app_config():
    return {
        "layers": {
            "APP": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "format": "plain-text"}
                ]
            }
        }
    }

# Use custom magic config
logger = HydraLogger.for_my_app()
```

### **List Available Configs**
```python
configs = HydraLogger.list_magic_configs()
print(configs)
# Output: {'production': 'Production-ready configuration', ...}
```

---

## Performance Modes

### **Minimal Features Mode**
```python
# Optimized for maximum throughput (~14K msgs/sec)
logger = HydraLogger.for_minimal_features()
logger.info("PERFORMANCE", "Fast log message")
```

### **Bare Metal Mode**
```python
# Maximum performance optimization (~14K msgs/sec)
logger = HydraLogger.for_bare_metal()
logger.info("PERFORMANCE", "Bare metal log message")
```

### **High-Performance Configurations**
```python
# Choose the right configuration for your use case
logger = HydraLogger.for_development()        # 101K messages/sec
logger = HydraLogger.for_background_worker()  # 101K messages/sec
logger = HydraLogger.for_production()         # 99K messages/sec
logger = HydraLogger.for_microservice()       # 99K messages/sec
logger = HydraLogger.for_web_app()           # 98K messages/sec
logger = HydraLogger.for_api_service()        # 87K messages/sec
```

### **Performance Monitoring**
```python
logger = HydraLogger(enable_performance_monitoring=True)

# Log some messages
for i in range(1000):
    logger.info("PERF", f"Message {i}")

# Get performance metrics
metrics = logger.get_performance_metrics()
print(metrics)
```

---

## Error Tracking & Recovery

**What users gain:** Comprehensive error monitoring and recovery capabilities

### **Get Error Statistics**
```python
# Get error statistics
error_stats = logger.get_error_stats()
print(f"Total errors: {error_stats['total_errors']}")
print(f"Error types: {error_stats['error_types']}")

# Clear error statistics
logger.clear_error_stats()

# Error tracking is automatic - no setup needed
```

### **Error Context Management**
```python
from hydra_logger.core.error_handler import error_context

# Track errors in specific contexts
with error_context("database", "query_execution"):
    try:
        # Database operation
        pass
    except Exception as e:
        # Error automatically tracked with context
        pass
```

### **Custom Error Tracking**
```python
from hydra_logger.core.error_handler import track_error, track_hydra_error

# Track custom errors
track_error("custom_error", Exception("Custom error"), {"context": "test"})

# Track Hydra-specific errors
from hydra_logger.core.exceptions import HydraLoggerError
track_hydra_error(HydraLoggerError("Hydra error"), "test_component")
```

---

## Data Protection & Fallback Systems

**What users gain:** Data loss protection, atomic writes, corruption detection

### **Data Loss Protection**
```python
from hydra_logger.data_protection import DataLossProtection

# Data loss protection for critical logs
protection = DataLossProtection(backup_dir=".hydra_backup")
await protection.backup_message("critical log message", "error_queue")

# Restore messages after failure
restored_messages = await protection.restore_messages("error_queue")
```

### **Atomic File Operations**
```python
from hydra_logger.data_protection import FallbackHandler

# Thread-safe atomic operations
handler = FallbackHandler()
handler.safe_write_json(data, "logs/data.json")
handler.safe_write_csv(records, "logs/data.csv")

# Safe reading with corruption detection
data = handler.safe_read_json("logs/data.json")
records = handler.safe_read_csv("logs/data.csv")
```

### **Corruption Detection**
```python
from hydra_logger.data_protection import CorruptionDetector

# Detect file corruption
detector = CorruptionDetector()
is_valid = detector.is_valid_json("logs/data.json")
is_csv_valid = detector.is_valid_csv("logs/data.csv")

# Detect corruption by format
is_corrupted = detector.detect_corruption("logs/data.json", "json")
```

---

## Advanced Async Features

**What users gain:** Context management, tracing, performance monitoring

### **Context Management**
```python
from hydra_logger.async_hydra.context import async_context, trace_context

# Context management for distributed tracing
async with async_context(context_id="request-123"):
    await logger.info("REQUEST", "Processing request")

# Tracing with correlation IDs
async with trace_context(trace_id="trace-456"):
    await logger.info("TRACE", "Request traced")
```

### **Performance Monitoring**
```python
from hydra_logger.async_hydra.performance import get_performance_monitor

# Performance monitoring with timing
monitor = get_performance_monitor()
async with monitor.async_timer("operation"):
    await logger.info("PERF", "Operation completed")

# Get performance statistics
stats = monitor.get_async_statistics()
print(f"Average operation time: {stats['average_duration']}ms")
```

### **Memory Monitoring**
```python
from hydra_logger.async_hydra.core.memory_monitor import MemoryMonitor

# Monitor memory usage
memory_monitor = MemoryMonitor(max_percent=70.0)
if memory_monitor.check_memory():
    await logger.warning("MEMORY", "High memory usage detected")

# Get memory statistics
memory_stats = memory_monitor.get_memory_stats()
print(f"Memory usage: {memory_stats['current_percent']}%")
```

---

## Health Monitoring

**What users gain:** Real-time health status, memory monitoring, performance alerts

### **Get Health Status**
```python
# Get comprehensive health status
health = logger.get_health_status()
print(f"Healthy: {health['is_healthy']}")
print(f"Memory usage: {health['memory_percent']}%")
print(f"Uptime: {health['uptime']} seconds")

# Check if logger is healthy
is_healthy = logger.is_healthy()
```

### **Memory Monitoring**
```python
# Get memory statistics
memory_stats = logger.get_memory_statistics()
print(f"Peak memory: {memory_stats['peak_memory_mb']}MB")
print(f"Current memory: {memory_stats['current_memory_mb']}MB")

# Take memory snapshot
snapshot = logger.take_memory_snapshot()
```

### **Performance Health**
```python
# Check performance health
is_perf_healthy = logger.is_performance_healthy()

# Get performance metrics
perf_metrics = logger.get_performance_metrics()
print(f"Total logs: {perf_metrics['total_logs']}")
print(f"Average response time: {perf_metrics['average_response_time']}ms")
```

---

## Advanced Configuration Options

**What users gain:** Fine-grained control over all aspects

### **Advanced Constructor Options**
```python
# Advanced constructor with all options
logger = HydraLogger(
    enable_security=True,
    enable_sanitization=True,
    enable_plugins=True,
    enable_performance_monitoring=True,
    date_format="%Y-%m-%d",
    time_format="%H:%M:%S",
    logger_name_format="[{name}]",
    message_format="{level}: {message}",
    buffer_size=8192,
    flush_interval=1.0,
    minimal_features_mode=False,
    bare_metal_mode=False
)

# Update configuration dynamically
new_config = {"layers": {"NEW": {"level": "DEBUG"}}}
logger.update_config(new_config)
```

### **Plugin Management**
```python
# Add custom plugins
logger.add_plugin("custom_plugin", CustomPlugin())

# Remove plugins
logger.remove_plugin("custom_plugin")

# Get plugin insights
insights = logger.get_plugin_insights()
```

---

## Context Manager Usage

**What users gain:** Automatic cleanup and resource management

### **Automatic Cleanup**
```python
# Automatic cleanup with context manager
with HydraLogger() as logger:
    logger.info("APP", "Application running")
    # Logger automatically closes when exiting context

# Async context manager
async with AsyncHydraLogger() as logger:
    await logger.info("ASYNC", "Async operation")
    # Logger automatically closes when exiting context
```

### **Error Handling in Context**
```python
# Context manager with error handling
try:
    with HydraLogger() as logger:
        logger.info("APP", "Processing data")
        # Simulate error
        raise Exception("Processing error")
except Exception as e:
    # Logger is automatically closed, no resource leaks
    print(f"Error: {e}")
```

---

## Advanced Security Features

**What users gain:** Threat detection, data hashing, security validation

### **Security Validation**
```python
from hydra_logger.data_protection.security import SecurityValidator

# Security validation
validator = SecurityValidator()
result = validator.validate_input("user input")
if result['threats']:
    print(f"Threats detected: {result['threats']}")
```

### **Data Hashing**
```python
from hydra_logger.data_protection.security import DataHasher

# Data hashing for sensitive fields
hasher = DataHasher(algorithm="sha256")
hashed_data = hasher.hash_sensitive_fields(
    {"password": "secret", "email": "user@example.com"},
    ["password", "email"]
)

# Verify hash
is_valid = hasher.verify_hash("secret", hashed_data["password"])
```

### **Custom Security Patterns**
```python
from hydra_logger.data_protection.security import DataSanitizer

# Add custom redaction patterns
sanitizer = DataSanitizer()
sanitizer.add_pattern("custom_id", r"\bID\d{6}\b")

# Remove patterns
sanitizer.remove_pattern("custom_id")
```

---

## File Rotation & Backup

**What users gain:** Automatic file rotation, backup management

### **File Rotation Configuration**
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {
                    "type": "file",
                    "path": "logs/app.log",
                    "max_size": "10MB",
                    "backup_count": 5
                }
            ]
        }
    }
}
```

### **Backup Management**
```python
from hydra_logger.data_protection import BackupManager

# Create backup manager
backup_manager = BackupManager(backup_dir=".hydra_backup")

# Create backup
backup_path = backup_manager.create_backup("logs/app.log")

# Restore from backup
success = backup_manager.restore_from_backup("logs/app.log", backup_path)
```

---

## Advanced Async Handlers

**What users gain:** Composite handlers, parallel execution, error recovery

### **Composite Handler**
```python
from hydra_logger.async_hydra.handlers import AsyncCompositeHandler

# Composite handler with parallel execution
composite = AsyncCompositeHandler(
    handlers=[console_handler, file_handler],
    parallel_execution=True,
    fail_fast=False
)

# Add/remove handlers dynamically
composite.add_handler(new_handler)
composite.remove_handler(old_handler)

# Get handler statistics
stats = composite.get_handler_stats()
```

### **Handler Health Monitoring**
```python
# Get handler health status
health = handler.get_health_status()
print(f"Handler healthy: {health['is_healthy']}")
print(f"Queue size: {health['queue_stats']['current_size']}")

# Check if handler is healthy
is_healthy = handler.is_healthy()
```

---

## Environment Variables

### **Format Customization**
```bash
export HYDRA_LOG_DATE_FORMAT="%Y-%m-%d"
export HYDRA_LOG_TIME_FORMAT="%H:%M:%S"
export HYDRA_LOG_LOGGER_NAME_FORMAT="[{name}]"
export HYDRA_LOG_MESSAGE_FORMAT="{level}: {message}"
```

### **Performance Settings**
```bash
export HYDRA_LOG_ENABLE_PERFORMANCE="true"
export HYDRA_LOG_ENABLE_ANALYTICS="true"
export HYDRA_LOG_REDACT_SENSITIVE="true"
```

### **Color Settings**
```bash
export HYDRA_LOG_COLOR_DEBUG="cyan"
export HYDRA_LOG_COLOR_INFO="green"
export HYDRA_LOG_COLOR_WARNING="yellow"
export HYDRA_LOG_COLOR_ERROR="red"
export HYDRA_LOG_COLOR_CRITICAL="bright_red"
```

---

## Best Practices

### **Layer Organization**
```python
# Use descriptive layer names
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")
logger.info("PAYMENT", "Payment processed")

# Or use centralized logging
logger.info("Application started")
logger.debug("Configuration loaded")
```

### **Security First**
```python
# Always enable security for production
logger = HydraLogger(
    enable_security=True,
    enable_sanitization=True,
    redact_sensitive=True
)

# Sensitive data will be auto-masked
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})
```

### **Performance Monitoring**
```python
# Monitor performance in production
logger = HydraLogger(enable_performance_monitoring=True)

# Log performance metrics
logger.info("PERF", "Memory usage", extra={"memory_mb": 512})
logger.info("PERF", "Response time", extra={"response_time_ms": 150})

# Get metrics
metrics = logger.get_performance_metrics()
```

### **Error Tracking**
```python
# Track errors automatically
logger = HydraLogger()

# Errors are automatically tracked
try:
    # Some operation
    pass
except Exception as e:
    logger.error("ERROR", "Operation failed")
    # Error is automatically tracked with context

# Get error statistics
error_stats = logger.get_error_stats()
print(f"Total errors: {error_stats['total_errors']}")
```

### **Health Monitoring**
```python
# Monitor logger health
logger = HydraLogger()

# Check health status
health = logger.get_health_status()
if not health['is_healthy']:
    logger.warning("HEALTH", "Logger health issues detected")

# Monitor memory usage
memory_stats = logger.get_memory_statistics()
if memory_stats['current_percent'] > 80:
    logger.warning("MEMORY", "High memory usage")
```

### **Format Customization**
```python
# Use environment variables for consistent formatting
import os
os.environ["HYDRA_LOG_DATE_FORMAT"] = "%Y-%m-%d %H:%M:%S"
os.environ["HYDRA_LOG_MESSAGE_FORMAT"] = "[{level}] {message}"

logger = HydraLogger()  # Uses environment variables
```

### **Color Mode Control**
```python
# Use appropriate color modes for different destinations
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "console", "color_mode": "always"},  # Colored console
                {"type": "file", "color_mode": "never"}       # Plain file
            ]
        }
    }
}
```

### **Custom Magic Configs**
```python
# Create reusable configurations for your team
@HydraLogger.register_magic("production_api")
def production_api_config():
    return {
        "layers": {
            "API": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "format": "plain-text"},
                    {"type": "file", "path": "logs/api.log", "format": "json"}
                ]
            },
            "SECURITY": {
                "level": "WARNING",
                "destinations": [
                    {"type": "file", "path": "logs/security.log", "format": "json"}
                ]
            }
        }
    }

# Use across your team
logger = HydraLogger.for_production_api()
```

---

## Progressive Complexity

### **Level 1: Zero Configuration**
```python
from hydra_logger import HydraLogger
logger = HydraLogger()
logger.info("It just works!")
```

### **Level 2: Basic Customization**
```python
config = {"layers": {"APP": {"level": "INFO", "destinations": [{"type": "console"}]}}}
logger = HydraLogger(config=config)
logger.info("APP", "Customized logging")
```

### **Level 3: Multiple Destinations**
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "console", "format": "plain-text"},
                {"type": "file", "path": "logs/app.log", "format": "json"}
            ]
        }
    }
}
logger = HydraLogger(config=config)
```

### **Level 4: Format Customization**
```python
logger = HydraLogger(
    date_format="%Y-%m-%d",
    logger_name_format="[{name}]",
    message_format="{level}: {message}"
)
```

### **Level 5: Color Mode Control**
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "console", "color_mode": "always"},
                {"type": "file", "color_mode": "never"}
            ]
        }
    }
}
```

### **Level 6: Security & Performance**
```python
logger = HydraLogger(
    enable_security=True,
    enable_sanitization=True,
    enable_performance_monitoring=True
)
metrics = logger.get_performance_metrics()
```

### **Level 7: Plugin System**
```python
from hydra_logger import register_plugin, AnalyticsPlugin
class MyAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        pass
register_plugin("analytics", MyAnalytics)
```

### **Level 8: Async & Advanced**
```python
from hydra_logger.async_hydra import AsyncHydraLogger
async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    await logger.info("ASYNC", "High-performance async logging")
    await logger.close()
asyncio.run(main())
```

### **Level 9: Custom Magic Configs**
```python
from hydra_logger import HydraLogger, LoggingConfig
@HydraLogger.register_magic("my_app")
def my_app_config():
    return LoggingConfig(layers={"APP": LogLayer(...)})
logger = HydraLogger.for_my_app()
```

---

## What Users Win by Using These Features

### **1. Reliability & Data Protection**
- **Zero data loss** with backup systems
- **Atomic writes** prevent corruption
- **Automatic recovery** from failures
- **Corruption detection** and repair

### **2. Performance & Monitoring**
- **Real-time health monitoring**
- **Memory leak detection**
- **Performance alerts**
- **Resource usage tracking**

### **3. Security & Compliance**
- **Automatic PII redaction**
- **Threat detection**
- **Data hashing**
- **Audit trail logging**

### **4. Flexibility & Extensibility**
- **Custom plugins** for any functionality
- **Dynamic configuration** updates
- **Context management** for complex workflows
- **Tracing** for distributed systems

### **5. Production Readiness**
- **Error tracking** and statistics
- **Health monitoring** and alerts
- **Performance optimization** modes
- **Resource cleanup** and management

---

## Next Steps

1. **Start Simple**: Use zero-configuration mode
2. **Add Layers**: Organize logs by functionality (optional)
3. **Customize Format**: Use format customization for consistency
4. **Control Colors**: Use color_mode for different destinations
5. **Enable Security**: Protect sensitive data
6. **Monitor Performance**: Track logging metrics
7. **Extend with Plugins**: Add custom functionality
8. **Go Async**: Use async logging for good performance
9. **Use Magic Configs**: Create reusable logging configurations
10. **Add Error Tracking**: Monitor and recover from errors
11. **Enable Health Monitoring**: Track system health
12. **Implement Data Protection**: Ensure data integrity

The modular architecture makes it easy to start simple and progressively add complexity as your needs grow! 