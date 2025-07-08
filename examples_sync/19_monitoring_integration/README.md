# 19 - Monitoring Integration

## 🎯 Overview

This example demonstrates how to integrate Hydra-Logger with monitoring systems and observability platforms. It shows:
- Integration with Prometheus metrics
- Integration with Grafana dashboards
- Integration with Jaeger tracing
- Health check monitoring
- Performance metrics collection

## 🚀 Running the Example

```bash
python main.py
```

## 📊 Expected Output

```
📊 Monitoring Integration Demo
========================================
✅ Monitoring integration demo complete! Check logs/monitoring_integration/monitoring.log.
```

### Generated Log File
Check `logs/monitoring_integration/monitoring.log` for monitoring-related logs.

## 🔑 Key Concepts

### **Monitoring Integration Benefits**
- **Observability**: Complete visibility into system behavior
- **Alerting**: Proactive notification of issues
- **Performance Tracking**: Monitor system performance metrics
- **Troubleshooting**: Quick identification of problems
- **Capacity Planning**: Understand system resource usage

### **Monitoring Components**
- **Metrics**: Numerical data about system performance
- **Logs**: Detailed event records
- **Traces**: Request flow through distributed systems
- **Alerts**: Notifications when thresholds are exceeded
- **Dashboards**: Visual representation of system state

### **Popular Monitoring Platforms**
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Jaeger**: Distributed tracing
- **Datadog**: All-in-one monitoring platform
- **New Relic**: Application performance monitoring

## 🎨 Code Example

```python
import time
import random
import psutil
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

class MonitoringLogger:
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self.metrics = {}
    
    def log_system_metrics(self):
        """Log system performance metrics."""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        self.logger.info("METRICS", "System performance metrics",
                        cpu_percent=cpu_percent,
                        memory_percent=memory.percent,
                        memory_available=memory.available,
                        disk_percent=disk.percent,
                        disk_free=disk.free,
                        timestamp=time.time())
    
    def log_application_metrics(self, operation, duration_ms, success=True):
        """Log application-specific metrics."""
        self.logger.info("METRICS", f"Application operation: {operation}",
                        operation=operation,
                        duration_ms=duration_ms,
                        success=success,
                        timestamp=time.time())
    
    def log_health_check(self, service_name, status, details=None):
        """Log health check results."""
        self.logger.info("HEALTH", f"Health check for {service_name}",
                        service=service_name,
                        status=status,
                        details=details,
                        timestamp=time.time())

def main():
    # Configure logger for monitoring integration
    config = LoggingConfig(layers={
        "MONITORING": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/monitoring_integration/monitoring.log",
                    format="json"
                )
            ]
        )
    })
    
    monitoring_logger = MonitoringLogger(config)
    
    # Simulate monitoring data collection
    for i in range(10):
        # Log system metrics
        monitoring_logger.log_system_metrics()
        
        # Log application metrics
        duration = random.randint(10, 200)
        success = random.choice([True, True, True, False])  # 75% success rate
        monitoring_logger.log_application_metrics("database_query", duration, success)
        
        # Log health checks
        services = ["database", "api", "cache", "queue"]
        for service in services:
            status = random.choice(["healthy", "healthy", "healthy", "degraded"])
            monitoring_logger.log_health_check(service, status)
        
        time.sleep(1)
```

## 🧪 Monitoring Patterns

### **Prometheus Metrics Integration**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

class PrometheusLogger:
    def __init__(self, logger):
        self.logger = logger
        
        # Define Prometheus metrics
        self.request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
        self.request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
        self.active_connections = Gauge('active_connections', 'Number of active connections')
        self.error_counter = Counter('errors_total', 'Total errors', ['type'])
    
    def log_request(self, method, endpoint, duration_seconds, status_code):
        """Log HTTP request metrics."""
        # Update Prometheus metrics
        self.request_counter.labels(method=method, endpoint=endpoint).inc()
        self.request_duration.observe(duration_seconds)
        
        # Log to Hydra-Logger
        self.logger.info("PROMETHEUS", "HTTP request processed",
                        method=method,
                        endpoint=endpoint,
                        duration_seconds=duration_seconds,
                        status_code=status_code)
    
    def log_error(self, error_type, error_message):
        """Log error metrics."""
        # Update Prometheus metrics
        self.error_counter.labels(type=error_type).inc()
        
        # Log to Hydra-Logger
        self.logger.error("PROMETHEUS", "Error occurred",
                         error_type=error_type,
                         error_message=error_message)
    
    def update_connection_count(self, count):
        """Update connection count metric."""
        self.active_connections.set(count)
        
        self.logger.info("PROMETHEUS", "Connection count updated",
                        active_connections=count)

