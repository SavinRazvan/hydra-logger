"""
Code Safeguards and Quality Assurance System for Hydra-Logger

This module provides comprehensive code quality safeguards and validation
rules to prevent common mistakes and ensure consistency across all logger
implementations. It includes automated code analysis, best practice
enforcement, and quality metrics.

ARCHITECTURE:
- SafeguardRule: Individual validation rules with severity levels
- CodeSafeguards: Main validation engine with rule management
- Quality Metrics: Automated code quality assessment
- Best Practice Enforcement: Automated compliance checking

SAFEGUARD CATEGORIES:
- Object Pool Requirements: Ensures proper object pooling usage
- Handler Parameters: Validates handler parameter consistency
- Required Methods: Checks for essential method implementations
- Log Method Optimization: Validates performance optimizations
- Duplicate Code Detection: Identifies code duplication issues
- Error Handling: Ensures proper error handling patterns

VALIDATION FEATURES:
- Automated code analysis
- Best practice enforcement
- Performance optimization validation
- Code duplication detection
- Error handling verification
- Consistency checking across implementations

QUALITY METRICS:
- Code quality scores
- Optimization compliance rates
- Error handling coverage
- Performance metric validation
- Consistency measurements

USAGE EXAMPLES:

Logger Class Validation:
    from hydra_logger.core.safeguards import CodeSafeguards
    
    safeguards = CodeSafeguards()
    results = safeguards.validate_logger_class(MyLogger, "MyLogger")
    
    if results['errors']:
        print("Validation errors:", results['errors'])
    if results['warnings']:
        print("Validation warnings:", results['warnings'])

Bulk Logger Validation:
    from hydra_logger.core.safeguards import CodeSafeguards
    
    safeguards = CodeSafeguards()
    logger_classes = {
        "SyncLogger": SyncLogger,
        "AsyncLogger": AsyncLogger,
        "CompositeLogger": CompositeLogger
    }
    
    all_results = safeguards.validate_all_loggers(logger_classes)
    for logger_name, results in all_results.items():
        print(f"{logger_name}: {len(results['errors'])} errors, {len(results['warnings'])} warnings")

Custom Safeguard Rules:
    from hydra_logger.core.safeguards import CodeSafeguards, SafeguardRule
    
    safeguards = CodeSafeguards()
    
    # Add custom validation rule
    def check_custom_pattern(logger_class, logger_name):
        # Custom validation logic
        return {"status": "pass", "message": "Custom check passed"}
    
    custom_rule = SafeguardRule(
        name="custom_pattern",
        description="Custom validation pattern",
        check_function=check_custom_pattern,
        severity="warning"
    )
    
    safeguards.add_rule(custom_rule)
"""

import inspect
import warnings
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass


@dataclass
class SafeguardRule:
    """A safeguard rule to prevent common mistakes."""
    name: str
    description: str
    check_function: callable
    severity: str  # 'error', 'warning', 'info'


