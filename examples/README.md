# Hydra-Logger Examples

This directory contains examples demonstrating Hydra-Logger's modular architecture and features, organized in a hierarchical structure for easy navigation and learning.

## **Hierarchical Structure**

```
examples/
├── 00_master_runner.py          # Master runner for all examples
├── 01_basics/                   # Basic usage and configuration
│   ├── 01_basic_usage.py        # Zero-configuration, minimal usage
│   ├── 02_layered_usage.py      # Layered logging with config dict
│   ├── 03_multiple_destinations.py # Multiple destinations
│   ├── 04_multi_layer_same_file.py # Multiple layers to same file
│   └── 05_mixed_formats.py      # Mixed formats in same configuration
├── 02_async/                    # Async logging capabilities
│   ├── 01_async_basic.py        # Minimal async usage
│   ├── 02_async_colored_console.py # Async with colored console
│   ├── 03_async_file_output.py  # Async file output
│   ├── 04_async_structured_logging.py # Structured async logging
│   ├── 05_async_convenience_methods.py # Async convenience methods
│   ├── 06_async_performance_features.py # Async performance features
│   ├── 07_async_reliability_features.py # Async reliability features
│   └── 08_async_comprehensive_example.py # Comprehensive async example
├── 03_format/                   # Format customization
│   ├── 01_format_customization.py # Complete format customization
│   ├── 02_environment_variables.py # Environment variable config
│   ├── 03_csv_format.py         # CSV format logging
│   ├── 04_syslog_format.py      # Syslog format logging
│   └── 05_gelf_format.py        # GELF format logging
├── 04_color/                    # Color system and control
│   ├── 01_colored_console.py    # Colored console output
│   └── 02_color_mode_control.py # Color mode control
├── 05_security/                 # Security features
│   └── 01_security_features.py  # PII detection and sanitization
├── 06_plugins/                  # Plugin system
│   └── 01_plugin_basic.py       # Custom analytics plugin
├── 07_performance/              # Performance monitoring
│   └── 01_performance_monitoring.py # Performance metrics
├── 08_magic_configs/            # Custom Magic Config System
│   └── 01_basic_magic_configs.py # Magic configs for sync and async
├── 09_error_handling/           # Error handling and recovery
│   └── 01_comprehensive_error_handling.py # Comprehensive error handling
└── 10_advanced_multi_layer/     # Advanced multi-layer scenarios
    ├── README.md                # Advanced multi-layer documentation
    ├── 01_advanced_multi_layer_demo.py # Advanced multi-layer demo
    └── 02_log_analysis_demo.py  # Log analysis and processing demo
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
python examples/01_basics/04_multi_layer_same_file.py
python examples/01_basics/05_mixed_formats.py

# Async logging
python examples/02_async/01_async_basic.py
python examples/02_async/02_async_colored_console.py
python examples/02_async/03_async_file_output.py
python examples/02_async/04_async_structured_logging.py
python examples/02_async/05_async_convenience_methods.py
python examples/02_async/06_async_performance_features.py
python examples/02_async/07_async_reliability_features.py
python examples/02_async/08_async_comprehensive_example.py

# Format customization
python examples/03_format/01_format_customization.py
python examples/03_format/02_environment_variables.py
python examples/03_format/03_csv_format.py
python examples/03_format/04_syslog_format.py
python examples/03_format/05_gelf_format.py

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

# Error handling
python examples/09_error_handling/01_comprehensive_error_handling.py

# Advanced multi-layer
python examples/10_advanced_multi_layer/01_advanced_multi_layer_demo.py
python examples/10_advanced_multi_layer/02_log_analysis_demo.py
```

## **Example Categories**

### **01_basics/** - Basic Usage and Configuration
- **01_basic_usage.py**: Zero-configuration, minimal usage of HydraLogger
- **02_layered_usage.py**: Layered logging with configuration dictionary
- **03_multiple_destinations.py**: Logging to multiple destinations with different formats
- **04_multi_layer_same_file.py**: Multiple layers writing to the same file
- **05_mixed_formats.py**: Mixed formats (JSON, plain-text) in the same configuration

### **02_async/** - Async Logging Capabilities
- **01_async_basic.py**: Minimal usage of AsyncHydraLogger
- **02_async_colored_console.py**: Async logging with colored console output
- **03_async_file_output.py**: Async logging to files with optimized performance
- **04_async_structured_logging.py**: Structured async logging with context and metadata
- **05_async_convenience_methods.py**: Async convenience methods and shortcuts
- **06_async_performance_features.py**: Async performance monitoring and optimization
- **07_async_reliability_features.py**: Async reliability features including flush, shutdown, and error handling
- **08_async_comprehensive_example.py**: Comprehensive async logging example with all features

### **03_format/** - Format Customization
- **01_format_customization.py**: Complete format customization demonstration
- **02_environment_variables.py**: Format customization using environment variables
- **03_csv_format.py**: CSV format logging for data analysis
- **04_syslog_format.py**: Syslog format for system integration
- **05_gelf_format.py**: GELF format for Graylog integration

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

### **09_error_handling/** - Error Handling and Recovery
- **01_comprehensive_error_handling.py**: Comprehensive error handling, recovery, and resilience features

### **10_advanced_multi_layer/** - Advanced Multi-Layer Scenarios
- **01_advanced_multi_layer_demo.py**: Advanced multi-layer logging scenarios
- **02_log_analysis_demo.py**: Log analysis and processing demonstration
- **README.md**: Detailed documentation for advanced multi-layer features

