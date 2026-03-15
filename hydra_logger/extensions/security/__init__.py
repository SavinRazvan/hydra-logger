"""
Role: Init implementation.
Used By:
 - (update when known)
Depends On:
 - data_redaction
Notes:
 - Header standardized by slim-header migration.
"""

from .data_redaction import DataRedaction

__all__ = ["DataRedaction"]
