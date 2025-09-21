"""
Component Discovery System for Hydra-Logger

This module provides automatic component discovery and loading capabilities with
support for multiple discovery sources, validation, and background processing.
It enables dynamic component loading and management without manual registration.

FEATURES:
- Multiple discovery sources (file system, Python modules, plugin directories)
- Configurable discovery strategies (immediate, lazy, on-demand, background)
- Component validation and filtering
- Discovery callbacks and hooks
- Background discovery processing
- Discovery history and statistics

DISCOVERY SOURCES:
- File System: Discover components from file system paths
- Python Modules: Discover components from Python modules
- Plugin Directories: Discover components from plugin directories
- Custom Paths: Discover components from custom paths
- Dynamic Loading: Dynamic component loading

DISCOVERY STRATEGIES:
- Immediate: Discover components immediately
- Lazy: Discover components on first access
- On Demand: Discover components when requested
- Background: Discover components in background thread

USAGE:
    from hydra_logger.registry import ComponentDiscovery, DiscoverySource, DiscoveryStrategy
    
    # Create discovery system
    discovery = ComponentDiscovery(enabled=True)
    
    # Add discovery paths
    discovery.add_discovery_path("/path/to/components", DiscoverySource.FILE_SYSTEM)
    discovery.add_discovery_path("my_app.plugins", DiscoverySource.PYTHON_MODULES)
    
    # Set discovery strategy
    discovery.set_discovery_strategy(DiscoveryStrategy.BACKGROUND)
    
    # Start background discovery
    discovery.start_background_discovery()
    
    # Discover components
    components = discovery.discover_components()
    
    # Get discovery statistics
    stats = discovery.get_discovery_stats()
"""

import os
import sys
import time
import threading
import importlib
import inspect
from typing import Any, Dict, List, Optional, Callable, Type, Set
from collections import defaultdict, deque
from pathlib import Path
from enum import Enum
from ..interfaces.registry import RegistryInterface


class DiscoverySource(Enum):
    """Sources for component discovery."""
    FILE_SYSTEM = "file_system"
    PYTHON_MODULES = "python_modules"
    PLUGIN_DIRECTORIES = "plugin_directories"
    CUSTOM_PATHS = "custom_paths"
    DYNAMIC_LOADING = "dynamic_loading"


class DiscoveryStrategy(Enum):
    """Discovery strategies."""
    IMMEDIATE = "immediate"
    LAZY = "lazy"
    ON_DEMAND = "on_demand"
    BACKGROUND = "background"


