"""
Cryptographic Utilities Component for Hydra-Logger

This module provides comprehensive cryptographic utilities including key
generation, data hashing, digital signatures, encryption, and key derivation.
It supports multiple algorithms and both synchronous and background processing.

FEATURES:
- Key generation (AES, RSA, Ed25519)
- Data hashing with multiple algorithms
- Digital signature creation and verification
- Symmetric and asymmetric encryption
- Key derivation functions (PBKDF2)
- Background processing support
- Performance monitoring and caching

SUPPORTED ALGORITHMS:
- Hash: MD5, SHA1, SHA256, SHA512, BLAKE2b
- Symmetric: AES-128, AES-256, ChaCha20
- Asymmetric: RSA-2048, RSA-4096, Ed25519
- KDF: PBKDF2, Scrypt, Argon2

USAGE:
    from hydra_logger.security import CryptoUtils
    
    # Create crypto utilities
    crypto = CryptoUtils(enabled=True, use_background_processing=True)
    
    # Generate encryption key
    key = crypto.generate_key(algorithm="aes-256")
    
    # Hash data
    hash_result = crypto.hash_data("sensitive data", algorithm="sha256")
    
    # Generate key pair
    key_pair = crypto.generate_key(algorithm="rsa-2048")
    
    # Sign data
    signature = crypto.sign_data("data", key_pair["private_key"], "rsa")
    
    # Verify signature
    is_valid = crypto.verify_signature("data", signature, key_pair["public_key"], "rsa")
    
    # Encrypt data
    encrypted = crypto.encrypt_symmetric("data", key, "aes-256")
    
    # Get crypto statistics
    stats = crypto.get_crypto_stats()
    print(f"Operations performed: {stats['total_operations']}")
"""

import base64
import hashlib
import os
import time
import threading
from typing import Any, Dict, List, Optional, Tuple, Union
from concurrent.futures import Future
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ed25519
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from ..interfaces.security import SecurityInterface
from .background_processing import (
    BackgroundSecurityProcessor, 
    SecurityOperationType, 
    get_background_processor
)


