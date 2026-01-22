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

Hydra-Logger is a multi-headed, event-oriented logging system with the following key characteristics:

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

![Hydra-Logger Data Flow](../data/diagrams/Hydra-Logger%20Data%20Flow-2026-01-22-095325.png)

### Complete Logging Flow (SyncLogger)

```
1. User Code
   logger.info("User logged in", layer="api", extra={"user_id": 123})
   
2. SyncLogger.log() Method (sync_logger.py:520)
   ├─→ Fast path checks:
   │   ├─→ Check if initialized (_initialized flag)
   │   └─→ Check if closed (_closed flag)
   │   └─→ If either fails, return immediately (silent)
   │
   ├─→ Level Conversion:
   │   ├─→ If level is string: LogLevelManager.get_level(level)
   │   └─→ If level is int: use directly
   │
   └─→ Create LogRecord:
       └─→ self.create_log_record(level, message, **kwargs)
   
3. LogRecord Creation (base.py:463)
   ├─→ Check if RecordCreationStrategy exists:
   │   ├─→ If yes: strategy.create_record(level, message, logger_name, **kwargs)
   │   │   └─→ Uses performance profile (minimal/context/auto_context)
   │   │       ├─→ MINIMAL: Essential fields only (fastest)
   │   │       ├─→ CONTEXT: Explicit context fields provided
   │   │       └─→ AUTO_CONTEXT: Auto-detect file_name, function_name, line_number
   │   │           └─→ Uses inspect.stack() to get caller info
   │   │
   └─→ If no strategy (fallback):
       └─→ Direct LogRecord creation with field order:
           ├─→ timestamp: time.time()
           ├─→ level_name: Converted from level
           ├─→ layer: kwargs.get("layer", "default")
           ├─→ file_name: kwargs.get("file_name")
           ├─→ function_name: kwargs.get("function_name")
           ├─→ message: message
           ├─→ level: Numeric level
           ├─→ logger_name: self._name
           ├─→ line_number: kwargs.get("line_number")
           └─→ extra: kwargs.get("extra", {})
   
4. Data Protection (if enabled) (sync_logger.py:535)
   ├─→ Check: self._data_protection and self._data_protection.is_enabled()
   ├─→ If enabled:
   │   ├─→ record.message = self._data_protection.process(record.message)
   │   └─→ Redact sensitive data (PII, API keys, etc.)
   └─→ If processing fails: Continue with original message (silent error)
   
5. Layer Routing (sync_logger.py:543)
   ├─→ Extract layer: layer_name = kwargs.get('layer', 'default')
   ├─→ Check level threshold:
   │   └─→ _is_level_enabled_for_layer(layer_name, level)
   │       └─→ Get layer threshold from LayerManager
   │       └─→ Compare: level >= threshold? ──No──→ Return (skip logging)
   │
   └─→ Get handlers for layer:
       └─→ _get_handlers_for_layer(layer_name)
           ├─→ Check cache: _handler_cache[layer_name]
           ├─→ If cached: Return cached handlers
           └─→ If not cached:
               ├─→ Lookup: _layer_handlers[layer_name]
               ├─→ If not found: Fallback to _layer_handlers['default']
               ├─→ If no default: Return empty list []
               └─→ Cache result in _handler_cache
   
6. Handler Processing (sync_logger.py:550)
   For each handler in layer_handlers:
   ├─→ handler.handle(record)  (base_handler.py:204)
   │   ├─→ Check level: handler.isEnabledFor(record.level)
   │   │   └─→ record.level >= handler.level? ──No──→ Return (skip)
   │   │
   │   └─→ If enabled: handler.emit(record)
   │       │
   │       ├─→ Get formatter: handler.formatter or handler._get_formatter()
   │       │   └─→ ConsoleHandler: Lazy initialization of formatter
   │       │       ├─→ If use_colors: ColoredFormatter
   │       │       └─→ Else: PlainTextFormatter
   │       │
   │       ├─→ Format record: formatter.format(record)
   │       │   ├─→ PlainTextFormatter: Extract fields, apply template
   │       │   ├─→ ColoredFormatter: Extends PlainTextFormatter, adds ANSI codes
   │       │   └─→ JsonLinesFormatter: Convert to JSON string
   │       │
   │       └─→ Write to destination:
   │           ├─→ ConsoleHandler.emit():
   │           │   ├─→ Add to buffer: _buffer.append(formatted_message)
   │           │   ├─→ Check buffer size: len(_buffer) >= _buffer_size?
   │           │   ├─→ Check flush interval: time elapsed >= _flush_interval?
   │           │   └─→ If either true: Flush buffer
   │           │       └─→ sys.stdout.write("\n".join(_buffer) + "\n")
   │           │
   │           ├─→ FileHandler.emit():
   │           │   ├─→ Add to buffer: _buffer.append(formatted_message)
   │           │   ├─→ Check buffer size: len(_buffer) >= _buffer_size?
   │           │   ├─→ Check flush interval: time elapsed >= _flush_interval?
   │           │   └─→ If either true: Flush buffer
   │           │       └─→ file.write("\n".join(_buffer) + "\n")
   │           │
   │           └─→ NetworkHandler.emit():
   │               └─→ http.post(url, data=formatted_message)
   
7. Completion
   └─→ Return (method completes, record may be garbage collected)
```

