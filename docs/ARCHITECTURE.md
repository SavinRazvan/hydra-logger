# Hydra-Logger Architecture

This document provides a detailed breakdown of the Hydra-Logger package structure, components, and internal architecture.

> **Note**: For workflow and data flow details, see [WORKFLOW_ARCHITECTURE.md](WORKFLOW_ARCHITECTURE.md)

---

## 📂 Core Package Structure

### 📜 `__init__.py` (Main Package)

**Purpose**: Main package exports and public API  
**Key Exports**:
- `SyncLogger`, `AsyncLogger`, `CompositeLogger`
- `create_logger`, `create_default_logger`, `create_development_logger`, `create_production_logger`
- `LoggingConfig`, `LogLevel`, `LogRecord`
- All formatters, handlers, and security components

**Architecture**: Centralized exports for clean public API

---

## 📂 Configuration System (`config/`)

### 📜 `__init__.py`

**Purpose**: Configuration system exports  
**Key Exports**:
- `LoggingConfig`, `LogLayer`, `LogDestination`
- `ConfigurationTemplates`, `register_configuration_template`
- `get_configuration_template`, `has_configuration_template`
- `create_default_config`, `create_development_config`, `create_production_config`

**Architecture**: Centralized configuration management

### 📜 `configuration_templates.py`

**Purpose**: Configuration templates system  
**Key Classes**:
- `ConfigurationTemplates`: Main template management class
- Built-in templates: `default`, `development`, `production`, `custom`

**Key Methods**:
- `register_template()`: Register new configuration templates
- `get_template()`: Retrieve template by name
- `has_template()`: Check if template exists
- `list_templates()`: List all available templates

**Architecture**: Template-based configuration system

### 📜 `defaults.py`

**Purpose**: Default configuration values and constants  
**Key Content**:
- Default log levels and layer configurations
- Standard output targets and formatters
- Default security settings
- Environment-specific defaults

**Architecture**: Centralized default values

### 📜 `models.py`

**Purpose**: Pydantic models for configuration validation  
**Key Models**:
- `LoggingConfig`: Main configuration model
- `LogLayer`: Layer-specific configuration
- `LogDestination`: Destination configuration
- `ExtensionConfig`: Extension configuration

**Architecture**: Type-safe configuration with validation

---

## 📂 Core System (`core/`)

### 📜 `__init__.py`

**Purpose**: Core system exports  
**Key Exports**:
- `BaseLogger`, `LogLevelManager`, `LayerManager`
- `LoggerManager`
- Core exceptions and constants

**Architecture**: Core functionality exports

### 📜 `base.py`

**Purpose**: Base classes and core functionality  
**Key Classes**:
- `BaseLogger`: Abstract base logger class
- `LogLevelManager`: Log level management
- `LayerManager`: Layer management system

**Architecture**: Foundation classes for all loggers

### 📜 `constants.py`

**Purpose**: Application constants and enums  
**Key Content**:
- Color constants (ANSI codes)
- Log level constants
- Default configuration values
- System constants

**Architecture**: Centralized constants

### 📜 `exceptions.py`

**Purpose**: Custom exception classes  
**Key Exceptions**:
- `HydraLoggerError`: Base exception class
- `ConfigurationError`: Configuration-related errors
- `SecurityError`: Security-related errors
- `ValidationError`: Data validation errors

**Architecture**: Hierarchical exception system

### 📜 `layer_management.py`

**Purpose**: Layer management system  
**Key Classes**:
- `LayerManager`: Layer configuration and management
- `LayerConfiguration`: Individual layer configuration

**Key Methods**:
- `setup_layers()`: Setup layers from configuration
- `get_handlers_for_layer()`: Get handlers for a layer with fallback
- `get_layer_threshold()`: Get minimum log level for a layer
- `add_layer()`: Add new logging layer
- `remove_layer()`: Remove layer configuration

**Architecture**: Centralized layer management with fallback logic

### 📜 `logger_management.py`

**Purpose**: Logger management system (Python logging style)  
**Key Classes**:
- `LoggerManager`: Logger lifecycle management

**Key Methods**:
- `getLogger()`: Get or create logger by name (Python logging compatible)
- `hasLogger()`: Check if logger exists
- `removeLogger()`: Remove logger from registry
- `listLoggers()`: List all registered loggers

**Architecture**: Centralized logger management with caching

