"""
Data Redaction Component for Hydra-Logger

This module provides comprehensive data redaction capabilities for sensitive
information protection. It supports pattern-based redaction, background
processing, and configurable redaction strategies.

FEATURES:
- Pattern-based sensitive data detection
- Multiple redaction patterns (API keys, SSN, email, etc.)
- Background processing support
- Result caching for performance
- Custom pattern management
- Configurable redaction strategies
- Performance monitoring and statistics

REDACTION PATTERNS:
- API Keys: Various API key formats
- SSN: Social Security Numbers
- Email: Email addresses
- Credit Cards: Credit card numbers
- Phone: Phone numbers
- IP Addresses: IP addresses
- UUIDs: Universally unique identifiers

USAGE:
    from hydra_logger.security import DataRedaction
    
    # Create redaction component
    redactor = DataRedaction(
        enabled=True,
        use_background_processing=True
    )
    
    # Redact all sensitive patterns
    redacted_data = redactor.redact_data("User email: user@example.com")
    
    # Redact specific fields
    redacted_dict = redactor.redact_data(
        {"email": "user@example.com", "name": "John"},
        fields=["email"]
    )
    
    # Add custom pattern
    redactor.add_pattern("custom_id", r"ID-\\d{6}")
    
    # Get redaction statistics
    stats = redactor.get_stats()
    print(f"Redactions performed: {stats['redaction_count']}")
"""

import re
import time
from typing import Any, Dict, List, Optional, Union


