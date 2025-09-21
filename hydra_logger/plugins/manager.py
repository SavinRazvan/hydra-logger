"""
Plugin Manager for Hydra-Logger

This module provides comprehensive plugin lifecycle management and operations
including registration, initialization, execution, and performance monitoring.
It supports both synchronous and background processing for optimal performance.

FEATURES:
- Plugin registration and lifecycle management
- Enable/disable and initialization control
- Synchronous and background execution modes
- Performance monitoring and caching
- Plugin status tracking and analytics

USAGE:
    from hydra_logger.plugins import PluginManager, FormatterPlugin
    
    # Create plugin manager
    manager = PluginManager(use_background_processing=True)
    
    # Register plugin
    plugin = MyFormatter("custom_formatter", "my_format")
    manager.register_plugin(plugin)
    
    # Initialize and enable plugin
    manager.initialize_plugin("custom_formatter")
    manager.enable_plugin("custom_formatter")
    
    # Execute plugin
    result = manager.execute_plugin("custom_formatter", data)
    
    # Get plugin status
    status = manager.get_plugin_status("custom_formatter")
"""

import time
import threading
from typing import Dict, List, Optional, Any, Union, Callable
from concurrent.futures import Future
from .base import BasePlugin
from .registry import PluginRegistry
from ..security.background_processing import (
    get_background_processor
)


