"""
Security Extensions for Hydra-Logger

Simple, modular security components with professional naming conventions.
Zero overhead when disabled, high performance when enabled.

ARCHITECTURE:
- DataRedaction: Redact sensitive information (PII, API keys, etc.)
- DataSanitizer: Sanitize and clean log data
- SecurityValidator: Validate data for security threats
- SecurityManager: Central security management

NAMING CONVENTIONS:
- All classes end with descriptive suffixes: *Redaction, *Sanitizer, *Validator, *Manager
- All files follow pattern: *_utility.py, *_manager.py
- Simple, clear, professional naming
- No abbreviations or confusing terms

USAGE:
    from hydra_logger.extensions.security import SecurityManager
    
    # Create security manager
    security = SecurityManager()
    
    # Enable specific features
    security.enable_redaction(['email', 'phone', 'api_key'])
    security.enable_sanitization()
    security.enable_validation()
    
    # Process data
    result = security.process("User login: john@example.com")
"""

from .data_redaction import DataRedaction
from .data_sanitizer import DataSanitizer
from .security_validator import SecurityValidator
from .security_manager import SecurityManager

__all__ = [
    "DataRedaction",
    "DataSanitizer", 
    "SecurityValidator",
    "SecurityManager"
]
