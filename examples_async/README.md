# Hydra-Logger Async Examples

This directory contains comprehensive examples of using Hydra-Logger's async capabilities, from basic setup to advanced enterprise patterns.

## 📚 **Learning Path**

### **🎯 Level 1: Getting Started (01-04)**
Start here if you're new to async logging with Hydra-Logger.

- **01_basic_setup/** - Simple async logger initialization
- **02_console_only/** - Async logging to console only  
- **03_file_only/** - Async logging to file only
- **04_simple_config/** - Basic configuration with one layer

### **🔧 Level 2: Common Use Cases (05-10)**
Learn practical patterns for everyday async logging needs.

- **05_multiple_layers/** - Different log levels for different purposes
- **06_rotation/** - File rotation with async logging
- **07_performance_monitoring/** - Async performance tracking
- **08_error_handling/** - Graceful error handling in async context
- **09_custom_formatters/** - Custom log formats for async logging
- **10_environment_detection/** - Auto-detection in async scenarios

### **🚀 Level 3: Production Ready (11-20)**
Advanced patterns for production async applications.

- **11_web_application/** - FastAPI/Django async web app logging
- **12_microservices/** - Distributed logging across services
- **13_high_concurrency/** - Handling thousands of concurrent log messages
- **14_backpressure_handling/** - Managing log queue overflow
- **15_structured_logging/** - JSON/structured logs for async systems
- **16_cloud_integration/** - AWS CloudWatch, GCP, Azure integration
- **17_database_logging/** - Async database logging (PostgreSQL, MongoDB)
- **18_queue_based/** - Redis/RabbitMQ async queue logging
- **19_monitoring_integration/** - Prometheus, Grafana integration
- **20_enterprise_patterns/** - Multi-tenant, audit trails, compliance

### **🔬 Level 4: Expert Scenarios (21-30)**
Specialized patterns for complex async systems.

- **21_machine_learning/** - ML pipeline async logging
- **22_streaming_data/** - Real-time data processing logs
- **23_serverless/** - AWS Lambda, Azure Functions logging
- **24_kubernetes/** - K8s pod/container async logging
- **25_observability/** - OpenTelemetry, Jaeger integration
- **26_security_audit/** - PII detection, security event logging
- **27_compliance/** - GDPR, SOX, HIPAA compliant logging
- **28_disaster_recovery/** - Backup, replication, failover logging
- **29_cost_optimization/** - Log storage and processing optimization
- **30_advanced_patterns/** - Custom sinks, plugins, extensions

## 🎯 **Example Categories**

### **📊 By Complexity**
- **Basic**: 01-04 (Simple setup and configuration)
- **Intermediate**: 05-10 (Common patterns and features)
- **Advanced**: 11-20 (Production-ready implementations)
- **Expert**: 21-30 (Specialized and complex scenarios)

### **🏗️ By Architecture**
- **Single Application**: 01-10 (Monolithic async apps)
- **Distributed Systems**: 11-20 (Microservices, cloud-native)
- **Specialized Platforms**: 21-30 (ML, serverless, K8s)

### **💼 By Use Case**
- **Development**: 01-10 (Local development and testing)
- **Production**: 11-20 (Live applications and services)
- **Enterprise**: 21-30 (Large-scale, compliance, security)

## 🚀 **Quick Start**

1. **Start with basic setup**:
   ```bash
   cd 01_basic_setup
   python main.py
   ```

2. **Explore by complexity**:
   - Basic: 01-04
   - Intermediate: 05-10
   - Advanced: 11-20
   - Expert: 21-30

3. **Find your use case**:
   - Web apps: 11_web_application
   - Microservices: 12_microservices
   - High concurrency: 13_high_concurrency
   - Cloud integration: 16_cloud_integration

## 📋 **Each Example Includes**

- **`main.py`** - Main example code
- **`config.py`** - Configuration examples
- **`requirements.txt`** - Dependencies (if needed)
- **`README.md`** - Detailed explanation
- **`output/`** - Sample output and logs
- **`tests/`** - Example tests (where applicable)

## 🔧 **Common Patterns Covered**

### **Async Logger Setup**
```python
from hydra_logger import AsyncHydraLogger

# Basic setup
logger = AsyncHydraLogger()

# With configuration
logger = AsyncHydraLogger(
    enable_performance_monitoring=True,
    redact_sensitive=True,
    queue_size=1000,
    batch_size=100
)
```

### **Async Logging Methods**
```python
# Basic logging
await logger.info("APP", "User logged in")

# With context
await logger.info("API", "Request processed", extra={
    "user_id": 123,
    "duration_ms": 45
})

# Error handling
await logger.error("DB", "Connection failed", exc_info=True)
```

### **Performance Monitoring**
```python
# Get async statistics
stats = await logger.get_async_performance_statistics()
print(f"Messages processed: {stats['total_messages']}")
print(f"Average processing time: {stats['avg_processing_time']}ms")
```

## 🎯 **Key Benefits of Async Logging**

1. **Non-blocking**: Logging doesn't block your application
2. **High performance**: Batch processing and buffering
3. **Scalability**: Handle thousands of log messages per second
4. **Reliability**: Built-in error handling and recovery
5. **Flexibility**: Multiple destinations and formats
6. **Monitoring**: Built-in performance tracking

## 🔍 **Finding the Right Example**

### **By Application Type**
- **Web Application**: 11_web_application
- **API Service**: 12_microservices
- **Background Job**: 13_high_concurrency
- **Data Pipeline**: 22_streaming_data

### **By Infrastructure**
- **Cloud Native**: 16_cloud_integration
- **Kubernetes**: 24_kubernetes
- **Serverless**: 23_serverless
- **On-premises**: 20_enterprise_patterns

### **By Requirements**
- **High Performance**: 13_high_concurrency, 14_backpressure_handling
- **Security**: 26_security_audit, 27_compliance
- **Observability**: 25_observability, 19_monitoring_integration
- **Cost Optimization**: 29_cost_optimization

## 📖 **Documentation Integration**

Each example is designed to be:
- **Self-contained**: Run independently
- **Well-documented**: Clear explanations
- **Production-ready**: Best practices included
- **Extensible**: Easy to modify for your needs

## 🤝 **Contributing**

When adding new examples:
1. Follow the naming convention: `XX_category_name/`
2. Include all required files (main.py, README.md, etc.)
3. Add to this README with appropriate categorization
4. Test the example thoroughly
5. Document any dependencies or setup requirements

---

**Start exploring!** Each example builds upon the previous ones, so follow the learning path for the best experience. 