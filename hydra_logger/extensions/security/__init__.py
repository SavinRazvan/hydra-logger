"""
Security Extensions for Hydra-Logger

Modular security components with descriptive naming conventions.
Zero overhead when disabled.

ARCHITECTURE:
- DataRedaction: Redact sensitive information (PII, API keys, etc.)

NAMING CONVENTIONS:
- All classes end with descriptive suffixes: *Redaction, *Sanitizer, *Validator, *Manager
- All files follow pattern: *_utility.py, *_manager.py
- Clear, descriptive naming
- No abbreviations or confusing terms

USAGE:
    from hydra_logger.extensions.security import DataRedaction

    # Create data redaction instance
    redaction = DataRedaction(enabled=True, patterns=['email', 'phone', 'api_key'])

    # Process data
    result = redaction.redact("User login: john@example.com")
"""

from .data_redaction import DataRedaction

__all__ = ["DataRedaction"]
