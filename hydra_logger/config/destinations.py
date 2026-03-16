"""
Role: Destination configuration model entrypoints.
Used By:
 - `hydra_logger.config`
Depends On:
 - hydra_logger
Notes:
 - Transitional modular facade around destination model definitions.
"""

from .models import LogDestination

__all__ = ["LogDestination"]
