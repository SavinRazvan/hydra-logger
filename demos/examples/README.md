# 🧪 Hydra-Logger Examples

This directory contains comprehensive examples and configuration files demonstrating how to use the Hydra-Logger system effectively.

## 📁 Directory Structure

```
hydra_logger/examples/
├── README.md                    # This file
├── basic_usage.py              # Comprehensive usage examples
└── config_examples/
    ├── simple.yaml             # Basic configuration example
    └── advanced.yaml           # Advanced configuration example
```

## 📋 Example Files

### `basic_usage.py`
A comprehensive example demonstrating four different usage patterns:

1. **Backward Compatible Usage** (`example_1_backward_compatible()`)
   - Same interface as the original `setup_logging()` from flexiai
   - Uses standard Python logging module
   - Creates `logs/app.log` with console output

2. **Migration Path** (`example_2_migration_path()`)
   - Easy migration with custom log file paths
   - Demonstrates `migrate_to_hydra()` function
   - Creates logs in custom folder structure

3. **Multi-layered Logging** (`example_3_multi_layered()`)
   - Advanced usage with different layers and destinations
   - Shows CONFIG, EVENTS, and SECURITY layers
   - Demonstrates custom folder paths and multiple destinations

4. **Configuration File** (`example_4_config_file()`)
   - Loading from YAML configuration files
   - Uses the advanced configuration example
   - Shows how to load external configurations

### Configuration Examples

#### `config_examples/simple.yaml`
Basic configuration demonstrating:
- **DEFAULT layer**: Standard file and console output
- **CONFIG layer**: Configuration logs in `logs/config/app.log`
- **EVENTS layer**: Event logs in `logs/events/stream.log`
- Simple folder structure with basic file rotation

#### `config_examples/advanced.yaml`
Advanced configuration showcasing:
- **Multiple specialized layers**: CONFIG, EVENTS, SECURITY, DATABASE, API, PERFORMANCE
- **Complex folder structures**: Each layer has its own dedicated folder
- **Multiple destinations per layer**: Some layers write to multiple files
- **Varied configurations**: Different file sizes, backup counts, and log levels
- **Real-world scenarios**: API errors separate from regular requests

## 🚀 Running the Examples

### Quick Start
```bash
# Run all examples at once
python hydra_logger/examples/basic_usage.py
```

### Individual Examples
```python
from hydra_logger.examples.basic_usage import (
    example_1_backward_compatible,
    example_2_migration_path,
    example_3_multi_layered,
    example_4_config_file
)

# Run specific examples
example_1_backward_compatible()
example_2_migration_path()
example_3_multi_layered()
example_4_config_file()
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

After running the examples, you'll see logs organized in different folders:

```
logs/
├── app.log                    # Default logs (backward compatible)
├── custom/
│   └── app.log               # Migration example logs
├── config/
│   └── app.log               # Configuration logs
├── events/
│   ├── stream.log            # Event logs
│   └── archive.log           # Event archive (advanced config)
├── security/
│   └── auth.log              # Security logs
├── database/
│   └── queries.log           # Database logs
├── api/
│   ├── requests.log          # API request logs
│   └── errors.log            # API error logs
└── performance/
    └── metrics.log           # Performance logs
```

## 🎯 Key Features Demonstrated

### 1. **Custom Folder Paths**
Each layer can have its own folder structure:
```python
"CONFIG": LogLayer(
    destinations=[LogDestination(path="logs/config/app.log")]
)
"EVENTS": LogLayer(
    destinations=[LogDestination(path="logs/events/stream.log")]
)
```

### 2. **Multiple Destinations**
File and console output per layer with different log levels:
```python
destinations=[
    LogDestination(type="file", path="logs/api/requests.log"),
    LogDestination(type="file", path="logs/api/errors.log"),
    LogDestination(type="console", level="ERROR")
]
```

### 3. **Different Log Levels**
Each layer can have different logging levels:
```yaml
CONFIG:
  level: INFO
EVENTS:
  level: DEBUG
SECURITY:
  level: ERROR
```

### 4. **File Rotation**
Configurable file sizes and backup counts:
```yaml
max_size: "10MB"
backup_count: 5
```

### 5. **Backward Compatibility**
Works seamlessly with existing `setup_logging()` code:
```python
setup_logging(enable_file_logging=True, console_level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Works exactly like before!")
```

## 🔧 Configuration Examples Explained

### Simple Configuration
The `simple.yaml` shows basic multi-layered logging:
- **DEFAULT**: General application logs
- **CONFIG**: Configuration-specific logs in separate folder
- **EVENTS**: Event logs with higher file size limits

### Advanced Configuration
The `advanced.yaml` demonstrates enterprise-level logging:
- **Multiple file destinations**: Some layers write to multiple files
- **Specialized folders**: Each module has its own folder
- **Error separation**: API errors separate from regular requests
- **Archiving**: Event logs have archive files for long-term storage
- **Performance monitoring**: Dedicated performance metrics logging

## 📚 Next Steps

1. **Run the examples** to see Hydra-Logger in action
2. **Modify configurations** to match your project structure
3. **Check the main README.md** for complete API documentation
4. **Explore the test suite** for more usage patterns
5. **Try the multi-module demo** in the root `examples/` directory

## 🤝 Contributing Examples

We welcome new examples! When contributing:
1. Follow the existing structure and naming conventions
2. Include clear comments explaining the example
3. Add corresponding configuration files if needed
4. Update this README to document new examples
5. Ensure examples work with the current version

---

**For complete documentation, see the main [README.md](../../README.md)** 