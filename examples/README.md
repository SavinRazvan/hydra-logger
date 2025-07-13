# Hydra-Logger Examples

This directory contains examples demonstrating Hydra-Logger's modular architecture and features, organized in a hierarchical structure for easy navigation and learning.

## **Hierarchical Structure**

```
examples/
├── 00_master_runner.py          # Master runner for all examples
├── 01_basics/                   # Basic usage and configuration
│   ├── 01_basic_usage.py        # Zero-configuration, minimal usage
│   ├── 02_layered_usage.py      # Layered logging with config dict
│   └── 03_multiple_destinations.py # Multiple destinations
├── 02_async/                    # Async logging capabilities
│   ├── 01_async_basic.py        # Minimal async usage
│   ├── 02_async_colored_console.py # Async with colored console
│   └── 03_async_file_output.py  # Async file output
├── 03_format/                   # Format customization
│   ├── 01_format_customization.py # Complete format customization
│   └── 02_environment_variables.py # Environment variable config
├── 04_color/                    # Color system and control
│   ├── 01_colored_console.py    # Colored console output
│   └── 02_color_mode_control.py # Color mode control
├── 05_security/                 # Security features
│   └── 01_security_features.py  # PII detection and sanitization
├── 06_plugins/                  # Plugin system
│   └── 01_plugin_basic.py       # Custom analytics plugin
├── 07_performance/              # Performance monitoring
│   └── 01_performance_monitoring.py # Performance metrics
└── 08_magic_configs/            # Custom Magic Config System
    └── 01_basic_magic_configs.py # Magic configs for sync and async
```

## **Quick Start**

### **Run All Examples**
```bash
# List all available examples
python examples/00_master_runner.py list

# Run all examples
python examples/00_master_runner.py run-all

# Run a specific example
python examples/00_master_runner.py run 01_basics 01_basic_usage.py
python examples/00_master_runner.py run 08_magic_configs 01_basic_magic_configs.py
```

### **Run Individual Examples**
```bash
# Basic usage
python examples/01_basics/01_basic_usage.py
python examples/01_basics/02_layered_usage.py
python examples/01_basics/03_multiple_destinations.py

# Async logging
python examples/02_async/01_async_basic.py
python examples/02_async/02_async_colored_console.py
python examples/02_async/03_async_file_output.py

# Format customization
python examples/03_format/01_format_customization.py
python examples/03_format/02_environment_variables.py

# Color system
python examples/04_color/01_colored_console.py
python examples/04_color/02_color_mode_control.py

# Security features
python examples/05_security/01_security_features.py

# Plugin system
python examples/06_plugins/01_plugin_basic.py

# Performance monitoring
python examples/07_performance/01_performance_monitoring.py

# Magic config system
python examples/08_magic_configs/01_basic_magic_configs.py
```

## **Example Categories**

### **01_basics/** - Basic Usage and Configuration
- **01_basic_usage.py**: Zero-configuration, minimal usage of HydraLogger
- **02_layered_usage.py**: Layered logging with configuration dictionary
- **03_multiple_destinations.py**: Logging to multiple destinations with different formats

### **02_async/** - Async Logging Capabilities
- **01_async_basic.py**: Minimal usage of AsyncHydraLogger
- **02_async_colored_console.py**: Async logging with colored console output
- **03_async_file_output.py**: Async logging to files with optimized performance

### **03_format/** - Format Customization
- **01_format_customization.py**: Complete format customization demonstration
- **02_environment_variables.py**: Format customization using environment variables

### **04_color/** - Color System and Control
- **01_colored_console.py**: Colored console output with format customization
- **02_color_mode_control.py**: Color mode control for different destinations

### **05_security/** - Security Features
- **01_security_features.py**: PII detection, data sanitization, and security features

### **06_plugins/** - Plugin System
- **01_plugin_basic.py**: Plugin system with custom analytics plugin

### **07_performance/** - Performance Monitoring
- **01_performance_monitoring.py**: Performance monitoring and metrics collection

### **08_magic_configs/** - Custom Magic Config System
- **01_basic_magic_configs.py**: Custom Magic Config System for sync and async loggers