class ComponentDiscovery:
    """Real component discovery system for automatic component loading."""
    
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._initialized = True
        
        # Discovery paths and sources
        self._discovery_paths = []
        self._plugin_directories = []
        self._custom_paths = []
        self._excluded_paths = set()
        self._excluded_patterns = set()
        
        # Discovery configuration
        self._discovery_strategy = DiscoveryStrategy.IMMEDIATE
        self._auto_discovery = True
        self._recursive_discovery = True
        self._max_depth = 5
        
        # Discovery callbacks and hooks
        self._discovery_callbacks = defaultdict(list)  # source -> [callbacks]
        self._validation_callbacks = defaultdict(list)  # component_type -> [callbacks]
        self._loading_callbacks = defaultdict(list)  # component_type -> [callbacks]
        
        # Discovery state and tracking
        self._discovered_components = defaultdict(set)  # source -> {component_ids}
        self._discovery_history = deque(maxlen=1000)
        self._failed_discoveries = defaultdict(int)  # source -> count
        
        # Threading
        self._lock = threading.RLock()
        self._discovery_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_discoveries = 0
        self._successful_discoveries = 0
        self._last_discovery_time = 0.0
    
    def add_discovery_path(self, path: str, source: DiscoverySource = DiscoverySource.FILE_SYSTEM) -> bool:
        """Add a path for component discovery."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if source == DiscoverySource.FILE_SYSTEM:
                    self._discovery_paths.append(path)
                elif source == DiscoverySource.PLUGIN_DIRECTORIES:
                    self._plugin_directories.append(path)
                elif source == DiscoverySource.CUSTOM_PATHS:
                    self._custom_paths.append(path)
                
                return True
                
        except Exception:
            return False
    
    def remove_discovery_path(self, path: str, source: DiscoverySource = DiscoverySource.FILE_SYSTEM) -> bool:
        """Remove a discovery path."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if source == DiscoverySource.FILE_SYSTEM and path in self._discovery_paths:
                    self._discovery_paths.remove(path)
                    return True
                elif source == DiscoverySource.PLUGIN_DIRECTORIES and path in self._plugin_directories:
                    self._plugin_directories.remove(path)
                    return True
                elif source == DiscoverySource.CUSTOM_PATHS and path in self._custom_paths:
                    self._custom_paths.remove(path)
                    return True
                
                return False
                
        except Exception:
            return False
    
    def add_excluded_path(self, path: str) -> bool:
        """Add a path to exclude from discovery."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._excluded_paths.add(path)
                return True
        except Exception:
            return False
    
    def remove_excluded_path(self, path: str) -> bool:
        """Remove a path from exclusion list."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._excluded_paths.discard(path)
                return True
        except Exception:
            return False
    
    def add_excluded_pattern(self, pattern: str) -> bool:
        """Add a pattern to exclude from discovery."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._excluded_patterns.add(pattern)
                return True
        except Exception:
            return False
    
    def remove_excluded_pattern(self, pattern: str) -> bool:
        """Remove a pattern from exclusion list."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._excluded_patterns.discard(pattern)
                return True
        except Exception:
            return False
    
    def set_discovery_strategy(self, strategy: DiscoveryStrategy) -> bool:
        """Set the discovery strategy."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._discovery_strategy = strategy
                return True
        except Exception:
            return False
    
    def get_discovery_strategy(self) -> DiscoveryStrategy:
        """Get the current discovery strategy."""
        return self._discovery_strategy
    
    def set_auto_discovery(self, enabled: bool) -> bool:
        """Enable or disable auto-discovery."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._auto_discovery = enabled
                return True
        except Exception:
            return False
    
    def is_auto_discovery_enabled(self) -> bool:
        """Check if auto-discovery is enabled."""
        return self._auto_discovery
    
    def set_recursive_discovery(self, enabled: bool) -> bool:
        """Enable or disable recursive discovery."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._recursive_discovery = enabled
                return True
        except Exception:
            return False
    
    def is_recursive_discovery_enabled(self) -> bool:
        """Check if recursive discovery is enabled."""
        return self._recursive_discovery
    
    def set_max_depth(self, depth: int) -> bool:
        """Set maximum discovery depth."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._max_depth = max(1, min(10, depth))
                return True
        except Exception:
            return False
    
    def get_max_depth(self) -> int:
        """Get maximum discovery depth."""
        return self._max_depth
    
    def register_discovery_callback(self, source: DiscoverySource, callback: Callable) -> bool:
        """Register a callback for discovery events."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._discovery_callbacks[source].append(callback)
                return True
        except Exception:
            return False
    
    def unregister_discovery_callback(self, source: DiscoverySource, callback: Callable) -> bool:
        """Unregister a discovery callback."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if source in self._discovery_callbacks:
                    try:
                        self._discovery_callbacks[source].remove(callback)
                        return True
                    except ValueError:
                        return False
                return False
        except Exception:
            return False
    
    def register_validation_callback(self, component_type: str, callback: Callable) -> bool:
        """Register a callback for component validation."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._validation_callbacks[component_type].append(callback)
                return True
        except Exception:
            return False
    
    def unregister_validation_callback(self, component_type: str, callback: Callable) -> bool:
        """Unregister a validation callback."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if component_type in self._validation_callbacks:
                    try:
                        self._validation_callbacks[component_type].remove(callback)
                        return True
                    except ValueError:
                        return False
                return False
        except Exception:
            return False
    
    def register_loading_callback(self, component_type: str, callback: Callable) -> bool:
        """Register a callback for component loading."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                self._loading_callbacks[component_type].append(callback)
                return True
        except Exception:
            return False
    
    def unregister_loading_callback(self, component_type: str, callback: Callable) -> bool:
        """Unregister a loading callback."""
        if not self._enabled:
            return False
        
        try:
            with self._lock:
                if component_type in self._loading_callbacks:
                    try:
                        self._loading_callbacks[component_type].remove(callback)
                        return True
                    except ValueError:
                        return False
                return False
        except Exception:
            return False
    
    def discover_components(self, source: Optional[DiscoverySource] = None) -> Dict[str, List[Any]]:
        """Discover components from specified or all sources."""
        if not self._enabled:
            return {}
        
        try:
            with self._lock:
                self._total_discoveries += 1
                current_time = time.time()
                
                discovered = defaultdict(list)
                
                if source:
                    sources = [source]
                else:
                    sources = list(DiscoverySource)
                
                for discovery_source in sources:
                    try:
                        source_components = self._discover_from_source(discovery_source)
                        discovered[discovery_source.value] = source_components
                        
                        # Update discovered components tracking
                        for component in source_components:
                            self._discovered_components[discovery_source].add(id(component))
                        
                        self._successful_discoveries += 1
                        
                    except Exception as e:
                        self._failed_discoveries[discovery_source] += 1
                        # Continue with other sources
                
                # Record discovery
                discovery_record = {
                    "timestamp": current_time,
                    "sources": [s.value for s in sources],
                    "total_discovered": sum(len(components) for components in discovered.values()),
                    "successful_sources": len([s for s in sources if discovered[s.value]]),
                    "failed_sources": len([s for s in sources if not discovered[s.value]])
                }
                
                self._discovery_history.append(discovery_record)
                self._last_discovery_time = current_time
                
                return dict(discovered)
                
        except Exception:
            return {}
    
    def discover_from_file_system(self, path: Optional[str] = None) -> List[Any]:
        """Discover components from file system."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                discovery_paths = [path] if path else self._discovery_paths
                discovered = []
                
                for discovery_path in discovery_paths:
                    if not os.path.exists(discovery_path):
                        continue
                    
                    if self._is_path_excluded(discovery_path):
                        continue
                    
                    path_components = self._scan_directory(discovery_path)
                    discovered.extend(path_components)
                
                return discovered
                
        except Exception:
            return []
    
    def discover_from_python_modules(self, module_names: Optional[List[str]] = None) -> List[Any]:
        """Discover components from Python modules."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                discovered = []
                
                if not module_names:
                    # Discover from common module patterns
                    module_names = self._find_potential_modules()
                
                for module_name in module_names:
                    try:
                        module_components = self._scan_module(module_name)
                        discovered.extend(module_components)
                    except Exception:
                        # Continue with other modules
                        pass
                
                return discovered
                
        except Exception:
            return []
    
    def discover_from_plugin_directories(self) -> List[Any]:
        """Discover components from plugin directories."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                discovered = []
                
                for plugin_dir in self._plugin_directories:
                    if not os.path.exists(plugin_dir):
                        continue
                    
                    if self._is_path_excluded(plugin_dir):
                        continue
                    
                    plugin_components = self._scan_plugin_directory(plugin_dir)
                    discovered.extend(plugin_components)
                
                return discovered
                
        except Exception:
            return []
    
    def discover_from_custom_paths(self) -> List[Any]:
        """Discover components from custom paths."""
        if not self._enabled:
            return []
        
        try:
            with self._lock:
                discovered = []
                
                for custom_path in self._custom_paths:
                    if not os.path.exists(custom_path):
                        continue
                    
                    if self._is_path_excluded(custom_path):
                        continue
                    
                    custom_components = self._scan_custom_path(custom_path)
                    discovered.extend(custom_components)
                
                return discovered
                
        except Exception:
            return []
    
    def start_background_discovery(self) -> bool:
        """Start background discovery process."""
        if not self._enabled or self._discovery_thread is not None:
            return False
        
        try:
            with self._lock:
                self._stop_event.clear()
                self._discovery_thread = threading.Thread(target=self._background_discovery_loop, daemon=True)
                self._discovery_thread.start()
                return True
        except Exception:
            return False
    
    def stop_background_discovery(self) -> bool:
        """Stop background discovery process."""
        if not self._enabled or self._discovery_thread is None:
            return False
        
        try:
            with self._lock:
                self._stop_event.set()
                
                if self._discovery_thread.is_alive():
                    self._discovery_thread.join(timeout=5.0)
                
                self._discovery_thread = None
                return True
        except Exception:
            return False
    
    def is_background_discovery_running(self) -> bool:
        """Check if background discovery is running."""
        return self._discovery_thread is not None and self._discovery_thread.is_alive()
    
    def get_discovery_paths(self) -> Dict[str, List[str]]:
        """Get all discovery paths organized by source."""
        return {
            "file_system": self._discovery_paths.copy(),
            "plugin_directories": self._plugin_directories.copy(),
            "custom_paths": self._custom_paths.copy()
        }
    
    def get_excluded_paths(self) -> Set[str]:
        """Get all excluded paths."""
        return self._excluded_paths.copy()
    
    def get_excluded_patterns(self) -> Set[str]:
        """Get all excluded patterns."""
        return self._excluded_patterns.copy()
    
    def get_discovered_components(self, source: Optional[DiscoverySource] = None) -> Dict[str, Set[int]]:
        """Get discovered components by source."""
        if source:
            return {source.value: self._discovered_components[source].copy()}
        else:
            return {s.value: components.copy() for s, components in self._discovered_components.items()}
    
    def get_discovery_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get discovery history."""
        return list(self._discovery_history)[-limit:] if limit > 0 else list(self._discovery_history)
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        return {
            "total_discoveries": self._total_discoveries,
            "successful_discoveries": self._successful_discoveries,
            "success_rate": (self._successful_discoveries / self._total_discoveries 
                           if self._total_discoveries > 0 else 0),
            "failed_discoveries": dict(self._failed_discoveries),
            "total_failures": sum(self._failed_discoveries.values()),
            "last_discovery_time": self._last_discovery_time,
            "background_discovery_running": self.is_background_discovery_running(),
            "enabled": self._enabled
        }
    
    def reset_discovery_stats(self) -> None:
        """Reset discovery statistics."""
        with self._lock:
            self._discovery_history.clear()
            self._failed_discoveries.clear()
            self._total_discoveries = 0
            self._successful_discoveries = 0
            self._last_discovery_time = 0.0
    
    def _discover_from_source(self, source: DiscoverySource) -> List[Any]:
        """Discover components from a specific source."""
        if source == DiscoverySource.FILE_SYSTEM:
            return self.discover_from_file_system()
        elif source == DiscoverySource.PYTHON_MODULES:
            return self.discover_from_python_modules()
        elif source == DiscoverySource.PLUGIN_DIRECTORIES:
            return self.discover_from_plugin_directories()
        elif source == DiscoverySource.CUSTOM_PATHS:
            return self.discover_from_custom_paths()
        else:
            return []
    
    def _is_path_excluded(self, path: str) -> bool:
        """Check if a path should be excluded from discovery."""
        # Check exact path exclusions
        if path in self._excluded_paths:
            return True
        
        # Check pattern exclusions
        for pattern in self._excluded_patterns:
            if pattern in path:
                return True
        
        # Check common exclusions
        common_exclusions = {
            '__pycache__', '.git', '.svn', '.hg', '.DS_Store',
            'node_modules', 'venv', 'env', '.env', 'dist', 'build'
        }
        
        path_parts = Path(path).parts
        for part in path_parts:
            if part in common_exclusions:
                return True
        
        return False
    
    def _scan_directory(self, directory: str, depth: int = 0) -> List[Any]:
        """Scan a directory for components."""
        if depth > self._max_depth:
            return []
        
        discovered = []
        
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                if self._is_path_excluded(item_path):
                    continue
                
                if os.path.isdir(item_path) and self._recursive_discovery:
                    sub_components = self._scan_directory(item_path, depth + 1)
                    discovered.extend(sub_components)
                elif item.endswith('.py'):
                    module_components = self._scan_python_file(item_path)
                    discovered.extend(module_components)
                
        except Exception:
            pass
        
        return discovered
    
    def _scan_python_file(self, file_path: str) -> List[Any]:
        """Scan a Python file for components."""
        discovered = []
        
        try:
            # Extract module name from file path
            module_name = self._file_path_to_module_name(file_path)
            if module_name:
                module_components = self._scan_module(module_name)
                discovered.extend(module_components)
                
        except Exception:
            pass
        
        return discovered
    
    def _file_path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert file path to module name."""
        try:
            # Get absolute path
            abs_path = os.path.abspath(file_path)
            
            # Find the path relative to Python path
            for path in sys.path:
                if abs_path.startswith(path):
                    relative_path = os.path.relpath(abs_path, path)
                    # Convert to module name
                    module_name = relative_path.replace(os.sep, '.').replace('.py', '')
                    return module_name
            
            return None
            
        except Exception:
            return None
    
    def _scan_module(self, module_name: str) -> List[Any]:
        """Scan a Python module for components."""
        discovered = []
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Scan module attributes for components
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if self._is_potential_component(attr):
                    # Validate component
                    if self._validate_discovered_component(attr):
                        discovered.append(attr)
                        
                        # Trigger loading callbacks
                        component_type = self._get_component_type(attr)
                        self._trigger_loading_callbacks(component_type, attr)
            
        except Exception:
            pass
        
        return discovered
    
    def _scan_plugin_directory(self, plugin_dir: str) -> List[Any]:
        """Scan a plugin directory for components."""
        discovered = []
        
        try:
            # Look for Python files and packages
            for item in os.listdir(plugin_dir):
                item_path = os.path.join(plugin_dir, item)
                
                if self._is_path_excluded(item_path):
                    continue
                
                if item.endswith('.py'):
                    # Single Python file
                    module_components = self._scan_python_file(item_path)
                    discovered.extend(module_components)
                elif os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, '__init__.py')):
                    # Python package
                    package_name = os.path.basename(item_path)
                    package_components = self._scan_module(package_name)
                    discovered.extend(package_components)
            
        except Exception:
            pass
        
        return discovered
    
    def _scan_custom_path(self, custom_path: str) -> List[Any]:
        """Scan a custom path for components."""
        discovered = []
        
        try:
            if os.path.isfile(custom_path):
                # Single file
                if custom_path.endswith('.py'):
                    file_components = self._scan_python_file(custom_path)
                    discovered.extend(file_components)
            elif os.path.isdir(custom_path):
                # Directory
                dir_components = self._scan_directory(custom_path)
                discovered.extend(dir_components)
            
        except Exception:
            pass
        
        return discovered
    
    def _is_potential_component(self, obj: Any) -> bool:
        """Check if an object is a potential component."""
        try:
            # Check if it's a class
            if not inspect.isclass(obj):
                return False
            
            # Check if it's not a builtin
            if obj.__module__ == 'builtins':
                return False
            
            # Check if it has component-like methods
            component_methods = ['initialize', 'start', 'stop', 'configure', 'validate']
            has_component_methods = any(hasattr(obj, method) for method in component_methods)
            
            return has_component_methods
            
        except Exception:
            return False
    
    def _validate_discovered_component(self, component: Any) -> bool:
        """Validate a discovered component."""
        try:
            component_type = self._get_component_type(component)
            
            # Trigger validation callbacks
            for callback in self._validation_callbacks[component_type]:
                if not callback(component):
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _get_component_type(self, component: Any) -> str:
        """Get the type of a component."""
        try:
            # Try to determine component type from class name or attributes
            class_name = component.__name__.lower()
            
            if 'handler' in class_name:
                return 'handler'
            elif 'formatter' in class_name:
                return 'formatter'
            elif 'plugin' in class_name:
                return 'plugin'
            elif 'monitor' in class_name:
                return 'monitor'
            elif 'security' in class_name:
                return 'security'
            else:
                return 'custom'
                
        except Exception:
            return 'unknown'
    
    def _find_potential_modules(self) -> List[str]:
        """Find potential modules for discovery."""
        potential_modules = []
        
        try:
            # Look for modules in current working directory
            cwd = os.getcwd()
            for item in os.listdir(cwd):
                if item.endswith('.py') and not item.startswith('_'):
                    potential_modules.append(item[:-3])
                elif os.path.isdir(os.path.join(cwd, item)) and os.path.exists(os.path.join(cwd, item, '__init__.py')):
                    potential_modules.append(item)
            
            # Add common Hydra-Logger module patterns
            common_patterns = [
                'hydra_logger', 'hydra', 'logger', 'logging',
                'handlers', 'formatters', 'plugins', 'monitors'
            ]
            
            for pattern in common_patterns:
                if pattern not in potential_modules:
                    potential_modules.append(pattern)
                    
        except Exception:
            pass
        
        return potential_modules
    
    def _trigger_loading_callbacks(self, component_type: str, component: Any) -> None:
        """Trigger loading callbacks for a component."""
        for callback in self._loading_callbacks[component_type]:
            try:
                callback(component_type, component)
            except Exception:
                # Continue with other callbacks
                pass
    
    def _background_discovery_loop(self) -> None:
        """Background discovery loop."""
        while not self._stop_event.is_set():
            try:
                # Perform discovery
                self.discover_components()
                
                # Wait before next discovery
                time.sleep(300)  # 5 minutes
                
            except Exception:
                # Continue discovery even if individual attempts fail
                pass
