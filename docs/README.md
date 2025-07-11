# Hydra-Logger Documentation

Welcome to the comprehensive documentation for Hydra-Logger, a modular, enterprise-ready Python logging library with zero-configuration and comprehensive features.

## Quick Navigation

### **Getting Started**
- **[Installation & Quick Start](api.md#installation)** - Get up and running in minutes
- **[Basic Usage Examples](examples.md#basic-usage)** - Zero-configuration examples
- **[Configuration Guide](configuration.md)** - Complete configuration reference

### **Core Features**
- **[Format Customization](api.md#format-customization)** - Complete control over log format
- **[Color Mode Control](api.md#color-mode-control)** - Per-destination color control
- **[Plugin System](api.md#plugin-system)** - Extensible plugin architecture
- **[Security Features](security.md)** - PII detection and data protection

### **Advanced Topics**
- **[Migration Guide](migration.md)** - Migrate from other logging libraries
- **[Testing Guide](testing.md)** - Comprehensive testing strategies
- **[Fallbacks & Error Handling](FALLBACKS.md)** - Robust error recovery
- **[Performance Optimization](api.md#performance)** - Performance monitoring

## Architecture Overview

Hydra-Logger uses a modular architecture for flexibility and maintainability:

```
hydra_logger/
├── core/           # Core functionality and main logger
├── config/         # Configuration system with Pydantic models
├── plugins/        # Plugin architecture with registry
├── data_protection/ # Security features and fallback mechanisms
└── __init__.py     # Main API and exports
```

## Key Features

### **Zero Configuration**
```python
from hydra_logger import HydraLogger

# Works immediately without configuration
logger = HydraLogger()
logger.info("APP", "Application started")
```

### **Format Customization**
```python
logger = HydraLogger(
    date_format="%Y-%m-%d",
    time_format="%H:%M:%S",
    logger_name_format="[{name}]",
    message_format="{level}: {message}"
)
```

### **Color Mode Control**
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "console", "color_mode": "always"},  # Colored
                {"type": "file", "color_mode": "never"}       # Plain
            ]
        }
    }
}
```

### **Plugin System**
```python
from hydra_logger import HydraLogger, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        # Custom analytics logic
        return {"processed": True}

logger = HydraLogger(enable_plugins=True)
logger.add_plugin("custom_analytics", CustomAnalytics())
```

### **Security & Data Protection**
```python
logger = HydraLogger(enable_security=True, enable_sanitization=True)

# Sensitive data automatically masked
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})
# Output: email=***@***.com password=***
```

## Performance Metrics

**Current Performance Results:**

- **Development/Background Worker**: 101,236 messages/sec
- **Web Application**: 98,452 messages/sec
- **API Service**: 87,123 messages/sec
- **Zero memory leaks** in extended testing
- **Consistent performance** across different workloads

## Progressive Complexity

### **Level 1: Zero Configuration**
```python
from hydra_logger import HydraLogger
logger = HydraLogger()
logger.info("APP", "Works immediately!")
```

### **Level 2: Basic Customization**
```python
config = {"layers": {"APP": {"level": "INFO", "destinations": [{"type": "console"}]}}}
logger = HydraLogger(config=config)
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
logger = HydraLogger(enable_security=True, enable_sanitization=True)
metrics = logger.get_performance_metrics()
```

### **Level 7: Plugin System**
```python
from hydra_logger import HydraLogger, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        # Custom analytics logic
        return {"processed": True}

logger = HydraLogger(enable_plugins=True)
logger.add_plugin("custom_analytics", CustomAnalytics())
```

## Documentation Structure

### **Core Documentation**
- **[API Reference](api.md)** - Complete API documentation
- **[Configuration Guide](configuration.md)** - Configuration system reference
- **[Examples](examples.md)** - Comprehensive examples and use cases

### **Advanced Topics**
- **[Security Guide](security.md)** - Security features and best practices
- **[Migration Guide](migration.md)** - Migration from other libraries
- **[Testing Guide](testing.md)** - Testing strategies and examples
- **[Fallbacks](FALLBACKS.md)** - Error handling and recovery

### **Development**
- **[Badge Automation](badge-automation.md)** - Development automation
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project

## Best Practices

### **Layer Organization**
```python
# Use descriptive layer names
logger.info("DATABASE", "Query executed")
logger.info("API", "Request received")
logger.info("AUTH", "User authenticated")
logger.info("PERF", "Performance metric")
```

### **Security First**
```python
# Always enable security for production
logger = HydraLogger(enable_security=True, enable_sanitization=True)

# Sensitive data will be auto-masked
logger.info("AUTH", "Login attempt", 
           extra={"user_id": 12345, "password": "secret", "session_token": "abc123"})
```

### **Performance Monitoring**
```python
# Monitor performance in production
logger = HydraLogger()

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

## Environment Variables

```bash
# Basic configuration
export HYDRA_LOG_LEVEL=DEBUG
export HYDRA_LOG_COLOR_ERROR=red
export HYDRA_LOG_LAYER_COLOR=cyan

# Format customization
export HYDRA_LOG_DATE_FORMAT="%Y-%m-%d"
export HYDRA_LOG_TIME_FORMAT="%H:%M:%S"
export HYDRA_LOG_LOGGER_NAME_FORMAT="%(name)s"
export HYDRA_LOG_MESSAGE_FORMAT="%(levelname)s - %(message)s"
```

## Next Steps

1. **Start Simple**: Use zero-configuration mode
2. **Add Layers**: Organize logs by functionality
3. **Customize Format**: Use format customization for consistency
4. **Control Colors**: Use color_mode for different destinations
5. **Enable Security**: Protect sensitive data
6. **Monitor Performance**: Track logging metrics
7. **Extend with Plugins**: Add custom functionality

The modular architecture makes it easy to start simple and progressively add complexity as your needs grow.

---

**Hydra-Logger**: Enterprise-ready Python logging library with modular architecture, zero-configuration, and comprehensive features.

- [Magic Config System](magic_configs.md) — One-line reusable logging setups 