### Complete Logging Flow (AsyncLogger)

```
1. User Code
   await logger.info("User logged in", layer="api")
   
2. AsyncLogger.log() Method (async_logger.py)
   ├─→ Validate logger state:
   │   ├─→ Check if initialized (_initialized flag)
   │   └─→ Check if closed (_closed flag)
   │
   ├─→ Level conversion: LogLevelManager.get_level(level)
   │
   ├─→ Create LogRecord: self.create_log_record(level, message, **kwargs)
   │   └─→ Same as SyncLogger (uses RecordCreationStrategy)
   │
   ├─→ Data Protection (if enabled):
   │   └─→ Same as SyncLogger
   │
   └─→ Queue for async processing:
       └─→ await self._queue.put(record)
           └─→ Non-blocking if queue not full
           └─→ If queue full: May use overflow_queue
   
3. Background Worker Task (async_logger.py)
   ├─→ Continuously running: _writer_tasks
   ├─→ Loop:
   │   ├─→ await queue.get()  (blocking wait for record)
   │   ├─→ Acquire semaphore: await _concurrency_semaphore.acquire()
   │   │   └─→ Controls concurrent processing (based on system memory)
   │   │
   │   ├─→ Process record (same as SyncLogger steps 5-6):
   │   │   ├─→ Layer routing
   │   │   ├─→ Get handlers for layer
   │   │   └─→ For each handler:
   │   │       ├─→ handler.handle(record)
   │   │       └─→ handler.emit(record)  (async if AsyncHandler)
   │   │
   │   └─→ Release semaphore: _concurrency_semaphore.release()
   │
   └─→ Continue loop
   
4. Overflow Queue Processing (if main queue full)
   ├─→ Records go to overflow_queue (asyncio.Queue, maxsize=100000)
   ├─→ Separate overflow_worker_task processes overflow
   └─→ Same processing as main queue
   
5. Batch Processing (optional, for high throughput)
   ├─→ Collect multiple records from queue
   ├─→ Process batch together
   └─→ Write batch to destination (reduces I/O operations)
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
SyncLogger.log() (sync_logger.py:520)
    │
    ├─→ Extract layer: layer_name = kwargs.get('layer', 'default')
    │
    ├─→ Check level threshold:
    │   └─→ _is_level_enabled_for_layer(layer_name, level)
    │       └─→ Get threshold: _get_layer_threshold(layer_name)
    │           ├─→ Check cache: _layer_cache[layer_name]
    │           ├─→ If cached: Return cached threshold
    │           └─→ If not cached:
    │               ├─→ Lookup: LayerManager.get_layer_threshold(layer_name)
    │               │   └─→ Returns numeric level (10, 20, 30, etc.)
    │               └─→ Cache result
    │       └─→ Compare: level >= threshold? ──No──→ Return (skip)
    │
    └─→ Get handlers: _get_handlers_for_layer(layer_name)
        │
        └─→ Check cache: _handler_cache[layer_name]
            │
            ├─→ If cached: Return cached handlers (O(1))
            │
            └─→ If not cached:
                ├─→ Lookup: _layer_handlers[layer_name]
                │   └─→ Dictionary lookup: O(1)
                │
                ├─→ If not found: Fallback to 'default'
                │   └─→ _layer_handlers.get('default', [])
                │
                ├─→ If no default: Return any available
                │   └─→ list(_layer_handlers.values())[0] if _layer_handlers
                │
                └─→ If no layers: Return []
                    │
                    └─→ Cache result in _handler_cache
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
LayerManager._create_handler_from_config() (layer_management.py:188)
    │
    ├─→ Extract destination type:
    │   ├─→ If dict: destination_config.get("type", "console")
    │   └─→ If object: getattr(destination_config, "type", "console")
    │
    ├─→ Create handler based on type:
    │   │
    │   ├─→ type == "console":
    │   │   ├─→ Import: SyncConsoleHandler
    │   │   ├─→ Extract: format_type, use_colors, stream
    │   │   ├─→ Create: SyncConsoleHandler(stream, use_colors)
    │   │   │   └─→ Initializes with:
    │   │   │       ├─→ buffer_size: 5000 (default)
    │   │   │       ├─→ flush_interval: 0.5 (default)
    │   │   │       └─→ use_colors: from config
    │   │   │
    │   │   └─→ Assign formatter:
    │   │       ├─→ get_formatter(format_type, use_colors)
    │   │       │   ├─→ "colored" → ColoredFormatter(use_colors)
    │   │       │   ├─→ "plain-text" → PlainTextFormatter()
    │   │       │   └─→ "json-lines" → JsonLinesFormatter()
    │   │       │
    │   │       └─→ handler.setFormatter(formatter)
    │   │
    │   ├─→ type == "file":
    │   │   ├─→ Import: FileHandler
    │   │   ├─→ Extract: path/filename, max_size, backup_count
    │   │   └─→ Create: FileHandler(
    │   │       filename=path,
    │   │       max_bytes=max_size,
    │   │       backup_count=backup_count
    │   │   )
    │   │   └─→ FileHandler creates SyncFileHandler internally
    │   │       └─→ Initializes with:
    │   │           ├─→ buffer_size: 50000 (default)
    │   │           └─→ flush_interval: 5.0 (default)
    │   │
    │   └─→ type == "null":
    │       └─→ Create: NullHandler()  (discards all logs)
    │
    └─→ Return handler instance
```