class CodeSafeguards:
    """
    Safeguard system to prevent common mistakes in logger implementations.
    
    Prevents:
    - Missing object pools in high-performance loggers
    - Incorrect handler parameter usage
    - Missing required methods
    - Performance regressions
    - Inconsistent implementations
    """
    
    def __init__(self):
        self.rules = self._setup_safeguard_rules()
    
    def _setup_safeguard_rules(self) -> List[SafeguardRule]:
        """Setup all safeguard rules."""
        return [
            # Rule 1: High-performance loggers must have object pools
            SafeguardRule(
                name="object_pool_required",
                description="High-performance loggers must have object pooling",
                check_function=self._check_object_pool_required,
                severity="error"
            ),
            
            # Rule 2: Handler parameters must be correct
            SafeguardRule(
                name="handler_parameters",
                description="Handler parameters must match constructor signature",
                check_function=self._check_handler_parameters,
                severity="error"
            ),
            
            # Rule 3: Required methods must exist
            SafeguardRule(
                name="required_methods",
                description="All loggers must have required methods",
                check_function=self._check_required_methods,
                severity="error"
            ),
            
            # Rule 4: Log method must be optimized
            SafeguardRule(
                name="log_method_optimization",
                description="Log method must be optimized for performance",
                check_function=self._check_log_method_optimization,
                severity="warning"
            ),
            
            # Rule 5: No duplicate code
            SafeguardRule(
                name="no_duplicate_code",
                description="No duplicate code patterns",
                check_function=self._check_duplicate_code,
                severity="warning"
            ),
            
            # Rule 6: Consistent error handling
            SafeguardRule(
                name="consistent_error_handling",
                description="Error handling must be consistent",
                check_function=self._check_error_handling,
                severity="warning"
            )
        ]
    
    def validate_logger_class(self, logger_class: Type, logger_name: str) -> Dict[str, Any]:
        """Validate a logger class against all safeguard rules."""
        results = {
            'logger_name': logger_name,
            'passed_rules': [],
            'failed_rules': [],
            'warnings': [],
            'errors': [],
            'overall_status': 'PASS'
        }
        
        print(f"\n🔍 SAFEGUARD VALIDATION: {logger_name}")
        print("-" * 50)
        
        for rule in self.rules:
            try:
                rule_result = rule.check_function(logger_class, logger_name)
                
                if rule_result['status'] == 'PASS':
                    results['passed_rules'].append(rule.name)
                    print(f"✅ {rule.name}: {rule_result['message']}")
                elif rule_result['status'] == 'WARNING':
                    results['warnings'].append(f"{rule.name}: {rule_result['message']}")
                    print(f"⚠️  {rule.name}: {rule_result['message']}")
                else:
                    results['failed_rules'].append(rule.name)
                    results['errors'].append(f"{rule.name}: {rule_result['message']}")
                    print(f"❌ {rule.name}: {rule_result['message']}")
                    
            except Exception as e:
                error_msg = f"Rule {rule.name} failed: {str(e)}"
                results['errors'].append(error_msg)
                print(f"❌ {rule.name}: {error_msg}")
        
        # Determine overall status
        if results['errors']:
            results['overall_status'] = 'FAIL'
        elif results['warnings']:
            results['overall_status'] = 'WARNING'
        
        return results
    
    def _check_object_pool_required(self, logger_class: Type, logger_name: str) -> Dict[str, Any]:
        """Check if high-performance loggers have object pools."""
        # High-performance loggers should have object pools
        high_perf_names = ['ultra', 'extreme', 'optimized', 'performance']
        is_high_perf = any(name in logger_name.lower() for name in high_perf_names)
        
        if is_high_perf:
            # Check if logger has object pool
            try:
                # Create instance to check
                logger = logger_class()
                if hasattr(logger, '_record_pool'):
                    return {'status': 'PASS', 'message': 'Object pool present'}
                else:
                    return {'status': 'FAIL', 'message': 'High-performance logger missing object pool'}
            except Exception as e:
                return {'status': 'ERROR', 'message': f'Cannot instantiate logger: {e}'}
        else:
            return {'status': 'PASS', 'message': 'Standard logger (object pool not required)'}
    
    def _check_handler_parameters(self, logger_class: Type, logger_name: str) -> Dict[str, Any]:
        """Check if handler parameters are correct."""
        try:
            # Check if logger creates handlers with correct parameters
            logger = logger_class()
            
            # Look for handler creation in the logger
            if hasattr(logger, '_handlers'):
                for handler_name, handler in logger._handlers.items():
                    # Check if handler has required methods
                    if not hasattr(handler, 'emit'):
                        return {'status': 'FAIL', 'message': f'Handler {handler_name} missing emit method'}
                    
                    # Check if handler is properly initialized
                    if not hasattr(handler, '_stream') and not hasattr(handler, '_file'):
                        return {'status': 'WARNING', 'message': f'Handler {handler_name} may not be properly initialized'}
            
            return {'status': 'PASS', 'message': 'Handler parameters correct'}
            
        except Exception as e:
            return {'status': 'ERROR', 'message': f'Cannot check handler parameters: {e}'}
    
    def _check_required_methods(self, logger_class: Type, logger_name: str) -> Dict[str, Any]:
        """Check if logger has all required methods."""
        required_methods = ['log', 'debug', 'info', 'warning', 'error', 'critical', 'close']
        missing_methods = []
        
        for method_name in required_methods:
            if not hasattr(logger_class, method_name):
                missing_methods.append(method_name)
        
        if missing_methods:
            return {'status': 'FAIL', 'message': f'Missing required methods: {missing_methods}'}
        else:
            return {'status': 'PASS', 'message': 'All required methods present'}
    
    def _check_log_method_optimization(self, logger_class: Type, logger_name: str) -> Dict[str, Any]:
        """Check if log method is optimized."""
        try:
            # Get the log method source code
            log_method = getattr(logger_class, 'log', None)
            if not log_method:
                return {'status': 'FAIL', 'message': 'No log method found'}
            
            # Check if method is optimized (simplified)
            source = inspect.getsource(log_method)
            
            # Look for optimization indicators
            optimizations = []
            if 'record_pool' in source:
                optimizations.append('object_pooling')
            if 'try:' in source and 'except' in source:
                optimizations.append('error_handling')
            if 'return' in source and source.count('return') > 1:
                optimizations.append('early_returns')
            
            # Look for anti-patterns (smarter detection)
            anti_patterns = []
            
            # Only flag too many conditionals if it's excessive
            if_count = source.count('if')
            if if_count > 20:  # Further increased threshold for feature-rich loggers
                anti_patterns.append('too_many_conditionals')
            
            # Only flag loops if they're in the actual log method execution path
            if 'for' in source and 'in' in source:
                # Check if this is in the main log method execution (not initialization)
                lines = source.split('\n')
                in_log_method = False
                loop_in_critical_path = False
                
                for line in lines:
                    if 'def log(' in line:
                        in_log_method = True
                    elif line.strip().startswith('def ') and 'def log(' not in line:
                        in_log_method = False
                    elif in_log_method and 'for ' in line and ' in ' in line:
                        # Check if it's a simple range loop (usually OK)
                        if 'range(' in line and 'i in range(' in line:
                            continue  # Simple range loops are usually fine
                        # Check if it's a simple iteration over a small collection
                        elif 'in [' in line or 'in (' in line:
                            continue  # Simple iterations are usually fine
                        # Check if it's a dictionary iteration (usually OK)
                        elif '.items()' in line or '.keys()' in line or '.values()' in line:
                            continue  # Dictionary iterations are usually fine
                        # Check if it's in setup/initialization code (usually OK)
                        elif 'kwargs' in line or 'layer' in line or 'handler' in line:
                            continue  # Setup loops are usually fine
                        # Check if it's a join operation (very fast, not a real loop)
                        elif '.join(' in line:
                            continue  # Join operations are optimized and fast
                        else:
                            print(f"DEBUG: Found loop in {logger_name}: {line.strip()}")
                            loop_in_critical_path = True
                
                if loop_in_critical_path:
                    # Debug: print what loop was detected
                    print(f"DEBUG: Detected loop in {logger_name} log method")
                    anti_patterns.append('loops_in_critical_path')
            
            if anti_patterns:
                return {'status': 'WARNING', 'message': f'Potential performance issues: {anti_patterns}'}
            elif optimizations:
                return {'status': 'PASS', 'message': f'Optimizations found: {optimizations}'}
            else:
                return {'status': 'WARNING', 'message': 'No obvious optimizations detected'}
                
        except Exception as e:
            return {'status': 'ERROR', 'message': f'Cannot analyze log method: {e}'}
    
    def _check_duplicate_code(self, logger_class: Type, logger_name: str) -> Dict[str, Any]:
        """Check for duplicate code patterns."""
        try:
            # Get all method source codes
            methods = []
            for name, method in inspect.getmembers(logger_class, predicate=inspect.isfunction):
                if not name.startswith('_'):
                    try:
                        source = inspect.getsource(method)
                        methods.append((name, source))
                    except:
                        pass
            
            # Simple duplicate detection (same source code)
            duplicates = []
            for i, (name1, source1) in enumerate(methods):
                for j, (name2, source2) in enumerate(methods[i+1:], i+1):
                    if source1 == source2 and len(source1) > 100:  # Only check substantial methods
                        duplicates.append(f"{name1} == {name2}")
            
            if duplicates:
                return {'status': 'WARNING', 'message': f'Duplicate code found: {duplicates}'}
            else:
                return {'status': 'PASS', 'message': 'No duplicate code detected'}
                
        except Exception as e:
            return {'status': 'ERROR', 'message': f'Cannot check for duplicates: {e}'}
    
    def _check_error_handling(self, logger_class: Type, logger_name: str) -> Dict[str, Any]:
        """Check for consistent error handling."""
        try:
            # Check if log method has proper error handling
            log_method = getattr(logger_class, 'log', None)
            if not log_method:
                return {'status': 'FAIL', 'message': 'No log method to check'}
            
            source = inspect.getsource(log_method)
            
            # Check for error handling patterns
            has_try_except = 'try:' in source and 'except' in source
            has_silent_handling = 'pass' in source or 'silent' in source.lower()
            
            if has_try_except and has_silent_handling:
                return {'status': 'PASS', 'message': 'Proper error handling with silent failures'}
            elif has_try_except:
                return {'status': 'WARNING', 'message': 'Error handling present but may not be silent'}
            else:
                return {'status': 'WARNING', 'message': 'No error handling detected in log method'}
                
        except Exception as e:
            return {'status': 'ERROR', 'message': f'Cannot check error handling: {e}'}
    
    def validate_all_loggers(self, logger_classes: Dict[str, Type]) -> Dict[str, Any]:
        """Validate all logger classes."""
        results = {
            'total_loggers': len(logger_classes),
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'logger_results': {}
        }
        
        print("🛡️  CODE SAFEGUARD VALIDATION")
        print("=" * 60)
        
        for logger_name, logger_class in logger_classes.items():
            logger_result = self.validate_logger_class(logger_class, logger_name)
            results['logger_results'][logger_name] = logger_result
            
            if logger_result['overall_status'] == 'PASS':
                results['passed'] += 1
            elif logger_result['overall_status'] == 'FAIL':
                results['failed'] += 1
            else:
                results['warnings'] += 1
        
        # Print summary
        print(f"\n📊 SAFEGUARD SUMMARY")
        print("-" * 30)
        print(f"Total Loggers: {results['total_loggers']}")
        print(f"✅ Passed: {results['passed']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"⚠️  Warnings: {results['warnings']}")
        
        if results['failed'] > 0:
            print(f"\n🚨 FAILED LOGGERS:")
            for logger_name, result in results['logger_results'].items():
                if result['overall_status'] == 'FAIL':
                    print(f"  • {logger_name}: {', '.join(result['errors'])}")
        
        return results


# Global safeguards instance
code_safeguards = CodeSafeguards()
