"""
Performance-Optimized Security Levels for Hydra-Logger

This module provides conditional security execution based on performance requirements.
Security features can be completely bypassed when disabled for maximum performance,
or selectively enabled based on security level requirements.

FEATURES:
- Configurable security performance levels
- Conditional security feature execution
- Performance metrics and monitoring
- Decorator-based conditional execution
- Fast security engine implementation
- Global security profile management

SECURITY LEVELS:
- DISABLED: Zero overhead - no security processing
- BASIC: Minimal overhead - essential security only
- STANDARD: Balanced - common security features
- HIGH: Enhanced - comprehensive security
- MAXIMUM: Full security - maximum protection

USAGE:
    from hydra_logger.security.performance_levels import (
        SecurityLevel, SecurityPerformanceProfile, FastSecurityEngine
    )
    
    # Create security profile
    profile = SecurityPerformanceProfile(SecurityLevel.STANDARD)
    
    # Check if feature is enabled
    if profile.is_feature_enabled('pii_detection'):
        # PII detection is enabled
        pass
    
    # Create fast security engine
    engine = FastSecurityEngine(SecurityLevel.BASIC)
    engine.initialize()
    
    # Use conditional security methods
    has_pii = engine.detect_pii("sensitive data")
    sanitized = engine.sanitize_data("data")
    
    # Get performance metrics
    metrics = engine.get_performance_metrics()
    print(f"Skip rate: {metrics['skip_rate']:.2%}")
"""

from enum import Enum
from typing import Optional, Dict, Any, Callable
from functools import wraps
import time


class SecurityLevel(Enum):
    """Security performance levels from fastest to most secure."""
    DISABLED = "disabled"        # Zero overhead - no security processing
    BASIC = "basic"             # Minimal overhead - essential security only
    STANDARD = "standard"       # Balanced - common security features
    HIGH = "high"              # Enhanced - comprehensive security
    MAXIMUM = "maximum"        # Full security - maximum protection


class SecurityPerformanceProfile:
    """Performance profile for security features."""
    
    def __init__(self, level: SecurityLevel = SecurityLevel.DISABLED):
        self.level = level
        self._enabled_features = self._get_enabled_features()
        self._performance_metrics = {
            'calls_skipped': 0,
            'calls_processed': 0,
            'total_time_saved': 0.0,
            'last_reset': time.time()
        }
    
    def _get_enabled_features(self) -> Dict[str, bool]:
        """Get enabled features based on security level."""
        features = {
            'pii_detection': False,
            'data_sanitization': False,
            'encryption': False,
            'threat_detection': False,
            'access_control': False,
            'audit_logging': False,
            'compliance_checking': False,
            'data_redaction': False,
            'hash_validation': False,
            'crypto_operations': False
        }
        
        if self.level == SecurityLevel.DISABLED:
            return features
        elif self.level == SecurityLevel.BASIC:
            features.update({
                'pii_detection': True,
                'data_sanitization': True
            })
        elif self.level == SecurityLevel.STANDARD:
            features.update({
                'pii_detection': True,
                'data_sanitization': True,
                'threat_detection': True,
                'access_control': True
            })
        elif self.level == SecurityLevel.HIGH:
            features.update({
                'pii_detection': True,
                'data_sanitization': True,
                'threat_detection': True,
                'access_control': True,
                'encryption': True,
                'audit_logging': True,
                'compliance_checking': True
            })
        elif self.level == SecurityLevel.MAXIMUM:
            features.update({
                'pii_detection': True,
                'data_sanitization': True,
                'threat_detection': True,
                'access_control': True,
                'encryption': True,
                'audit_logging': True,
                'compliance_checking': True,
                'data_redaction': True,
                'hash_validation': True,
                'crypto_operations': True
            })
        
        return features
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific security feature is enabled."""
        return self._enabled_features.get(feature, False)
    
    def record_skipped_call(self, time_saved: float = 0.0):
        """Record a skipped security call for performance metrics."""
        self._performance_metrics['calls_skipped'] += 1
        self._performance_metrics['total_time_saved'] += time_saved
    
    def record_processed_call(self):
        """Record a processed security call."""
        self._performance_metrics['calls_processed'] += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this security profile."""
        total_calls = (self._performance_metrics['calls_skipped'] + 
                      self._performance_metrics['calls_processed'])
        
        return {
            'security_level': self.level.value,
            'total_calls': total_calls,
            'calls_skipped': self._performance_metrics['calls_skipped'],
            'calls_processed': self._performance_metrics['calls_processed'],
            'skip_rate': (self._performance_metrics['calls_skipped'] / total_calls 
                         if total_calls > 0 else 0.0),
            'time_saved_ms': self._performance_metrics['total_time_saved'] * 1000,
            'uptime_seconds': time.time() - self._performance_metrics['last_reset']
        }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self._performance_metrics = {
            'calls_skipped': 0,
            'calls_processed': 0,
            'total_time_saved': 0.0,
            'last_reset': time.time()
        }


