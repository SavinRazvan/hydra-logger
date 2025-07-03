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
- **Multiple formats**: Support for text, JSON, CSV, syslog, and GELF formats
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
logger.info("DEFAULT", "Application started")
logger.error("DEFAULT", "An error occurred")
logger.debug("DEFAULT", "Debug information")
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
                    format="text",
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
                    format="text"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Use different layers
logger.info("DEFAULT", "Application started")
logger.error("DEFAULT", "An error occurred")
logger.debug("DEBUG", "Debug information")
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
logger.info("DEFAULT", "Application started")
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
                    format="text",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    level="WARNING",
                    format="text"
                )
            ]
        )
    }
)

logger = HydraLogger(config)
logger.info("DEFAULT", "Application started")
```

#### Option 3: Enhanced Configuration with Multiple Formats

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Enhanced configuration with multiple formats
config = LoggingConfig(
    default_level="INFO",
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="text",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="file",
                    path="logs/app.json",
                    format="json"
                )
            ]
        ),
        "CONSOLE": LogLayer(
            level="WARNING",
            destinations=[
                LogDestination(
                    type="console",
                    format="json"
                )
            ]
        )
    }
)

logger = HydraLogger(config)
logger.info("APP", "Application started")
logger.warning("CONSOLE", "Warning message")
```

## Migrating from Multiple Loggers

### Current Code

```python
import logging

# Setup different loggers
def setup_loggers():
    # Main application logger
    app_logger = logging.getLogger('app')
    app_handler = logging.FileHandler('logs/app.log')
    app_logger.addHandler(app_handler)
    app_logger.setLevel(logging.INFO)
    
    # Error logger
    error_logger = logging.getLogger('errors')
    error_handler = logging.FileHandler('logs/errors.log')
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)
    
    # Debug logger
    debug_logger = logging.getLogger('debug')
    debug_handler = logging.FileHandler('logs/debug.log')
    debug_logger.addHandler(debug_handler)
    debug_logger.setLevel(logging.DEBUG)
    
    # API logger
    api_logger = logging.getLogger('api')
    api_handler = logging.FileHandler('logs/api.log')
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    
    return app_logger, error_logger, debug_logger, api_logger

# Usage
app_logger, error_logger, debug_logger, api_logger = setup_loggers()
app_logger.info("Application started")
error_logger.error("An error occurred")
debug_logger.debug("Debug information")
api_logger.info("API request processed")
```

### Migrated Code with Multiple Formats

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create configuration with multiple layers and formats
config = LoggingConfig(
    default_level="INFO",
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="text"
                ),
                LogDestination(
                    type="file",
                    path="logs/app.json",
                    format="json"
                )
            ]
        ),
        "ERROR": LogLayer(
            level="ERROR",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/errors.log",
                    format="text"
                ),
                LogDestination(
                    type="file",
                    path="logs/errors.json",
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
                    format="text"
                )
            ]
        ),
        "API": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/api/requests.json",
                    format="json"
                ),
                LogDestination(
                    type="file",
                    path="logs/api/errors.log",
                    format="text"
                )
            ]
        )
    }
)

# Create single logger instance
logger = HydraLogger(config)

# Use different layers (equivalent to different loggers)
logger.info("APP", "Application started")
logger.error("ERROR", "An error occurred")
logger.debug("DEBUG", "Debug information")
logger.info("API", "API request processed")
```

## Migrating from Configuration Files

### Current Python Logging Configuration

```python
# logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'standard'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'json_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.json',
            'maxBytes': 10485760,
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'loggers': {
        'app': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        },
        'api': {
            'handlers': ['json_file'],
            'level': 'INFO'
        },
        'errors': {
            'handlers': ['file'],
            'level': 'ERROR'
        }
    }
}
```

### Migrated Hydra-Logger Configuration

```yaml
# hydra_logging.yaml
default_level: INFO

layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        format: text
        max_size: 10MB
        backup_count: 5
      - type: console
        format: text
  
  API:
    level: INFO
    destinations:
      - type: file
        path: logs/app.json
        format: json
        max_size: 10MB
        backup_count: 5
  
  ERROR:
    level: ERROR
    destinations:
      - type: file
        path: logs/app.log
        format: text
        max_size: 10MB
        backup_count: 5
```

### Usage

```python
from hydra_logger import HydraLogger

# Load from configuration file
logger = HydraLogger.from_config("hydra_logging.yaml")

# Use the logger
logger.info("APP", "Application started")
logger.info("API", "API request processed")
logger.error("ERROR", "An error occurred")
```

## Migrating from Other Logging Libraries

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

# Use structlog
logger = structlog.get_logger()
logger.info("Application started", user_id=123, action="login")
logger.error("Database error", error="Connection failed", retry_count=3)
```

#### Migrated Hydra-Logger Code

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Configure Hydra-Logger with JSON format
config = LoggingConfig(
    default_level="INFO",
    layers={
        "APP": LogLayer(
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

# Use Hydra-Logger with structured data
logger.info("APP", "Application started", extra={"user_id": 123, "action": "login"})
logger.error("APP", "Database error", extra={"error": "Connection failed", "retry_count": 3})
```

### Migrating from Loguru

#### Current Loguru Code

```python
from loguru import logger
import sys

# Configure loguru
logger.remove()
logger.add(
    sys.stdout,
    format="{time} | {level} | {name}:{function}:{line} | {message}",
    level="INFO"
)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="5 days",
    format="{time} | {level} | {name}:{function}:{line} | {message}",
    level="DEBUG"
)

# Use loguru
logger.info("Application started")
logger.debug("Debug information")
logger.error("An error occurred")
```

#### Migrated Hydra-Logger Code

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Configure Hydra-Logger with similar settings
config = LoggingConfig(
    default_level="INFO",
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="console",
                    format="text"
                ),
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="text",
                    max_size="10MB",
                    backup_count=5
                )
            ]
        ),
        "DEBUG": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="text",
                    max_size="10MB",
                    backup_count=5
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Use Hydra-Logger
logger.info("DEFAULT", "Application started")
logger.debug("DEBUG", "Debug information")
logger.error("DEFAULT", "An error occurred")
```

## Advanced Migration Strategies

### Gradual Migration

For large applications, you can migrate gradually:

```python
from hydra_logger import HydraLogger
import logging

# Keep existing logging for some components
logging.basicConfig(level=logging.INFO)
legacy_logger = logging.getLogger(__name__)

# Use Hydra-Logger for new components
config = LoggingConfig(
    layers={
        "NEW_FEATURE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/new_feature.json",
                    format="json"
                )
            ]
        )
    }
)
new_logger = HydraLogger(config)

# Use both during transition
legacy_logger.info("Legacy component message")
new_logger.info("NEW_FEATURE", "New feature message")
```

### Configuration Migration Script

```python
import yaml
import json
from pathlib import Path

def migrate_logging_config(old_config_path, new_config_path):
    """Migrate from old logging configuration to Hydra-Logger format."""
    
    # Load old configuration
    with open(old_config_path, 'r') as f:
        old_config = yaml.safe_load(f)
    
    # Convert to Hydra-Logger format
    new_config = {
        'default_level': 'INFO',
        'layers': {}
    }
    
    # Convert loggers to layers
    for logger_name, logger_config in old_config.get('loggers', {}).items():
        layer_name = logger_name.upper()
        new_config['layers'][layer_name] = {
            'level': logger_config.get('level', 'INFO'),
            'destinations': []
        }
        
        # Convert handlers to destinations
        for handler_name in logger_config.get('handlers', []):
            handler_config = old_config['handlers'][handler_name]
            
            if handler_config['class'] == 'logging.handlers.RotatingFileHandler':
                destination = {
                    'type': 'file',
                    'path': handler_config['filename'],
                    'max_size': f"{handler_config['maxBytes'] // (1024*1024)}MB",
                    'backup_count': handler_config['backupCount'],
                    'format': 'json' if 'json' in handler_name else 'text'
                }
            elif handler_config['class'] == 'logging.StreamHandler':
                destination = {
                    'type': 'console',
                    'format': 'text'
                }
            
            new_config['layers'][layer_name]['destinations'].append(destination)
    
    # Save new configuration
    with open(new_config_path, 'w') as f:
        yaml.dump(new_config, f, default_flow_style=False)
    
    print(f"Configuration migrated to {new_config_path}")

# Usage
migrate_logging_config('old_logging.yaml', 'hydra_logging.yaml')
```

## Testing Migration

### Migration Testing Script

```python
import tempfile
import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def test_migration():
    """Test that migration produces equivalent logging behavior."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test configuration
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "test.log"),
                            format="text"
                        ),
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "test.json"),
                            format="json"
                        )
                    ]
                )
            }
        )
        
        # Test logger
        logger = HydraLogger(config)
        
        # Test different log levels
        test_messages = [
            ("INFO", "Test info message"),
            ("DEBUG", "Test debug message"),
            ("WARNING", "Test warning message"),
            ("ERROR", "Test error message"),
            ("CRITICAL", "Test critical message")
        ]
        
        for level, message in test_messages:
            if level == "INFO":
                logger.info("TEST", message)
            elif level == "DEBUG":
                logger.debug("TEST", message)
            elif level == "WARNING":
                logger.warning("TEST", message)
            elif level == "ERROR":
                logger.error("TEST", message)
            elif level == "CRITICAL":
                logger.critical("TEST", message)
        
        # Verify files were created
        assert os.path.exists(os.path.join(temp_dir, "test.log"))
        assert os.path.exists(os.path.join(temp_dir, "test.json"))
        
        # Verify content
        with open(os.path.join(temp_dir, "test.log"), 'r') as f:
            log_content = f.read()
            assert "Test info message" in log_content
            assert "Test error message" in log_content
        
        with open(os.path.join(temp_dir, "test.json"), 'r') as f:
            json_content = f.read()
            assert "Test info message" in json_content
            assert "Test error message" in json_content
        
        print("Migration test passed!")

if __name__ == "__main__":
    test_migration()
```

## Troubleshooting

### Common Migration Issues

#### Issue: Log files not created
**Solution**: Ensure the log directory exists or use absolute paths.

```python
import os
from pathlib import Path

# Create log directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Use absolute paths
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path=str(log_dir / "app.log"),
                    format="text"
                )
            ]
        )
    }
)
```

#### Issue: Format not working as expected
**Solution**: Check format dependencies and fallback behavior.

```python
# Ensure required packages are installed
# pip install python-json-logger graypy

# Test format configuration
config = LoggingConfig(
    layers={
        "TEST": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="test.json",
                    format="json"  # Requires python-json-logger
                )
            ]
        )
    }
)
```

#### Issue: Performance degradation
**Solution**: Optimize configuration for high-throughput scenarios.

```python
# Use appropriate file sizes and backup counts
config = LoggingConfig(
    layers={
        "HIGH_VOLUME": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/high_volume.csv",
                    format="csv",
                    max_size="100MB",
                    backup_count=2
                )
            ]
        )
    }
)
```

### Migration Checklist

- [ ] Install Hydra-Logger: `pip install hydra-logger`
- [ ] Install format dependencies: `pip install python-json-logger graypy`
- [ ] Create log directories
- [ ] Test basic functionality
- [ ] Migrate configuration files
- [ ] Update import statements
- [ ] Test all log levels and formats
- [ ] Verify file rotation works
- [ ] Check performance impact
- [ ] Update documentation

This comprehensive migration guide provides multiple paths for transitioning to Hydra-Logger, ensuring a smooth migration process regardless of your current logging setup. 