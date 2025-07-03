# 🧪 Hydra-Logger Examples

This directory contains comprehensive examples and configuration files demonstrating how to use the Hydra-Logger system effectively, including all supported log formats.

## 📁 Directory Structure

```
hydra_logger/examples/
├── README.md                    # This file
├── basic_usage.py              # Comprehensive usage examples with formats
├── log_formats_demo.py         # Dedicated log formats demonstration
└── config_examples/
    ├── simple.yaml             # Basic configuration example with formats
    └── advanced.yaml           # Advanced configuration example with formats
```

## 📋 Example Files

### `basic_usage.py`
A comprehensive example demonstrating five different usage patterns:

1. **Backward Compatible Usage** (`example_1_backward_compatible()`)
   - Same interface as the original `setup_logging()` from flexiai
   - Uses standard Python logging module
   - Creates `logs/app.log` with console output

2. **Migration Path** (`example_2_migration_path()`)
   - Easy migration with custom log file paths
   - Demonstrates `migrate_to_hydra()` function
   - Creates logs in custom folder structure

3. **Multi-layered Logging with Formats** (`example_3_multi_layered()`)
   - Advanced usage with different layers, destinations, and formats
   - Shows CONFIG (text), EVENTS (JSON), SECURITY (syslog), ANALYTICS (CSV), MONITORING (GELF)
   - Demonstrates custom folder paths and multiple destinations with different formats

4. **Configuration File** (`example_4_config_file()`)
   - Loading from YAML configuration files
   - Uses the advanced configuration example
   - Shows how to load external configurations

5. **Log Format Demonstration** (`example_5_format_demonstration()`)
   - Shows all supported log formats side by side
   - Creates separate files for each format (text, JSON, CSV, syslog, GELF)
   - Demonstrates format differences with the same log messages

### `log_formats_demo.py`
A dedicated demonstration of all supported log formats:
- **Text format**: Traditional plain text logging
- **JSON format**: Structured logging for analysis
- **CSV format**: Comma-separated values for analytics
- **Syslog format**: System integration format
- **GELF format**: Graylog Extended Log Format for centralized logging

This demo shows how the same log messages appear in different formats and explains their use cases.

### Configuration Examples

#### `config_examples/simple.yaml`
Basic configuration demonstrating:
- **DEFAULT layer**: Standard file and console output (text format)
- **CONFIG layer**: Configuration logs in `logs/config/app.log` (text format)
- **EVENTS layer**: Event logs in `logs/events/stream.json` (JSON format)
- Simple folder structure with basic file rotation and format examples

#### `config_examples/advanced.yaml`
Advanced configuration showcasing:
- **Multiple specialized layers**: CONFIG, EVENTS, SECURITY, DATABASE, API, PERFORMANCE, MONITORING
- **Complex folder structures**: Each layer has its own dedicated folder
- **Multiple destinations per layer**: Some layers write to multiple files
- **Different log formats**: text, JSON, CSV, syslog, and GELF formats
- **Varied configurations**: Different file sizes, backup counts, and log levels
- **Real-world scenarios**: API errors separate from regular requests, performance metrics in CSV

## 🚀 Running the Examples

### Quick Start
```bash
# Run all basic examples at once
python hydra_logger/examples/basic_usage.py

# Run the dedicated log formats demo
python hydra_logger/examples/log_formats_demo.py
```

### Individual Examples
```python
from hydra_logger.examples.basic_usage import (
    example_1_backward_compatible,
    example_2_migration_path,
    example_3_multi_layered,
    example_4_config_file,
    example_5_format_demonstration
)

# Run specific examples
example_1_backward_compatible()
example_2_migration_path()
example_3_multi_layered()
example_4_config_file()
example_5_format_demonstration()
```

### Using Configuration Files
```python
from hydra_logger import HydraLogger

# Load from simple config
logger = HydraLogger.from_config("hydra_logger/examples/config_examples/simple.yaml")

# Load from advanced config
logger = HydraLogger.from_config("hydra_logger/examples/config_examples/advanced.yaml")

# Use the logger
logger.info("CONFIG", "Configuration loaded successfully")
logger.debug("EVENTS", "Event stream started")
logger.error("SECURITY", "Authentication failed")
```

## 📁 Expected Output Structure

After running the examples, you'll see logs organized in different folders with various formats:

