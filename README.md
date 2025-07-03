# 🐉 Hydra-Logger

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen.svg)](https://github.com/SavinRazvan/hydra-logger)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)](https://github.com/SavinRazvan/hydra-logger)
[![PyPI](https://img.shields.io/badge/PyPI-hydra--logger-blue.svg)](https://pypi.org/project/hydra-logger/)

A **dynamic, multi-headed logging system** for Python applications that supports custom folder paths, multi-layered logging, and configuration via YAML/TOML files. Perfect for organizing logs by module, purpose, or severity level.

## ✨ Features

- 🎯 **Multi-layered Logging**: Route different types of logs to different destinations
- 📁 **Custom Folder Paths**: Specify custom folders for each log file (e.g., `logs/config/`, `logs/security/`)
- 🔄 **Multiple Destinations**: File and console output per layer with different log levels
- ⚙️ **Configuration Files**: YAML/TOML configuration support for easy deployment
- 🔄 **Backward Compatibility**: Works with existing `setup_logging()` code
- 📦 **File Rotation**: Configurable file sizes and backup counts
- 🚀 **Standalone Package**: Reusable across multiple projects
- 🧵 **Thread-Safe**: Safe for concurrent logging operations
- 🛡️ **Error Handling**: Graceful fallbacks and error recovery

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install hydra-logger

# Or install for development
git clone https://github.com/SavinRazvan/hydra-logger.git
cd hydra-logger
pip install -e .
```

### Basic Usage

```python
from hydra_logger import HydraLogger

# Simple usage with default configuration
logger = HydraLogger()
logger.info("DEFAULT", "Hello, Hydra-Logger!")

# Advanced usage with custom configuration
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
                    backup_count=3
                ),
                LogDestination(
                    type="console",
                    level="WARNING"
                )
            ]
        ),
        "EVENTS": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/events/stream.log",  # Different folder!
                    max_size="10MB"
                )
            ]
        )
    }
)

logger = HydraLogger(config)
logger.info("CONFIG", "Configuration loaded")
logger.debug("EVENTS", "Event processed")
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
      - type: console
        level: WARNING
  
  EVENTS:
    level: DEBUG
    destinations:
      - type: file
        path: "logs/events/stream.log"
        max_size: "10MB"
  
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: "logs/security/auth.log"
        max_size: "1MB"
        backup_count: 10
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

### Multiple Destinations per Layer

```yaml
layers:
  API:
    level: INFO
    destinations:
      - type: file
        path: "logs/api/requests.log"
        max_size: "10MB"
        backup_count: 5
      - type: file
        path: "logs/api/errors.log"
        max_size: "2MB"
        backup_count: 3
      - type: console
        level: ERROR
```

### Different Log Levels per Layer

```yaml
layers:
  DEBUG_LAYER:
    level: DEBUG
    destinations:
      - type: file
        path: "logs/debug/detailed.log"
  
  ERROR_LAYER:
    level: ERROR
    destinations:
      - type: file
        path: "logs/errors/critical.log"
```

### Real-World Application Example

```python
# Web application with multiple modules
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/app/main.log"),
                LogDestination(type="console", level="WARNING")
            ]
        ),
        "AUTH": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/auth/security.log"),
                LogDestination(type="file", path="logs/auth/errors.log")
            ]
        ),
        "API": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/api/requests.log"),
                LogDestination(type="file", path="logs/api/errors.log")
            ]
        ),
        "DB": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/database/queries.log")
            ]
        ),
        "PERF": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/performance/metrics.log")
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
```

## 📁 File Structure

After running the examples, you'll see logs organized in different folders:

```
logs/
├── app.log                    # Default logs
├── config/
│   └── app.log               # Configuration logs
├── events/
│   └── stream.log            # Event logs
├── security/
│   └── auth.log              # Security logs
├── api/
│   ├── requests.log          # API request logs
│   └── errors.log            # API error logs
├── database/
│   └── queries.log           # Database query logs
└── performance/
    └── metrics.log           # Performance logs
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

See the `examples/` directory for comprehensive examples:

- `examples/multi_module_demo.py`: Real-world multi-module application demo
- `hydra_logger/examples/basic_usage.py`: Different usage patterns
- `hydra_logger/examples/config_examples/simple.yaml`: Basic configuration
- `hydra_logger/examples/config_examples/advanced.yaml`: Advanced configuration

### Running Examples

```bash
# Run the multi-module demo
python examples/multi_module_demo.py

# Run basic usage examples
python hydra_logger/examples/basic_usage.py
```

## 🛠️ Development

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/SavinRazvan/hydra-logger.git
cd hydra-logger

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
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

- **50 tests** covering all major functionality
- **96% code coverage** (204 lines, only 8 missing)
- **Comprehensive edge case testing** including thread safety, error handling, and integration tests

## 📦 Package Structure

```
hydra-logger/
├── 📋 Project Files
│   ├── README.md, LICENSE, pyproject.toml
│   ├── setup.py, requirements.txt, requirements-dev.txt
│   ├── pytest.ini, .gitignore
│   ├── PACKAGING.md, DEVELOPMENT.md
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
└── 📚 Examples
    └── multi_module_demo.py # Real-world multi-module demo
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

- [ ] JSON configuration support
- [ ] Remote logging destinations (syslog, etc.)
- [ ] Structured logging with JSON output
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
- YAML/TOML configuration
- Backward compatibility
- Thread-safe logging
- Comprehensive test suite (96% coverage)
- Real-world examples and documentation
- Professional packaging and distribution

---

**Made with ❤️ by [Savin Ionut Razvan](https://github.com/SavinRazvan) for better logging organization**
