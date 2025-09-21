"""
Component Compatibility Tracking System for Hydra-Logger

This module provides comprehensive component compatibility tracking and management
with support for multiple compatibility types, rule-based validation, and
compatibility matrix management. It helps ensure components work together
correctly and provides recommendations for compatibility issues.

FEATURES:
- Multiple compatibility types (interface, version, performance, security, etc.)
- Rule-based compatibility validation
- Compatibility matrix management and caching
- Component metadata analysis
- Compatibility recommendations and upgrade paths
- Export/import compatibility data

COMPATIBILITY TYPES:
- Interface: API interface compatibility
- Data Format: Data format compatibility
- Protocol: Communication protocol compatibility
- Version: Version compatibility
- Dependency: Dependency compatibility
- Performance: Performance compatibility
- Security: Security compatibility
- Custom: Custom compatibility criteria

USAGE:
    from hydra_logger.registry import CompatibilityTracker, CompatibilityRule, CompatibilityType
    
    # Create compatibility tracker
    tracker = CompatibilityTracker()
    
    # Add compatibility rule
    rule = CompatibilityRule(
        rule_id="version_check",
        rule_name="Version Compatibility",
        description="Check version compatibility",
        compatibility_type=CompatibilityType.VERSION,
        criteria={"min_version": "1.0.0", "max_version": "2.0.0"}
    )
    tracker.add_compatibility_rule(rule)
    
    # Check compatibility
    result = tracker.check_compatibility("component_a", "component_b")
    
    # Get compatible components
    compatible = tracker.get_compatible_components("component_a", min_score=0.8)
"""

import time
import json
from typing import Any, Dict, List, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict


class CompatibilityStatus(Enum):
    """Compatibility status levels."""
    COMPATIBLE = "compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"
    TESTING = "testing"
    DEPRECATED = "deprecated"


class CompatibilityType(Enum):
    """Types of compatibility relationships."""
    INTERFACE = "interface"           # API interface compatibility
    DATA_FORMAT = "data_format"       # Data format compatibility
    PROTOCOL = "protocol"             # Communication protocol compatibility
    VERSION = "version"               # Version compatibility
    DEPENDENCY = "dependency"         # Dependency compatibility
    PERFORMANCE = "performance"       # Performance compatibility
    SECURITY = "security"             # Security compatibility
    CUSTOM = "custom"                 # Custom compatibility criteria


