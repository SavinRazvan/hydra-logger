"""
Security Validation Component for Hydra-Logger

This module provides comprehensive input validation and threat detection
capabilities to ensure secure logging operations. It includes multiple
validation levels, context-specific validation, and extensive threat detection.

FEATURES:
- Comprehensive input validation
- Multiple threat pattern detection
- Context-specific validation (file paths, SQL, URLs)
- Configurable security levels (basic, standard, strict)
- Custom threat pattern management
- Validation statistics and monitoring
- Input size and depth limits

THREAT DETECTION:
- SQL Injection: Database injection patterns
- XSS: Cross-site scripting patterns
- Path Traversal: Directory traversal patterns
- Command Injection: Command execution patterns
- LDAP Injection: LDAP query injection patterns

VALIDATION CONTEXTS:
- General: Basic input validation
- File Path: File path specific validation
- SQL: SQL query validation
- URL: URL validation

USAGE:
    from hydra_logger.security import SecurityValidator
    
    # Create validator with standard security
    validator = SecurityValidator(
        enabled=True,
        security_level="standard"
    )
    
    # Validate input data
    result = validator.validate_input(
        "SELECT * FROM users",
        context="sql"
    )
    
    # Check validation result
    if result['valid']:
        print("Input is valid")
    else:
        print(f"Threats: {result['threats']}")
        print(f"Warnings: {result['warnings']}")
    
    # Add custom threat pattern
    validator.add_threat_pattern("custom", r"malicious_pattern")
    
    # Get validation statistics
    stats = validator.get_security_stats()
    print(f"Inputs validated: {stats['inputs_validated']}")
"""

import re
import json
from typing import Any, Dict, List, Optional, Union


