# Security Guide

This document outlines security considerations and best practices when using Hydra-Logger.

## Security Considerations

### 1. Log File Permissions

**Risk**: Unauthorized access to log files containing sensitive information.

**Best Practices**:
- Set appropriate file permissions (e.g., 600 for sensitive logs)
- Use dedicated log directories with restricted access
- Consider using encrypted log files for highly sensitive data

```python
import os
from hydra_logger import HydraLogger

# Set secure permissions after creating log files
logger = HydraLogger()
os.chmod("logs/security.log", 0o600)
```

### 2. Sensitive Data in Logs

**Risk**: Logging sensitive information like passwords, tokens, or personal data.

**Best Practices**:
- Never log passwords, API keys, or tokens
- Redact or mask sensitive data before logging
- Use structured logging to separate sensitive fields

```python
import re
from hydra_logger import HydraLogger

def sanitize_data(data):
    """Remove sensitive information from data before logging."""
    # Mask email addresses
    data = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', data)
    # Mask credit card numbers
    data = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]', data)
    return data

logger = HydraLogger()
user_data = {"email": "user@example.com", "card": "1234-5678-9012-3456"}
logger.info("USER", f"User data: {sanitize_data(str(user_data))}")
```

### 3. Log File Locations

**Risk**: Storing logs in insecure locations or with predictable paths.

**Best Practices**:
- Use secure, dedicated log directories
- Avoid storing logs in web-accessible directories
- Use absolute paths to prevent path traversal attacks

```yaml
layers:
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: /var/log/secure/app/security.log  # Secure location
        max_size: 1MB
        backup_count: 10
```

### 4. Log Rotation and Retention

**Risk**: Accumulation of sensitive data in old log files.

**Best Practices**:
- Implement appropriate log rotation
- Set reasonable retention periods
- Securely delete old log files

```yaml
layers:
  SENSITIVE:
    level: INFO
    destinations:
      - type: file
        path: logs/sensitive/auth.log
        max_size: 1MB
        backup_count: 3  # Keep only 3 backup files
```

### 5. Console Logging in Production

**Risk**: Sensitive information appearing in console output.

**Best Practices**:
- Disable console logging in production for sensitive layers
- Use appropriate log levels for console output
- Consider using structured logging for better control

```yaml
layers:
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: logs/security.log
      # No console destination for sensitive data
```

## Security Configuration Examples

### High-Security Configuration

```yaml
layers:
  SECURITY:
    level: ERROR
    destinations:
      - type: file
        path: /var/log/secure/auth.log
        max_size: 1MB
        backup_count: 5
  
  AUDIT:
    level: INFO
    destinations:
      - type: file
        path: /var/log/secure/audit.log
        max_size: 2MB
        backup_count: 10
  
  APP:
    level: INFO
    destinations:
      - type: file
        path: logs/app.log
        max_size: 10MB
        backup_count: 5
      - type: console
        level: WARNING  # Only warnings and errors to console
```

### Development vs Production Security

**Development Configuration:**
```yaml
layers:
  DEBUG:
    level: DEBUG
    destinations:
      - type: console  # Debug to console in development
      - type: file
        path: logs/debug.log
```

**Production Configuration:**
```yaml
layers:
  DEBUG:
    level: DEBUG
    destinations:
      - type: file
        path: logs/debug.log
        max_size: 5MB
        backup_count: 3
      # No console destination in production
```

## Data Sanitization

### Built-in Sanitization

Hydra-Logger provides utilities for data sanitization:

```python
from hydra_logger.utils import sanitize_log_data

# Sanitize sensitive data before logging
user_input = "Password: secret123, Email: user@example.com"
safe_data = sanitize_log_data(user_input)
logger.info("USER", f"User input: {safe_data}")
```

### Custom Sanitization

```python
import re
from typing import Any, Dict

def sanitize_user_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Custom sanitization for user data."""
    sanitized = data.copy()
    
    # Mask sensitive fields
    sensitive_fields = ['password', 'token', 'api_key', 'secret']
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '[REDACTED]'
    
    # Mask email addresses
    if 'email' in sanitized:
        email = sanitized['email']
        if '@' in email:
            parts = email.split('@')
            sanitized['email'] = f"{parts[0][:2]}***@{parts[1]}"
    
    return sanitized

# Use custom sanitization
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secret123",
    "api_key": "sk-1234567890abcdef"
}

safe_data = sanitize_user_data(user_data)
logger.info("USER", f"User created: {safe_data}")
```

## Log Encryption

For highly sensitive environments, consider encrypting log files:

