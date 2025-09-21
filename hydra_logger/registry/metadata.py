"""
Registry Metadata Management System for Hydra-Logger

This module provides comprehensive metadata management for registered components
including rich metadata storage, search capabilities, indexing, and analytics.
It enables detailed component information tracking and analysis.

FEATURES:
- Rich component metadata storage
- Metadata search and filtering
- Component indexing and categorization
- Performance and usage tracking
- Security information management
- Metadata export/import
- Analytics and reporting

METADATA TYPES:
- Component Info: Basic component information
- Performance: Performance metrics and data
- Security: Security-related information
- Compatibility: Compatibility information
- Usage: Usage statistics and patterns
- Custom: Custom metadata fields

METADATA PRIORITY LEVELS:
- Critical: Critical metadata
- High: High priority metadata
- Medium: Medium priority metadata
- Low: Low priority metadata
- Info: Informational metadata

USAGE:
    from hydra_logger.registry import RegistryMetadata, ComponentMetadata, MetadataPriority
    
    # Create metadata manager
    metadata_manager = RegistryMetadata()
    
    # Create component metadata
    component_metadata = ComponentMetadata(
        component_id="my_component",
        component_type="logger",
        name="My Logger",
        description="A custom logger component",
        version="1.0.0",
        author="Developer",
        priority=MetadataPriority.HIGH,
        tags={"logging", "custom"},
        capabilities={"async", "colored"}
    )
    
    # Add metadata
    metadata_manager.add_metadata("my_component", component_metadata)
    
    # Search metadata
    results = metadata_manager.search_metadata({"tags": "logging"})
    
    # Update metadata
    metadata_manager.update_metadata("my_component", {"version": "1.1.0"})
    
    # Get metadata summary
    summary = metadata_manager.get_metadata_summary()
"""

import time
import json
import hashlib
from typing import Any, Dict, List, Optional, Union, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict


class MetadataType(Enum):
    """Types of metadata that can be stored."""
    COMPONENT_INFO = "component_info"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"
    USAGE = "usage"
    CUSTOM = "custom"


class MetadataPriority(Enum):
    """Metadata priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComponentMetadata:
    """Rich metadata for a registered component."""
    
    # Basic information
    component_id: str
    component_type: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    license: str = ""
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    
    # Classification
    tags: Set[str] = field(default_factory=set)
    categories: Set[str] = field(default_factory=set)
    priority: MetadataPriority = MetadataPriority.MEDIUM
    
    # Technical details
    dependencies: Set[str] = field(default_factory=set)
    requirements: Dict[str, Any] = field(default_factory=dict)
    capabilities: Set[str] = field(default_factory=set)
    limitations: Set[str] = field(default_factory=set)
    
    # Performance metrics
    performance_score: Optional[float] = None
    memory_usage: Optional[int] = None
    cpu_usage: Optional[float] = None
    response_time: Optional[float] = None
    
    # Security information
    security_level: str = "standard"
    permissions: Set[str] = field(default_factory=set)
    vulnerabilities: List[str] = field(default_factory=list)
    
    # Usage statistics
    usage_count: int = 0
    error_count: int = 0
    success_rate: Optional[float] = None
    
    # Custom metadata
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if isinstance(self.tags, list):
            self.tags = set(self.tags)
        if isinstance(self.categories, list):
            self.categories = set(self.categories)
        if isinstance(self.dependencies, list):
            self.dependencies = set(self.dependencies)
        if isinstance(self.capabilities, list):
            self.capabilities = set(self.capabilities)
        if isinstance(self.limitations, list):
            self.limitations = set(self.limitations)
        if isinstance(self.permissions, list):
            self.permissions = set(self.permissions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.last_accessed:
            data['last_accessed'] = self.last_accessed.isoformat()
        return data
    
    def to_json(self) -> str:
        """Convert metadata to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def update_usage(self, success: bool = True):
        """Update usage statistics."""
        self.usage_count += 1
        if not success:
            self.error_count += 1
        
        if self.usage_count > 0:
            self.success_rate = (self.usage_count - self.error_count) / self.usage_count
        
        self.last_accessed = datetime.now()
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str):
        """Add a tag to the component."""
        self.tags.add(tag)
        self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str):
        """Remove a tag from the component."""
        self.tags.discard(tag)
        self.updated_at = datetime.now()
    
    def add_category(self, category: str):
        """Add a category to the component."""
        self.categories.add(category)
        self.updated_at = datetime.now()
    
    def remove_category(self, category: str):
        """Remove a category from the component."""
        self.categories.discard(category)
        self.updated_at = datetime.now()
    
    def set_performance_metrics(self, score: float, memory: Optional[int] = None, 
                               cpu: Optional[float] = None, response_time: Optional[float] = None):
        """Set performance metrics."""
        self.performance_score = score
        if memory is not None:
            self.memory_usage = memory
        if cpu is not None:
            self.cpu_usage = cpu
        if response_time is not None:
            self.response_time = response_time
        self.updated_at = datetime.now()
    
    def add_vulnerability(self, vulnerability: str):
        """Add a security vulnerability."""
        if vulnerability not in self.vulnerabilities:
            self.vulnerabilities.append(vulnerability)
            self.updated_at = datetime.now()
    
    def remove_vulnerability(self, vulnerability: str):
        """Remove a security vulnerability."""
        if vulnerability in self.vulnerabilities:
            self.vulnerabilities.remove(vulnerability)
            self.updated_at = datetime.now()
    
    def is_healthy(self) -> bool:
        """Check if component is healthy based on metadata."""
        if self.error_count > 0 and self.usage_count > 0:
            if self.success_rate < 0.8:  # Less than 80% success rate
                return False
        
        if self.vulnerabilities:
            return False
        
        if self.performance_score is not None and self.performance_score < 0.5:
            return False
        
        return True
    
    def get_age(self) -> timedelta:
        """Get the age of the component."""
        return datetime.now() - self.created_at
    
    def get_last_activity(self) -> timedelta:
        """Get time since last activity."""
        if self.last_accessed:
            return datetime.now() - self.last_accessed
        return datetime.now() - self.created_at


