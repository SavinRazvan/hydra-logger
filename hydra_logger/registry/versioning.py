"""
Component Versioning and Compatibility Management System for Hydra-Logger

This module provides comprehensive version management and compatibility tracking
for components with support for multiple versioning schemes, dependency resolution,
and compatibility analysis. It ensures proper version handling and compatibility
checking across the system.

FEATURES:
- Multiple versioning schemes (SemVer, CalVer, PEP440, Custom)
- Version parsing and validation
- Compatibility level determination
- Dependency resolution and management
- Version policy enforcement
- Export/import version data
- Version analytics and reporting

VERSIONING SCHEMES:
- SemVer: Semantic versioning (1.2.3)
- CalVer: Calendar versioning (2024.1.15)
- PEP440: Python PEP 440 versioning
- Custom: Custom versioning schemes

COMPATIBILITY LEVELS:
- Fully Compatible: Complete compatibility
- Backward Compatible: Backward compatibility
- Forward Compatible: Forward compatibility
- Partially Compatible: Partial compatibility
- Incompatible: No compatibility
- Unknown: Compatibility unknown

USAGE:
    from hydra_logger.registry import ComponentVersioning, VersionInfo, VersionType, CompatibilityLevel
    
    # Create versioning system
    versioning = ComponentVersioning()
    
    # Create version info
    version_info = VersionInfo(
        version_string="1.2.3",
        version_type=VersionType.SEMVER,
        release_date=datetime.now(),
        python_versions=["3.8+", "3.9+", "3.10+"],
        dependencies={"requests": ">=2.25.0"}
    )
    
    # Register version
    versioning.register_version("my_component", version_info)
    
    # Check compatibility
    compatibility = versioning.check_compatibility(
        "component_a", "1.0.0",
        "component_b", "1.1.0"
    )
    
    # Resolve dependencies
    dependencies = versioning.resolve_dependencies("my_component", "1.2.3")
    
    # Get compatibility report
    report = versioning.get_compatibility_report("my_component", "1.2.3")
    
    # Get version summary
    summary = versioning.get_version_summary()
"""

import re
import time
import json
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from packaging import version as pkg_version
from packaging.specifiers import SpecifierSet
from packaging.requirements import Requirement


class VersionType(Enum):
    """Types of versioning schemes."""
    SEMVER = "semver"  # Semantic versioning (1.2.3)
    CALVER = "calver"  # Calendar versioning (2024.1.15)
    PEP440 = "pep440"  # Python PEP 440 versioning
    CUSTOM = "custom"  # Custom versioning scheme


class CompatibilityLevel(Enum):
    """Component compatibility levels."""
    FULLY_COMPATIBLE = "fully_compatible"
    BACKWARD_COMPATIBLE = "backward_compatible"
    FORWARD_COMPATIBLE = "forward_compatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"