@dataclass
class CompatibilityRule:
    """Rule for determining component compatibility."""
    
    # Rule identification
    rule_id: str
    rule_name: str
    description: str
    
    # Compatibility criteria
    compatibility_type: CompatibilityType
    criteria: Dict[str, Any]
    weight: float = 1.0  # Importance weight (0.0 to 1.0)
    
    # Validation
    validation_function: Optional[str] = None  # Name of validation function
    custom_logic: Optional[str] = None  # Custom validation logic
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    priority: str = "medium"  # low, medium, high, critical
    
    # Tags and categories
    tags: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary."""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'description': self.description,
            'compatibility_type': self.compatibility_type.value,
            'criteria': self.criteria,
            'weight': self.weight,
            'validation_function': self.validation_function,
            'custom_logic': self.custom_logic,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'priority': self.priority,
            'tags': list(self.tags),
            'categories': list(self.categories)
        }


@dataclass
class CompatibilityResult:
    """Result of a compatibility check."""
    
    # Basic information
    component_a_id: str
    component_b_id: str
    compatibility_status: CompatibilityStatus
    overall_score: float  # 0.0 to 1.0
    
    # Detailed results
    rule_results: Dict[str, Dict[str, Any]]  # rule_id -> {status, score, details}
    passed_rules: int
    failed_rules: int
    total_rules: int
    
    # Metadata
    checked_at: datetime = field(default_factory=datetime.now)
    check_duration: float = 0.0  # seconds
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    upgrade_paths: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'component_a_id': self.component_a_id,
            'component_b_id': self.component_b_id,
            'compatibility_status': self.compatibility_status.value,
            'overall_score': self.overall_score,
            'rule_results': self.rule_results,
            'passed_rules': self.passed_rules,
            'failed_rules': self.failed_rules,
            'total_rules': self.total_rules,
            'checked_at': self.checked_at.isoformat(),
            'check_duration': self.check_duration,
            'error_messages': self.error_messages,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'upgrade_paths': self.upgrade_paths
        }
    
    def is_compatible(self) -> bool:
        """Check if components are compatible."""
        return self.compatibility_status in [CompatibilityStatus.COMPATIBLE, CompatibilityStatus.PARTIALLY_COMPATIBLE]
    
    def get_confidence_level(self) -> str:
        """Get confidence level based on score."""
        if self.overall_score >= 0.9:
            return "high"
        elif self.overall_score >= 0.7:
            return "medium"
        elif self.overall_score >= 0.5:
            return "low"
        else:
            return "very_low"


class CompatibilityTracker:
    """Component compatibility tracking and management system."""
    
    def __init__(self):
        """Initialize the compatibility tracker."""
        self._compatibility_rules: Dict[str, CompatibilityRule] = {}
        self._compatibility_cache: Dict[str, CompatibilityResult] = {}
        self._compatibility_matrix: Dict[str, Dict[str, CompatibilityResult]] = {}
        self._component_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Compatibility policies
        self._auto_check_policy = "on_demand"  # on_demand, periodic, real_time
        self._cache_ttl = 3600  # 1 hour
        self._min_compatibility_score = 0.7
        
        # Statistics
        self._total_checks = 0
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize built-in rules
        self._initialize_builtin_rules()
    
    def add_compatibility_rule(self, rule: CompatibilityRule) -> bool:
        """Add a compatibility rule."""
        try:
            self._compatibility_rules[rule.rule_id] = rule
            return True
        except Exception:
            return False
    
    def remove_compatibility_rule(self, rule_id: str) -> bool:
        """Remove a compatibility rule."""
        if rule_id in self._compatibility_rules:
            del self._compatibility_rules[rule_id]
            return True
        return False
    
    def get_compatibility_rule(self, rule_id: str) -> Optional[CompatibilityRule]:
        """Get a compatibility rule by ID."""
        return self._compatibility_rules.get(rule_id)
    
    def get_all_rules(self) -> List[CompatibilityRule]:
        """Get all compatibility rules."""
        return list(self._compatibility_rules.values())
    
    def check_compatibility(self, component_a_id: str, component_b_id: str, 
                          force_refresh: bool = False) -> CompatibilityResult:
        """Check compatibility between two components."""
        cache_key = f"{component_a_id}:{component_b_id}"
        
        # Check cache first
        if not force_refresh and cache_key in self._compatibility_cache:
            cached_result = self._compatibility_cache[cache_key]
            if self._is_cache_valid(cached_result):
                self._cache_hits += 1
                return cached_result
        
        self._cache_misses += 1
        self._total_checks += 1
        
        # Perform compatibility check
        start_time = time.time()
        result = self._perform_compatibility_check(component_a_id, component_b_id)
        result.check_duration = time.time() - start_time
        
        # Cache result
        self._compatibility_cache[cache_key] = result
        
        # Update compatibility matrix
        if component_a_id not in self._compatibility_matrix:
            self._compatibility_matrix[component_a_id] = {}
        self._compatibility_matrix[component_a_id][component_b_id] = result
        
        return result
    
    def get_compatibility_matrix(self) -> Dict[str, Dict[str, CompatibilityResult]]:
        """Get the complete compatibility matrix."""
        return self._compatibility_matrix.copy()
    
    def get_compatible_components(self, component_id: str, 
                                min_score: Optional[float] = None) -> List[Tuple[str, float]]:
        """Get all components compatible with a given component."""
        if min_score is None:
            min_score = self._min_compatibility_score
        
        compatible = []
        
        if component_id in self._compatibility_matrix:
            for other_id, result in self._compatibility_matrix[component_id].items():
                if result.overall_score >= min_score:
                    compatible.append((other_id, result.overall_score))
        
        # Sort by compatibility score (descending)
        compatible.sort(key=lambda x: x[1], reverse=True)
        return compatible
    
    def get_compatibility_summary(self) -> Dict[str, Any]:
        """Get a summary of compatibility information."""
        summary = {
            'total_components': len(self._component_metadata),
            'total_rules': len(self._compatibility_rules),
            'total_checks': self._total_checks,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(self._total_checks, 1),
            'compatibility_distribution': defaultdict(int),
            'rule_usage': defaultdict(int),
            'recent_checks': 0
        }
        
        now = datetime.now()
        recent_threshold = now - timedelta(hours=24)
        
        # Analyze compatibility matrix
        for component_a, results in self._compatibility_matrix.items():
            for component_b, result in results.items():
                # Compatibility distribution
                summary['compatibility_distribution'][result.compatibility_status.value] += 1
                
                # Recent checks
                if result.checked_at > recent_threshold:
                    summary['recent_checks'] += 1
                
                # Rule usage
                for rule_id in result.rule_results:
                    summary['rule_usage'][rule_id] += 1
        
        return summary
    
    def export_compatibility_data(self, format_type: str = "json") -> Union[str, Dict[str, Any]]:
        """Export compatibility data in specified format."""
        export_data = {
            'rules': {rule_id: rule.to_dict() for rule_id, rule in self._compatibility_rules.items()},
            'matrix': {
                component_a: {
                    component_b: result.to_dict()
                    for component_b, result in results.items()
                }
                for component_a, results in self._compatibility_matrix.items()
            },
            'metadata': self._component_metadata,
            'statistics': self.get_compatibility_summary()
        }
        
        if format_type.lower() == "json":
            return json.dumps(export_data, indent=2)
        elif format_type.lower() == "dict":
            return export_data
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def import_compatibility_data(self, data: Union[str, Dict[str, Any]], format_type: str = "json") -> bool:
        """Import compatibility data from external source."""
        try:
            if format_type.lower() == "json" and isinstance(data, str):
                data = json.loads(data)
            
            if not isinstance(data, dict):
                return False
            
            # Import rules
            if 'rules' in data:
                for rule_id, rule_dict in data['rules'].items():
                    rule = CompatibilityRule(**rule_dict)
                    self.add_compatibility_rule(rule)
            
            # Import matrix
            if 'matrix' in data:
                for component_a, results in data['matrix'].items():
                    for component_b, result_dict in results.items():
                        result = CompatibilityResult(**result_dict)
                        if component_a not in self._compatibility_matrix:
                            self._compatibility_matrix[component_a] = {}
                        self._compatibility_matrix[component_a][component_b] = result
                        
                        # Update cache
                        cache_key = f"{component_a}:{component_b}"
                        self._compatibility_cache[cache_key] = result
            
            # Import metadata
            if 'metadata' in data:
                self._component_metadata.update(data['metadata'])
            
            return True
        except Exception:
            return False
    
    def set_compatibility_policy(self, auto_check: str = "on_demand", 
                               cache_ttl: int = 3600, 
                               min_score: float = 0.7):
        """Set compatibility checking policies."""
        self._auto_check_policy = auto_check
        self._cache_ttl = cache_ttl
        self._min_compatibility_score = min_score
    
    def _initialize_builtin_rules(self):
        """Initialize built-in compatibility rules."""
        # Interface compatibility rule
        interface_rule = CompatibilityRule(
            rule_id="interface_compatibility",
            rule_name="Interface Compatibility",
            description="Check if components implement compatible interfaces",
            compatibility_type=CompatibilityType.INTERFACE,
            criteria={
                "required_methods": [],
                "required_attributes": [],
                "interface_version": "1.0"
            },
            weight=0.8,
            priority="high",
            tags={"core", "interface"},
            categories={"validation"}
        )
        self.add_compatibility_rule(interface_rule)
        
        # Version compatibility rule
        version_rule = CompatibilityRule(
            rule_id="version_compatibility",
            rule_name="Version Compatibility",
            description="Check version compatibility between components",
            compatibility_type=CompatibilityType.VERSION,
            criteria={
                "min_version": "1.0.0",
                "max_version": "2.0.0",
                "version_scheme": "semver"
            },
            weight=0.9,
            priority="critical",
            tags={"version", "semver"},
            categories={"validation"}
        )
        self.add_compatibility_rule(version_rule)
        
        # Performance compatibility rule
        performance_rule = CompatibilityRule(
            rule_id="performance_compatibility",
            rule_name="Performance Compatibility",
            description="Check if components have compatible performance characteristics",
            compatibility_type=CompatibilityType.PERFORMANCE,
            criteria={
                "max_response_time": 1000,  # milliseconds
                "min_throughput": 100,      # operations per second
                "memory_limit": 100         # MB
            },
            weight=0.6,
            priority="medium",
            tags={"performance", "metrics"},
            categories={"validation"}
        )
        self.add_compatibility_rule(performance_rule)
    
    def _perform_compatibility_check(self, component_a_id: str, component_b_id: str) -> CompatibilityResult:
        """Perform the actual compatibility check."""
        # Initialize result
        result = CompatibilityResult(
            component_a_id=component_a_id,
            component_b_id=component_b_id,
            compatibility_status=CompatibilityStatus.UNKNOWN,
            overall_score=0.0,
            rule_results={},
            passed_rules=0,
            failed_rules=0,
            total_rules=0
        )
        
        # Get component metadata
        metadata_a = self._component_metadata.get(component_a_id, {})
        metadata_b = self._component_metadata.get(component_b_id, {})
        
        # Apply each compatibility rule
        total_score = 0.0
        total_weight = 0.0
        
        for rule_id, rule in self._compatibility_rules.items():
            if not rule.is_active:
                continue
            
            result.total_rules += 1
            
            try:
                # Apply rule validation
                rule_score = self._apply_compatibility_rule(rule, metadata_a, metadata_b)
                rule_result = {
                    'status': 'passed' if rule_score >= 0.5 else 'failed',
                    'score': rule_score,
                    'details': f"Rule {rule.rule_name} applied successfully"
                }
                
                if rule_score >= 0.5:
                    result.passed_rules += 1
                else:
                    result.failed_rules += 1
                
                # Weight the score
                weighted_score = rule_score * rule.weight
                total_score += weighted_score
                total_weight += rule.weight
                
                result.rule_results[rule_id] = rule_result
                
            except Exception as e:
                rule_result = {
                    'status': 'error',
                    'score': 0.0,
                    'details': f"Error applying rule: {str(e)}"
                }
                result.rule_results[rule_id] = rule_result
                result.error_messages.append(f"Rule {rule_id} failed: {str(e)}")
                result.failed_rules += 1
        
        # Calculate overall score
        if total_weight > 0:
            result.overall_score = total_score / total_weight
        else:
            result.overall_score = 0.0
        
        # Determine compatibility status
        if result.overall_score >= 0.9:
            result.compatibility_status = CompatibilityStatus.COMPATIBLE
        elif result.overall_score >= 0.7:
            result.compatibility_status = CompatibilityStatus.PARTIALLY_COMPATIBLE
        elif result.overall_score >= 0.5:
            result.compatibility_status = CompatibilityStatus.PARTIALLY_COMPATIBLE
        else:
            result.compatibility_status = CompatibilityStatus.INCOMPATIBLE
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _apply_compatibility_rule(self, rule: CompatibilityRule, 
                                metadata_a: Dict[str, Any], 
                                metadata_b: Dict[str, Any]) -> float:
        """Apply a specific compatibility rule."""
        rule_type = rule.compatibility_type
        
        if rule_type == CompatibilityType.INTERFACE:
            return self._check_interface_compatibility(rule, metadata_a, metadata_b)
        elif rule_type == CompatibilityType.VERSION:
            return self._check_version_compatibility(rule, metadata_a, metadata_b)
        elif rule_type == CompatibilityType.PERFORMANCE:
            return self._check_performance_compatibility(rule, metadata_a, metadata_b)
        else:
            # Default to basic compatibility check
            return self._check_basic_compatibility(rule, metadata_a, metadata_b)
    
    def _check_interface_compatibility(self, rule: CompatibilityRule, 
                                     metadata_a: Dict[str, Any], 
                                     metadata_b: Dict[str, Any]) -> float:
        """Check interface compatibility."""
        # This is a simplified check - in practice, you'd do deeper interface analysis
        required_methods = rule.criteria.get("required_methods", [])
        required_attributes = rule.criteria.get("required_attributes", [])
        
        score = 1.0
        
        # Check required methods
        for method in required_methods:
            if method not in metadata_a.get("methods", []) or method not in metadata_b.get("methods", []):
                score -= 0.2
        
        # Check required attributes
        for attr in required_attributes:
            if attr not in metadata_a.get("attributes", []) or attr not in metadata_b.get("attributes", []):
                score -= 0.2
        
        return max(0.0, score)
    
    def _check_version_compatibility(self, rule: CompatibilityRule, 
                                   metadata_a: Dict[str, Any], 
                                   metadata_b: Dict[str, Any]) -> float:
        """Check version compatibility."""
        # This is a simplified check - in practice, you'd use proper version parsing
        version_a = metadata_a.get("version", "0.0.0")
        version_b = metadata_b.get("version", "0.0.0")
        
        # Simple version comparison (in practice, use proper version parsing)
        try:
            # Convert versions to comparable numbers
            v_a = [int(x) for x in version_a.split('.')]
            v_b = [int(x) for x in version_b.split('.')]
            
            # Major version should match for compatibility
            if v_a[0] == v_b[0]:
                return 1.0
            else:
                return 0.0
        except Exception:
            return 0.5  # Unknown compatibility
    
    def _check_performance_compatibility(self, rule: CompatibilityRule, 
                                       metadata_a: Dict[str, Any], 
                                       metadata_b: Dict[str, Any]) -> float:
        """Check performance compatibility."""
        # This is a simplified check - in practice, you'd do performance benchmarking
        score = 1.0
        
        # Check response time compatibility
        max_response_time = rule.criteria.get("max_response_time", 1000)
        response_time_a = metadata_a.get("response_time", 0)
        response_time_b = metadata_b.get("response_time", 0)
        
        if response_time_a > max_response_time or response_time_b > max_response_time:
            score -= 0.3
        
        # Check throughput compatibility
        min_throughput = rule.criteria.get("min_throughput", 100)
        throughput_a = metadata_a.get("throughput", 0)
        throughput_b = metadata_b.get("throughput", 0)
        
        if throughput_a < min_throughput or throughput_b < min_throughput:
            score -= 0.3
        
        return max(0.0, score)
    
    def _check_basic_compatibility(self, rule: CompatibilityRule, 
                                 metadata_a: Dict[str, Any], 
                                 metadata_b: Dict[str, Any]) -> float:
        """Check basic compatibility using rule criteria."""
        # Default compatibility check
        score = 1.0
        
        # Check if components have similar characteristics
        for key, expected_value in rule.criteria.items():
            if key in metadata_a and key in metadata_b:
                value_a = metadata_a[key]
                value_b = metadata_b[key]
                
                if value_a != value_b:
                    score -= 0.2
        
        return max(0.0, score)
    
    def _generate_recommendations(self, result: CompatibilityResult) -> List[str]:
        """Generate recommendations based on compatibility results."""
        recommendations = []
        
        if result.compatibility_status == CompatibilityStatus.INCOMPATIBLE:
            recommendations.append("Components are incompatible. Consider using compatible versions.")
        
        if result.overall_score < 0.7:
            recommendations.append("Low compatibility score. Review component requirements.")
        
        if result.failed_rules > 0:
            recommendations.append(f"{result.failed_rules} compatibility rules failed. Check component specifications.")
        
        if result.overall_score >= 0.9:
            recommendations.append("High compatibility. Components should work well together.")
        
        return recommendations
    
    def _is_cache_valid(self, result: CompatibilityResult) -> bool:
        """Check if cached result is still valid."""
        age = datetime.now() - result.checked_at
        return age.total_seconds() < self._cache_ttl
