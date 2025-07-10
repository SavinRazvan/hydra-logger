"""
Security and data protection utilities for Hydra-Logger.

This module provides utilities for data sanitization, PII detection,
and security measures for log data.
"""

import re
import hashlib
from typing import Any, Dict, List, Optional, Union

from hydra_logger.core.constants import PII_PATTERNS
from hydra_logger.core.exceptions import DataProtectionError


class DataSanitizer:
    """Data sanitization utilities."""
    
    def __init__(self, redact_patterns: Optional[Dict[str, str]] = None):
        """
        Initialize data sanitizer.
        
        Args:
            redact_patterns: Custom redaction patterns
        """
        self.redact_patterns = redact_patterns or PII_PATTERNS.copy()
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for performance."""
        return {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.redact_patterns.items()
        }
    
    def sanitize_data(self, data: Any, depth: int = 0) -> Any:
        """
        Sanitize data by redacting sensitive information.
        
        Args:
            data: Data to sanitize
            depth: Current recursion depth (to prevent infinite recursion)
            
        Returns:
            Sanitized data
        """
        # Prevent infinite recursion
        if depth > 10:
            return "[REDACTED_CIRCULAR_REFERENCE]"
            
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return self._sanitize_dict(data, depth + 1)
        elif isinstance(data, (list, tuple)):
            return self._sanitize_list(data, depth + 1)
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string by redacting sensitive patterns."""
        sanitized = text
        
        for pattern_name, pattern in self._compiled_patterns.items():
            if pattern_name in ["email", "credit_card", "ssn", "phone"]:
                sanitized = pattern.sub(f"[REDACTED_{pattern_name.upper()}]", sanitized)
            else:
                sanitized = pattern.sub("[REDACTED]", sanitized)
        
        return sanitized
    
    def _sanitize_dict(self, data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """Sanitize a dictionary."""
        sanitized = {}
        
        for key, value in data.items():
            # Check if key is sensitive
            if self._is_sensitive_key(key):
                sanitized[key] = "[REDACTED]"
            else:
                # Recursively sanitize nested structures
                sanitized[key] = self.sanitize_data(value, depth + 1)
        
        return sanitized
    
    def _sanitize_list(self, data: Union[List[Any], tuple], depth: int = 0) -> Union[List[Any], tuple]:
        """Sanitize a list or tuple."""
        if isinstance(data, tuple):
            return tuple(self.sanitize_data(item, depth + 1) for item in data)
        else:
            return [self.sanitize_data(item, depth + 1) for item in data]
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key is sensitive."""
        sensitive_keywords = [
            "password", "secret", "token", "key", "auth", "credential",
            "private", "sensitive", "confidential", "session_id"
        ]
        
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in sensitive_keywords)
    
    def add_pattern(self, name: str, pattern: str) -> None:
        """
        Add a custom redaction pattern.
        
        Args:
            name: Pattern name
            pattern: Regex pattern
        """
        try:
            self.redact_patterns[name] = pattern
            self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
        except re.error:
            # Silently ignore invalid regex patterns
            pass
    
    def remove_pattern(self, name: str) -> bool:
        """
        Remove a redaction pattern.
        
        Args:
            name: Pattern name
            
        Returns:
            True if pattern was removed, False if not found
        """
        if name in self.redact_patterns:
            del self.redact_patterns[name]
            del self._compiled_patterns[name]
            return True
        return False


class SecurityValidator:
    """Security validation utilities."""
    
    def __init__(self):
        """Initialize security validator."""
        self._threat_patterns = self._get_threat_patterns()
        self._compiled_threat_patterns = self._compile_threat_patterns()
    
    def _get_threat_patterns(self) -> Dict[str, str]:
        """Get threat detection patterns."""
        return {
            "sql_injection": r"(\b(union|select|insert|update|delete|drop|alter|create)\b)",
            "xss": r"(<script|javascript:|on\w+\s*=|vbscript:)",
            "path_traversal": r"(\.\./|\.\.\\)",
            "command_injection": r"(;|\||`|\$\(|\$\{|\$\$|&&|\|\|)",
            "ldap_injection": r"(\*|\(|\)|\||&)",
            "nosql_injection": r"(\$where|\$ne|\$gt|\$lt|\$regex)",
        }
    
    def _compile_threat_patterns(self) -> Dict[str, re.Pattern]:
        """Compile threat patterns."""
        return {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self._threat_patterns.items()
        }
    
    def validate_input(self, data: Any) -> Dict[str, Any]:
        """
        Validate input for security threats.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation results
        """
        if isinstance(data, str):
            return self._validate_string(data)
        elif isinstance(data, dict):
            return self._validate_dict(data)
        elif isinstance(data, list):
            return self._validate_list(data)
        else:
            return {"valid": True, "threats": []}
    
    def _validate_string(self, text: str) -> Dict[str, Any]:
        """Validate a string for security threats."""
        threats = []
        
        for threat_name, pattern in self._compiled_threat_patterns.items():
            if pattern.search(text):
                threats.append({
                    "type": threat_name,
                    "pattern": pattern.pattern,
                    "severity": self._get_threat_severity(threat_name)
                })
        
        return {
            "valid": len(threats) == 0,
            "threats": threats
        }
    
    def _validate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a dictionary for security threats."""
        all_threats = []
        
        for key, value in data.items():
            validation = self.validate_input(value)
            if not validation["valid"]:
                all_threats.extend(validation["threats"])
        
        return {
            "valid": len(all_threats) == 0,
            "threats": all_threats
        }
    
    def _validate_list(self, data: List[Any]) -> Dict[str, Any]:
        """Validate a list for security threats."""
        all_threats = []
        
        for item in data:
            validation = self.validate_input(item)
            if not validation["valid"]:
                all_threats.extend(validation["threats"])
        
        return {
            "valid": len(all_threats) == 0,
            "threats": all_threats
        }
    
    def _get_threat_severity(self, threat_type: str) -> str:
        """Get severity level for a threat type."""
        high_severity = ["sql_injection", "command_injection", "xss"]
        medium_severity = ["path_traversal", "ldap_injection"]
        low_severity = ["nosql_injection"]
        
        if threat_type in high_severity:
            return "high"
        elif threat_type in medium_severity:
            return "medium"
        elif threat_type in low_severity:
            return "low"
        else:
            return "low"
    
    def add_threat_pattern(self, name: str, pattern: str) -> None:
        """
        Add a custom threat pattern.
        
        Args:
            name: Threat name
            pattern: Regex pattern
        """
        self._threat_patterns[name] = pattern
        self._compiled_threat_patterns[name] = re.compile(pattern, re.IGNORECASE)


class DataHasher:
    """Data hashing utilities for sensitive data."""
    
    def __init__(self, algorithm: str = "sha256"):
        """
        Initialize data hasher.
        
        Args:
            algorithm: Hashing algorithm to use
        """
        self.algorithm = algorithm
        self._hash_functions = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
        }
    
    def hash_data(self, data: str) -> str:
        """
        Hash sensitive data.
        
        Args:
            data: Data to hash
            
        Returns:
            Hashed data
        """
        if self.algorithm not in self._hash_functions:
            raise DataProtectionError(f"Unsupported hash algorithm: {self.algorithm}")
        
        hash_func = self._hash_functions[self.algorithm]
        return hash_func(data.encode('utf-8')).hexdigest()
    
    def hash_sensitive_fields(self, data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
        """
        Hash sensitive fields in a dictionary.
        
        Args:
            data: Data dictionary
            fields: List of sensitive field names
            
        Returns:
            Data with sensitive fields hashed
        """
        hashed_data = data.copy()
        
        for field in fields:
            if field in hashed_data:
                field_value = hashed_data[field]
                if isinstance(field_value, str):
                    hashed_data[field] = self.hash_data(field_value)
                elif isinstance(field_value, (dict, list)):
                    # For complex structures, hash the string representation
                    hashed_data[field] = self.hash_data(str(field_value))
                else:
                    # For other types, hash the string representation
                    hashed_data[field] = self.hash_data(str(field_value))
        
        return hashed_data
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """
        Verify a hash value.
        
        Args:
            data: Original data
            hash_value: Hash to verify
            
        Returns:
            True if hash matches, False otherwise
        """
        return self.hash_data(data) == hash_value 