---

## 📂 Factory System (`factories/`)

### 📜 `__init__.py`

**Purpose**: Factory system exports  
**Key Exports**:
- `create_logger`, `create_default_logger`
- `create_development_logger`, `create_production_logger`
- `create_custom_logger`
- `LoggerFactory` class

**Architecture**: Factory pattern implementation

### 📜 `logger_factory.py`

**Purpose**: Logger factory implementation  
**Key Classes**:
- `LoggerFactory`: Main factory class

**Key Methods**:
- `create_logger()`: Generic logger creation
- `create_logger_with_template()`: Template-based creation
- `create_default_logger()`: Default configuration logger
- `create_development_logger()`: Development logger
- `create_production_logger()`: Production logger

**Architecture**: Factory pattern with template support

---

## 📂 Formatter System (`formatters/`)

### 📜 `__init__.py`

**Purpose**: Formatter system exports  
**Key Exports**:
- `BaseFormatter`, `PlainTextFormatter`
- `ColoredFormatter`, `JsonLinesFormatter`
- `CsvFormatter`, `SyslogFormatter`, `GelfFormatter`, `LogstashFormatter`
- `get_formatter()`: Factory function

**Architecture**: Centralized formatter exports

### 📜 `base.py`

**Purpose**: Base formatter class  
**Key Classes**:
- `BaseFormatter`: Abstract base formatter class

**Key Methods**:
- `format()`: Abstract format method
- `format_timestamp()`: Timestamp formatting

**Architecture**: Foundation for all formatters

### 📜 `text_formatter.py`

**Purpose**: Plain text formatters  
**Key Classes**:
- `PlainTextFormatter`: Main text formatter

**Key Features**:
- Clean text output
- Default format: `"{timestamp} {level_name} {layer} {message}"`
- Timestamp formatting support

**Architecture**: Human-readable text logging

### 📜 `colored_formatter.py`

**Purpose**: Colored console formatter  
**Key Classes**:
- `ColoredFormatter`: Colored text formatter (extends PlainTextFormatter)

**Key Features**:
- ANSI color codes for log levels and layers
- Zero overhead when `use_colors=False`
- Extends PlainTextFormatter

**Architecture**: Color-enhanced text logging

### 📜 `json_formatter.py`

**Purpose**: JSON and JSON Lines formatters  
**Key Classes**:
- `JsonLinesFormatter`: JSON Lines format (one JSON per line)

**Key Features**:
- Structured data support
- Pre-compiled JSON encoder for performance
- Extra and context field handling

**Architecture**: JSON-based structured logging

### 📜 `structured_formatter.py`

**Purpose**: Structured data formatters  
**Key Classes**:
- `CsvFormatter`: CSV format
- `SyslogFormatter`: System logging format
- `GelfFormatter`: Graylog Extended Log Format
- `LogstashFormatter`: Elasticsearch-compatible format

**Architecture**: Multi-format structured logging

---

## 📂 Handler System (`handlers/`)

### 📜 `__init__.py`

**Purpose**: Handler system exports  
**Key Exports**:
- `BaseHandler`, `SyncConsoleHandler`, `AsyncConsoleHandler`
- `FileHandler`, `SyncFileHandler`, `AsyncFileHandler`
- `NullHandler`, `RotatingFileHandler`
- Network handlers (HTTP, WebSocket, Socket)

**Architecture**: Centralized handler exports

### 📜 `base_handler.py`

**Purpose**: Base handler class  
**Key Classes**:
- `BaseHandler`: Abstract base handler class

**Key Methods**:
- `emit()`: Abstract emit method
- `handle()`: Handle log record (check level and emit)
- `setFormatter()`: Set formatter for handler
- `isEnabledFor()`: Check if handler is enabled for level

**Architecture**: Foundation for all handlers

### 📜 `console_handler.py`

**Purpose**: Console output handlers  
**Key Classes**:
- `SyncConsoleHandler`: Synchronous console output with buffering
- `AsyncConsoleHandler`: Asynchronous console output

**Key Features**:
- Buffer-based batching (default: 5000 messages, 0.5s flush)
- Color support (console only)
- Stream selection (stdout/stderr)
- Lazy formatter initialization

**Architecture**: Console logging with performance optimization

### 📜 `file_handler.py`