# Usage
logger = HydraLogger()
prometheus_logger = PrometheusLogger(logger)

# Simulate requests
for i in range(100):
    method = random.choice(["GET", "POST", "PUT", "DELETE"])
    endpoint = random.choice(["/api/users", "/api/orders", "/api/products"])
    duration = random.uniform(0.01, 0.5)
    status = random.choice([200, 200, 200, 404, 500])
    
    prometheus_logger.log_request(method, endpoint, duration, status)
    
    if status >= 400:
        prometheus_logger.log_error("http_error", f"HTTP {status} error")
```

### **Grafana Dashboard Integration**
```python
class GrafanaLogger:
    def __init__(self, logger):
        self.logger = logger
        self.dashboard_metrics = {}
    
    def log_dashboard_metric(self, metric_name, value, tags=None):
        """Log metric for Grafana dashboard."""
        metric_data = {
            "metric": metric_name,
            "value": value,
            "timestamp": time.time()
        }
        
        if tags:
            metric_data["tags"] = tags
        
        self.logger.info("GRAFANA", f"Dashboard metric: {metric_name}",
                        **metric_data)
        
        # Store for dashboard
        self.dashboard_metrics[metric_name] = value
    
    def log_business_metric(self, metric_name, value, category):
        """Log business-specific metrics."""
        self.logger.info("BUSINESS", f"Business metric: {metric_name}",
                        metric=metric_name,
                        value=value,
                        category=category,
                        timestamp=time.time())
    
    def log_user_activity(self, user_id, action, duration_ms=None):
        """Log user activity metrics."""
        self.logger.info("USER_ACTIVITY", f"User activity: {action}",
                        user_id=user_id,
                        action=action,
                        duration_ms=duration_ms,
                        timestamp=time.time())

# Usage
logger = HydraLogger()
grafana_logger = GrafanaLogger(logger)

# Log various metrics
grafana_logger.log_dashboard_metric("cpu_usage", 75.5, {"host": "web-server-1"})
grafana_logger.log_dashboard_metric("memory_usage", 60.2, {"host": "web-server-1"})
grafana_logger.log_business_metric("orders_per_minute", 15, "sales")
grafana_logger.log_business_metric("active_users", 1250, "engagement")
grafana_logger.log_user_activity(12345, "login", 150)
grafana_logger.log_user_activity(12345, "purchase", 2000)
```

### **Jaeger Tracing Integration**
```python
import uuid

class JaegerLogger:
    def __init__(self, logger):
        self.logger = logger
        self.trace_id = None
        self.span_id = None
    
    def start_trace(self, operation_name):
        """Start a new trace."""
        self.trace_id = str(uuid.uuid4())
        self.span_id = str(uuid.uuid4())
        
        self.logger.info("JAEGER", f"Trace started: {operation_name}",
                        trace_id=self.trace_id,
                        span_id=self.span_id,
                        operation=operation_name,
                        event="trace_start")
    
    def log_span(self, span_name, duration_ms, tags=None):
        """Log a span within a trace."""
        span_data = {
            "trace_id": self.trace_id,
            "span_id": str(uuid.uuid4()),
            "span_name": span_name,
            "duration_ms": duration_ms,
            "event": "span"
        }
        
        if tags:
            span_data["tags"] = tags
        
        self.logger.info("JAEGER", f"Span: {span_name}",
                        **span_data)
    
    def end_trace(self, operation_name, total_duration_ms):
        """End the current trace."""
        self.logger.info("JAEGER", f"Trace ended: {operation_name}",
                        trace_id=self.trace_id,
                        operation=operation_name,
                        total_duration_ms=total_duration_ms,
                        event="trace_end")
        
        self.trace_id = None
        self.span_id = None

# Usage
logger = HydraLogger()
jaeger_logger = JaegerLogger(logger)

