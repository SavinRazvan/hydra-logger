# Examples Guide

This comprehensive guide provides detailed examples of how to use Hydra-Logger in various real-world scenarios, demonstrating different configurations, log formats, and use cases.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Web Application Examples](#web-application-examples)
- [Microservices Examples](#microservices-examples)
- [Database Application Examples](#database-application-examples)
- [Security and Monitoring Examples](#security-and-monitoring-examples)
- [Analytics and Reporting Examples](#analytics-and-reporting-examples)
- [Enterprise Integration Examples](#enterprise-integration-examples)
- [Performance Optimization Examples](#performance-optimization-examples)

## Basic Examples

### Simple Logging with Default Configuration

```python
from hydra_logger import HydraLogger

# Create logger with default configuration
logger = HydraLogger()

# Log messages to different levels
logger.info("DEFAULT", "Application started successfully")
logger.debug("DEFAULT", "Debug information for development")
logger.warning("DEFAULT", "Configuration file not found, using defaults")
logger.error("DEFAULT", "Database connection failed")
logger.critical("DEFAULT", "System shutdown initiated")
```

### Custom Configuration with Multiple Formats

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create custom configuration with different formats
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
                    type="console",
                    level="WARNING",
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

# Create logger with custom configuration
logger = HydraLogger(config)

# Use the logger
logger.info("APP", "Application started with custom configuration")
logger.debug("DEBUG", "Detailed debug information")
logger.warning("APP", "This warning appears in both file and console")
```

### Configuration File Usage

```python
from hydra_logger import HydraLogger

# Load configuration from YAML file
logger = HydraLogger.from_config("config/logging.yaml")

# Use the logger
logger.info("APP", "Application loaded from configuration file")
logger.debug("API", "API endpoint called")
logger.error("SECURITY", "Authentication failed")
```

## Web Application Examples

### Flask Application with Multi-Format Logging

```python
from flask import Flask, request, jsonify
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time

# Create Flask app
app = Flask(__name__)

# Configure logging for web application
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app/main.log",
                    format="text"
                ),
                LogDestination(
                    type="console",
                    format="json"
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
        ),
        "SECURITY": LogLayer(
            level="WARNING",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/security/auth.log",
                    format="syslog"
                )
            ]
        ),
        "PERFORMANCE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/performance/metrics.csv",
                    format="csv"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

@app.before_request
def log_request():
    """Log incoming requests for monitoring."""
    start_time = time.time()
    request.start_time = start_time
    
    logger.info("API", f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def log_response(response):
    """Log response times and status codes."""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        logger.info("PERFORMANCE", f"Response time: {duration:.3f}s, Status: {response.status_code}")
    
    return response

@app.route('/api/users', methods=['GET'])
def get_users():
    logger.info("API", f"GET /api/users - IP: {request.remote_addr}")
    
    try:
        # Simulate database query
        users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        logger.debug("APP", f"Retrieved {len(users)} users from database")
        
        return jsonify(users)
    except Exception as e:
        logger.error("API", f"Error retrieving users: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    logger.info("API", f"POST /api/users - IP: {request.remote_addr}")
    
    try:
        user_data = request.get_json()
        logger.info("SECURITY", f"Creating user: {user_data.get('name', 'Unknown')}")
        
        # Simulate user creation
        new_user = {"id": 3, "name": user_data.get('name')}
        logger.info("APP", f"User created with ID: {new_user['id']}")
        
        return jsonify(new_user), 201
    except Exception as e:
        logger.error("API", f"Error creating user: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    logger.info("API", f"POST /api/auth/login - IP: {request.remote_addr}")
    
    try:
        auth_data = request.get_json()
        username = auth_data.get('username')
        
        # Simulate authentication
        if username == "admin":
            logger.warning("SECURITY", f"Failed login attempt for user: {username}")
            return jsonify({"error": "Invalid credentials"}), 401
        else:
            logger.info("SECURITY", f"Successful login for user: {username}")
            return jsonify({"message": "Login successful"})
    except Exception as e:
        logger.error("SECURITY", f"Authentication error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500

if __name__ == '__main__':
    logger.info("APP", "Flask application starting on port 5000")
    app.run(debug=True)
```

### Django Application with Structured Logging

```python
# settings.py
LOGGING_CONFIG = {
    'default_level': 'INFO',
    'layers': {
        'APP': {
            'level': 'INFO',
            'destinations': [
                {
                    'type': 'file',
                    'path': 'logs/django/app.log',
                    'format': 'text'
                }
            ]
        },
        'API': {
            'level': 'INFO',
            'destinations': [
                {
                    'type': 'file',
                    'path': 'logs/django/api.json',
                    'format': 'json'
                }
            ]
        },
        'SECURITY': {
            'level': 'WARNING',
            'destinations': [
                {
                    'type': 'file',
                    'path': 'logs/django/security.log',
                    'format': 'syslog'
                }
            ]
        }
    }
}

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from hydra_logger import HydraLogger

logger = HydraLogger.from_config("config/django_logging.yaml")

@csrf_exempt
@require_http_methods(["GET"])
def get_users(request):
    logger.info("API", f"GET /api/users - IP: {request.META.get('REMOTE_ADDR')}")
    
    try:
        # Simulate database query
        users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        logger.debug("APP", f"Retrieved {len(users)} users from database")
        
        return JsonResponse(users, safe=False)
    except Exception as e:
        logger.error("API", f"Error retrieving users: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    logger.info("API", f"POST /api/users - IP: {request.META.get('REMOTE_ADDR')}")
    
    try:
        user_data = json.loads(request.body)
        logger.info("SECURITY", f"Creating user: {user_data.get('name', 'Unknown')}")
        
        # Simulate user creation
        new_user = {"id": 3, "name": user_data.get('name')}
        logger.info("APP", f"User created with ID: {new_user['id']}")
        
        return JsonResponse(new_user, status=201)
    except Exception as e:
        logger.error("API", f"Error creating user: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
```

## Microservices Examples

### API Service with JSON Logging

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time

# Create FastAPI app
app = FastAPI()

# Configure logging for microservice
config = LoggingConfig(
    layers={
        "SERVICE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/service/service.log",
                    format="text"
                ),
                LogDestination(
                    type="console",
                    format="json"
                )
            ]
        ),
        "API": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/service/api.json",
                    format="json"
                )
            ]
        ),
        "EXTERNAL": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/service/external.json",
                    format="json"
                )
            ]
        ),
        "MONITORING": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/service/monitoring.gelf",
                    format="gelf"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

class UserCreate(BaseModel):
    name: str
    email: str

@app.on_event("startup")
async def startup_event():
    logger.info("SERVICE", "User service starting up")
    logger.info("MONITORING", "Service health check initiated")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("SERVICE", "User service shutting down")

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    logger.info("API", f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info("API", f"Response: {response.status_code} in {duration:.3f}s")
    
    return response

@app.get("/api/users")
async def get_users():
    logger.info("API", "GET /api/users endpoint called")
    
    try:
        # Simulate external API call
        logger.debug("EXTERNAL", "Calling user database service")
        
        users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        logger.info("API", f"Retrieved {len(users)} users")
        
        return {"users": users}
    except Exception as e:
        logger.error("API", f"Error retrieving users: {str(e)}")
        logger.warning("MONITORING", "Service degradation detected")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/users")
async def create_user(user: UserCreate):
    logger.info("API", f"POST /api/users - Creating user: {user.name}")
    
    try:
        # Simulate user creation
        new_user = {"id": 3, "name": user.name, "email": user.email}
        logger.info("API", f"User created successfully: {new_user}")
        
        return new_user
    except Exception as e:
        logger.error("API", f"Error creating user: {str(e)}")
        logger.error("MONITORING", "Service failure detected")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    logger.info("MONITORING", "Health check requested")
    return {"status": "healthy"}
```

## Database Application Examples

### SQLAlchemy Integration with Multi-Format Logging

```python
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
from datetime import datetime

Base = declarative_base()

# Configure logging for database operations
config = LoggingConfig(
    layers={
        "DB": LogLayer(
            level="DEBUG",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/database/queries.log",
                    format="text"
                ),
                LogDestination(
                    type="file",
                    path="logs/database/performance.csv",
                    format="csv"
                )
            ]
        ),
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app/main.log",
                    format="text"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

class UserService:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logger.info("DB", f"Database connection established: {db_url}")
    
    def create_user(self, name, email):
        start_time = datetime.utcnow()
        logger.info("DB", f"Creating user: {name} ({email})")
        
        try:
            user = User(name=name, email=email)
            self.session.add(user)
            self.session.commit()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info("DB", f"User created successfully with ID: {user.id}")
            logger.info("DB", f"Query execution time: {duration:.3f}s")
            
            return user
        except Exception as e:
            logger.error("DB", f"Error creating user: {str(e)}")
            self.session.rollback()
            raise
    
    def get_user(self, user_id):
        start_time = datetime.utcnow()
        logger.debug("DB", f"Retrieving user with ID: {user_id}")
        
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            if user:
                logger.debug("DB", f"User found: {user.name}")
                logger.info("DB", f"Query execution time: {duration:.3f}s")
            else:
                logger.warning("DB", f"User not found: {user_id}")
            
            return user
        except Exception as e:
            logger.error("DB", f"Error retrieving user: {str(e)}")
            raise

    def get_all_users(self):
        start_time = datetime.utcnow()
        logger.debug("DB", "Retrieving all users")
        
        try:
            users = self.session.query(User).all()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info("DB", f"Retrieved {len(users)} users")
            logger.info("DB", f"Query execution time: {duration:.3f}s")
            
            return users
        except Exception as e:
            logger.error("DB", f"Error retrieving users: {str(e)}")
            raise
    
    def update_user(self, user_id, **kwargs):
        start_time = datetime.utcnow()
        logger.info("DB", f"Updating user {user_id} with: {kwargs}")
        
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                self.session.commit()
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info("DB", f"User {user_id} updated successfully")
                logger.info("DB", f"Query execution time: {duration:.3f}s")
            else:
                logger.warning("DB", f"User not found for update: {user_id}")
            
            return user
    except Exception as e:
            logger.error("DB", f"Error updating user: {str(e)}")
            self.session.rollback()
        raise

    def delete_user(self, user_id):
        start_time = datetime.utcnow()
        logger.info("DB", f"Deleting user {user_id}")
        
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                self.session.delete(user)
                self.session.commit()
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info("DB", f"User {user_id} deleted successfully")
                logger.info("DB", f"Query execution time: {duration:.3f}s")
            else:
                logger.warning("DB", f"User not found for deletion: {user_id}")
            
            return user
    except Exception as e:
            logger.error("DB", f"Error deleting user: {str(e)}")
            self.session.rollback()
        raise

# Usage example
if __name__ == "__main__":
    # Initialize service
    service = UserService("sqlite:///users.db")
    
    # Create users
    user1 = service.create_user("John Doe", "john@example.com")
    user2 = service.create_user("Jane Smith", "jane@example.com")
    
    # Retrieve users
    all_users = service.get_all_users()
    user = service.get_user(1)
    
    # Update user
    service.update_user(1, name="John Updated")
    
    # Delete user
    service.delete_user(2)
    
    logger.info("APP", "Database operations completed successfully")
```

## Security and Monitoring Examples

### Security Event Logging

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
from datetime import datetime

# Configure security-focused logging
config = LoggingConfig(
    layers={
        "SECURITY": LogLayer(
            level="WARNING",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/security/events.log",
                    format="syslog"
                ),
                LogDestination(
                    type="file",
                    path="logs/security/alerts.json",
                    format="json"
                )
            ]
        ),
        "AUTH": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/security/auth.log",
                    format="syslog"
                )
            ]
        ),
        "MONITORING": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/monitoring/alerts.gelf",
                    format="gelf"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

class SecurityMonitor:
    def __init__(self):
        self.failed_attempts = {}
        self.blocked_ips = set()
    
    def log_login_attempt(self, username, ip_address, success=True):
        """Log authentication attempts."""
        if success:
            logger.info("AUTH", f"Successful login: {username} from {ip_address}")
        else:
            logger.warning("AUTH", f"Failed login attempt: {username} from {ip_address}")
            
            # Track failed attempts
            if ip_address not in self.failed_attempts:
                self.failed_attempts[ip_address] = 0
            self.failed_attempts[ip_address] += 1
            
            # Block IP after 5 failed attempts
            if self.failed_attempts[ip_address] >= 5:
                self.block_ip(ip_address)
    
    def block_ip(self, ip_address):
        """Block an IP address due to suspicious activity."""
        if ip_address not in self.blocked_ips:
            self.blocked_ips.add(ip_address)
            logger.error("SECURITY", f"IP address blocked: {ip_address} - Multiple failed login attempts")
            logger.warning("MONITORING", f"Security alert: IP {ip_address} blocked")
    
    def log_suspicious_activity(self, activity_type, details):
        """Log suspicious activities."""
        logger.warning("SECURITY", f"Suspicious activity detected: {activity_type} - {details}")
        logger.warning("MONITORING", f"Security alert: {activity_type}")
    
    def log_data_access(self, user, resource, action):
        """Log data access events."""
        logger.info("SECURITY", f"Data access: {user} {action} {resource}")
    
    def log_configuration_change(self, user, change_details):
        """Log configuration changes."""
        logger.warning("SECURITY", f"Configuration change by {user}: {change_details}")

# Usage example
security_monitor = SecurityMonitor()

# Simulate security events
security_monitor.log_login_attempt("admin", "192.168.1.100", success=False)
security_monitor.log_login_attempt("admin", "192.168.1.100", success=False)
security_monitor.log_login_attempt("admin", "192.168.1.100", success=False)
security_monitor.log_login_attempt("admin", "192.168.1.100", success=False)
security_monitor.log_login_attempt("admin", "192.168.1.100", success=False)

security_monitor.log_suspicious_activity("SQL Injection Attempt", "query: SELECT * FROM users WHERE id = 1 OR 1=1")
security_monitor.log_data_access("john.doe", "user_profiles", "read")
security_monitor.log_configuration_change("admin", "Changed password policy")
```

## Analytics and Reporting Examples

### Performance Metrics Collection

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import psutil
import threading

# Configure analytics-focused logging
config = LoggingConfig(
    layers={
        "PERFORMANCE": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/analytics/performance.csv",
                    format="csv"
                )
            ]
        ),
        "METRICS": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/analytics/metrics.json",
                    format="json"
                )
            ]
        ),
        "MONITORING": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/monitoring/system.gelf",
                    format="gelf"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

class PerformanceMonitor:
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start continuous performance monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("MONITORING", "Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("MONITORING", "Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Continuous monitoring loop."""
        while self.monitoring:
            self.collect_system_metrics()
            time.sleep(60)  # Collect metrics every minute
    
    def collect_system_metrics(self):
        """Collect system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024**3)  # GB
            memory_total = memory.total / (1024**3)  # GB
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used / (1024**3)  # GB
            disk_total = disk.total / (1024**3)  # GB
            
            # Network metrics
            network = psutil.net_io_counters()
            bytes_sent = network.bytes_sent
            bytes_recv = network.bytes_recv
            
            # Log performance metrics
            logger.info("PERFORMANCE", f"CPU Usage: {cpu_percent}%")
            logger.info("PERFORMANCE", f"Memory Usage: {memory_percent}%")
            logger.info("PERFORMANCE", f"Disk Usage: {disk_percent}%")
            
            # Log detailed metrics as JSON
            metrics = {
                "timestamp": time.time(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "used_gb": round(memory_used, 2),
                    "total_gb": round(memory_total, 2)
                },
                "disk": {
                    "percent": disk_percent,
                    "used_gb": round(disk_used, 2),
                    "total_gb": round(disk_total, 2)
                },
                "network": {
                    "bytes_sent": bytes_sent,
                    "bytes_recv": bytes_recv
                }
            }
            
            logger.info("METRICS", f"System metrics: {metrics}")
            
            # Alert on high usage
            if cpu_percent > 80:
                logger.warning("MONITORING", f"High CPU usage detected: {cpu_percent}%")
            
            if memory_percent > 85:
                logger.warning("MONITORING", f"High memory usage detected: {memory_percent}%")
            
            if disk_percent > 90:
                logger.warning("MONITORING", f"High disk usage detected: {disk_percent}%")
                
    except Exception as e:
            logger.error("MONITORING", f"Error collecting metrics: {str(e)}")
    
    def log_api_performance(self, endpoint, method, duration, status_code):
        """Log API performance metrics."""
        logger.info("PERFORMANCE", f"API {method} {endpoint}: {duration:.3f}s, Status: {status_code}")
        
        # Log detailed API metrics
        api_metrics = {
            "endpoint": endpoint,
            "method": method,
            "duration": duration,
            "status_code": status_code,
            "timestamp": time.time()
        }
        
        logger.info("METRICS", f"API performance: {api_metrics}")
    
    def log_database_performance(self, query, duration, rows_affected):
        """Log database performance metrics."""
        logger.info("PERFORMANCE", f"Database query: {duration:.3f}s, Rows: {rows_affected}")
        
        # Log detailed database metrics
        db_metrics = {
            "query": query,
            "duration": duration,
            "rows_affected": rows_affected,
            "timestamp": time.time()
        }
        
        logger.info("METRICS", f"Database performance: {db_metrics}")

# Usage example
performance_monitor = PerformanceMonitor()

# Start monitoring
performance_monitor.start_monitoring()

# Simulate API calls
performance_monitor.log_api_performance("/api/users", "GET", 0.150, 200)
performance_monitor.log_api_performance("/api/users", "POST", 0.250, 201)
performance_monitor.log_api_performance("/api/users/1", "GET", 0.075, 200)

# Simulate database operations
performance_monitor.log_database_performance("SELECT * FROM users", 0.050, 100)
performance_monitor.log_database_performance("INSERT INTO users", 0.100, 1)

# Stop monitoring after some time
time.sleep(120)  # Monitor for 2 minutes
performance_monitor.stop_monitoring()
```

## Enterprise Integration Examples

### Graylog Integration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Configure logging for Graylog integration
        config = LoggingConfig(
            layers={
        "APPLICATION": LogLayer(
            level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                    path="logs/app/main.log",
                    format="text"
                ),
                LogDestination(
                    type="file",
                    path="logs/graylog/app.gelf",
                    format="gelf"
                )
            ]
        ),
        "SECURITY": LogLayer(
            level="WARNING",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/security/events.log",
                    format="syslog"
                ),
                LogDestination(
                    type="file",
                    path="logs/graylog/security.gelf",
                    format="gelf"
                )
            ]
        ),
        "MONITORING": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/graylog/monitoring.gelf",
                    format="gelf"
                        )
                    ]
                )
            }
        )

