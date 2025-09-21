"""
Plugin Types for Hydra-Logger

This module provides comprehensive type definitions for plugins,
including configuration, state management, metadata, and compatibility
tracking. It supports all aspects of plugin lifecycle and management.

FEATURES:
- PluginConfig: Plugin configuration and settings
- PluginState: Current plugin state and status
- PluginMetadata: Plugin information and documentation
- PluginCompatibility: Compatibility checking and validation

PLUGIN CONFIGURATION:
- Core settings: ID, type, name, version, enabled status
- Plugin settings: Custom configuration parameters
- Dependencies: Required and optional dependencies, conflicts
- Performance settings: Caching, optimization, execution time limits
- Security settings: Sandboxing, authentication, operation restrictions

PLUGIN STATE:
- Status tracking: Initializing, active, paused, stopped, error, disabled
- Operational flags: Initialized, active, paused, stopped, error, disabled
- Error information: Error messages, counts, timestamps, stack traces
- Performance state: Memory usage, CPU usage, execution count
- Lifecycle information: Start time, last activity, uptime

PLUGIN METADATA:
- Basic information: Name, version, description
- Author information: Author, email, URL
- Project information: Project URL, documentation, source code
- Classification: Category, tags, keywords
- Technical information: Python version, platform, architecture
- Licensing: License type and URL
- Timestamps: Created, updated, published dates

PLUGIN COMPATIBILITY:
- Version compatibility: Hydra-Logger version, Python version
- Platform compatibility: Supported platforms and architectures
- Dependency compatibility: Required and optional packages
- Feature compatibility: Required and optional features
- Compatibility scoring: 0-100 compatibility score with issues and warnings

USAGE:
    from hydra_logger.types import (
        PluginConfig, PluginState, PluginMetadata, PluginCompatibility
    )
    
    # Create plugin configuration
    config = PluginConfig(
        plugin_type="analytics",
        name="Performance Monitor",
        version="1.0.0",
        enabled=True,
        settings={"interval": 60, "threshold": 0.8}
    )
    
    # Create plugin state
    state = PluginState(plugin_id=config.plugin_id)
    state.set_status("active")
    
    # Create plugin metadata
    metadata = PluginMetadata(
        plugin_id=config.plugin_id,
        name=config.name,
        version=config.version,
        description="Performance monitoring plugin",
        author="Hydra-Logger Team",
        category="monitoring"
    )
    
    # Create plugin compatibility
    compatibility = PluginCompatibility(
        plugin_id=config.plugin_id,
        hydra_logger_version="2.0.0",
        python_version_min="3.8"
    )
    
    # Check compatibility
    if compatibility.is_compatible:
        print("Plugin is compatible")
    else:
        print(f"Compatibility issues: {compatibility.compatibility_issues}")
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List, Callable
from datetime import datetime
import time


@dataclass
class PluginConfig:
    """Base configuration for plugins."""
    
    # Core configuration
    plugin_id: str = field(default_factory=lambda: f"plugin_{int(time.time() * 1000)}")
    plugin_type: str = "unknown"
    name: str = "Unknown Plugin"
    version: str = "1.0.0"
    enabled: bool = True
    
    # Plugin settings
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    required_dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    
    # Performance settings
    enable_caching: bool = True
    cache_size: int = 1000
    enable_optimization: bool = True
    max_execution_time: Optional[float] = None
    
    # Security settings
    enable_sandboxing: bool = False
    require_authentication: bool = False
    allowed_operations: List[str] = field(default_factory=list)
    restricted_operations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize plugin config after creation."""
        if not self.plugin_id:
            self.plugin_id = f"plugin_{int(time.time() * 1000)}"
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a plugin setting."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a plugin setting."""
        self.settings[key] = value
    
    def has_setting(self, key: str) -> bool:
        """Check if a setting exists."""
        return key in self.settings
    
    def remove_setting(self, key: str) -> Any:
        """Remove a setting and return its value."""
        return self.settings.pop(key, None)
    
    def add_dependency(self, dependency: str, required: bool = True) -> None:
        """Add a dependency."""
        if required and dependency not in self.required_dependencies:
            self.required_dependencies.append(dependency)
        elif not required and dependency not in self.optional_dependencies:
            self.optional_dependencies.append(dependency)
    
    def remove_dependency(self, dependency: str) -> None:
        """Remove a dependency."""
        if dependency in self.required_dependencies:
            self.required_dependencies.remove(dependency)
        if dependency in self.optional_dependencies:
            self.optional_dependencies.remove(dependency)
    
    def add_conflict(self, conflicting_plugin: str) -> None:
        """Add a conflicting plugin."""
        if conflicting_plugin not in self.conflicts:
            self.conflicts.append(conflicting_plugin)
    
    def remove_conflict(self, conflicting_plugin: str) -> None:
        """Remove a conflicting plugin."""
        if conflicting_plugin in self.conflicts:
            self.conflicts.remove(conflicting_plugin)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'plugin_id': self.plugin_id,
            'plugin_type': self.plugin_type,
            'name': self.name,
            'version': self.version,
            'enabled': self.enabled,
            'settings': self.settings,
            'required_dependencies': self.required_dependencies,
            'optional_dependencies': self.optional_dependencies,
            'conflicts': self.conflicts,
            'enable_caching': self.enable_caching,
            'cache_size': self.cache_size,
            'enable_optimization': self.enable_optimization,
            'max_execution_time': self.max_execution_time,
            'enable_sandboxing': self.enable_sandboxing,
            'require_authentication': self.require_authentication,
            'allowed_operations': self.allowed_operations,
            'restricted_operations': self.restricted_operations
        }


