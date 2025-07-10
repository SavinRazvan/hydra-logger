# 🚀 Hydra-Logger Usage Guide

**Complete guide to using Hydra-Logger with all features and capabilities.**

## 📋 Table of Contents

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
12. [Environment Variables](#environment-variables)
13. [Best Practices](#best-practices)

---

## 🚀 Quick Start

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

### **With Layers**
```python
logger = HydraLogger()
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")
```

---

## 📝 Basic Usage

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

## ⚙️ Configuration

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
                    "format": "text",
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
                    "format": "text",
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

## 🏗️ Layer System

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

## 🎨 Format Customization

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
- `"text"` - Human-readable text (colored in console)
- `"plain"` - Plain text (no color, best for files)
- `"json"` - JSON format (structured)
- `"csv"` - CSV format (tabular)
- `"syslog"` - Syslog format (system logging)
- `"gelf"` - GELF format (Graylog)

---

## 🌈 Color System

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
                    "format": "text",
                    "color_mode": "always"  # Colored console
                },
                {
                    "type": "file",
                    "path": "logs/app.log",
                    "format": "plain",
                    "color_mode": "never"   # Plain file
                }
            ]
        }
    }
}
```

---

## ⚡ Async Logging

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
# High-performance async logger
logger = AsyncHydraLogger.for_high_performance()
await logger.initialize()

# Ultra-fast async logger
logger = AsyncHydraLogger.for_ultra_fast()
await logger.initialize()
```

---

## 🔒 Security Features

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

## 🔌 Plugin System

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

## 🪄 Magic Configs

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
                    {"type": "console", "format": "text"}
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

## 🚀 Performance Modes

### **Minimal Features Mode**
```python
# Optimized for maximum throughput (~14K msgs/sec)
logger = HydraLogger.for_minimal_features()
logger.info("PERFORMANCE", "Fast log message")
```

### **Bare Metal Mode**
```python
# Extreme performance optimization (~14K msgs/sec)
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

## 🌍 Environment Variables

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

## 🎯 Best Practices

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
                    {"type": "console", "format": "text"},
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

## 🚀 Progressive Complexity

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
                {"type": "console", "format": "text"},
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

## 🎯 Next Steps

1. **Start Simple**: Use zero-configuration mode
2. **Add Layers**: Organize logs by functionality (optional)
3. **Customize Format**: Use format customization for consistency
4. **Control Colors**: Use color_mode for different destinations
5. **Enable Security**: Protect sensitive data
6. **Monitor Performance**: Track logging metrics
7. **Extend with Plugins**: Add custom functionality
8. **Go Async**: Use async logging for high performance
9. **Use Magic Configs**: Create reusable logging configurations

The modular architecture makes it easy to start simple and progressively add complexity as your needs grow! 