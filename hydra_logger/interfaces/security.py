"""
Security Interface for Hydra-Logger

This module defines the abstract interface for security components
including data sanitization, validation, encryption, and threat detection.
It ensures consistent behavior across all security implementations.

ARCHITECTURE:
- SecurityInterface: Abstract interface for all security implementations
- Defines contract for security operations and threat detection
- Ensures consistent behavior across different security types
- Supports security monitoring and statistics

CORE FEATURES:
- Security enable/disable operations
- Security level management
- Threat detection and counting
- Security statistics and monitoring
- Security status checking

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import SecurityInterface
    from typing import Any, Dict
    
    class BasicSecurity(SecurityInterface):
        def __init__(self):
            self._enabled = False
            self._security_level = "low"
            self._threat_count = 0
            self._stats = {
                "threats_detected": 0,
                "security_violations": 0,
                "last_threat_time": None
            }
        
        def is_enabled(self) -> bool:
            return self._enabled
        
        def enable(self) -> None:
            self._enabled = True
        
        def disable(self) -> None:
            self._enabled = False
        
        def get_security_level(self) -> str:
            return self._security_level
        
        def get_threat_count(self) -> int:
            return self._threat_count
        
        def get_security_stats(self) -> Dict[str, Any]:
            return self._stats.copy()
        
        def reset_security_stats(self) -> None:
            self._stats = {
                "threats_detected": 0,
                "security_violations": 0,
                "last_threat_time": None
            }
        
        def is_secure(self) -> bool:
            return self._enabled and self._threat_count == 0

Security Usage:
    from hydra_logger.interfaces import SecurityInterface
    
    def use_security(security: SecurityInterface):
        \"\"\"Use any security that implements SecurityInterface.\"\"\"
        # Enable security
        security.enable()
        if security.is_enabled():
            print("Security enabled")
        
        # Check security level
        level = security.get_security_level()
        print(f"Security level: {level}")
        
        # Check threat count
        threats = security.get_threat_count()
        print(f"Threats detected: {threats}")
        
        # Get security stats
        stats = security.get_security_stats()
        print(f"Security stats: {stats}")
        
        # Check if secure
        if security.is_secure():
            print("System is secure")
        else:
            print("System is not secure")
        
        # Reset stats
        security.reset_security_stats()
        print("Security stats reset")
        
        # Disable security
        security.disable()
        if not security.is_enabled():
            print("Security disabled")

Security Monitoring:
    from hydra_logger.interfaces import SecurityInterface
    
    def monitor_security(security: SecurityInterface):
        \"\"\"Monitor security using the security interface.\"\"\"
        # Check if security is enabled
        if security.is_enabled():
            print("Security is enabled")
            
            # Check security level
            level = security.get_security_level()
            print(f"Current security level: {level}")
            
            # Check threat count
            threats = security.get_threat_count()
            if threats > 0:
                print(f"Warning: {threats} threats detected")
            else:
                print("No threats detected")
            
            # Get security statistics
            stats = security.get_security_stats()
            print(f"Security statistics: {stats}")
            
            # Check overall security status
            if security.is_secure():
                print("System is secure")
            else:
                print("System security compromised")
        else:
            print("Security is disabled")

Statistics Management:
    from hydra_logger.interfaces import SecurityInterface
    
    def manage_security_stats(security: SecurityInterface):
        \"\"\"Manage security statistics using the interface.\"\"\"
        # Get current stats
        stats = security.get_security_stats()
        print(f"Current stats: {stats}")
        
        # Check threat count
        threats = security.get_threat_count()
        print(f"Threat count: {threats}")
        
        # Reset stats if needed
        if threats > 100:  # Example threshold
            security.reset_security_stats()
            print("Security stats reset due to high threat count")
        
        # Check security status
        if security.is_secure():
            print("System is secure")
        else:
            print("System requires attention")

INTERFACE CONTRACTS:
- is_enabled(): Check if security is enabled
- enable(): Enable security features
- disable(): Disable security features
- get_security_level(): Get current security level
- get_threat_count(): Get count of detected threats
- get_security_stats(): Get security statistics
- reset_security_stats(): Reset security statistics
- is_secure(): Check if system is secure

ERROR HANDLING:
- All methods return boolean success indicators
- Clear error messages and status reporting
- Graceful handling of security failures
- Safe security management

BENEFITS:
- Consistent security API across implementations
- Easy testing with mock security
- Clear contracts for custom security
- Polymorphic usage without tight coupling
- Better security monitoring and threat detection
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List


class SecurityInterface(ABC):
    """
    Abstract interface for all security implementations.
    
    This interface defines the contract that all security components must implement,
    ensuring consistent behavior across different security types.
    """
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """
        Check if security is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def enable(self) -> None:
        """Enable security features."""
        raise NotImplementedError
    
    @abstractmethod
    def disable(self) -> None:
        """Disable security features."""
        raise NotImplementedError
    
    @abstractmethod
    def get_security_level(self) -> str:
        """
        Get current security level.
        
        Returns:
            Security level string
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_threat_count(self) -> int:
        """
        Get count of detected threats.
        
        Returns:
            Number of threats detected
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_security_stats(self) -> Dict[str, Any]:
        """
        Get security statistics.
        
        Returns:
            Security statistics dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def reset_security_stats(self) -> None:
        """Reset security statistics."""
        raise NotImplementedError
    
    @abstractmethod
    def is_secure(self) -> bool:
        """
        Check if system is secure.
        
        Returns:
            True if secure, False otherwise
        """
        raise NotImplementedError
