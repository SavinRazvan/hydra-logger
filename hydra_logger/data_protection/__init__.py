"""
Data protection module for Hydra-Logger.

This module provides data protection, security validation, and fallback
mechanisms for safe logging operations.
"""

from hydra_logger.data_protection.fallbacks import FallbackHandler
from hydra_logger.data_protection.security import (
    DataSanitizer,
    SecurityValidator,
    DataHasher
)

__all__ = [
    "FallbackHandler",
    "DataSanitizer",
    "SecurityValidator",
    "DataHasher"
]
