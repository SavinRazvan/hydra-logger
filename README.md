# 🐉 Hydra-Logger

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-white.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-146%20passed-darkgreen.svg)](https://github.com/SavinRazvan/hydra-logger)
[![Coverage](https://img.shields.io/badge/coverage-97%25-darkgreen.svg)](https://github.com/SavinRazvan/hydra-logger)
[![PyPI](https://img.shields.io/badge/PyPI-hydra--logger-darkblue.svg)](https://pypi.org/project/hydra-logger/)

A **dynamic, multi-headed logging system** for Python applications that supports custom folder paths, multi-layered logging, multiple log formats, and configuration via YAML/TOML files. Perfect for organizing logs by module, purpose, or severity level with structured output formats.

## ✨ Features

- 🎯 **Multi-layered Logging**: Route different types of logs to different destinations
- 📁 **Custom Folder Paths**: Specify custom folders for each log file (e.g., `logs/config/`, `logs/security/`)
- 🔄 **Multiple Destinations**: File and console output per layer with different log levels
- 📊 **Multiple Log Formats**: Support for text, structured JSON, CSV, Syslog, and GELF formats
- ⚙️ **Configuration Files**: YAML/TOML configuration support for easy deployment
- 🔄 **Backward Compatibility**: Works with existing `setup_logging()` code
- 📦 **File Rotation**: Configurable file sizes and backup counts
- 🚀 **Standalone Package**: Reusable across multiple projects
- 🧵 **Thread-Safe**: Safe for concurrent logging operations
- 🛡️ **Error Handling**: Graceful fallbacks and error recovery
- 📈 **Structured Logging**: JSON Lines format for log aggregation and analysis

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install hydra-logger

# Or install for development
git clone https://github.com/SavinRazvan/hydra-logger.git
cd hydra-logger

# Option 1: Install with pip (recommended)
pip install -e .

# Option 2: Install with conda
conda env create -f environment.yml
conda activate hydra-logger

# Option 3: Install with requirements files
pip install -r requirements.txt          # Core dependencies only
pip install -r requirements-dev.txt      # Development dependencies
```

### Basic Usage

```python
from hydra_logger import HydraLogger

# Simple usage with default configuration
logger = HydraLogger()
logger.info("DEFAULT", "Hello, Hydra-Logger!")

# Advanced usage with custom configuration and multiple formats
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

config = LoggingConfig(
    layers={
        "CONFIG": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/config/app.log",  # Custom folder!
                    max_size="5MB",
                    backup_count=3,
                    format="text"  # Plain text format
                ),
                LogDestination(
                    type="console",
                    level="WARNING",
                    format="json"  # Structured JSON format for console
                )
            ]
        ),
        "EVENTS": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/events/stream.json",  # Different folder!
                    max_size="10MB",
                    format="json"  # Structured JSON format for log aggregation
                )
            ]
        ),
        "ANALYTICS": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/analytics/metrics.csv",
                    format="csv"  # CSV format for data analysis
                )
            ]
        )
    }
)

logger = HydraLogger(config)
logger.info("CONFIG", "Configuration loaded")
logger.debug("EVENTS", "Event processed")
logger.info("ANALYTICS", "Performance metric recorded")
```

## 📊 Supported Log Formats

Hydra-Logger supports multiple log formats for different use cases:

### **Text Format** (Default)
Traditional plain text logging with timestamps and log levels.
```
2025-07-03 14:30:15 INFO [hydra.CONFIG] Configuration loaded (logger.py:483)
```

### **JSON Format** 
Structured JSON format for log aggregation and analysis. Each log entry is a valid JSON object.
```json
{"timestamp": "2025-07-03 14:30:15", "level": "INFO", "logger": "hydra.CONFIG", "message": "Configuration loaded", "filename": "logger.py", "lineno": 483}
```

### **CSV Format**
Comma-separated values for analytics and data processing.
```csv
timestamp,level,logger,message,filename,lineno
2025-07-03 14:30:15,INFO,hydra.CONFIG,Configuration loaded,logger.py,483
```

### **Syslog Format**
Standard syslog format for system integration.
```
<134>2025-07-03T14:30:15.123Z hostname hydra.CONFIG: Configuration loaded
```

### **GELF Format**
Graylog Extended Log Format for centralized logging systems.
```json
{"version": "1.1", "host": "hostname", "short_message": "Configuration loaded", "level": 6, "_logger": "hydra.CONFIG"}
```

## 📋 Configuration File Usage

Create `hydra_logging.yaml` (see `demos/examples/config_examples/` for more examples):

```yaml
layers:
  CONFIG:
    level: INFO
    destinations:
      - type: file
        path: "logs/config/app.log"
        max_size: "5MB"
        backup_count: 3
        format: text
      - type: console
        level: WARNING
        format: json
  
  EVENTS:
    level: DEBUG
    destinations:
      - type: file
        path: "logs/events/stream.json"
        max_size: "10MB"
        format: json
  
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: "logs/security/auth.log"
        max_size: "1MB"
        backup_count: 10
        format: syslog
  
  ANALYTICS:
    level: INFO
    destinations:
      - type: file
        path: "logs/analytics/metrics.csv"
        format: csv