```
logs/
├── app.log                    # Default logs (backward compatible, text format)
├── custom/
│   └── app.log               # Migration example logs (text format)
├── config/
│   └── app.log               # Configuration logs (text format)
├── events/
│   ├── stream.json           # Event logs (JSON format)
│   └── archive.csv           # Event archive (CSV format)
├── security/
│   └── auth.log              # Security logs (syslog format)
├── database/
│   └── queries.log           # Database logs (text format)
├── api/
│   ├── requests.json         # API request logs (JSON format)
│   └── errors.log            # API error logs (text format)
├── performance/
│   └── metrics.csv           # Performance logs (CSV format)
├── monitoring/
│   └── alerts.gelf           # Monitoring logs (GELF format)
└── formats/                  # Log formats demo output
    ├── text.log              # Text format example
    ├── json.log              # JSON format example
    ├── csv.log               # CSV format example
    ├── syslog.log            # Syslog format example
    └── gelf.log              # GELF format example
```

## 🎯 Key Features Demonstrated

### 1. **Multiple Log Formats**
Each destination can specify its own format:
```python
"API": LogLayer(
    destinations=[
        LogDestination(path="logs/api/requests.json", format="json"),
        LogDestination(path="logs/api/errors.log", format="text")
    ]
)
"PERFORMANCE": LogLayer(
    destinations=[LogDestination(path="logs/performance/metrics.csv", format="csv")]
)
```

### 2. **Custom Folder Paths**
Each layer can have its own folder structure:
```python
"CONFIG": LogLayer(
    destinations=[LogDestination(path="logs/config/app.log")]
)
"EVENTS": LogLayer(
    destinations=[LogDestination(path="logs/events/stream.json")]
)
```

### 3. **Multiple Destinations**
File and console output per layer with different log levels and formats:
```python
destinations=[
    LogDestination(type="file", path="logs/api/requests.json", format="json"),
    LogDestination(type="file", path="logs/api/errors.log", format="text"),
    LogDestination(type="console", level="ERROR", format="json")
]
```

### 4. **Different Log Levels**
Each layer can have different logging levels:
```yaml
CONFIG:
  level: INFO
EVENTS:
  level: DEBUG
SECURITY:
  level: ERROR
```

### 5. **File Rotation**
Configurable file sizes and backup counts:
```yaml
max_size: "10MB"
backup_count: 5
```

### 6. **Backward Compatibility**
Works seamlessly with existing `setup_logging()` code:
```python
setup_logging(enable_file_logging=True, console_level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Works exactly like before!")
```

## 📊 Supported Log Formats

Hydra-Logger supports multiple log formats for different use cases:

- **`text`** (default): Plain text format with timestamps and log levels
- **`json`**: Structured JSON format for log aggregation and analysis
- **`csv`**: Comma-separated values for analytics and data processing
- **`syslog`**: Syslog format for system integration
- **`gelf`**: Graylog Extended Log Format for centralized logging

Each destination can specify its own format, allowing you to mix formats within the same application.

## 🔧 Configuration Examples Explained

### Simple Configuration
The `simple.yaml` shows basic multi-layered logging with format examples:
- **DEFAULT**: General application logs (text format)
- **CONFIG**: Configuration-specific logs in separate folder (text format)
- **EVENTS**: Event logs with JSON format for structured logging

### Advanced Configuration
The `advanced.yaml` demonstrates enterprise-level logging with multiple formats:
- **Multiple file destinations**: Some layers write to multiple files
- **Specialized folders**: Each module has its own folder
- **Different formats**: text, JSON, CSV, syslog, and GELF formats
- **Error separation**: API errors separate from regular requests
- **Archiving**: Event logs have archive files for long-term storage
- **Performance monitoring**: Dedicated performance metrics logging in CSV format
- **Centralized monitoring**: GELF format for centralized logging systems

## 📚 Next Steps

1. **Run the examples** to see Hydra-Logger in action
2. **Try the log formats demo** to understand format differences
3. **Modify configurations** to match your project structure
4. **Check the main README.md** for complete API documentation
5. **Explore the test suite** for more usage patterns
6. **Try the multi-module demo** in the root `examples/` directory

## 🤝 Contributing Examples

We welcome new examples! When contributing:
1. Follow the existing structure and naming conventions
2. Include clear comments explaining the example
3. Demonstrate format usage when appropriate
4. Show real-world use cases for different formats 