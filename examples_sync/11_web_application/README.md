# 11 - Web Application

## 🎯 Overview

This example demonstrates how to use Hydra-Logger in a real-world web application with multiple modules. It shows:
- Multi-module logging architecture
- Different log layers for different concerns
- Structured logging for web requests
- Error handling and debugging
- Performance monitoring

## 🚀 Running the Example

```bash
# Run the main web application demo
python multi_module_demo.py

# Or run individual modules
python demo_modules/api_client.py
python demo_modules/database_handler.py
python demo_modules/user_manager.py
```

## 📊 Expected Output

### Console Output
```
2025-01-27 10:30:15 INFO [APP] Web application started
2025-01-27 10:30:15 INFO [API] API request: GET /api/users
2025-01-27 10:30:15 DEBUG [DB] SQL Query: SELECT * FROM users WHERE id = 123
2025-01-27 10:30:15 INFO [AUTH] User authentication: user123
2025-01-27 10:30:15 INFO [NOTIFY] Email sent: welcome@example.com
```

### File Structure
```
logs/
├── app/
│   ├── main.log          # Application logs
│   └── errors.log        # Error logs
├── api/
│   ├── requests.log       # API request logs
│   └── responses.log      # API response logs
├── database/
│   └── queries.log        # Database query logs
├── auth/
│   └── security.log       # Authentication logs
└── notifications/
    └── emails.log         # Email notification logs
```

## 🔑 Key Concepts

- **Multi-Module Architecture**: Separate logging for different modules
- **Layer Organization**: Different log layers for different concerns
- **Structured Logging**: JSON format for machine-readable logs
- **Error Handling**: Dedicated error logging
- **Performance Monitoring**: Track request times and performance
- **Security Logging**: Separate security and audit logs

## 📁 Module Structure

```
demo_modules/
├── __init__.py
├── api_client.py          # API client with request logging
├── database_handler.py    # Database operations with query logging
├── user_manager.py        # User management with auth logging
├── notification_service.py # Email notifications with delivery logging
└── helpers.py             # Utility functions with debug logging
```

## 🎨 Code Example

### Main Application
```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Web application configuration
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/app/main.log", format="text"),
                LogDestination(type="console", level="WARNING", format="json")
            ]
        ),
        "API": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/api/requests.log", format="json"),
                LogDestination(type="file", path="logs/api/errors.log", format="text")
            ]
        ),
        "DB": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(type="file", path="logs/database/queries.log", format="text")
            ]
        ),
        "AUTH": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/auth/security.log", format="syslog")
            ]
        ),
        "NOTIFY": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/notifications/emails.log", format="json")
            ]
        )
    }
)

logger = HydraLogger(config)
```

### Module Example (API Client)
```python
import time
from hydra_logger import HydraLogger

class APIClient:
    def __init__(self, logger):
        self.logger = logger
    
    def make_request(self, method, url, data=None):
        start_time = time.time()
        
        self.logger.info("API", f"API request: {method} {url}")
        
        # Simulate API call
        time.sleep(0.1)
        
        response_time = (time.time() - start_time) * 1000
        self.logger.info("API", f"API response: {method} {url} - {response_time:.2f}ms")
        
        return {"status": "success", "data": data}
```

## 🧪 Testing

```bash
# Run the complete web application demo
python multi_module_demo.py

# Check the generated logs
ls -la logs/
cat logs/app/main.log
cat logs/api/requests.log
cat logs/database/queries.log
cat logs/auth/security.log
cat logs/notifications/emails.log
```

## 📚 Module Examples

### **API Client** (`demo_modules/api_client.py`)
- Logs API requests and responses
- Tracks response times
- Handles API errors

### **Database Handler** (`demo_modules/database_handler.py`)
- Logs SQL queries
- Tracks query performance
- Handles database errors

### **User Manager** (`demo_modules/user_manager.py`)
- Logs user authentication
- Tracks user actions
- Handles security events

### **Notification Service** (`demo_modules/notification_service.py`)
- Logs email notifications
- Tracks delivery status
- Handles notification errors

### **Helpers** (`demo_modules/helpers.py`)
- Utility functions
- Debug logging
- Error handling

## 🎯 Real-World Patterns

### **Request Flow Logging**
```python
# Log the complete request flow
logger.info("API", "Request started: GET /api/users")
logger.debug("DB", "Query executed: SELECT * FROM users")
logger.info("API", "Request completed: GET /api/users - 150ms")
```

### **Error Handling**
```python
try:
    # API call
    response = api_client.make_request("GET", "/api/users")
except Exception as e:
    logger.error("API", f"API request failed: {e}")
    logger.debug("API", f"Request details: {request_data}")
```

### **Performance Monitoring**
```python
import time

start_time = time.time()
# ... operation ...
duration = (time.time() - start_time) * 1000
logger.info("PERF", f"Operation completed in {duration:.2f}ms")
```

## 📚 Next Steps

After understanding this example, try:
- **12_microservices** - Microservice patterns
- **13_high_concurrency** - High-concurrency scenarios
- **14_backpressure_handling** - Handling backpressure 