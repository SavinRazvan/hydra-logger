# Security Guide

This comprehensive guide outlines security considerations, best practices, and implementation strategies for securing Hydra-Logger in enterprise environments, including the multi-format logging capabilities.

## Table of Contents

- [Security Overview](#security-overview)
- [Log File Security](#log-file-security)
- [Data Protection](#data-protection)
- [Access Control](#access-control)
- [Format-Specific Security](#format-specific-security)
- [Compliance and Auditing](#compliance-and-auditing)
- [Security Configuration](#security-configuration)
- [Best Practices](#best-practices)
- [Incident Response](#incident-response)

## Security Overview

### Security Principles

Hydra-Logger follows these core security principles:

1. **Defense in Depth**: Multiple layers of security controls
2. **Principle of Least Privilege**: Minimal access required for functionality
3. **Secure by Default**: Secure configurations out of the box
4. **Fail Secure**: System remains secure even when components fail
5. **Audit Trail**: Comprehensive logging of security events

### Threat Model

**Primary Threats:**
- Unauthorized access to log files
- Sensitive data exposure in logs
- Log file tampering or deletion
- Information disclosure through log analysis
- Denial of service through log flooding

**Secondary Threats:**
- Path traversal attacks
- Log injection attacks
- Format-specific vulnerabilities
- Configuration file compromise

## Log File Security

### File Permissions and Ownership

**Risk**: Unauthorized access to log files containing sensitive information.

**Best Practices**:
- Set restrictive file permissions (600 for sensitive logs, 640 for general logs)
- Use dedicated log directories with restricted access
- Implement proper file ownership (root:adm for system logs)
- Use ACLs for fine-grained access control

```python
import os
import stat
from pathlib import Path
from hydra_logger import HydraLogger

# Create secure log directory
log_dir = Path("/var/log/secure/app")
log_dir.mkdir(parents=True, exist_ok=True)
os.chmod(log_dir, 0o750)  # rwxr-x---

# Configure logger
config = LoggingConfig(
    layers={
        "SECURITY": LogLayer(
            level="ERROR",
            destinations=[
                LogDestination(
                    type="file",
                    path="/var/log/secure/app/security.log",
                    format="syslog"
                )
            ]
        )
    }
)

logger = HydraLogger(config)

# Set secure permissions after file creation
security_log = Path("/var/log/secure/app/security.log")
if security_log.exists():
    os.chmod(security_log, 0o600)  # rw-------
    os.chown(security_log, 0, 0)  # root:root
```

### Directory Security

```python
# Secure log directory setup
def setup_secure_logging():
    """Setup secure logging environment."""
    log_base = Path("/var/log/secure")
    
    # Create directory structure
    directories = [
        log_base / "app",
        log_base / "auth",
        log_base / "audit",
        log_base / "system"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o750)
        os.chown(directory, 0, 0)  # root:root
    
    # Set up log rotation with secure permissions
    return log_base
```

### Log File Encryption

For highly sensitive environments, consider encrypting log files:

```python
from cryptography.fernet import Fernet
import base64

class EncryptedLogHandler:
    """Handler for encrypted log files."""
    
    def __init__(self, key_file: str):
        with open(key_file, 'rb') as f:
            key = f.read()
        self.cipher = Fernet(key)
    
    def write_encrypted(self, filepath: str, data: str):
        """Write encrypted data to file."""
        encrypted_data = self.cipher.encrypt(data.encode())
        with open(filepath, 'wb') as f:
            f.write(encrypted_data)
    
    def read_encrypted(self, filepath: str) -> str:
        """Read and decrypt data from file."""
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return decrypted_data.decode()

# Usage with Hydra-Logger
encrypted_handler = EncryptedLogHandler("/etc/keys/log.key")
```

## Data Protection

### Sensitive Data Identification

**Risk**: Logging sensitive information like passwords, tokens, or personal data.

**Best Practices**:
- Never log passwords, API keys, or tokens
- Redact or mask sensitive data before logging
- Use structured logging to separate sensitive fields
- Implement data classification policies

```python
import re
from typing import Any, Dict, List
from hydra_logger import HydraLogger

class DataSanitizer:
    """Sanitize sensitive data before logging."""
    
    SENSITIVE_PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'api_key': r'[a-zA-Z0-9]{32,}',
        'jwt_token': r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'
    }
    
    SENSITIVE_FIELDS = [
        'password', 'token', 'api_key', 'secret', 'key',
        'authorization', 'cookie', 'session', 'credential'
    ]
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text content."""
        sanitized = text
        
        # Apply pattern-based masking
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            sanitized = re.sub(pattern, f'[{pattern_name.upper()}_MASKED]', sanitized)
        
        return sanitized
    
    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary data."""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value)
            elif isinstance(value, str):
                # Check if field name indicates sensitive data
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self.sanitize_text(value)
            else:
                sanitized[key] = value
        
        return sanitized

# Usage with Hydra-Logger
sanitizer = DataSanitizer()
logger = HydraLogger(enable_security=True, enable_sanitization=True)

# Sensitive data will be automatically masked
logger.info("User login attempt", "AUTH", 
           extra={"email": "user@example.com", "password": "secret123"})
# Output: email=***@***.com password=***
```

### PII Detection and Redaction

```python
from hydra_logger import HydraLogger

class PIIDetector:
    """Detect and redact PII in log messages."""
    
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
        'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    }
    
    def redact_pii(self, text: str) -> str:
        """Redact PII from text."""
        redacted = text
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            redacted = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', redacted)
        
        return redacted

# Usage
pii_detector = PIIDetector()
logger = HydraLogger(enable_security=True)

# PII will be automatically redacted
logger.info("User profile updated", "USER", 
           extra={"email": "user@example.com", "phone": "555-123-4567"})
# Output: email=[EMAIL_REDACTED] phone=[PHONE_REDACTED]
```

## Access Control

### Role-Based Access Control

```python
from enum import Enum
from typing import Set

class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class Role(Enum):
    DEVELOPER = "developer"
    OPERATOR = "operator"
    ADMIN = "admin"
    AUDITOR = "auditor"

class AccessControl:
    """Role-based access control for logging."""
    
    def __init__(self):
        self.role_permissions = {
            Role.DEVELOPER: {LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING},
            Role.OPERATOR: {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR},
            Role.ADMIN: {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL},
            Role.AUDITOR: {LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL}
        }
    
    def can_access(self, role: Role, level: LogLevel) -> bool:
        """Check if role can access log level."""
        return level in self.role_permissions.get(role, set())
    
    def get_accessible_levels(self, role: Role) -> Set[LogLevel]:
        """Get accessible log levels for role."""
        return self.role_permissions.get(role, set())

# Usage
access_control = AccessControl()
logger = HydraLogger()

# Check permissions before logging
if access_control.can_access(Role.OPERATOR, LogLevel.ERROR):
    logger.error("System error occurred", "SYSTEM")
```

### Network Security

```python
import socket
import ssl
from hydra_logger import HydraLogger

class SecureNetworkLogger:
    """Logger with network security features."""
    
    def __init__(self, config, host: str, port: int, use_ssl: bool = True):
        self.logger = HydraLogger(config)
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.socket = None
    
    def connect(self):
        """Establish secure connection."""
        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                self.socket = context.wrap_socket(
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                    server_hostname=self.host
                )
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            self.socket.connect((self.host, self.port))
            self.logger.info("Secure connection established", "NETWORK")
            
        except Exception as e:
            self.logger.error(f"Connection failed: {e}", "NETWORK")
    
    def send_log(self, message: str):
        """Send log message securely."""
        if self.socket:
            try:
                self.socket.send(message.encode())
            except Exception as e:
                self.logger.error(f"Failed to send log: {e}", "NETWORK")
```

## Format-Specific Security

### JSON Format Security

```python
import json
from hydra_logger import HydraLogger

class SecureJSONLogger:
    """Logger with JSON-specific security features."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self.sensitive_keys = {'password', 'token', 'secret', 'key'}
    
    def sanitize_json(self, data: dict) -> dict:
        """Sanitize JSON data before logging."""
        sanitized = {}
        
        for key, value in data.items():
            if key.lower() in self.sensitive_keys:
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_json(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_secure_json(self, layer: str, level: str, message: str, data: dict = None):
        """Log JSON data with security sanitization."""
        if data:
            sanitized_data = self.sanitize_json(data)
            message = json.dumps(sanitized_data)
        
        self.logger.log(level, message, layer)

# Usage
secure_json_logger = SecureJSONLogger(config)
secure_json_logger.log_secure_json(
    "API", "INFO", "User data", 
    {"user_id": 123, "password": "secret123", "email": "user@example.com"}
)
# Output: {"user_id": 123, "password": "[REDACTED]", "email": "user@example.com"}
```

### CSV Format Security

```python
import csv
from hydra_logger import HydraLogger

class SecureCSVLogger:
    """Logger with CSV-specific security features."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self.sensitive_columns = {'password', 'token', 'secret'}
    
    def sanitize_csv_row(self, row: dict) -> dict:
        """Sanitize CSV row data."""
        sanitized = {}
        
        for column, value in row.items():
            if column.lower() in self.sensitive_columns:
                sanitized[column] = '[REDACTED]'
            else:
                sanitized[column] = value
        
        return sanitized
    
    def log_secure_csv(self, layer: str, level: str, data: dict):
        """Log CSV data with security sanitization."""
        sanitized_data = self.sanitize_csv_row(data)
        message = ','.join(f'{k}={v}' for k, v in sanitized_data.items())
        
        self.logger.log(level, message, layer)

# Usage
secure_csv_logger = SecureCSVLogger(config)
secure_csv_logger.log_secure_csv(
    "USER", "INFO", 
    {"user_id": "123", "password": "secret123", "email": "user@example.com"}
)
# Output: user_id=123,password=[REDACTED],email=user@example.com
```

## Compliance and Auditing

### GDPR Compliance

```python
from datetime import datetime, timedelta
from hydra_logger import HydraLogger

class GDPRCompliantLogger:
    """Logger with GDPR compliance features."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self.retention_period = timedelta(days=30)  # GDPR default
        self.user_consent = {}
    
    def log_with_consent(self, user_id: str, message: str, layer: str = "USER"):
        """Log message only with user consent."""
        if self.has_consent(user_id):
            self.logger.info(message, layer, extra={"user_id": user_id})
        else:
            self.logger.warning("Logging attempted without consent", "GDPR", 
                              extra={"user_id": user_id})
    
    def has_consent(self, user_id: str) -> bool:
        """Check if user has given consent."""
        return self.user_consent.get(user_id, False)
    
    def set_consent(self, user_id: str, has_consent: bool):
        """Set user consent status."""
        self.user_consent[user_id] = has_consent
    
    def cleanup_expired_logs(self):
        """Remove logs older than retention period."""
        cutoff_date = datetime.now() - self.retention_period
        # Implementation would depend on log storage mechanism
        self.logger.info("Cleaned up expired logs", "GDPR", 
                        extra={"cutoff_date": cutoff_date.isoformat()})

# Usage
gdpr_logger = GDPRCompliantLogger(config)
gdpr_logger.set_consent("user123", True)
gdpr_logger.log_with_consent("user123", "User action performed")
```

### SOX Compliance

```python
from hydra_logger import HydraLogger

class SOXCompliantLogger:
    """Logger with SOX compliance features."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self.audit_trail = []
    
    def log_financial_transaction(self, transaction_id: str, amount: float, 
                                account: str, user_id: str):
        """Log financial transaction with SOX compliance."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "transaction_id": transaction_id,
            "amount": amount,
            "account": account,
            "user_id": user_id,
            "action": "financial_transaction"
        }
        
        self.audit_trail.append(audit_entry)
        self.logger.info("Financial transaction logged", "SOX", extra=audit_entry)
    
    def get_audit_trail(self, start_date: datetime = None, end_date: datetime = None):
        """Get audit trail for specified period."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        filtered_trail = [
            entry for entry in self.audit_trail
            if start_date <= datetime.fromisoformat(entry["timestamp"]) <= end_date
        ]
        
        return filtered_trail

# Usage
sox_logger = SOXCompliantLogger(config)
sox_logger.log_financial_transaction("TXN001", 1000.00, "ACCT123", "user456")
```

## Security Configuration

### Secure Default Configuration

```python
from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination

def create_secure_config():
    """Create secure default configuration."""
    return LoggingConfig(
        layers={
            "SECURITY": LogLayer(
                level="WARNING",
                destinations=[
                    LogDestination(
                        type="file",
                        path="/var/log/secure/security.log",
                        format="syslog",
                        max_size="10MB",
                        backup_count=10
                    )
                ]
            ),
            "AUDIT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="/var/log/secure/audit.log",
                        format="json",
                        max_size="50MB",
                        backup_count=5
                    )
                ]
            ),
            "APPLICATION": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="/var/log/app/app.log",
                        format="plain-text",
                        max_size="100MB",
                        backup_count=3
                    ),
                    LogDestination(
                        type="console",
                        format="plain-text",
                        color_mode="auto"
                    )
                ]
            )
        }
    )

# Usage
secure_config = create_secure_config()
secure_logger = HydraLogger(secure_config)
```

### Environment-Specific Security

```python
import os
from hydra_logger import HydraLogger

def get_secure_config_for_environment():
    """Get secure configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    base_config = {
        "layers": {
            "SECURITY": {
                "level": "WARNING",
                "destinations": [
                    {
                        "type": "file",
                        "path": "/var/log/secure/security.log",
                        "format": "syslog"
                    }
                ]
            }
        }
    }
    
    if env == "production":
        # Add additional security layers for production
        base_config["layers"]["AUDIT"] = {
            "level": "INFO",
            "destinations": [
                {
                    "type": "file",
                    "path": "/var/log/secure/audit.log",
                    "format": "json"
                }
            ]
        }
    
    return base_config

# Usage
config = get_secure_config_for_environment()
secure_logger = HydraLogger(config)
```

## Best Practices

### Security Logging Best Practices

1. **Never log sensitive data directly**
   ```python
   # Bad
   logger.info("User login", "AUTH", extra={"password": "secret123"})
   
   # Good
   logger.info("User login", "AUTH", extra={"user_id": "123", "status": "success"})
   ```

2. **Use appropriate log levels**
   ```python
   # Security events should be WARNING or higher
   logger.warning("Failed login attempt", "SECURITY", extra={"ip": "192.168.1.1"})
   logger.error("Unauthorized access attempt", "SECURITY", extra={"user_id": "unknown"})
   ```

3. **Implement log rotation**
   ```python
   # Configure log rotation to prevent disk space issues
   LogDestination(
       type="file",
       path="/var/log/secure/security.log",
       max_size="10MB",
       backup_count=5
   )
   ```

4. **Use secure file permissions**
   ```python
   # Set restrictive permissions on log files
   os.chmod("/var/log/secure/security.log", 0o600)
   ```

### Incident Response

```python
from hydra_logger import HydraLogger
import time

class SecurityIncidentLogger:
    """Logger for security incident response."""
    
    def __init__(self, config):
        self.logger = HydraLogger(config)
        self.incident_counter = 0
    
    def log_security_incident(self, incident_type: str, severity: str, 
                             details: dict, user_id: str = None):
        """Log security incident with appropriate level."""
        self.incident_counter += 1
        
        incident_data = {
            "incident_id": f"INC-{self.incident_counter:06d}",
            "incident_type": incident_type,
            "severity": severity,
            "timestamp": time.time(),
            "details": details
        }
        
        if user_id:
            incident_data["user_id"] = user_id
        
        # Map severity to log level
        severity_map = {
            "low": "WARNING",
            "medium": "ERROR", 
            "high": "CRITICAL"
        }
        
        log_level = severity_map.get(severity, "ERROR")
        self.logger.log(log_level, f"Security incident: {incident_type}", "SECURITY", 
                       extra=incident_data)
    
    def log_incident_response(self, incident_id: str, action: str, 
                            responder: str, details: dict):
        """Log incident response actions."""
        response_data = {
            "incident_id": incident_id,
            "action": action,
            "responder": responder,
            "timestamp": time.time(),
            "details": details
        }
        
        self.logger.info("Incident response action", "SECURITY", extra=response_data)

# Usage
incident_logger = SecurityIncidentLogger(config)

# Log security incident
incident_logger.log_security_incident(
    "failed_login",
    "medium",
    {"ip": "192.168.1.1", "attempts": 5},
    "user123"
)

# Log response action
incident_logger.log_incident_response(
    "INC-000001",
    "account_locked",
    "security_team",
    {"duration": "24h", "reason": "multiple_failed_attempts"}
)
```

This security guide provides comprehensive coverage of security considerations for Hydra-Logger, ensuring that your logging implementation meets enterprise security requirements while maintaining compliance with relevant regulations. 