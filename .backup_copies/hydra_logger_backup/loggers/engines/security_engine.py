"""
Security Engine for Hydra-Logger Loggers

This module provides security features including data validation,
sanitization, PII detection and redaction, security threat detection, and
compliance monitoring. It serves as the central security system for all logger implementations.

ARCHITECTURE:
- SecurityEngine: Central security and validation engine
- SecurityValidator: Data validation and threat detection
- DataSanitizer: Data sanitization and cleaning
- DataRedaction: PII detection and redaction
- Security monitoring and compliance tracking

CORE FEATURES:
- Data validation and sanitization
- PII detection and redaction
- Security threat detection
- Compliance monitoring and reporting
- Security metrics and statistics
- Configurable security levels

USAGE EXAMPLES:

Basic Security:
    from hydra_logger.loggers.engines import SecurityEngine
    
    # Create security engine
    security = SecurityEngine()
    
    # Enable security features
    security.set_security_enabled(True)
    security.set_sanitization_enabled(True)
    security.set_redaction_enabled(True)
    
    # Validate message
    result = security.validate_message("User login: john@example.com")
    print(f"Validation result: {result}")

Data Sanitization:
    from hydra_logger.loggers.engines import SecurityEngine
    
    # Create security engine
    security = SecurityEngine()
    
    # Enable sanitization
    security.set_sanitization_enabled(True)
    
    # Sanitize message
    sanitized = security.sanitize_message("Sensitive data: password123")
    print(f"Sanitized: {sanitized}")
    
    # Sanitize with custom options
    sanitized = security.sanitize_message(
        "User data: john.doe@example.com",
        remove_emails=True,
        remove_phones=True
    )
    print(f"Sanitized with options: {sanitized}")

PII Redaction:
    from hydra_logger.loggers.engines import SecurityEngine
    
    # Create security engine
    security = SecurityEngine()
    
    # Enable redaction
    security.set_redaction_enabled(True)
    
    # Redact sensitive data
    redacted = security.redact_sensitive_data("User: john@example.com, Phone: 555-1234")
    print(f"Redacted: {redacted}")
    
    # Redact with custom patterns
    redacted = security.redact_sensitive_data(
        "Credit card: 4111-1111-1111-1111",
        redact_credit_cards=True,
        redact_ssn=True
    )
    print(f"Redacted with patterns: {redacted}")

Security Threat Detection:
    from hydra_logger.loggers.engines import SecurityEngine
    
    # Create security engine
    security = SecurityEngine()
    
    # Enable security
    security.set_security_enabled(True)
    
    # Detect threats
    threats = security.detect_threats("Attempted SQL injection: ' OR 1=1 --")
    print(f"Threats detected: {threats['threats']}")
    print(f"Risk level: {threats['risk_level']}")
    
    # Detect threats with custom patterns
    threats = security.detect_threats(
        "Suspicious activity detected",
        check_sql_injection=True,
        check_xss=True,
        check_path_traversal=True
    )
    print(f"Custom threat detection: {threats}")

Log Record Processing:
    from hydra_logger.loggers.engines import SecurityEngine
    from hydra_logger.types.records import LogRecord
    
    # Create security engine
    security = SecurityEngine()
    
    # Enable all security features
    security.set_security_enabled(True)
    security.set_sanitization_enabled(True)
    security.set_redaction_enabled(True)
    
    # Create log record
    record = LogRecord(
        level=20,
        level_name="INFO",
        message="User login: john@example.com with password123",
        layer="auth",
        logger_name="auth_logger"
    )
    
    # Process record through security engine
    processed_record = security.process_log_record(record)
    print(f"Processed message: {processed_record.message}")

Security Metrics:
    from hydra_logger.loggers.engines import SecurityEngine
    
    # Create security engine
    security = SecurityEngine()
    
    # Enable security features
    security.set_security_enabled(True)
    security.set_sanitization_enabled(True)
    security.set_redaction_enabled(True)
    
    # Process some messages
    security.validate_message("Test message")
    security.sanitize_message("Sensitive data")
    security.redact_sensitive_data("PII data")
    
    # Get security metrics
    metrics = security.get_security_metrics()
    print(f"Security metrics: {metrics}")
    
    # Reset metrics
    security.reset_metrics()

Security Configuration:
    from hydra_logger.loggers.engines import SecurityEngine
    
    # Create security engine
    security = SecurityEngine()
    
    # Configure security levels
    security.set_security_enabled(True)
    security.set_sanitization_enabled(True)
    security.set_redaction_enabled(True)
    
    # Get individual components
    validator = security.get_validator()
    sanitizer = security.get_sanitizer()
    redactor = security.get_redactor()
    
    # Use components directly
    # (Components are typically used internally by the engine)

DATA VALIDATION:
- Message content validation
- Input sanitization and cleaning
- Format validation and verification
- Content type checking
- Validation error reporting

DATA SANITIZATION:
- Sensitive data removal
- Content cleaning and normalization
- Format standardization
- Malicious content filtering
- Custom sanitization rules

PII REDACTION:
- Email address redaction
- Phone number redaction
- Credit card redaction
- SSN redaction
- Custom PII pattern redaction

THREAT DETECTION:
- SQL injection detection
- XSS attack detection
- Path traversal detection
- Command injection detection
- Custom threat pattern detection

COMPLIANCE MONITORING:
- Security compliance tracking
- Audit trail generation
- Compliance reporting
- Security metrics collection
- Regulatory compliance support

ERROR HANDLING:
- Graceful error handling with fallback mechanisms
- Error isolation between security components
- Comprehensive error reporting
- Automatic security recovery
- Silent error handling for maximum performance

BENEFITS:
- Comprehensive security and validation system
- Easy integration with logger implementations
- Configurable security levels and options
- Production-ready security features
- Compliance and audit support
"""

