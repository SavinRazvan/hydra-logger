# Examples

This document provides comprehensive examples of how to use Hydra-Logger in various scenarios.

## Basic Examples

### Simple Logging

```python
from hydra_logger import HydraLogger

# Create logger with default configuration
logger = HydraLogger()

# Log messages to different levels
logger.info("DEFAULT", "Application started")
logger.debug("DEFAULT", "Debug information")
logger.warning("DEFAULT", "Warning message")
logger.error("DEFAULT", "Error occurred")
logger.critical("DEFAULT", "Critical error!")
```

### Custom Configuration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

# Create custom configuration
config = LoggingConfig(
    layers={
        "APP": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="logs/app.log",
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

# Create logger with custom configuration
logger = HydraLogger(config)

# Use the logger
logger.info("APP", "Application started")
logger.warning("APP", "Warning message")
```

## Web Application Examples

### Flask Application

```python
from flask import Flask, request, jsonify
from hydra_logger import HydraLogger

app = Flask(__name__)
logger = HydraLogger()

@app.route('/api/users', methods=['GET'])
def get_users():
    logger.info("API", f"GET /api/users - IP: {request.remote_addr}")
    
    try:
        # Simulate database query
        users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        logger.debug("DB", f"Retrieved {len(users)} users from database")
        
        return jsonify(users)
    except Exception as e:
        logger.error("API", f"Error retrieving users: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    logger.info("API", f"POST /api/users - IP: {request.remote_addr}")
    
    try:
        user_data = request.get_json()
        logger.info("AUTH", f"Creating user: {user_data.get('name', 'Unknown')}")
        
        # Simulate user creation
        new_user = {"id": 3, "name": user_data.get('name')}
        logger.info("DB", f"User created with ID: {new_user['id']}")
        
        return jsonify(new_user), 201
    except Exception as e:
        logger.error("API", f"Error creating user: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    logger.info("APP", "Flask application starting")
    app.run(debug=True)
```

### Django Application

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from hydra_logger import HydraLogger

logger = HydraLogger()

@csrf_exempt
@require_http_methods(["GET"])
def get_users(request):
    logger.info("API", f"GET /api/users - IP: {request.META.get('REMOTE_ADDR')}")
    
    try:
        # Simulate database query
        users = [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
        logger.debug("DB", f"Retrieved {len(users)} users from database")
        
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
        logger.info("AUTH", f"Creating user: {user_data.get('name', 'Unknown')}")
        
        # Simulate user creation
        new_user = {"id": 3, "name": user_data.get('name')}
        logger.info("DB", f"User created with ID: {new_user['id']}")
        
        return JsonResponse(new_user, status=201)
    except Exception as e:
        logger.error("API", f"Error creating user: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
```

## Database Application Examples

### SQLAlchemy Integration

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from hydra_logger import HydraLogger

Base = declarative_base()
logger = HydraLogger()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100))

# Database operations with logging
class UserService:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def create_user(self, name, email):
        logger.info("DB", f"Creating user: {name} ({email})")
        
        try:
            user = User(name=name, email=email)
            self.session.add(user)
            self.session.commit()
            
            logger.info("DB", f"User created successfully with ID: {user.id}")
            return user
        except Exception as e:
            logger.error("DB", f"Error creating user: {str(e)}")
            self.session.rollback()
            raise
    
    def get_user(self, user_id):
        logger.debug("DB", f"Retrieving user with ID: {user_id}")
        
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                logger.debug("DB", f"User found: {user.name}")
            else:
                logger.warning("DB", f"User not found with ID: {user_id}")
            return user
        except Exception as e:
            logger.error("DB", f"Error retrieving user: {str(e)}")
            raise

# Usage
user_service = UserService('sqlite:///users.db')
user = user_service.create_user("John Doe", "john@example.com")
retrieved_user = user_service.get_user(user.id)
```

## API Client Examples

### REST API Client

```python
import requests
from hydra_logger import HydraLogger

logger = HydraLogger()

class APIClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        
        logger.info("API_CLIENT", f"Initialized API client for {base_url}")
    
    def get(self, endpoint, params=None):
        url = f"{self.base_url}{endpoint}"
        logger.debug("API_CLIENT", f"GET {url}")
        
        try:
            response = self.session.get(url, params=params)
            logger.info("API_CLIENT", f"GET {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error("API_CLIENT", f"API error: {response.status_code} - {response.text}")
            
            return response
        except requests.exceptions.RequestException as e:
            logger.error("API_CLIENT", f"Request failed: {str(e)}")
            raise
    
    def post(self, endpoint, data=None, json=None):
        url = f"{self.base_url}{endpoint}"
        logger.debug("API_CLIENT", f"POST {url}")
        
        try:
            response = self.session.post(url, data=data, json=json)
            logger.info("API_CLIENT", f"POST {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error("API_CLIENT", f"API error: {response.status_code} - {response.text}")
            
            return response
        except requests.exceptions.RequestException as e:
            logger.error("API_CLIENT", f"Request failed: {str(e)}")
            raise

# Usage
api_client = APIClient("https://api.example.com", api_key="your-api-key")

# Get users
response = api_client.get("/users")
if response.status_code == 200:
    users = response.json()
    logger.info("APP", f"Retrieved {len(users)} users")

# Create user
user_data = {"name": "John Doe", "email": "john@example.com"}
response = api_client.post("/users", json=user_data)
if response.status_code == 201:
    new_user = response.json()
    logger.info("APP", f"Created user with ID: {new_user['id']}")
```

## Background Task Examples

### Celery Task

```python
from celery import Celery
from hydra_logger import HydraLogger

app = Celery('tasks')
logger = HydraLogger()

@app.task
def process_user_data(user_id, data):
    logger.info("CELERY", f"Starting processing for user {user_id}")
    
    try:
        # Simulate processing
        logger.debug("CELERY", f"Processing data: {data}")
        
        # Simulate some work
        import time
        time.sleep(2)
        
        result = {"user_id": user_id, "processed": True, "data": data}
        logger.info("CELERY", f"Successfully processed user {user_id}")
        
        return result
    except Exception as e:
        logger.error("CELERY", f"Error processing user {user_id}: {str(e)}")
        raise

@app.task
def send_email_notification(user_id, email_type):
    logger.info("EMAIL", f"Sending {email_type} email to user {user_id}")
    
    try:
        # Simulate email sending
        logger.debug("EMAIL", f"Preparing email content for {email_type}")
        
        # Simulate some work
        import time
        time.sleep(1)
        
        logger.info("EMAIL", f"Successfully sent {email_type} email to user {user_id}")
        return {"user_id": user_id, "email_sent": True, "type": email_type}
    except Exception as e:
        logger.error("EMAIL", f"Error sending email to user {user_id}: {str(e)}")
        raise

# Usage
def trigger_user_processing(user_id, data):
    logger.info("APP", f"Triggering processing for user {user_id}")
    
    # Start processing task
    process_task = process_user_data.delay(user_id, data)
    
    # Start email notification task
    email_task = send_email_notification.delay(user_id, "welcome")
    
    logger.info("APP", f"Tasks queued for user {user_id}")
    return process_task.id, email_task.id
```

## Configuration File Examples

### YAML Configuration

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
  
  API:
    level: INFO
    destinations:
      - type: file
        path: logs/api/requests.log
        max_size: 10MB
        backup_count: 5
      - type: file
        path: logs/api/errors.log
        max_size: 2MB
        backup_count: 3
      - type: console
        level: ERROR
  
  DB:
    level: DEBUG
    destinations:
      - type: file
        path: logs/database/queries.log
        max_size: 5MB
        backup_count: 3
  
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: logs/security/auth.log
        max_size: 1MB
        backup_count: 10
      - type: console
        level: CRITICAL
  
  EMAIL:
    level: INFO
    destinations:
      - type: file
        path: logs/email/notifications.log
        max_size: 2MB
        backup_count: 5
```

### TOML Configuration

```toml
# hydra_logging.toml
[layers.APP]
level = "INFO"

[[layers.APP.destinations]]
type = "file"
path = "logs/app.log"
max_size = "10MB"
backup_count = 5

[[layers.APP.destinations]]
type = "console"
level = "WARNING"

[layers.API]
level = "INFO"

[[layers.API.destinations]]
type = "file"
path = "logs/api/requests.log"
max_size = "10MB"
backup_count = 5

[[layers.API.destinations]]
type = "file"
path = "logs/api/errors.log"
max_size = "2MB"
backup_count = 3

[[layers.API.destinations]]
type = "console"
level = "ERROR"

[layers.DB]
level = "DEBUG"

[[layers.DB.destinations]]
type = "file"
path = "logs/database/queries.log"
max_size = "5MB"
backup_count = 3

[layers.SECURITY]
level = "ERROR"

[[layers.SECURITY.destinations]]
type = "file"
path = "logs/security/auth.log"
max_size = "1MB"
backup_count = 10

[[layers.SECURITY.destinations]]
type = "console"
level = "CRITICAL"
```

## Advanced Examples

### Custom Logger with Context

```python
from hydra_logger import HydraLogger
from contextvars import ContextVar
from typing import Optional

# Context variables for request tracking
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

class ContextualHydraLogger(HydraLogger):
    """Hydra-Logger with request context support."""
    
    def _format_message(self, layer: str, message: str) -> str:
        """Format message with context information."""
        context_parts = []
        
        if request_id.get():
            context_parts.append(f"req_id={request_id.get()}")
        
        if user_id.get():
            context_parts.append(f"user_id={user_id.get()}")
        
        if context_parts:
            context_str = " | ".join(context_parts)
            return f"[{context_str}] {message}"
        
        return message
    
    def info(self, layer: str, message: str, *args, **kwargs):
        formatted_message = self._format_message(layer, message)
        super().info(layer, formatted_message, *args, **kwargs)
    
    def error(self, layer: str, message: str, *args, **kwargs):
        formatted_message = self._format_message(layer, message)
        super().error(layer, formatted_message, *args, **kwargs)

# Usage
logger = ContextualHydraLogger()

def handle_request(req_id: str, user_id_str: str):
    """Handle a request with context."""
    # Set context
    request_id.set(req_id)
    user_id.set(user_id_str)
    
    logger.info("REQUEST", "Request started")
    
    try:
        # Process request
        logger.info("APP", "Processing request")
        
        # Simulate some work
        result = {"status": "success", "data": "processed"}
        
        logger.info("REQUEST", "Request completed successfully")
        return result
    except Exception as e:
        logger.error("REQUEST", f"Request failed: {str(e)}")
        raise
    finally:
        # Clear context
        request_id.set(None)
        user_id.set(None)

# Example usage
handle_request("req-123", "user-456")
```

### Structured Logging

```python
from hydra_logger import HydraLogger
import json
from datetime import datetime
from typing import Any, Dict

class StructuredHydraLogger(HydraLogger):
    """Hydra-Logger with structured logging support."""
    
    def _log_structured(self, level: str, layer: str, event: str, **kwargs):
        """Log structured data as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "layer": layer,
            "event": event,
            **kwargs
        }
        
        message = json.dumps(log_data)
        
        if level == "INFO":
            super().info(layer, message)
        elif level == "ERROR":
            super().error(layer, message)
        elif level == "DEBUG":
            super().debug(layer, message)
        elif level == "WARNING":
            super().warning(layer, message)
        elif level == "CRITICAL":
            super().critical(layer, message)
    
    def log_event(self, layer: str, event: str, **kwargs):
        """Log an event with structured data."""
        self._log_structured("INFO", layer, event, **kwargs)
    
    def log_error(self, layer: str, event: str, error: Exception, **kwargs):
        """Log an error with structured data."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            **kwargs
        }
        self._log_structured("ERROR", layer, event, **error_data)

# Usage
logger = StructuredHydraLogger()

# Log structured events
logger.log_event("USER", "user_login", user_id=123, ip_address="192.168.1.1")
logger.log_event("DB", "query_executed", query="SELECT * FROM users", duration_ms=45)

# Log structured errors
try:
    # Simulate an error
    raise ValueError("Invalid user data")
except Exception as e:
    logger.log_error("AUTH", "login_failed", error=e, user_id=123, ip_address="192.168.1.1")
```

## Testing Examples

### Unit Testing with Hydra-Logger

```python
import pytest
import tempfile
import os
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

class TestHydraLogger:
    @pytest.fixture
    def temp_log_dir(self):
        """Create a temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create a logger with temporary log files."""
        config = LoggingConfig(
            layers={
                "TEST": LogLayer(
                    level="DEBUG",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_log_dir, "test.log")
                        )
                    ]
                )
            }
        )
        return HydraLogger(config)
    
    def test_info_logging(self, logger, temp_log_dir):
        """Test info level logging."""
        logger.info("TEST", "Test info message")
        
        log_file = os.path.join(temp_log_dir, "test.log")
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test info message" in content
            assert "INFO" in content
    
    def test_error_logging(self, logger, temp_log_dir):
        """Test error level logging."""
        logger.error("TEST", "Test error message")
        
        log_file = os.path.join(temp_log_dir, "test.log")
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test error message" in content
            assert "ERROR" in content
    
    def test_debug_logging(self, logger, temp_log_dir):
        """Test debug level logging."""
        logger.debug("TEST", "Test debug message")
        
        log_file = os.path.join(temp_log_dir, "test.log")
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test debug message" in content
            assert "DEBUG" in content

# Integration test
def test_multi_layer_logging():
    """Test logging to multiple layers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = LoggingConfig(
            layers={
                "APP": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "app.log")
                        )
                    ]
                ),
                "ERROR": LogLayer(
                    level="ERROR",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=os.path.join(temp_dir, "error.log")
                        )
                    ]
                )
            }
        )
        
        logger = HydraLogger(config)
        
        # Log to different layers
        logger.info("APP", "Application message")
        logger.error("ERROR", "Error message")
        
        # Check app log
        with open(os.path.join(temp_dir, "app.log"), 'r') as f:
            app_content = f.read()
            assert "Application message" in app_content
            assert "Error message" not in app_content
        
        # Check error log
        with open(os.path.join(temp_dir, "error.log"), 'r') as f:
            error_content = f.read()
            assert "Error message" in error_content
            assert "Application message" not in error_content
```

These examples demonstrate various use cases and patterns for using Hydra-Logger in different types of applications. Each example can be adapted and extended based on your specific requirements. 