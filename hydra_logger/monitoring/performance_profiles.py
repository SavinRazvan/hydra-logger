"""
Performance Profile Management Component for Hydra-Logger

This module provides dynamic performance profile management with predefined
and custom profiles for different use cases. It enables automatic profile
switching based on workload conditions and system requirements.

FEATURES:
- Predefined performance profiles (development, testing, production, etc.)
- Custom profile creation and management
- Dynamic profile switching based on conditions
- Profile export and import capabilities
- Profile usage analytics and recommendations

USAGE:
    from hydra_logger.monitoring import PerformanceProfileManager, ProfileType
    
    # Create profile manager
    manager = PerformanceProfileManager(enabled=True)
    
    # Start monitoring
    manager.start_monitoring()
    
    # Switch to production profile
    manager.switch_profile(ProfileType.PRODUCTION, reason="deployment")
    
    # Create custom profile
    manager.create_custom_profile(
        name="high_throughput",
        config={"buffer_size": 10000, "worker_count": 8},
        description="High throughput configuration"
    )
    
    # Get current profile
    current = manager.get_current_profile()
"""

import time
import threading
import json
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
from enum import Enum
from ..interfaces.monitor import MonitorInterface


class ProfileType(Enum):
    """Types of performance profiles."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_PERFORMANCE = "high_performance"
    LOW_LATENCY = "low_latency"
    MEMORY_EFFICIENT = "memory_efficient"
    CUSTOM = "custom"


class ProfilePriority(Enum):
    """Profile priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceProfileManager(MonitorInterface):
    """Real performance profile management component for dynamic profile switching."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        
        # Built-in performance profiles
        self._builtin_profiles = {
            ProfileType.DEVELOPMENT: {
                "name": "Development",
                "description": "Optimized for development and debugging",
                "priority": ProfilePriority.LOW,
                "config": {
                    "buffer_size": 1000,
                    "worker_count": 2,
                    "flush_interval": 2.0,
                    "compression": False,
                    "async_io": False,
                    "batch_processing": False,
                    "log_level": "DEBUG",
                    "enable_profiling": True,
                    "enable_debugging": True
                }
            },
            ProfileType.TESTING: {
                "name": "Testing",
                "description": "Optimized for testing and validation",
                "priority": ProfilePriority.LOW,
                "config": {
                    "buffer_size": 500,
                    "worker_count": 1,
                    "flush_interval": 1.0,
                    "compression": False,
                    "async_io": False,
                    "batch_processing": False,
                    "log_level": "INFO",
                    "enable_profiling": True,
                    "enable_debugging": False
                }
            },
            ProfileType.STAGING: {
                "name": "Staging",
                "description": "Optimized for staging and pre-production",
                "priority": ProfilePriority.NORMAL,
                "config": {
                    "buffer_size": 2000,
                    "worker_count": 4,
                    "flush_interval": 1.0,
                    "compression": True,
                    "async_io": True,
                    "batch_processing": True,
                    "log_level": "INFO",
                    "enable_profiling": False,
                    "enable_debugging": False
                }
            },
            ProfileType.PRODUCTION: {
                "name": "Production",
                "description": "Optimized for production workloads",
                "priority": ProfilePriority.HIGH,
                "config": {
                    "buffer_size": 5000,
                    "worker_count": 8,
                    "flush_interval": 0.5,
                    "compression": True,
                    "async_io": True,
                    "batch_processing": True,
                    "log_level": "WARNING",
                    "enable_profiling": False,
                    "enable_debugging": False
                }
            },
            ProfileType.HIGH_PERFORMANCE: {
                "name": "High Performance",
                "description": "Maximum performance configuration",
                "priority": ProfilePriority.HIGH,
                "config": {
                    "buffer_size": 10000,
                    "worker_count": 16,
                    "flush_interval": 0.1,
                    "compression": False,
                    "async_io": True,
                    "batch_processing": True,
                    "log_level": "ERROR",
                    "enable_profiling": False,
                    "enable_debugging": False
                }
            },
            ProfileType.LOW_LATENCY: {
                "name": "Low Latency",
                "description": "Optimized for minimal latency",
                "priority": ProfilePriority.HIGH,
                "config": {
                    "buffer_size": 500,
                    "worker_count": 12,
                    "flush_interval": 0.05,
                    "compression": False,
                    "async_io": True,
                    "batch_processing": False,
                    "log_level": "WARNING",
                    "enable_profiling": False,
                    "enable_debugging": False
                }
            },
            ProfileType.MEMORY_EFFICIENT: {
                "name": "Memory Efficient",
                "description": "Optimized for minimal memory usage",
                "priority": ProfilePriority.NORMAL,
                "config": {
                    "buffer_size": 100,
                    "worker_count": 2,
                    "flush_interval": 5.0,
                    "compression": True,
                    "async_io": False,
                    "batch_processing": False,
                    "log_level": "INFO",
                    "enable_profiling": False,
                    "enable_debugging": False
                }
            }
        }
        
        # Custom profiles
        self._custom_profiles = {}
        
        # Profile switching
        self._current_profile = ProfileType.DEVELOPMENT
        self._profile_history = []
        self._max_history = 100
        
        # Profile validation and constraints
        self._profile_constraints = {
            "buffer_size": {"min": 50, "max": 100000},
            "worker_count": {"min": 1, "max": 64},
            "flush_interval": {"min": 0.01, "max": 60.0},
            "max_profiles": 50
        }
        
        # Profile switching rules
        self._switching_rules = [
            self._rule_workload_change,
            self._rule_performance_degradation,
            self._rule_resource_constraints,
            self._rule_scheduled_switch
        ]
        
        # Threading
        self._lock = threading.Lock()
        self._profile_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_profile_switches = 0
        self._successful_switches = 0
        self._last_switch_time = 0.0
        self._profile_performance = defaultdict(list)
    
    def start_monitoring(self) -> bool:
        """Start profile management monitoring."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                self._profile_thread = threading.Thread(target=self._profile_loop, daemon=True)
                self._profile_thread.start()
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop profile management monitoring."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                
                if self._profile_thread and self._profile_thread.is_alive():
                    self._profile_thread.join(timeout=5.0)
                
                return True
        except Exception:
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def _profile_loop(self) -> None:
        """Main profile management loop."""
        while not self._stop_event.is_set():
            try:
                self._check_profile_switching_rules()
                time.sleep(30)  # Check every 30 seconds
            except Exception:
                # Continue monitoring even if individual checks fail
                pass
    
    def _check_profile_switching_rules(self) -> None:
        """Check if profile switching is needed based on rules."""
        if not self._enabled:
            return
        
        for rule in self._switching_rules:
            try:
                new_profile = rule()
                if new_profile and new_profile != self._current_profile:
                    self.switch_profile(new_profile, reason=f"rule_{rule.__name__}")
                    break
            except Exception:
                # Continue with other rules
                pass
    
    def _rule_workload_change(self) -> Optional[ProfileType]:
        """Rule for workload-based profile switching."""
        # This would analyze current workload and suggest appropriate profile
        # For now, return None (no switch needed)
        return None
    
    def _rule_performance_degradation(self) -> Optional[ProfileType]:
        """Rule for performance degradation-based switching."""
        # This would detect performance issues and suggest profile changes
        # For now, return None (no switch needed)
        return None
    
    def _rule_resource_constraints(self) -> Optional[ProfileType]:
        """Rule for resource constraint-based switching."""
        # This would check resource usage and suggest profile changes
        # For now, return None (no switch needed)
        return None
    
    def _rule_scheduled_switch(self) -> Optional[ProfileType]:
        """Rule for scheduled profile switching."""
        # This would implement time-based profile switching
        # For now, return None (no switch needed)
        return None
    
    def create_custom_profile(self, name: str, config: Dict[str, Any], 
                             description: str = "", priority: ProfilePriority = ProfilePriority.NORMAL) -> bool:
        """
        Create a custom performance profile.
        
        Args:
            name: Profile name
            config: Profile configuration
            description: Profile description
            priority: Profile priority
            
        Returns:
            True if profile created successfully
        """
        if not self._enabled:
            return False
        
        try:
            # Validate configuration
            if not self._validate_profile_config(config):
                return False
            
            # Check profile limit
            if len(self._custom_profiles) >= self._profile_constraints["max_profiles"]:
                return False
            
            # Create profile
            profile = {
                "name": name,
                "description": description,
                "priority": priority,
                "config": config.copy(),
                "created_at": time.time(),
                "last_used": None,
                "usage_count": 0
            }
            
            self._custom_profiles[name] = profile
            return True
            
        except Exception:
            return False
    
    def update_custom_profile(self, name: str, config: Dict[str, Any], 
                             description: str = None, priority: ProfilePriority = None) -> bool:
        """
        Update an existing custom profile.
        
        Args:
            name: Profile name
            config: New configuration
            description: New description (optional)
            priority: New priority (optional)
            
        Returns:
            True if profile updated successfully
        """
        if not self._enabled or name not in self._custom_profiles:
            return False
        
        try:
            # Validate configuration
            if not self._validate_profile_config(config):
                return False
            
            profile = self._custom_profiles[name]
            
            # Update fields
            profile["config"] = config.copy()
            if description is not None:
                profile["description"] = description
            if priority is not None:
                profile["priority"] = priority
            
            profile["updated_at"] = time.time()
            return True
            
        except Exception:
            return False
    
    def delete_custom_profile(self, name: str) -> bool:
        """Delete a custom profile."""
        if not self._enabled or name not in self._custom_profiles:
            return False
        
        try:
            del self._custom_profiles[name]
            return True
        except Exception:
            return False
    
    def get_profile(self, profile_type: ProfileType) -> Optional[Dict[str, Any]]:
        """Get a built-in profile."""
        if profile_type in self._builtin_profiles:
            return self._builtin_profiles[profile_type].copy()
        return None
    
    def get_custom_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a custom profile."""
        if name in self._custom_profiles:
            return self._custom_profiles[name].copy()
        return None
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all available profiles."""
        all_profiles = {}
        
        # Add built-in profiles
        for profile_type, profile in self._builtin_profiles.items():
            all_profiles[f"builtin_{profile_type.value}"] = profile.copy()
        
        # Add custom profiles
        for name, profile in self._custom_profiles.items():
            all_profiles[f"custom_{name}"] = profile.copy()
        
        return all_profiles
    
    def switch_profile(self, profile_type: ProfileType, reason: str = "manual") -> bool:
        """
        Switch to a different profile.
        
        Args:
            profile_type: Profile to switch to
            reason: Reason for switching
            
        Returns:
            True if profile switched successfully
        """
        if not self._enabled or profile_type not in self._builtin_profiles:
            return False
        
        try:
            with self._lock:
                old_profile = self._current_profile
                self._current_profile = profile_type
                
                # Record profile switch
                switch_record = {
                    "timestamp": time.time(),
                    "from_profile": old_profile.value,
                    "to_profile": profile_type.value,
                    "reason": reason,
                    "config": self._builtin_profiles[profile_type]["config"].copy()
                }
                
                self._profile_history.append(switch_record)
                self._total_profile_switches += 1
                self._last_switch_time = time.time()
                
                # Keep history size manageable
                if len(self._profile_history) > self._max_history:
                    self._profile_history = self._profile_history[-self._max_history:]
                
                # Update usage statistics
                if profile_type in self._builtin_profiles:
                    self._builtin_profiles[profile_type]["last_used"] = time.time()
                    if "usage_count" not in self._builtin_profiles[profile_type]:
                        self._builtin_profiles[profile_type]["usage_count"] = 0
                    self._builtin_profiles[profile_type]["usage_count"] += 1
                
                self._successful_switches += 1
                return True
                
        except Exception:
            return False
    
    def switch_to_custom_profile(self, name: str, reason: str = "manual") -> bool:
        """
        Switch to a custom profile.
        
        Args:
            name: Custom profile name
            reason: Reason for switching
            
        Returns:
            True if profile switched successfully
        """
        if not self._enabled or name not in self._custom_profiles:
            return False
        
        try:
            with self._lock:
                old_profile = self._current_profile
                
                # Record profile switch
                switch_record = {
                    "timestamp": time.time(),
                    "from_profile": old_profile.value,
                    "to_profile": f"custom_{name}",
                    "reason": reason,
                    "config": self._custom_profiles[name]["config"].copy()
                }
                
                self._profile_history.append(switch_record)
                self._total_profile_switches += 1
                self._last_switch_time = time.time()
                
                # Update usage statistics
                self._custom_profiles[name]["last_used"] = time.time()
                self._custom_profiles[name]["usage_count"] += 1
                
                self._successful_switches += 1
                return True
                
        except Exception:
            return False
    
    def get_current_profile(self) -> ProfileType:
        """Get current active profile."""
        return self._current_profile
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current profile configuration."""
        if self._current_profile in self._builtin_profiles:
            return self._builtin_profiles[self._current_profile]["config"].copy()
        return {}
    
    def _validate_profile_config(self, config: Dict[str, Any]) -> bool:
        """Validate profile configuration against constraints."""
        try:
            for param_name, value in config.items():
                if param_name in self._profile_constraints:
                    constraints = self._profile_constraints[param_name]
                    
                    if "min" in constraints and value < constraints["min"]:
                        return False
                    if "max" in constraints and value > constraints["max"]:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def get_profile_switching_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get profile switching history."""
        return self._profile_history[-limit:] if limit > 0 else self._profile_history.copy()
    
    def get_profile_usage_stats(self) -> Dict[str, Any]:
        """Get profile usage statistics."""
        usage_stats = {}
        
        # Built-in profile stats
        for profile_type, profile in self._builtin_profiles.items():
            usage_stats[f"builtin_{profile_type.value}"] = {
                "name": profile["name"],
                "usage_count": profile.get("usage_count", 0),
                "last_used": profile.get("last_used"),
                "priority": profile["priority"].value
            }
        
        # Custom profile stats
        for name, profile in self._custom_profiles.items():
            usage_stats[f"custom_{name}"] = {
                "name": profile["name"],
                "usage_count": profile.get("usage_count", 0),
                "last_used": profile.get("last_used"),
                "priority": profile["priority"].value
            }
        
        return usage_stats
    
    def export_profile(self, profile_type: ProfileType, format: str = "json") -> str:
        """Export a profile configuration."""
        if profile_type not in self._builtin_profiles:
            return ""
        
        profile = self._builtin_profiles[profile_type]
        
        if format.lower() == "json":
            return json.dumps(profile, indent=2, default=str)
        else:
            return str(profile)
    
    def export_custom_profile(self, name: str, format: str = "json") -> str:
        """Export a custom profile configuration."""
        if name not in self._custom_profiles:
            return ""
        
        profile = self._custom_profiles[name]
        
        if format.lower() == "json":
            return json.dumps(profile, indent=2, default=str)
        else:
            return str(profile)
    
    def import_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Import a profile from external data."""
        try:
            name = profile_data.get("name", "")
            config = profile_data.get("config", {})
            description = profile_data.get("description", "")
            priority = ProfilePriority(profile_data.get("priority", ProfilePriority.NORMAL.value))
            
            return self.create_custom_profile(name, config, description, priority)
            
        except Exception:
            return False
    
    def get_profile_recommendations(self, workload_type: str = "general") -> List[Dict[str, Any]]:
        """Get profile recommendations based on workload type."""
        recommendations = []
        
        if workload_type == "high_throughput":
            recommendations.append({
                "profile": ProfileType.HIGH_PERFORMANCE,
                "reason": "Optimized for maximum throughput",
                "priority": ProfilePriority.HIGH
            })
        elif workload_type == "low_latency":
            recommendations.append({
                "profile": ProfileType.LOW_LATENCY,
                "reason": "Optimized for minimal latency",
                "priority": ProfilePriority.HIGH
            })
        elif workload_type == "memory_constrained":
            recommendations.append({
                "profile": ProfileType.MEMORY_EFFICIENT,
                "reason": "Optimized for minimal memory usage",
                "priority": ProfilePriority.NORMAL
            })
        else:
            recommendations.append({
                "profile": ProfileType.PRODUCTION,
                "reason": "Balanced configuration for general workloads",
                "priority": ProfilePriority.NORMAL
            })
        
        return recommendations
    
    def get_profile_manager_stats(self) -> Dict[str, Any]:
        """Get profile manager statistics."""
        return {
            "total_profile_switches": self._total_profile_switches,
            "successful_switches": self._successful_switches,
            "switch_success_rate": (self._successful_switches / self._total_profile_switches 
                                  if self._total_profile_switches > 0 else 0),
            "current_profile": self._current_profile.value,
            "builtin_profiles": len(self._builtin_profiles),
            "custom_profiles": len(self._custom_profiles),
            "total_profiles": len(self._builtin_profiles) + len(self._custom_profiles),
            "last_switch_time": self._last_switch_time,
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
    
    def reset_profile_stats(self) -> None:
        """Reset profile manager statistics."""
        with self._lock:
            self._profile_history.clear()
            self._total_profile_switches = 0
            self._successful_switches = 0
            self._last_switch_time = 0.0
            
            # Reset usage counts
            for profile in self._builtin_profiles.values():
                profile["usage_count"] = 0
                profile["last_used"] = None
            
            for profile in self._custom_profiles.values():
                profile["usage_count"] = 0
                profile["last_used"] = None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get profile manager metrics."""
        return self.get_profile_manager_stats()
    
    def reset_metrics(self) -> None:
        """Reset profile manager metrics."""
        self.reset_profile_stats()
    
    def is_healthy(self) -> bool:
        """Check if profile manager is healthy."""
        return (self._total_profile_switches > 0 and 
                self._successful_switches / self._total_profile_switches > 0.8)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get profile manager health status."""
        return {
            "healthy": self.is_healthy(),
            "switch_success_rate": (self._successful_switches / self._total_profile_switches 
                                  if self._total_profile_switches > 0 else 0),
            "current_profile": self._current_profile.value,
            "total_profiles": len(self._builtin_profiles) + len(self._custom_profiles),
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
