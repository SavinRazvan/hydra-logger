Nice — thanks for the full file-structure dump. I’ve updated the **Architecture** section of your README to exactly reflect what you currently have in reality, using your provided “Complete File Structure Documentation.”
Below is the **complete, ready-to-paste `README.md`** with that architecture section integrated and the rest of the document preserved (quick start, critical TODOs, checklists, etc.). Copy this over your existing README and you’ll be aligned.

---

# HYDRA-LOGGER

## 🚀 Professional Logging System

A dynamic, scalable, event-driven logging system built with KISS (Keep It Simple) principles: modular, zero-overhead when disabled, and extension-based.

---

## 🎯 Core Principles

* **KISS** — simple, maintainable code; avoid over-engineering.
* **Event-Driven (Simplified)** — direct method calls, loose coupling, async-ready.
* **Zero Overhead Extensions** — default disabled; no runtime cost when off.
* **Standardization** — consistent names, file patterns, method signatures, and configuration.

---

## 🏗 Architecture Overview — Current (Reality)

# 📦 Hydra Logger - Complete File Structure Documentation

## 🏗️ Project Overview

**Total Files**: 48 essential files
**Architecture**: Event-driven, modular, scalable
**Design Principles**: KISS, EDA, zero overhead, professional standards

---

## 📂 Core Package Structure

### 📜 `__init__.py` (Main Package)

**Purpose**: Main package exports and public API
**Key Exports**:

* `SyncLogger`, `AsyncLogger`, `CompositeLogger`
* `create_logger`, `create_default_logger`, `create_development_logger`, `create_production_logger`
* `LoggingConfig`, `LogLevel`, `LogRecord`
* All formatters, handlers, and security components

**Architecture**: Centralized exports for clean public API

---

## 📂 Configuration System (`config/`)

### 📜 `__init__.py`

**Purpose**: Configuration system exports
**Key Exports**:

* `LoggingConfig`, `LogLayer`, `OutputTarget`
* `ConfigurationTemplates`, `register_configuration_template`
* `get_configuration_template`, `has_configuration_template`
* `create_default_config`, `create_development_config`, `create_production_config`

**Architecture**: Centralized configuration management

### 📜 `configuration_templates.py`

**Purpose**: Configuration templates system (renamed from magic\_configs)
**Key Classes**:

* `ConfigurationTemplates`: Main template management class
* Built-in templates: `default`, `development`, `production`, `custom`

**Key Methods**:

* `register_template()`: Register new configuration templates
* `get_template()`: Retrieve template by name
* `has_template()`: Check if template exists
* `list_templates()`: List all available templates

**Architecture**: Template-based configuration system

### 📜 `defaults.py`

**Purpose**: Default configuration values and constants
**Key Content**:

* Default log levels and layer configurations
* Standard output targets and formatters
* Default security settings
* Environment-specific defaults

**Architecture**: Centralized default values

### 📜 `models.py`

**Purpose**: Pydantic models for configuration validation
**Key Models**:

* `LoggingConfig`: Main configuration model
* `LogLayer`: Layer-specific configuration
* `OutputTarget`: Output target configuration
* `SecurityConfig`: Security settings
* `ExtensionConfig`: Extension configuration

**Architecture**: Type-safe configuration with validation

---

## 📂 Core System (`core/`)

### 📜 `__init__.py`

**Purpose**: Core system exports
**Key Exports**:

* `BaseLogger`, `LogLevelManager`, `LayerManager`
* `LoggerManager`, `SecurityEngine`
* Core exceptions and constants

**Architecture**: Core functionality exports

### 📜 `base.py`

**Purpose**: Base classes and core functionality
**Key Classes**:

* `BaseLogger`: Abstract base logger class
* `LogLevelManager`: Log level management
* `LayerManager`: Layer management system

**Key Methods**:

* Logger lifecycle management
* Log level validation
* Layer configuration handling

**Architecture**: Foundation classes for all loggers

### 📜 `constants.py`

**Purpose**: Application constants and enums
**Key Content**:

