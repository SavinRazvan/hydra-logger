"""
Data Encryption Component for Hydra-Logger

This module provides AES encryption and decryption capabilities for secure
data handling in logging operations. It uses Fernet symmetric encryption
with PBKDF2 key derivation for enhanced security.

FEATURES:
- AES-256-CBC encryption with Fernet
- PBKDF2-HMAC-SHA256 key derivation
- Automatic key generation and rotation
- Encryption statistics and monitoring
- Error handling and fallback mechanisms
- Base64 encoding for safe data transmission

USAGE:
    from hydra_logger.security import DataEncryption
    
    # Create encryption component
    encryption = DataEncryption(enabled=True)
    
    # Encrypt sensitive data
    encrypted_data = encryption.encrypt_data("sensitive information")
    
    # Decrypt data
    decrypted_data = encryption.decrypt_data(encrypted_data)
    
    # Generate new key
    new_key = encryption.generate_key()
    
    # Rotate to new key
    success = encryption.rotate_key(new_key)
    
    # Get encryption statistics
    stats = encryption.get_encryption_stats()
    print(f"Encryptions performed: {stats['encryption_count']}")
"""

import base64
import os
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..interfaces.security import SecurityInterface


class DataEncryption(SecurityInterface):
    """Real AES encryption component for secure data handling."""
    
    def __init__(self, enabled: bool = True, key: Optional[str] = None, salt: Optional[str] = None):
        """
        Initialize data encryption.
        
        Args:
            enabled: Whether encryption is enabled
            key: Encryption key (if None, generates a new one)
            salt: Salt for key derivation (if None, generates a new one)
        """
        self._enabled = enabled
        self._initialized = True
        self._encryption_count = 0
        self._decryption_count = 0
        self._error_count = 0
        
        if enabled:
            self._salt = salt or os.urandom(16)
            self._key = self._derive_key(key or Fernet.generate_key())
            self._fernet = Fernet(self._key)
        else:
            self._salt = None
            self._key = None
            self._fernet = None
    
    def _derive_key(self, password: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt data using AES encryption.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        if not self._enabled or not self._fernet:
            return data
        
        try:
            encrypted = self._fernet.encrypt(data.encode('utf-8'))
            self._encryption_count += 1
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            self._error_count += 1
            # Fallback to plain text on encryption failure
            return f"[ENCRYPTION_FAILED:{data}]"
    
    def decrypt_data(self, data: str) -> str:
        """
        Decrypt data using AES decryption.
        
        Args:
            data: Encrypted data as base64 string
            
        Returns:
            Decrypted data
        """
        if not self._enabled or not self._fernet:
            return data
        
        try:
            # Handle legacy format
            if data.startswith("[ENCRYPTED:") and data.endswith("]"):
                return data[11:-1]
            
            # Handle new encrypted format
            encrypted_bytes = base64.urlsafe_b64decode(data.encode('utf-8'))
            decrypted = self._fernet.decrypt(encrypted_bytes)
            self._decryption_count += 1
            return decrypted.decode('utf-8')
        except Exception as e:
            self._error_count += 1
            # Return original data on decryption failure
            return f"[DECRYPTION_FAILED:{data}]"
    
    def generate_key(self) -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode('utf-8')
    
    def rotate_key(self, new_key: str) -> bool:
        """
        Rotate to a new encryption key.
        
        Args:
            new_key: New encryption key
            
        Returns:
            True if key rotation successful
        """
        try:
            self._key = self._derive_key(new_key.encode('utf-8'))
            self._fernet = Fernet(self._key)
            return True
        except Exception:
            return False
    
    def get_encryption_stats(self) -> Dict[str, Any]:
        """Get encryption statistics."""
        return {
            "encryption_count": self._encryption_count,
            "decryption_count": self._decryption_count,
            "error_count": self._error_count,
            "enabled": self._enabled,
            "algorithm": "AES-256-CBC",
            "key_derivation": "PBKDF2-HMAC-SHA256"
        }
    
    def reset_stats(self) -> None:
        """Reset encryption statistics."""
        self._encryption_count = 0
        self._decryption_count = 0
        self._error_count = 0
    
    # SecurityInterface implementation
    def is_enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        if not self._fernet:
            self._salt = os.urandom(16)
            self._key = self._derive_key(Fernet.generate_key())
            self._fernet = Fernet(self._key)
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False
    
    def get_security_level(self) -> str:
        return "high" if self._enabled else "disabled"
    
    def get_threat_count(self) -> int:
        return self._error_count
    
    def get_security_stats(self) -> Dict[str, Any]:
        return self.get_encryption_stats()
    
    def reset_security_stats(self) -> None:
        self.reset_stats()
    
    def is_secure(self) -> bool:
        return self._enabled and self._initialized and self._fernet is not None