from typing import Any, Dict, Optional, Union
from ...security.validator import SecurityValidator
from ...security.sanitizer import DataSanitizer
from ...security.redaction import DataRedaction
from ...types.records import LogRecord


class SecurityEngine:
    """Security and validation engine for loggers."""
    
    def __init__(self):
        """Initialize the security engine."""
        self._validator = SecurityValidator()
        self._sanitizer = DataSanitizer()
        self._redactor = DataRedaction()
        self._security_enabled = True
        self._sanitization_enabled = True
        self._redaction_enabled = True
        
        # Security statistics
        self._validation_count = 0
        self._sanitization_count = 0
        self._redaction_count = 0
        self._threat_detections = 0
    
    def set_security_enabled(self, enabled: bool) -> None:
        """Enable or disable security features."""
        self._security_enabled = enabled
    
    def set_sanitization_enabled(self, enabled: bool) -> None:
        """Enable or disable data sanitization."""
        self._sanitization_enabled = enabled
    
    def set_redaction_enabled(self, enabled: bool) -> None:
        """Enable or disable data redaction."""
        self._redaction_enabled = enabled
    
    def validate_message(self, message: str, **kwargs) -> Dict[str, Any]:
        """Validate a log message for security issues."""
        if not self._security_enabled:
            return {'valid': True, 'warnings': []}
        
        self._validation_count += 1
        
        try:
            result = self._validator.validate_message(message, **kwargs)
            return result
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'warnings': ['Validation failed']
            }
    
    def sanitize_message(self, message: str, **kwargs) -> str:
        """Sanitize a log message to remove potentially harmful content."""
        if not self._sanitization_enabled:
            return message
        
        self._sanitization_count += 1
        
        try:
            return self._sanitizer.sanitize(message, **kwargs)
        except Exception:
            # Return original message if sanitization fails
            return message
    
    def redact_sensitive_data(self, message: str, **kwargs) -> str:
        """Redact sensitive data from a log message."""
        if not self._redaction_enabled:
            return message
        
        self._redaction_count += 1
        
        try:
            return self._redactor.redact_data(message, **kwargs)
        except Exception:
            # Return original message if redaction fails
            return message
    
    def process_log_record(self, record: LogRecord) -> LogRecord:
        """Process a log record through all security features."""
        if not self._security_enabled:
            return record
        
        # Validate the message
        validation_result = self.validate_message(record.message)
        if not validation_result.get('valid', True):
            # Log security warning
            record.message = f"[SECURITY_WARNING] {record.message}"
        
        # Sanitize the message
        if self._sanitization_enabled:
            record.message = self.sanitize_message(record.message)
        
        # Redact sensitive data
        if self._redaction_enabled:
            record.message = self.redact_sensitive_data(record.message)
        
        return record
    
    def detect_threats(self, message: str, **kwargs) -> Dict[str, Any]:
        """Detect potential security threats in a message."""
        if not self._security_enabled:
            return {'threats': [], 'risk_level': 'low'}
        
        try:
            threats = self._validator.detect_threats(message, **kwargs)
            if threats:
                self._threat_detections += 1
            
            return {
                'threats': threats,
                'risk_level': 'high' if threats else 'low'
            }
        except Exception:
            return {'threats': [], 'risk_level': 'unknown'}
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics."""
        return {
            'security_enabled': self._security_enabled,
            'sanitization_enabled': self._sanitization_enabled,
            'redaction_enabled': self._redaction_enabled,
            'validation_count': self._validation_count,
            'sanitization_count': self._sanitization_count,
            'redaction_count': self._redaction_count,
            'threat_detections': self._threat_detections
        }
    
    def reset_metrics(self) -> None:
        """Reset security metrics."""
        self._validation_count = 0
        self._sanitization_count = 0
        self._redaction_count = 0
        self._threat_detections = 0
    
    def get_validator(self) -> SecurityValidator:
        """Get the security validator."""
        return self._validator
    
    def get_sanitizer(self) -> DataSanitizer:
        """Get the data sanitizer."""
        return self._sanitizer
    
    def get_redactor(self) -> DataRedaction:
        """Get the data redactor."""
        return self._redactor