# Simulate distributed trace
jaeger_logger.start_trace("user_login")
jaeger_logger.log_span("validate_credentials", 50, {"service": "auth"})
jaeger_logger.log_span("fetch_user_profile", 120, {"service": "user-service"})
jaeger_logger.log_span("update_last_login", 30, {"service": "user-service"})
jaeger_logger.end_trace("user_login", 200)
```

## 📚 Use Cases

### **Application Performance Monitoring**
```python
class APMLogger:
    def __init__(self, logger):
        self.logger = logger
        self.operation_times = {}
    
    def start_operation(self, operation_name):
        """Start timing an operation."""
        self.operation_times[operation_name] = time.time()
    
    def end_operation(self, operation_name, success=True, error=None):
        """End timing an operation and log metrics."""
        if operation_name in self.operation_times:
            start_time = self.operation_times[operation_name]
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info("APM", f"Operation completed: {operation_name}",
                           operation=operation_name,
                           duration_ms=duration_ms,
                           success=success,
                           error=error)
            
            del self.operation_times[operation_name]
    
    def log_performance_alert(self, operation_name, duration_ms, threshold_ms):
        """Log performance alerts."""
        self.logger.warning("APM", f"Slow operation detected: {operation_name}",
                           operation=operation_name,
                           duration_ms=duration_ms,
                           threshold_ms=threshold_ms)

# Usage
logger = HydraLogger()
apm_logger = APMLogger(logger)

# Monitor database operations
apm_logger.start_operation("database_query")
time.sleep(0.1)  # Simulate work
apm_logger.end_operation("database_query", success=True)

# Monitor API calls
apm_logger.start_operation("api_call")
time.sleep(0.05)  # Simulate work
apm_logger.end_operation("api_call", success=True)
```

### **Health Check Monitoring**
```python
class HealthCheckLogger:
    def __init__(self, logger):
        self.logger = logger
        self.health_status = {}
    
    def check_service_health(self, service_name, check_function):
        """Perform health check for a service."""
        start_time = time.time()
        
        try:
            result = check_function()
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info("HEALTH", f"Health check passed: {service_name}",
                           service=service_name,
                           status="healthy",
                           duration_ms=duration_ms,
                           result=result)
            
            self.health_status[service_name] = "healthy"
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error("HEALTH", f"Health check failed: {service_name}",
                            service=service_name,
                            status="unhealthy",
                            duration_ms=duration_ms,
                            error=str(e))
            
            self.health_status[service_name] = "unhealthy"
    
    def log_overall_health(self):
        """Log overall system health."""
        healthy_services = sum(1 for status in self.health_status.values() if status == "healthy")
        total_services = len(self.health_status)
        
        self.logger.info("HEALTH", "Overall system health",
                        healthy_services=healthy_services,
                        total_services=total_services,
                        health_percentage=(healthy_services / total_services) * 100)

# Usage
logger = HydraLogger()
health_logger = HealthCheckLogger(logger)

# Define health check functions
def check_database():
    return {"connections": 5, "response_time": 10}

def check_api():
    return {"endpoints": 10, "response_time": 50}

def check_cache():
    return {"hit_rate": 0.85, "memory_usage": 60}

# Perform health checks
health_logger.check_service_health("database", check_database)
health_logger.check_service_health("api", check_api)
health_logger.check_service_health("cache", check_cache)
health_logger.log_overall_health()
```

### **Resource Monitoring**
```python
class ResourceMonitor:
    def __init__(self, logger):
        self.logger = logger
    
    def log_system_resources(self):
        """Log system resource usage."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        self.logger.info("RESOURCES", "System resource usage",
                        cpu_percent=cpu_percent,
                        memory_percent=memory.percent,
                        memory_used=memory.used,
                        memory_available=memory.available,
                        disk_percent=disk.percent,
                        disk_used=disk.used,
                        disk_free=disk.free,
                        network_bytes_sent=network.bytes_sent,
                        network_bytes_recv=network.bytes_recv)
    
    def log_process_resources(self, process_name):
        """Log resource usage for specific process."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if proc.info['name'] == process_name:
                    self.logger.info("RESOURCES", f"Process resource usage: {process_name}",
                                   process_name=process_name,
                                   pid=proc.info['pid'],
                                   cpu_percent=proc.info['cpu_percent'],
                                   memory_percent=proc.info['memory_percent'])
                    break
        except Exception as e:
            self.logger.error("RESOURCES", f"Error monitoring process: {process_name}",
                            error=str(e))

# Usage
logger = HydraLogger()
resource_monitor = ResourceMonitor(logger)

# Monitor system resources
resource_monitor.log_system_resources()

# Monitor specific processes
resource_monitor.log_process_resources("python")
```

## ⚡ Performance Strategies

### **1. Batch Metrics Collection**
```python
class BatchMetricsLogger:
    def __init__(self, logger, batch_size=100):
        self.logger = logger
        self.batch_size = batch_size
        self.metrics_batch = []
    
    def add_metric(self, metric_name, value, tags=None):
        """Add metric to batch."""
        metric_data = {
            "metric": metric_name,
            "value": value,
            "timestamp": time.time()
        }
        
        if tags:
            metric_data["tags"] = tags
        
        self.metrics_batch.append(metric_data)
        
        if len(self.metrics_batch) >= self.batch_size:
            self.flush_batch()
    
    def flush_batch(self):
        """Flush metrics batch to logger."""
        if self.metrics_batch:
            self.logger.info("BATCH_METRICS", f"Batch of {len(self.metrics_batch)} metrics",
                           metrics=self.metrics_batch)
            self.metrics_batch = []

