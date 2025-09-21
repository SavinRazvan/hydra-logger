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
import threading
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import Future
from ..interfaces.security import SecurityInterface
from .background_processing import (
    BackgroundSecurityProcessor, 
    SecurityOperationType, 
    get_background_processor
)


class DataRedaction(SecurityInterface):
    """Real data redaction component for sensitive information protection."""
    
    def __init__(self, enabled: bool = True, patterns: Optional[Dict[str, str]] = None, 
                 use_background_processing: bool = True):
        self._enabled = enabled
        self._initialized = True
        self._redaction_count = 0
        self._patterns = patterns or self._get_default_patterns()
        self._compiled_patterns = self._compile_patterns()
        
        # Background processing configuration
        self._use_background_processing = use_background_processing and enabled
        self._background_processor = get_background_processor()
        
        # Statistics
        self._stats = {
            'synchronous_redactions': 0,
            'background_redactions': 0,
            'total_redaction_time': 0.0,
            'average_redaction_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_reset': time.time()
        }
        
        # Cache for redaction results
        self._redaction_cache = {}
        self._cache_max_size = 1000
        self._cache_ttl = 300.0  # 5 minutes
        
        # Thread lock for thread-safe operations
        self._lock = threading.RLock()
    
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
    
    def redact_data(self, data: Any, fields: Optional[List[str]] = None, 
                   use_background: bool = None) -> Union[Any, Future]:
        """
        Redact sensitive data with optional background processing.
        
        Args:
            data: Data to redact
            fields: Specific fields to redact (if None, redacts all patterns)
            use_background: Whether to use background processing
            
        Returns:
            Redacted data (synchronous) or Future (asynchronous)
        """
        if not self._enabled:
            return data
        
        # Determine if we should use background processing
        should_use_background = (
            use_background if use_background is not None 
            else self._use_background_processing
        )
        
        if should_use_background:
            return self._redact_data_background(data, fields)
        else:
            return self._redact_data_sync(data, fields)
    
    def _redact_data_sync(self, data: Any, fields: Optional[List[str]] = None) -> Any:
        """Synchronous data redaction."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(data, fields)
            if cache_key in self._redaction_cache:
                cached_result = self._redaction_cache[cache_key]
                if time.time() - cached_result['timestamp'] < self._cache_ttl:
                    with self._lock:
                        self._stats['cache_hits'] += 1
                    return cached_result['result']
            
            # Perform redaction
            if fields:
                result = self._redact_specific_fields(data, fields)
            else:
                result = self._redact_all_patterns(data)
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Update statistics
            processing_time = time.time() - start_time
            with self._lock:
                self._stats['synchronous_redactions'] += 1
                self._stats['total_redaction_time'] += processing_time
                self._stats['average_redaction_time'] = (
                    self._stats['total_redaction_time'] / 
                    (self._stats['synchronous_redactions'] + self._stats['background_redactions'])
                )
                self._stats['cache_misses'] += 1
            
            return result
            
        except Exception as e:
            # Log error and return original data
            import logging
            logging.error(f"Error in synchronous redaction: {e}")
            return data
    
    def _redact_data_background(self, data: Any, fields: Optional[List[str]] = None) -> Future:
        """Asynchronous data redaction using background processing."""
        def callback(result):
            """Callback for background processing result."""
            with self._lock:
                self._stats['background_redactions'] += 1
                self._stats['total_redaction_time'] += result.processing_time
                self._stats['average_redaction_time'] = (
                    self._stats['total_redaction_time'] / 
                    (self._stats['synchronous_redactions'] + self._stats['background_redactions'])
                )
        
        # Submit task to background processor
        task_id = self._background_processor.submit_task(
            operation_type=SecurityOperationType.PII_DETECTION,
            data=data,
            callback=callback,
            priority=1  # High priority for redaction
        )
        
        # Return a future that will be resolved when processing is complete
        future = Future()
        
        def result_callback(result):
            if result.success:
                future.set_result(result.result)
            else:
                future.set_exception(Exception(result.error))
        
        return future
    
    def _get_cache_key(self, data: Any, fields: Optional[List[str]] = None) -> str:
        """Generate cache key for data and fields."""
        import hashlib
        key_data = f"{str(data)}:{str(fields)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: Any):
        """Cache redaction result."""
        with self._lock:
            if len(self._redaction_cache) >= self._cache_max_size:
                # Remove oldest entries
                oldest_key = min(self._redaction_cache.keys(),
                               key=lambda k: self._redaction_cache[k]['timestamp'])
                del self._redaction_cache[oldest_key]
            
            self._redaction_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get redaction statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats['redaction_count'] = self._redaction_count
            stats['cache_size'] = len(self._redaction_cache)
            stats['background_processor_stats'] = self._background_processor.get_stats()
            return stats
    
    def reset_stats(self):
        """Reset redaction statistics."""
        with self._lock:
            self._stats = {
                'synchronous_redactions': 0,
                'background_redactions': 0,
                'total_redaction_time': 0.0,
                'average_redaction_time': 0.0,
                'cache_hits': 0,
                'cache_misses': 0,
                'last_reset': time.time()
            }
            self._redaction_count = 0
            self._redaction_cache.clear()
            self._background_processor.reset_stats()
    
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
        return self._redaction_count
    
    def get_security_stats(self) -> Dict[str, Any]:
        return self.get_redaction_stats()
    
    def reset_security_stats(self) -> None:
        self.reset_stats()
    
    def is_secure(self) -> bool:
        return self._enabled and self._initialized