@dataclass
class PluginState:
    """Current state of a plugin."""
    
    # State information
    plugin_id: str
    status: str = "initializing"  # initializing, active, paused, stopped, error, disabled
    last_status_change: float = field(default_factory=time.time)
    
    # Operational state
    is_initialized: bool = False
    is_active: bool = False
    is_paused: bool = False
    is_stopped: bool = False
    has_error: bool = False
    is_disabled: bool = False
    
    # Error information
    error_message: Optional[str] = None
    error_count: int = 0
    last_error_time: Optional[float] = None
    error_stack_trace: Optional[str] = None
    
    # Performance state
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    execution_count: int = 0
    
    # Lifecycle information
    start_time: Optional[float] = None
    last_activity: Optional[float] = None
    uptime: float = 0.0
    
    def __post_init__(self):
        """Initialize plugin state after creation."""
        self.last_status_change = time.time()
    
    def set_status(self, status: str) -> None:
        """Set the plugin status."""
        if status != self.status:
            self.status = status
            self.last_status_change = time.time()
            
            # Update boolean flags
            self.is_active = status == "active"
            self.is_paused = status == "paused"
            self.is_stopped = status == "stopped"
            self.has_error = status == "error"
            self.is_disabled = status == "disabled"
            
            # Update timestamps
            if status == "active" and self.start_time is None:
                self.start_time = time.time()
            if status in ["active", "paused"]:
                self.last_activity = time.time()
    
    def set_error(self, error_message: str, stack_trace: Optional[str] = None) -> None:
        """Set an error state."""
        self.set_status("error")
        self.error_message = error_message
        self.error_count += 1
        self.last_error_time = time.time()
        self.error_stack_trace = stack_trace
    
    def clear_error(self) -> None:
        """Clear error state."""
        self.error_message = None
        self.error_stack_trace = None
        self.has_error = False
        if self.status == "error":
            self.set_status("stopped")
    
    def update_activity(self) -> None:
        """Update last activity time."""
        self.last_activity = time.time()
        if self.start_time:
            self.uptime = time.time() - self.start_time
    
    def increment_execution(self) -> None:
        """Increment execution count."""
        self.execution_count += 1
        self.update_activity()
    
    def update_performance(self, memory_usage: Optional[int] = None, 
                          cpu_usage: Optional[float] = None) -> None:
        """Update performance metrics."""
        if memory_usage is not None:
            self.memory_usage = memory_usage
        if cpu_usage is not None:
            self.cpu_usage = cpu_usage
        self.update_activity()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            'plugin_id': self.plugin_id,
            'status': self.status,
            'last_status_change': self.last_status_change,
            'is_initialized': self.is_initialized,
            'is_active': self.is_active,
            'is_paused': self.is_paused,
            'is_stopped': self.is_stopped,
            'has_error': self.has_error,
            'is_disabled': self.is_disabled,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'last_error_time': self.last_error_time,
            'error_stack_trace': self.error_stack_trace,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'execution_count': self.execution_count,
            'start_time': self.start_time,
            'last_activity': self.last_activity,
            'uptime': self.uptime
        }


@dataclass
class PluginMetadata:
    """Metadata information for a plugin."""
    
    # Basic information
    plugin_id: str
    name: str
    version: str
    description: str = ""
    
    # Author information
    author: Optional[str] = None
    author_email: Optional[str] = None
    author_url: Optional[str] = None
    
    # Project information
    project_url: Optional[str] = None
    documentation_url: Optional[str] = None
    source_code_url: Optional[str] = None
    
    # Classification
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Technical information
    python_version: Optional[str] = None
    platform: Optional[str] = None
    architecture: Optional[str] = None
    
    # Licensing
    license: Optional[str] = None
    license_url: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize metadata after creation."""
        self.updated_at = self.created_at
    
    def add_tag(self, tag: str) -> None:
        """Add a tag."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def add_keyword(self, keyword: str) -> None:
        """Add a keyword."""
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            self.updated_at = datetime.now()
    
    def remove_keyword(self, keyword: str) -> None:
        """Remove a keyword."""
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            self.updated_at = datetime.now()
    
    def set_published(self) -> None:
        """Mark plugin as published."""
        self.published_at = datetime.now()
        self.updated_at = self.published_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'plugin_id': self.plugin_id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'author_email': self.author_email,
            'author_url': self.author_url,
            'project_url': self.project_url,
            'documentation_url': self.documentation_url,
            'source_code_url': self.source_code_url,
            'category': self.category,
            'tags': self.tags,
            'keywords': self.keywords,
            'python_version': self.python_version,
            'platform': self.platform,
            'architecture': self.architecture,
            'license': self.license,
            'license_url': self.license_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None
        }


