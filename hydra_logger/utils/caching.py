"""
Caching Utilities for Hydra-Logger

This module provides comprehensive caching utilities with multiple backends,
eviction policies, and performance monitoring. It supports both memory-based
and file-based caching with configurable policies and statistics tracking.

FEATURES:
- Multiple cache backends (memory, file)
- Various eviction policies (LRU, LFU, FIFO, TTL)
- Performance monitoring and statistics
- Thread-safe operations with locking
- Configurable size limits and TTL
- Cache entry metadata and tracking
- High-performance LRU cache for formatting operations

CACHE BACKENDS:
- MemoryCache: In-memory cache with OrderedDict
- FileCache: File-based cache with serialization
- LRUCache: Lightweight LRU cache for high performance

EVICTION POLICIES:
- LRU: Least Recently Used
- LFU: Least Frequently Used
- FIFO: First In, First Out
- TTL: Time To Live

USAGE:
    from hydra_logger.utils import CacheManager, MemoryCache, LRUCache
    
    # High-level cache management
    manager = CacheManager()
    cache = manager.create_cache("my_cache", max_size=1000)
    cache.set("key", "value", ttl=3600)
    value = cache.get("key")
    
    # Direct cache usage
    memory_cache = MemoryCache(max_size=1000, policy=CachePolicy.LRU)
    memory_cache.set("key", "value")
    value = memory_cache.get("key")
    
    # High-performance LRU cache
    lru_cache = LRUCache(max_size=1000)
    lru_cache.set("key", "value")
    value = lru_cache.get("key")
"""

import os
import json
import pickle
import hashlib
import time
import threading
import tempfile
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Generic, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict
import shutil


class CachePolicy(Enum):
    """Cache eviction policies."""

    LRU = "lru"     # Least Recently Used
    LFU = "lfu"     # Least Frequently Used
    FIFO = "fifo"   # First In, First Out
    TTL = "ttl"     # Time To Live


class CacheBackend(Enum):
    """Available cache backends."""

    MEMORY = "memory"
    FILE = "file"
    REDIS = "redis"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl: Optional[float] = None
    size: Optional[int] = None

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() > (self.created_at + self.ttl)

    def touch(self):
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1

    def get_age(self) -> float:
        """Get age of entry in seconds."""
        return time.time() - self.created_at

    def get_time_to_live(self) -> Optional[float]:
        """Get remaining time to live in seconds."""
        if self.ttl is None:
            return None
        remaining = (self.created_at + self.ttl) - time.time()
        return max(0, remaining)


@dataclass
class CacheStats:
    """Cache statistics and metrics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_entries: int = 0
    total_size: int = 0
    max_size: int = 0
    max_entries: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """Calculate miss rate percentage."""
        return 100.0 - self.hit_rate

    @property
    def efficiency(self) -> float:
        """Calculate cache efficiency (hits vs total requests)."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0


T = TypeVar("T")