### Handler Processing Flow

```
Handler.handle(LogRecord)  (base_handler.py:204)
    │
    ├─→ Check level threshold:
    │   └─→ handler.isEnabledFor(record.level)
    │       └─→ record.level >= handler.level? ──No──→ Return (skip)
    │
    └─→ If enabled: handler.emit(record)
        │
        ├─→ Get formatter:
        │   ├─→ If handler.formatter exists: Use it
        │   └─→ Else: handler._get_formatter()  (lazy initialization)
        │       ├─→ ConsoleHandler:
        │       │   ├─→ If use_colors and _colored_formatter is None:
        │       │   │   └─→ Create ColoredFormatter(use_colors=True)
        │       │   └─→ Else if _plain_formatter is None:
        │       │       └─→ Create PlainTextFormatter()
        │       │
        │       └─→ FileHandler: Always uses plain formatter (no colors)
        │
        ├─→ Format record: formatter.format(record)
        │   │
        │   ├─→ PlainTextFormatter.format():
        │   │   ├─→ Extract fields from LogRecord
        │   │   ├─→ Format timestamp: timestamp_config.format_timestamp()
        │   │   ├─→ Apply format_string template
        │   │   └─→ Return formatted string
        │   │
        │   ├─→ ColoredFormatter.format():
        │   │   ├─→ Call super().format() (PlainTextFormatter)
        │   │   ├─→ Extract level_name and layer
        │   │   ├─→ Apply ANSI color codes:
        │   │   │   ├─→ Level: LEVEL_COLORS[level_name]
        │   │   │   └─→ Layer: Colors.get_layer_color(layer)
        │   │   └─→ Return colorized string
        │   │
        │   └─→ JsonLinesFormatter.format():
        │       ├─→ Extract all LogRecord fields
        │       ├─→ Build dictionary with field order:
        │       │   ├─→ timestamp, level_name, layer, file_name, function_name, message
        │       │   └─→ level, logger_name, line_number, extra, context
        │       ├─→ Serialize to JSON: _encoder.encode(dict)
        │       └─→ Return JSON string (one line)
        │
        └─→ Write to destination:
            │
            ├─→ ConsoleHandler.emit() (console_handler.py:181):
            │   ├─→ Add to buffer: _buffer.append(formatted_message)
            │   ├─→ Update stats: _messages_processed += 1
            │   ├─→ Check buffer conditions:
            │   │   ├─→ len(_buffer) >= _buffer_size? (5000 default)
            │   │   └─→ time elapsed >= _flush_interval? (0.5s default)
            │   └─→ If either true: Flush buffer
            │       ├─→ Join buffer: "\n".join(_buffer) + "\n"
            │       └─→ Write: sys.stdout.write(joined_string)
            │
            ├─→ FileHandler.emit() (file_handler.py):
            │   ├─→ Add to buffer: _buffer.append(formatted_message)
            │   ├─→ Update stats: _messages_processed += 1
            │   ├─→ Check buffer conditions:
            │   │   ├─→ len(_buffer) >= _buffer_size? (50000 default)
            │   │   └─→ time elapsed >= _flush_interval? (5.0s default)
            │   └─→ If either true: Flush buffer
            │       ├─→ Join buffer: "\n".join(_buffer) + "\n"
            │       ├─→ Encode: string.encode(encoding)
            │       └─→ Write: file.write(encoded_string)
            │
            └─→ NetworkHandler.emit():
                └─→ http.post(url, data=formatted_string, headers=headers)
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
get_formatter(format_type, use_colors)  (formatters/__init__.py:107)
    │
    ├─→ format_type == "plain-text":
    │   └─→ Return PlainTextFormatter()
    │
    ├─→ format_type == "colored":
    │   └─→ Return ColoredFormatter(use_colors=use_colors)
    │
    ├─→ format_type == "json-lines" or "json":
    │   └─→ Return JsonLinesFormatter()
    │
    ├─→ format_type == "csv":
    │   └─→ Return CsvFormatter()
    │
    ├─→ format_type == "syslog":
    │   └─→ Return SyslogFormatter()
    │
    ├─→ format_type == "gelf":
    │   └─→ Return GelfFormatter()
    │
    ├─→ format_type == "logstash":
    │   └─→ Return LogstashFormatter()
    │
    └─→ Default (unknown format):
        └─→ Return PlainTextFormatter()  (fallback)
```