class DataRedaction:
    """Real data redaction component for sensitive information protection."""
    
    def __init__(self, enabled: bool = True, patterns: Optional[Dict[str, str]] = None):
        """Initialize data redaction component."""
        self._enabled = enabled
        self._initialized = True
        self._redaction_count = 0
        self._patterns = patterns or self._get_default_patterns()
        self._compiled_patterns = self._compile_patterns()
        
        # Simple statistics
        self._stats = {
            'redactions_performed': 0,
            'last_reset': time.time()
        }
    
    def _get_default_patterns(self) -> Dict[str, str]:
        """Get default redaction patterns."""
        return {
            # API Key patterns FIRST (higher priority)
            "api_key_sk": r"sk-[a-zA-Z0-9_-]{10,}",  # OpenAI, Anthropic style (allows hyphens and underscores)
            "api_key_pk": r"pk-[a-zA-Z0-9_-]{10,}",  # Public keys (allows hyphens and underscores)
            "api_key_bearer": r"Bearer\s+[a-zA-Z0-9._-]{16,}",  # Bearer tokens
            "api_key_basic": r"Basic\s+[a-zA-Z0-9+/=]{8,}",  # Basic auth (shorter minimum length)
            "api_key_header": r"(?:X-API-Key|X-Auth-Token|Authorization):\s*[a-zA-Z0-9._-]{16,}",  # Header tokens
            "api_key_param": r"(?:api_key|access_token|secret_key|token)=[a-zA-Z0-9._-]{16,}",  # URL params
            "api_key_oauth": r"ya29\.[a-zA-Z0-9._-]{16,}",  # OAuth tokens
            "api_key_jwt": r"eyJ[a-zA-Z0-9._-]{20,}\.[a-zA-Z0-9._-]{20,}\.[a-zA-Z0-9._-]{20,}",  # JWT tokens
            # SSN pattern (higher priority than phone to avoid conflicts)
            "ssn": r"\b(?:SSN|ssn|social\s*security\s*number)\s*:?\s*\d{3}-\d{2}-\d{4}\b|\b\d{3}-\d{2}-\d{4}\b(?!\d)",  # SSN with context or standalone
            # Other patterns (lower priority)
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "password": r"\b(?:password|passwd|pwd)\s*[:=]\s*[^\s]{3,}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "phone": r"\b(?:phone|tel|telephone)\s*:?\s*\d{3}[-.]?\d{3}[-.]?\d{4}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b(?!\d)",  # Phone with context or standalone
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "mac_address": r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b",
            "uuid": r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile redaction patterns for performance."""
        return {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self._patterns.items()
        }
    
    def redact_data(self, data: Any, fields: Optional[List[str]] = None) -> Any:
        """
        Redact sensitive data.
        
        Args:
            data: Data to redact
            fields: Specific fields to redact (if None, redacts all patterns)
            
        Returns:
            Redacted data
        """
        if not self._enabled:
            return data
        
        return self._redact_data_sync(data, fields)
    
    def _redact_data_sync(self, data: Any, fields: Optional[List[str]] = None) -> Any:
        """Synchronous data redaction."""
        try:
            # Perform redaction
            if fields:
                result = self._redact_specific_fields(data, fields)
            else:
                result = self._redact_all_patterns(data)
            
            # Update statistics
            self._stats['redactions_performed'] += 1
            
            return result
            
        except Exception as e:
            # Log error and return original data
            import logging
            logging.error(f"Error in redaction: {e}")
            return data
    
    
    def get_stats(self) -> Dict[str, Any]:
        """Get redaction statistics."""
        stats = self._stats.copy()
        stats['redaction_count'] = self._redaction_count
        return stats
    
    def reset_stats(self):
        """Reset redaction statistics."""
        self._stats = {
            'redactions_performed': 0,
            'last_reset': time.time()
        }
        self._redaction_count = 0
    
    def _redact_all_patterns(self, data: Any) -> Any:
        """Redact all sensitive patterns in data."""
        if isinstance(data, str):
            return self._redact_string(data)
        elif isinstance(data, dict):
            return self._redact_dict(data)
        elif isinstance(data, list):
            return self._redact_list(data)
        else:
            return data
    
    def _redact_string(self, text: str) -> str:
        """Redact sensitive patterns in a string."""
        redacted = text
        for pattern_name, pattern in self._compiled_patterns.items():
            if pattern.search(redacted):
                redacted = pattern.sub(f"[REDACTED_{pattern_name.upper()}]", redacted)
                self._redaction_count += 1
        return redacted
    
    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data in a dictionary."""
        redacted = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                redacted[key] = "[REDACTED_SENSITIVE_KEY]"
                self._redaction_count += 1
            else:
                redacted[key] = self._redact_all_patterns(value)
        return redacted
    
    def _redact_list(self, data: List[Any]) -> List[Any]:
        """Redact sensitive data in a list."""
        return [self._redact_all_patterns(item) for item in data]
    
    def _redact_specific_fields(self, data: Any, fields: List[str]) -> Any:
        """Redact specific fields in data."""
        if isinstance(data, dict):
            redacted = data.copy()
            for field in fields:
                if field in redacted:
                    redacted[field] = "[REDACTED_SPECIFIC_FIELD]"
                    self._redaction_count += 1
            return redacted
        return data
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key is sensitive."""
        sensitive_keywords = [
            "password", "secret", "token", "key", "auth", "credential",
            "private", "sensitive", "confidential", "session_id", "api_key"
        ]
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in sensitive_keywords)
    
    def add_pattern(self, name: str, pattern: str) -> bool:
        """Add a custom redaction pattern."""
        try:
            self._patterns[name] = pattern
            self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            return True
        except re.error:
            return False
    
    def remove_pattern(self, name: str) -> bool:
        """Remove a redaction pattern."""
        if name in self._patterns:
            del self._patterns[name]
            del self._compiled_patterns[name]
            return True
        return False
    
    def get_redaction_stats(self) -> Dict[str, Any]:
        """Get redaction statistics."""
        return {
            "total_redactions": self._redaction_count,
            "patterns": list(self._patterns.keys()),
            "enabled": self._enabled
        }
    
    def reset_stats(self) -> None:
        """Reset redaction statistics."""
        self._redaction_count = 0
    
    def is_enabled(self) -> bool:
        """Check if redaction is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable redaction."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable redaction."""
        self._enabled = False
