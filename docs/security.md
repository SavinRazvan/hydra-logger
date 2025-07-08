# Security Guide

This comprehensive guide outlines security considerations, best practices, and implementation strategies for securing Hydra-Logger in enterprise environments, including the new multi-format logging capabilities.

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
            elif isinstance(value, list):
                sanitized[key] = [self.sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, str):
                # Check if key indicates sensitive data
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self.sanitize_text(value)
            else:
                sanitized[key] = value
        
        return sanitized

# Usage with Hydra-Logger
sanitizer = DataSanitizer()
logger = HydraLogger()

# Sanitize user data before logging
user_data = {
    "email": "user@example.com",
    "password": "secret123",
    "credit_card": "1234-5678-9012-3456",
    "profile": {
        "name": "John Doe",
        "ssn": "123-45-6789"
    }
}

safe_data = sanitizer.sanitize_dict(user_data)
logger.info("USER", f"User registration: {safe_data}")
```

### Structured Data Protection

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SecureUserData:
    """Secure user data structure."""
    user_id: str
    name: str
    email: str
    password: Optional[str] = None  # Never logged
    
    def __str__(self) -> str:
        """Safe string representation."""
        return f"User(id={self.user_id}, name={self.name}, email=[REDACTED])"
    
    def to_log_dict(self) -> Dict[str, Any]:
        """Convert to dictionary safe for logging."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": "[REDACTED]"
        }

# Usage
user = SecureUserData("123", "John Doe", "john@example.com", "secret123")
logger.info("AUTH", f"User login: {user.to_log_dict()}")
```

## Access Control

### Log File Access Control

```python
import os
import pwd
import grp
from pathlib import Path

class SecureLogManager:
    """Manage secure log file access."""
    
    def __init__(self, log_base: str = "/var/log/secure"):
        self.log_base = Path(log_base)
        self.app_user = "app"
        self.log_group = "adm"
    
    def setup_secure_permissions(self):
        """Setup secure permissions for log directory."""
        # Create directory structure
        self.log_base.mkdir(parents=True, exist_ok=True)
        
        # Set directory permissions
        os.chmod(self.log_base, 0o750)  # rwxr-x---
        
        # Set ownership
        uid = pwd.getpwnam(self.app_user).pw_uid
        gid = grp.getgrnam(self.log_group).gr_gid
        os.chown(self.log_base, uid, gid)
        
        # Create subdirectories
        subdirs = ["app", "auth", "audit", "system"]
        for subdir in subdirs:
            subdir_path = self.log_base / subdir
            subdir_path.mkdir(exist_ok=True)
            os.chmod(subdir_path, 0o750)
            os.chown(subdir_path, uid, gid)
    
    def create_secure_log_file(self, filename: str, permissions: int = 0o640):
        """Create a log file with secure permissions."""
        filepath = self.log_base / filename
        filepath.touch()
        os.chmod(filepath, permissions)
        
        uid = pwd.getpwnam(self.app_user).pw_uid
        gid = grp.getgrnam(self.log_group).gr_gid
        os.chown(filepath, uid, gid)
        
        return filepath

# Usage
log_manager = SecureLogManager()
log_manager.setup_secure_permissions()
secure_log_path = log_manager.create_secure_log_file("app.log")
```

### Role-Based Access Control

```python
from enum import Enum
from typing import Set

class LogAccessLevel(Enum):
    """Log access levels."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class LogAccessControl:
    """Role-based access control for logs."""
    
    def __init__(self):
        self.access_rules = {
            "admin": {LogAccessLevel.READ, LogAccessLevel.WRITE, LogAccessLevel.ADMIN},
            "security_analyst": {LogAccessLevel.READ, LogAccessLevel.WRITE},
            "developer": {LogAccessLevel.READ},
            "monitoring": {LogAccessLevel.READ}
        }
    
    def can_access(self, user_role: str, access_level: LogAccessLevel) -> bool:
        """Check if user can access logs at specified level."""
        if user_role not in self.access_rules:
            return False
        return access_level in self.access_rules[user_role]
    
    def get_accessible_logs(self, user_role: str) -> List[str]:
        """Get list of logs accessible to user role."""
        if user_role == "admin":
            return ["*"]  # All logs
        elif user_role == "security_analyst":
            return ["security.log", "auth.log", "audit.log"]
        elif user_role == "developer":
            return ["app.log", "debug.log"]
        elif user_role == "monitoring":
            return ["system.log", "performance.log"]
        else:
            return []

# Usage
access_control = LogAccessControl()
if access_control.can_access("security_analyst", LogAccessLevel.READ):
    # Allow access to security logs
    pass
```

## Format-Specific Security

### JSON Format Security

**Considerations:**
- JSON injection attacks
- Large payload attacks
- Sensitive data in structured format