class BaseCache(Generic[T]):
    """Base cache class with common functionality."""

    def __init__(
        self,
        max_size: int = 1000,
        max_entries: int = 10000,
        policy: CachePolicy = CachePolicy.LRU,
        default_ttl: Optional[float] = None,
    ):
        """Initialize base cache."""
        self.max_size = max_size
        self.max_entries = max_entries
        self.policy = policy
        self.default_ttl = default_ttl
        self.stats = CacheStats(max_size=max_size, max_entries=max_entries)
        self._lock = threading.RLock()

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get value from cache."""
        raise NotImplementedError

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> bool:
        """Set value in cache."""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        raise NotImplementedError

    def keys(self) -> List[str]:
        """Get all cache keys."""
        raise NotImplementedError

    def values(self) -> List[T]:
        """Get all cache values."""
        raise NotImplementedError

    def items(self) -> List[Tuple[str, T]]:
        """Get all cache items."""
        raise NotImplementedError

    def size(self) -> int:
        """Get current cache size."""
        raise NotImplementedError

    def count(self) -> int:
        """Get current cache entry count."""
        raise NotImplementedError

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        raise NotImplementedError

    def _evict_entries(self) -> None:
        """Evict entries based on policy."""
        raise NotImplementedError


class MemoryCache(BaseCache[T]):
    """In-memory cache implementation."""

    def __init__(
        self,
        max_size: int = 1000,
        max_entries: int = 10000,
        policy: CachePolicy = CachePolicy.LRU,
        default_ttl: Optional[float] = None,
    ):
        """Initialize memory cache."""
        super().__init__(max_size, max_entries, policy, default_ttl)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._size_map: Dict[str, int] = {}

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get value from memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    self._remove_entry(key)
                    self.stats.misses += 1
                    return default

                entry.touch()
                # Move to end for LRU policy
                self._cache.move_to_end(key)
                self.stats.hits += 1
                return entry.value

            self.stats.misses += 1
            return default

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> bool:
        """Set value in memory cache."""
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)

            # Calculate entry size
            entry_size = self._estimate_size(value)
            ttl = ttl if ttl is not None else self.default_ttl

            # Check if we need to evict entries
            while (
                self._cache and len(self._cache) >= self.max_entries
                or self.stats.total_size + entry_size > self.max_size
            ):
                self._evict_entries()

            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                ttl=ttl,
                size=entry_size,
            )

            self._cache[key] = entry
            self._size_map[key] = entry_size
            self.stats.total_entries = len(self._cache)
            self.stats.total_size += entry_size

            return True

    def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        with self._lock:
            return self._remove_entry(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._size_map.clear()
            self.stats.total_entries = 0
            self.stats.total_size = 0

    def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    self._remove_entry(key)
                    return False
                return True
            return False

    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())

    def values(self) -> List[T]:
        """Get all cache values."""
        with self._lock:
            self._cleanup_expired()
            return [entry.value for entry in self._cache.values()]

    def items(self) -> List[Tuple[str, T]]:
        """Get all cache items."""
        with self._lock:
            self._cleanup_expired()
            return [(key, entry.value) for key, entry in self._cache.items()]

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return self.stats.total_size

    def count(self) -> int:
        """Get current cache entry count."""
        with self._lock:
            return len(self._cache)

    def _remove_entry(self, key: str) -> bool:
        """Remove entry from cache."""
        if key in self._cache:
            entry = self._cache[key]
            self.stats.total_size -= entry.size or 0
            del self._cache[key]
            del self._size_map[key]
            self.stats.total_entries = len(self._cache)
            return True
        return False

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items() if entry.is_expired()
        ]
        for key in expired_keys:
            self._remove_entry(key)

    def _evict_entries(self) -> None:
        """Evict entries based on policy."""
        if not self._cache:
            return

        if self.policy == CachePolicy.LRU:
            # Remove least recently used
            key = next(iter(self._cache))
        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used
            key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
        elif self.policy == CachePolicy.FIFO:
            # Remove first in
            key = next(iter(self._cache))
        else:  # TTL
            # Remove oldest
            key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)

        self._remove_entry(key)
        self.stats.evictions += 1

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes."""
        try:
            # Rough estimation - can be improved
            if isinstance(value, (str, bytes)):
                return len(value)
            elif isinstance(value, (int, float)):
                return 8
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(
                    self._estimate_size(k) + self._estimate_size(v)
                    for k, v in value.items()
                )
            else:
                return 100  # Default size for complex objects
        except Exception:
            return 100