### Formatting Flow

```
Formatter.format(LogRecord)
    │
    ├─→ Extract record fields (from LogRecord dataclass)
    │   ├─→ timestamp: float (Unix timestamp)
    │   ├─→ level_name: str ("DEBUG", "INFO", etc.)
    │   ├─→ layer: str ("default", "api", etc.)
    │   ├─→ file_name: Optional[str]
    │   ├─→ function_name: Optional[str]
    │   ├─→ message: str
    │   ├─→ level: int (10, 20, 30, 40, 50)
    │   ├─→ logger_name: str
    │   ├─→ line_number: Optional[int]
    │   ├─→ extra: Dict[str, Any]
    │   └─→ context: Dict[str, Any]
    │
    ├─→ Apply format template (formatter-specific):
    │   │
    │   ├─→ PlainTextFormatter.format():
    │   │   ├─→ Format timestamp: timestamp_config.format_timestamp(dt)
    │   │   │   └─→ Converts float timestamp to datetime
    │   │   │   └─→ Applies format (RFC3339, ISO, etc.)
    │   │   ├─→ Apply format_string template:
    │   │   │   └─→ Default: "{timestamp} {level_name} {layer} {message}"
    │   │   └─→ Replace placeholders with field values
    │   │
    │   ├─→ ColoredFormatter.format():
    │   │   ├─→ Call super().format() (PlainTextFormatter)
    │   │   ├─→ Get level_name and layer from record
    │   │   ├─→ Apply colors:
    │   │   │   ├─→ _colorize_level(level_name)
    │   │   │   │   └─→ LEVEL_COLORS.get(level_name) → ANSI code
    │   │   │   │   └─→ Wrap: f"{color_code}{text}{Colors.RESET}"
    │   │   │   └─→ _colorize_layer(layer)
    │   │   │       └─→ Colors.get_layer_color(layer) → ANSI code
    │   │   └─→ Replace level and layer in formatted string
    │   │
    │   └─→ JsonLinesFormatter.format():
    │       ├─→ Build dictionary with field order:
    │       │   └─→ {
    │       │       "timestamp": record.timestamp,
    │       │       "level_name": record.level_name,
    │       │       "layer": record.layer,
    │       │       "file_name": record.file_name,
    │       │       "function_name": record.function_name,
    │       │       "message": record.message,
    │       │       "level": record.level,
    │       │       "logger_name": record.logger_name,
    │       │       "line_number": record.line_number,
    │       │       "extra": record.extra,
    │       │       "context": record.context
    │       │   }
    │       ├─→ Serialize: _encoder.encode(dict)
    │       │   └─→ Pre-compiled JSONEncoder with:
    │       │       ├─→ ensure_ascii=False
    │       │       ├─→ separators=(",", ":")  (compact)
    │       │       └─→ sort_keys=False  (performance)
    │       └─→ Return JSON string (one line, no newline)
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

### 1. RecordCreationStrategy (Performance Profiles)

```
Performance Profile Selection (base.py:213)
    │
    ├─→ Default: "convenient" (auto-detect context)
    ├─→ Options: "minimal", "context", "convenient"
    │
    └─→ Strategy created once at logger initialization
        └─→ Reused for all record creation

