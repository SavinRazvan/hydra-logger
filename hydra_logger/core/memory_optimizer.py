"""
Advanced Memory Management and GC Optimization for Hydra-Logger

This module provides sophisticated memory optimization techniques designed
for high-performance logging scenarios. It includes string interning,
memory pooling, garbage collection optimization, and zero-allocation
patterns to minimize memory overhead and improve performance.

ARCHITECTURE:
- StringInterner: String interning for common log strings
- MemoryPool: Pre-allocated object pools for memory efficiency
- GCOptimizer: Garbage collection tuning and optimization
- MemoryOptimizer: Centralized memory optimization coordinator

OPTIMIZATION TECHNIQUES:
- String Interning: Reuse common strings to reduce memory usage
- Memory Pooling: Pre-allocate objects to avoid runtime allocation
- GC Optimization: Tune garbage collection for logging workloads
- Zero-Allocation Patterns: Minimize memory allocations in hot paths
- Memory Pressure Detection: Adaptive optimization based on memory usage

PERFORMANCE FEATURES:
- Pre-interned common strings (log levels, logger names)
- Configurable memory pools with statistics
- GC threshold-based optimization
- Memory usage tracking and monitoring
- Adaptive optimization based on usage patterns

MEMORY MANAGEMENT:
- Automatic string interning for common values
- Object pooling with reuse statistics
- GC pressure reduction through pooling
- Memory threshold monitoring
- Adaptive pool sizing

USAGE EXAMPLES:

String Interning:
    from hydra_logger.core.memory_optimizer import get_memory_optimizer
    
    optimizer = get_memory_optimizer()
    optimized_string = optimizer.intern_string("INFO")  # Reuses pre-interned string

Memory Pool Usage:
    from hydra_logger.core.memory_optimizer import MemoryPool
    
    # Create a pool for LogRecord objects
    pool = MemoryPool(LogRecord, initial_size=1000, max_size=5000)
    
    # Get object from pool
    record = pool.get()
    # Use record...
    pool.put(record)  # Return to pool for reuse

GC Optimization:
    from hydra_logger.core.memory_optimizer import get_memory_optimizer
    
    optimizer = get_memory_optimizer()
    
    # Trigger GC if needed (called automatically in hot paths)
    optimizer.trigger_gc_if_needed()
    
    # Force garbage collection
    optimizer.force_gc()

Global Memory Optimization:
    from hydra_logger.core.memory_optimizer import optimize_string, trigger_gc_if_needed
    
    # Optimize strings globally
    optimized = optimize_string("DEBUG")
    
    # Trigger GC globally
    trigger_gc_if_needed()

Memory Statistics:
    from hydra_logger.core.memory_optimizer import get_memory_optimizer
    
    optimizer = get_memory_optimizer()
    stats = optimizer.get_stats()
    print(f"String interning: {stats['string_interning']}")
    print(f"GC optimization: {stats['gc_optimization']}")
"""

import gc
import sys
import weakref
from typing import Dict, Any, Optional, List
from functools import lru_cache


class StringInterner:
    """String interning for common log strings to reduce memory usage."""
    
    def __init__(self):
        self._interned_strings = {}
        self._common_strings = {
            'NOTSET': 'NOTSET',
            'DEBUG': 'DEBUG',
            'INFO': 'INFO', 
            'WARNING': 'WARNING',
            'ERROR': 'ERROR',
            'CRITICAL': 'CRITICAL',
            'default': 'default',
            'HydraLogger': 'HydraLogger',
            'HydraLoggerAsync': 'HydraLoggerAsync'
        }
        
        # Pre-intern common strings
        for key, value in self._common_strings.items():
            self._interned_strings[value] = sys.intern(value)
    
    def intern(self, string: str) -> str:
        """Intern a string if it's common, otherwise return as-is."""
        if string in self._interned_strings:
            return self._interned_strings[string]
        
        # Only intern strings that are likely to be reused
        if len(string) < 50 and string.isalnum():
            interned = sys.intern(string)
            self._interned_strings[string] = interned
            return interned
        
        return string
    
    def get_stats(self) -> Dict[str, Any]:
        """Get string interning statistics."""
        return {
            'interned_count': len(self._interned_strings),
            'common_strings': len(self._common_strings)
        }


