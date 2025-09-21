# HYDRA-LOGGER

## 🚀 Professional Logging System

A simplified, production-ready logging system built on KISS principles with comprehensive features and zero overhead when disabled.

### 🎯 Core Principles
- **KISS Principle**: Simple, focused core functionality
- **Modular Design**: Essential components with optional extensions
- **Performance First**: Zero overhead when features disabled
- **User Control**: Enable only what you need
- **Clean API**: Intuitive, professional interface

## 📊 Architecture Overview

**Simplified from 100+ files to 48 essential files (52% reduction)**
- **6 Essential Handlers**: Console, File, Rotating, Null, Network
- **6 Essential Formatters**: PlainText, JsonLines, CSV, Syslog, GELF, Logstash
- **6 Core Security Components**: DataRedaction, DataSanitizer, SecurityValidator, DataEncryption, DataHasher, AccessController
- **4 Essential Types**: LogRecord, LogLevel, LogContext, Enums
- **3 Core Utilities**: Text, Time, File

## 🏗️ Architecture

### **Core System Structure**
```
hydra_logger/
├── core/                    # Core functionality (6 modules)
├── loggers/                # Logger implementations (4 modules)
├── handlers/               # Handler implementations (6 modules)
├── formatters/             # Formatter implementations (6 modules)
├── security/               # Security components (6 modules)
├── config/                 # Configuration system (6 modules)
├── types/                  # Type definitions (4 modules)
├── utils/                  # Utility functions (3 modules)
├── factories/              # Factory system (2 modules)
└── __init__.py             # Main package exports
```

### **Key Features**
- **Event-Driven Architecture**: Direct event handling with loose coupling
- **Asynchronous Processing**: Built-in async support with graceful fallback
- **Zero Overhead**: Features disabled by default for maximum performance
- **Professional Standards**: Consistent naming, robust error handling
- **Production Ready**: Comprehensive testing and validation

## 🚀 Quick Start

### Installation
```bash
pip install hydra-logger
```

### Basic Usage
```python
from hydra_logger import create_logger

# Create a logger
logger = create_logger("MyApp")

# Basic logging
logger.info("Application started")
logger.warning("Low memory warning")
logger.error("Database connection failed")

# Structured logging
logger.info("User action", 
    extra={"user_id": 12345, "action": "login"},
    context={"correlation_id": "corr-123"}
)
```

### Advanced Usage
```python
from hydra_logger import create_production_logger, create_async_logger
import asyncio

# Production logger with security features
prod_logger = create_production_logger("sync")

# Async logger with automatic context detection
async_logger = create_async_logger("MyAsyncApp")

# Works in both sync and async contexts
async_logger.info("This works everywhere!")

# In async context
async def main():
    await async_logger.info("Async logging")
```

## 📋 Available Loggers

### **SyncLogger**
- Synchronous logging with immediate output
- Perfect for simple applications
- Zero overhead, maximum performance

### **AsyncLogger**
- Asynchronous logging with queue-based processing
- Automatic sync/async context detection
- Graceful fallback when no event loop available

### **CompositeLogger**
- Combines multiple logger instances
- Perfect for complex applications
- Flexible component management

## 🎨 Formatters

### **PlainTextFormatter**
- Default format: `{timestamp} {level_name} {layer} {message}`
- Customizable format strings
- Clean, readable output

### **JsonLinesFormatter**
- Structured JSON output
- Perfect for log aggregation
- Supports extra and context fields

### **Structured Formatters**
- **CSV**: Comma-separated values for analysis
- **Syslog**: System logging format
- **GELF**: Graylog Extended Log Format
- **Logstash**: Elasticsearch-compatible format

## 🔒 Security Features

### **Data Protection**
- **DataRedaction**: Automatically redact sensitive information
- **DataSanitizer**: Clean data before logging
- **DataEncryption**: Encrypt sensitive log data
- **DataHasher**: Hash sensitive values

### **Access Control**
- **SecurityValidator**: Validate log data
- **AccessController**: Control logging access

## ⚙️ Configuration

### **Configuration Templates**
```python
from hydra_logger import create_default_logger, create_production_logger

# Pre-configured loggers
default_logger = create_default_logger("sync")
prod_logger = create_production_logger("async")
dev_logger = create_development_logger("sync")
custom_logger = create_custom_logger("sync")
```

### **Custom Configuration**
```python
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

config = LoggingConfig(
    default_level="INFO",
    layers={
        "api": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="console", format="colored", use_colors=True),
                LogDestination(type="file", path="api.log", format="json-lines")
            ]
        )
    }
)

logger = create_logger(config, "sync")
```

## 📊 Performance

### **Zero Overhead Design**
- Features disabled by default
- No performance impact when not used
- Smart context detection
- Graceful degradation

### **Professional Defaults**
- Auto-detection of app name, hostname, environment
- Environment-aware timestamps
- Professional tagging and metadata
- Zero configuration required

## 🧪 Testing

### **Comprehensive Testing**
- All loggers tested and verified
- Async/sync context testing
- Error handling validation
- Performance testing completed

### **Quality Assurance**
- Professional naming conventions
- Robust error handling
- Comprehensive documentation
- Production-ready reliability

## 📈 Migration Summary

### **Phase 1-17 Completed**
- **Architecture Simplification**: Reduced from 100+ to 48 files
- **Over-Engineering Removal**: Eliminated 70+ unnecessary components
- **Naming Standardization**: Professional naming conventions throughout
- **API Improvements**: Unified interface for all contexts
- **Error Handling**: Robust error handling and user feedback
- **Performance Optimization**: Zero overhead design with smart defaults
- **Documentation**: Comprehensive, accurate documentation

### **Key Achievements**
- ✅ **52% Complexity Reduction**: From 100+ files to 48 essential files
- ✅ **Zero Data Loss**: AsyncLogger works in all contexts
- ✅ **Professional Standards**: Consistent naming and error handling
- ✅ **Production Ready**: Comprehensive testing and validation
- ✅ **KISS Principles**: Simple, focused, maintainable code

## 📚 Documentation

### **API Reference**
- Complete API documentation
- Usage examples for all components
- Configuration options and defaults
- Best practices and patterns

### **Examples**
- Basic logging examples
- Advanced configuration examples
- Security feature examples
- Performance optimization examples

## 🤝 Contributing

### **Development Guidelines**
- Follow KISS principles
- Maintain professional standards
- Comprehensive testing required
- Clear documentation expected

### **Code Quality**
- Consistent naming conventions
- Robust error handling
- Performance-first design
- User-friendly APIs

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Status

**Production Ready** - The Hydra-Logger system is a professional, production-ready logging solution that follows KISS principles while providing powerful, reliable functionality.

---

*Built with ❤️ following KISS principles for maximum simplicity and reliability.*