Strategy.create_record() (records.py:434)
    │
    ├─→ "minimal": Fastest, no context extraction
    │   └─→ Only essential fields (timestamp, level, layer, message)
    │
    ├─→ "context": Balanced, explicit context
    │   └─→ All fields, but user must provide context
    │
    └─→ "convenient": Convenient, auto-detection
        └─→ Uses inspect.stack() to auto-detect file/function/line
            └─→ Slightly slower but no user effort required
```

### 2. Level Caching

```
Level Conversion (types/levels.py)
    │
    ├─→ LogLevelManager.get_level(level)
    │   ├─→ If string: Lookup in level_map
    │   └─→ If int: Return directly
    │
    └─→ RecordCreationStrategy._level_cache
        └─→ Caches level name ↔ int conversions
```

### 3. Handler Caching

```
Handler Lookup (sync_logger.py:576)
    │
    ├─→ _get_handlers_for_layer(layer_name)
    │   ├─→ Check cache: _handler_cache[layer_name]
    │   ├─→ If cached: Return immediately (O(1))
    │   └─→ If not cached:
    │       ├─→ Lookup: _layer_handlers[layer_name]
    │       ├─→ Fallback to 'default' layer
    │       └─→ Cache result in _handler_cache
    │
    └─→ Layer threshold caching: _layer_cache[layer_name]
        └─→ Caches level threshold lookups
```

### 4. Formatter Caching

```
Formatter Creation (console_handler.py:165)
    │
    ├─→ Lazy initialization: _get_formatter()
    │   ├─→ If formatter already set: Return it
    │   ├─→ If use_colors and _colored_formatter is None:
    │   │   └─→ Create once, cache in _colored_formatter
    │   └─→ Else if _plain_formatter is None:
    │       └─→ Create once, cache in _plain_formatter
    │
    └─→ Formatter instances reused for all records
```

### 5. Buffer-Based Batching

```
ConsoleHandler Buffering (console_handler.py:181)
    │
    ├─→ Default buffer_size: 5000 messages
    ├─→ Default flush_interval: 0.5 seconds
    │
    ├─→ Records added to buffer: _buffer.append(message)
    │
    └─→ Flush conditions:
        ├─→ Buffer full: len(_buffer) >= buffer_size
        └─→ Time elapsed: time >= flush_interval
            └─→ Batch write: sys.stdout.write("\n".join(_buffer))

FileHandler Buffering (file_handler.py)
    │
    ├─→ Default buffer_size: 50000 messages
    ├─→ Default flush_interval: 5.0 seconds
    │
    └─→ Same flush logic as ConsoleHandler
        └─→ Reduces disk I/O operations significantly
```

### 6. Async Queue Processing

```
AsyncLogger Queue System (async_logger.py)
    │
    ├─→ Main queue: asyncio.Queue (unbounded)
    ├─→ Overflow queue: asyncio.Queue(maxsize=100000)
    │
    ├─→ Concurrency control: asyncio.Semaphore
    │   └─→ Dynamic concurrency based on system memory
    │
    ├─→ Background workers: Multiple _writer_tasks
    │   └─→ Process records concurrently
    │
    └─→ Batch processing: Optional batch collection
        └─→ Process multiple records together