```python
import json
from typing import Any

class SecureJSONFormatter:
    """Secure JSON formatter with data sanitization."""
    
    def __init__(self, max_size: int = 1024 * 1024):  # 1MB limit
        self.max_size = max_size
        self.sanitizer = DataSanitizer()
    
    def format(self, record: Any) -> str:
        """Format log record as secure JSON."""
        # Sanitize data
        safe_data = self.sanitizer.sanitize_dict(record.__dict__)
        
        # Convert to JSON
        json_data = json.dumps(safe_data, default=str)
        
        # Check size limit
        if len(json_data) > self.max_size:
            return json.dumps({
                "error": "Log entry too large",
                "original_size": len(json_data),
                "max_size": self.max_size
            })
        
        return json_data

# Configuration
config = LoggingConfig(
    layers={
        "SECURE_API": LogLayer(
            level="INFO",
            destinations=[
                LogDestination(
                    type="file",
                    path="/var/log/secure/api.json",
                    format="json"
                )
            ]
        )
    }
)
```

### CSV Format Security

**Considerations:**
- CSV injection attacks
- Large file generation
- Data leakage through formatting

```python
import csv
import io

class SecureCSVFormatter:
    """Secure CSV formatter."""
    
    def __init__(self):
        self.sanitizer = DataSanitizer()
    
    def escape_csv_value(self, value: str) -> str:
        """Escape CSV value to prevent injection."""
        if not isinstance(value, str):
            value = str(value)
        
        # Check for CSV injection patterns
        if value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')):
            value = "'" + value
        
        # Escape quotes
        value = value.replace('"', '""')
        
        return value
    
    def format(self, record: Any) -> str:
        """Format log record as secure CSV."""
        # Sanitize data
        safe_data = self.sanitizer.sanitize_dict(record.__dict__)
        
        # Create CSV row
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Write headers and data
        headers = list(safe_data.keys())
        values = [self.escape_csv_value(safe_data[h]) for h in headers]
        
        writer.writerow(headers)
        writer.writerow(values)
        
        return output.getvalue()
```

### Syslog Format Security

**Considerations:**
- Syslog injection attacks
- Priority level manipulation
- Facility spoofing

```python
import re

class SecureSyslogFormatter:
    """Secure syslog formatter."""
    
    def __init__(self, facility: int = 1, hostname: str = "localhost"):
        self.facility = facility
        self.hostname = hostname
        self.sanitizer = DataSanitizer()
    
    def sanitize_message(self, message: str) -> str:
        """Sanitize syslog message."""
        # Remove control characters
        message = re.sub(r'[\x00-\x1F\x7F]', '', message)
        
        # Limit message length (RFC 3164 limit)
        if len(message) > 1024:
            message = message[:1021] + "..."
        
        return message
    
    def format(self, level: str, message: str) -> str:
        """Format as secure syslog message."""
        # Map levels to syslog priorities
        priority_map = {
            "DEBUG": 7,
            "INFO": 6,
            "WARNING": 4,
            "ERROR": 3,
            "CRITICAL": 2
        }
        
        priority = priority_map.get(level, 6)
        facility_priority = (self.facility << 3) | priority
        
        # Sanitize message
        safe_message = self.sanitize_message(message)
        safe_message = self.sanitizer.sanitize_text(safe_message)
        
        # Format according to RFC 3164
        timestamp = time.strftime("%b %d %H:%M:%S")
        return f"<{facility_priority}>{timestamp} {self.hostname} hydra-logger: {safe_message}"
```

## Compliance and Auditing

### Audit Trail Configuration

```yaml
# audit_config.yaml
layers:
  AUDIT:
    level: INFO
    destinations:
      - type: file
        path: /var/log/secure/audit.log
        format: syslog
        max_size: 2MB
        backup_count: 10
      - type: file
        path: /var/log/secure/audit.json
        format: json
  
  COMPLIANCE:
    level: INFO
    destinations:
      - type: file
        path: /var/log/secure/compliance.csv
        format: csv
      - type: file
        path: /var/log/secure/compliance.json
        format: json
```

### Compliance Logging

```python
from datetime import datetime
from typing import Dict, Any

class ComplianceLogger:
    """Compliance-focused logging."""
    
    def __init__(self, logger: HydraLogger):
        self.logger = logger
    
    def log_data_access(self, user_id: str, resource: str, action: str, 
                       success: bool, details: Dict[str, Any] = None):
        """Log data access for compliance."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "data_access",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "success": success,
            "details": details or {}
        }
        
        self.logger.info("AUDIT", f"Data access: {audit_entry}")
        self.logger.info("COMPLIANCE", f"Compliance event: {audit_entry}")
    
    def log_configuration_change(self, user_id: str, change_type: str, 
                               old_value: Any, new_value: Any):
        """Log configuration changes."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "config_change",
            "user_id": user_id,
            "change_type": change_type,
            "old_value": str(old_value),
            "new_value": str(new_value)
        }
        
        self.logger.warning("AUDIT", f"Configuration change: {audit_entry}")
    
    def log_security_event(self, event_type: str, severity: str, 
                          details: Dict[str, Any]):
        """Log security events."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "security_event",
            "severity": severity,
            "details": details
        }
        
        self.logger.error("AUDIT", f"Security event: {audit_entry}")
        self.logger.error("COMPLIANCE", f"Security compliance: {audit_entry}")

# Usage
compliance_logger = ComplianceLogger(logger)
compliance_logger.log_data_access("user123", "user_profiles", "read", True)
compliance_logger.log_configuration_change("admin", "log_level", "INFO", "DEBUG")
compliance_logger.log_security_event("failed_login", "high", {"ip": "192.168.1.100"})
```

