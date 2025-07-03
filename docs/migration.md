# Migration Guide

This guide helps you migrate from existing logging systems to Hydra-Logger.

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
```

### Migrated Code

```python
from hydra_logger import HydraLogger

# Create logger with similar configuration
logger = HydraLogger()

# Use the new API
logger.info("DEFAULT", "Application started")
logger.error("DEFAULT", "An error occurred")
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

### Migrated Code

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Option 1: Use the migration function
from hydra_logger.compatibility import migrate_to_hydra

logger = migrate_to_hydra(
    enable_file_logging=True,
    console_level=logging.WARNING
)

# Option 2: Create equivalent configuration
config = LoggingConfig(
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="app.log",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    level="WARNING"
                )
            ]
        )
    }
)

logger = HydraLogger(config)
logger.info("DEFAULT", "Application started")
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
    
    return app_logger, error_logger, debug_logger

# Usage
app_logger, error_logger, debug_logger = setup_loggers()
app_logger.info("Application started")
error_logger.error("An error occurred")
debug_logger.debug("Debug information")
```

### Migrated Code

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
                    path="logs/app.log"
                )
            ]
        ),
        "ERROR": LogLayer(
            level="ERROR",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/errors.log"
                )
            ]
        ),
        "DEBUG": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/debug.log"
                )
            ]
        )
    }
)

# Create single logger instance
logger = HydraLogger(config)

# Use different layers
logger.info("APP", "Application started")
logger.error("ERROR", "An error occurred")
logger.debug("DEBUG", "Debug information")
```

## Migrating from Configuration Files

### Current YAML Configuration

```yaml
# logging_config.yaml
version: 1
formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    filename: logs/app.log
    maxBytes: 10485760
    backupCount: 5
    formatter: standard
  console:
    class: logging.StreamHandler
    level: WARNING
    formatter: standard
loggers:
  app:
    level: INFO
    handlers: [file, console]
    propagate: false
  errors:
    level: ERROR
    handlers: [file]
    propagate: false
```

### Migrated YAML Configuration

```yaml
# hydra_logging.yaml
layers:
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        max_size: 10MB
        backup_count: 5
      - type: console
        level: WARNING
  
  ERROR:
    level: ERROR
    destinations:
      - type: file
        path: logs/app.log
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
logger.error("ERROR", "An error occurred")
```

## Migrating from Structured Logging

### Current Code (using structlog)

```python
import structlog

# Setup structured logging
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

# Usage
logger = structlog.get_logger()
logger.info("user_login", user_id=123, ip_address="192.168.1.1")
logger.error("database_error", error="Connection failed", retry_count=3)
```

### Migrated Code

```python
from hydra_logger import HydraLogger
import json

# Create logger with structured output
logger = HydraLogger()

# Use structured logging with JSON formatting
def log_structured(layer: str, event: str, **kwargs):
    """Log structured data as JSON."""
    log_data = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    logger.info(layer, json.dumps(log_data))

# Usage
log_structured("AUTH", "user_login", user_id=123, ip_address="192.168.1.1")
log_structured("DB", "database_error", error="Connection failed", retry_count=3)
```

## Migrating from Django Logging

### Current Django Settings

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'myapp': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Migrated Configuration

```yaml
# hydra_logging.yaml
layers:
  DJANGO:
    level: INFO
    destinations:
      - type: file
        path: logs/django.log
        max_size: 10MB
        backup_count: 5
      - type: console
        level: WARNING
  
  MYAPP:
    level: DEBUG
    destinations:
      - type: file
        path: logs/django.log
        max_size: 10MB
        backup_count: 5
```

### Usage in Django

```python
# views.py
from hydra_logger import HydraLogger

logger = HydraLogger.from_config("hydra_logging.yaml")

def my_view(request):
    logger.info("MYAPP", f"Request from {request.META.get('REMOTE_ADDR')}")
    # ... view logic
    return response
```

## Migrating from Flask Logging

### Current Flask Code

```python
from flask import Flask
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Setup logging
if not app.debug:
    file_handler = RotatingFileHandler(
        'logs/flask.log',
        maxBytes=1024*1024*10,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask startup')

# Usage
@app.route('/')
def index():
    app.logger.info('Index page accessed')
    return 'Hello, World!'
```

### Migrated Code

```python
from flask import Flask
from hydra_logger import HydraLogger

app = Flask(__name__)

# Setup Hydra-Logger
logger = HydraLogger()

@app.before_first_request
def setup_logging():
    logger.info("FLASK", "Flask startup")

@app.route('/')
def index():
    logger.info("FLASK", "Index page accessed")
    return 'Hello, World!'
```

## Migration Checklist

### Before Migration

- [ ] Audit current logging usage
- [ ] Identify all log files and their purposes
- [ ] Document current log levels and formats
- [ ] Identify any custom handlers or formatters
- [ ] Check for any logging dependencies

### During Migration

- [ ] Create equivalent Hydra-Logger configuration
- [ ] Update import statements
- [ ] Replace logger calls with new API
- [ ] Test log output and formatting
- [ ] Verify log file creation and rotation

### After Migration

- [ ] Verify all log messages are captured
- [ ] Check log file permissions and locations
- [ ] Test log rotation and retention
- [ ] Update documentation
- [ ] Remove old logging code

## Common Migration Patterns

### Pattern 1: Simple Replacement

```python
# Before
import logging
logger = logging.getLogger(__name__)
logger.info("Message")

# After
from hydra_logger import HydraLogger
logger = HydraLogger()
logger.info("DEFAULT", "Message")
```

### Pattern 2: Multiple Loggers to Layers

```python
# Before
app_logger = logging.getLogger('app')
error_logger = logging.getLogger('errors')
app_logger.info("Message")
error_logger.error("Error")

# After
from hydra_logger import HydraLogger
logger = HydraLogger()
logger.info("APP", "Message")
logger.error("ERROR", "Error")
```

### Pattern 3: Configuration File Migration

```python
# Before
import logging.config
logging.config.fileConfig('logging.conf')

# After
from hydra_logger import HydraLogger
logger = HydraLogger.from_config('hydra_logging.yaml')
```

## Troubleshooting Migration Issues

### Issue: Log Files Not Created

**Solution**: Check file paths and permissions

```python
import os
from hydra_logger import HydraLogger

# Ensure directory exists
os.makedirs("logs", exist_ok=True)
logger = HydraLogger()
```

### Issue: Different Log Format

**Solution**: Hydra-Logger uses a standard format. If you need custom formatting, you can extend the logger:

```python
from hydra_logger import HydraLogger
import logging

class CustomHydraLogger(HydraLogger):
    def _setup_formatter(self):
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return formatter

logger = CustomHydraLogger()
```

### Issue: Missing Log Levels

**Solution**: Ensure all required log levels are configured

```yaml
layers:
  ALL_LEVELS:
    level: DEBUG  # Capture all levels
    destinations:
      - type: file
        path: logs/all.log
```

## Performance Considerations

### Before Migration

- Monitor current logging performance
- Identify any performance bottlenecks
- Document current log volumes

### After Migration

- Compare performance metrics
- Monitor disk usage
- Check for any performance regressions

### Optimization Tips

- Use appropriate log levels
- Implement log rotation
- Consider async logging for high-volume applications
- Use separate log files for different concerns 