* `CSV_HEADERS`: CSV formatter field order
* Log level constants
* Default configuration values
* System constants

**Architecture**: Centralized constants

### 📜 `exceptions.py`

**Purpose**: Custom exception classes
**Key Exceptions**:

* `HydraLoggerError`: Base exception class
* `ConfigurationError`: Configuration-related errors
* `SecurityError`: Security-related errors
* `ValidationError`: Data validation errors

**Architecture**: Hierarchical exception system

### 📜 `layer_management.py`

**Purpose**: Layer management system (renamed from layer\_manager)
**Key Classes**:

* `LayerManager`: Layer configuration and management
* `LayerConfig`: Individual layer configuration

**Key Methods**:

* `add_layer()`: Add new logging layer
* `get_layer()`: Retrieve layer configuration
* `list_layers()`: List all configured layers
* `remove_layer()`: Remove layer configuration

**Architecture**: Centralized layer management

### 📜 `logger_management.py`

**Purpose**: Logger management system (renamed from logger\_manager)
**Key Classes**:

* `LoggerManager`: Logger lifecycle management
* `LoggerRegistry`: Logger registration system

**Key Methods**:

* `create_logger()`: Create new logger instance
* `get_logger()`: Retrieve existing logger
* `close_logger()`: Close logger instance
* `list_loggers()`: List all active loggers

**Architecture**: Centralized logger management

---

## 📂 Factory System (`factories/`)

### 📜 `__init__.py`

**Purpose**: Factory system exports
**Key Exports**:

* `create_logger`, `create_default_logger`
* `create_development_logger`, `create_production_logger`
* `create_custom_logger`
* `LoggerFactory` class

**Architecture**: Factory pattern implementation

### 📜 `logger_factory.py`

**Purpose**: Logger factory implementation
**Key Classes**:

* `LoggerFactory`: Main factory class
* Factory methods for different logger types

**Key Methods**:

* `create_logger()`: Generic logger creation
* `create_logger_with_template()`: Template-based creation
* `create_default_logger()`: Default configuration logger
* `create_development_logger()`: Development logger
* `create_production_logger()`: Production logger
* `create_custom_logger()`: Custom configuration logger

**Architecture**: Factory pattern with template support

---

## 📂 Formatter System (`formatters/`)

### 📜 `__init__.py`

**Purpose**: Formatter system exports
**Key Exports**:

* `BaseFormatter`, `PlainTextFormatter`
* `JsonLinesFormatter`, `CsvFormatter`
* `SyslogFormatter`, `GelfFormatter`, `LogstashFormatter`
* All formatter classes and utilities

**Architecture**: Centralized formatter exports

### 📜 `base.py`

**Purpose**: Base formatter class and utilities
**Key Classes**:

* `BaseFormatter`: Abstract base formatter class
* `TimestampConfig`: Timestamp configuration
* `TimestampFormat`: Timestamp format options
* `TimestampPrecision`: Timestamp precision options

**Key Methods**:

* `format()`: Abstract format method
* `format_timestamp()`: Timestamp formatting
* `_get_professional_timestamp_config()`: Smart timestamp defaults
* `get_stats()`: Formatter statistics

**Architecture**: Foundation for all formatters

### 📜 `json_formatter.py`

**Purpose**: JSON and JSON Lines formatters
**Key Classes**:

* `JsonLinesFormatter`: JSON Lines format
* `JsonFormatter`: Standard JSON format

**Key Features**:

* Structured data support
* Extra and context field handling
* Professional timestamp defaults
* Environment-aware configuration

**Architecture**: JSON-based structured logging

### 📜 `structured_formatter.py`

**Purpose**: Structured data formatters
**Key Classes**:

* `CsvFormatter`: CSV format for analysis
* `SyslogFormatter`: System logging format
* `GelfFormatter`: Graylog Extended Log Format
* `LogstashFormatter`: Elasticsearch-compatible format

**Key Features**:

* Multiple structured formats
* Professional defaults with auto-detection
* Extra and context field support
* Environment-aware timestamps

**Architecture**: Multi-format structured logging

