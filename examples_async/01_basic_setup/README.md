# Custom Async Logger Setup

## Overview
This example demonstrates how to properly initialize and customize Hydra-Logger's async logging capabilities with working file output, custom colors, and performance monitoring. It's the perfect starting point for understanding async logging fundamentals and customization.

## Key Features
- **Custom Configuration**: Proper async logger setup with multiple layers and destinations
- **Working File Logging**: File output with rotation and backup management
- **Custom Color Schemes**: Beautiful terminal output with custom colors
- **Performance Monitoring**: Built-in performance tracking and statistics
- **Multiple Log Layers**: Different log levels for different purposes
- **Concurrent Logging**: Shows how async logging handles multiple concurrent operations
- **Proper Cleanup**: Demonstrates correct shutdown procedures

## Prerequisites
- Python 3.7+ with asyncio support
- Hydra-Logger installed (`pip install hydra-logger`)

## Running the Example
```bash
python main.py
```

## Expected Output
```
🚀 Starting Custom Async Logger Example
============================================================
📁 Logs directory: /path/to/examples_async/01_basic_setup/logs
⚙️  Creating custom configuration...
   • APP layer: File + Console (INFO level)
   • DEBUG layer: File only (DEBUG level)
   • ERROR layer: File + Console (ERROR level)
   • SECURITY layer: File + Console (WARNING level)
   • PERFORMANCE layer: File only (INFO level)

✅ Async logger initialized successfully
📊 Performance monitoring: True
🔒 Sensitive data redaction: True
📦 Queue size: 2000
📦 Batch size: 100
⏱️  Batch timeout: 0.5s

📝 Testing all logging levels and layers:
🚀 Application started successfully
📁 Configuration loaded from config.yaml
🔗 Database connection established
❌ Database connection failed: Connection timeout
❌ API request failed: 500 Internal Server Error
🔐 User authentication attempt: john.doe@example.com
⚡ API response time: 45ms

📊 Performance Statistics:
📈 Total messages: 15
⏱️  Average processing time: 2.34ms
🚀 Messages per second: 32.15
❌ Total errors: 0
📊 Error rate: 0.00%
⏰ Uptime: 0.25s

🔄 Concurrent logging example:
✅ All concurrent messages logged

📈 Final message count: 25

📁 Checking log files:
✅ app.log: 2048 bytes
✅ debug.log: 1024 bytes
✅ error.log: 512 bytes
✅ security.log: 768 bytes
✅ performance.log: 256 bytes

🧹 Cleaning up...
✅ Async logger closed successfully

🎉 Custom async logger example completed!
============================================================
💡 Check the logs/ directory to see the generated log files
```

## Custom Configuration Guide

### 1. Creating Custom Configurations

The key to proper async logging is creating a custom `LoggingConfig` with specific layers and destinations:

```python
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def create_custom_config(logs_dir: str) -> LoggingConfig:
    return LoggingConfig(
        layers={
            "APP": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file", 
                        path=os.path.join(logs_dir, "app.log"), 
                        format="text",
                        max_size="5MB",
                        backup_count=3
                    ),
                    LogDestination(type="console", format="text")
                ]
            ),
            "DEBUG": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file", 
                        path=os.path.join(logs_dir, "debug.log"), 
                        format="json",
                        max_size="10MB",
                        backup_count=5
                    )
                ]
            )
        },
        default_level="INFO"
    )
```

### 2. Log Layer Design Patterns

#### APP Layer (General Application Logs)
```python
"APP": LogLayer(
    level="INFO",
    destinations=[
        LogDestination(type="file", path="logs/app.log", format="text"),
        LogDestination(type="console", format="text")
    ]
)
```

#### DEBUG Layer (Detailed Debug Information)
```python
"DEBUG": LogLayer(
    level="DEBUG",
    destinations=[
        LogDestination(type="file", path="logs/debug.log", format="json")
    ]
)
```

#### ERROR Layer (Error Messages)
```python
"ERROR": LogLayer(
    level="ERROR",
    destinations=[
        LogDestination(type="file", path="logs/error.log", format="json"),
        LogDestination(type="console", format="text")
    ]
)
```

#### SECURITY Layer (Security Events)
```python
"SECURITY": LogLayer(
    level="WARNING",
    destinations=[
        LogDestination(type="file", path="logs/security.log", format="json"),
        LogDestination(type="console", format="text")
    ]
)
```

#### PERFORMANCE Layer (Performance Metrics)
```python
"PERFORMANCE": LogLayer(
    level="INFO",
    destinations=[
        LogDestination(type="file", path="logs/performance.log", format="json")
    ]
)
```

### 3. Custom Color Schemes

Create beautiful terminal output with custom colors:

```python
class CustomColors:
    """Custom color scheme for the logger."""
    HEADER = "\033[95m"      # Purple
    BLUE = "\033[94m"        # Blue
    CYAN = "\033[96m"        # Cyan
    GREEN = "\033[92m"       # Green
    YELLOW = "\033[93m"      # Yellow
    RED = "\033[91m"         # Red
    BOLD = "\033[1m"         # Bold
    UNDERLINE = "\033[4m"    # Underline
    END = "\033[0m"          # End color

# Usage
print(f"{CustomColors.GREEN}✅ Success message{CustomColors.END}")
print(f"{CustomColors.RED}❌ Error message{CustomColors.END}")
```