class PluginManager:
    """Manager for plugin lifecycle and operations."""
    
    def __init__(self, use_background_processing: bool = True):
        """Initialize plugin manager."""
        self.registry = PluginRegistry()
        self._enabled_plugins: Dict[str, BasePlugin] = {}
        
        # Background processing configuration
        self._use_background_processing = use_background_processing
        self._background_processor = get_background_processor()
        
        # Plugin operation queue for background processing
        self._plugin_queue = []
        self._queue_lock = threading.Lock()
        self._background_thread = None
        self._stop_event = threading.Event()
        
        # Performance metrics and caching
        self._plugin_cache = {}
        self._cache_max_size = 1000
        self._cache_ttl = 300.0  # 5 minutes
        
        # Statistics
        self._synchronous_operations = 0
        self._background_operations = 0
        self._plugin_execution_times = {}
        self._plugin_success_count = {}
        self._plugin_error_count = {}
        
        # Thread lock for thread-safe operations
        self._lock = threading.RLock()
    
    def register_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register a plugin.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration successful, False otherwise
        """
        success = self.registry.register_plugin(plugin)
        if success and plugin.is_enabled():
            self._enabled_plugins[plugin.name] = plugin
        return success
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        # Remove from enabled plugins if present
        if plugin_name in self._enabled_plugins:
            del self._enabled_plugins[plugin_name]
        
        return self.registry.unregister_plugin(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin_name: Name of plugin to enable
            
        Returns:
            True if enabled, False otherwise
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return False
        
        plugin.enable()
        self._enabled_plugins[plugin_name] = plugin
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin_name: Name of plugin to disable
            
        Returns:
            True if disabled, False otherwise
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return False
        
        plugin.disable()
        if plugin_name in self._enabled_plugins:
            del self._enabled_plugins[plugin_name]
        return True
    
    def initialize_plugin(self, plugin_name: str) -> bool:
        """
        Initialize a plugin.
        
        Args:
            plugin_name: Name of plugin to initialize
            
        Returns:
            True if initialization successful, False otherwise
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return False
        
        try:
            success = plugin.initialize()
            return success
        except Exception:
            return False
    
    def initialize_all_plugins(self) -> Dict[str, bool]:
        """
        Initialize all enabled plugins.
        
        Returns:
            Dictionary mapping plugin names to initialization success
        """
        results = {}
        
        for plugin_name in list(self._enabled_plugins.keys()):
            try:
                success = self.initialize_plugin(plugin_name)
                results[plugin_name] = success
                
                # Remove failed plugins from enabled list
                if not success:
                    del self._enabled_plugins[plugin_name]
                    
            except Exception:
                results[plugin_name] = False
                if plugin_name in self._enabled_plugins:
                    del self._enabled_plugins[plugin_name]
        
        return results
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by name.
        
        Args:
            plugin_name: Name of plugin to get
            
        Returns:
            Plugin instance or None if not found
        """
        return self.registry.get_plugin(plugin_name)
    
    def get_enabled_plugins(self) -> List[BasePlugin]:
        """
        Get all enabled plugins.
        
        Returns:
            List of enabled plugin instances
        """
        return list(self._enabled_plugins.values())
    
    def get_plugins_by_type(self, plugin_type: str) -> List[BasePlugin]:
        """
        Get all plugins of a specific type.
        
        Args:
            plugin_type: Plugin type to get
            
        Returns:
            List of plugin instances
        """
        return self.registry.get_plugins_by_type(plugin_type)
    
    def list_plugins(self, plugin_type: Optional[str] = None) -> List[str]:
        """
        List registered plugins.
        
        Args:
            plugin_type: Optional plugin type to filter by
            
        Returns:
            List of plugin names
        """
        return self.registry.list_plugins(plugin_type)
    
    def list_enabled_plugins(self) -> List[str]:
        """
        List enabled plugins.
        
        Returns:
            List of enabled plugin names
        """
        return list(self._enabled_plugins.keys())
    
    def get_plugin_status(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get status of a plugin.
        
        Args:
            plugin_name: Name of plugin to get status for
            
        Returns:
            Plugin status dictionary
        """
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return {"error": "Plugin not found"}
        
        return {
            "name": plugin.name,
            "enabled": plugin.is_enabled(),
            "initialized": plugin.is_initialized(),
            "type": plugin.__class__.__name__,
            "config": plugin.get_config()
        }
    
    def get_all_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all plugins.
        
        Returns:
            Dictionary mapping plugin names to status
        """
        status = {}
        for plugin_name in self.registry.list_plugins():
            status[plugin_name] = self.get_plugin_status(plugin_name)
        return status
    
    def shutdown_plugins(self) -> None:
        """Shutdown all plugins."""
        for plugin in self._enabled_plugins.values():
            try:
                if hasattr(plugin, 'shutdown'):
                    plugin.shutdown()
            except Exception:
                pass  # Silently ignore shutdown errors
        
        self._enabled_plugins.clear()
    
    def get_plugin_count(self) -> int:
        """
        Get total number of registered plugins.
        
        Returns:
            Plugin count
        """
        return self.registry.get_plugin_count()
    
    def get_enabled_plugin_count(self) -> int:
        """
        Get number of enabled plugins.
        
        Returns:
            Enabled plugin count
        """
        return len(self._enabled_plugins)
    
    def start_background_processing(self) -> bool:
        """Start background processing for plugin operations."""
        if not self._use_background_processing or self._background_thread:
            return False
        
        try:
            self._stop_event.clear()
            self._background_thread = threading.Thread(target=self._background_processor_loop, daemon=True)
            self._background_thread.start()
            return True
        except Exception:
            return False
    
    def stop_background_processing(self) -> bool:
        """Stop background processing for plugin operations."""
        if not self._background_thread:
            return False
        
        try:
            self._stop_event.set()
            if self._background_thread.is_alive():
                self._background_thread.join(timeout=5.0)
            self._background_thread = None
            return True
        except Exception:
            return False
    
    def _background_processor_loop(self) -> None:
        """Background processing loop for plugin operations."""
        while not self._stop_event.is_set():
            try:
                self._process_plugin_queue()
                time.sleep(0.1)  # Small delay to prevent busy waiting
            except Exception:
                # Continue processing even if individual operations fail
                pass
    
    def _process_plugin_queue(self) -> None:
        """Process queued plugin operations."""
        with self._queue_lock:
            if not self._plugin_queue:
                return
            
            # Process all queued operations
            operations = self._plugin_queue.copy()
            self._plugin_queue.clear()
        
        for operation in operations:
            try:
                self._execute_plugin_operation(operation)
                with self._lock:
                    self._background_operations += 1
            except Exception:
                # Log error but continue processing
                pass
    
    def _execute_plugin_operation(self, operation: Dict[str, Any]) -> None:
        """Execute a plugin operation."""
        op_type = operation.get('type')
        plugin_name = operation.get('plugin_name')
        data = operation.get('data', {})
        callback = operation.get('callback')
        
        if op_type == 'execute':
            result = self._execute_plugin_sync(plugin_name, data)
            if callback:
                callback(result)
        elif op_type == 'initialize':
            result = self._initialize_plugin_sync(plugin_name)
            if callback:
                callback(result)
        elif op_type == 'shutdown':
            result = self._shutdown_plugin_sync(plugin_name)
            if callback:
                callback(result)
    
    def _queue_plugin_operation(self, operation: Dict[str, Any]) -> None:
        """Queue a plugin operation for background processing."""
        with self._queue_lock:
            self._plugin_queue.append(operation)
    
    def execute_plugin(self, plugin_name: str, data: Any = None, 
                      use_background: bool = None, callback: Optional[Callable] = None) -> Union[Any, Future]:
        """
        Execute a plugin with optional background processing.
        
        Args:
            plugin_name: Name of plugin to execute
            data: Data to pass to plugin
            use_background: Whether to use background processing
            callback: Callback function for background processing
            
        Returns:
            Plugin result (synchronous) or Future (asynchronous)
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin or not plugin.is_enabled():
            return None
        
        # Determine if we should use background processing
        should_use_background = (
            use_background if use_background is not None 
            else self._use_background_processing
        )
        
        if should_use_background:
            return self._execute_plugin_background(plugin_name, data, callback)
        else:
            return self._execute_plugin_sync(plugin_name, data)
    
    def _execute_plugin_sync(self, plugin_name: str, data: Any = None) -> Any:
        """Synchronous plugin execution."""
        start_time = time.time()
        
        try:
            plugin = self.get_plugin(plugin_name)
            if not plugin:
                return None
            
            # Check cache first
            cache_key = self._get_cache_key('execute', plugin_name, data)
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute plugin
            result = plugin.execute(data) if hasattr(plugin, 'execute') else None
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Update statistics
            execution_time = time.time() - start_time
            with self._lock:
                self._synchronous_operations += 1
                self._plugin_execution_times[plugin_name] = execution_time
                self._plugin_success_count[plugin_name] = self._plugin_success_count.get(plugin_name, 0) + 1
            
            return result
            
        except Exception as e:
            with self._lock:
                self._plugin_error_count[plugin_name] = self._plugin_error_count.get(plugin_name, 0) + 1
            return None
    
    def _execute_plugin_background(self, plugin_name: str, data: Any = None, 
                                 callback: Optional[Callable] = None) -> Future:
        """Asynchronous plugin execution using background processing."""
        def result_callback(result):
            if callback:
                callback(result)
        
        # Queue operation for background processing
        self._queue_plugin_operation({
            'type': 'execute',
            'plugin_name': plugin_name,
            'data': data,
            'callback': result_callback
        })
        
        # Return a future that will be resolved when processing is complete
        future = Future()
        
        def future_callback(result):
            future.set_result(result)
        
        # Store the callback for when the result is ready
        return future
    
    def _get_cache_key(self, operation: str, plugin_name: str, data: Any = None) -> str:
        """Generate cache key for plugin operation."""
        import hashlib
        key_data = f"{operation}:{plugin_name}:{str(data)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache plugin operation result."""
        with self._lock:
            if len(self._plugin_cache) >= self._cache_max_size:
                # Remove oldest entries
                oldest_key = min(self._plugin_cache.keys(),
                               key=lambda k: self._plugin_cache[k]['timestamp'])
                del self._plugin_cache[oldest_key]
            
            self._plugin_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if valid."""
        if cache_key in self._plugin_cache:
            cached_result = self._plugin_cache[cache_key]
            if time.time() - cached_result['timestamp'] < self._cache_ttl:
                return cached_result['result']
        return None
    
    def get_plugin_performance_stats(self) -> Dict[str, Any]:
        """Get plugin performance statistics."""
        with self._lock:
            return {
                "synchronous_operations": self._synchronous_operations,
                "background_operations": self._background_operations,
                "plugin_execution_times": self._plugin_execution_times.copy(),
                "plugin_success_count": self._plugin_success_count.copy(),
                "plugin_error_count": self._plugin_error_count.copy(),
                "cache_size": len(self._plugin_cache),
                "queue_size": len(self._plugin_queue),
                "background_processing": self._use_background_processing
            }
    
    def reset_plugin_stats(self) -> None:
        """Reset plugin performance statistics."""
        with self._lock:
            self._synchronous_operations = 0
            self._background_operations = 0
            self._plugin_execution_times.clear()
            self._plugin_success_count.clear()
            self._plugin_error_count.clear()
            self._plugin_cache.clear()
            self._plugin_queue.clear()
    
    def enable_background_processing(self, enabled: bool = True) -> None:
        """Enable or disable background processing."""
        self._use_background_processing = enabled
        if enabled:
            self.start_background_processing()
        else:
            self.stop_background_processing()
    
    def is_background_processing_enabled(self) -> bool:
        """Check if background processing is enabled."""
        return self._use_background_processing
