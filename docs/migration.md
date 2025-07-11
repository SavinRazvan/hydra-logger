# Migration Guide

This comprehensive guide helps you migrate from existing logging systems to Hydra-Logger, including support for multiple log formats and advanced configuration options.

## Table of Contents

- [Migration Overview](#migration-overview)
- [Migrating from Standard Python Logging](#migrating-from-standard-python-logging)
- [Migrating from Custom Logging Functions](#migrating-from-custom-logging-functions)
- [Migrating from Multiple Loggers](#migrating-from-multiple-loggers)
- [Migrating from Configuration Files](#migrating-from-configuration-files)
- [Migrating from Other Logging Libraries](#migrating-from-other-logging-libraries)
- [Advanced Migration Strategies](#advanced-migration-strategies)
- [Testing Migration](#testing-migration)
- [Troubleshooting](#troubleshooting)

## Migration Overview

Hydra-Logger provides multiple migration paths to help you transition from existing logging systems:

### Migration Benefits
- **Multi-layered logging**: Route different types of logs to different destinations
- **Multiple formats**: Support for plain-text, JSON, CSV, syslog, and GELF formats
- **Better organization**: Separate logs by functionality or concern
- **Enhanced performance**: Optimized for high-throughput logging
- **Enterprise features**: File rotation, custom paths, and format support

### Migration Strategies
1. **Gradual Migration**: Migrate one component at a time
2. **Complete Replacement**: Replace entire logging system at once
3. **Hybrid Approach**: Use both systems during transition period
4. **Configuration Migration**: Convert existing configuration files

## Migrating from Standard Python Logging

### Current Code

```python
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Use logging
logger = logging.getLogger(__name__)
logger.info("Application started")
logger.error("An error occurred")
logger.debug("Debug information")
```

### Simple Migration

```python
from hydra_logger import HydraLogger

# Create logger with default configuration
logger = HydraLogger()

# Use the new API
logger.info("Application started", "DEFAULT")
logger.error("An error occurred", "DEFAULT")
logger.debug("Debug information", "DEFAULT")
```

### Advanced Migration with Multiple Formats

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create configuration with multiple formats
config = LoggingConfig(
    default_level="INFO",
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="plain-text",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    format="json"
                )
            ]
        ),
        "DEBUG": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/debug.log",
                    format="plain-text"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Use different layers
logger.info("Application started", "DEFAULT")
logger.error("An error occurred", "DEFAULT")
logger.debug("Debug information", "DEBUG")
```

## Migrating from Custom Logging Functions

### Current Code

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(enable_file_logging=True, console_level=logging.INFO):
    """Setup logging configuration."""
    handlers = []
    
    if enable_file_logging:
        file_handler = RotatingFileHandler(
            'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handlers.append(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    handlers.append(console_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )

# Usage
setup_logging(enable_file_logging=True, console_level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.info("Application started")
```

### Migration Options

#### Option 1: Use Migration Function

```python
from hydra_logger import migrate_to_hydra
import logging

# Direct migration with same parameters
logger = migrate_to_hydra(
    enable_file_logging=True,
    console_level=logging.WARNING,
    log_file_path="app.log",
    max_size="10MB",
    backup_count=5
)

# Use the new API
logger.info("Application started", "DEFAULT")
```

#### Option 2: Create Equivalent Configuration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create equivalent configuration
config = LoggingConfig(
    default_level="INFO",
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="app.log",
                    format="plain-text",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    level="WARNING",
                    format="plain-text"
                )
            ]
        )
    }
)

logger = HydraLogger(config)
logger.info("Application started", "DEFAULT")
```

## Migrating from Multiple Loggers

### Current Code

```python
import logging

# Multiple loggers for different components
app_logger = logging.getLogger("app")
api_logger = logging.getLogger("api")
db_logger = logging.getLogger("database")

# Configure each logger separately
app_handler = logging.FileHandler("logs/app.log")
api_handler = logging.FileHandler("logs/api.log")
db_handler = logging.FileHandler("logs/database.log")

app_logger.addHandler(app_handler)
api_logger.addHandler(api_handler)
db_logger.addHandler(db_handler)

# Usage
app_logger.info("Application started")
api_logger.info("API request received")
db_logger.info("Database query executed")
```

### Migration to Hydra-Logger

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create configuration with multiple layers
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="plain-text"
                )
            ]
        ),
        "API": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/api.log",
                    format="json"
                )
            ]
        ),
        "DATABASE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/database.log",
                    format="plain-text"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Use different layers for different components
logger.info("Application started", "APP")
logger.info("API request received", "API")
logger.info("Database query executed", "DATABASE")
```

## Migrating from Configuration Files

### Current Logging Configuration

```python
# logging.conf
[loggers]
keys=root,app,api,database

[handlers]
keys=consoleHandler,fileHandler,apiHandler,dbHandler

[formatters]
keys=normalFormatter,jsonFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_app]
level=INFO
handlers=fileHandler
qualname=app
propagate=0

[logger_api]
level=INFO
handlers=apiHandler
qualname=api
propagate=0

[logger_database]
level=INFO
handlers=dbHandler
qualname=database
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=normalFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=normalFormatter
args=('logs/app.log', 'a')

[handler_apiHandler]
class=FileHandler
level=INFO
formatter=jsonFormatter
args=('logs/api.log', 'a')

[handler_dbHandler]
class=FileHandler
level=INFO
formatter=normalFormatter
args=('logs/database.log', 'a')

[formatter_normalFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_jsonFormatter]
format={"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}
```

### Migration to Hydra-Logger Configuration

```yaml
# hydra_logging.yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        format: plain-text
      - type: console
        format: plain-text
  
  API:
    level: INFO
    destinations:
      - type: file
        path: logs/api.log
        format: json
  
  DATABASE:
    level: INFO
    destinations:
      - type: file
        path: logs/database.log
        format: plain-text
```

### Usage

```python
from hydra_logger import HydraLogger

# Load configuration from file
logger = HydraLogger.from_config("hydra_logging.yaml")

# Use the new API
logger.info("Application started", "APP")
logger.info("API request received", "API")
logger.info("Database query executed", "DATABASE")
```

## Migrating from Other Logging Libraries

### Migrating from Loguru

#### Current Loguru Code

```python
from loguru import logger

# Configure loguru
logger.add("logs/app.log", rotation="10 MB", retention="1 week")
logger.add("logs/error.log", level="ERROR", rotation="5 MB")

# Usage
logger.info("Application started")
logger.error("An error occurred")
logger.debug("Debug information")
```

#### Migration to Hydra-Logger

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create equivalent configuration
config = LoggingConfig(
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="plain-text",
                    max_size="10MB",
                    backup_count=7  # 1 week retention
                ),
                LogDestination(
                    type="console",
                    format="plain-text"
                )
            ]
        ),
        "ERROR": LogLayer(
            level="ERROR",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/error.log",
                    format="plain-text",
                    max_size="5MB",
                    backup_count=7
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Use the new API
logger.info("Application started", "DEFAULT")
logger.error("An error occurred", "ERROR")
logger.debug("Debug information", "DEFAULT")
```

### Migrating from Structlog

#### Current Structlog Code

```python
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info("Application started", user_id=123, action="login")
logger.error("An error occurred", error_code=500, user_id=123)
```

#### Migration to Hydra-Logger

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create configuration with JSON format
config = LoggingConfig(
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.json",
                    format="json"
                ),
                LogDestination(
                    type="console",
                    format="json"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Use the new API with structured data
logger.info("Application started", "DEFAULT", extra={"user_id": 123, "action": "login"})
logger.error("An error occurred", "DEFAULT", extra={"error_code": 500, "user_id": 123})
```

## Advanced Migration Strategies

### Gradual Migration Strategy

```python
from hydra_logger import HydraLogger
import logging

class HybridLogger:
    """Hybrid logger for gradual migration."""
    
    def __init__(self, hydra_config=None):
        self.hydra_logger = HydraLogger(hydra_config) if hydra_config else None
        self.legacy_logger = logging.getLogger(__name__)
    
    def info(self, message, layer="DEFAULT", **kwargs):
        """Log info message to both systems."""
        if self.hydra_logger:
            self.hydra_logger.info(message, layer, **kwargs)
        else:
            self.legacy_logger.info(message)
    
    def error(self, message, layer="DEFAULT", **kwargs):
        """Log error message to both systems."""
        if self.hydra_logger:
            self.hydra_logger.error(message, layer, **kwargs)
        else:
            self.legacy_logger.error(message)
    
    def migrate_to_hydra(self, config):
        """Complete migration to Hydra-Logger."""
        self.hydra_logger = HydraLogger(config)
        return self.hydra_logger

# Usage for gradual migration
hybrid_logger = HybridLogger()

# Use legacy logging initially
hybrid_logger.info("Application started")

# Later, migrate to Hydra-Logger
config = LoggingConfig(layers={...})
hydra_logger = hybrid_logger.migrate_to_hydra(config)
```

### Configuration Migration Tool

```python
import yaml
import json
from pathlib import Path
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

class ConfigMigrator:
    """Migrate logging configurations to Hydra-Logger format."""
    
    def migrate_logging_conf(self, conf_path: str) -> LoggingConfig:
        """Migrate Python logging.conf to Hydra-Logger config."""
        # Parse logging.conf and convert to Hydra-Logger format
        # Implementation would parse the INI-style config
        pass
    
    def migrate_loguru_config(self, config_dict: dict) -> LoggingConfig:
        """Migrate Loguru configuration to Hydra-Logger config."""
        layers = {}
        
        # Convert Loguru sinks to Hydra-Logger destinations
        for sink_name, sink_config in config_dict.get("sinks", {}).items():
            layer_name = sink_name.upper()
            
            destinations = []
            if "file" in sink_config:
                destinations.append(LogDestination(
                    type="file",
                    path=sink_config["file"],
                    format="json" if sink_config.get("serialize") else "plain-text"
                ))
            
            if "console" in sink_config:
                destinations.append(LogDestination(
                    type="console",
                    format="json" if sink_config.get("serialize") else "plain-text"
                ))
            
            layers[layer_name] = LogLayer(
                level=sink_config.get("level", "INFO"),
                destinations=destinations
            )
        
        return LoggingConfig(layers=layers)
    
    def migrate_structlog_config(self, config_dict: dict) -> LoggingConfig:
        """Migrate Structlog configuration to Hydra-Logger config."""
        # Convert Structlog processors to Hydra-Logger format
        # Implementation would map processors to Hydra-Logger features
        pass

# Usage
migrator = ConfigMigrator()

# Migrate Loguru config
loguru_config = {
    "sinks": {
        "app": {"file": "logs/app.log", "serialize": True},
        "console": {"console": True, "serialize": False}
    }
}

hydra_config = migrator.migrate_loguru_config(loguru_config)
logger = HydraLogger(hydra_config)
```

## Testing Migration

### Migration Testing Strategy

```python
import pytest
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

class MigrationTester:
    """Test migration from legacy logging to Hydra-Logger."""
    
    def __init__(self, legacy_logger, hydra_logger):
        self.legacy_logger = legacy_logger
        self.hydra_logger = hydra_logger
        self.test_results = []
    
    def test_basic_logging(self):
        """Test basic logging functionality."""
        test_message = "Test message"
        
        # Test legacy logger
        self.legacy_logger.info(test_message)
        
        # Test Hydra-Logger
        self.hydra_logger.info(test_message, "DEFAULT")
        
        # Compare outputs (implementation would check log files)
        return True
    
    def test_log_levels(self):
        """Test all log levels."""
        levels = ["debug", "info", "warning", "error", "critical"]
        
        for level in levels:
            test_message = f"Test {level} message"
            
            # Test legacy logger
            getattr(self.legacy_logger, level)(test_message)
            
            # Test Hydra-Logger
            getattr(self.hydra_logger, level)(test_message, "DEFAULT")
        
        return True
    
    def test_structured_logging(self):
        """Test structured logging capabilities."""
        structured_data = {"user_id": 123, "action": "test"}
        
        # Test Hydra-Logger structured logging
        self.hydra_logger.info("Structured test", "DEFAULT", extra=structured_data)
        
        return True
    
    def run_all_tests(self):
        """Run all migration tests."""
        tests = [
            self.test_basic_logging,
            self.test_log_levels,
            self.test_structured_logging
        ]
        
        for test in tests:
            try:
                result = test()
                self.test_results.append({"test": test.__name__, "passed": result})
            except Exception as e:
                self.test_results.append({"test": test.__name__, "passed": False, "error": str(e)})
        
        return self.test_results

# Usage
import logging
legacy_logger = logging.getLogger("test")
hydra_logger = HydraLogger()

tester = MigrationTester(legacy_logger, hydra_logger)
results = tester.run_all_tests()

for result in results:
    status = "PASS" if result["passed"] else "FAIL"
    print(f"{result['test']}: {status}")
```

### Performance Testing

```python
import time
import statistics
from hydra_logger import HydraLogger

class PerformanceTester:
    """Test performance of Hydra-Logger vs legacy logging."""
    
    def __init__(self, legacy_logger, hydra_logger):
        self.legacy_logger = legacy_logger
        self.hydra_logger = hydra_logger
    
    def benchmark_logging(self, iterations: int = 10000) -> dict:
        """Benchmark logging performance."""
        results = {
            "legacy": [],
            "hydra": []
        }
        
        # Test legacy logger
        start_time = time.time()
        for i in range(iterations):
            self.legacy_logger.info(f"Test message {i}")
        legacy_time = time.time() - start_time
        results["legacy"] = iterations / legacy_time
        
        # Test Hydra-Logger
        start_time = time.time()
        for i in range(iterations):
            self.hydra_logger.info(f"Test message {i}", "DEFAULT")
        hydra_time = time.time() - start_time
        results["hydra"] = iterations / hydra_time
        
        return results
    
    def test_memory_usage(self, iterations: int = 10000) -> dict:
        """Test memory usage during logging."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Test legacy logger memory usage
        initial_memory = process.memory_info().rss
        for i in range(iterations):
            self.legacy_logger.info(f"Memory test {i}")
        legacy_memory = process.memory_info().rss - initial_memory
        
        # Test Hydra-Logger memory usage
        initial_memory = process.memory_info().rss
        for i in range(iterations):
            self.hydra_logger.info(f"Memory test {i}", "DEFAULT")
        hydra_memory = process.memory_info().rss - initial_memory
        
        return {
            "legacy_memory_mb": legacy_memory / 1024 / 1024,
            "hydra_memory_mb": hydra_memory / 1024 / 1024
        }

# Usage
import logging
legacy_logger = logging.getLogger("perf_test")
hydra_logger = HydraLogger()

tester = PerformanceTester(legacy_logger, hydra_logger)

# Benchmark performance
perf_results = tester.benchmark_logging(10000)
print(f"Legacy logger: {perf_results['legacy']:.0f} logs/sec")
print(f"Hydra-Logger: {perf_results['hydra']:.0f} logs/sec")

# Test memory usage
memory_results = tester.test_memory_usage(10000)
print(f"Legacy memory: {memory_results['legacy_memory_mb']:.2f} MB")
print(f"Hydra memory: {memory_results['hydra_memory_mb']:.2f} MB")
```

## Troubleshooting

### Common Migration Issues

#### Issue 1: Missing Log Files

**Problem**: Log files are not being created after migration.

**Solution**: Check file permissions and directory structure.

```python
import os
from pathlib import Path

# Ensure log directory exists with proper permissions
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
os.chmod(log_dir, 0o755)

# Test file creation
logger = HydraLogger()
logger.info("Test message", "DEFAULT")
```

#### Issue 2: Incorrect Log Levels

**Problem**: Log levels are not working as expected.

**Solution**: Verify configuration and layer setup.

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create configuration with explicit levels
config = LoggingConfig(
    layers={
        "DEBUG": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="console", format="plain-text")
            ]
        ),
        "INFO": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="console", format="plain-text")
            ]
        )
    }
)