```

Use the configuration:

```python
from hydra_logger import HydraLogger

logger = HydraLogger.from_config("hydra_logging.yaml")
logger.info("CONFIG", "Configuration loaded")
logger.debug("EVENTS", "Event processed")
logger.error("SECURITY", "Security alert")
```

## 🔄 Backward Compatibility

If you're migrating from the original `setup_logging()` function:

```python
from hydra_logger import setup_logging, migrate_to_hydra
import logging

# Option 1: Keep using the old interface
setup_logging(enable_file_logging=True, console_level=logging.INFO)

# Option 2: Migrate with custom path
logger = migrate_to_hydra(
    enable_file_logging=True,
    console_level=logging.INFO,
    log_file_path="logs/custom/app.log"  # Custom folder path!
)
```

## 🏗️ Advanced Configuration

### Multiple Destinations per Layer with Different Formats

```yaml
layers:
  API:
    level: INFO
    destinations:
      - type: file
        path: "logs/api/requests.json"
        max_size: "10MB"
        backup_count: 5
        format: json  # Structured logging for requests
      - type: file
        path: "logs/api/errors.log"
        max_size: "2MB"
        backup_count: 3
        format: text  # Plain text for errors
      - type: console
        level: ERROR
        format: gelf  # GELF format for console
```

### Different Log Levels per Layer

```yaml
layers:
  DEBUG_LAYER:
    level: DEBUG
    destinations:
      - type: file
        path: "logs/debug/detailed.log"
        format: text  # Plain text for debugging
  
  ERROR_LAYER:
    level: ERROR
    destinations:
      - type: file
        path: "logs/errors/critical.json"
        format: json  # JSON for error analysis
```

### Real-World Application Example

```python
# Web application with multiple modules and formats
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/app/main.log", format="text"),
                LogDestination(type="console", level="WARNING", format="json")
            ]
        ),
        "AUTH": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/auth/security.log", format="syslog"),
                LogDestination(type="file", path="logs/auth/errors.json", format="json")
            ]
        ),
        "API": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/api/requests.json", format="json"),
                LogDestination(type="file", path="logs/api/errors.log", format="text")
            ]
        ),
        "DB": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/database/queries.log", format="text")
            ]
        ),
        "PERF": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/performance/metrics.csv", format="csv")
            ]
        ),
        "MONITORING": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/monitoring/alerts.gelf", format="gelf")
            ]
        )
    }
)

logger = HydraLogger(config)

# Log from different modules
logger.info("APP", "Application started")
logger.debug("AUTH", "User login attempt: user123")
logger.info("API", "API request: GET /api/users")
logger.debug("DB", "SQL Query: SELECT * FROM users")
logger.info("PERF", "Response time: 150ms")
logger.info("MONITORING", "System health check completed")
```

## 📁 File Structure

After running the examples, you'll see logs organized in different folders:

```
logs/
├── app.log                    # Default logs
├── config/
│   └── app.log               # Configuration logs
├── events/
│   └── stream.json           # Event logs (JSON format)
├── security/
│   └── auth.log              # Security logs (Syslog format)
├── api/
│   ├── requests.json         # API request logs (JSON format)
│   └── errors.log            # API error logs (Text format)
├── database/
│   └── queries.log           # Database query logs (Text format)
└── performance/
    └── metrics.csv           # Performance logs (CSV format)
