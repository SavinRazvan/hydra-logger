# 05 - Multiple Layers

## 🎯 Overview

This example demonstrates multi-layered logging with Hydra-Logger. It shows how to:
- Organize logs by different concerns and purposes
- Use different log levels for different layers
- Route logs to different destinations based on layer
- Create structured log organization
- Separate concerns in logging

## 🚀 Running the Example

```bash
python main.py
```

## 📊 Expected Output

### Console Output
```
🏗️ Multiple Layers Demo
========================================

🚀 Application Startup
--------------------
2025-01-27 10:30:15 INFO [APP] Application starting up
2025-01-27 10:30:15 INFO [APP] Configuration loaded successfully
2025-01-27 10:30:15 INFO [APP] Database connection established

🌐 API Requests
--------------------
2025-01-27 10:30:15 INFO [API] API request started (method: GET, endpoint: /api/users, user_id: 123)
2025-01-27 10:30:15 DEBUG [DB] SQL Query (query: SELECT * FROM users WHERE id = 123, duration: 50ms)
2025-01-27 10:30:15 INFO [API] API request completed (method: GET, endpoint: /api/users, status_code: 200, duration: 100.25ms)
2025-01-27 10:30:15 INFO [PERFORMANCE] API Response Time (endpoint: /api/users, duration: 100.25ms)

🔒 Security Events
--------------------
2025-01-27 10:30:15 INFO [SECURITY] User login successful (user_id: 123, ip: 192.168.1.100)
2025-01-27 10:30:15 WARNING [SECURITY] Failed login attempt (user_id: unknown, ip: 192.168.1.101)
2025-01-27 10:30:15 ERROR [SECURITY] Unauthorized access attempt (user_id: unknown, ip: 192.168.1.102, endpoint: /admin)

❌ Error Handling
--------------------
2025-01-27 10:30:15 ERROR [API] Database connection failed (error: Connection timeout, retry_count: 3)
2025-01-27 10:30:15 ERROR [DB] Query execution failed (query: SELECT * FROM non_existent_table, error: Table not found)
2025-01-27 10:30:15 CRITICAL [APP] Critical system error (error: Out of memory, action: restarting)

📊 Performance Monitoring
--------------------
2025-01-27 10:30:15 INFO [PERFORMANCE] Memory Usage (memory_mb: 512, max_memory_mb: 1024)
2025-01-27 10:30:15 INFO [PERFORMANCE] CPU Usage (cpu_percent: 45.2, load_average: 1.2)

🛑 Application Shutdown
--------------------
2025-01-27 10:30:15 INFO [APP] Graceful shutdown initiated
2025-01-27 10:30:15 INFO [APP] Database connections closed
2025-01-27 10:30:15 INFO [APP] Application shutdown complete

✅ Multiple layers demo completed!
📝 Check the logs/ directory for organized log files

📁 Generated Log Structure:
------------------------------
logs/
  app/
    main.log
  api/
    requests.log
    errors.log
  database/
    queries.log
  security/
    auth.log
  performance/
    metrics.csv
```

## 🔑 Key Concepts

- **Layer Organization**: Different layers for different concerns
- **Selective Routing**: Route logs to specific destinations
- **Structured Organization**: Organized log file structure
- **Concern Separation**: Separate different types of logs
- **Flexible Configuration**: Different configs per layer

## 📁 Generated Files

```
logs/
├── app/
│   └── main.log              # Application logs
├── api/
│   ├── requests.log           # API request logs (JSON)
│   └── errors.log             # API error logs
├── database/
│   └── queries.log            # Database query logs
├── security/
│   └── auth.log               # Security logs (Syslog)
└── performance/
    └── metrics.csv            # Performance metrics (CSV)
```

## 🎨 Code Example

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Multi-layer configuration
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/app/main.log", format="text"),
                LogDestination(type="console", level="WARNING", format="text")
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
        "SECURITY": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/security/auth.log", format="syslog"),
                LogDestination(type="console", level="ERROR", format="text")
            ]
        ),
        "PERFORMANCE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(type="file", path="logs/performance/metrics.csv", format="csv")
            ]
        )
    }
)

logger = HydraLogger(config)

# Log to different layers
logger.info("APP", "Application started")
logger.info("API", "API request", method="GET", endpoint="/api/users")
logger.debug("DB", "SQL query", query="SELECT * FROM users")
logger.info("SECURITY", "User login", user_id="123", ip="192.168.1.100")
logger.info("PERFORMANCE", "Response time", endpoint="/api/users", duration="150ms")
```

## 🧪 Testing

```bash
# Run the example
python main.py

# Check the generated log structure
ls -la logs/
find logs/ -name "*.log" -o -name "*.csv" | head -10

# View specific log files
cat logs/app/main.log
cat logs/api/requests.log
cat logs/security/auth.log
cat logs/performance/metrics.csv
```

## 📚 Layer Organization

### **Application Layer (APP)**
- Application lifecycle events
- Startup and shutdown
- Configuration changes
- System status

### **API Layer (API)**
- HTTP requests and responses
- API performance metrics
- Request/response details
- API errors and exceptions

### **Database Layer (DB)**
- SQL queries and execution
- Database connection events
- Query performance metrics
- Database errors

### **Security Layer (SECURITY)**
- Authentication events
- Authorization checks
- Security violations
- User activity tracking

### **Performance Layer (PERFORMANCE)**
- System metrics
- Performance measurements
- Resource usage
- Response times

## 📚 Use Cases

### **Web Applications**
```python
# Different layers for different concerns
logger.info("APP", "Server started on port 8000")
logger.info("API", "Request received", method="POST", path="/api/users")
logger.debug("DB", "Query executed", sql="INSERT INTO users...")
logger.info("SECURITY", "User authenticated", user_id="123")
logger.info("PERFORMANCE", "Response time", duration="150ms")
```

### **Microservices**
```python
# Each service can have its own layers
logger.info("AUTH_SERVICE", "Service started")
logger.info("USER_SERVICE", "User created", user_id="456")
logger.info("PAYMENT_SERVICE", "Payment processed", amount="$99.99")
```

### **Enterprise Applications**
```python
# Compliance and audit layers
logger.info("AUDIT", "Data accessed", user_id="123", data_type="customer")
logger.info("COMPLIANCE", "GDPR consent recorded", user_id="123")
logger.info("SECURITY", "Access granted", user_id="123", resource="/admin")
```

## 📚 Next Steps

After understanding this example, try:
- **06_rotation** - Log file rotation
- **07_performance_monitoring** - Performance tracking
- **11_web_application** - Web application logging 