### 4. Proper Async Logger Initialization

```python
# Ensure logs directory exists
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)

# Create custom configuration
config = create_custom_config(logs_dir)

# Initialize async logger with custom configuration
logger = AsyncHydraLogger(
    config=config,
    enable_performance_monitoring=True,
    redact_sensitive=True,
    queue_size=2000,
    batch_size=100,
    batch_timeout=0.5
)

# Wait for initialization
await asyncio.sleep(0.2)
```

## Configuration Parameters

### AsyncHydraLogger Parameters
- **`config`**: Custom LoggingConfig object
- **`enable_performance_monitoring`**: Track performance metrics (default: False)
- **`redact_sensitive`**: Automatically redact sensitive data (default: False)
- **`queue_size`**: Maximum number of messages in queue (default: 1000)
- **`batch_size`**: Number of messages to process in batch (default: 100)
- **`batch_timeout`**: Timeout for batch processing in seconds (default: 1.0)

### LogDestination Parameters
- **`type`**: "file", "console", "async_http", "async_database", "async_queue", "async_cloud"
- **`path`**: File path for file destinations
- **`format`**: "text", "json", "csv", "syslog", "gelf"
- **`max_size`**: Maximum file size for rotation (e.g., "5MB", "1GB")
- **`backup_count`**: Number of backup files to keep
- **`level`**: Logging level for this destination

## Logging Levels

### Standard Levels
- **`debug()`**: Detailed information for debugging
- **`info()`**: General information messages
- **`warning()`**: Warning messages for potential issues
- **`error()`**: Error messages for actual problems
- **`critical()`**: Critical errors requiring immediate attention

### Specialized Levels
- **`security()`**: Security-related events (authentication, authorization)
- **`audit()`**: Audit trail events (configuration changes, access logs)
- **`compliance()`**: Compliance-related events (data retention, privacy)

## Performance Monitoring

Access performance statistics:

```python
stats = await logger.get_async_performance_statistics()

if stats:
    print(f"Total messages: {stats.get('total_messages', 0)}")
    print(f"Average processing time: {stats.get('avg_processing_time', 0):.2f}ms")
    print(f"Messages per second: {stats.get('messages_per_second', 0):.2f}")
    print(f"Error rate: {stats.get('error_rate', 0):.2f}%")
```

## Concurrent Logging

Handle multiple concurrent operations:

```python
async def log_concurrent_message(i: int):
    await asyncio.sleep(0.01 * i)
    await logger.info("APP", f"Concurrent message {i}")

tasks = [log_concurrent_message(i) for i in range(10)]
await asyncio.gather(*tasks)
```

## Best Practices

### 1. Always Use Custom Configurations
```python
# ❌ Don't use default config
logger = AsyncHydraLogger()

# ✅ Use custom config
config = create_custom_config(logs_dir)
logger = AsyncHydraLogger(config=config)
```

### 2. Proper Directory Management
```python
# Ensure logs directory exists
logs_dir = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(logs_dir, exist_ok=True)
```

### 3. Wait for Initialization
```python
# Wait for logger to initialize
await asyncio.sleep(0.2)
```

### 4. Always Clean Up
```python
# Proper cleanup
await logger.close()
```

### 5. Check Log Files
```python
# Verify log files were created
for log_file in ["app.log", "debug.log", "error.log"]:
    file_path = os.path.join(logs_dir, log_file)
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {log_file}: {size} bytes")
```

## Troubleshooting

### Common Issues

1. **Log files not created**
   - Solution: Ensure logs directory exists and is writable
   - Check file permissions
   - Verify custom configuration is used

2. **Performance monitoring shows 0**
   - Solution: Enable performance monitoring in logger initialization
   - Wait for messages to be processed before checking stats

3. **Async logger not working**
   - Solution: Use custom configuration instead of default
   - Wait for proper initialization with `await asyncio.sleep(0.2)`

4. **Messages not appearing in files**
   - Solution: Check file paths in LogDestination configuration
   - Ensure proper file permissions
   - Wait for async processing to complete

### Performance Tips

1. **Queue Size**: Adjust based on message volume
2. **Batch Size**: Optimize for your use case
3. **Timeout**: Balance between latency and throughput
4. **File Rotation**: Set appropriate max_size and backup_count

## Use Cases

- **Development**: Custom async logging for development environments
- **Production**: High-performance logging with multiple destinations
- **Debugging**: Detailed debug logging with JSON format
- **Security**: Dedicated security event logging
- **Performance**: Performance metrics collection

## Next Steps

After understanding this example, explore:
1. **02_console_only/**: Console-only async logging
2. **03_file_only/**: File-only async logging
3. **04_simple_config/**: Basic configuration examples
4. **07_performance_monitoring/**: Advanced performance monitoring 