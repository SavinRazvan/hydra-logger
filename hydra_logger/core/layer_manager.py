"""
Intelligent Layer Management System for Hydra-Logger

This module provides sophisticated layer management for organizing logging handlers
into logical groups with intelligent fallback strategies, caching, and performance
optimizations. It supports multi-layer configurations with automatic handler
creation and intelligent routing.

ARCHITECTURE:
- LayerManager: Centralized layer management with intelligent fallback
- LayerConfiguration: Individual layer configuration and metadata
- Handler Creation: Automatic handler creation from configuration
- Cache Integration: High-performance caching for layer lookups
- Multi-Layer Optimization: Performance optimizations for multiple layers

LAYER FEATURES:
- Intelligent fallback hierarchy (requested → default → any available)
- Automatic handler creation from configuration
- Thread-safe operations with RLock
- Multi-layer performance optimizations
- Layer-specific level thresholds
- Dynamic layer addition and removal

HANDLER SUPPORT:
- Console handlers with color support
- File handlers with rotation
- Null handlers for testing
- Custom handler integration
- Formatter assignment per handler

COLOR SYSTEM INTEGRATION:
- LayerConfiguration.color_mode for per-layer color settings
- LogDestination.use_colors integration for console handlers
- Color inheritance and layer-specific overrides
- ColoredFormatter assignment when colors enabled
- Cross-platform terminal compatibility

CACHING & PERFORMANCE:
- Intelligent caching with fallback strategies
- Cache hit/miss statistics
- Multi-layer optimization flags
- Performance monitoring and statistics

USAGE EXAMPLES:

Basic Layer Setup:
    from hydra_logger.core.layer_manager import LayerManager
    
    manager = LayerManager()
    config_layers = {
        "api": {"level": "INFO", "destinations": [...]},
        "database": {"level": "WARNING", "destinations": [...]}
    }
    manager.setup_layers(config_layers)

Layer Handler Access:
    from hydra_logger.core.layer_manager import LayerManager
    
    manager = LayerManager()
    handlers = manager.get_handlers_for_layer("api")
    threshold = manager.get_layer_threshold("api")

Layer Management:
    from hydra_logger.core.layer_manager import LayerManager
    
    manager = LayerManager()
    manager.add_layer("custom", "DEBUG")
    manager.remove_layer("custom")
    layer_config = manager.get_layer_config("api")

Performance Monitoring:
    from hydra_logger.core.layer_manager import LayerManager
    
    manager = LayerManager()
    stats = manager.get_multi_layer_stats()
    print(f"Cache hit rate: {stats['cache_stats']['overall']['overall_cache_hit_rate']:.2%}")
"""

import threading
from typing import Any, Dict, List, Optional, Union

from ..interfaces.handler import HandlerInterface
from ..interfaces.formatter import FormatterInterface as BaseFormatter
from ..types.levels import LogLevel
from .cache_manager import CacheManager


class LayerConfiguration:
    """Configuration for a logging layer."""
    
    def __init__(self, name: str, level: str = "INFO", destinations: Optional[List[Dict[str, Any]]] = None):
        self.name = name
        self.level = level
        self.destinations = destinations or []
        self.handlers: List[HandlerInterface] = []
        self.formatter: Optional[BaseFormatter] = None
        self.color_mode: str = "auto"
        self.enabled: bool = True
    
    def add_destination(self, destination: Dict[str, Any]) -> None:
        """Add a destination to this layer."""
        self.destinations.append(destination)
    
    def set_handlers(self, handlers: List[HandlerInterface]) -> None:
        """Set handlers for this layer."""
        self.handlers = handlers
    
    def set_formatter(self, formatter: BaseFormatter) -> None:
        """Set formatter for this layer."""
        self.formatter = formatter
    
    def get_level_numeric(self) -> int:
        """Get numeric log level for this layer."""
        return LogLevel.get_level(self.level)