**Purpose**: File output handlers  
**Key Classes**:
- `SyncFileHandler`: Synchronous file handler with buffering
- `AsyncFileHandler`: Asynchronous file handler
- `FileHandler`: Unified interface

**Key Features**:
- Buffer-based batching (default: 50000 messages, 5.0s flush)
- Automatic directory creation
- File rotation support
- Persistent file handles (async)

**Architecture**: File logging with high-performance buffering

### 📜 `network_handler.py`

**Purpose**: Network output handlers  
**Key Classes**:
- `HTTPHandler`: HTTP/HTTPS logging
- `WebSocketHandler`: WebSocket logging
- `SocketHandler`: TCP socket logging
- `DatagramHandler`: UDP logging

**Architecture**: Network-based logging

### 📜 `null_handler.py`

**Purpose**: Null output handler  
**Key Classes**:
- `NullHandler`: No-op handler

**Key Features**:
- Silent logging (no output)
- Performance testing
- Zero overhead

**Architecture**: Silent logging option

### 📜 `rotating_handler.py`

**Purpose**: Rotating file handler  
**Key Classes**:
- `RotatingFileHandler`: File rotation handler

**Key Features**:
- Automatic file rotation
- Size-based and time-based rotation
- Log retention management

**Architecture**: Rotating file logging

---

## 📂 Logger System (`loggers/`)

### 📜 `__init__.py`

**Purpose**: Logger system exports  
**Key Exports**:
- `SyncLogger`, `AsyncLogger`
- `CompositeLogger`, `CompositeAsyncLogger`
- `BaseLogger`

**Architecture**: Centralized logger exports

### 📜 `base.py`

**Purpose**: Base logger class  
**Key Classes**:
- `BaseLogger`: Abstract base logger class

**Key Methods**:
- `log()`: Abstract log method
- `debug()`, `info()`, `warning()`, `error()`, `critical()`: Convenience methods
- `create_log_record()`: Create log record with performance profiles
- `close()`: Close logger

**Architecture**: Foundation for all loggers

### 📜 `sync_logger.py`

**Purpose**: Synchronous logger implementation  
**Key Classes**:
- `SyncLogger`: Synchronous logging implementation

**Key Features**:
- Synchronous logging operations
- Multi-layer support with handler caching
- Data protection integration
- Performance optimization with caching
- Context manager support for automatic cleanup

**Architecture**: Synchronous logging system

### 📜 `async_logger.py`

**Purpose**: Asynchronous logger implementation  
**Key Classes**:
- `AsyncLogger`: Asynchronous logging implementation

**Key Features**:
- Queue-based async processing
- Concurrency control with semaphores
- Overflow queue for burst traffic
- Background worker tasks
- Context manager support for automatic cleanup

**Architecture**: Asynchronous logging with queue-based processing

### 📜 `composite_logger.py`

**Purpose**: Composite logger implementation  
**Key Classes**:
- `CompositeLogger`: Multiple logger composition (sync)
- `CompositeAsyncLogger`: Multiple logger composition (async)

**Key Features**:
- Multiple logger component support
- Unified logging interface
- Batch processing optimization
- Error handling and fallback

**Architecture**: Composite pattern for complex logging scenarios

---

## 📂 Extension System (`extensions/`)

### 📜 `__init__.py`

**Purpose**: Extension system exports  
**Key Exports**:
- `ExtensionManager`, `ExtensionBase`
- `SecurityExtension`, `FormattingExtension`, `PerformanceExtension`

**Architecture**: Centralized extension exports

### 📜 `extension_base.py`

**Purpose**: Extension base classes  
**Key Classes**:
- `ExtensionBase`: Abstract base extension class
- `SecurityExtension`: Security extension base
- `FormattingExtension`: Formatting extension base
- `PerformanceExtension`: Performance extension base

**Architecture**: Foundation for all extensions

### 📜 `extension_manager.py`

**Purpose**: Extension management system  
**Key Classes**:
- `ExtensionManager`: Extension lifecycle management

**Key Methods**:
- `create_extension()`: Create extension by type
- `enable_extension()`: Enable extension
- `disable_extension()`: Disable extension
- `process_data()`: Process data through enabled extensions

**Architecture**: Centralized extension management

### 📂 Security Extensions (`extensions/security/`)

### 📜 `data_redaction.py`

**Purpose**: Data redaction extension  
**Key Classes**:
- `DataRedactionExtension`: Data redaction implementation