## Security Configuration

### High-Security Configuration

```yaml
# high_security_config.yaml
default_level: WARNING

layers:
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: /var/log/secure/security.log
        format: syslog
        max_size: 1MB
        backup_count: 5
  
  AUTH:
    level: INFO
    destinations:
      - type: file
        path: /var/log/secure/auth.log
        format: syslog
        max_size: 2MB
        backup_count: 10
  
  AUDIT:
    level: INFO
    destinations:
      - type: file
        path: /var/log/secure/audit.log
        format: syslog
        max_size: 2MB
        backup_count: 10
      - type: file
        path: /var/log/secure/audit.json
        format: json
  
  APP:
    level: WARNING
    destinations:
      - type: file
        path: /var/log/secure/app.log
        format: plain-text
        max_size: 10MB
        backup_count: 5
      - type: console
        level: ERROR
        format: json
```

### Development vs Production Security

**Development Configuration:**
```yaml
# dev_config.yaml
layers:
  DEBUG:
    level: DEBUG
    destinations:
      - type: console
        format: plain-text
      - type: file
        path: logs/debug.log
        format: plain-text
  
  APP:
    level: INFO
    destinations:
      - type: console
        format: json
      - type: file
        path: logs/app.log
        format: plain-text
```

**Production Configuration:**
```yaml
# prod_config.yaml
layers:
  DEBUG:
    level: DEBUG
    destinations:
      - type: file
        path: /var/log/secure/debug.log
        format: plain-text
        max_size: 5MB
        backup_count: 3
      # No console output in production
  
  APP:
    level: INFO
    destinations:
      - type: file
        path: /var/log/secure/app.log
        format: plain-text
        max_size: 10MB
        backup_count: 5
      - type: console
        level: ERROR
        format: json
```

## Best Practices

### General Security Practices

1. **Principle of Least Privilege**
   - Use minimal required permissions for log files
   - Separate log directories by sensitivity level
   - Use dedicated service accounts for logging

2. **Defense in Depth**
   - Implement multiple security controls
   - Use file system permissions, ACLs, and encryption
   - Monitor log access and changes

3. **Secure Configuration**
   - Use secure defaults
   - Validate all configuration inputs
   - Implement configuration change logging

4. **Monitoring and Alerting**
   - Monitor log file access patterns
   - Alert on suspicious activities
   - Implement log integrity monitoring

### Implementation Checklist

- [ ] Set appropriate file permissions (600 for sensitive, 640 for general)
- [ ] Use secure log directories with restricted access
- [ ] Implement data sanitization for all log entries
- [ ] Configure log rotation with secure retention policies
- [ ] Disable console logging for sensitive data in production
- [ ] Use structured logging for better data control
- [ ] Implement access controls for log files
- [ ] Monitor log file integrity
- [ ] Configure audit logging for compliance
- [ ] Test security configurations regularly

## Incident Response

### Log Analysis for Security Incidents

```python
class SecurityIncidentAnalyzer:
    """Analyze logs for security incidents."""
    
    def __init__(self, log_paths: List[str]):
        self.log_paths = log_paths
    
    def search_for_patterns(self, patterns: List[str]) -> List[Dict[str, Any]]:
        """Search logs for security patterns."""
        incidents = []
        
        for log_path in self.log_paths:
            with open(log_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern in patterns:
                        if pattern in line:
                            incidents.append({
                                "log_file": log_path,
                                "line_number": line_num,
                                "pattern": pattern,
                                "content": line.strip()
                            })
        
        return incidents
    
    def analyze_failed_logins(self, time_window: int = 3600) -> Dict[str, Any]:
        """Analyze failed login attempts."""
        # Implementation for analyzing failed login patterns
        pass
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalous log patterns."""
        # Implementation for anomaly detection
        pass

# Usage
analyzer = SecurityIncidentAnalyzer([
    "/var/log/secure/auth.log",
    "/var/log/secure/security.log"
])

# Search for suspicious patterns
suspicious_patterns = [
    "failed login",
    "unauthorized access",
    "sql injection",
    "xss attempt"
]

incidents = analyzer.search_for_patterns(suspicious_patterns)
```

### Incident Response Procedures

1. **Detection**: Monitor logs for security events
2. **Analysis**: Analyze log data for incident details
3. **Containment**: Implement immediate security measures
4. **Eradication**: Remove security threats
5. **Recovery**: Restore normal operations
6. **Lessons Learned**: Update security procedures

This comprehensive security guide ensures that Hydra-Logger can be deployed securely in enterprise environments while maintaining compliance with security standards and regulations. 