"""
Extension Base Classes for Hydra-Logger

Professional, performance-focused extension system with zero overhead when disabled.
Users have full control over all extensions, formats, and destinations.

ARCHITECTURE:
- ExtensionBase: Abstract base class for all extensions
- SecurityExtension: Data redaction and sanitization
- FormattingExtension: Message formatting and enhancement
- PerformanceExtension: Performance monitoring and optimization

NAMING CONVENTIONS:
- All classes end with descriptive suffixes: *Extension, *Manager, *Utility
- Professional, clear naming - no "simple" or generic terms
- Consistent with project standards
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import re


class ExtensionBase(ABC):
    """
    Base class for all Hydra-Logger extensions.
    
    Professional naming: ExtensionBase (clear, descriptive)
    Zero overhead when disabled, high performance when enabled.
    """
    
    def __init__(self, enabled: bool = False, **config):
        """
        Initialize extension.
        
        Args:
            enabled: Whether extension is enabled
            **config: Extension-specific configuration
        """
        self.enabled = enabled
        self.config = config or {}
        self._setup()
    
    def _setup(self) -> None:
        """Setup extension - override in subclasses."""
        pass
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data - override in subclasses."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if extension is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable extension."""
        self.enabled = True
        self._setup()
    
    def disable(self) -> None:
        """Disable extension."""
        self.enabled = False
    
    def get_config(self) -> Dict[str, Any]:
        """Get extension configuration."""
        return self.config.copy()
    
    def update_config(self, **updates) -> None:
        """Update extension configuration."""
        self.config.update(updates)
        if self.enabled:
            self._setup()


class SecurityExtension(ExtensionBase):
    """
    Security extension for data redaction and sanitization.
    
    Professional naming: SecurityExtension (clear, descriptive)
    User-controllable patterns and redaction rules.
    """
    
    def __init__(self, enabled: bool = False, patterns: Optional[List[str]] = None, **config):
        """
        Initialize security extension.
        
        Args:
            enabled: Whether security is enabled
            patterns: List of patterns to redact
            **config: Additional configuration
        """
        self.patterns = patterns or ['email', 'phone', 'ssn', 'credit_card', 'api_key']
        self.redaction_enabled = config.get('redaction_enabled', True)
        self.sanitization_enabled = config.get('sanitization_enabled', True)
        super().__init__(enabled, **config)
    
    def _setup(self) -> None:
        """Setup redaction patterns."""
        if not self.enabled:
            return
        
        # Compile patterns for performance
        self._compiled_patterns = []
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
    
    def process(self, data: Any) -> Any:
        """Process data through security extension."""
        if not self.enabled:
            return data
        
        if isinstance(data, str):
            return self._process_string(data)
        elif isinstance(data, dict):
            return self._process_dict(data)
        else:
            return data
    
    def _process_string(self, text: str) -> str:
        """Process string data."""
        result = text
        
        # Apply redaction if enabled
        if self.redaction_enabled and hasattr(self, '_compiled_patterns'):
            for pattern, replacement in self._compiled_patterns:
                result = pattern.sub(replacement, result)
        
        # Apply sanitization if enabled
        if self.sanitization_enabled:
            result = self._sanitize_text(result)
        
        return result
    
    def _process_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dictionary data."""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._process_string(value)
            elif isinstance(value, dict):
                result[key] = self._process_dict(value)
            else:
                result[key] = value
        return result
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text data."""
        # Remove potential XSS patterns
        text = re.sub(r'<script[^>]*>.*?</script>', '[SANITIZED_SCRIPT]', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '[SANITIZED_JS]', text, flags=re.IGNORECASE)
        return text


class FormattingExtension(ExtensionBase):
    """
    Formatting extension for message enhancement.
    
    Professional naming: FormattingExtension (clear, descriptive)
    User-controllable formatting options.
    """
    
    def __init__(self, enabled: bool = False, **config):
        """Initialize formatting extension."""
        self.add_timestamp = config.get('add_timestamp', False)
        self.add_context = config.get('add_context', False)
        self.timestamp_format = config.get('timestamp_format', '%Y-%m-%d %H:%M:%S')
        super().__init__(enabled, **config)
    
    def process(self, data: Any) -> Any:
        """Process data through formatting extension."""
        if not self.enabled:
            return data
        
        if isinstance(data, str):
            return self._format_string(data)
        elif isinstance(data, dict):
            return self._format_dict(data)
        else:
            return data
    
    def _format_string(self, text: str) -> str:
        """Format string message."""
        if self.add_timestamp:
            from datetime import datetime
            timestamp = datetime.now().strftime(self.timestamp_format)
            text = f"[{timestamp}] {text}"
        return text
    
    def _format_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format dictionary data."""
        if self.add_context and 'message' in data:
            data['context'] = data.get('context', {})
            data['context']['formatted'] = True
            data['context']['timestamp'] = data.get('timestamp', None)
        return data


class PerformanceExtension(ExtensionBase):
    """
    Performance extension for monitoring and optimization.
    
    Professional naming: PerformanceExtension (clear, descriptive)
    User-controllable performance monitoring.
    """
    
    def __init__(self, enabled: bool = False, **config):
        """Initialize performance extension."""
        self.monitor_latency = config.get('monitor_latency', True)
        self.monitor_memory = config.get('monitor_memory', False)
        self.sample_rate = config.get('sample_rate', 100)  # Every N operations
        self._operation_count = 0
        super().__init__(enabled, **config)
    
    def process(self, data: Any) -> Any:
        """Process data through performance extension."""
        if not self.enabled:
            return data
        
        self._operation_count += 1
        
        # Sample performance data
        if self._operation_count % self.sample_rate == 0:
            self._collect_metrics()
        
        return data
    
    def _collect_metrics(self) -> None:
        """Collect performance metrics."""
        if self.monitor_latency:
            # Monitor operation latency
            pass
        
        if self.monitor_memory:
            # Monitor memory usage
            import psutil
            memory_info = psutil.Process().memory_info()
            # Store or log memory metrics
            pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            'operations_processed': self._operation_count,
            'sample_rate': self.sample_rate,
            'enabled': self.enabled
        }
