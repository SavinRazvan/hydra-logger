"""
Data Sanitization Component for Hydra-Logger

This module provides comprehensive data sanitization capabilities to ensure
sensitive information is properly handled in log records. It supports
pattern-based detection, multiple sanitization strategies, and configurable
security levels.

FEATURES:
- Pattern-based sensitive data detection
- Multiple sanitization strategies (redact, hash, mask)
- Configurable security levels (basic, standard, strict)
- Custom pattern and key management
- Performance-optimized sanitization
- Comprehensive statistics and monitoring

SENSITIVE PATTERNS:
- Credit Cards: Credit card number patterns
- SSN: Social Security Numbers
- Email: Email addresses
- Phone: Phone numbers
- API Keys: API key patterns
- Passwords: Password field patterns

SANITIZATION STRATEGIES:
- Redact: Replace with [REDACTED]
- Hash: Replace with [HASH:hash_value]
- Mask: Show first and last characters

USAGE:
    from hydra_logger.security import DataSanitizer
    
    # Create sanitizer with standard security
    sanitizer = DataSanitizer(
        enabled=True,
        security_level="standard"
    )
    
    # Sanitize data with redaction
    sanitized = sanitizer.sanitize_data(
        {"email": "user@example.com", "password": "secret123"},
        strategy="redact"
    )
    
    # Add custom sensitive key
    sanitizer.add_sensitive_key("api_token")
    
    # Add custom pattern
    sanitizer.add_pattern("custom_id", r"ID-\\d{6}")
    
    # Get sanitization statistics
    stats = sanitizer.get_security_stats()
    print(f"Records processed: {stats['records_processed']}")
"""

import re
import hashlib
from typing import Any, Dict, List, Optional, Union