logger = HydraLogger(config)

class EnterpriseApplication:
    def __init__(self):
        logger.info("APPLICATION", "Enterprise application initialized")
    
    def process_business_logic(self, data):
        """Process business logic with comprehensive logging."""
        logger.info("APPLICATION", f"Processing business logic: {data}")
        
        try:
            # Simulate business processing
            result = self._validate_data(data)
            if result:
                processed_data = self._transform_data(data)
                logger.info("APPLICATION", f"Business logic completed successfully")
                return processed_data
            else:
                logger.warning("APPLICATION", "Data validation failed")
                return None
        except Exception as e:
            logger.error("APPLICATION", f"Business logic error: {str(e)}")
            raise
    
    def _validate_data(self, data):
        """Validate input data."""
        logger.debug("APPLICATION", f"Validating data: {data}")
        return True  # Simulate validation
    
    def _transform_data(self, data):
        """Transform data according to business rules."""
        logger.debug("APPLICATION", f"Transforming data: {data}")
        return f"processed_{data}"
    
    def handle_security_event(self, event_type, details):
        """Handle security events with enterprise logging."""
        logger.warning("SECURITY", f"Security event: {event_type} - {details}")
        logger.warning("MONITORING", f"Security alert raised: {event_type}")
    
    def log_system_health(self, component, status, metrics):
        """Log system health information."""
        logger.info("MONITORING", f"System health check: {component} - {status}")
        logger.info("MONITORING", f"Health metrics: {metrics}")