class RegistryMetadata:
    """Registry metadata management system."""
    
    def __init__(self):
        """Initialize the metadata manager."""
        self._metadata_store: Dict[str, ComponentMetadata] = {}
        self._metadata_index: Dict[str, Set[str]] = defaultdict(set)
        self._metadata_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        
    def add_metadata(self, component_id: str, metadata: ComponentMetadata) -> bool:
        """Add metadata for a component."""
        try:
            self._metadata_store[component_id] = metadata
            
            # Update indices
            self._update_indices(component_id, metadata)
            
            # Clear cache
            self._clear_cache()
            
            return True
        except Exception:
            return False
    
    def get_metadata(self, component_id: str) -> Optional[ComponentMetadata]:
        """Get metadata for a component."""
        return self._metadata_store.get(component_id)
    
    def update_metadata(self, component_id: str, updates: Dict[str, Any]) -> bool:
        """Update metadata for a component."""
        if component_id not in self._metadata_store:
            return False
        
        try:
            metadata = self._metadata_store[component_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
            
            metadata.updated_at = datetime.now()
            
            # Update indices
            self._update_indices(component_id, metadata)
            
            # Clear cache
            self._clear_cache()
            
            return True
        except Exception:
            return False
    
    def remove_metadata(self, component_id: str) -> bool:
        """Remove metadata for a component."""
        if component_id not in self._metadata_store:
            return False
        
        try:
            metadata = self._metadata_store[component_id]
            
            # Remove from indices
            self._remove_from_indices(component_id, metadata)
            
            # Remove from store
            del self._metadata_store[component_id]
            
            # Clear cache
            self._clear_cache()
            
            return True
        except Exception:
            return False
    
    def search_metadata(self, query: Dict[str, Any]) -> List[str]:
        """Search for components based on metadata criteria."""
        cache_key = f"search_{hashlib.md5(json.dumps(query, sort_keys=True).encode()).hexdigest()}"
        
        # Check cache
        if cache_key in self._metadata_cache:
            cache_entry = self._metadata_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                return cache_entry['results']
        
        results = []
        
        for component_id, metadata in self._metadata_store.items():
            if self._matches_criteria(metadata, query):
                results.append(component_id)
        
        # Cache results
        self._metadata_cache[cache_key] = {
            'timestamp': time.time(),
            'results': results
        }
        
        return results
    
    def get_metadata_summary(self) -> Dict[str, Any]:
        """Get a summary of all metadata."""
        if 'summary' in self._metadata_cache:
            cache_entry = self._metadata_cache['summary']
            if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                return cache_entry['data']
        
        summary = {
            'total_components': len(self._metadata_store),
            'component_types': defaultdict(int),
            'categories': defaultdict(int),
            'tags': defaultdict(int),
            'performance_distribution': defaultdict(int),
            'security_levels': defaultdict(int),
            'recent_activity': 0,
            'health_status': {'healthy': 0, 'unhealthy': 0}
        }
        
        now = datetime.now()
        recent_threshold = now - timedelta(hours=24)
        
        for metadata in self._metadata_store.values():
            # Component types
            summary['component_types'][metadata.component_type] += 1
            
            # Categories
            for category in metadata.categories:
                summary['categories'][category] += 1
            
            # Tags
            for tag in metadata.tags:
                summary['tags'][tag] += 1
            
            # Performance distribution
            if metadata.performance_score is not None:
                if metadata.performance_score >= 0.9:
                    summary['performance_distribution']['excellent'] += 1
                elif metadata.performance_score >= 0.7:
                    summary['performance_distribution']['good'] += 1
                elif metadata.performance_score >= 0.5:
                    summary['performance_distribution']['fair'] += 1
                else:
                    summary['performance_distribution']['poor'] += 1
            
            # Security levels
            summary['security_levels'][metadata.security_level] += 1
            
            # Recent activity
            if metadata.last_accessed and metadata.last_accessed > recent_threshold:
                summary['recent_activity'] += 1
            
            # Health status
            if metadata.is_healthy():
                summary['health_status']['healthy'] += 1
            else:
                summary['health_status']['unhealthy'] += 1
        
        # Cache summary
        self._metadata_cache['summary'] = {
            'timestamp': time.time(),
            'data': summary
        }
        
        return summary
    
    def export_metadata(self, format_type: str = "json") -> Union[str, Dict[str, Any]]:
        """Export all metadata in specified format."""
        if format_type.lower() == "json":
            return json.dumps({
                component_id: metadata.to_dict()
                for component_id, metadata in self._metadata_store.items()
            }, indent=2)
        elif format_type.lower() == "dict":
            return {
                component_id: metadata.to_dict()
                for component_id, metadata in self._metadata_store.items()
            }
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def import_metadata(self, data: Union[str, Dict[str, Any]], format_type: str = "json") -> bool:
        """Import metadata from external source."""
        try:
            if format_type.lower() == "json" and isinstance(data, str):
                data = json.loads(data)
            
            if not isinstance(data, dict):
                return False
            
            for component_id, metadata_dict in data.items():
                # Convert dict to ComponentMetadata
                metadata = ComponentMetadata(**metadata_dict)
                self.add_metadata(component_id, metadata)
            
            return True
        except Exception:
            return False
    
    def _update_indices(self, component_id: str, metadata: ComponentMetadata):
        """Update search indices for a component."""
        # Type index
        self._metadata_index[f"type:{metadata.component_type}"].add(component_id)
        
        # Category indices
        for category in metadata.categories:
            self._metadata_index[f"category:{category}"].add(component_id)
        
        # Tag indices
        for tag in metadata.tags:
            self._metadata_index[f"tag:{tag}"].add(component_id)
        
        # Priority index
        self._metadata_index[f"priority:{metadata.priority.value}"].add(component_id)
        
        # Security level index
        self._metadata_index[f"security:{metadata.security_level}"].add(component_id)
    
    def _remove_from_indices(self, component_id: str, metadata: ComponentMetadata):
        """Remove component from search indices."""
        # Type index
        self._metadata_index[f"type:{metadata.component_type}"].discard(component_id)
        
        # Category indices
        for category in metadata.categories:
            self._metadata_index[f"category:{category}"].discard(component_id)
        
        # Tag indices
        for tag in metadata.tags:
            self._metadata_index[f"tag:{tag}"].discard(component_id)
        
        # Priority index
        self._metadata_index[f"priority:{metadata.priority.value}"].discard(component_id)
        
        # Security level index
        self._metadata_index[f"security:{metadata.security_level}"].discard(component_id)
    
    def _matches_criteria(self, metadata: ComponentMetadata, query: Dict[str, Any]) -> bool:
        """Check if metadata matches search criteria."""
        for key, value in query.items():
            if key == "component_type" and metadata.component_type != value:
                return False
            elif key == "category" and value not in metadata.categories:
                return False
            elif key == "tag" and value not in metadata.tags:
                return False
            elif key == "priority" and metadata.priority != value:
                return False
            elif key == "security_level" and metadata.security_level != value:
                return False
            elif key == "healthy" and metadata.is_healthy() != value:
                return False
            elif key == "min_performance" and metadata.performance_score is not None:
                if metadata.performance_score < value:
                    return False
            elif key == "max_performance" and metadata.performance_score is not None:
                if metadata.performance_score > value:
                    return False
        
        return True
    
    def _clear_cache(self):
        """Clear the metadata cache."""
        self._metadata_cache.clear()
