"""
Data Redaction Utility

Simple, high-performance data redaction for sensitive information.
Zero overhead when disabled, fast regex-based redaction when enabled.

FEATURES:
- Email redaction
- Phone number redaction
- API key redaction
- Credit card redaction
- SSN redaction
- Custom pattern redaction
- Performance-optimized regex compilation
"""

import re
from typing import List, Optional, Dict, Any


class DataRedaction:
    """
    Simple data redaction utility.
    
    Professional naming: DataRedaction (clear, descriptive)
    Zero overhead when disabled, high performance when enabled.
    """
    
    def __init__(self, enabled: bool = False, patterns: Optional[List[str]] = None):
        """
        Initialize data redaction.
        
        Args:
            enabled: Whether redaction is enabled
            patterns: List of patterns to redact
        """
        self.enabled = enabled
        self.patterns = patterns or []
        self._compiled_patterns: List[tuple] = []
        
        if self.enabled:
            self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        pattern_map = {
            'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED_EMAIL]'),
            'phone': (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[REDACTED_PHONE]'),
            'ssn': (r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]'),
            'credit_card': (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED_CARD]'),
            'api_key': (r'\bsk-[A-Za-z0-9]{20,}\b', '[REDACTED_API_KEY]'),
            'password': (r'\bpassword["\s]*[:=]["\s]*[^\s]+', 'password="[REDACTED]"'),
            'token': (r'\btoken["\s]*[:=]["\s]*[^\s]+', 'token="[REDACTED]"')
        }
        
        for pattern in self.patterns:
            if pattern in pattern_map:
                regex, replacement = pattern_map[pattern]
                self._compiled_patterns.append((re.compile(regex), replacement))
    
    def enable(self) -> None:
        """Enable redaction."""
        self.enabled = True
        self._compile_patterns()
    
    def disable(self) -> None:
        """Disable redaction."""
        self.enabled = False
        self._compiled_patterns.clear()
    
    def add_pattern(self, pattern: str, replacement: str = '[REDACTED]') -> None:
        """Add custom redaction pattern."""
        if self.enabled:
            self._compiled_patterns.append((re.compile(pattern), replacement))
    
    def redact(self, data: Any) -> Any:
        """
        Redact sensitive data.
        
        Args:
            data: Data to redact (string, dict, or other)
            
        Returns:
            Redacted data
        """
        if not self.enabled or not self._compiled_patterns:
            return data
        
        if isinstance(data, str):
            return self._redact_string(data)
        elif isinstance(data, dict):
            return self._redact_dict(data)
        else:
            return data
    
    def _redact_string(self, text: str) -> str:
        """Redact sensitive patterns in string."""
        result = text
        for pattern, replacement in self._compiled_patterns:
            result = pattern.sub(replacement, result)
        return result
    
    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive patterns in dictionary."""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._redact_string(value)
            elif isinstance(value, dict):
                result[key] = self._redact_dict(value)
            else:
                result[key] = value
        return result
    
    def is_enabled(self) -> bool:
        """Check if redaction is enabled."""
        return self.enabled
