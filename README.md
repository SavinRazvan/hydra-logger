# 🚀 Hydra-Logger

**The most user-friendly, enterprise-ready Python logging library with modular architecture, zero-configuration, and exceptional performance.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🏆 Performance Highlights

**Comprehensive benchmark results show exceptional performance across all configurations:**

- **🚀 Production/API Service/Background Worker/Microservice/Development/Web App**: 107,980 messages/sec
- **⚡ Bare Metal/Minimal Features**: 20,000 messages/sec (optimized for maximum performance)
- **📊 6.9x performance improvement** from default to optimized configurations
- **💾 Zero memory leaks** across all 13 tested configurations
- **🛡️ Comprehensive error handling** ensures reliable logging

*See [benchmarks/README.md](benchmarks/README.md) for detailed performance analysis.*

## ✨ Features

### 🎯 **Zero Configuration**
```python
from hydra_logger import HydraLogger

# It just works - no configuration needed!
logger = HydraLogger()
logger.info("Application started")
```

### 🏗️ **Flexible Layer System**
```python
# Option 1: Custom layer names (your choice)
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")

# Option 2: Centralized logging (no layers)
logger.info("Application started")
logger.debug("Configuration loaded")
logger.warning("High memory usage detected")
```

### 🚀 **Optimized Configurations**
```python
# High-performance configurations for specific use cases
logger = HydraLogger.for_production()         # 108K messages/sec
logger = HydraLogger.for_api_service()        # 108K messages/sec
logger = HydraLogger.for_background_worker()  # 108K messages/sec
logger = HydraLogger.for_microservice()       # 108K messages/sec
logger = HydraLogger.for_development()        # 108K messages/sec
logger = HydraLogger.for_web_app()           # 108K messages/sec
```

### 🎨 **Format Customization**
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

### 🌈 **Color Mode Control**
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

### ⚡ **Async Logging**
```python
from hydra_logger.async_hydra import AsyncHydraLogger
import asyncio

async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    # High-performance async logging
    await logger.info("ASYNC", "Async message")
    
    await logger.close()

asyncio.run(main())
```

### 🔌 **Plugin System**
```python
from hydra_logger import HydraLogger, register_plugin, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def process_event(self, event):
        # Custom analytics logic
        return {"processed": True}

register_plugin("analytics", CustomAnalytics)
logger = HydraLogger(enable_plugins=True)
```

### 🔒 **Security & Data Protection**
```python
logger = HydraLogger(enable_security=True, enable_sanitization=True)

# Sensitive data automatically masked
logger.info("AUTH", "Login attempt", 
           extra={"email": "user@example.com", "password": "secret123"})
# Output: email=***@***.com password=***
```

### 🌍 **Environment Variable Support**
```bash
export HYDRA_LOG_DATE_FORMAT="%Y-%m-%d"
export HYDRA_LOG_MESSAGE_FORMAT="[{level}] {message}"
export HYDRA_LOG_LEVEL=DEBUG
```

### 🪄 **Custom Magic Config System**
```python
from hydra_logger import HydraLogger, LoggingConfig

@HydraLogger.register_magic("my_app")
def my_app_config():
    return LoggingConfig(layers={"APP": LogLayer(...)})

logger = HydraLogger.for_my_app()
```

- Built-in configs: `for_production()`, `for_development()`, `for_testing()`, `for_microservice()`, `for_web_app()`, `for_api_service()`, `for_background_worker()`, `for_minimal_features()`, `for_bare_metal()`

### 🚀 **Performance Modes**
```python
# Minimal features mode for optimized performance (~20K msgs/sec)
logger = HydraLogger.for_minimal_features()
logger.info("PERFORMANCE", "Fast log message")

# Bare metal mode for maximum performance (~20K msgs/sec)
logger = HydraLogger.for_bare_metal()
logger.info("PERFORMANCE", "Bare metal log message")
```

## 🚀 Quick Start