class DataSanitizer:
    """
    Professional data sanitizer for sensitive information.
    
    Features:
    - Pattern-based sensitive data detection
    - Configurable redaction strategies
    - Hash-based sensitive field protection
    - Performance-optimized sanitization
    """
    
    def __init__(self, enabled: bool = True, security_level: str = "standard"):
        """
        Initialize data sanitizer.
        
        Args:
            enabled: Whether sanitization is enabled
            security_level: Security level (basic, standard, strict)
        """
        self._enabled = enabled
        self._security_level = security_level
        self._initialized = False
        
        # Sensitive patterns (credit cards, SSNs, emails, etc.)
        self._sensitive_patterns = {
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'api_key': r'\b[A-Za-z0-9]{32,}\b',
            'password': r'\bpassword["\s]*[:=]\s*["\s]*[^"\s]+\b',
            'token': r'\btoken["\s]*[:=]\s*["\s]*[^"\s]+\b',
        }
        
        # Compile patterns for performance
        self._compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self._sensitive_patterns.items()
        }
        
        # Sensitive keys that should always be redacted
        self._sensitive_keys = {
            'password', 'passwd', 'pwd', 'secret', 'key', 'token',
            'auth', 'authorization', 'credential', 'private', 'sensitive'
        }
        
        # Sanitization statistics
        self._sanitization_stats = {
            'records_processed': 0,
            'fields_sanitized': 0,
            'patterns_matched': 0,
            'errors': 0
        }
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the sanitizer."""
        try:
            # Validate security level
            if self._security_level not in ['basic', 'standard', 'strict']:
                self._security_level = 'standard'
            
            # Add additional patterns for strict mode
            if self._security_level == 'strict':
                self._add_strict_patterns()
            
            self._initialized = True
            
        except Exception as e:
            self._sanitization_stats['errors'] += 1
            raise RuntimeError(f"Failed to initialize DataSanitizer: {e}")
    
    def _add_strict_patterns(self) -> None:
        """Add additional patterns for strict security mode."""
        strict_patterns = {
            'uuid': r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',
            'mac_address': r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b',
            'file_path': r'\b(/[a-zA-Z0-9._/-]+|C:\\[a-zA-Z0-9._\\-]+)\b',
            'url_path': r'https?://[^\s]+',
        }
        
        self._sensitive_patterns.update(strict_patterns)
        self._compiled_patterns.update({
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in strict_patterns.items()
        })
    
    def sanitize_data(self, data: Any, strategy: str = "redact") -> Any:
        """
        Sanitize sensitive data.
        
        Args:
            data: Data to sanitize
            strategy: Sanitization strategy (redact, hash, mask)
            
        Returns:
            Sanitized data
        """
        if not self._enabled or not self._initialized:
            return data
        
        try:
            self._sanitization_stats['records_processed'] += 1
            
            if isinstance(data, dict):
                return self._sanitize_dict(data, strategy)
            elif isinstance(data, list):
                return self._sanitize_list(data, strategy)
            elif isinstance(data, str):
                return self._sanitize_string(data, strategy)
            else:
                return data
                
        except Exception as e:
            self._sanitization_stats['errors'] += 1
            # Return original data on error to avoid breaking logging
            return data
    
    def _sanitize_dict(self, data: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """Sanitize dictionary data."""
        sanitized = {}
        
        for key, value in data.items():
            # Check if key itself is sensitive
            if self._is_sensitive_key(key):
                sanitized[key] = self._apply_strategy(value, strategy)
                self._sanitization_stats['fields_sanitized'] += 1
            else:
                # Recursively sanitize nested values
                sanitized[key] = self.sanitize_data(value, strategy)
        
        return sanitized
    
    def _sanitize_list(self, data: List[Any], strategy: str) -> List[Any]:
        """Sanitize list data."""
        return [self.sanitize_data(item, strategy) for item in data]
    
    def _sanitize_string(self, data: str, strategy: str) -> str:
        """Sanitize string data."""
        if not data:
            return data
        
        # Check for sensitive patterns
        for pattern_name, pattern in self._compiled_patterns.items():
            if pattern.search(data):
                self._sanitization_stats['patterns_matched'] += 1
                return self._apply_strategy(data, strategy)
        
        return data
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key is sensitive."""
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self._sensitive_keys)
    
    def _apply_strategy(self, value: Any, strategy: str) -> Any:
        """Apply sanitization strategy."""
        if strategy == "redact":
            return "[REDACTED]"
        elif strategy == "hash":
            return self._hash_value(value)
        elif strategy == "mask":
            return self._mask_value(value)
        else:
            return "[REDACTED]"  # Default to redaction
    
    def _hash_value(self, value: Any) -> str:
        """Hash a value for consistent but secure representation."""
        if isinstance(value, str):
            return f"[HASH:{hashlib.md5(value.encode()).hexdigest()[:8]}]"
        else:
            return f"[HASH:{hashlib.md5(str(value).encode()).hexdigest()[:8]}]"
    
    def _mask_value(self, value: Any) -> str:
        """Mask a value showing only first and last characters."""
        if isinstance(value, str) and len(value) > 2:
            return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
        else:
            return "[MASKED]"
    
    def add_pattern(self, name: str, pattern: str) -> bool:
        """
        Add a custom sensitive pattern.
        
        Args:
            name: Pattern name
            pattern: Regex pattern
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            self._sensitive_patterns[name] = pattern
            self._compiled_patterns[name] = compiled
            return True
        except re.error:
            return False
    
    def remove_pattern(self, name: str) -> bool:
        """
        Remove a sensitive pattern.
        
        Args:
            name: Pattern name
            
        Returns:
            True if removed successfully, False otherwise
        """
        if name in self._sensitive_patterns:
            del self._sensitive_patterns[name]
            del self._compiled_patterns[name]
            return True
        return False
    
    def add_sensitive_key(self, key: str) -> None:
        """Add a sensitive key."""
        self._sensitive_keys.add(key.lower())
    
    def remove_sensitive_key(self, key: str) -> None:
        """Remove a sensitive key."""
        self._sensitive_keys.discard(key.lower())
    
    def is_enabled(self) -> bool:
        """Check if sanitizer is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable sanitizer."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable sanitizer."""
        self._enabled = False