```

### 7. Pre-compiled JSON Encoder

```
JsonLinesFormatter (json_formatter.py:138)
    │
    ├─→ Pre-compiled encoder created at initialization:
    │   └─→ json.JSONEncoder(
    │       ensure_ascii=False,
    │       separators=(",", ":"),  # Compact
    │       sort_keys=False  # Performance
    │   )
    │
    └─→ Reused for all JSON serialization
        └─→ Avoids encoder creation overhead
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
- **Extensibility**: Extension system for custom functionality
- **User Control**: Full control over all aspects of logging

Use this document as a reference for:
- Understanding system flow
- Creating architectural diagrams
- Debugging logging issues
- Extending the system with new components
- Optimizing performance

---

## Key Implementation Files Reference

### Core Logger Files
- **Base Logger**: `hydra_logger/loggers/base.py` - Abstract base class, LogRecord creation
- **Sync Logger**: `hydra_logger/loggers/sync_logger.py` - Synchronous logging implementation
- **Async Logger**: `hydra_logger/loggers/async_logger.py` - Asynchronous logging with queue
- **Composite Logger**: `hydra_logger/loggers/composite_logger.py` - Composite pattern implementation

### Handler Files
- **Base Handler**: `hydra_logger/handlers/base_handler.py` - Abstract handler interface
- **Console Handler**: `hydra_logger/handlers/console_handler.py` - Console output with buffering
- **File Handler**: `hydra_logger/handlers/file_handler.py` - File output with buffering
- **Network Handler**: `hydra_logger/handlers/network_handler.py` - Network destinations

### Formatter Files
- **Base Formatter**: `hydra_logger/formatters/base.py` - Abstract formatter interface
- **Text Formatter**: `hydra_logger/formatters/text_formatter.py` - Plain text formatting
- **Colored Formatter**: `hydra_logger/formatters/colored_formatter.py` - ANSI color support
- **JSON Formatter**: `hydra_logger/formatters/json_formatter.py` - JSON Lines format

### Core System Files
- **Layer Management**: `hydra_logger/core/layer_management.py` - Layer routing and handler management
- **Logger Management**: `hydra_logger/core/logger_management.py` - Logger registry (getLogger)
- **Factory**: `hydra_logger/factories/logger_factory.py` - Logger creation factory

### Type Files
- **LogRecord**: `hydra_logger/types/records.py` - LogRecord dataclass and creation strategies
- **LogLevel**: `hydra_logger/types/levels.py` - Log level constants and management
- **LogContext**: `hydra_logger/types/context.py` - Context information container

### Configuration Files
- **Config Models**: `hydra_logger/config/models.py` - LoggingConfig, LogLayer, LogDestination
- **Config Templates**: `hydra_logger/config/configuration_templates.py` - Pre-configured templates
- **Defaults**: `hydra_logger/config/defaults.py` - Default configuration values

### Extension Files
- **Extension Manager**: `hydra_logger/extensions/extension_manager.py` - Extension system
- **Extension Base**: `hydra_logger/extensions/extension_base.py` - Extension base classes
- **Security Extension**: `hydra_logger/extensions/security/data_redaction.py` - Data protection

---

## Critical Implementation Details

### LogRecord Field Order
The LogRecord dataclass follows a specific field order for performance:
1. `timestamp` (float)
2. `level_name` (str)
3. `layer` (str)
4. `file_name` (Optional[str])
5. `function_name` (Optional[str])
6. `message` (str)
7. `level` (int)
8. `logger_name` (str)
9. `line_number` (Optional[int])
10. `extra` (Dict[str, Any])
11. `context` (Dict[str, Any])

### Performance Profiles
- **minimal**: Fastest, no context extraction (file_name, function_name, line_number = None)
- **context**: Balanced, requires explicit context in kwargs
- **convenient** (default): Auto-detects context using inspect.stack()

### Buffer Sizes
- **ConsoleHandler**: buffer_size=5000, flush_interval=0.5s
- **FileHandler**: buffer_size=50000, flush_interval=5.0s
- **AsyncLogger**: queue unbounded, overflow_queue maxsize=100000

### Color System
- Colors only work with console handlers (not file handlers)
- ColoredFormatter extends PlainTextFormatter
- Colors applied via ANSI escape codes from `core/constants.py`
- use_colors=False by default for performance

### Error Handling
- All errors are silently caught to prevent infinite loops
- Handler errors don't affect other handlers
- Extension errors don't stop logging
- Fallback mechanisms at every level
