"""
Role: Layer configuration model entrypoints.
Used By:
 - `hydra_logger.config`
Depends On:
 - hydra_logger
Notes:
 - Transitional modular facade around layer model definitions.
"""

from .models import LogLayer

__all__ = ["LogLayer"]
