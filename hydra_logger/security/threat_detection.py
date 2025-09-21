"""
Threat Detection Component for Hydra-Logger

This module provides comprehensive threat detection capabilities for security
monitoring. It detects various types of security threats including injection
attacks, XSS, path traversal, and other malicious patterns.

FEATURES:
- Multiple threat pattern detection
- SQL injection detection
- XSS (Cross-Site Scripting) detection
- Path traversal detection
- Command injection detection
- LDAP injection detection
- NoSQL injection detection
- Custom threat pattern management
- Severity level classification

THREAT TYPES:
- SQL Injection: Database injection attacks
- XSS: Cross-site scripting attacks
- Path Traversal: Directory traversal attacks
- Command Injection: Command execution attacks
- LDAP Injection: LDAP query injection
- NoSQL Injection: NoSQL database injection

USAGE:
    from hydra_logger.security import ThreatDetector
    
    # Create threat detector
    detector = ThreatDetector(enabled=True)
    
    # Detect threats in data
    threats = detector.detect_threats("SELECT * FROM users WHERE id = 1")
    
    # Process detected threats
    for threat in threats:
        print(f"Threat: {threat['type']} - Severity: {threat['severity']}")
    
    # Add custom threat pattern
    detector.add_threat_pattern("custom_attack", r"malicious_pattern")
    
    # Get threat statistics
    stats = detector.get_threat_stats()
    print(f"Total threats detected: {stats['total_threats']}")
"""
import re
from typing import Any, Dict, List, Optional
from ..interfaces.security import SecurityInterface


class ThreatDetector(SecurityInterface):
    """Real threat detection component for security monitoring."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        self._threat_count = 0
        self._threat_patterns = self._get_threat_patterns()
        self._compiled_patterns = self._compile_patterns()
    
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
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile threat patterns for performance."""
        return {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self._threat_patterns.items()
        }
    
    def detect_threats(self, data: Any) -> List[Dict[str, Any]]:
        """Detect security threats in data."""
        if not self._enabled:
            return []
        
        threats = []
        if isinstance(data, str):
            threats.extend(self._detect_string_threats(data))
        elif isinstance(data, dict):
            threats.extend(self._detect_dict_threats(data))
        elif isinstance(data, list):
            threats.extend(self._detect_list_threats(data))
        
        self._threat_count += len(threats)
        return threats
    
    def _detect_string_threats(self, text: str) -> List[Dict[str, Any]]:
        """Detect threats in a string."""
        threats = []
        for threat_name, pattern in self._compiled_patterns.items():
            if pattern.search(text):
                threats.append({
                    "type": threat_name,
                    "pattern": pattern.pattern,
                    "severity": self._get_threat_severity(threat_name),
                    "sample": text[:100] + "..." if len(text) > 100 else text
                })
        return threats
    
    def _detect_dict_threats(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect threats in a dictionary."""
        threats = []
        for value in data.values():
            threats.extend(self.detect_threats(value))
        return threats
    
    def _detect_list_threats(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Detect threats in a list."""
        threats = []
        for item in data:
            threats.extend(self.detect_threats(item))
        return threats
    
    def _get_threat_severity(self, threat_type: str) -> str:
        """Get severity level for a threat type."""
        high_severity = ["sql_injection", "command_injection", "xss"]
        medium_severity = ["path_traversal", "ldap_injection"]
        low_severity = ["nosql_injection"]
        
        if threat_type in high_severity:
            return "high"
        elif threat_type in medium_severity:
            return "medium"
        else:
            return "low"
    
    def add_threat_pattern(self, name: str, pattern: str) -> bool:
        """Add a custom threat pattern."""
        try:
            self._threat_patterns[name] = pattern
            self._compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            return True
        except re.error:
            return False
    
    def get_threat_stats(self) -> Dict[str, Any]:
        """Get threat detection statistics."""
        return {
            "total_threats": self._threat_count,
            "patterns": list(self._threat_patterns.keys()),
            "enabled": self._enabled
        }
    
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
        return self._threat_count
    
    def get_security_stats(self) -> Dict[str, Any]:
        return self.get_threat_stats()
    
    def reset_security_stats(self) -> None:
        self._threat_count = 0
    
    def is_secure(self) -> bool:
        return self._enabled and self._initialized