## **Progressive Learning Path**

### **Level 1: Basics (01_basics/)**
1. **01_basic_usage.py** - Start with zero-configuration
2. **02_layered_usage.py** - Learn layered logging
3. **03_multiple_destinations.py** - Multiple destinations
4. **04_multi_layer_same_file.py** - Multiple layers to same file
5. **05_mixed_formats.py** - Mixed formats in configuration

### **Level 2: Async (02_async/)**
1. **01_async_basic.py** - Basic async logging
2. **02_async_colored_console.py** - Async with colors
3. **03_async_file_output.py** - Async file output
4. **04_async_structured_logging.py** - Structured async logging
5. **05_async_convenience_methods.py** - Async convenience methods
6. **06_async_performance_features.py** - Async performance features
7. **07_async_reliability_features.py** - Async reliability features
8. **08_async_comprehensive_example.py** - Comprehensive async example

### **Level 3: Format Customization (03_format/)**
1. **01_format_customization.py** - Complete format control
2. **02_environment_variables.py** - Environment-based config
3. **03_csv_format.py** - CSV format for data analysis
4. **04_syslog_format.py** - Syslog format for system integration
5. **05_gelf_format.py** - GELF format for Graylog integration

### **Level 4: Color System (04_color/)**
1. **01_colored_console.py** - Colored output
2. **02_color_mode_control.py** - Color mode control

### **Level 5: Advanced Features**
1. **05_security/01_security_features.py** - Security features
2. **06_plugins/01_plugin_basic.py** - Plugin system
3. **07_performance/01_performance_monitoring.py** - Performance monitoring
4. **08_magic_configs/01_basic_magic_configs.py** - Custom Magic Config System
5. **09_error_handling/01_comprehensive_error_handling.py** - Error handling and recovery
6. **10_advanced_multi_layer/** - Advanced multi-layer scenarios

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
    await logger.aclose()
```

### **Structured Async Logging**
```python
from hydra_logger.async_hydra import AsyncHydraLogger

async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    # Structured logging with context
    await logger.info("API", "Request processed", 
                     extra={"user_id": 123, "response_time": 150})
    await logger.aclose()
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

### **Error Handling and Recovery**
```python
from hydra_logger import HydraLogger

logger = HydraLogger(enable_error_tracking=True)

try:
    # Your application code
    result = risky_operation()
except Exception as e:
    logger.error("APP", "Operation failed", extra={"error": str(e)})
    # Automatic error tracking and recovery
```

### **Advanced Multi-Layer Logging**
```python
from hydra_logger import HydraLogger

config = {
    "layers": {
        "SYSTEM": {"level": "INFO", "destinations": [{"type": "console"}]},
        "DATABASE": {"level": "DEBUG", "destinations": [{"type": "file", "path": "logs/db.log"}]},
        "API": {"level": "WARNING", "destinations": [{"type": "file", "path": "logs/api.log"}]},
        "SECURITY": {"level": "ERROR", "destinations": [{"type": "file", "path": "logs/security.log"}]}
    }
}

logger = HydraLogger(config)
```

## **Performance Features**

**Performance Capabilities**

- **High-Performance Mode**: Optimized for throughput (~14K messages/sec)
- **Bare Metal Mode**: Maximum performance optimization (~14K messages/sec)
- **Buffered Operations**: Efficient file and network logging
- **Async Capabilities**: Non-blocking concurrent logging
- **Memory Optimization**: Reduced memory footprint
- **Performance Monitoring**: Built-in metrics tracking
- **Reliability Features**: Flush, shutdown, and error recovery
- **Structured Logging**: Context-aware logging with metadata

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
│   ├── debug_plain.log         # Plain debug logs
│   ├── db.log                  # Database logs
│   ├── api.log                 # API logs
│   ├── security.log            # Security logs
│   └── analysis.log            # Log analysis output
├── 01_basics/                  # Basic examples
├── 02_async/                   # Async examples
├── 03_format/                  # Format examples
├── 04_color/                   # Color examples
├── 05_security/                # Security examples
├── 06_plugins/                 # Plugin examples
├── 07_performance/             # Performance examples
├── 08_magic_configs/           # Magic config examples
├── 09_error_handling/          # Error handling examples
├── 10_advanced_multi_layer/    # Advanced multi-layer examples
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
logger.info("SECURITY", "Access attempt")
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

### **Async Reliability**
```python
from hydra_logger.async_hydra import AsyncHydraLogger

async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    try:
        await logger.info("APP", "Processing started")
        # Your async operations
        await logger.info("APP", "Processing completed")
    finally:
        # Ensure proper cleanup
        await logger.aclose()
```

### **Error Handling**
```python
from hydra_logger import HydraLogger

logger = HydraLogger(enable_error_tracking=True)

try:
    # Risky operation
    result = complex_operation()
except Exception as e:
    # Automatic error tracking
    logger.error("APP", "Operation failed", extra={"error": str(e)})
    # Error recovery logic
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
10. **Handle Errors**: Implement comprehensive error handling (09_error_handling/)
11. **Advanced Scenarios**: Explore advanced multi-layer logging (10_advanced_multi_layer/)

The modular architecture makes it easy to start simple and progressively add complexity as your needs grow.

---

**Hydra-Logger**: Python logging library with modular architecture, zero-configuration, and comprehensive features.
