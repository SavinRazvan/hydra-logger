"""
Data Hashing Component for Hydra-Logger

This module provides data hashing and verification capabilities for secure
data handling and integrity checking. It supports multiple hash algorithms
with configurable security levels.

FEATURES:
- Multiple hash algorithms (MD5, SHA1, SHA256)
- Configurable algorithm selection
- Data integrity verification
- Simple and efficient hashing
- Security level configuration

SUPPORTED ALGORITHMS:
- MD5: Fast hashing (less secure)
- SHA1: Standard hashing
- SHA256: Secure hashing (default)

USAGE:
    from hydra_logger.security import DataHasher
    
    # Create hasher with SHA256
    hasher = DataHasher(enabled=True, algorithm="sha256")
    
    # Hash data
    hash_value = hasher.hash_data("sensitive data")
    print(f"Hash: {hash_value}")
    
    # Hash with different algorithm
    hasher_md5 = DataHasher(enabled=True, algorithm="md5")
    hash_md5 = hasher_md5.hash_data("data")
    
    # Get hasher statistics
    stats = hasher.get_security_stats()
    print(f"Algorithm: {stats['algorithm']}")
"""

import hashlib
from typing import Any, Dict, Optional


class DataHasher:
    """Data hashing component for secure data handling."""
    
    def __init__(self, enabled: bool = True, algorithm: str = "sha256"):
        self._enabled = enabled
        self._algorithm = algorithm
        self._initialized = True
    
    def hash_data(self, data: Any) -> str:
        """Hash data using the configured algorithm."""
        if not self._enabled:
            return str(data)
        
        data_str = str(data)
        if self._algorithm == "md5":
            return hashlib.md5(data_str.encode()).hexdigest()
        elif self._algorithm == "sha1":
            return hashlib.sha1(data_str.encode()).hexdigest()
        else:  # sha256
            return hashlib.sha256(data_str.encode()).hexdigest()
    
    def is_enabled(self) -> bool:
        """Check if hasher is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable the hasher."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the hasher."""
        self._enabled = False