# Usage example
app = EnterpriseApplication()

# Process business logic
result = app.process_business_logic("sample_data")

# Handle security events
app.handle_security_event("Unauthorized Access", "User attempted to access restricted resource")

# Log system health
app.log_system_health("Database", "Healthy", {"response_time": "0.05s", "connections": 10})
app.log_system_health("API", "Degraded", {"response_time": "2.5s", "error_rate": "5%"})
```

## Performance Optimization Examples

### High-Throughput Logging

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import threading
import time
import queue

# Configure high-performance logging
        config = LoggingConfig(
            layers={
        "HIGH_VOLUME": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                    path="logs/high_volume/events.csv",
                    format="csv",
                    max_size="100MB",
                    backup_count=2
                        )
                    ]
                ),
        "CRITICAL": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(
                            type="file",
                    path="logs/critical/errors.log",
                    format="text"
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
        
class HighThroughputLogger:
    def __init__(self, max_queue_size=10000):
        self.log_queue = queue.Queue(maxsize=max_queue_size)
        self.running = False
        self.worker_thread = None
    
    def start(self):
        """Start the high-throughput logging worker."""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.daemon = True
        self.worker_thread.start()
        logger.info("HIGH_VOLUME", "High-throughput logging started")
    
    def stop(self):
        """Stop the high-throughput logging worker."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("HIGH_VOLUME", "High-throughput logging stopped")
    
    def _worker_loop(self):
        """Worker loop for processing log messages."""
        batch = []
        batch_size = 100
        last_flush = time.time()
        
        while self.running:
            try:
                # Get message from queue with timeout
                message = self.log_queue.get(timeout=1)
                batch.append(message)
                
                # Flush batch if it's full or enough time has passed
                current_time = time.time()
                if len(batch) >= batch_size or (current_time - last_flush) >= 5:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = current_time
                    
            except queue.Empty:
                # Flush any remaining messages
                if batch:
                    self._flush_batch(batch)
                    batch = []
    
    def _flush_batch(self, batch):
        """Flush a batch of log messages."""
        for message in batch:
            logger.info("HIGH_VOLUME", message)
    
    def log_event(self, event_type, data):
        """Log an event to the high-throughput queue."""
        try:
            message = f"Event: {event_type}, Data: {data}"
            self.log_queue.put_nowait(message)
        except queue.Full:
            # If queue is full, log critical error
            logger.error("CRITICAL", "High-throughput log queue is full")
    
    def log_metrics(self, metric_name, value):
        """Log metrics to the high-throughput queue."""
        try:
            message = f"Metric: {metric_name}, Value: {value}"
            self.log_queue.put_nowait(message)
        except queue.Full:
            logger.error("CRITICAL", "High-throughput log queue is full")

# Usage example
high_throughput_logger = HighThroughputLogger()
high_throughput_logger.start()

# Simulate high-volume logging
for i in range(1000):
    high_throughput_logger.log_event("user_action", f"action_{i}")
    high_throughput_logger.log_metrics("response_time", i * 0.001)
    time.sleep(0.001)  # Simulate high frequency

# Stop logging
high_throughput_logger.stop()
```

This comprehensive examples guide demonstrates how to use Hydra-Logger in various real-world scenarios, from simple applications to complex enterprise systems, showing the flexibility and power of the multi-format logging system. 