### **Installation**
```bash
pip install hydra-logger
```

### **Basic Usage**
```python
from hydra_logger import HydraLogger

# Zero configuration - it just works!
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

# Choose the right configuration for your use case
if is_api_service:
    logger = HydraLogger.for_api_service()        # 108K messages/sec
elif is_background_worker:
    logger = HydraLogger.for_background_worker()  # 108K messages/sec
elif is_microservice:
    logger = HydraLogger.for_microservice()       # 108K messages/sec
elif is_web_app:
    logger = HydraLogger.for_web_app()           # 108K messages/sec
else:
    logger = HydraLogger.for_production()         # 108K messages/sec

# Log with confidence - comprehensive error handling ensures delivery
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

### **Async Logging**
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
    
    # Structured logging with context
    await logger.log_structured(
        layer="REQUEST",
        level="INFO",
        message="HTTP request processed",
        correlation_id="req-123",
        context={"user_id": "456", "duration": 0.5}
    )
    
    # Close logger
    await logger.close()

asyncio.run(main())
```

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

# Security events are tracked
logger.security("SECURITY", "Suspicious activity detected")
logger.audit("AUDIT", "User action logged")
logger.compliance("COMPLIANCE", "GDPR compliance check")
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

## 🎯 Performance Goals

**Target: Exceptional Performance Metrics**

- **Throughput**: 15,000+ logs/second
- **Latency**: <0.5ms average
- **Memory**: Optimized memory usage
- **Startup**: Fast initialization
- **Async**: High concurrent performance

## 📚 Documentation

- [Usage Guide](USAGE_GUIDE.md) - Comprehensive usage examples
- [Performance Summary](PERFORMANCE_SUMMARY.md) - Latest benchmark results and performance data
- [Strategic Plan](STRATEGIC_PLAN.md) - Development roadmap
- [Current Status](CURRENT_STATUS.md) - Project status and progress
- [Error Handling](ERROR_HANDLING_SUMMARY.md) - Error handling guide
- [Roadmap](ROADMAP.md) - Future development plans

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Roadmap

- **Week 4**: Performance Optimization (Exceptional Performance)
- **Week 5**: Security Features (Enhanced PII Protection)
- **Week 6**: Custom Magic Config System (✅ COMPLETED)
- **Week 7**: Enhanced Color System (Colored formatters for all formats)
- **Week 8**: Plugin Marketplace (Community plugin repository)
- **Week 9**: Cloud Integrations (Auto-detection for cloud environments)

---

**Hydra-Logger**: The most user-friendly, enterprise-ready Python logging library with modular architecture, zero-configuration, and exceptional performance.

## Performance Recommendations for Async Logging

To ensure world-class performance with Hydra-Logger's async logging system:

1. **Console Logging**
   - Console logs are now written immediately with no buffering or delay. No further tuning is needed for optimal performance.

2. **File Logging**
   - For true async file logging, install the `aiofiles` package in your environment:
     ```bash
     pip install aiofiles
     ```
   - Without `aiofiles`, file logging will fall back to synchronous I/O, which is slower and may block the event loop.

3. **Network, Database, and Cloud Sinks**
   - All network, database, and cloud sinks use high-performance async libraries (`aiohttp`, `asyncpg`, `aioredis`).
   - Ensure these dependencies are installed for non-blocking logging.

4. **No Blocking Calls**
   - The async logging pipeline is fully non-blocking. Avoid adding any synchronous I/O or `time.sleep` in your async code.

5. **Error Handling**
   - All exceptions in async handlers are caught and logged. Logging failures will not crash your application.

6. **Initialization and Shutdown**
   - Handlers start and stop cleanly. No resource leaks or unawaited coroutines.

7. **Performance Monitoring**
   - Optional performance monitoring is available and adds minimal overhead.

**Summary:**
- Hydra-Logger's async logging is production-ready, robust, and highly performant. For best results, always use async-compatible dependencies in production environments.