class SecurityValidator:
    """
    Professional security validator for input validation and threat detection.
    
    Features:
    - Input validation with configurable rules
    - Threat pattern detection
    - SQL injection prevention
    - XSS protection
    - Path traversal prevention
    """
    
    def __init__(self, enabled: bool = True, security_level: str = "standard"):
        """
        Initialize security validator.
        
        Args:
            enabled: Whether validation is enabled
            security_level: Security level (basic, standard, strict)
        """
        self._enabled = enabled
        self._security_level = security_level
        self._initialized = False
        
        # Threat patterns
        self._threat_patterns = {
            'sql_injection': [
                r'(\b(union|select|insert|update|delete|drop|create|alter)\b)',
                r'(\b(exec|execute|execsql)\b)',
                r'(\b(script|javascript|vbscript)\b)',
                r'(\b(onload|onerror|onclick)\b)',
            ],
            'xss': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'on\w+\s*=',
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'%2e%2e%2f',
                r'%2e%2e%5c',
            ],
            'command_injection': [
                r'[;&|`$]',
                r'\b(cmd|powershell|bash|sh)\b',
                r'(\$\(|`)',
            ],
            'ldap_injection': [
                r'[()&|!]',
                r'\b(uid|cn|ou|dc)\b',
            ]
        }
        
        # Compile patterns for performance
        self._compiled_threats = {}
        for category, patterns in self._threat_patterns.items():
            self._compiled_threats[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Validation rules
        self._validation_rules = {
            'max_string_length': 10000,
            'max_dict_depth': 10,
            'max_list_length': 1000,
            'allowed_file_extensions': {'.log', '.txt', '.json', '.csv'},
            'blocked_characters': {'\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07'},
        }
        
        # Security statistics
        self._security_stats = {
            'inputs_validated': 0,
            'threats_detected': 0,
            'validation_errors': 0,
            'blocked_inputs': 0,
            'errors': 0
        }
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the validator."""
        try:
            # Validate security level
            if self._security_level not in ['basic', 'standard', 'strict']:
                self._security_level = 'standard'
            
            # Add additional patterns for strict mode
            if self._security_level == 'strict':
                self._add_strict_patterns()
            
            self._initialized = True
            
        except Exception as e:
            self._security_stats['errors'] += 1
            raise RuntimeError(f"Failed to initialize SecurityValidator: {e}")
    
    def _add_strict_patterns(self) -> None:
        """Add additional patterns for strict security mode."""
        strict_patterns = {
            'advanced_xss': [
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>',
                r'<form[^>]*>',
            ],
            'advanced_sql': [
                r'(\b(declare|begin|end|goto|label)\b)',
                r'(\b(waitfor|delay|sleep)\b)',
            ],
            'file_inclusion': [
                r'include\s*\([^)]*\)',
                r'require\s*\([^)]*\)',
                r'import\s*\([^)]*\)',
            ]
        }
        
        for category, patterns in strict_patterns.items():
            self._threat_patterns[category] = patterns
            self._compiled_threats[category] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
    
    def validate_input(self, data: Any, context: str = "general") -> Dict[str, Any]:
        """
        Validate input data for security threats.
        
        Args:
            data: Data to validate
            context: Validation context (general, file_path, sql, etc.)
            
        Returns:
            Validation result dictionary
        """
        if not self._enabled or not self._initialized:
            return {'valid': True, 'threats': [], 'warnings': []}
        
        try:
            self._security_stats['inputs_validated'] += 1
            
            result = {
                'valid': True,
                'threats': [],
                'warnings': [],
                'context': context
            }
            
            # Basic validation
            basic_validation = self._basic_validation(data)
            if not basic_validation['valid']:
                result['valid'] = False
                result['warnings'].extend(basic_validation['warnings'])
            
            # Threat detection
            threats = self._detect_threats(data, context)
            if threats:
                result['valid'] = False
                result['threats'] = threats
                self._security_stats['threats_detected'] += len(threats)
                self._security_stats['blocked_inputs'] += 1
            
            # Context-specific validation
            context_validation = self._context_specific_validation(data, context)
            if not context_validation['valid']:
                result['valid'] = False
                result['warnings'].extend(context_validation['warnings'])
            
            return result
            
        except Exception as e:
            self._security_stats['errors'] += 1
            return {
                'valid': False,
                'threats': [],
                'warnings': [f'Validation error: {str(e)}'],
                'context': context
            }
    
    def _basic_validation(self, data: Any) -> Dict[str, Any]:
        """Perform basic input validation."""
        result = {'valid': True, 'warnings': []}
        
        if isinstance(data, str):
            if len(data) > self._validation_rules['max_string_length']:
                result['valid'] = False
                result['warnings'].append(f'String too long: {len(data)} > {self._validation_rules["max_string_length"]}')
            
            # Check for blocked characters
            for char in self._validation_rules['blocked_characters']:
                if char in data:
                    result['valid'] = False
                    result['warnings'].append(f'Blocked character detected: {repr(char)}')
        
        elif isinstance(data, dict):
            if self._get_dict_depth(data) > self._validation_rules['max_dict_depth']:
                result['valid'] = False
                result['warnings'].append(f'Dictionary too deep: {self._get_dict_depth(data)} > {self._validation_rules["max_dict_depth"]}')
        
        elif isinstance(data, list):
            if len(data) > self._validation_rules['max_list_length']:
                result['valid'] = False
                result['warnings'].append(f'List too long: {len(data)} > {self._validation_rules["max_list_length"]}')
        
        return result
    
    def _get_dict_depth(self, data: Dict[str, Any], current_depth: int = 0) -> int:
        """Get the maximum depth of a nested dictionary."""
        if not isinstance(data, dict) or current_depth > self._validation_rules['max_dict_depth']:
            return current_depth
        
        max_depth = current_depth
        for value in data.values():
            if isinstance(value, dict):
                depth = self._get_dict_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _detect_threats(self, data: Any, context: str) -> List[Dict[str, Any]]:
        """Detect security threats in data."""
        threats = []
        
        if isinstance(data, str):
            threats.extend(self._detect_string_threats(data, context))
        elif isinstance(data, dict):
            threats.extend(self._detect_dict_threats(data, context))
        elif isinstance(data, list):
            threats.extend(self._detect_list_threats(data, context))
        
        return threats
    
    def _detect_string_threats(self, data: str, context: str) -> List[Dict[str, Any]]:
        """Detect threats in string data."""
        threats = []
        
        for category, patterns in self._compiled_threats.items():
            for pattern in patterns:
                if pattern.search(data):
                    threats.append({
                        'type': category,
                        'pattern': pattern.pattern,
                        'context': context,
                        'severity': 'high' if category in ['sql_injection', 'command_injection'] else 'medium'
                    })
        
        return threats
    
    def _detect_dict_threats(self, data: Dict[str, Any], context: str) -> List[Dict[str, Any]]:
        """Detect threats in dictionary data."""
        threats = []
        
        for key, value in data.items():
            # Check key for threats
            key_threats = self._detect_string_threats(str(key), f"{context}.key")
            threats.extend(key_threats)
            
            # Check value for threats
            value_threats = self._detect_threats(value, f"{context}.value")
            threats.extend(value_threats)
        
        return threats
    
    def _detect_list_threats(self, data: List[Any], context: str) -> List[Dict[str, Any]]:
        """Detect threats in list data."""
        threats = []
        
        for i, item in enumerate(data):
            item_threats = self._detect_threats(item, f"{context}[{i}]")
            threats.extend(item_threats)
        
        return threats
    
    def _context_specific_validation(self, data: Any, context: str) -> Dict[str, Any]:
        """Perform context-specific validation."""
        result = {'valid': True, 'warnings': []}
        
        if context == "file_path":
            result = self._validate_file_path(data)
        elif context == "sql":
            result = self._validate_sql(data)
        elif context == "url":
            result = self._validate_url(data)
        
        return result
    
    def _validate_file_path(self, data: Any) -> Dict[str, Any]:
        """Validate file path data."""
        result = {'valid': True, 'warnings': []}
        
        if not isinstance(data, str):
            result['valid'] = False
            result['warnings'].append('File path must be a string')
            return result
        
        # Check for path traversal
        if '..' in data or '\\' in data:
            result['valid'] = False
            result['warnings'].append('Path traversal detected')
        
        # Check file extension
        if '.' in data:
            ext = data.split('.')[-1].lower()
            if ext not in self._validation_rules['allowed_file_extensions']:
                result['warnings'].append(f'Unusual file extension: .{ext}')
        
        return result
    
    def _validate_sql(self, data: Any) -> Dict[str, Any]:
        """Validate SQL data."""
        result = {'valid': True, 'warnings': []}
        
        if not isinstance(data, str):
            result['valid'] = False
            result['warnings'].append('SQL must be a string')
            return result
        
        # Additional SQL-specific checks
        sql_lower = data.lower()
        if 'union' in sql_lower and 'select' in sql_lower:
            result['warnings'].append('Potential SQL injection pattern detected')
        
        return result
    
    def _validate_url(self, data: Any) -> Dict[str, Any]:
        """Validate URL data."""
        result = {'valid': True, 'warnings': []}
        
        if not isinstance(data, str):
            result['valid'] = False
            result['warnings'].append('URL must be a string')
            return result
        
        # Basic URL validation
        if not data.startswith(('http://', 'https://', 'ftp://')):
            result['warnings'].append('URL should start with http://, https://, or ftp://')
        
        return result
    
    def add_threat_pattern(self, category: str, pattern: str) -> bool:
        """
        Add a custom threat pattern.
        
        Args:
            category: Threat category
            pattern: Regex pattern
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            
            if category not in self._threat_patterns:
                self._threat_patterns[category] = []
                self._compiled_threats[category] = []
            
            self._threat_patterns[category].append(pattern)
            self._compiled_threats[category].append(compiled)
            return True
            
        except re.error:
            return False
    
    def remove_threat_pattern(self, category: str, pattern: str) -> bool:
        """
        Remove a threat pattern.
        
        Args:
            category: Threat category
            pattern: Regex pattern
            
        Returns:
            True if removed successfully, False otherwise
        """
        if category in self._threat_patterns and pattern in self._threat_patterns[category]:
            index = self._threat_patterns[category].index(pattern)
            del self._threat_patterns[category][index]
            del self._compiled_threats[category][index]
            return True
        return False
    
    def is_enabled(self) -> bool:
        """Check if validator is enabled."""
        return self._enabled
    
    def enable(self) -> None:
        """Enable validator."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable validator."""
        self._enabled = False