class FileCache(BaseCache[T]):
    """File-based cache implementation."""

    def __init__(
        self,
        cache_dir: str,
        max_size: int = 1000,
        max_entries: int = 10000,
        policy: CachePolicy = CachePolicy.LRU,
        default_ttl: Optional[float] = None,
        serializer: str = "pickle",
    ):
        """Initialize file cache."""
        super().__init__(max_size, max_entries, policy, default_ttl)
        self.cache_dir = cache_dir
        self.serializer = serializer
        self._index_file = os.path.join(cache_dir, ".cache_index")
        self._index: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        self._load_index()

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """Get value from file cache."""
        with self._lock:
            if key not in self._index:
                self.stats.misses += 1
                return default

            entry_info = self._index[key]
            if self._is_expired(entry_info):
                self._remove_entry(key)
                self.stats.misses += 1
                return default

            try:
                file_path = self._get_file_path(key)
                if not os.path.exists(file_path):
                    self._remove_entry(key)
                    self.stats.misses += 1
                    return default

                value = self._deserialize_value(file_path)
                if value is not None:
                    # Update access info
                    entry_info["accessed_at"] = time.time()
                    entry_info["access_count"] += 1
                    self._save_index()
                    self.stats.hits += 1
                    return value

            except Exception:
                pass

            self.stats.misses += 1
            return default

    def set(self, key: str, value: T, ttl: Optional[float] = None) -> bool:
        """Set value in file cache."""
        with self._lock:
            try:
                # Remove existing entry if present
                if key in self._index:
                    self._remove_entry(key)

                # Check if we need to evict entries
                while (
                    len(self._index) >= self.max_entries
                    or self._get_total_size() >= self.max_size
                ):
                    self._evict_entries()

                # Serialize and save value
                file_path = self._get_file_path(key)
                if self._serialize_value(value, file_path):
                    ttl = ttl if ttl is not None else self.default_ttl
                    entry_size = os.path.getsize(file_path)

                    entry_info = {
                        "key": key,
                        "file_path": file_path,
                        "created_at": time.time(),
                        "accessed_at": time.time(),
                        "access_count": 0,
                        "ttl": ttl,
                        "size": entry_size,
                    }

                    self._index[key] = entry_info
                    self._save_index()
                    self.stats.total_entries = len(self._index)
                    self.stats.total_size = self._get_total_size()

                    return True

            except Exception:
                pass

            return False

    def delete(self, key: str) -> bool:
        """Delete value from file cache."""
        with self._lock:
            return self._remove_entry(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            try:
                # Remove all cache files
                for entry_info in self._index.values():
                    file_path = entry_info.get("file_path")
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)

                # Clear index
                self._index.clear()
                self._save_index()
                self.stats.total_entries = 0
                self.stats.total_size = 0

            except Exception:
                pass

    def exists(self, key: str) -> bool:
        """Check if key exists in file cache."""
        with self._lock:
            if key not in self._index:
                return False

            entry_info = self._index[key]
            if self._is_expired(entry_info):
                self._remove_entry(key)
                return False

            file_path = entry_info.get("file_path")
            return file_path and os.path.exists(file_path)

    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            self._cleanup_expired()
            return list(self._index.keys())

    def values(self) -> List[T]:
        """Get all cache values."""
        with self._lock:
            self._cleanup_expired()
            values = []
            for key in self._index:
                value = self.get(key)
                if value is not None:
                    values.append(value)
            return values

    def items(self) -> List[Tuple[str, T]]:
        """Get all cache items."""
        with self._lock:
            self._cleanup_expired()
            items = []
            for key in self._index:
                value = self.get(key)
                if value is not None:
                    items.append((key, value))
            return items

    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return self._get_total_size()

    def count(self) -> int:
        """Get current cache entry count."""
        with self._lock:
            return len(self._index)

    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key."""
        # Create a safe filename from the key
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.cache")

    def _serialize_value(self, value: T, file_path: str) -> bool:
        """Serialize value to file."""
        try:
            if self.serializer == "pickle":
                with open(file_path, "wb") as f:
                    pickle.dump(value, f)
            elif self.serializer == "json":
                with open(file_path, "w") as f:
                    json.dump(value, f)
            else:
                return False
            return True
        except Exception:
            return False

    def _deserialize_value(self, file_path: str) -> Optional[T]:
        """Deserialize value from file."""
        try:
            if self.serializer == "pickle":
                with open(file_path, "rb") as f:
                    return pickle.load(f)
            elif self.serializer == "json":
                with open(file_path, "r") as f:
                    return json.load(f)
            else:
                return None
        except Exception:
            return None

    def _is_expired(self, entry_info: Dict[str, Any]) -> bool:
        """Check if entry is expired."""
        ttl = entry_info.get("ttl")
        if ttl is None:
            return False
        created_at = entry_info.get("created_at", 0)
        return time.time() > (created_at + ttl)

    def _remove_entry(self, key: str) -> bool:
        """Remove entry from cache."""
        if key in self._index:
            entry_info = self._index[key]
            file_path = entry_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

            del self._index[key]
            self._save_index()
            self.stats.total_entries = len(self._index)
            self.stats.total_size = self._get_total_size()
            return True
        return False

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry_info in self._index.items() if self._is_expired(entry_info)
        ]
        for key in expired_keys:
            self._remove_entry(key)

    def _evict_entries(self) -> None:
        """Evict entries based on policy."""
        if not self._index:
            return

        if self.policy == CachePolicy.LRU:
            # Remove least recently used
            key = min(
                self._index.keys(),
                key=lambda k: self._index[k].get("accessed_at", 0),
            )
        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used
            key = min(
                self._index.keys(),
                key=lambda k: self._index[k].get("access_count", 0),
            )
        elif self.policy == CachePolicy.FIFO:
            # Remove first in
            key = min(
                self._index.keys(),
                key=lambda k: self._index[k].get("created_at", 0),
            )
        else:  # TTL
            # Remove oldest
            key = min(
                self._index.keys(),
                key=lambda k: self._index[k].get("created_at", 0),
            )

        self._remove_entry(key)
        self.stats.evictions += 1

    def _get_total_size(self) -> int:
        """Get total size of all cache files."""
        total_size = 0
        for entry_info in self._index.values():
            file_path = entry_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    total_size += os.path.getsize(file_path)
                except Exception:
                    pass
        return total_size

    def _load_index(self) -> None:
        """Load cache index from file."""
        try:
            if os.path.exists(self._index_file):
                with open(self._index_file, "r") as f:
                    self._index = json.load(f)
                    self.stats.total_entries = len(self._index)
                    self.stats.total_size = self._get_total_size()
        except Exception:
            self._index = {}

    def _save_index(self) -> None:
        """Save cache index to file."""
        try:
            with open(self._index_file, "w") as f:
                json.dump(self._index, f)
        except Exception:
            pass


class CacheManager:
    """High-level cache management with multiple backends."""

    def __init__(self):
        """Initialize cache manager."""
        self._caches: Dict[str, BaseCache] = {}
        self._default_backend = CacheBackend.MEMORY

    def create_cache(
        self,
        name: str,
        backend: CacheBackend = CacheBackend.MEMORY,
        **kwargs
    ) -> BaseCache:
        """Create a new cache instance."""
        if backend == CacheBackend.MEMORY:
            cache = MemoryCache(**kwargs)
        elif backend == CacheBackend.FILE:
            cache_dir = kwargs.get("cache_dir", tempfile.mkdtemp())
            cache = FileCache(cache_dir=cache_dir, **kwargs)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

        self._caches[name] = cache
        return cache

    def get_cache(self, name: str) -> Optional[BaseCache]:
        """Get existing cache by name."""
        return self._caches.get(name)

    def remove_cache(self, name: str) -> bool:
        """Remove cache by name."""
        if name in self._caches:
            cache = self._caches[name]
            cache.clear()
            del self._caches[name]
            return True
        return False

    def list_caches(self) -> List[str]:
        """List all cache names."""
        return list(self._caches.keys())

    def get_cache_stats(self, name: str) -> Optional[CacheStats]:
        """Get statistics for specific cache."""
        cache = self._caches.get(name)
        return cache.get_stats() if cache else None

    def get_all_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all caches."""
        return {name: cache.get_stats() for name, cache in self._caches.items()}

    def clear_all(self) -> None:
        """Clear all caches."""
        for cache in self._caches.values():
            cache.clear()

    def cleanup_expired(self) -> None:
        """Clean up expired entries in all caches."""
        for cache in self._caches.values():
            cache._cleanup_expired()


class LRUCache:
    """
    Simple, high-performance LRU cache optimized for formatting operations.
    
    This is a lightweight alternative to the full-featured MemoryCache
    when you only need basic LRU functionality with maximum performance.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries to cache
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                value = self._cache.pop(key)
                self._cache[key] = value
                self._hits += 1
                return value
            
            self._misses += 1
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._cache.pop(key)
            
            # Add new entry
            self._cache[key] = value
            
            # Evict oldest if we exceed max size
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        with self._lock:
            return key in self._cache
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            
            return {
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'size': len(self._cache),
                'max_size': self.max_size
            }
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.exists(key)
    
    def __len__(self) -> int:
        """Get cache size."""
        return self.size()
    
    def __bool__(self) -> bool:
        """Return True if cache is initialized."""
        return True  # Cache is always True if initialized, regardless of entries