@dataclass
class PluginCompatibility:
    """Compatibility information for a plugin."""
    
    # Core compatibility
    plugin_id: str
    hydra_logger_version: str = "2.0.0"
    python_version_min: str = "3.8"
    python_version_max: Optional[str] = None
    
    # Platform compatibility
    supported_platforms: List[str] = field(default_factory=lambda: ["linux", "windows", "macos"])
    supported_architectures: List[str] = field(default_factory=lambda: ["x86_64", "arm64"])
    
    # Dependency compatibility
    required_packages: Dict[str, str] = field(default_factory=dict)
    optional_packages: Dict[str, str] = field(default_factory=dict)
    conflicting_packages: List[str] = field(default_factory=list)
    
    # Feature compatibility
    required_features: List[str] = field(default_factory=list)
    optional_features: List[str] = field(default_factory=list)
    incompatible_features: List[str] = field(default_factory=list)
    
    # Compatibility status
    is_compatible: bool = True
    compatibility_score: float = 100.0  # 0-100 scale
    compatibility_issues: List[str] = field(default_factory=list)
    compatibility_warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize compatibility after creation."""
        self._check_compatibility()
    
    def _check_compatibility(self) -> None:
        """Check plugin compatibility."""
        self.compatibility_issues.clear()
        self.compatibility_warnings.clear()
        self.compatibility_score = 100.0
        
        # Check Python version
        import sys
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        if not self._version_compatible(current_version, self.python_version_min, self.python_version_max):
            self.compatibility_issues.append(f"Python version {current_version} not compatible")
            self.compatibility_score -= 30
        
        # Check platform
        import platform
        current_platform = platform.system().lower()
        if current_platform not in self.supported_platforms:
            self.compatibility_warnings.append(f"Platform {current_platform} not explicitly supported")
            self.compatibility_score -= 10
        
        # Check architecture
        current_arch = platform.machine().lower()
        if current_arch not in self.supported_architectures:
            self.compatibility_warnings.append(f"Architecture {current_arch} not explicitly supported")
            self.compatibility_score -= 10
        
        # Check required packages
        for package, version in self.required_packages.items():
            if not self._package_available(package, version):
                self.compatibility_issues.append(f"Required package {package} {version} not available")
                self.compatibility_score -= 20
        
        # Ensure score is within bounds
        self.compatibility_score = max(0.0, min(100.0, self.compatibility_score))
        self.is_compatible = self.compatibility_score >= 70.0
    
    def _version_compatible(self, current: str, min_version: str, max_version: Optional[str]) -> bool:
        """Check if version is compatible."""
        from packaging import version
        
        try:
            current_ver = version.parse(current)
            min_ver = version.parse(min_version)
            
            if current_ver < min_ver:
                return False
            
            if max_version:
                max_ver = version.parse(max_version)
                if current_ver > max_ver:
                    return False
            
            return True
        except Exception:
            return False
    
    def _package_available(self, package: str, required_version: str) -> bool:
        """Check if package is available."""
        try:
            import importlib
            importlib.import_module(package)
            return True
        except ImportError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert compatibility to dictionary."""
        return {
            'plugin_id': self.plugin_id,
            'hydra_logger_version': self.hydra_logger_version,
            'python_version_min': self.python_version_min,
            'python_version_max': self.python_version_max,
            'supported_platforms': self.supported_platforms,
            'supported_architectures': self.supported_architectures,
            'required_packages': self.required_packages,
            'optional_packages': self.optional_packages,
            'conflicting_packages': self.conflicting_packages,
            'required_features': self.required_features,
            'optional_features': self.optional_features,
            'incompatible_features': self.incompatible_features,
            'is_compatible': self.is_compatible,
            'compatibility_score': self.compatibility_score,
            'compatibility_issues': self.compatibility_issues,
            'compatibility_warnings': self.compatibility_warnings
        }


# Convenience functions
def create_plugin_config(plugin_type: str, name: str, **kwargs) -> PluginConfig:
    """Create a new plugin configuration."""
    return PluginConfig(plugin_type=plugin_type, name=name, **kwargs)


def create_plugin_state(plugin_id: str) -> PluginState:
    """Create new plugin state."""
    return PluginState(plugin_id=plugin_id)


def create_plugin_metadata(plugin_id: str, name: str, version: str, **kwargs) -> PluginMetadata:
    """Create new plugin metadata."""
    return PluginMetadata(plugin_id=plugin_id, name=name, version=version, **kwargs)


def create_plugin_compatibility(plugin_id: str, **kwargs) -> PluginCompatibility:
    """Create new plugin compatibility."""
    return PluginCompatibility(plugin_id=plugin_id, **kwargs)


# Export the main classes and functions
__all__ = [
    "PluginConfig",
    "PluginState",
    "PluginMetadata",
    "PluginCompatibility",
    "create_plugin_config",
    "create_plugin_state",
    "create_plugin_metadata",
    "create_plugin_compatibility"
]
