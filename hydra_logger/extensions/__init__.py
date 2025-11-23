"""
Hydra-Logger Extensions System

User-controllable extension system with zero overhead when disabled.
Users have full control over formats, destinations, configurations, and extensions.

ARCHITECTURE:
- ExtensionBase: Base class for all extensions
- ExtensionManager: Central management system
- SecurityExtension: Data redaction and sanitization
- FormattingExtension: Message formatting and enhancement
- PerformanceExtension: Performance monitoring

USER CONTROL:
- Enable/disable any extension
- Configure extension parameters
- Choose processing order
- Add custom extensions
- Control via LoggingConfig

NAMING CONVENTIONS:
- Descriptive naming
- Consistent with project standards
- Clear, unambiguous terminology
"""

from .extension_base import (
    ExtensionBase,
    SecurityExtension,
    FormattingExtension,
    PerformanceExtension,
)
from .extension_manager import ExtensionManager

# Exports
__all__ = [
    # Base classes
    "ExtensionBase",
    # Extension implementations
    "SecurityExtension",
    "FormattingExtension",
    "PerformanceExtension",
    # Management
    "ExtensionManager",
]
