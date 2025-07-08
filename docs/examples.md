# Examples Guide

This comprehensive guide provides detailed examples of how to use Hydra-Logger in various real-world scenarios, demonstrating different configurations, log formats, and use cases. **Hydra-Logger works with any type of Python application** - from simple scripts to complex distributed systems.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Environment-Specific Configurations](#environment-specific-configurations)
- [Web Application Examples](#web-application-examples)
- [Microservices Examples](#microservices-examples)
- [Database Application Examples](#database-application-examples)
- [Security and Monitoring Examples](#security-and-monitoring-examples)
- [Analytics and Reporting Examples](#analytics-and-reporting-examples)
- [Enterprise Integration Examples](#enterprise-integration-examples)
- [Performance Optimization Examples](#performance-optimization-examples)
- [Dynamic Configuration Examples](#dynamic-configuration-examples)

## Application Types Supported

Hydra-Logger is designed to work with **any Python application**:

- **Web Applications**: Django, Flask, FastAPI, REST APIs, GraphQL services
- **Desktop Applications**: GUI apps, CLI tools, system utilities
- **Data Science**: ML models, data analysis, ETL pipelines
- **Microservices**: Containerized apps, message queues, background workers
- **Enterprise Systems**: Business logic, financial systems, healthcare apps
- **IoT & Embedded**: Sensor data, device monitoring, edge computing
- **Games & Entertainment**: Game engines, media processing, streaming
- **DevOps & Infrastructure**: Automation, monitoring, deployment tools

**The examples below demonstrate specific use cases, with configuration principles that apply to all application types.**

## Format System: `plain-text` and Color Mode

Hydra-Logger supports the `plain-text` format for human-readable output with color control:

- **`plain-text`**: Human-readable plain-text format with color control via `color_mode`
- **Other formats**: `json`, `csv`, `syslog`, `gelf` (all support color_mode for future colored variants)

**Color Mode** (`color_mode`):
- `auto`: Detects if colors should be used (default)
- `always`: Forces colors on
- `never`: Forces colors off

**Example:**
```python
config = {
    "layers": {
        "FRONTEND": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},  # Colored console
                {"type": "file", "format": "plain-text", "color_mode": "never"}      # Plain file
            ]
        }
    }
}
logger = HydraLogger(config=config)
logger.info("FRONTEND", "Colored console, plain file")
```

## Available Formats
- `plain-text` - Human-readable text (colored in console if color_mode allows)
- `json` - JSON format (structured)
- `csv` - CSV format (tabular)
- `syslog` - Syslog format (system logging)
- `gelf` - GELF format (Graylog)

## Color Mode Options
- `auto` - Automatic detection (default)
- `always` - Force colors on
- `never` - Force colors off

## Example Configuration
```python
config = {
    "layers": {
        "FRONTEND": {
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "auto"},
                {"type": "file", "format": "plain-text", "color_mode": "never"}
            ]
        }
    }
}
```

## Basic Examples

### Zero-Configuration Mode (New Way)

```python
from hydra_logger import HydraLogger

# Create logger with zero configuration - it just works!
logger = HydraLogger()

# Centralized logging (no layers)
logger.info("Application started successfully")
logger.debug("Debug information for development")
logger.warning("Configuration file not found, using defaults")
logger.error("Database connection failed")
logger.critical("System shutdown initiated")
```

### Flexible Layer System

```python
from hydra_logger import HydraLogger

# Option 1: Centralized logging (no layers)
logger.info("Application started")
logger.debug("Configuration loaded")

# Option 2: Custom layer names (your choice)
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API endpoint called")
logger.info("DATABASE", "Query executed")
logger.info("PAYMENT", "Payment processed")
```

### Auto-Detection Mode

```python
from hydra_logger import HydraLogger

# Enable auto-detection for environment-aware configuration
logger = HydraLogger(auto_detect=True)

# The logger automatically detects your environment:
# - Development: Debug level, console + file, plain-text format
# - Production: Info level, JSON format, file rotation
# - Cloud: Console output for better log aggregation

logger.info("Auto-detected configuration applied")
```

### Manual Configuration (Old Way - Still Supported)

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create custom configuration manually
config = LoggingConfig(
    layers={
        "DEFAULT": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
                    format="plain-text"
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

# Create logger with manual configuration
logger = HydraLogger(config)

# Use the logger
logger.info("DEFAULT", "Application started with manual configuration")
```

### Custom Configuration with Multiple Formats

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create custom configuration with different formats (old way - still supported)
config = LoggingConfig(
    default_level="INFO",
    layers={
        "FRONTEND": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/frontend.log",
                    format="plain-text",
                    max_size="10MB",
                    backup_count=5
                ),
                LogDestination(
                    type="console",
                    level="WARNING",
                    format="json"
                )
            ]
        ),
        "BACKEND": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/backend.log",
                    format="plain-text"
                )
            ]
        )
    }
)

# Create logger with custom configuration
logger = HydraLogger(config)

# Use the logger
logger.info("FRONTEND", "Application started with custom configuration")
logger.debug("BACKEND", "API endpoint called")
```

## Environment-Specific Configurations

### Development Environment

```python
from hydra_logger import HydraLogger

# Development configuration
config = {
    "layers": {
        "FRONTEND": {
            "level": "DEBUG",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},
                {"type": "file", "path": "logs/dev/frontend.log", "format": "plain-text"}
            ]
        },
        "BACKEND": {
            "level": "DEBUG",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},
                {"type": "file", "path": "logs/dev/backend.log", "format": "json"}
            ]
        }
    }
}

logger = HydraLogger(config)
logger.debug("FRONTEND", "User interface component loaded")
logger.debug("BACKEND", "API endpoint registered")
```

### Production Environment

```python
from hydra_logger import HydraLogger

# Production configuration
config = {
    "layers": {
        "FRONTEND": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/prod/frontend.json", "format": "json", "max_size": "100MB", "backup_count": 10},
                {"type": "console", "level": "ERROR", "format": "json"}
            ]
        },
        "BACKEND": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/prod/backend.json", "format": "json", "max_size": "100MB", "backup_count": 10},
                {"type": "console", "level": "ERROR", "format": "json"}
            ]
        },
        "SECURITY": {
            "level": "WARNING",
            "destinations": [
                {"type": "file", "path": "logs/prod/security.log", "format": "syslog", "max_size": "50MB", "backup_count": 20}
            ]
        }
    }
}

logger = HydraLogger(config)
logger.info("FRONTEND", "User interface updated")
logger.info("BACKEND", "API request processed")
logger.warning("SECURITY", "Authentication attempt failed")
```

### Testing Environment

```python
from hydra_logger import HydraLogger

# Testing configuration
config = {
    "layers": {
        "TEST": {
            "level": "DEBUG",
            "destinations": [
                {"type": "file", "path": "logs/test/test.log", "format": "plain-text"}
            ]
        }
    }
}

logger = HydraLogger(config)
logger.debug("TEST", "Test case started")
logger.info("TEST", "Test case completed")
```

## Web Application Examples

### Django Application

```python
from hydra_logger import HydraLogger

# Django-specific configuration
config = {
    "layers": {
        "DJANGO": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/django/app.log", "format": "json"},
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        },
        "REQUESTS": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/django/requests.json", "format": "json"}
            ]
        },
        "ERRORS": {
            "level": "ERROR",
            "destinations": [
                {"type": "file", "path": "logs/django/errors.log", "format": "plain-text"}
            ]
        }
    }
}

logger = HydraLogger(config)

# In your Django views
def my_view(request):
    logger.info("DJANGO", "View function called")
    logger.info("REQUESTS", "HTTP request received", method=request.method, path=request.path)
    
    try:
        # Your view logic
        result = process_request(request)
        logger.info("DJANGO", "Request processed successfully")
        return result
    except Exception as e:
        logger.error("ERRORS", "View error occurred", error=str(e))
        raise
```

### FastAPI Application

```python
from hydra_logger import HydraLogger
from fastapi import FastAPI, Request

app = FastAPI()

# FastAPI-specific configuration
config = {
    "layers": {
        "API": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/fastapi/api.json", "format": "json"},
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        },
        "PERFORMANCE": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/fastapi/performance.csv", "format": "csv"}
            ]
        }
    }
}

logger = HydraLogger(config)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    logger.info("API", "Request started", method=request.method, url=str(request.url))
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info("PERFORMANCE", "Request completed", 
               method=request.method, 
               url=str(request.url), 
               status_code=response.status_code,
               process_time_ms=process_time * 1000)
    
    return response

@app.get("/")
async def root():
    logger.info("API", "Root endpoint called")
    return {"message": "Hello World"}
```

## Microservices Examples

### API Gateway

```python
from hydra_logger import HydraLogger

# API Gateway configuration
config = {
    "layers": {
        "GATEWAY": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/gateway/requests.json", "format": "json"},
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        },
        "ROUTING": {
            "level": "DEBUG",
            "destinations": [
                {"type": "file", "path": "logs/gateway/routing.log", "format": "plain-text"}
            ]
        },
        "AUTH": {
            "level": "WARNING",
            "destinations": [
                {"type": "file", "path": "logs/gateway/auth.log", "format": "syslog"}
            ]
        }
    }
}

logger = HydraLogger(config)

def route_request(request):
    logger.info("GATEWAY", "Request received", client_ip=request.client_ip)
    logger.debug("ROUTING", "Routing request", service=request.service)
    
    if not authenticate_request(request):
        logger.warning("AUTH", "Authentication failed", user_id=request.user_id)
        return None
    
    return forward_request(request)
```

### Background Worker

```python
from hydra_logger import HydraLogger

# Background worker configuration
config = {
    "layers": {
        "WORKER": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/worker/tasks.json", "format": "json"},
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        },
        "QUEUE": {
            "level": "DEBUG",
            "destinations": [
                {"type": "file", "path": "logs/worker/queue.log", "format": "plain-text"}
            ]
        }
    }
}

logger = HydraLogger(config)

def process_task(task):
    logger.info("WORKER", "Task started", task_id=task.id, task_type=task.type)
    logger.debug("QUEUE", "Processing task from queue", queue_name=task.queue)
    
    try:
        result = execute_task(task)
        logger.info("WORKER", "Task completed", task_id=task.id, result=result)
        return result
    except Exception as e:
        logger.error("WORKER", "Task failed", task_id=task.id, error=str(e))
        raise
```

## Database Application Examples

### Database Operations

```python
from hydra_logger import HydraLogger

# Database-specific configuration
config = {
    "layers": {
        "DATABASE": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/database/queries.json", "format": "json"},
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        },
        "PERFORMANCE": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/database/performance.csv", "format": "csv"}
            ]
        }
    }
}

logger = HydraLogger(config)

def execute_query(query, params=None):
    start_time = time.time()
    
    logger.info("DATABASE", "Query executed", query=query, params=params)
    
    try:
        result = db.execute(query, params)
        execution_time = time.time() - start_time
        
        logger.info("PERFORMANCE", "Query performance", 
                   query=query, 
                   execution_time_ms=execution_time * 1000,
                   rows_affected=result.rowcount)
        
        return result
    except Exception as e:
        logger.error("DATABASE", "Query failed", query=query, error=str(e))
        raise
```

## Security and Monitoring Examples

### Security Logging

```python
from hydra_logger import HydraLogger

# Security-specific configuration
config = {
    "layers": {
        "SECURITY": {
            "level": "WARNING",
            "destinations": [
                {"type": "file", "path": "logs/security/events.log", "format": "syslog"},
                {"type": "file", "path": "logs/security/events.json", "format": "json"}
            ]
        },
        "AUTH": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/security/auth.log", "format": "plain-text"}
            ]
        }
    }
}

logger = HydraLogger(config)

def authenticate_user(username, password):
    logger.info("AUTH", "Authentication attempt", username=username)
    
    if not validate_credentials(username, password):
        logger.warning("SECURITY", "Authentication failed", username=username, ip=request.ip)
        return False
    
    logger.info("AUTH", "Authentication successful", username=username)
    return True
```

### Performance Monitoring

```python
from hydra_logger import HydraLogger

# Performance monitoring configuration
config = {
    "layers": {
        "PERFORMANCE": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/performance/metrics.csv", "format": "csv"},
                {"type": "file", "path": "logs/performance/metrics.json", "format": "json"}
            ]
        },
        "ALERTS": {
            "level": "WARNING",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},
                {"type": "file", "path": "logs/performance/alerts.log", "format": "plain-text"}
            ]
        }
    }
}

logger = HydraLogger(config)

def monitor_performance():
    cpu_usage = get_cpu_usage()
    memory_usage = get_memory_usage()
    
    logger.info("PERFORMANCE", "System metrics", 
               cpu_percent=cpu_usage, 
               memory_percent=memory_usage)
    
    if cpu_usage > 80:
        logger.warning("ALERTS", "High CPU usage detected", cpu_percent=cpu_usage)
    
    if memory_usage > 90:
        logger.warning("ALERTS", "High memory usage detected", memory_percent=memory_usage)
```

## Analytics and Reporting Examples

### Data Analytics

```python
from hydra_logger import HydraLogger

# Analytics configuration
config = {
    "layers": {
        "ANALYTICS": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/analytics/events.csv", "format": "csv"},
                {"type": "file", "path": "logs/analytics/events.json", "format": "json"}
            ]
        },
        "REPORTS": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/analytics/reports.json", "format": "json"}
            ]
        }
    }
}

logger = HydraLogger(config)

def track_user_event(user_id, event_type, data):
    logger.info("ANALYTICS", "User event tracked", 
               user_id=user_id, 
               event_type=event_type, 
               data=data)

def generate_report(report_type, data):
    logger.info("REPORTS", "Report generated", 
               report_type=report_type, 
               record_count=len(data))
```

## Enterprise Integration Examples

### Enterprise Application

```python
from hydra_logger import HydraLogger

# Enterprise configuration
config = {
    "layers": {
        "BUSINESS": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/enterprise/business.log", "format": "json"},
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        },
        "AUDIT": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/enterprise/audit.log", "format": "syslog"}
            ]
        },
        "COMPLIANCE": {
            "level": "WARNING",
            "destinations": [
                {"type": "file", "path": "logs/enterprise/compliance.log", "format": "json"}
            ]
        }
    }
}

logger = HydraLogger(config)

def process_business_transaction(transaction):
    logger.info("BUSINESS", "Transaction started", 
               transaction_id=transaction.id, 
               amount=transaction.amount)
    
    logger.info("AUDIT", "Transaction audited", 
               user_id=transaction.user_id, 
               transaction_id=transaction.id)
    
    if transaction.amount > 10000:
        logger.warning("COMPLIANCE", "Large transaction flagged", 
                      transaction_id=transaction.id, 
                      amount=transaction.amount)
```

## Performance Optimization Examples

### High-Performance Logging

```python
from hydra_logger import HydraLogger

# High-performance configuration
config = {
    "layers": {
        "PERFORMANCE": {
            "level": "INFO",
            "destinations": [
                {"type": "file", "path": "logs/performance/metrics.json", "format": "json"},
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        }
    }
}

logger = HydraLogger(config, high_performance_mode=True)

def performance_test():
    start_time = time.time()
    
    # Log many messages quickly
    for i in range(10000):
        logger.info("PERFORMANCE", f"Performance test message {i}")
    
    total_time = time.time() - start_time
    throughput = 10000 / total_time
    
    print(f"Logged 10,000 messages in {total_time:.2f} seconds")
    print(f"Throughput: {throughput:.0f} messages/second")
```

## Dynamic Configuration Examples

### Runtime Configuration Changes

```python
from hydra_logger import HydraLogger

# Initial configuration
config = {
    "layers": {
        "APP": {
            "level": "INFO",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"}
            ]
        }
    }
}

logger = HydraLogger(config)

# Log with initial configuration
logger.info("APP", "Application started")

# Update configuration at runtime
new_config = {
    "layers": {
        "APP": {
            "level": "DEBUG",
            "destinations": [
                {"type": "console", "format": "plain-text", "color_mode": "always"},
                {"type": "file", "path": "logs/runtime.log", "format": "json"}
            ]
        }
    }
}

logger.update_config(new_config)

# Log with updated configuration
logger.debug("APP", "Configuration updated at runtime")
```

This comprehensive guide demonstrates how Hydra-Logger can be used in various real-world scenarios. The examples show both centralized logging (without layers) and custom layer names, giving users complete flexibility in organizing their logging according to their specific needs. 