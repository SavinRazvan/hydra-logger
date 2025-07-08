# 16 - Cloud Integration

## 🎯 Overview

This example demonstrates how to integrate Hydra-Logger with cloud logging services. It shows:
- Integration with AWS CloudWatch
- Integration with Google Cloud Logging
- Integration with Azure Monitor
- Best practices for cloud logging
- Structured logging for cloud platforms

## 🚀 Running the Example

```bash
python main.py
```

## 📊 Expected Output

```
☁️ Cloud Integration Demo
========================================
✅ Cloud integration demo complete! Check logs/cloud_integration/cloud.log.
```

### Generated Log File
Check `logs/cloud_integration/cloud.log` for cloud-formatted log messages.

## 🔑 Key Concepts

### **Cloud Logging Benefits**
- Centralized log management
- Real-time monitoring and alerting
- Scalable storage and processing
- Advanced search and analytics
- Integration with other cloud services

### **Cloud-Specific Considerations**
- **Structured Logging**: Cloud platforms prefer JSON/structured logs
- **Log Levels**: Cloud platforms have specific level mappings
- **Metadata**: Include relevant context (region, service, etc.)
- **Cost**: Monitor log volume to control costs
- **Security**: Ensure sensitive data is not logged

### **Popular Cloud Platforms**
- **AWS CloudWatch**: Amazon's logging service
- **Google Cloud Logging**: Google's logging service
- **Azure Monitor**: Microsoft's logging service
- **Datadog**: Third-party monitoring platform
- **Splunk**: Enterprise log management

## 🎨 Code Example

```python
import json
import time
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def cloud_formatted_log(logger):
    """Demonstrate cloud-formatted logging."""
    
    # Structured log for cloud platforms
    cloud_data = {
        "service": "user-service",
        "region": "us-west-2",
        "environment": "production",
        "version": "1.2.3",
        "timestamp": time.time(),
        "user_id": 12345,
        "action": "login",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "session_id": "sess_abc123"
    }
    
    logger.info("CLOUD", "User login successful", **cloud_data)

def main():
    # Configure logger for cloud integration
    config = LoggingConfig(layers={
        "CLOUD": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/cloud_integration/cloud.log",
                    format="json"  # Use JSON for cloud platforms
                )
            ]
        )
    })
    
    logger = HydraLogger(config)
    
    # Demonstrate cloud-formatted logging
    cloud_formatted_log(logger)
```

## 🧪 Cloud Platform Integrations

### **AWS CloudWatch Integration**
```python
import boto3
import json

class CloudWatchLogger:
    def __init__(self, log_group, log_stream):
        self.client = boto3.client('logs')
        self.log_group = log_group
        self.log_stream = log_stream
    
    def log(self, message, level="INFO", **kwargs):
        log_entry = {
            "timestamp": int(time.time() * 1000),
            "level": level,
            "message": message,
            **kwargs
        }
        
        try:
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[{
                    'timestamp': log_entry['timestamp'],
                    'message': json.dumps(log_entry)
                }]
            )
        except Exception as e:
            print(f"CloudWatch logging failed: {e}")

# Usage
cloudwatch = CloudWatchLogger("my-app", "production")
cloudwatch.log("User login", user_id=123, action="login")
```

### **Google Cloud Logging Integration**
```python
from google.cloud import logging
import json

class GoogleCloudLogger:
    def __init__(self, project_id):
        self.client = logging.Client(project=project_id)
        self.logger = self.client.logger('my-app')
    
    def log(self, message, level="INFO", **kwargs):
        log_entry = {
            "severity": level,
            "message": message,
            "timestamp": time.time(),
            **kwargs
        }
        
        try:
            self.logger.log_struct(log_entry)
        except Exception as e:
            print(f"Google Cloud logging failed: {e}")

# Usage
gcp_logger = GoogleCloudLogger("my-project-id")
gcp_logger.log("User login", user_id=123, action="login")
```

### **Azure Monitor Integration**
```python
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

class AzureLogger:
    def __init__(self, connection_string):
        self.handler = AzureLogHandler(
            connection_string=connection_string
        )
        self.logger = logging.getLogger('azure-logger')
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)
    
    def log(self, message, level="INFO", **kwargs):
        log_entry = {
            "message": message,
            "level": level,
            **kwargs
        }
        
        try:
            self.logger.info(json.dumps(log_entry))
        except Exception as e:
            print(f"Azure logging failed: {e}")

# Usage
azure_logger = AzureLogger("InstrumentationKey=...")
azure_logger.log("User login", user_id=123, action="login")
```

## 📚 Use Cases

### **Microservices Logging**
```python
def microservice_logging():
    logger = HydraLogger()
    
    # Service-specific context
    service_context = {
        "service": "user-service",
        "version": "1.2.3",
        "instance_id": "us-west-2-1",
        "request_id": "req_abc123"
    }
    
    logger.info("MICROSERVICE", "Request received", 
               endpoint="/api/users",
               method="POST",
               **service_context)
```

### **Application Performance Monitoring**
```python
import time

def apm_logging():
    logger = HydraLogger()
    
    start_time = time.time()
    
    # Simulate work
    time.sleep(0.1)
    
    duration = time.time() - start_time
    
    logger.info("APM", "Database query completed",
               operation="user_lookup",
               duration_ms=duration * 1000,
               rows_returned=1)
```

### **Security Event Logging**
```python
def security_logging():
    logger = HydraLogger()
    
    logger.warning("SECURITY", "Failed login attempt",
                  user_id=123,
                  ip_address="192.168.1.100",
                  reason="invalid_password",
                  attempt_count=3)
```

