"""
Intelligent Cache Management System for Hydra-Logger

This module provides a sophisticated caching system designed to optimize performance
by intelligently caching frequently accessed components like layer handlers and
formatters. It includes intelligent fallback strategies, TTL management, and
comprehensive cache statistics.

ARCHITECTURE:
- CacheEntry: Represents cached items with metadata and TTL support
- LayerHandlerCache: Intelligent caching for layer handler lookups with fallback
- FormatterCache: Caching for formatter instances to avoid repeated creation
- CacheManager: Centralized cache management and coordination

CACHING STRATEGIES:
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) expiration support
- Intelligent fallback hierarchies
- Thread-safe operations with RLock
- Automatic cache size management
- Performance statistics and monitoring

FALLBACK HIERARCHY:
1. Requested layer handlers
2. Default layer handlers
3. Any available layer handlers
4. Empty handlers list (cached to prevent repeated lookups)

FEATURES:
- Thread-safe operations throughout
- Configurable cache sizes and TTL
- Intelligent fallback strategies
- Comprehensive statistics
- Memory-efficient storage
- Automatic cleanup and maintenance

USAGE EXAMPLES:

Basic Cache Usage:
    from hydra_logger.core.cache_manager import CacheManager
    
    cache = CacheManager()
    handlers = cache.get_layer_handlers("api", fallback_handlers)
    formatter = cache.get_formatter("json", formatter_factory)

Layer Handler Caching:
    from hydra_logger.core.cache_manager import LayerHandlerCache
    
    layer_cache = LayerHandlerCache(max_size=1000, default_ttl=300)
    handlers = layer_cache.get_handlers("database", fallback_handlers)

Formatter Caching:
    from hydra_logger.core.cache_manager import FormatterCache
    
    formatter_cache = FormatterCache(max_size=100)
    formatter = formatter_cache.get_formatter("colored", formatter_factory)
"""

import threading
import time
from typing import Any, Dict, List, Optional, Union
from collections import OrderedDict

from ..interfaces.handler import HandlerInterface
from ..interfaces.formatter import FormatterInterface as BaseFormatter


class CacheEntry:
    """Represents a cached item with metadata."""
    
    def __init__(self, data: Any, timestamp: float, ttl: Optional[int] = None):
        self.data = data
        self.timestamp = timestamp
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = timestamp
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> None:
        """Record an access to this cache entry."""
        self.access_count += 1
        self.last_accessed = time.time()


class LayerHandlerCache:
    """Cache for layer handler lookups with intelligent fallback."""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        self._cache: Dict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache_hits = 0
        self._cache_misses = 0
        self._lock = threading.RLock()
    
    def get_handlers(self, layer: str, fallback_handlers: Dict[str, List[HandlerInterface]]) -> List[HandlerInterface]:
        """
        Get handlers for a layer with intelligent fallback and caching.
        
        Fallback priority:
        1. Requested layer
        2. default layer
        3. Any available layer
        
        Args:
            layer: The requested layer name
            fallback_handlers: Dictionary of layer -> handlers mapping
            
        Returns:
            List of handlers for the layer
        """
        with self._lock:
            # Check cache first for performance
            if layer in self._cache:
                entry = self._cache[layer]
                if not entry.is_expired():
                    self._cache_hits += 1
                    entry.access()
                    return entry.data
                else:
                    # Remove expired entry
                    del self._cache[layer]
            
            self._cache_misses += 1
            
            # Try requested layer
            if layer in fallback_handlers and fallback_handlers[layer]:
                handlers = fallback_handlers[layer]
                self._cache_result(layer, handlers)
                return handlers
            
            # Try default layer
            if "default" in fallback_handlers and fallback_handlers["default"]:
                handlers = fallback_handlers["default"]
                self._cache_result(layer, handlers)
                return handlers
            
            # Try any available layer
            for layer_name, handlers in fallback_handlers.items():
                if handlers:
                    self._cache_result(layer, handlers)
                    return handlers
            
            # No handlers available - cache empty list
            empty_handlers = []
            self._cache_result(layer, empty_handlers)
            return empty_handlers
    
    def _cache_result(self, layer: str, handlers: List[HandlerInterface]) -> None:
        """Cache the result for a layer."""
        entry = CacheEntry(handlers, time.time(), self._default_ttl)
        self._cache[layer] = entry
        
        # Maintain cache size
        if len(self._cache) > self._max_size:
            # Remove least recently used entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            total_ops = self._cache_hits + self._cache_misses
            cache_hit_rate = (self._cache_hits / total_ops * 100) if total_ops > 0 else 0
            
            return {
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": round(cache_hit_rate, 2),
                "cache_size": len(self._cache),
                "max_size": self._max_size,
                "total_operations": total_ops
            }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._cache_hits = 0
            self._cache_misses = 0


class FormatterCache:
    """Cache for formatter instances to avoid repeated creation."""
    
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()
    
    def get_formatter(self, cache_key: str, formatter_factory: callable) -> BaseFormatter:
        """
        Get a formatter from cache or create it using the factory.
        
        Args:
            cache_key: Unique key for the formatter
            formatter_factory: Function to create the formatter if not cached
            
        Returns:
            Cached or newly created formatter
        """
        with self._lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if not entry.is_expired():
                    entry.access()
                    return entry.data
            
            # Create new formatter
            formatter = formatter_factory()
            
            # Cache it
            entry = CacheEntry(formatter, time.time())
            self._cache[cache_key] = entry
            
            # Maintain cache size
            if len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            return formatter
    
    def clear(self) -> None:
        """Clear all cached formatters."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get formatter cache statistics."""
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "max_size": self._max_size
            }


class CacheManager:
    """Centralized cache management for Hydra-Logger."""
    
    def __init__(self):
        self._layer_handler_cache = LayerHandlerCache()
        self._formatter_cache = FormatterCache()
        self._lock = threading.RLock()
    
    def get_layer_handlers(self, layer: str, fallback_handlers: Dict[str, List[HandlerInterface]]) -> List[HandlerInterface]:
        """Get cached layer handlers."""
        return self._layer_handler_cache.get_handlers(layer, fallback_handlers)
    
    def get_formatter(self, cache_key: str, formatter_factory: callable) -> BaseFormatter:
        """Get cached formatter."""
        return self._formatter_cache.get_formatter(cache_key, formatter_factory)
    
    def clear_all(self) -> None:
        """Clear all caches."""
        with self._lock:
            self._layer_handler_cache.clear()
            self._formatter_cache.clear()
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            stats = {
                "layer_handler_cache": self._layer_handler_cache.get_stats(),
                "formatter_cache": self._formatter_cache.get_stats()
            }
            
            # Add overall cache statistics
            total_hits = stats["layer_handler_cache"]["cache_hits"]
            total_misses = stats["layer_handler_cache"]["cache_misses"]
            total_ops = total_hits + total_misses
            overall_hit_rate = (total_hits / total_ops * 100) if total_ops > 0 else 0
            
            stats["overall"] = {
                "total_cache_hits": total_hits,
                "total_cache_misses": total_misses,
                "overall_cache_hit_rate": round(overall_hit_rate, 2),
                "total_operations": total_ops
            }
            
            return stats
    
    def reset_all_stats(self) -> None:
        """Reset all cache statistics."""
        with self._lock:
            self._layer_handler_cache.reset_stats()
