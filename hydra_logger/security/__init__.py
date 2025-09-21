"""
Security Module for Hydra-Logger

This module provides comprehensive security and data protection features
including data sanitization, validation, encryption, threat detection,
access control, audit logging, and compliance management. It offers
configurable security levels and performance-optimized processing.

FEATURES:
- Data sanitization and redaction
- Input validation and threat detection
- Encryption and cryptographic utilities
- Access control and audit logging
- Compliance management (GDPR, HIPAA, SOX)
- Background processing for performance
- Configurable security levels

SECURITY COMPONENTS:
- DataSanitizer: Pattern-based data sanitization
- SecurityValidator: Input validation and threat detection
- DataHasher: Data hashing and integrity checking
- DataEncryption: AES encryption and decryption
- DataRedaction: Sensitive data redaction
- ThreatDetector: Security threat detection
- ComplianceManager: Regulatory compliance checking
- AccessController: Role-based access control
- AuditLogger: Security audit logging
- CryptoUtils: Advanced cryptographic operations

USAGE:
    from hydra_logger.security import DataSanitizer, SecurityValidator
    
    # Create security components
    sanitizer = DataSanitizer(enabled=True, security_level="standard")
    validator = SecurityValidator(enabled=True, security_level="standard")
    
    # Sanitize sensitive data
    sanitized_data = sanitizer.sanitize_data(data, strategy="redact")
    
    # Validate input for threats
    validation_result = validator.validate_input(input_data, context="general")
    
    # Check if validation passed
    if validation_result['valid']:
        # Process validated data
        pass
    else:
        # Handle threats and warnings
        for threat in validation_result['threats']:
            print(f"Threat detected: {threat['type']}")
"""

from .sanitizer import DataSanitizer
from .validator import SecurityValidator
from .hasher import DataHasher
from .encryption import DataEncryption
from .redaction import DataRedaction
from .access_control import AccessController

__all__ = [
    # Core security components (KISS principle)
    "DataSanitizer",
    "SecurityValidator", 
    "DataHasher",
    "DataEncryption",
    "DataRedaction",
    "AccessController",
]