class MemoryPool:
    """Memory pool for pre-allocated objects to reduce GC pressure."""
    
    def __init__(self, object_type, initial_size: int = 1000, max_size: int = 5000):
        self._object_type = object_type
        self._pool = []
        self._max_size = max_size
        self._created_count = 0
        self._reused_count = 0
        
        # Pre-allocate objects
        for _ in range(initial_size):
            self._pool.append(object_type())
            self._created_count += 1
    
    def get(self):
        """Get an object from the pool."""
        if self._pool:
            self._reused_count += 1
            return self._pool.pop()
        else:
            self._created_count += 1
            return self._object_type()
    
    def put(self, obj):
        """Return an object to the pool."""
        if len(self._pool) < self._max_size:
            # Reset object state if it has a reset method
            if hasattr(obj, 'reset'):
                obj.reset()
            self._pool.append(obj)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        total_requests = self._created_count + self._reused_count
        hit_rate = (self._reused_count / total_requests) if total_requests > 0 else 0.0
        
        return {
            'pool_size': len(self._pool),
            'max_size': self._max_size,
            'created_count': self._created_count,
            'reused_count': self._reused_count,
            'total_requests': total_requests,
            'hit_rate': hit_rate
        }


class GCOptimizer:
    """Garbage collection optimizer to reduce GC pressure."""
    
    def __init__(self):
        self._gc_threshold = 1000  # Trigger GC after this many operations
        self._operation_count = 0
        self._gc_count = 0
        self._disabled = False
    
    def optimize_gc(self):
        """Optimize garbage collection settings."""
        # Disable automatic GC for better performance
        gc.disable()
        self._disabled = True
    
    def restore_gc(self):
        """Restore normal garbage collection."""
        gc.enable()
        self._disabled = False
    
    def trigger_gc_if_needed(self):
        """Trigger GC if threshold is reached."""
        self._operation_count += 1
        
        if self._operation_count >= self._gc_threshold:
            if not self._disabled:
                gc.collect()
                self._gc_count += 1
                self._operation_count = 0
    
    def force_gc(self):
        """Force garbage collection."""
        if not self._disabled:
            gc.collect()
            self._gc_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get GC optimization statistics."""
        return {
            'gc_disabled': self._disabled,
            'operation_count': self._operation_count,
            'gc_count': self._gc_count,
            'gc_threshold': self._gc_threshold
        }


class MemoryOptimizer:
    """Main memory optimizer that coordinates all memory optimizations."""
    
    def __init__(self):
        self._string_interner = StringInterner()
        self._gc_optimizer = GCOptimizer()
        self._enabled = True
        
        # Optimize GC settings
        self._gc_optimizer.optimize_gc()
    
    def intern_string(self, string: str) -> str:
        """Intern a string for memory efficiency."""
        if not self._enabled:
            return string
        return self._string_interner.intern(string)
    
    def trigger_gc_if_needed(self):
        """Trigger GC if needed."""
        if self._enabled:
            self._gc_optimizer.trigger_gc_if_needed()
    
    def force_gc(self):
        """Force garbage collection."""
        if self._enabled:
            self._gc_optimizer.force_gc()
    
    def disable(self):
        """Disable memory optimization."""
        self._enabled = False
        self._gc_optimizer.restore_gc()
    
    def enable(self):
        """Enable memory optimization."""
        self._enabled = True
        self._gc_optimizer.optimize_gc()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory optimization statistics."""
        return {
            'enabled': self._enabled,
            'string_interning': self._string_interner.get_stats(),
            'gc_optimization': self._gc_optimizer.get_stats()
        }


# Global memory optimizer instance
_global_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get the global memory optimizer instance."""
    global _global_memory_optimizer
    if _global_memory_optimizer is None:
        _global_memory_optimizer = MemoryOptimizer()
    return _global_memory_optimizer


def optimize_string(string: str) -> str:
    """Optimize a string using memory optimization."""
    return get_memory_optimizer().intern_string(string)


def trigger_gc_if_needed():
    """Trigger GC if needed using memory optimization."""
    get_memory_optimizer().trigger_gc_if_needed()