@dataclass
class VersionInfo:
    """Version information for a component."""
    
    # Version details
    version_string: str
    version_type: VersionType
    major: Optional[int] = None
    minor: Optional[int] = None
    patch: Optional[int] = None
    prerelease: Optional[str] = None
    build: Optional[str] = None
    
    # Metadata
    release_date: Optional[datetime] = None
    end_of_life: Optional[datetime] = None
    is_stable: bool = True
    is_supported: bool = True
    
    # Compatibility
    python_versions: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    breaking_changes: List[str] = field(default_factory=list)
    new_features: List[str] = field(default_factory=list)
    bug_fixes: List[str] = field(default_factory=list)
    
    # Custom fields
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.version_type == VersionType.SEMVER:
            self._parse_semver()
        elif self.version_type == VersionType.CALVER:
            self._parse_calver()
        elif self.version_type == VersionType.PEP440:
            self._parse_pep440()
    
    def _parse_semver(self):
        """Parse semantic version string."""
        try:
            # Handle extended semver format (1.2.3-alpha.1+build.123)
            match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([\w\-\.]+))?(?:\+([\w\-\.]+))?$', self.version_string)
            if match:
                self.major = int(match.group(1))
                self.minor = int(match.group(2))
                self.patch = int(match.group(3))
                self.prerelease = match.group(4)
                self.build = match.group(5)
                
                # Check if stable
                self.is_stable = not self.prerelease or not re.match(r'^alpha|beta|rc|pre', self.prerelease, re.IGNORECASE)
        except Exception:
            pass
    
    def _parse_calver(self):
        """Parse calendar version string."""
        try:
            # Handle calendar versioning (2024.1.15)
            match = re.match(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', self.version_string)
            if match:
                self.major = int(match.group(1))  # Year
                self.minor = int(match.group(2))  # Month
                self.patch = int(match.group(3))  # Day
        except Exception:
            pass
    
    def _parse_pep440(self):
        """Parse PEP 440 version string."""
        try:
            # Use packaging library for PEP 440 parsing
            parsed = pkg_version.parse(self.version_string)
            if hasattr(parsed, 'major'):
                self.major = parsed.major
            if hasattr(parsed, 'minor'):
                self.minor = parsed.minor
            if hasattr(parsed, 'micro'):
                self.patch = parsed.micro
            if hasattr(parsed, 'pre'):
                self.prerelease = str(parsed.pre) if parsed.pre else None
            if hasattr(parsed, 'dev'):
                self.build = str(parsed.dev) if parsed.dev else None
        except Exception:
            pass
    
    def is_compatible_with(self, other_version: 'VersionInfo') -> CompatibilityLevel:
        """Check compatibility with another version."""
        if self.version_type != other_version.version_type:
            return CompatibilityLevel.UNKNOWN
        
        if self.version_type == VersionType.SEMVER:
            return self._check_semver_compatibility(other_version)
        elif self.version_type == VersionType.CALVER:
            return self._check_calver_compatibility(other_version)
        elif self.version_type == VersionType.PEP440:
            return self._check_pep440_compatibility(other_version)
        
        return CompatibilityLevel.UNKNOWN
    
    def _check_semver_compatibility(self, other: 'VersionInfo') -> CompatibilityLevel:
        """Check semantic version compatibility."""
        if not all([self.major, self.minor, self.patch, other.major, other.minor, other.patch]):
            return CompatibilityLevel.UNKNOWN
        
        # Major version change = breaking change
        if self.major != other.major:
            return CompatibilityLevel.INCOMPATIBLE
        
        # Minor version change = backward compatible
        if self.minor != other.minor:
            return CompatibilityLevel.BACKWARD_COMPATIBLE
        
        # Patch version change = fully compatible
        if self.patch != other.patch:
            return CompatibilityLevel.FULLY_COMPATIBLE
        
        return CompatibilityLevel.FULLY_COMPATIBLE
    
    def _check_calver_compatibility(self, other: 'VersionInfo') -> CompatibilityLevel:
        """Check calendar version compatibility."""
        if not all([self.major, self.minor, self.patch, other.major, other.minor, other.patch]):
            return CompatibilityLevel.UNKNOWN
        
        # Year change = potentially breaking
        if self.major != other.major:
            return CompatibilityLevel.PARTIALLY_COMPATIBLE
        
        # Month change = backward compatible
        if self.minor != other.minor:
            return CompatibilityLevel.BACKWARD_COMPATIBLE
        
        # Day change = fully compatible
        if self.patch != other.patch:
            return CompatibilityLevel.FULLY_COMPATIBLE
        
        return CompatibilityLevel.FULLY_COMPATIBLE
    
    def _check_pep440_compatibility(self, other: 'VersionInfo') -> CompatibilityLevel:
        """Check PEP 440 version compatibility."""
        try:
            # Use packaging library for compatibility checking
            self_ver = pkg_version.parse(self.version_string)
            other_ver = pkg_version.parse(other.version_string)
            
            if self_ver == other_ver:
                return CompatibilityLevel.FULLY_COMPATIBLE
            elif self_ver < other_ver:
                return CompatibilityLevel.BACKWARD_COMPATIBLE
            else:
                return CompatibilityLevel.FORWARD_COMPATIBLE
        except Exception:
            return CompatibilityLevel.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert version info to dictionary."""
        return {
            'version_string': self.version_string,
            'version_type': self.version_type.value,
            'major': self.major,
            'minor': self.minor,
            'patch': self.patch,
            'prerelease': self.prerelease,
            'build': self.build,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'end_of_life': self.end_of_life.isoformat() if self.end_of_life else None,
            'is_stable': self.is_stable,
            'is_supported': self.is_supported,
            'python_versions': self.python_versions,
            'dependencies': self.dependencies,
            'breaking_changes': self.breaking_changes,
            'new_features': self.new_features,
            'bug_fixes': self.bug_fixes,
            'custom_data': self.custom_data
        }
    
    def to_json(self) -> str:
        """Convert version info to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def is_end_of_life(self) -> bool:
        """Check if version has reached end of life."""
        if self.end_of_life:
            return datetime.now() > self.end_of_life
        return False
    
    def get_age(self) -> Optional[timedelta]:
        """Get the age of this version."""
        if self.release_date:
            return datetime.now() - self.release_date
        return None
    
    def get_time_to_eol(self) -> Optional[timedelta]:
        """Get time until end of life."""
        if self.end_of_life:
            time_left = self.end_of_life - datetime.now()
            return time_left if time_left > timedelta(0) else timedelta(0)
        return None


class ComponentVersioning:
    """Component versioning and compatibility management system."""
    
    def __init__(self):
        """Initialize the versioning system."""
        self._version_store: Dict[str, Dict[str, VersionInfo]] = {}  # component_id -> {version -> VersionInfo}
        self._compatibility_matrix: Dict[str, Dict[str, CompatibilityLevel]] = {}  # component_id -> {other_id -> compatibility}
        self._dependency_graph: Dict[str, Set[str]] = {}  # component_id -> {dependency_ids}
        self._version_constraints: Dict[str, Dict[str, str]] = {}  # component_id -> {dependency -> constraint}
        
        # Version policies
        self._auto_update_policy = "conservative"  # conservative, aggressive, manual
        self._compatibility_threshold = CompatibilityLevel.BACKWARD_COMPATIBLE
        self._end_of_life_policy = "warn"  # warn, block, ignore
        
        # Statistics
        self._total_versions = 0
        self._compatibility_checks = 0
        self._dependency_resolutions = 0
    
    def register_version(self, component_id: str, version_info: VersionInfo) -> bool:
        """Register a new version of a component."""
        try:
            if component_id not in self._version_store:
                self._version_store[component_id] = {}
            
            self._version_store[component_id][version_info.version_string] = version_info
            self._total_versions += 1
            
            # Update compatibility matrix
            self._update_compatibility_matrix(component_id, version_info)
            
            return True
        except Exception:
            return False
    
    def get_version(self, component_id: str, version_string: str) -> Optional[VersionInfo]:
        """Get version information for a component."""
        return self._version_store.get(component_id, {}).get(version_string)
    
    def get_latest_version(self, component_id: str, stable_only: bool = True) -> Optional[VersionInfo]:
        """Get the latest version of a component."""
        if component_id not in self._version_store:
            return None
        
        versions = self._version_store[component_id]
        if not versions:
            return None
        
        # Filter by stability if requested
        if stable_only:
            versions = {v: info for v, info in versions.items() if info.is_stable}
        
        if not versions:
            return None
        
        # Sort by version and return latest
        try:
            latest = max(versions.values(), key=lambda v: pkg_version.parse(v.version_string))
            return latest
        except Exception:
            # Fallback to string comparison
            latest = max(versions.values(), key=lambda v: v.version_string)
            return latest
    
    def get_all_versions(self, component_id: str) -> List[VersionInfo]:
        """Get all versions of a component."""
        if component_id not in self._version_store:
            return []
        
        return list(self._version_store[component_id].values())
    
    def check_compatibility(self, component_id: str, version_string: str, 
                          other_component_id: str, other_version_string: str) -> CompatibilityLevel:
        """Check compatibility between two component versions."""
        try:
            version1 = self.get_version(component_id, version_string)
            version2 = self.get_version(other_component_id, other_version_string)
            
            if not version1 or not version2:
                return CompatibilityLevel.UNKNOWN
            
            self._compatibility_checks += 1
            
            # Check direct compatibility
            compatibility = version1.is_compatible_with(version2)
            
            # Cache result
            cache_key = f"{component_id}:{version_string}:{other_component_id}:{other_version_string}"
            if component_id not in self._compatibility_matrix:
                self._compatibility_matrix[component_id] = {}
            self._compatibility_matrix[component_id][cache_key] = compatibility
            
            return compatibility
        except Exception:
            return CompatibilityLevel.UNKNOWN
    
    def resolve_dependencies(self, component_id: str, version_string: str) -> Dict[str, str]:
        """Resolve dependencies for a component version."""
        try:
            version_info = self.get_version(component_id, version_string)
            if not version_info:
                return {}
            
            self._dependency_resolutions += 1
            
            resolved_deps = {}
            
            for dep_name, dep_constraint in version_info.dependencies.items():
                # Parse constraint (e.g., ">=1.0.0,<2.0.0")
                try:
                    spec = SpecifierSet(dep_constraint)
                    
                    # Find compatible versions
                    compatible_versions = []
                    for other_id, versions in self._version_store.items():
                        if other_id == dep_name:
                            for ver_string, ver_info in versions.items():
                                try:
                                    ver = pkg_version.parse(ver_string)
                                    if spec.contains(ver):
                                        compatible_versions.append((ver_string, ver_info))
                                except Exception:
                                    continue
                    
                    # Select best version
                    if compatible_versions:
                        # Prefer stable versions
                        stable_versions = [v for v in compatible_versions if v[1].is_stable]
                        if stable_versions:
                            best_version = max(stable_versions, key=lambda v: pkg_version.parse(v[0]))
                        else:
                            best_version = max(compatible_versions, key=lambda v: pkg_version.parse(v[0]))
                        
                        resolved_deps[dep_name] = best_version[0]
                    
                except Exception:
                    # Fallback to exact version if constraint parsing fails
                    resolved_deps[dep_name] = dep_constraint
            
            return resolved_deps
        except Exception:
            return {}
    
    def get_compatibility_report(self, component_id: str, version_string: str) -> Dict[str, Any]:
        """Get a comprehensive compatibility report for a component version."""
        version_info = self.get_version(component_id, version_string)
        if not version_info:
            return {}
        
        report = {
            'component_id': component_id,
            'version': version_string,
            'version_info': version_info.to_dict(),
            'compatibility': {},
            'dependencies': {},
            'recommendations': []
        }
        
        # Check compatibility with other components
        for other_id, versions in self._version_store.items():
            if other_id == component_id:
                continue
            
            other_latest = self.get_latest_version(other_id, stable_only=True)
            if other_latest:
                compatibility = self.check_compatibility(
                    component_id, version_string,
                    other_id, other_latest.version_string
                )
                report['compatibility'][other_id] = {
                    'version': other_latest.version_string,
                    'level': compatibility.value,
                    'status': 'compatible' if compatibility != CompatibilityLevel.INCOMPATIBLE else 'incompatible'
                }
        
        # Resolve dependencies
        report['dependencies'] = self.resolve_dependencies(component_id, version_string)
        
        # Generate recommendations
        recommendations = []
        
        # Check for end of life
        if version_info.is_end_of_life():
            recommendations.append({
                'type': 'warning',
                'message': f'Version {version_string} has reached end of life',
                'action': 'Consider upgrading to a supported version'
            })
        
        # Check for unstable versions
        if not version_info.is_stable:
            recommendations.append({
                'type': 'info',
                'message': f'Version {version_string} is not stable',
                'action': 'Consider using a stable release for production'
            })
        
        # Check for outdated dependencies
        for dep_name, dep_version in report['dependencies'].items():
            dep_info = self.get_version(dep_name, dep_version)
            if dep_info and dep_info.is_end_of_life():
                recommendations.append({
                    'type': 'warning',
                    'message': f'Dependency {dep_name} version {dep_version} has reached end of life',
                    'action': f'Upgrade {dep_name} to a supported version'
                })
        
        report['recommendations'] = recommendations
        
        return report
    
    def get_version_summary(self) -> Dict[str, Any]:
        """Get a summary of all version information."""
        summary = {
            'total_components': len(self._version_store),
            'total_versions': self._total_versions,
            'compatibility_checks': self._compatibility_checks,
            'dependency_resolutions': self._dependency_resolutions,
            'version_types': {},
            'stability_distribution': {'stable': 0, 'unstable': 0},
            'end_of_life_versions': 0,
            'recent_releases': 0
        }
        
        now = datetime.now()
        recent_threshold = now - timedelta(days=30)
        
        for component_id, versions in self._version_store.items():
            for version_string, version_info in versions.items():
                # Version types
                vtype = version_info.version_type.value
                summary['version_types'][vtype] = summary['version_types'].get(vtype, 0) + 1
                
                # Stability
                if version_info.is_stable:
                    summary['stability_distribution']['stable'] += 1
                else:
                    summary['stability_distribution']['unstable'] += 1
                
                # End of life
                if version_info.is_end_of_life():
                    summary['end_of_life_versions'] += 1
                
                # Recent releases
                if version_info.release_date and version_info.release_date > recent_threshold:
                    summary['recent_releases'] += 1
        
        return summary
    
    def _update_compatibility_matrix(self, component_id: str, version_info: VersionInfo):
        """Update compatibility matrix for a new version."""
        # This would be called when registering new versions
        # For now, we'll just ensure the matrix structure exists
        if component_id not in self._compatibility_matrix:
            self._compatibility_matrix[component_id] = {}
    
    def set_version_policy(self, auto_update: str = "conservative", 
                          compatibility_threshold: CompatibilityLevel = CompatibilityLevel.BACKWARD_COMPATIBLE,
                          end_of_life_policy: str = "warn"):
        """Set versioning policies."""
        self._auto_update_policy = auto_update
        self._compatibility_threshold = compatibility_threshold
        self._end_of_life_policy = end_of_life_policy
    
    def export_version_data(self, format_type: str = "json") -> Union[str, Dict[str, Any]]:
        """Export version data in specified format."""
        if format_type.lower() == "json":
            return json.dumps({
                component_id: {
                    version: info.to_dict()
                    for version, info in versions.items()
                }
                for component_id, versions in self._version_store.items()
            }, indent=2)
        elif format_type.lower() == "dict":
            return {
                component_id: {
                    version: info.to_dict()
                    for version, info in versions.items()
                }
                for component_id, versions in self._version_store.items()
            }
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def import_version_data(self, data: Union[str, Dict[str, Any]], format_type: str = "json") -> bool:
        """Import version data from external source."""
        try:
            if format_type.lower() == "json" and isinstance(data, str):
                data = json.loads(data)
            
            if not isinstance(data, dict):
                return False
            
            for component_id, versions in data.items():
                for version_string, version_dict in versions.items():
                    # Convert dict to VersionInfo
                    version_info = VersionInfo(**version_dict)
                    self.register_version(component_id, version_info)
            
            return True
        except Exception:
            return False