## **Progressive Learning Path**

### **Level 1: Basics (01_basics/)**
1. **01_basic_usage.py** - Start with zero-configuration
2. **02_layered_usage.py** - Learn layered logging
3. **03_multiple_destinations.py** - Multiple destinations

### **Level 2: Async (02_async/)**
1. **01_async_basic.py** - Basic async logging
2. **02_async_colored_console.py** - Async with colors
3. **03_async_file_output.py** - Async file output

### **Level 3: Format Customization (03_format/)**
1. **01_format_customization.py** - Complete format control
2. **02_environment_variables.py** - Environment-based config

### **Level 4: Color System (04_color/)**
1. **01_colored_console.py** - Colored output
2. **02_color_mode_control.py** - Color mode control

### **Level 5: Advanced Features**
1. **05_security/01_security_features.py** - Security features
2. **06_plugins/01_plugin_basic.py** - Plugin system
3. **07_performance/01_performance_monitoring.py** - Performance monitoring
4. **08_magic_configs/01_basic_magic_configs.py** - Custom Magic Config System

## **Example Features**

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
                {"type": "file", "path": "logs/app.log", "color_mode": "never"}  # Plain
            ]
        }
    }
}
```

### **Async Logging**
```python
from hydra_logger.async_hydra import AsyncHydraLogger

async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    await logger.info("ASYNC", "Async logging")
    await logger.close()
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

### **Custom Magic Config System**
```python
from hydra_logger import HydraLogger

@HydraLogger.register_magic("my_app", description="My application's logging configuration")
def my_app_config():
    return {
        "layers": {
            "APP": {
                "level": "INFO",
                "destinations": [
                    {"type": "console", "format": "plain-text", "color_mode": "always"},
                    {"type": "file", "path": "logs/app.log", "format": "json"}
                ]
            }
        }
    }

# Use the magic config
logger = HydraLogger.for_my_app()
```

### **Security Features**
```python
logger = HydraLogger(enable_security=True, enable_sanitization=True)

# Sensitive data automatically masked
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})
# Output: email=***@***.com password=***
```

## **Performance Features**

**Performance Capabilities**

- **High-Performance Mode**: Optimized for maximum throughput
- **Bare Metal Mode**: Maximum performance optimization
- **Buffered Operations**: Efficient file and network logging
- **Async Capabilities**: Non-blocking concurrent logging
- **Memory Optimization**: Reduced memory footprint
- **Performance Monitoring**: Built-in metrics tracking

## **Output Structure**

Examples create organized output:

```
examples/
├── logs/                        # Application logs
│   ├── app.log                 # Basic application logs
│   ├── debug.log               # Debug information
│   ├── async_app.json          # Async JSON logs
│   ├── async_debug.log         # Async debug logs
│   ├── app_plain.log           # Plain text logs
│   └── debug_plain.log         # Plain debug logs
├── 01_basics/                  # Basic examples
├── 02_async/                   # Async examples
├── 03_format/                  # Format examples
├── 04_color/                   # Color examples
├── 05_security/                # Security examples
├── 06_plugins/                 # Plugin examples
├── 07_performance/             # Performance examples
└── README.md                   # This file
```

## **Best Practices**

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

## **Next Steps**

1. **Start Simple**: Use zero-configuration mode (01_basics/01_basic_usage.py)
2. **Add Layers**: Organize logs by functionality (01_basics/02_layered_usage.py)
3. **Customize Format**: Use format customization for consistency (03_format/)
4. **Control Colors**: Use color_mode for different destinations (04_color/)
5. **Enable Security**: Protect sensitive data (05_security/)
6. **Monitor Performance**: Track logging metrics (07_performance/)
7. **Extend with Plugins**: Add custom functionality (06_plugins/)
8. **Go Async**: Use async logging for high performance (02_async/)
9. **Use Magic Configs**: Create reusable logging configurations (08_magic_configs/)

The modular architecture makes it easy to start simple and progressively add complexity as your needs grow.

---

**Hydra-Logger**: Enterprise-ready Python logging library with modular architecture, zero-configuration, and comprehensive features.