```

## 📚 API Reference

### HydraLogger

Main logging class for multi-layered logging.

#### Methods

- `__init__(config=None)`: Initialize with optional configuration
- `from_config(config_path)`: Create from configuration file
- `log(layer, level, message)`: Log message to specific layer
- `debug(layer, message)`: Log debug message
- `info(layer, message)`: Log info message
- `warning(layer, message)`: Log warning message
- `error(layer, message)`: Log error message
- `critical(layer, message)`: Log critical message
- `get_logger(layer)`: Get underlying logging.Logger

### Configuration Models

- `LoggingConfig`: Main configuration container
- `LogLayer`: Configuration for a single layer
- `LogDestination`: Configuration for a single destination

### Compatibility Functions

- `setup_logging()`: Original flexiai setup_logging function
- `migrate_to_hydra()`: Migration helper function

## 🧪 Examples

See the `demos/` directory for comprehensive examples:

- `demos/examples/basic_usage.py`: Different usage patterns and migration examples
- `demos/examples/log_formats_demo.py`: Demonstration of all supported formats
- `demos/multi_module_demo.py`: Real-world multi-module application demo
- `demos/multi_file_workflow_demo.py`: Complex workflow with multiple modules
- `demos/examples/config_examples/`: Various configuration examples

### Running Examples

```bash
# Run the basic usage examples
python demos/examples/basic_usage.py

# Run the log formats demonstration
python demos/examples/log_formats_demo.py

# Run the multi-module demo
python demos/multi_module_demo.py

# Run the multi-file workflow demo
python demos/multi_file_workflow_demo.py
```

## 🛠️ Development

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/SavinRazvan/hydra-logger.git
cd hydra-logger

# Option 1: Install with pip (recommended)
pip install -e .
pip install -r requirements-dev.txt

# Option 2: Install with conda
conda env create -f environment.yml
conda activate hydra-logger

# Option 3: Install with requirements files
pip install -r requirements.txt          # Core dependencies only
pip install -r requirements-dev.txt      # Development dependencies
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=hydra_logger --cov-report=term-missing

# Run specific test file
pytest tests/test_integration.py -v

# Run with HTML coverage report
pytest --cov=hydra_logger --cov-report=html
```

### Test Coverage

- **146 tests** covering all major functionality
- **97% code coverage** with comprehensive edge case testing
- **Thread safety, error handling, and integration tests** included
- **Format-specific tests** for all supported log formats

## 📦 Package Structure

```
hydra-logger/
├── 📋 Project Files
│   ├── README.md, LICENSE, pyproject.toml
│   ├── setup.py, requirements.txt, requirements-dev.txt
│   ├── environment.yml, .gitignore
│   ├── pytest.ini, .github/ (CI/CD workflows)
│   └── .github/ (CI/CD workflows)
│
├── 🏗️  Core Package (hydra_logger/)
│   ├── __init__.py          # Main package exports
│   ├── config.py            # Pydantic models & config loading
│   ├── logger.py            # Main HydraLogger class
│   ├── compatibility.py     # Backward compatibility layer
│   └── examples/            # Example configurations & usage
│       ├── basic_usage.py
│       ├── README.md
│       └── config_examples/
│           ├── simple.yaml
│           └── advanced.yaml
│
├── 🧪 Tests (tests/)
│   ├── test_config.py       # Config model tests
│   ├── test_logger.py       # Core logger tests
│   ├── test_compatibility.py # Backward compatibility tests
│   └── test_integration.py  # Integration & real-world tests
│
└── 📚 Demos (demos/)
    ├── examples/            # Basic examples and configurations
    ├── demo_modules/        # Module examples
    ├── multi_module_demo.py # Real-world multi-module demo
    └── multi_file_workflow_demo.py # Complex workflow demo
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](DEVELOPMENT.md#contributing) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🗺️ Roadmap

- [x] Multi-format logging support (text, JSON, CSV, syslog, GELF)
- [x] Structured JSON logging with all fields
- [x] Configuration file support (YAML/TOML)
- [x] Backward compatibility layer
- [x] Comprehensive test suite
- [ ] Remote logging destinations (syslog server, etc.)
- [ ] Log aggregation and analysis tools
- [ ] Performance monitoring integration
- [ ] Docker and Kubernetes deployment examples
- [ ] Web UI for log visualization
- [ ] Integration with popular logging frameworks

## 📝 Changelog

### 0.1.0 (Current)
- Initial release
- Multi-layered logging support
- Custom folder paths
- Multiple log formats (text, JSON, CSV, syslog, GELF)
- YAML/TOML configuration
- Backward compatibility
- Thread-safe logging
- Comprehensive test suite (97% coverage)
- Real-world examples and documentation
- Professional packaging and distribution

---

**Made with ❤️ by [Savin Ionut Razvan](https://github.com/SavinRazvan) for better logging organization**