### 📜 `text_formatter.py`

**Purpose**: Plain text formatters
**Key Classes**:

* `PlainTextFormatter`: Main text formatter
* `FastPlainTextFormatter`: Optimized text formatter (removed)
* `DetailedFormatter`: Detailed text formatter (removed)

**Key Features**:

* Clean text output without brackets/pipes
* Default format: `"{timestamp} {level_name} {layer} {message}"`
* Professional timestamp defaults
* F-string optimization for performance

**Architecture**: Human-readable text logging

---

## 📂 Handler System (`handlers/`)

### 📜 `__init__.py`

**Purpose**: Handler system exports
**Key Exports**:

* `BaseHandler`, `ConsoleHandler`
* `FileHandler`, `AsyncFileHandler`
* `NetworkHandler`, `NullHandler`
* `RotatingFileHandler`

**Architecture**: Centralized handler exports

### 📜 `base.py`

**Purpose**: Base handler class and utilities
**Key Classes**:

* `BaseHandler`: Abstract base handler class
* Handler configuration and management

**Key Methods**:

* `emit()`: Abstract emit method
* `flush()`: Flush handler buffer
* `close()`: Close handler
* `set_formatter()`: Set formatter for handler

**Architecture**: Foundation for all handlers

### 📜 `console.py`

**Purpose**: Console output handler
**Key Classes**:

* `ConsoleHandler`: Console output handler
* `ColoredConsoleHandler`: Colored console output

**Key Features**:

* Console output with optional colors
* Stream selection (stdout/stderr)
* Color configuration
* Performance optimization

**Architecture**: Console-based logging

### 📜 `file.py`

**Purpose**: File output handlers
**Key Classes**:

* `FileHandler`: Synchronous file handler
* `AsyncFileHandler`: Asynchronous file handler

**Key Features**:

* File-based logging
* Async support with graceful fallback
* Performance optimization
* Error handling

**Architecture**: File-based logging

### 📜 `network.py`

**Purpose**: Network output handlers
**Key Classes**:

* `NetworkHandler`: Network logging handler
* `UDPHandler`: UDP network handler
* `TCPHandler`: TCP network handler

**Key Features**:

* Network-based logging
* Multiple protocol support
* Error handling and retry logic
* Performance optimization

**Architecture**: Network-based logging

### 📜 `null.py`

**Purpose**: Null output handler
**Key Classes**:

* `NullHandler`: No-op handler

**Key Features**:

* Silent logging (no output)
* Performance testing
* Debugging and development
* Zero overhead

**Architecture**: Silent logging option

### 📜 `rotating_handler.py`

**Purpose**: Rotating file handler
**Key Classes**:

* `RotatingFileHandler`: File rotation handler

**Key Features**:

* Automatic file rotation
* Size-based rotation
* Time-based rotation
* Log retention management

**Architecture**: Rotating file logging

---

## 📂 Logger System (`loggers/`)

### 📜 `__init__.py`

**Purpose**: Logger system exports
**Key Exports**:

* `SyncLogger`, `AsyncLogger`
* `CompositeLogger`, `BaseLogger`
* All logger classes and utilities

**Architecture**: Centralized logger exports

### 📜 `base.py`

**Purpose**: Base logger class
**Key Classes**:

* `BaseLogger`: Abstract base logger class

**Key Methods**:

* `log()`: Abstract log method
* `debug()`, `info()`, `warning()`, `error()`, `critical()`: Convenience methods
* `close()`: Close logger
* `create_log_record()`: Create log record

**Architecture**: Foundation for all loggers

### 📜 `sync_logger.py`

**Purpose**: Synchronous logger implementation
**Key Classes**:

* `SyncLogger`: Synchronous logging implementation

**Key Features**:

* Synchronous logging operations
* Multiple handler support
* Layer-based logging
* Security integration
* Performance optimization

**Architecture**: Synchronous logging system

### 📜 `async_logger.py`

**Purpose**: Asynchronous logger implementation
**Key Classes**:

* `AsyncLogger`: Asynchronous logging implementation

**Key Features**:

* Asynchronous logging operations
* Automatic async/sync detection
* Graceful fallback to sync mode
* No data loss in any context
* Performance optimization

**Architecture**: Asynchronous logging system

### 📜 `composite_logger.py`

**Purpose**: Composite logger implementation
**Key Classes**:

* `CompositeLogger`: Multiple logger composition

**Key Features**:

* Multiple logger support
* Unified logging interface
* Error handling and fallback
* Performance optimization

**Architecture**: Composite logging system

### 📂 Engines (`loggers/engines/`)

#### 📜 `__init__.py`

**Purpose**: Engine system exports
**Key Exports**:

* `SecurityEngine`: Security processing engine
* Engine utilities and interfaces

**Architecture**: Engine system exports

#### 📜 `security_engine.py`

**Purpose**: Security processing engine
**Key Classes**:

* `SecurityEngine`: Security processing engine

**Key Features**:

* Security component integration
* Data protection processing
* Access control enforcement
* Performance optimization

**Architecture**: Security processing system

---

## 📂 Security System (`security/`)

### 📜 `__init__.py`

**Purpose**: Security system exports
**Key Exports**:

* `DataRedaction`, `DataSanitizer`
* `SecurityValidator`, `DataEncryption`
* `DataHasher`, `AccessController`
* All security components

**Architecture**: Centralized security exports

### 📜 `access_control.py`

**Purpose**: Access control system
**Key Classes**:

* `AccessController`: Access control implementation

**Key Features**:

* Logging access control
* Permission management
* Security enforcement
* Performance optimization

**Architecture**: Access control system

### 📜 `encryption.py`

**Purpose**: Data encryption system
**Key Classes**:

* `DataEncryption`: Data encryption implementation

**Key Features**:

* Data encryption/decryption
* Key management
* Security algorithms
* Performance optimization

**Architecture**: Data encryption system

### 📜 `hasher.py`

**Purpose**: Data hashing system
**Key Classes**:

* `DataHasher`: Data hashing implementation

**Key Features**:

* Data hashing algorithms
* Hash verification
* Security algorithms
* Performance optimization

**Architecture**: Data hashing system

### 📜 `redaction.py`

**Purpose**: Data redaction system
**Key Classes**:

* `DataRedaction`: Data redaction implementation

**Key Features**:

* Sensitive data redaction
* Pattern matching
* Security enforcement
* Performance optimization

**Architecture**: Data redaction system

### 📜 `sanitizer.py`

**Purpose**: Data sanitization system
**Key Classes**:

* `DataSanitizer`: Data sanitization implementation

**Key Features**:

* Data cleaning and sanitization
* Security enforcement
* Pattern matching
* Performance optimization

**Architecture**: Data sanitization system

### 📜 `validator.py`

**Purpose**: Data validation system
**Key Classes**:

* `SecurityValidator`: Data validation implementation

**Key Features**:

* Data validation and verification
* Security enforcement
* Error handling
* Performance optimization

**Architecture**: Data validation system

---

## 📂 Type System (`types/`)

### 📜 `__init__.py`

**Purpose**: Type system exports
**Key Exports**:

* `LogRecord`, `LogLevel`
* `LogContext`, `LogLayer`
* All type definitions and enums

**Architecture**: Centralized type exports

### 📜 `context.py`

**Purpose**: Log context definitions
**Key Classes**:

* `LogContext`: Log context structure
* Context management utilities

**Key Features**:

* Context data structure
* Context validation
* Context management
* Performance optimization

**Architecture**: Context management system

### 📜 `enums.py`

**Purpose**: Enumeration definitions
**Key Enums**:

* `LogLevel`: Log level enumeration
* `HandlerType`: Handler type enumeration
* `FormatterType`: Formatter type enumeration
* `SecurityLevel`: Security level enumeration

**Architecture**: Centralized enumerations

### 📜 `levels.py`

**Purpose**: Log level definitions
**Key Classes**:

* `LogLevel`: Log level class
* `LogLevelManager`: Log level management

**Key Features**:

* Log level definitions
* Level validation
* Level management
* Performance optimization