**Key Features**:
- PII detection and redaction
- Pattern-based redaction
- Configurable redaction patterns
- Zero overhead when disabled

**Architecture**: Security-focused data protection

---

## 📂 Type System (`types/`)

### 📜 `__init__.py`

**Purpose**: Type system exports  
**Key Exports**:
- `LogRecord`, `LogLevel`
- `LogContext`, `ContextType`
- All type definitions and enums

**Architecture**: Centralized type exports

### 📜 `records.py`

**Purpose**: Log record definitions  
**Key Classes**:
- `LogRecord`: Log record dataclass (frozen, immutable)
- `RecordCreationStrategy`: Strategy pattern for record creation
- `LogRecordFactory`: Factory for record creation

**Key Features**:
- Performance profiles (minimal, context, convenient)
- Field order optimization
- Immutable design for thread safety

**Architecture**: Log record management with performance optimization

### 📜 `levels.py`

**Purpose**: Log level definitions  
**Key Classes**:
- `LogLevel`: Log level constants
- `LogLevelManager`: Log level management

**Key Features**:
- Standard log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Level conversion and validation
- Caching for performance

**Architecture**: Log level management system

### 📜 `context.py`

**Purpose**: Log context definitions  
**Key Classes**:
- `LogContext`: Log context container
- `CallerInfo`: Caller information
- `SystemInfo`: System information

**Architecture**: Context management system

### 📜 `enums.py`

**Purpose**: Enumeration definitions  
**Key Enums**:
- `ContextType`: Context type enumeration
- `TimeUnit`: Time unit enumeration

**Architecture**: Centralized enumerations

---

## 📂 Utility System (`utils/`)

### 📜 `__init__.py`

**Purpose**: Utility system exports  
**Key Exports**:
- `TextUtility`, `TimeUtility`
- `FileUtility`
- All utility classes and functions

**Architecture**: Centralized utility exports

### 📜 `file_utility.py`

**Purpose**: File utility functions  
**Key Classes**:
- File operation utilities

**Key Features**:
- File operations
- Directory handling
- Path management

**Architecture**: File management utilities

### 📜 `text_utility.py`

**Purpose**: Text utility functions  
**Key Classes**:
- Text processing utilities

**Key Features**:
- Text formatting
- String manipulation
- Pattern matching

**Architecture**: Text processing utilities

### 📜 `time_utility.py`

**Purpose**: Time utility functions  
**Key Classes**:
- `TimeUtility`: Time operations utility
- `TimestampConfig`: Timestamp configuration

**Key Features**:
- Time operations
- Timestamp formatting
- Timezone handling

**Architecture**: Time management utilities

### 📜 `system_detector.py`

**Purpose**: System detection utilities  
**Key Features**:
- Platform detection
- Optimal buffer configuration
- System-specific optimizations

**Architecture**: System-aware optimization

### 📜 `error_logger.py`

**Purpose**: Safe error logging  
**Key Classes**:
- `SafeErrorLogger`: Error logging without recursion

**Architecture**: Safe error handling

---

## 🎯 Architecture Summary

### Design Principles

* **KISS**: Keep It Simple, Stupid
* **Event-Oriented**: Direct method calls, loose coupling
* **Zero Overhead**: Features disabled by default
* **Consistent Standards**: Consistent naming and error handling

### Key Features

* **Modular Design**: Independent, self-contained components
* **Extension System**: Pluggable architecture with user control
* **Dynamic Configuration**: Runtime configuration and component loading
* **Scalable Design**: Horizontal and vertical scaling capabilities
* **Performance Optimized**: Zero-cost when features disabled

### File Organization

* **49 Python Files**: Core package files
* **Consistent Naming**: Consistent naming conventions throughout
* **Clear Structure**: Logical organization and separation of concerns

### Component Relationships

```
Logger (Sync/Async/Composite)
    ↓
LayerManager (route to layer)
    ↓
Handler (check level, format, write)
    ↓
Formatter (internal to handler)
    ↓
Destination (console/file/network)
```

---

## 📚 Related Documentation

- **[WORKFLOW_ARCHITECTURE.md](WORKFLOW_ARCHITECTURE.md)** - Complete workflow and data flow
- **[README.md](../README.md)** - Quick start and overview
- **[PERFORMANCE.md](PERFORMANCE.md)** - Performance benchmarks and optimizations
