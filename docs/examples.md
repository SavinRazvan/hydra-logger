# Examples

This document provides comprehensive examples for Hydra-Logger, from basic usage to advanced features.

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Basic Usage Examples](#basic-usage-examples)
3. [Configuration Examples](#configuration-examples)
4. [Async Logging Examples](#async-logging-examples)
5. [Context Management Examples](#context-management-examples)
6. [Security Examples](#security-examples)
7. [Performance Examples](#performance-examples)
8. [Data Protection Examples](#data-protection-examples)
9. [Plugin Examples](#plugin-examples)
10. [Real-World Examples](#real-world-examples)

## Quick Start Examples

### Zero Configuration

```python
from hydra_logger import HydraLogger

# Works immediately without configuration
logger = HydraLogger()
logger.info("APP", "Application started")
logger.warning("APP", "Configuration file not found")
logger.error("APP", "Database connection failed")
```

### Quick Setup with create_logger

```python
from hydra_logger import create_logger

# Simplest way to get started
logger = create_logger()
logger.info("Application started")

# Disable security features for performance
logger = create_logger(enable_security=False)

# Disable plugins for simpler setup
logger = create_logger(enable_plugins=False)

# Custom configuration with some features disabled
logger = create_logger(
    config={"layers": {"app": {"level": "DEBUG"}}},
    enable_sanitization=False,
    enable_plugins=False
)
```

## Basic Usage Examples

### Multi-Layer Logging

```python
from hydra_logger import HydraLogger

logger = HydraLogger()

# Log to different layers
logger.info("APP", "Application initialized")
logger.info("API", "API endpoint called")
logger.info("DB", "Database query executed")
logger.info("AUTH", "User authenticated")
logger.info("PERF", "Response time: 150ms")
```

### Log Levels

```python
from hydra_logger import HydraLogger

logger = HydraLogger()

# Different log levels
logger.debug("DEBUG", "Debug information")
logger.info("INFO", "General information")
logger.warning("WARNING", "Warning message")
logger.error("ERROR", "Error occurred")
logger.critical("CRITICAL", "Critical error")
```

### Extra Data

```python
from hydra_logger import HydraLogger

logger = HydraLogger()

# Log with extra data
logger.info("API", "Request processed", extra={
    "user_id": 12345,
    "response_time": 150,
    "status_code": 200
})

logger.error("DB", "Query failed", extra={
    "query": "SELECT * FROM users",
    "error_code": 500,
    "retry_count": 3
})
```

## Configuration Examples

### Basic Configuration

```python
from hydra_logger import HydraLogger

config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text"},
                {"type": "file", "path": "logs/app.log", "format": "json"}
            ]
        }
    }
}

logger = HydraLogger(config)
logger.info("APP", "Application started")
```

### Multiple Layers and Destinations

```python
from hydra_logger import HydraLogger

config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},
                {"type": "file", "path": "logs/app.log", "format": "json"}
            ]
        },
        "API": {
            "level": "DEBUG",
            "destinations": [
                {"type": "file", "path": "logs/api/requests.json", "format": "json"}
            ]
        },
        "ERRORS": {
            "level": "ERROR",
            "destinations": [
                {"type": "file", "path": "logs/errors.log", "format": "plain-text"},
                {"type": "console", "level": "CRITICAL", "format": "gelf"}
            ]
        }
    }
}

logger = HydraLogger(config)

# Log to different layers
logger.info("APP", "Application started")
logger.debug("API", "API request received")
logger.error("ERRORS", "Critical error occurred")
```

### Format Examples

```python
from hydra_logger import HydraLogger

# Plain text format
config_plain = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        }
    }
}

# JSON format
config_json = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/app.json", "format": "json"}
            ]
        }
    }
}

# CSV format
config_csv = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/metrics.csv", "format": "csv"}
            ]
        }
    }
}

# Syslog format
config_syslog = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/system.log", "format": "syslog"}
            ]
        }
    }
}

# GELF format
config_gelf = {
    "layers": {
        "APP": {
            "destinations": [
                {"type": "file", "path": "logs/graylog.gelf", "format": "gelf"}
            ]
        }
    }
}
```

### Color Mode Examples

```python
from hydra_logger import HydraLogger

config = {
    "layers": {
        "APP": {
            "destinations": [
                {
                    "type": "console",
                    "format": "plain-text",
                    "color_mode": "always"  # Always colored
                },
                {
                    "type": "file",
                    "path": "logs/app.log",
                    "format": "plain-text",
                    "color_mode": "never"   # Never colored
                }
            ]
        }
    }
}

logger = HydraLogger(config)
logger.info("APP", "This will be colored in console but plain in file")
```

## Async Logging Examples

### Basic Async Logging

```python
from hydra_logger.async_hydra import AsyncHydraLogger

async def main():
    async with AsyncHydraLogger() as logger:
        await logger.info("APP", "Application started")
        await logger.info("API", "API request processed")
        await logger.error("ERROR", "Error occurred")

# Run async function
import asyncio
asyncio.run(main())
```

### Async Configuration

```python
from hydra_logger.async_hydra import AsyncHydraLogger

config = {
    "handlers": [
        {
            "type": "file",
            "filename": "logs/async.log",
            "max_queue_size": 1000,
            "memory_threshold": 70.0
        },
        {
            "type": "console",
            "use_colors": True,
            "max_queue_size": 500
        }
    ]
}

async def main():
    async with AsyncHydraLogger(config) as logger:
        await logger.info("APP", "Async logging configured")
        await logger.debug("DEBUG", "Debug information")
        await logger.warning("WARNING", "Warning message")

asyncio.run(main())
```

### Async with Multiple Handlers

```python
from hydra_logger.async_hydra import AsyncHydraLogger, AsyncFileHandler, AsyncConsoleHandler

async def main():
    logger = AsyncHydraLogger()
    await logger.initialize()
    
    # Add handlers
    file_handler = AsyncFileHandler("logs/async.log")
    console_handler = AsyncConsoleHandler(use_colors=True)
    
    logger.add_handler(file_handler)
    logger.add_handler(console_handler)
    
    # Log messages
    await logger.info("APP", "Message to both handlers")
    await logger.error("ERROR", "Error to both handlers")
    
    await logger.aclose()

asyncio.run(main())
```

## Context Management Examples

### Basic Context Management

```python
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.async_hydra.context import async_context

async def main():
    async with AsyncHydraLogger() as logger:
        async with async_context(context_id="request-123"):
            await logger.info("REQUEST", "Processing request")
            await logger.info("REQUEST", "Request completed")

asyncio.run(main())
```

### Distributed Tracing

```python
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.async_hydra.context import trace_context, span_context

async def main():
    async with AsyncHydraLogger() as logger:
        async with trace_context(trace_id="trace-456"):
            await logger.info("TRACE", "Request traced")
            
            async with span_context("database_query", {"table": "users"}):
                await logger.info("DB", "Query executed")
            
            async with span_context("api_call", {"endpoint": "/api/users"}):
                await logger.info("API", "API call made")

asyncio.run(main())
```

### Context with Metadata

```python
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.async_hydra.context import async_context

async def main():
    async with AsyncHydraLogger() as logger:
        async with async_context(context_id="request-123") as ctx:
            # Add metadata to context
            ctx.update_metadata("user_id", 12345)
            ctx.update_metadata("session_id", "session-789")
            
            await logger.info("REQUEST", "Processing request with context")
            await logger.info("REQUEST", "Request completed")

asyncio.run(main())
```

### Nested Context

```python
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.async_hydra.context import async_context

async def main():
    async with AsyncHydraLogger() as logger:
        async with async_context(context_id="outer-context") as outer_ctx:
            outer_ctx.update_metadata("outer_data", "value1")
            await logger.info("OUTER", "Outer context")
            
            async with async_context(context_id="inner-context") as inner_ctx:
                inner_ctx.update_metadata("inner_data", "value2")
                await logger.info("INNER", "Inner context")
                
                await logger.info("BOTH", "Both contexts active")

asyncio.run(main())
```

## Security Examples

### Basic Security Features

```python
from hydra_logger import HydraLogger

# Enable security features
logger = HydraLogger(enable_security=True, enable_sanitization=True)

# Sensitive data will be automatically masked
logger.info("AUTH", "Login attempt", extra={
    "email": "user@example.com",
    "password": "secret123",
    "session_token": "abc123def456"
})

# Output: email=***@***.com password=*** session_token=***
```

### Custom Security Patterns

```python
from hydra_logger.data_protection import DataSanitizer

sanitizer = DataSanitizer()

# Add custom patterns
sanitizer.add_pattern("credit_card", r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")
sanitizer.add_pattern("phone_number", r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")

logger = HydraLogger(enable_sanitization=True)

# Test custom patterns
logger.info("USER", "User data", extra={
    "credit_card": "1234-5678-9012-3456",
    "phone": "555-123-4567",
    "email": "user@example.com"
})

# Output: credit_card=*** phone=*** email=***@***.com
```

### Security Validation

```python
from hydra_logger.data_protection import SecurityValidator

validator = SecurityValidator()

# Test for SQL injection
sql_input = "SELECT * FROM users WHERE id = 1; DROP TABLE users;"
result = validator.validate_input(sql_input)

if result["is_safe"]:
    logger.info("SAFE", "Input is safe")
else:
    logger.warning("SECURITY", f"Potential threat: {result['threats']}")

# Test for XSS
xss_input = "<script>alert('xss')</script>"
result = validator.validate_input(xss_input)

if not result["is_safe"]:
    logger.error("SECURITY", f"XSS detected: {result['threats']}")
```

## Performance Examples

### Performance Monitoring

```python
from hydra_logger.async_hydra.performance import get_performance_monitor

async def main():
    monitor = get_performance_monitor()
    
    async with monitor.async_timer("database_query"):
        # Simulate database query
        await asyncio.sleep(0.1)
        await logger.info("DB", "Query executed")
    
    async with monitor.async_timer("api_call"):
        # Simulate API call
        await asyncio.sleep(0.2)
        await logger.info("API", "API call completed")
    
    # Get performance statistics
    stats = monitor.get_async_statistics()
    print(f"Average database query time: {stats['database_query']['average_duration']}ms")
    print(f"Average API call time: {stats['api_call']['average_duration']}ms")

asyncio.run(main())
```

### Memory Monitoring

```python
from hydra_logger.async_hydra.core import MemoryMonitor

async def main():
    monitor = MemoryMonitor(max_percent=70.0, check_interval=5.0)
    
    # Check memory usage
    if monitor.check_memory():
        await logger.warning("MEMORY", "Memory usage high")
    
    # Get memory statistics
    stats = monitor.get_memory_stats()
    print(f"Memory usage: {stats['usage_percent']}%")
    print(f"Available memory: {stats['available_mb']}MB")

asyncio.run(main())
```

### Performance Modes

```python
from hydra_logger import HydraLogger

# Minimal features for maximum performance
logger = HydraLogger.for_minimal_features()

# Bare metal for ultimate performance
logger = HydraLogger.for_bare_metal()

# Production with balanced features
logger = HydraLogger.for_production()

# Development with debug features
logger = HydraLogger.for_development()

# Testing with test-specific features
logger = HydraLogger.for_testing()
```

## Data Protection Examples

### Data Loss Protection

```python
from hydra_logger.data_protection import DataLossProtection

async def main():
    protection = DataLossProtection(backup_dir=".hydra_backup")
    
    # Backup critical messages
    await protection.backup_message("Critical log message", "error_queue")
    await protection.backup_message("Another critical message", "error_queue")
    
    # Restore messages after failure
    restored_messages = await protection.restore_messages("error_queue")
    
    for message in restored_messages:
        print(f"Restored: {message}")

asyncio.run(main())
```

### Atomic File Operations

```python
from hydra_logger.data_protection import FallbackHandler

handler = FallbackHandler()

# Safe writing
data = {"key": "value", "number": 42}
handler.safe_write_json(data, "logs/critical.json")

records = [
    {"timestamp": "2024-01-15", "level": "INFO", "message": "Test"},
    {"timestamp": "2024-01-15", "level": "ERROR", "message": "Error"}
]
handler.safe_write_csv(records, "logs/data.csv")

# Safe reading with corruption detection
try:
    data = handler.safe_read_json("logs/critical.json")
    print(f"Read data: {data}")
except Exception as e:
    print(f"Failed to read JSON: {e}")

try:
    records = handler.safe_read_csv("logs/data.csv")
    print(f"Read records: {records}")
except Exception as e:
    print(f"Failed to read CSV: {e}")
```

### Corruption Detection

```python
from hydra_logger.data_protection import CorruptionDetector

detector = CorruptionDetector()

# Check JSON file
is_valid_json = detector.is_valid_json("logs/data.json")
print(f"JSON file is valid: {is_valid_json}")

# Check CSV file
is_valid_csv = detector.is_valid_csv("logs/data.csv")
print(f"CSV file is valid: {is_valid_csv}")

# Detect corruption by format
is_corrupted = detector.detect_corruption("logs/data.json", "json")
print(f"File is corrupted: {is_corrupted}")

# Get corruption details
corruption_info = detector.get_corruption_info("logs/data.json")
if corruption_info:
    print(f"Corruption details: {corruption_info}")
```

## Plugin Examples

### Basic Plugin

```python
from hydra_logger import HydraLogger, AnalyticsPlugin

class CustomAnalytics(AnalyticsPlugin):
    def __init__(self):
        self.event_count = 0
        self.error_count = 0
    
    def process_event(self, event):
        self.event_count += 1
        
        if event.get("level") == "ERROR":
            self.error_count += 1
        
        return {"processed": True}
    
    def get_insights(self):
        return {
            "total_events": self.event_count,
            "error_rate": self.error_count / self.event_count if self.event_count > 0 else 0
        }

# Use plugin
logger = HydraLogger(enable_plugins=True)
logger.add_plugin("custom_analytics", CustomAnalytics())

# Log some events
logger.info("APP", "Event 1")
logger.error("APP", "Error event")
logger.info("APP", "Event 2")

# Get insights
insights = logger.get_plugin_insights()
print(f"Analytics insights: {insights}")
```

### Advanced Plugin

```python
from hydra_logger import HydraLogger, AnalyticsPlugin
import time

class PerformancePlugin(AnalyticsPlugin):
    def __init__(self):
        self.operation_times = {}
        self.start_times = {}
    
    def process_event(self, event):
        # Track operation times
        if "operation" in event:
            operation = event["operation"]
            if operation in self.start_times:
                duration = time.time() - self.start_times[operation]
                if operation not in self.operation_times:
                    self.operation_times[operation] = []
                self.operation_times[operation].append(duration)
                del self.start_times[operation]
        
        return {"processed": True}
    
    def start_operation(self, operation_name):
        """Start timing an operation."""
        self.start_times[operation_name] = time.time()
    
    def get_insights(self):
        insights = {}
        for operation, times in self.operation_times.items():
            if times:
                insights[operation] = {
                    "count": len(times),
                    "average_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
        return insights

# Use performance plugin
logger = HydraLogger(enable_plugins=True)
performance_plugin = PerformancePlugin()
logger.add_plugin("performance", performance_plugin)

# Track operations
performance_plugin.start_operation("database_query")
logger.info("DB", "Query executed", extra={"operation": "database_query"})

performance_plugin.start_operation("api_call")
logger.info("API", "API call made", extra={"operation": "api_call"})

# Get performance insights
insights = logger.get_plugin_insights()
print(f"Performance insights: {insights}")
```

## Real-World Examples

### Web Application

```python
from hydra_logger import HydraLogger
from flask import Flask, request

app = Flask(__name__)

# Configure logger for web app
config = {
    "layers": {
        "WEB": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/web/requests.json", "format": "json"},
                {"type": "console", "level": "ERROR", "format": "plain-text"}
            ]
        },
        "AUTH": {
            "level": "WARNING",
            "destinations": [
                {"type": "file", "path": "logs/web/auth.log", "format": "syslog"}
            ]
        }
    }
}

logger = HydraLogger(config)

@app.route('/api/users')
def get_users():
    logger.info("WEB", "API request received", extra={
        "endpoint": "/api/users",
        "method": "GET",
        "ip": request.remote_addr
    })
    
    try:
        # Process request
        users = get_users_from_db()
        logger.info("WEB", "API request successful", extra={
            "endpoint": "/api/users",
            "user_count": len(users)
        })
        return {"users": users}
    except Exception as e:
        logger.error("WEB", "API request failed", extra={
            "endpoint": "/api/users",
            "error": str(e)
        })
        return {"error": "Internal server error"}, 500

@app.route('/login', methods=['POST'])
def login():
    logger.warning("AUTH", "Login attempt", extra={
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent')
    })
    
    # Process login
    return {"message": "Login successful"}
```

### Microservice

```python
from hydra_logger.async_hydra import AsyncHydraLogger
from hydra_logger.async_hydra.context import async_context, trace_context
import aiohttp

# Configure async logger for microservice
config = {
    "handlers": [
        {
            "type": "file",
            "filename": "logs/service.log",
            "format": "json"
        },
        {
            "type": "console",
            "format": "plain-text",
            "color_mode": "always"
        }
    ]
}

async def process_request(request_id: str, data: dict):
    async with AsyncHydraLogger(config) as logger:
        async with async_context(context_id=request_id):
            await logger.info("REQUEST", "Processing request", extra={
                "request_id": request_id,
                "data_size": len(str(data))
            })
            
            async with trace_context(trace_id=f"trace-{request_id}"):
                # Call external service
                async with aiohttp.ClientSession() as session:
                    async with session.post("http://external-service/api", json=data) as response:
                        result = await response.json()
                
                await logger.info("EXTERNAL", "External service called", extra={
                    "status_code": response.status,
                    "response_size": len(str(result))
                })
            
            await logger.info("REQUEST", "Request completed", extra={
                "request_id": request_id,
                "success": True
            })

# Usage
import asyncio
asyncio.run(process_request("req-123", {"user_id": 12345}))
```

### Data Processing Pipeline

```python
from hydra_logger import HydraLogger
from hydra_logger.data_protection import FallbackHandler
import pandas as pd

# Configure logger for data processing
config = {
    "layers": {
        "DATA": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/data/processing.csv", "format": "csv"}
            ]
        },
        "ERRORS": {
            "level": "ERROR",
            "destinations": [
                {"type": "file", "path": "logs/data/errors.log", "format": "json"}
            ]
        }
    }
}

logger = HydraLogger(config)
handler = FallbackHandler()

def process_data(data_file: str):
    try:
        # Load data
        logger.info("DATA", "Loading data file", extra={"file": data_file})
        df = pd.read_csv(data_file)
        
        # Process data
        logger.info("DATA", "Processing data", extra={
            "rows": len(df),
            "columns": len(df.columns)
        })
        
        # Save processed data
        processed_file = "processed_data.csv"
        handler.safe_write_csv(df.to_dict('records'), processed_file)
        
        logger.info("DATA", "Data processing completed", extra={
            "output_file": processed_file,
            "processed_rows": len(df)
        })
        
    except Exception as e:
        logger.error("ERRORS", "Data processing failed", extra={
            "file": data_file,
            "error": str(e)
        })
        raise

# Usage
process_data("input_data.csv")
```

### Background Worker

```python
from hydra_logger import HydraLogger
import time
import random

# Configure logger for background worker
config = {
    "layers": {
        "WORKER": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/worker/tasks.log", "format": "json"}
            ]
        },
        "PERFORMANCE": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/worker/performance.csv", "format": "csv"}
            ]
        }
    }
}

logger = HydraLogger(config)

def process_task(task_id: str, task_data: dict):
    start_time = time.time()
    
    logger.info("WORKER", "Starting task", extra={
        "task_id": task_id,
        "task_type": task_data.get("type")
    })
    
    try:
        # Simulate work
        time.sleep(random.uniform(0.1, 2.0))
        
        # Log performance
        duration = time.time() - start_time
        logger.info("PERFORMANCE", "Task completed", extra={
            "task_id": task_id,
            "duration_seconds": duration,
            "success": True
        })
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error("WORKER", "Task failed", extra={
            "task_id": task_id,
            "duration_seconds": duration,
            "error": str(e)
        })

# Simulate background worker
tasks = [
    {"id": "task-1", "data": {"type": "email"}},
    {"id": "task-2", "data": {"type": "report"}},
    {"id": "task-3", "data": {"type": "cleanup"}}
]

for task in tasks:
    process_task(task["id"], task["data"])
```

These examples demonstrate the full range of Hydra-Logger capabilities, from basic usage to advanced features like async logging, context management, security, and data protection. 