```python
import cryptography.fernet
from hydra_logger import HydraLogger

class EncryptedFileHandler:
    """Custom handler for encrypted log files."""
    
    def __init__(self, key: bytes, filepath: str):
        self.cipher = cryptography.fernet.Fernet(key)
        self.filepath = filepath
    
    def write(self, data: str):
        encrypted_data = self.cipher.encrypt(data.encode())
        with open(self.filepath, 'ab') as f:
            f.write(encrypted_data + b'\n')

# Usage (simplified example)
key = cryptography.fernet.Fernet.generate_key()
handler = EncryptedFileHandler(key, "logs/encrypted.log")
```

## Monitoring and Alerting

### Security Event Monitoring

```python
from hydra_logger import HydraLogger

# Create a security-focused logger
security_logger = HydraLogger.from_config("security_config.yaml")

# Log security events
def log_security_event(event_type: str, details: str, severity: str = "INFO"):
    """Log security events with appropriate severity."""
    if severity == "CRITICAL":
        security_logger.critical("SECURITY", f"{event_type}: {details}")
    elif severity == "ERROR":
        security_logger.error("SECURITY", f"{event_type}: {details}")
    else:
        security_logger.info("SECURITY", f"{event_type}: {details}")

# Example usage
log_security_event("LOGIN_ATTEMPT", "Failed login for user admin", "ERROR")
log_security_event("PERMISSION_GRANTED", "Admin access granted to user", "INFO")
```

### Rate Limiting

```python
import time
from collections import defaultdict
from hydra_logger import HydraLogger

class RateLimitedLogger:
    """Logger with rate limiting for security events."""
    
    def __init__(self, max_events_per_minute: int = 10):
        self.logger = HydraLogger()
        self.max_events = max_events_per_minute
        self.event_counts = defaultdict(list)
    
    def log_security_event(self, event_type: str, message: str):
        """Log security event with rate limiting."""
        current_time = time.time()
        minute = int(current_time // 60)
        
        # Clean old events
        self.event_counts[event_type] = [
            t for t in self.event_counts[event_type] 
            if t > current_time - 60
        ]
        
        # Check rate limit
        if len(self.event_counts[event_type]) >= self.max_events:
            self.logger.warning("SECURITY", f"Rate limit exceeded for {event_type}")
            return
        
        # Log the event
        self.event_counts[event_type].append(current_time)
        self.logger.info("SECURITY", f"{event_type}: {message}")

# Usage
security_logger = RateLimitedLogger(max_events_per_minute=5)
```

## Compliance Considerations

### GDPR Compliance

- Implement data retention policies
- Provide data export capabilities
- Ensure right to be forgotten

```yaml
layers:
  GDPR:
    level: INFO
    destinations:
      - type: file
        path: logs/gdpr/requests.log
        max_size: 1MB
        backup_count: 12  # Keep for 1 year
```

### SOX Compliance

- Maintain audit trails
- Implement access controls
- Ensure data integrity

```yaml
layers:
  AUDIT:
    level: INFO
    destinations:
      - type: file
        path: logs/audit/access.log
        max_size: 2MB
        backup_count: 60  # Keep for 5 years
```

## Incident Response

### Security Incident Logging

```python
from datetime import datetime
from hydra_logger import HydraLogger

def log_security_incident(
    incident_type: str,
    description: str,
    severity: str,
    affected_systems: list,
    response_actions: list
):
    """Log security incidents with structured data."""
    incident_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": incident_type,
        "description": description,
        "severity": severity,
        "affected_systems": affected_systems,
        "response_actions": response_actions
    }
    
    logger = HydraLogger()
    logger.error("INCIDENT", f"Security incident: {incident_data}")

# Example usage
log_security_incident(
    incident_type="UNAUTHORIZED_ACCESS",
    description="Multiple failed login attempts detected",
    severity="HIGH",
    affected_systems=["web_server", "database"],
    response_actions=["blocked_ip", "notified_admin"]
)
```

## Security Checklist

- [ ] Set appropriate file permissions for log files
- [ ] Implement log rotation and retention policies
- [ ] Sanitize sensitive data before logging
- [ ] Use secure log file locations
- [ ] Disable console logging for sensitive data in production
- [ ] Implement monitoring and alerting for security events
- [ ] Consider log encryption for highly sensitive environments
- [ ] Ensure compliance with relevant regulations
- [ ] Document security incident response procedures
- [ ] Regularly review and update security configurations

## Reporting Security Issues

If you discover a security vulnerability in Hydra-Logger, please report it responsibly:

1. **Email**: razvan.i.savin@gmail.com
2. **GitHub Issues**: Use the security vulnerability template
3. **Private Disclosure**: For sensitive issues, use private GitHub issues

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available) 