**Architecture**: Log level management system

### 📜 `records.py`

**Purpose**: Log record definitions
**Key Classes**:

* `LogRecord`: Log record structure
* Record validation and management

**Key Features**:

* Log record structure
* Record validation
* Record management
* Performance optimization

**Architecture**: Log record management system

---

## 📂 Utility System (`utils/`)

### 📜 `__init__.py`

**Purpose**: Utility system exports
**Key Exports**:

* `TextUtility`, `TimeUtility`
* `FileUtility`, `PathUtility`
* `TimeZoneUtility`
* All utility classes and functions

**Architecture**: Centralized utility exports

### 📜 `file_utility.py`

**Purpose**: File utility functions
**Key Classes**:

* `FileUtility`: File operations utility
* `PathUtility`: Path management utility

**Key Features**:

* File operations
* Path management
* Directory handling
* Performance optimization

**Architecture**: File management utilities

### 📜 `text_utility.py`

**Purpose**: Text utility functions
**Key Classes**:

* `TextFormatter`: Text formatting utility

**Key Features**:

* Text formatting
* String manipulation
* Pattern matching
* Performance optimization

**Architecture**: Text processing utilities

### 📜 `time_utility.py`

**Purpose**: Time utility functions
**Key Classes**:

* `TimeUtility`: Time operations utility
* `TimeZoneUtility`: Timezone management utility

**Key Features**:

* Time operations
* Timestamp formatting
* Timezone handling
* Performance optimization

**Architecture**: Time management utilities

---

## 🎯 Architecture Summary

### **Design Principles**

* **KISS**: Keep It Simple, Stupid
* **EDA**: Event-Driven Architecture
* **Zero Overhead**: Features disabled by default
* **Professional Standards**: Consistent naming and error handling

### **Key Features**

* **Modular Design**: Independent, self-contained components
* **Extension System**: Pluggable architecture with user control
* **Dynamic Configuration**: Runtime configuration and component loading
* **Scalable Design**: Horizontal and vertical scaling capabilities
* **Performance Optimized**: Zero-cost when features disabled

### **File Organization**

* **48 Essential Files**: Reduced from 100+ files
* **Consistent Naming**: Professional naming conventions throughout
* **Clear Structure**: Logical organization and separation of concerns
* **Zero Linter Errors**: All code quality issues resolved

### **Production Ready**

* **Comprehensive Testing**: All components tested and verified
* **Robust Error Handling**: User-friendly error messages
* **Professional Documentation**: Complete API documentation
* **Performance Optimized**: \~0.009ms per format operation

---

## 🔌 Extension System (Design Summary)

* **Plug-in / Plug-out** design.
* **Default disabled** — zero cost when not used.
* **Dynamic loading** — runtime enable/disable via config.
* **Sensible defaults** for each extension.
* **Two initial extensions planned**: `data_protection` and `message_formatting`.

Example config snippet:

```python
from hydra_logger.config import LoggingConfig

config = LoggingConfig(
    extensions={
        "data_protection": {
            "enabled": True,
            "redaction_patterns": ["password", "token"],
            "encryption_key": "your-key-here"
        },
        "message_formatting": {
            "enabled": False,
            "custom_templates": True
        }
    }
)
```

---

## 🚀 Quick Start

### Installation

```bash
pip install hydra-logger
```

### Basic usage

```python
from hydra_logger import create_logger

logger = create_logger("MyApp")
logger.info("Application started")
logger.warning("Low memory")
logger.error("Database connection failed")

logger.info("User action",
    extra={"user_id": 12345, "action": "login"},
    context={"correlation_id": "corr-123"}
)
```

### Async usage

```python
from hydra_logger import create_async_logger
import asyncio

async_logger = create_async_logger("MyAsyncApp")

async def main():
    await async_logger.info("Async logging works")
```

---

## 📋 Current Status (Snapshot)

* **Overall Completion**: 70%
* **Core Architecture**: 100% ✅
* **Formatters**: 100% ✅
* **Extension System**: 30% ⚠️
* **Security Migration**: 20% ⚠️
* **Factory Integration**: 40% ⚠️