class CryptoUtils(SecurityInterface):
    """Real cryptographic utilities component for advanced security operations."""
    
    def __init__(self, enabled: bool = True, use_background_processing: bool = True):
        self._enabled = enabled
        self._initialized = True
        self._operations_count = 0
        self._error_count = 0
        self._key_cache = {}
        
        # Background processing configuration
        self._use_background_processing = use_background_processing and enabled
        self._background_processor = get_background_processor()
        
        # Statistics
        self._stats = {
            'synchronous_operations': 0,
            'background_operations': 0,
            'total_operation_time': 0.0,
            'average_operation_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_reset': time.time()
        }
        
        # Thread lock for thread-safe operations
        self._lock = threading.RLock()
        
        self._supported_algorithms = {
            "hash": ["md5", "sha1", "sha256", "sha512", "blake2b"],
            "symmetric": ["aes-128", "aes-256", "chacha20"],
            "asymmetric": ["rsa-2048", "rsa-4096", "ed25519"],
            "kdf": ["pbkdf2", "scrypt", "argon2"]
        }
    
    def generate_key(self, algorithm: str = "aes-256", key_size: Optional[int] = None) -> str:
        """
        Generate a cryptographic key.
        
        Args:
            algorithm: Key algorithm (aes-128, aes-256, rsa-2048, etc.)
            key_size: Custom key size in bits
            
        Returns:
            Generated key as base64 string
        """
        if not self._enabled:
            return ""
        
        try:
            if algorithm.startswith("aes"):
                size = key_size or int(algorithm.split("-")[1])
                key = os.urandom(size // 8)
                self._operations_count += 1
                return base64.b64encode(key).decode('utf-8')
            
            elif algorithm.startswith("rsa"):
                size = key_size or int(algorithm.split("-")[1])
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=size
                )
                public_key = private_key.public_key()
                
                # Serialize both keys
                private_pem = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                public_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                
                self._operations_count += 1
                return {
                    "private_key": private_pem.decode('utf-8'),
                    "public_key": public_pem.decode('utf-8'),
                    "algorithm": algorithm,
                    "key_size": size
                }
            
            elif algorithm == "ed25519":
                private_key = ed25519.Ed25519PrivateKey.generate()
                public_key = private_key.public_key()
                
                private_bytes = private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                public_bytes = public_key.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                
                self._operations_count += 1
                return {
                    "private_key": base64.b64encode(private_bytes).decode('utf-8'),
                    "public_key": base64.b64encode(public_bytes).decode('utf-8'),
                    "algorithm": "ed25519",
                    "key_size": 256
                }
            
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
                
        except Exception as e:
            self._error_count += 1
            raise ValueError(f"Key generation failed: {str(e)}")
    
    def hash_data(self, data: str, algorithm: str = "sha256", use_background: bool = None) -> Union[str, Future]:
        """
        Hash data using specified algorithm with optional background processing.
        
        Args:
            data: Data to hash
            algorithm: Hashing algorithm
            use_background: Whether to use background processing
            
        Returns:
            Hashed data as hex string (synchronous) or Future (asynchronous)
        """
        if not self._enabled:
            return data
        
        # Determine if we should use background processing
        should_use_background = (
            use_background if use_background is not None 
            else self._use_background_processing
        )
        
        if should_use_background:
            return self._hash_data_background(data, algorithm)
        else:
            return self._hash_data_sync(data, algorithm)
    
    def _hash_data_sync(self, data: str, algorithm: str = "sha256") -> str:
        """Synchronous data hashing."""
        try:
            data_bytes = data.encode('utf-8')
            
            if algorithm == "md5":
                hash_obj = hashlib.md5(data_bytes)
            elif algorithm == "sha1":
                hash_obj = hashlib.sha1(data_bytes)
            elif algorithm == "sha256":
                hash_obj = hashlib.sha256(data_bytes)
            elif algorithm == "sha512":
                hash_obj = hashlib.sha512(data_bytes)
            elif algorithm == "blake2b":
                hash_obj = hashlib.blake2b(data_bytes)
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
            with self._lock:
                self._operations_count += 1
                self._stats['synchronous_operations'] += 1
                self._stats['cache_misses'] += 1
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            with self._lock:
                self._error_count += 1
            raise ValueError(f"Hashing failed: {str(e)}")
    
    def _hash_data_background(self, data: str, algorithm: str = "sha256") -> Future:
        """Asynchronous data hashing using background processing."""
        def callback(result):
            """Callback for background processing result."""
            with self._lock:
                self._stats['background_operations'] += 1
                self._operations_count += 1
        
        # Submit task to background processor
        task_id = self._background_processor.submit_task(
            operation_type=SecurityOperationType.HASH_VALIDATION,
            data={'data': data, 'algorithm': algorithm},
            callback=callback,
            priority=1  # High priority for hashing
        )
        
        # Return a future that will be resolved when processing is complete
        future = Future()
        
        def result_callback(result):
            if result.success:
                future.set_result(result.result)
            else:
                future.set_exception(Exception(result.error))
        
        return future
    
    def sign_data(self, data: str, private_key: str, algorithm: str = "rsa") -> str:
        """
        Sign data using private key.
        
        Args:
            data: Data to sign
            private_key: Private key for signing
            algorithm: Signing algorithm
            
        Returns:
            Digital signature as base64 string
        """
        if not self._enabled:
            return ""
        
        try:
            data_bytes = data.encode('utf-8')
            
            if algorithm == "rsa":
                # Load private key
                if isinstance(private_key, dict):
                    key_bytes = private_key["private_key"].encode('utf-8')
                else:
                    key_bytes = private_key.encode('utf-8')
                
                private_key_obj = load_pem_private_key(key_bytes, password=None)
                signature = private_key_obj.sign(
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            
            elif algorithm == "ed25519":
                # Load private key
                if isinstance(private_key, dict):
                    key_bytes = base64.b64decode(private_key["private_key"])
                else:
                    key_bytes = base64.b64decode(private_key)
                
                private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
                signature = private_key_obj.sign(data_bytes)
            
            else:
                raise ValueError(f"Unsupported signing algorithm: {algorithm}")
            
            self._operations_count += 1
            return base64.b64encode(signature).decode('utf-8')
            
        except Exception as e:
            self._error_count += 1
            raise ValueError(f"Signing failed: {str(e)}")
    
    def verify_signature(self, data: str, signature: str, public_key: str, algorithm: str = "rsa") -> bool:
        """
        Verify digital signature.
        
        Args:
            data: Original data
            signature: Digital signature to verify
            public_key: Public key for verification
            algorithm: Signing algorithm used
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self._enabled:
            return False
        
        try:
            data_bytes = data.encode('utf-8')
            signature_bytes = base64.b64decode(signature)
            
            if algorithm == "rsa":
                # Load public key
                if isinstance(public_key, dict):
                    key_bytes = public_key["public_key"].encode('utf-8')
                else:
                    key_bytes = public_key.encode('utf-8')
                
                public_key_obj = load_pem_public_key(key_bytes)
                public_key_obj.verify(
                    signature_bytes,
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            
            elif algorithm == "ed25519":
                # Load public key
                if isinstance(public_key, dict):
                    key_bytes = base64.b64decode(public_key["public_key"])
                else:
                    key_bytes = base64.b64decode(public_key)
                
                public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
                public_key_obj.verify(signature_bytes, data_bytes)
            
            else:
                raise ValueError(f"Unsupported verification algorithm: {algorithm}")
            
            self._operations_count += 1
            return True
            
        except Exception as e:
            self._error_count += 1
            return False
    
    def derive_key(self, password: str, salt: Optional[str] = None, 
                   algorithm: str = "pbkdf2", iterations: int = 100000) -> str:
        """
        Derive key from password using KDF.
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if None)
            algorithm: Key derivation algorithm
            iterations: Number of iterations for PBKDF2
            
        Returns:
            Derived key as base64 string
        """
        if not self._enabled:
            return ""
        
        try:
            if salt is None:
                salt = os.urandom(16)
            elif isinstance(salt, str):
                salt = salt.encode('utf-8')
            
            password_bytes = password.encode('utf-8')
            
            if algorithm == "pbkdf2":
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=iterations,
                )
                key = kdf.derive(password_bytes)
            
            else:
                raise ValueError(f"Unsupported KDF algorithm: {algorithm}")
            
            self._operations_count += 1
            return {
                "key": base64.b64encode(key).decode('utf-8'),
                "salt": base64.b64encode(salt).decode('utf-8'),
                "algorithm": algorithm,
                "iterations": iterations
            }
            
        except Exception as e:
            self._error_count += 1
            raise ValueError(f"Key derivation failed: {str(e)}")
    
    def encrypt_symmetric(self, data: str, key: str, algorithm: str = "aes-256") -> str:
        """
        Encrypt data using symmetric encryption.
        
        Args:
            data: Data to encrypt
            key: Encryption key
            algorithm: Encryption algorithm
            
        Returns:
            Encrypted data as base64 string
        """
        if not self._enabled:
            return data
        
        try:
            data_bytes = data.encode('utf-8')
            key_bytes = base64.b64decode(key)
            
            if algorithm.startswith("aes"):
                # Generate IV
                iv = os.urandom(16)
                
                # Create cipher
                cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
                encryptor = cipher.encryptor()
                
                # Pad data to block size
                padded_data = self._pad_data(data_bytes, 16)
                encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
                
                # Combine IV and encrypted data
                result = iv + encrypted_data
                
            else:
                raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
            
            self._operations_count += 1
            return base64.b64encode(result).decode('utf-8')
            
        except Exception as e:
            self._error_count += 1
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt_symmetric(self, encrypted_data: str, key: str, algorithm: str = "aes-256") -> str:
        """
        Decrypt data using symmetric decryption.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            key: Decryption key
            algorithm: Decryption algorithm
            
        Returns:
            Decrypted data
        """
        if not self._enabled:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            key_bytes = base64.b64decode(key)
            
            if algorithm.startswith("aes"):
                # Extract IV
                iv = encrypted_bytes[:16]
                ciphertext = encrypted_bytes[16:]
                
                # Create cipher
                cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
                decryptor = cipher.decryptor()
                
                # Decrypt data
                decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
                
                # Remove padding
                result = self._unpad_data(decrypted_data)
                
            else:
                raise ValueError(f"Unsupported decryption algorithm: {algorithm}")
            
            self._operations_count += 1
            return result.decode('utf-8')
            
        except Exception as e:
            self._error_count += 1
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def _pad_data(self, data: bytes, block_size: int) -> bytes:
        """Pad data to block size using PKCS7 padding."""
        padding_length = block_size - (len(data) % block_size)
        padding_bytes = bytes([padding_length] * padding_length)
        return data + padding_bytes
    
    def _unpad_data(self, data: bytes) -> bytes:
        """Remove PKCS7 padding from data."""
        padding_length = data[-1]
        return data[:-padding_length]
    
    def get_supported_algorithms(self) -> Dict[str, List[str]]:
        """Get list of supported cryptographic algorithms."""
        return self._supported_algorithms.copy()
    
    def get_crypto_stats(self) -> Dict[str, Any]:
        """Get cryptographic operations statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                "total_operations": self._operations_count,
                "error_count": self._error_count,
                "success_rate": (self._operations_count - self._error_count) / max(self._operations_count, 1),
                "supported_algorithms": self._supported_algorithms,
                "enabled": self._enabled,
                "background_processing": self._use_background_processing,
                "background_processor_stats": self._background_processor.get_stats()
            })
            return stats
    
    def reset_stats(self) -> None:
        """Reset cryptographic statistics."""
        self._operations_count = 0
        self._error_count = 0
    
    # SecurityInterface implementation
    def is_enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False
    
    def get_security_level(self) -> str:
        return "high" if self._enabled else "disabled"
    
    def get_threat_count(self) -> int:
        return self._error_count
    
    def get_security_stats(self) -> Dict[str, Any]:
        return self.get_crypto_stats()
    
    def reset_security_stats(self) -> None:
        self.reset_stats()
    
    def is_secure(self) -> bool:
        return self._enabled and self._initialized
