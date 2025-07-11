# Hydra-Logger

**A modular, enterprise-ready Python logging library with zero-configuration, comprehensive sync logging, plugins, and advanced formatting capabilities.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-white.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI Downloads](https://static.pepy.tech/badge/hydra-logger)](https://pepy.tech/projects/hydra-logger)

## Performance Summary

**Benchmark results from comprehensive testing:**

- **Development/Background Worker**: 101,236 messages/sec
- **Production/Microservice/Web App**: 99,248-98,670 messages/sec
- **API Service**: 87,045 messages/sec
- **Zero memory leaks** across all 13 tested configurations
- **6.9x performance improvement** from default to optimized configurations

*See [benchmarks/README.md](benchmarks/README.md) for detailed performance analysis.*

## Core Features

### **Zero Configuration**
```python
from hydra_logger import HydraLogger

# Works immediately without configuration
logger = HydraLogger()
logger.info("Application started")
```

### **Layer-Based Logging**
```python
# Organize logs by functional areas
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")

# Or use centralized logging
logger.info("Application started")
logger.debug("Configuration loaded")
logger.warning("High memory usage detected")
```

### **Optimized Configurations**
```python
# Pre-configured for specific use cases
logger = HydraLogger.for_production()         # 99K messages/sec
logger = HydraLogger.for_development()        # 101K messages/sec
logger = HydraLogger.for_background_worker()  # 101K messages/sec
logger = HydraLogger.for_microservice()       # 99K messages/sec
logger = HydraLogger.for_web_app()           # 98K messages/sec
logger = HydraLogger.for_api_service()        # 87K messages/sec
```

### **Format Customization**
```python
# Complete control over log format
logger = HydraLogger(
    date_format="%Y-%m-%d",
    time_format="%H:%M:%S",
    logger_name_format="[{name}]",
    message_format="{level}: {message}"
)

logger.info("APP", "Custom format message")
# Output: [APP] INFO: Custom format message
```

### **Color Mode Control**
```python
config = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "console", "color_mode": "always"},  # Colored console
                {"type": "file", "path": "logs/app.log", "color_mode": "never"}  # Plain file
            ]
        }
    }
}

logger = HydraLogger(config=config)
```

### **Async Logging (Experimental)**
```python
from hydra_logger.async_hydra import AsyncHydraLogger
import asyncio

async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    await logger.info("ASYNC", "Async message")
    await logger.close()

asyncio.run(main())
```

**Note**: Async logging is currently in development. File writing and some features may not work as expected. For production use, we recommend the sync HydraLogger.

### **Plugin System**
```python
from hydra_logger import HydraLogger, register_plugin, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        # Custom analytics logic
        return {"processed": True}

register_plugin("analytics", CustomAnalytics)
logger = HydraLogger(enable_plugins=True)
```

### **Security & Data Protection**
```python
logger = HydraLogger(enable_security=True, enable_sanitization=True)

# Automatic sensitive data masking
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})
# Output: email=***@***.com password=***
```

### **Environment Variable Support**
```bash
export HYDRA_LOG_DATE_FORMAT="%Y-%m-%d"
export HYDRA_LOG_MESSAGE_FORMAT="[{level}] {message}"
export HYDRA_LOG_LEVEL=DEBUG
```

### **Custom Magic Config System**
```python
from hydra_logger import HydraLogger, LoggingConfig

@HydraLogger.register_magic("my_app")
def my_app_config():
    return LoggingConfig(layers={"APP": LogLayer(...)})

logger = HydraLogger.for_my_app()
```

### **Performance Modes**
```python
# Minimal features mode for optimized performance (~14K msgs/sec)
logger = HydraLogger.for_minimal_features()
logger.info("PERFORMANCE", "Fast log message")

# Bare metal mode for maximum performance (~14K msgs/sec)
logger = HydraLogger.for_bare_metal()
logger.info("PERFORMANCE", "Bare metal log message")
```

## Quick Start

### **Installation**
```bash
pip install hydra-logger
```

### **Basic Usage**
```python
from hydra_logger import HydraLogger

# Zero configuration - works immediately
logger = HydraLogger()

# Centralized logging (no layers)
logger.info("Application started")
logger.debug("Configuration loaded")
logger.warning("High memory usage detected")
logger.error("Authentication failed")

# Or use custom layer names
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")
```

### **High-Performance Usage**
```python
from hydra_logger import HydraLogger

# Choose configuration based on use case
if is_development:
    logger = HydraLogger.for_development()        # 101K messages/sec
elif is_background_worker:
    logger = HydraLogger.for_background_worker()  # 101K messages/sec
elif is_production:
    logger = HydraLogger.for_production()         # 99K messages/sec
elif is_microservice:
    logger = HydraLogger.for_microservice()       # 99K messages/sec
elif is_web_app:
    logger = HydraLogger.for_web_app()           # 98K messages/sec
else:
    logger = HydraLogger.for_api_service()        # 87K messages/sec

logger.info("APP", "Application message")
```

### **Advanced Configuration**
```python
from hydra_logger import HydraLogger

config = {
    "layers": {
        "FRONTEND": {
            "level": "INFO",
            "destinations": [
                {
                    "type": "console",
                    "format": "text",
                    "level": "INFO",
                    "color_mode": "always"
                },
                {
                    "type": "file",
                    "path": "logs/frontend.log",
                    "format": "json",
                    "level": "INFO"
                }
            ]
        },
        "BACKEND": {
            "level": "DEBUG",
            "destinations": [
                {
                    "type": "file",
                    "path": "logs/backend.json",
                    "format": "json"
                }
            ]
        }
    }
}

logger = HydraLogger(config=config)
logger.info("FRONTEND", "User interface updated")
logger.debug("BACKEND", "API endpoint called")
```

### **Async Logging (Experimental)**
```python
from hydra_logger.async_hydra import AsyncHydraLogger
import asyncio

async def main():
    # Create async logger
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    # Log messages asynchronously
    await logger.info("ASYNC", "Async message")
    await logger.error("ERROR", "Async error")
    
    # Close logger
    await logger.close()

asyncio.run(main())
```

**Note**: Async logging is currently in development. For production use, we recommend the sync HydraLogger.

### **Security Features**
```python
from hydra_logger import HydraLogger

# Enable security and sanitization
logger = HydraLogger(
    enable_security=True,
    enable_sanitization=True,
    redact_sensitive=True
)

# Sensitive data is automatically redacted
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})

# Security features are enabled
# Note: Security-specific logging methods are available in the async logger
```

### **Plugin System**
```python
from hydra_logger import HydraLogger, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        # Process log events
        return {"processed": True}
    
    def get_insights(self):
        # Return analytics insights
        return {"total_events": 100}

# Register and use plugin
logger = HydraLogger(enable_plugins=True)
logger.add_plugin("custom_analytics", CustomAnalytics())

# Get plugin insights
insights = logger.get_plugin_insights()
```

### **Magic Configs**
```python
from hydra_logger import HydraLogger

# Use built-in magic configs
logger = HydraLogger.for_production()
logger = HydraLogger.for_development()
logger = HydraLogger.for_testing()

# Create custom magic config
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

## Detailed Features

### **Modular Architecture**
- **Core Module**: Main logging functionality with exceptions and constants
- **Config Module**: Configuration loaders and Pydantic models
- **Async Module**: Async logging system (experimental)
- **Plugin Module**: Extensible plugin architecture with registry and base classes
- **Data Protection**: Security features and fallback mechanisms

### **Format Support**
- **Text Format**: Human-readable with color support
- **Plain Format**: Uncolored text for file output
- **JSON Format**: Structured logging for machine processing
- **CSV Format**: Tabular data for analysis
- **Syslog Format**: System logging compatibility
- **GELF Format**: Graylog integration

### **Color System**
- **Auto Detection**: Automatic color detection for TTY/Jupyter
- **Manual Control**: Force colors on/off per destination
- **Per-Destination**: Different color settings for console vs file
- **Smart Selection**: Intelligent formatter selection based on environment

### **Security Features**
- **PII Detection**: Email, password, API key, credit card, SSN, phone number patterns
- **Automatic Redaction**: Configurable sensitive data masking
- **Data Sanitization**: Input validation and output sanitization
- **Security Validation**: Built-in security checks and validation
- **Thread Safety**: All security operations are thread-safe

### **Performance Optimization**
- **High-Performance Mode**: Disabled expensive features for speed
- **Ultra-Fast Mode**: Maximum performance optimization
- **Buffered Operations**: High-performance file writing
- **Memory Optimization**: Object pooling and efficient data structures
- **Zero-Copy Logging**: Minimized data copying where possible

### **Async Capabilities (Experimental)**
- **AsyncHydraLogger**: Async logging implementation (in development)
- **Async Handlers**: Async-compatible handlers
- **Async Queues**: Message queue system
- **Async Sinks**: HTTP, database, queue, and cloud destinations
- **Async Context**: Context propagation for async applications

### **Plugin Architecture**
- **AnalyticsPlugin**: Custom analytics processing
- **FormatterPlugin**: Custom formatters
- **SecurityPlugin**: Security features
- **Registry System**: Plugin registration and management
- **Lifecycle Management**: Plugin initialization and cleanup

### **Magic Config System**
- **Built-in Configs**: Production, development, testing, microservice, web app, API service, background worker
- **Custom Registration**: `@HydraLogger.register_magic()` decorator
- **Configuration Validation**: Error handling and validation
- **Documentation**: Built-in help and examples

### **Environment Integration**
- **Environment Variables**: All format parameters configurable via environment
- **Auto-Detection**: Automatic environment detection
- **Fallback Chain**: Intelligent layer fallback mechanism
- **Backward Compatibility**: Maintains compatibility with existing code

## Development Plan

### **Completed Features**
- ✅ **Performance Optimization**: Comprehensive benchmarks and optimization
- ✅ **Security Features**: PII detection, data sanitization, and compliance logging
- ✅ **Magic Config System**: Extensible configuration system with built-in presets
- ✅ **Plugin Architecture**: Extensible plugin system with registry and base classes
- ✅ **Format Customization**: Complete control over log formats and color modes

### **In Progress**
- 🔄 **Async Logging**: Complete async implementation with data loss protection
- 🔄 **Enhanced Color System**: Colored formatters for JSON, CSV, and syslog formats
- 🔄 **Smart Formatter Selection**: Intelligent formatter selection based on environment

### **Planned Features**
- 📋 **Plugin Marketplace**: Community plugin repository with built-in integrations
- 📋 **Cloud Integrations**: Auto-detection for AWS, GCP, Azure environments
- 📋 **Framework Integrations**: Django, Flask, FastAPI, and Celery support
- 📋 **Advanced Analytics**: Log analytics and business intelligence integration
- 📋 **Enterprise Features**: Multi-tenant support and role-based access control
- 📋 **Production Enhancements**: Advanced monitoring and enterprise support

### **Future Vision**
- **Community Growth**: Active contributor program and training materials
- **Industry Recognition**: Conference presence and strategic partnerships
- **Enterprise Adoption**: Enterprise deployment and support

## Performance Targets

**Current Performance Metrics:**
- **Throughput**: 101,236 messages/sec (best configuration)
- **Latency**: <0.1ms average
- **Memory**: Zero memory leaks across all configurations
- **Startup**: ~50ms initialization time
- **Async**: In development

## Documentation

- [Usage Guide](USAGE_GUIDE.md) - Comprehensive usage examples
- [Performance Summary](PERFORMANCE_SUMMARY.md) - Latest benchmark results and performance data
- [Strategic Plan](STRATEGIC_PLAN.md) - Development roadmap
- [Current Status](CURRENT_STATUS.md) - Project status and progress
- [Error Handling](ERROR_HANDLING_SUMMARY.md) - Error handling guide
- [Roadmap](ROADMAP.md) - Future development plans

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Hydra-Logger**: A modular, enterprise-ready Python logging library with zero-configuration, comprehensive sync logging, and advanced formatting capabilities.

## Performance Recommendations

To ensure good performance with Hydra-Logger:

1. **Console Logging**
   - Console logs are written immediately with no buffering or delay. No further tuning is needed for good performance.

2. **File Logging**
   - File logging uses high-performance buffered operations with automatic flushing
   - No additional dependencies required for good performance

3. **Async Logging (Experimental)**
   - Async logging is currently in development
   - For production use, we recommend the sync HydraLogger
   - When async logging is stable, it will support non-blocking operations

4. **No Blocking Calls**
   - The sync logging pipeline is fully optimized. Avoid adding any unnecessary I/O operations.

5. **Error Handling**
   - All exceptions in handlers are caught and logged. Logging failures will not crash your application.

6. **Initialization and Shutdown**
   - Handlers start and stop cleanly. No resource leaks or unawaited coroutines.

7. **Performance Monitoring**
   - Optional performance monitoring is available and adds minimal overhead.

**Summary:**
- Hydra-Logger's sync logging is production-ready, robust, and performant. Async logging is in development and should be used with caution in production environments.