---

# ✅ CRITICAL TODO CHECKLIST - UPDATED ARCHITECTURE

> **Priority order**: Security Migration → Extension System → Factory Integration → Handler Consistency → Configuration Alignment.

---

## 🚨 IMMEDIATE ACTION REQUIRED (PRIORITY)

### 1) SECURITY ARCHITECTURE MIGRATION (BLOCKER)

* [ ] **Move security components to `extensions/security/`**

  * [ ] Move `security/access_control.py` → `extensions/security/access_control.py`
  * [ ] Move `security/encryption.py` → `extensions/security/encryption.py`
  * [ ] Move `security/hasher.py` → `extensions/security/hasher.py`
  * [ ] Move `security/redaction.py` → `extensions/security/redaction.py`
  * [ ] Move `security/sanitizer.py` → `extensions/security/sanitizer.py`
  * [ ] Move `security/validator.py` → `extensions/security/validator.py`

* [ ] **Update security engine to use extension system**

  * [ ] Modify `loggers/engines/security_engine.py` to consume extension instances instead of importing direct components
  * [ ] Remove direct imports of security component modules from `security_engine.py`
  * [ ] Ensure `security_engine` accepts dependency-injected extension instance(s) and calls extension APIs (redact/sanitize/hash/validate/encrypt)

* [ ] **Fix references and imports**

  * [ ] Update imports in `logger_factory.py` to reference new extension locations (or to ask factory to initialize the extension)
  * [ ] Update all other modules that imported security components directly
  * [ ] Run an import-scan to catch stale references (IDE or `grep`/`rg`)

* [ ] **Create/convert `data_protection` extension**

  * [ ] Implement `extensions/data_protection.py` that wraps/accesses the moved security components
  * [ ] Ensure extension exposes clear API methods: `redact(record)`, `sanitize(record)`, `validate(record)`, `encrypt(record)`, `hash(record)`
  * [ ] Implement extension-level config (redaction patterns, encryption keys, hashing salt, toggle flags)
  * [ ] Add unit tests for each method

---

### 2) EXTENSION SYSTEM IMPLEMENTATION (FOUNDATION)

* [ ] **Extension loader & registry**

  * [ ] Implement `extensions/__init__.py` with `ExtensionLoader` class
  * [ ] `ExtensionLoader` responsibilities:

    * Register available extensions (static discovery + dynamic registration)
    * Load/initialize enabled extensions from config
    * Provide `get_extension(name)` API
    * Graceful error handling for missing/invalid extensions

* [ ] **Base Extension class**

  * [ ] Implement `extensions/base.py` with `Extension` abstract base class
  * [ ] Required interface methods (suggested):

    * `def __init__(self, config: dict) -> None`
    * `def enable(self) -> None`
    * `def disable(self) -> None`
    * `def is_enabled(self) -> bool`
    * `def validate_config(self) -> None`
  * [ ] Provide default config handling and enable/disable semantics

* [ ] **Data protection extension**

  * [ ] Convert security components into a cohesive extension `extensions/data_protection.py`
  * [ ] Maintain compatibility with previous security APIs where possible
  * [ ] Implement configuration schema & validation

* [ ] **Message formatting extension**

  * [ ] Add `extensions/message_formatting.py`
  * [ ] Provide template management, conditional formatting, and safe fast-path when disabled
  * [ ] Integrate with formatters so formatters call into this extension only when enabled

---

### 3) FACTORY INTEGRATION (HOW LOGGERS ARE CREATED)

* [ ] **Update `logger_factory.py`**

  * [ ] Add extension loader initialization when factory bootstraps a logger
  * [ ] Parse extension configs and initialize extension instances
  * [ ] Pass extension instances into created loggers (constructor or `attach_extension()`)

* [ ] **Extension initialization & lifetimes**

  * [ ] Ensure factory handles enabling/disabling extension lifecycles
  * [ ] Support injection into `security_engine` and other pluggable components