# Usage
logger = HydraLogger()
batch_logger = BatchMetricsLogger(logger)

# Add metrics to batch
for i in range(1000):
    batch_logger.add_metric("request_count", i, {"endpoint": "/api/users"})
    batch_logger.add_metric("response_time", random.uniform(10, 100), {"endpoint": "/api/users"})

batch_logger.flush_batch()
```

### **2. Sampling for High-Volume Metrics**
```python
import random

class SampledMetricsLogger:
    def __init__(self, logger, sample_rate=0.1):
        self.logger = logger
        self.sample_rate = sample_rate
    
    def log_metric(self, metric_name, value, tags=None):
        """Log metric with sampling."""
        if random.random() < self.sample_rate:
            metric_data = {
                "metric": metric_name,
                "value": value,
                "timestamp": time.time(),
                "sampled": True
            }
            
            if tags:
                metric_data["tags"] = tags
            
            self.logger.info("SAMPLED_METRICS", f"Sampled metric: {metric_name}",
                           **metric_data)

# Usage
logger = HydraLogger()
sampled_logger = SampledMetricsLogger(logger, sample_rate=0.1)

# Log high-volume metrics with sampling
for i in range(10000):
    sampled_logger.log_metric("high_frequency_metric", random.random())
```

### **3. Alert Threshold Monitoring**
```python
class AlertLogger:
    def __init__(self, logger):
        self.logger = logger
        self.thresholds = {}
    
    def set_threshold(self, metric_name, threshold_value, alert_type="warning"):
        """Set threshold for a metric."""
        self.thresholds[metric_name] = {
            "value": threshold_value,
            "type": alert_type
        }
    
    def check_threshold(self, metric_name, current_value):
        """Check if metric exceeds threshold."""
        if metric_name in self.thresholds:
            threshold = self.thresholds[metric_name]
            
            if current_value > threshold["value"]:
                self.logger.warning("ALERT", f"Threshold exceeded: {metric_name}",
                                  metric=metric_name,
                                  current_value=current_value,
                                  threshold_value=threshold["value"],
                                  alert_type=threshold["type"])

# Usage
logger = HydraLogger()
alert_logger = AlertLogger(logger)

# Set thresholds
alert_logger.set_threshold("cpu_usage", 80, "warning")
alert_logger.set_threshold("memory_usage", 90, "critical")
alert_logger.set_threshold("error_rate", 0.05, "warning")

# Check thresholds
alert_logger.check_threshold("cpu_usage", 85)
alert_logger.check_threshold("memory_usage", 95)
alert_logger.check_threshold("error_rate", 0.08)
```

## 📚 Best Practices

### **1. Use Structured Logging for Metrics**
```python
def structured_metrics_logging():
    logger = HydraLogger()
    
    # Good: Structured metric logging
    logger.info("METRICS", "Application performance metric",
               metric_name="request_duration",
               value=150.5,
               unit="milliseconds",
               tags={"endpoint": "/api/users", "method": "GET"},
               timestamp=time.time())
    
    # Avoid: Unstructured metric logging
    # logger.info("METRICS", f"Request duration: 150.5ms for /api/users")
```

### **2. Include Context with Metrics**
```python
def contextual_metrics_logging():
    logger = HydraLogger()
    
    # Include relevant context
    logger.info("METRICS", "Database query performance",
               operation="user_lookup",
               duration_ms=120,
               rows_returned=1,
               database="postgresql",
               table="users",
               query_type="SELECT")
```

### **3. Monitor Metric Collection Performance**
```python
def performance_monitored_logging():
    logger = HydraLogger()
    
    start_time = time.time()
    
    # Collect metrics
    metrics = {
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
    
    collection_time = (time.time() - start_time) * 1000
    
    # Log metrics with collection performance
    logger.info("METRICS", "System metrics collected",
               metrics=metrics,
               collection_time_ms=collection_time)
```

## 📚 Next Steps

After understanding this example, try:
- **16_cloud_integration** - Cloud platform integration
- **17_database_logging** - Database-specific logging
- **18_queue_based** - Queue-based logging patterns 