class LayerManager:
    """Manages logging layers with intelligent fallback and caching."""
    
    def __init__(self):
        self._layers: Dict[str, LayerConfiguration] = {}
        self._handlers: Dict[str, List[HandlerInterface]] = {}
        self._layer_levels: Dict[str, int] = {}
        self._cache_manager = CacheManager()
        self._lock = threading.RLock()
        
        # Multi-layer optimization flags
        self._multi_layer_mode = False
        self._layer_count = 0
        self._default_layer_name = "default"
    
    def setup_layers(self, config_layers: Dict[str, Any]) -> None:
        """
        Setup logging layers from configuration.
        
        Args:
            config_layers: Dictionary of layer configurations
        """
        with self._lock:
            if not config_layers:
                self._setup_default_layer()
                return
            
            for layer_name, layer_config in config_layers.items():
                try:
                    self._create_layer(layer_name, layer_config)
                except Exception as e:
                    # Log error and continue with other layers
                    print(f"Layer setup failed for {layer_name}: {e}")
            
            self._update_multi_layer_flags()
    
    def _create_layer(self, layer_name: str, layer_config: Any) -> None:
        """Create a layer from configuration."""
        try:
            # Handle both dict and object configs
            if isinstance(layer_config, dict):
                level = layer_config.get('level', 'INFO')
                destinations = layer_config.get('destinations', [])
            else:
                level = getattr(layer_config, 'level', 'INFO')
                destinations = getattr(layer_config, 'destinations', [])
            
            # Create layer configuration
            layer = LayerConfiguration(layer_name, level, destinations)
            self._layers[layer_name] = layer
            
            # Create handlers for this layer
            handlers = []
            for destination_config in destinations:
                handler = self._create_handler_from_config(destination_config)
                if handler:
                    handlers.append(handler)
            
            # Set handlers and update mappings
            layer.set_handlers(handlers)
            self._handlers[layer_name] = handlers
            self._layer_levels[layer_name] = layer.get_level_numeric()
            
        except Exception as e:
            raise RuntimeError(f"Failed to create layer '{layer_name}': {e}") from e
    
    def _create_handler_from_config(self, destination_config: Any) -> Optional[HandlerInterface]:
        """Create a handler from destination configuration."""
        try:
            # Handle both dict and object configs
            if isinstance(destination_config, dict):
                dest_type = destination_config.get('type', 'console')
            else:
                dest_type = getattr(destination_config, 'type', 'console')
            
            # Import handlers dynamically to avoid circular imports
            if dest_type == 'console':
                from ..handlers.console import SyncConsoleHandler
                from ..formatters import get_formatter
                
                # Get format type from destination config
                format_type = destination_config.get('format', 'plain-text')
                use_colors = destination_config.get('use_colors', False)
                
                # Create console handler with appropriate formatter
                console_handler = SyncConsoleHandler(
                    stream=destination_config.get('stream', 'stdout'),
                    use_colors=use_colors
                )
                
                # Set the appropriate formatter based on format type
                formatter = get_formatter(format_type, use_colors=use_colors)
                if formatter:
                    console_handler.setFormatter(formatter)
                
                return console_handler
            elif dest_type == 'file':
                from ..handlers.file import FileHandler
                return FileHandler(
                    filename=destination_config.get('path') or destination_config.get('filename'),
                    max_bytes=destination_config.get('max_size', '10MB'),
                    backup_count=destination_config.get('backup_count', 5)
                )
            elif dest_type == 'null':
                from ..handlers.null import NullHandler
                return NullHandler()
            else:
                # For unsupported types, return null handler
                from ..handlers.null import NullHandler
                return NullHandler()
                
        except Exception as e:
            print(f"Handler creation failed: {e}")
            return None
    
    def _setup_default_layer(self) -> None:
        """Setup a default layer with console output."""
        try:
            from ..handlers.console import SyncConsoleHandler
            from ..formatters.text import ColoredFormatter
            
            # Create default console handler
            console_handler = SyncConsoleHandler(
                stream='stdout',
                use_colors=True
            )
            
            # Create default formatter using standardized formatters
            from ..formatters import get_formatter
            formatter = get_formatter('colored', use_colors=True)
            console_handler.setFormatter(formatter)
            
            # Setup default layer
            default_layer = LayerConfiguration(self._default_layer_name, "WARNING")
            default_layer.set_handlers([console_handler])
            default_layer.set_formatter(formatter)
            
            self._layers[self._default_layer_name] = default_layer
            self._handlers[self._default_layer_name] = [console_handler]
            self._layer_levels[self._default_layer_name] = LogLevel.WARNING
            
        except Exception as e:
            print(f"Default layer setup failed: {e}")
    
    def _update_multi_layer_flags(self) -> None:
        """Update multi-layer optimization flags."""
        self._layer_count = len(self._handlers)
        self._multi_layer_mode = self._layer_count > 1
    
    def get_handlers_for_layer(self, layer: str) -> List[HandlerInterface]:
        """
        Get handlers for a layer with intelligent fallback and caching.
        
        Args:
            layer: The requested layer name
            
        Returns:
            List of handlers for the layer
        """
        return self._cache_manager.get_layer_handlers(layer, self._handlers)
    
    def get_layer_threshold(self, layer: str) -> int:
        """
        Get minimum log level for a layer.
        
        Args:
            layer: The layer name
            
        Returns:
            Numeric log level threshold
        """
        return self._layer_levels.get(layer, self._layer_levels.get(self._default_layer_name, LogLevel.INFO))
    
    def get_layer_names(self) -> List[str]:
        """Get list of all layer names."""
        with self._lock:
            return list(self._layers.keys())
    
    def has_layer(self, layer: str) -> bool:
        """Check if a layer exists."""
        with self._lock:
            return layer in self._layers
    
    def get_layer_config(self, layer: str) -> Optional[LayerConfiguration]:
        """Get configuration for a specific layer."""
        with self._lock:
            return self._layers.get(layer)
    
    def add_layer(self, layer_name: str, level: str = "INFO") -> None:
        """Add a new layer."""
        with self._lock:
            if layer_name in self._layers:
                raise ValueError(f"Layer '{layer_name}' already exists")
            
            layer = LayerConfiguration(layer_name, level)
            self._layers[layer_name] = layer
            self._handlers[layer_name] = []
            self._layer_levels[layer_name] = layer.get_level_numeric()
            self._update_multi_layer_flags()
    
    def remove_layer(self, layer_name: str) -> bool:
        """Remove a layer."""
        with self._lock:
            if layer_name == self._default_layer_name:
                raise ValueError("Cannot remove default layer")
            
            if layer_name in self._layers:
                del self._layers[layer_name]
                del self._handlers[layer_name]
                del self._layer_levels[layer_name]
                self._update_multi_layer_flags()
                return True
            return False
    
    def get_multi_layer_stats(self) -> Dict[str, Any]:
        """Get multi-layer optimization statistics."""
        with self._lock:
            return {
                "multi_layer_mode": self._multi_layer_mode,
                "layer_count": self._layer_count,
                "default_layer": self._default_layer_name,
                "available_layers": list(self._layers.keys()),
                "cache_stats": self._cache_manager.get_comprehensive_stats()
            }
    
    def clear_all(self) -> None:
        """Clear all layers and handlers."""
        with self._lock:
            self._layers.clear()
            self._handlers.clear()
            self._layer_levels.clear()
            self._cache_manager.clear_all()
            self._multi_layer_mode = False
            self._layer_count = 0
    
    def get_cache_manager(self) -> CacheManager:
        """Get the cache manager instance."""
        return self._cache_manager