* [ ] **Extension defaults**

  * [ ] Add and document sensible default configs for `data_protection` and `message_formatting`
  * [ ] Default state: disabled

---

### 4) HANDLER CONSISTENCY (CLEANUP)

* [ ] **Rename handler files for consistency**

  * [ ] `handlers/console.py` → `handlers/console_handler.py`
  * [ ] `handlers/file.py` → `handlers/file_handler.py`
  * [ ] `handlers/network.py` → `handlers/network_handler.py`
  * [ ] `handlers/null.py` → `handlers/null_handler.py`
  * [ ] (keep `rotating_handler.py` as-is if already named)

* [ ] **Update all imports**

  * [ ] Update `logger_factory.py`, `handler_manager.py`, tests, and docs to use new file names
  * [ ] Run import checks

* [ ] **Interface & naming checks**

  * [ ] Ensure handler classes are consistently named e.g., `ConsoleHandler`, `FileHandler`, `NetworkHandler`, `NullHandler`
  * [ ] Ensure all handlers implement same method signatures: `emit(record)`, `flush()`, `close()`, `configure(config)`

---

### 5) CONFIGURATION ALIGNMENT

* [ ] **Extend config models to support extensions**

  * [ ] Modify `config/models.py` (or equivalent) to include `extensions: Dict[str, ExtensionConfig]`
  * [ ] Add Pydantic (or dataclass) models for `data_protection` and `message_formatting` configs
  * [ ] Add validation rules (required fields, value ranges)

* [ ] **Naming consistency**

  * [ ] Use `data_protection` (not `security`) across code, docs, and examples
  * [ ] Use `message_formatting` (not `formatting` or `custom_formatting`)

* [ ] **Validation & conflict handling**

  * [ ] Validate extension configurations at startup
  * [ ] Detect and report conflicting extension configs (e.g., two extensions trying to encrypt the same fields)

---

## 🔧 REFINEMENTS NEEDED (SECONDARY)

* [ ] Remove leftover EventBus / `LogEvent` references — replace with `LogRecord` and direct calls
* [ ] Standardize extension names and docstrings
* [ ] Update README / API docs with extension usage examples
* [ ] Add unit and integration tests for extension loader, extension enable/disable, and fast-path disabled behavior
* [ ] Ensure zero-cost extension path (early return, no allocations when disabled)
* [ ] Performance and memory optimizations for extension management

---

## 🎯 COMPLETED (KEEP AS REFERENCE)

These items are implemented and **should be left as completed** in history (no action required):

* ✅ Formatter standardization (PlainText, JsonLines, CSV, Syslog, GELF, Logstash)
* ✅ Professional defaults and structured data support (`extra`, `context`)
* ✅ Core architecture cleanup and file reduction (100+ → \~47 files)
* ✅ Naming conventions and import standardization
* ✅ Zero linter errors and comprehensive formatter tests

---

## 📚 Documentation & Examples

* Update extension usage examples in docs after `extensions/` is implemented.
* Examples to add:

  * How to enable `data_protection` and specific patterns
  * How to enable `message_formatting` with templates
  * Factory examples showing extension injection

---

## 🧪 Testing

* Add tests for:

  * Extension loader discovery & initialization
  * Extension enable/disable fast path (zero-cost)
  * Security engine behavior with data protection extension
  * Handler emit path after handler renames
  * Config validation for extension schemas

---

## 🤝 Contributing

* Follow KISS principles and naming standards in this README.
* Add tests for each new change.
* Update README/docs for any behavior or API changes.
* Use `pre-commit` (formatting, linter) and run full test suite locally before PR.

---

## 📄 License

MIT — see `LICENSE`.

---

If you want, I can next:

* Produce a compact `ARCHITECTURE.md` with just the file tree and a short map (useful for reviewers).
* Generate a `TODO.md` that turns the Critical Checklist into per-file actionable subtasks (e.g., exact diffs / `git mv` commands and sample code for `Extension` base).
* Produce a small `rg`/`sed` script you can run to find & update imports referencing `security.*` to `extensions.security.*` (I can craft safe grep/sed commands).