## ⚡ Performance Strategies

### **1. Batch Logging for Cloud**
```python
class CloudBatchLogger:
    def __init__(self, cloud_logger, batch_size=100):
        self.cloud_logger = cloud_logger
        self.batch_size = batch_size
        self.batch = []
    
    def log(self, message, **kwargs):
        self.batch.append({
            "message": message,
            "timestamp": time.time(),
            **kwargs
        })
        
        if len(self.batch) >= self.batch_size:
            self.flush()
    
    def flush(self):
        if self.batch:
            # Send batch to cloud
            for entry in self.batch:
                self.cloud_logger.log(**entry)
            self.batch = []
```

### **2. Async Cloud Logging**
```python
import asyncio
import aiohttp

class AsyncCloudLogger:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def log(self, message, **kwargs):
        if not self.session:
            return
        
        log_data = {
            "message": message,
            "timestamp": time.time(),
            **kwargs
        }
        
        try:
            async with self.session.post(
                self.endpoint, 
                json=log_data
            ) as response:
                if response.status != 200:
                    print(f"Log failed: {response.status}")
        except Exception as e:
            print(f"Async logging failed: {e}")
```

### **3. Structured Logging**
```python
def structured_cloud_logging():
    logger = HydraLogger()
    
    # Structured data for cloud platforms
    structured_data = {
        "event_type": "user_action",
        "user_id": 12345,
        "session_id": "sess_abc123",
        "action": "login",
        "result": "success",
        "duration_ms": 150,
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "timestamp": time.time(),
        "service": "auth-service",
        "version": "1.2.3"
    }
    
    logger.info("STRUCTURED", "User login event", **structured_data)
```

## 🔍 Monitoring and Alerting

### **Log Volume Monitoring**
```python
class LogVolumeMonitor:
    def __init__(self, logger):
        self.logger = logger
        self.log_count = 0
        self.last_reset = time.time()
    
    def log(self, message, **kwargs):
        self.log_count += 1
        
        # Check volume every minute
        current_time = time.time()
        if current_time - self.last_reset >= 60:
            if self.log_count > 1000:  # Alert threshold
                self.logger.warning("VOLUME", "High log volume detected",
                                  logs_per_minute=self.log_count)
            
            self.log_count = 0
            self.last_reset = current_time
        
        self.logger.info("APP", message, **kwargs)
```

### **Error Rate Monitoring**
```python
class ErrorRateMonitor:
    def __init__(self, logger):
        self.logger = logger
        self.error_count = 0
        self.total_count = 0
    
    def log(self, message, level="INFO", **kwargs):
        self.total_count += 1
        
        if level in ["ERROR", "CRITICAL"]:
            self.error_count += 1
        
        # Check error rate every 100 logs
        if self.total_count % 100 == 0:
            error_rate = self.error_count / self.total_count
            if error_rate > 0.05:  # 5% error rate threshold
                self.logger.warning("ERROR_RATE", "High error rate detected",
                                  error_rate=error_rate,
                                  error_count=self.error_count,
                                  total_count=self.total_count)
        
        self.logger.log(level, "APP", message, **kwargs)
```

## 📚 Best Practices

### **1. Include Relevant Context**
```python
def contextual_logging():
    logger = HydraLogger()
    
    # Include all relevant context
    context = {
        "request_id": "req_abc123",
        "user_id": 12345,
        "session_id": "sess_xyz789",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "service": "user-service",
        "version": "1.2.3",
        "environment": "production",
        "region": "us-west-2"
    }
    
    logger.info("REQUEST", "API call processed", **context)
```

### **2. Use Appropriate Log Levels**
```python
def level_appropriate_logging():
    logger = HydraLogger()
    
    # DEBUG: Detailed debugging information
    logger.debug("DEBUG", "Processing user data", user_id=123)
    
    # INFO: General application flow
    logger.info("INFO", "User login successful", user_id=123)
    
    # WARNING: Something unexpected but handled
    logger.warning("WARNING", "Rate limit approaching", user_id=123)
    
    # ERROR: Error that needs attention
    logger.error("ERROR", "Database connection failed", user_id=123)
    
    # CRITICAL: System failure
    logger.critical("CRITICAL", "Service unavailable", user_id=123)
```

### **3. Avoid Sensitive Data**
```python
def secure_logging():
    logger = HydraLogger()
    
    # Good: Log user action without sensitive data
    logger.info("USER", "User login attempt",
               user_id=123,
               action="login",
               success=True)
    
    # Avoid: Logging sensitive information
    # logger.info("USER", "User login", password="secret123")  # BAD!
```

## 📚 Configuration Examples

### **AWS CloudWatch Configuration**
```python
# AWS CloudWatch configuration
aws_config = {
    "log_group": "/my-app/production",
    "log_stream": "application-logs",
    "region": "us-west-2",
    "retention_days": 14
}
```

### **Google Cloud Logging Configuration**
```python
# Google Cloud Logging configuration
gcp_config = {
    "project_id": "my-project-id",
    "log_name": "my-app-logs",
    "resource_type": "gce_instance"
}
```

### **Azure Monitor Configuration**
```python
# Azure Monitor configuration
azure_config = {
    "connection_string": "InstrumentationKey=...",
    "log_name": "my-app-logs"
}
```

## 📚 Next Steps

After understanding this example, try:
- **17_database_logging** - Database-specific logging
- **18_queue_based** - Queue-based logging patterns
- **19_monitoring_integration** - Monitoring system integration 