logger = HydraLogger(config)

# Test different levels
logger.debug("Debug message", "DEBUG")  # Should appear
logger.info("Info message", "INFO")     # Should appear
logger.warning("Warning message", "INFO")  # Should appear
```

#### Issue 3: Format Issues

**Problem**: Log format is not as expected.

**Solution**: Check format configuration and color mode settings.

```python
# Test different formats
config = LoggingConfig(
    layers={
        "TEST": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="console",
                    format="json",
                    color_mode="never"
                )
            ]
        )
    }
)

logger = HydraLogger(config)
logger.info("Test message", "TEST", extra={"key": "value"})
```

#### Issue 4: Performance Issues

**Problem**: Logging performance is slower than expected.

**Solution**: Optimize configuration for your use case.

```python
# Optimize for high-throughput logging
config = LoggingConfig(
    layers={
        "HIGH_VOLUME": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/high_volume.log",
                    format="plain-text",  # Fastest format
                    max_size="100MB",
                    backup_count=1
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Test performance
import time
start_time = time.time()
for i in range(10000):
    logger.info(f"Performance test {i}", "HIGH_VOLUME")
end_time = time.time()
print(f"Performance: {10000 / (end_time - start_time):.0f} logs/sec")
```

### Migration Checklist

- [ ] **Backup existing logs** before migration
- [ ] **Test migration** in development environment
- [ ] **Verify log levels** are working correctly
- [ ] **Check file permissions** for log directories
- [ ] **Test all log formats** (plain-text, JSON, CSV, etc.)
- [ ] **Verify performance** meets requirements
- [ ] **Test error handling** and fallback mechanisms
- [ ] **Update documentation** for new logging system
- [ ] **Train team** on new logging API
- [ ] **Monitor logs** after migration to production

### Support and Resources

If you encounter issues during migration:

1. **Check the documentation** for detailed API reference
2. **Review examples** in the examples directory
3. **Test with simple configuration** first
4. **Use the migration helper functions** provided
5. **Compare outputs** between legacy and new systems

This migration guide provides comprehensive coverage for transitioning from existing logging systems to Hydra-Logger, ensuring a smooth and successful migration process. 