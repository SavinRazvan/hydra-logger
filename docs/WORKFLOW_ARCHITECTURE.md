# Hydra-Logger Workflow Architecture

This document provides a detailed workflow description of the Hydra-Logger system architecture, designed to help understand the system flow and create architectural diagrams.

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Logger Types and Flows](#logger-types-and-flows)
5. [Layer Management System](#layer-management-system)
6. [Handler System](#handler-system)
7. [Formatter System](#formatter-system)
8. [Extension System](#extension-system)
9. [Configuration System](#configuration-system)
10. [Factory Pattern](#factory-pattern)
11. [Performance Optimizations](#performance-optimizations)

---

## System Overview

Hydra-Logger is a multi-headed, event-driven logging system with the following key characteristics:

- **Modular Architecture**: Pluggable components (handlers, formatters, extensions)
- **Multi-Layer Support**: Independent logging layers with different configurations
- **Multiple Logger Types**: Sync, Async, Composite, and CompositeAsync loggers
- **Zero Overhead Extensions**: Extensions disabled by default, no runtime cost when off
- **User Control**: Full control over formats, destinations, configurations, and extensions

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Code                          │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        │ logger.info("message", layer="api")
                        │
┌──────────────────────▼──────────────────────────────────────┐
│                    Logger Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Sync    │  │  Async   │  │Composite │  │Composite │  │
│  │  Logger   │  │  Logger  │  │  Logger  │  │  Async   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└───────┼──────────────┼──────────────┼──────────────┼───────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Layer Manager              │
        │  (Route to layer handlers)   │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Handler System            │
        │  Console │ File │ Network    │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Formatter System           │
        │  Text │ JSON │ Colored        │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Output Destinations        │
        │  Console │ Files │ Network   │
        └───────────────────────────────┘
```

---

## Core Components

### 1. Logger Types

#### SyncLogger
- **Purpose**: Synchronous logging with immediate output
- **Flow**: Direct, blocking execution
- **Use Case**: Simple applications, debugging, low-volume logging

#### AsyncLogger
- **Purpose**: Asynchronous logging with queue-based processing
- **Flow**: Non-blocking, queue-based execution
- **Use Case**: High-performance applications, high-volume logging

#### CompositeLogger
- **Purpose**: Composite pattern for multiple logger components
- **Flow**: Routes to multiple component loggers
- **Use Case**: Complex scenarios requiring multiple logging strategies

#### CompositeAsyncLogger
- **Purpose**: Async version of composite logger
- **Flow**: Async queue with multiple component routing
- **Use Case**: High-performance composite logging

### 2. Layer Manager

**Purpose**: Organize logging handlers into logical groups with independent configurations

**Key Features**:
- Fallback hierarchy (requested → default → any available)
- Automatic handler creation from configuration
- Thread-safe operations
- Multi-layer performance optimizations
- Layer-specific level thresholds

**Layer Flow**:
```
User Call (layer="api")
    │
    ▼
LayerManager.get_handlers_for_layer("api")
    │
    ├─→ Layer exists? ──Yes──→ Return layer handlers
    │
    └─→ No ──→ Fallback to "default" layer
            │
            └─→ No default? ──→ Return any available layer
                              │
                              └─→ No layers? ──→ Return empty list
```

### 3. Handler System

**Purpose**: Deliver formatted log records to their final destinations

**Handler Types**:
- **ConsoleHandler**: Output to stdout/stderr
- **FileHandler**: Write to local files
- **NetworkHandler**: Send to remote servers (HTTP, WebSocket, etc.)
- **DatabaseHandler**: Store in databases (PostgreSQL, MongoDB, Redis)
- **CloudHandler**: Send to cloud services (AWS CloudWatch, Elasticsearch)
- **NullHandler**: Discard logs (for testing)

**Handler Flow**:
```
LogRecord
    │
    ▼
Handler.handle(record)
    │
    ├─→ Check level threshold
    │
    ├─→ Apply formatter.format(record)
    │
    └─→ Write to destination
```

### 4. Formatter System

**Purpose**: Convert LogRecord objects into formatted strings

**Formatter Types**:
- **PlainTextFormatter**: Clean text output
- **ColoredFormatter**: ANSI color codes for console
- **JsonLinesFormatter**: JSON Lines format (one JSON per line)
- **StructuredFormatters**: CSV, Syslog, GELF, Logstash formats

**Formatter Flow**:
```
LogRecord
    │
    ▼
Formatter.format(record)
    │
    ├─→ Extract fields (timestamp, level, message, etc.)
    │
    ├─→ Apply format string or structure
    │
    └─→ Return formatted string
```

### 5. Extension System

**Purpose**: Extend logger functionality with plugins

**Extension Types**:
- **SecurityExtension**: Data redaction, PII detection
- **FormattingExtension**: Custom formatting logic
- **PerformanceExtension**: Performance monitoring

**Extension Flow**:
```
LogRecord (before handler)
    │
    ▼
ExtensionManager.process_data(record)
    │
    ├─→ Iterate enabled extensions in order
    │
    ├─→ extension.process(record)
    │
    └─→ Return processed record
```

---

## Data Flow Architecture

### Complete Logging Flow (SyncLogger)

```
1. User Code
   logger.info("User logged in", layer="api", extra={"user_id": 123})
   
2. Logger.log() Method
   ├─→ Validate logger state (initialized, not closed)
   ├─→ Convert level string to numeric (if needed)
   └─→ Create LogRecord
   
3. LogRecord Creation
   ├─→ Extract context (file_name, function_name, line_number)
   ├─→ Create LogRecord with:
   │   - timestamp (current time)
   │   - level_name ("INFO")
   │   - layer ("api")
   │   - message ("User logged in")
   │   - extra data ({"user_id": 123})
   │   - context data
   └─→ Return LogRecord
   
4. Data Protection (if enabled)
   ├─→ SecurityExtension.process(record.message)
   ├─→ Redact sensitive data (PII, API keys, etc.)
   └─→ Return sanitized message
   
5. Layer Routing
   ├─→ Get layer name from kwargs (default: "default")
   ├─→ Check if level is enabled for layer
   └─→ Get handlers for layer
   
6. Handler Processing
   For each handler in layer:
   ├─→ handler.handle(record)
   │   ├─→ Check handler level threshold
   │   ├─→ Get formatter from handler
   │   ├─→ formatter.format(record)
   │   │   ├─→ Extract record fields
   │   │   ├─→ Apply format template
   │   │   └─→ Return formatted string
   │   └─→ Write formatted string to destination
   │       ├─→ Console: sys.stdout.write()
   │       ├─→ File: file.write()
   │       └─→ Network: http.post() / websocket.send()
   
7. Completion
   └─→ Return (record may be returned to pool for reuse)
```

### Complete Logging Flow (AsyncLogger)

```
1. User Code
   await logger.info("User logged in", layer="api")
   
2. AsyncLogger.log() Method
   ├─→ Validate logger state
   ├─→ Create LogRecord
   └─→ Queue record for async processing
       └─→ asyncio.Queue.put(record)
   
3. Background Worker (async)
   ├─→ Continuously await queue.get()
   ├─→ Process record (same as SyncLogger steps 4-6)
   └─→ Loop back to await next record
   
4. Batch Processing (optional)
   ├─→ Collect multiple records
   ├─→ Process batch together
   └─→ Write batch to destination
```

---

## Logger Types and Flows

### SyncLogger Flow

```
┌─────────────┐
│ User Call   │
│ logger.info │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ SyncLogger.log  │
│ - Validate      │
│ - Create Record │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Data Protection │
│ (if enabled)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Layer Routing   │
│ - Get handlers  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Handler Loop    │
│ - Format        │
│ - Write         │
└─────────────────┘
```

### AsyncLogger Flow

```
┌─────────────┐
│ User Call   │
│ await       │
│ logger.info │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ AsyncLogger.log │
│ - Create Record │
│ - Queue.put()   │
└──────┬──────────┘
       │
       │ (Non-blocking)
       │
       ▼
┌─────────────────┐
│ Background      │
│ Worker Loop     │
│ - queue.get()   │
│ - Process       │
│ - Format        │
│ - Write         │
└─────────────────┘
```

### CompositeLogger Flow

```
┌─────────────┐
│ User Call   │
│ logger.info │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ CompositeLogger │
│ .log()          │
└──────┬──────────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
       ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Component│   │ Component│   │ Component│
│ Logger 1 │   │ Logger 2 │   │ Logger 3 │
└────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │
     └──────────────┴──────────────┘
                    │
                    ▼
            (Each processes independently)
```

---

## Layer Management System

### Layer Configuration Structure

```
LoggingConfig
    │
    └─→ layers: Dict[str, LogLayer]
            │
            ├─→ "api": LogLayer
            │   ├─→ level: "INFO"
            │   └─→ destinations: [LogDestination, ...]
            │
            ├─→ "database": LogLayer
            │   ├─→ level: "WARNING"
            │   └─→ destinations: [LogDestination, ...]
            │
            └─→ "default": LogLayer
                ├─→ level: "WARNING"
                └─→ destinations: [LogDestination, ...]
```

### Layer Manager Initialization

```
1. LoggerFactory.create_logger(config)
   │
   └─→ SyncLogger.__init__(config)
       │
       └─→ _setup_layers()
           │
           └─→ LayerManager.setup_layers(config.layers)
               │
               ├─→ For each layer in config:
               │   ├─→ Create LayerConfiguration
               │   ├─→ Create handlers from destinations
               │   ├─→ Assign formatters to handlers
               │   └─→ Store in _layers dict
               │
               └─→ Update multi-layer flags
```

### Layer Routing Flow

```
User Call: logger.info("message", layer="api")
    │
    ▼
SyncLogger.log()
    │
    ├─→ Extract layer from kwargs (default: "default")
    │
    ├─→ Check level threshold: _is_level_enabled_for_layer("api", level)
    │   └─→ LayerManager.get_layer_threshold("api")
    │
    └─→ Get handlers: _get_handlers_for_layer("api")
        │
        └─→ LayerManager.get_handlers_for_layer("api")
            │
            ├─→ Layer exists? ──Yes──→ Return handlers
            │
            └─→ No ──→ Fallback to "default"
                    │
                    └─→ No default? ──→ Return any available
                                      │
                                      └─→ No layers? ──→ Return []
```

---

## Handler System

### Handler Creation Flow

```
LogDestination (from config)
    │
    ├─→ type: "console"
    ├─→ format: "colored"
    ├─→ use_colors: True
    └─→ stream: "stdout"
        │
        ▼
LayerManager._create_handler_from_config()
    │
    ├─→ Determine handler type
    │
    ├─→ Create handler instance
    │   ├─→ Console: SyncConsoleHandler(stream, use_colors)
    │   ├─→ File: FileHandler(filename, max_bytes, backup_count)
    │   └─→ Network: HTTPHandler(url, method, headers)
    │
    └─→ Assign formatter
        │
        └─→ get_formatter(format_type, use_colors)
            │
            └─→ Set handler.setFormatter(formatter)
```

### Handler Processing Flow

```
Handler.handle(LogRecord)
    │
    ├─→ Check level threshold
    │   └─→ record.level >= handler.level? ──No──→ Return (skip)
    │
    ├─→ Get formatter: handler.getFormatter()
    │
    ├─→ Format record: formatter.format(record)
    │   └─→ Returns formatted string
    │
    └─→ Write to destination
        │
        ├─→ ConsoleHandler
        │   └─→ sys.stdout.write(formatted_string)
        │
        ├─→ FileHandler
        │   └─→ file.write(formatted_string + "\n")
        │
        └─→ NetworkHandler
            └─→ http.post(url, data=formatted_string)
```

---

## Formatter System

### Formatter Selection

```
LogDestination
    │
    ├─→ format: "json-lines"
    └─→ use_colors: False
        │
        ▼
get_formatter("json-lines", use_colors=False)
    │
    └─→ Return JsonLinesFormatter()
```

### Formatting Flow

```
Formatter.format(LogRecord)
    │
    ├─→ Extract record fields
    │   ├─→ timestamp
    │   ├─→ level_name
    │   ├─→ layer
    │   ├─→ message
    │   ├─→ file_name
    │   ├─→ function_name
    │   └─→ extra, context
    │
    ├─→ Apply format template
    │   ├─→ PlainText: "{timestamp} {level} {message}"
    │   ├─→ JSON: {"timestamp": ..., "level": ..., "message": ...}
    │   └─→ Colored: ANSI codes + text
    │
    └─→ Return formatted string
```

### Formatter Types

#### PlainTextFormatter
```
Input:  LogRecord(level="INFO", message="User logged in")
Output: "2026-01-22 10:30:45 INFO User logged in"
```

#### JsonLinesFormatter
```
Input:  LogRecord(level="INFO", message="User logged in", extra={"user_id": 123})
Output: {"timestamp":1705915845.0,"level_name":"INFO","message":"User logged in","extra":{"user_id":123}}
```

#### ColoredFormatter
```
Input:  LogRecord(level="INFO", message="User logged in")
Output: "\033[32mINFO\033[0m User logged in"  (with ANSI color codes)
```

---

## Extension System

### Extension Initialization

```
LoggerFactory.create_logger(config)
    │
    └─→ _setup_extensions(config)
        │
        ├─→ Check config.extensions
        │
        ├─→ Create ExtensionManager
        │
        └─→ For each extension in config:
            ├─→ extension_type = config.get("type")
            ├─→ enabled = config.get("enabled", False)
            │
            └─→ ExtensionManager.create_extension(
                    name, extension_type, enabled, **config
                )
```

### Extension Processing Flow

```
LogRecord (before handler)
    │
    ▼
ExtensionManager.process_data(record)
    │
    ├─→ Get processing order
    │
    └─→ For each extension in order:
        │
        ├─→ extension.is_enabled()? ──No──→ Skip
        │
        └─→ Yes ──→ extension.process(record)
                    │
                    ├─→ SecurityExtension: Redact PII
                    ├─→ FormattingExtension: Custom format
                    └─→ PerformanceExtension: Monitor metrics
```

### Security Extension Example

```
SecurityExtension.process(message)
    │
    ├─→ Check redaction patterns
    │   ├─→ Email: user@example.com → [EMAIL_REDACTED]
    │   ├─→ Phone: +1234567890 → [PHONE_REDACTED]
    │   └─→ API Key: sk_live_... → [API_KEY_REDACTED]
    │
    └─→ Return sanitized message
```

---

## Configuration System

### Configuration Hierarchy

```
1. User Configuration (LoggingConfig)
   ├─→ layers: Dict[str, LogLayer]
   ├─→ extensions: Dict[str, ExtensionConfig]
   └─→ global_level: str
   
2. Layer Configuration (LogLayer)
   ├─→ level: str
   └─→ destinations: List[LogDestination]
   
3. Destination Configuration (LogDestination)
   ├─→ type: str (console, file, network, etc.)
   ├─→ format: str (plain-text, json-lines, colored)
   ├─→ use_colors: bool
   └─→ path/url: str (for file/network)
   
4. Extension Configuration
   ├─→ enabled: bool
   ├─→ type: str (security, formatting, performance)
   └─→ config: Dict (extension-specific settings)
```

### Configuration Flow

```
1. User creates LoggingConfig
   config = LoggingConfig(
       layers={
           "api": LogLayer(
               level="INFO",
               destinations=[
                   LogDestination(
                       type="console",
                       format="colored",
                       use_colors=True
                   ),
                   LogDestination(
                       type="file",
                       path="logs/api.log",
                       format="json-lines"
                   )
               ]
           )
       }
   )
   
2. Factory creates logger
   logger = create_logger(config, logger_type="sync")
   
3. Logger initializes
   ├─→ Parse config
   ├─→ Setup layers
   ├─→ Create handlers
   ├─→ Assign formatters
   └─→ Setup extensions
   
4. Logger ready for use
   logger.info("Message", layer="api")
```

---

## Factory Pattern

### Factory Flow

```
User Code
    │
    ├─→ create_logger(config, "sync")
    ├─→ create_async_logger(config)
    ├─→ create_logger_with_template("production", "async")
    └─→ getLogger(__name__)
        │
        ▼
LoggerFactory
    │
    ├─→ Parse configuration
    │   ├─→ Dict → LoggingConfig
    │   └─→ None → Default config
    │
    ├─→ Setup extensions
    │
    └─→ Create logger instance
        ├─→ "sync" → SyncLogger(config)
        ├─→ "async" → AsyncLogger(config)
        ├─→ "composite" → CompositeLogger(config)
        └─→ "composite-async" → CompositeAsyncLogger(config)
```

### Logger Manager Flow

```
getLogger(__name__)
    │
    ▼
LoggerManager.getLogger(name, config, logger_type)
    │
    ├─→ Check cache: name in _loggers? ──Yes──→ Return cached
    │
    └─→ No ──→ Create new logger
        │
        ├─→ Use factory.create_logger()
        │
        └─→ Cache and return
```

---

## Performance Optimizations

### 1. LogRecord Pooling

```
LogRecord Creation
    │
    ├─→ Check pool for available record
    │
    ├─→ Pool available? ──Yes──→ Reuse record
    │
    └─→ No ──→ Create new record
        │
        └─→ Return to pool after use
```

### 2. Level Caching

```
Level Conversion
    │
    ├─→ Check cache: level_str in _level_cache?
    │
    ├─→ Yes ──→ Return cached value
    │
    └─→ No ──→ Convert and cache
        │
        └─→ Return value
```

### 3. Handler Caching

```
Handler Lookup
    │
    ├─→ Layer handlers cached in LayerManager
    │
    └─→ Direct dictionary lookup (O(1))
```

### 4. Async Queue Batching

```
AsyncLogger
    │
    ├─→ Collect records in batch
    │
    ├─→ Process batch together
    │
    └─→ Write batch to destination
        └─→ Reduces I/O operations
```

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Application                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ logger.info("message", layer="api")
                       │
        ┌──────────────▼──────────────┐
        │      Logger (Sync/Async)    │
        │  - Create LogRecord         │
        │  - Apply extensions         │
        │  - Route to layer           │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │     LayerManager            │
        │  - Get layer handlers       │
        │  - Fallback logic           │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │      Handler(s)             │
        │  - Check level              │
        │  - Get formatter            │
        │  - Format record            │
        │  - Write to destination     │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │      Formatter              │
        │  - Extract fields           │
        │  - Apply template           │
        │  - Return string            │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │    Destination              │
        │  - Console (stdout)         │
        │  - File (disk)               │
        │  - Network (HTTP/WS)         │
        │  - Database (PostgreSQL)     │
        └─────────────────────────────┘
```

---

## Key Design Patterns

### 1. Factory Pattern
- **LoggerFactory**: Creates logger instances based on type and configuration
- **HandlerFactory**: Creates handlers from destination configurations
- **FormatterFactory**: Creates formatters based on format type

### 2. Strategy Pattern
- **Performance Profiles**: Different record creation strategies (minimal, balanced, convenient)
- **Formatting Strategies**: Different formatters for different output formats

### 3. Composite Pattern
- **CompositeLogger**: Combines multiple logger components
- **Layer System**: Multiple layers with independent configurations

### 4. Observer Pattern
- **Extension System**: Extensions observe and process log records
- **Handler System**: Multiple handlers observe and process records

### 5. Chain of Responsibility
- **Layer Fallback**: Requested → default → any available
- **Extension Processing**: Process through enabled extensions in order

---

## Thread Safety

### Synchronization Points

1. **LoggerManager**: Thread-safe logger registry with per-logger locks
2. **LayerManager**: Thread-safe layer operations with RLock
3. **Handler Operations**: Thread-safe handler.handle() calls
4. **ExtensionManager**: Thread-safe extension processing

### Async Safety

1. **AsyncLogger**: Uses asyncio.Queue for thread-safe async operations
2. **Async Handlers**: Async handlers use async I/O operations
3. **Context Managers**: Proper async context manager support

---

## Error Handling

### Error Handling Strategy

1. **Silent Failures**: Logging errors don't crash the application
2. **Fallback Mechanisms**: Layer fallback, handler fallback
3. **Graceful Degradation**: Continue with available components
4. **Error Isolation**: Errors in one handler don't affect others

### Error Flow

```
Handler.handle(record)
    │
    ├─→ Try: Format and write
    │
    └─→ Exception ──→ Catch silently
        │
        └─→ Continue with next handler
```

---

## Summary

This workflow architecture document provides a comprehensive view of how Hydra-Logger processes log messages from user code to final output destinations. The system is designed with:

- **Modularity**: Each component has a clear responsibility
- **Flexibility**: Multiple logger types, handlers, and formatters
- **Performance**: Optimizations at every level
- **Extensibility**: Plugin system for custom functionality
- **User Control**: Full control over all aspects of logging

Use this document as a reference for:
- Understanding system flow
- Creating architectural diagrams
- Debugging logging issues
- Extending the system with new components
- Optimizing performance