def conditional_security(feature: str, fallback_value: Any = None):
    """
    Decorator for conditional security execution.
    
    Args:
        feature: Security feature name to check
        fallback_value: Value to return when feature is disabled
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check if security is enabled and feature is available
            if (hasattr(self, '_security_profile') and 
                self._security_profile and 
                self._security_profile.is_feature_enabled(feature)):
                
                # Record processed call
                self._security_profile.record_processed_call()
                return func(self, *args, **kwargs)
            else:
                # Record skipped call with estimated time saved
                if hasattr(self, '_security_profile') and self._security_profile:
                    self._security_profile.record_skipped_call(0.001)  # 1ms saved per call
                return fallback_value
        
        return wrapper
    return decorator


class FastSecurityEngine:
    """High-performance security engine with conditional execution."""
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.DISABLED):
        self._security_profile = SecurityPerformanceProfile(security_level)
        self._initialized = False
    
    def initialize(self):
        """Initialize security engine only if needed."""
        if self._security_profile.level != SecurityLevel.DISABLED:
            self._initialized = True
        else:
            self._initialized = False
    
    @conditional_security('pii_detection', False)
    def detect_pii(self, data: str) -> bool:
        """Detect PII in data - only runs if PII detection is enabled."""
        # This would contain actual PII detection logic
        # For now, return False as placeholder
        return False
    
    @conditional_security('data_sanitization', None)
    def sanitize_data(self, data: str) -> str:
        """Sanitize data - only runs if sanitization is enabled."""
        # This would contain actual sanitization logic
        # For now, return data as-is
        return data
    
    @conditional_security('threat_detection', False)
    def detect_threats(self, data: str) -> bool:
        """Detect security threats - only runs if threat detection is enabled."""
        # This would contain actual threat detection logic
        # For now, return False as placeholder
        return False
    
    @conditional_security('encryption', None)
    def encrypt_data(self, data: str) -> str:
        """Encrypt data - only runs if encryption is enabled."""
        # This would contain actual encryption logic
        # For now, return data as-is
        return data
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this security engine."""
        return self._security_profile.get_performance_metrics()
    
    def is_initialized(self) -> bool:
        """Check if security engine is initialized."""
        return self._initialized


# Global security profile for easy access
_global_security_profile: Optional[SecurityPerformanceProfile] = None


def set_global_security_level(level: SecurityLevel):
    """Set global security level for all loggers."""
    global _global_security_profile
    _global_security_profile = SecurityPerformanceProfile(level)


def get_global_security_profile() -> Optional[SecurityPerformanceProfile]:
    """Get global security profile."""
    return _global_security_profile


def create_fast_security_engine(level: SecurityLevel = SecurityLevel.DISABLED) -> FastSecurityEngine:
    """Create a fast security engine with specified level."""
    engine = FastSecurityEngine(level)
    engine.initialize()
    return engine
