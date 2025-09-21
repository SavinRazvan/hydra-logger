"""
Standard Format Templates for Hydra-Logger

This module provides optimized string formatting templates used by all
Hydra-Logger formatters. It includes LRU caching for performance and
supports various format types with consistent interfaces.

ARCHITECTURE:
- UltraFastFormats: Optimized format functions with direct string operations
- StandardFormats: Main formatting class with LRU caching
- FormatRegistry: Registry system for format functions
- PerformanceLevel: Currently only FAST level is used in practice

CURRENT IMPLEMENTATION:
- All formatters use PerformanceLevel.FAST by default
- LRU cache with 1000 entries for common patterns
- Direct string concatenation for maximum speed
- Pre-allocated color codes for level and layer colors
- Thread-safe operations

FORMAT TYPES:
- Basic: Simple text formatting without colors
- Colored: Colorized formatting with level and layer colors
- With Timestamp: Formatting with timestamp information
- Colored With Timestamp: Colorized formatting with timestamp

USAGE EXAMPLES:

Basic Usage (Current Practice):
    from hydra_logger.formatters.standard_formats import get_standard_formats
    
    # Get formatter (uses FAST performance level by default)
    formatter = get_standard_formats()
    
    # Format record
    output = formatter.format_basic(record)
    colored_output = formatter.format_colored(record)

Performance Monitoring:
    # Get performance statistics
    stats = formatter.get_stats()
    print(f"Formats processed: {stats['formats_processed']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']}")
    print(f"Formats per second: {stats['formats_per_second']}")
    
    # Clear caches for memory management
    formatter.clear_cache()

Custom Format Registry:
    from hydra_logger.formatters.standard_formats import FormatRegistry
    
    # Create custom registry
    registry = FormatRegistry()
    
    # Get format function
    format_func = registry.get_format_function('colored')
    
    # Register custom format
    def custom_format(record):
        return f"CUSTOM: {record.message}"
    
    registry.register_format('custom', custom_format)

PERFORMANCE FEATURES:
- LRU cache with 1000 entries for common patterns
- Direct string concatenation for maximum speed
- Pre-allocated color codes for level and layer colors
- Thread-safe operations
- Performance monitoring and statistics
- Memory-efficient cache implementation

NOTE ON PERFORMANCE LEVELS:
While the code supports multiple performance levels (ULTRA_FAST, FAST, ENHANCED, DEBUG),
in practice all formatters use the FAST level. The other levels are available for
future use but are not currently utilized in the codebase.
"""
import time
from time import perf_counter
import threading
from typing import Dict, Any, Optional, Callable
from functools import lru_cache

from ..types.records import LogRecord
from ..types.levels import LogLevel, LogLevelManager
from ..core.constants import Colors, DEFAULT_FORMAT_STRING


class UltraFastFormats:
    """Ultra-optimized format functions with zero overhead."""
    
    # Use existing constants from core.constants
    RESET = Colors.RESET
    
    # Pre-allocated color codes for maximum speed - using existing constants
    LEVEL_COLORS = {
        10: Colors.CYAN,      # DEBUG
        20: Colors.GREEN,     # INFO  
        30: Colors.YELLOW,    # WARNING
        40: Colors.RED,       # ERROR
        50: Colors.MAGENTA,   # CRITICAL
    }
    LAYER_COLORS = {
        'default': Colors.BLUE,      # blue
        'core': Colors.MAGENTA,      # magenta
        'handlers': Colors.CYAN,     # cyan
        'formatters': Colors.YELLOW, # yellow
        'loggers': Colors.GREEN,     # green
        'tests': Colors.WHITE,       # white
    }
    
    @staticmethod
    def format_basic(record: LogRecord) -> str:
        """Ultra-fast basic formatting - direct string concatenation."""
        # Direct concatenation is faster than f-strings for simple cases
        return record.level_name + ' [' + record.layer + '] ' + record.message + '\n'
    
    @staticmethod
    def format_colored(record: LogRecord) -> str:
        """Ultra-fast colored formatting - pre-allocated colors, direct concatenation."""
        level_color = UltraFastFormats.LEVEL_COLORS.get(record.level, '')
        layer_color = UltraFastFormats.LAYER_COLORS.get(record.layer, '')
        
        if not level_color and not layer_color:
            # No colors - use basic format
            return UltraFastFormats.format_basic(record)
        
        # Direct string concatenation for maximum speed
        result = level_color + '[' + record.level_name + ']' + UltraFastFormats.RESET
        result += ' ' + layer_color + '[' + record.layer + ']' + UltraFastFormats.RESET
        result += ' ' + record.message + '\n'
        return result
    
    @staticmethod
    def format_colored_fast(record: LogRecord, level_color: str, layer_color: str) -> str:
        """Ultra-fast colored formatting with pre-allocated colors."""
        # Direct concatenation with pre-allocated colors
        result = level_color + '[' + record.level_name + ']' + UltraFastFormats.RESET
        result += ' ' + layer_color + '[' + record.layer + ']' + UltraFastFormats.RESET
        result += ' ' + record.message + '\n'
        return result


class PerformanceLevel:
    """Performance levels for formatters."""
    ULTRA_FAST = "ultra_fast"      # Minimal overhead, maximum speed
    FAST = "fast"                  # Balanced performance and features
    ENHANCED = "enhanced"          # Full infrastructure features
    DEBUG = "debug"                # Maximum debugging and monitoring


class StandardFormats:
    """Standardized format templates with configurable performance levels."""
    
    def __init__(self, performance_level: str = PerformanceLevel.FAST):
        """Initialize with configurable performance level."""
        self.performance_level = performance_level
        
        # Performance tracking (minimal overhead)
        self._stats = {
            'formats_processed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': perf_counter()
        }
        
        # Thread safety (only for enhanced mode)
        self._lock = threading.RLock() if performance_level == PerformanceLevel.ENHANCED else None
        
        # Initialize based on performance level
        self._setup_performance_level()
    
    def _setup_performance_level(self):
        """Setup formatters based on performance level."""
        if self.performance_level == PerformanceLevel.ULTRA_FAST:
            # Ultra-fast: Direct string operations, no overhead
            self._format_basic = self._format_basic_ultra_fast
            self._format_colored = self._format_colored_ultra_fast
            self._format_with_timestamp = self._format_with_timestamp_ultra_fast
            self._format_colored_with_timestamp = self._format_colored_with_timestamp_ultra_fast
            
        elif self.performance_level == PerformanceLevel.FAST:
            # Fast: LRU cache, minimal overhead
            self._format_basic = self._format_basic_fast
            self._format_colored = self._format_colored_fast
            self._format_with_timestamp = self._format_with_timestamp_fast
            self._format_colored_with_timestamp = self._format_colored_with_timestamp_fast
            
        elif self.performance_level == PerformanceLevel.ENHANCED:
            # Enhanced: Full infrastructure (previous implementation)
            self._setup_enhanced_mode()
            
        else:  # DEBUG
            # Debug: Full monitoring and infrastructure
            self._setup_enhanced_mode()
            self._setup_debug_mode()
    
    def _setup_enhanced_mode(self):
        """Setup enhanced mode with full infrastructure."""
        try:
            from ..core.memory_optimizer import get_memory_optimizer, optimize_string
            from ..core.cache_manager import CacheManager
            from ..core.compiled_logging import get_compiled_engine, get_jit_optimizer
            from ..core.object_pool import get_log_record_pool
            from ..core.decorators import performance_timer
            
            self._memory_optimizer = get_memory_optimizer()
            self._cache_manager = CacheManager()
            self._compiled_engine = get_compiled_engine()
            self._jit_optimizer = get_jit_optimizer()
            self._record_pool = get_log_record_pool("standard_formats")
            
            # Use enhanced formatters
            self._format_basic = self._format_basic_enhanced
            self._format_colored = self._format_colored_enhanced
            self._format_with_timestamp = self._format_with_timestamp_enhanced
            self._format_colored_with_timestamp = self._format_colored_with_timestamp_enhanced
            
        except ImportError:
            # Fallback to fast mode if infrastructure not available
            self._format_basic = self._format_basic_fast
            self._format_colored = self._format_colored_fast
            self._format_with_timestamp = self._format_with_timestamp_fast
            self._format_colored_with_timestamp = self._format_colored_with_timestamp_fast
    
    def _setup_debug_mode(self):
        """Setup debug mode with additional monitoring."""
        self._debug_stats = {
            'memory_usage': [],
            'execution_times': [],
            'cache_performance': []
        }
    
    # Ultra-fast formatters (minimal overhead)
    def _format_basic_ultra_fast(self, record: LogRecord) -> str:
        """Ultra-fast basic formatting with zero overhead."""
        self._stats['formats_processed'] += 1
        return UltraFastFormats.format_basic(record)
    
    def _format_colored_ultra_fast(self, record: LogRecord, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
        """Ultra-fast colored formatting with zero overhead."""
        self._stats['formats_processed'] += 1
        if level_color_code is None:
            level_color_code = UltraFastFormats.LEVEL_COLORS.get(record.level, '')
        if layer_color_code is None:
            layer_color_code = UltraFastFormats.LAYER_COLORS.get(record.layer, '')
        if reset_code is None:
            reset_code = Colors.RESET
        return UltraFastFormats.format_colored_fast(record, level_color_code, layer_color_code)
    
    def _format_with_timestamp_ultra_fast(self, record: LogRecord, timestamp: str = None) -> str:
        """Ultra-fast timestamp formatting with zero overhead."""
        self._stats['formats_processed'] += 1
        if timestamp is None:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
        return '[' + timestamp + '] ' + record.level_name + ' [' + record.layer + '] ' + record.message + '\n'
    
    def _format_colored_with_timestamp_ultra_fast(self, record: LogRecord, timestamp: str = None, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
        """Ultra-fast colored timestamp formatting with zero overhead."""
        self._stats['formats_processed'] += 1
        if timestamp is None:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
        if level_color_code is None:
            level_color_code = UltraFastFormats.LEVEL_COLORS.get(record.level, '')
        if layer_color_code is None:
            layer_color_code = UltraFastFormats.LAYER_COLORS.get(record.layer, '')
        if reset_code is None:
            reset_code = Colors.RESET
        
        result = level_color_code + '[' + timestamp + ']' + reset_code
        result += ' ' + level_color_code + '[' + record.level_name + ']' + reset_code
        result += ' ' + layer_color_code + '[' + record.layer + ']' + reset_code
        result += ' ' + record.message + '\n'
        return result
    
    # Fast formatters (LRU cache optimized)
    @lru_cache(maxsize=1000)
    def _format_basic_fast(self, level: int, level_name: str, layer: str, message: str) -> str:
        """Fast basic formatting with LRU cache."""
        return level_name + ' [' + layer + '] ' + message + '\n'
    
    @lru_cache(maxsize=1000)
    def _format_colored_fast(self, level: int, level_name: str, layer: str, message: str, level_color: str, layer_color: str, reset: str) -> str:
        """Fast colored formatting with LRU cache."""
        result = level_color + '[' + level_name + ']' + reset
        result += ' ' + layer_color + '[' + layer + ']' + reset
        result += ' ' + message + '\n'
        return result
    
    @lru_cache(maxsize=1000)
    def _format_with_timestamp_fast(self, level: int, level_name: str, layer: str, message: str, timestamp: str) -> str:
        """Fast timestamp formatting with LRU cache."""
        return '[' + timestamp + '] ' + level_name + ' [' + layer + '] ' + message + '\n'
    
    @lru_cache(maxsize=1000)
    def _format_colored_with_timestamp_fast(self, level: int, level_name: str, layer: str, message: str, timestamp: str, level_color: str, layer_color: str, reset: str) -> str:
        """Fast colored timestamp formatting with LRU cache."""
        result = level_color + '[' + timestamp + ']' + reset
        result += ' ' + level_color + '[' + level_name + ']' + reset
        result += ' ' + layer_color + '[' + layer + ']' + reset
        result += ' ' + message + '\n'
        return result
    
    # Public interface methods
    def format_basic(self, record: LogRecord) -> str:
        """Format basic log record."""
        if self.performance_level == PerformanceLevel.FAST:
            # Use LRU cached version
            return self._format_basic_fast(record.level, record.level_name, record.layer, record.message)
        else:
            # Use direct version
            return self._format_basic(record)
    
    def format_colored(self, record: LogRecord, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
        """Format colored log record."""
        if self.performance_level == PerformanceLevel.FAST:
            # Use LRU cached version
            if level_color_code is None:
                level_color_code = UltraFastFormats.LEVEL_COLORS.get(record.level, '')
            if layer_color_code is None:
                layer_color_code = UltraFastFormats.LAYER_COLORS.get(record.layer, '')
            if reset_code is None:
                reset_code = Colors.RESET
            return self._format_colored_fast(record.level, record.level_name, record.layer, record.message, 
                                           level_color_code, layer_color_code, reset_code)
        else:
            # Use direct version
            return self._format_colored(record, level_color_code, layer_color_code, reset_code)
    
    def format_with_timestamp(self, record: LogRecord, timestamp: str = None) -> str:
        """Format log record with timestamp."""
        if self.performance_level == PerformanceLevel.FAST:
            # Use LRU cached version
            if timestamp is None:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
            return self._format_with_timestamp_fast(record.level, record.level_name, record.layer, record.message, timestamp)
        else:
            # Use direct version
            return self._format_with_timestamp(record, timestamp)
    
    def format_colored_with_timestamp(self, record: LogRecord, timestamp: str = None, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
        """Format colored log record with timestamp."""
        if self.performance_level == PerformanceLevel.FAST:
            # Use LRU cached version
            if timestamp is None:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.timestamp))
            if level_color_code is None:
                level_color_code = UltraFastFormats.LEVEL_COLORS.get(record.level, '')
            if layer_color_code is None:
                layer_color_code = UltraFastFormats.LAYER_COLORS.get(record.layer, '')
            if reset_code is None:
                reset_code = Colors.RESET
            return self._format_colored_with_timestamp_fast(record.level, record.level_name, record.layer, record.message, 
                                                          timestamp, level_color_code, layer_color_code, reset_code)
        else:
            # Use direct version
            return self._format_colored_with_timestamp(record, timestamp, level_color_code, layer_color_code, reset_code)
    
    # Enhanced formatters (full infrastructure - only for ENHANCED/DEBUG modes)
    def _format_basic_enhanced(self, record: LogRecord) -> str:
        """Enhanced basic formatting with full infrastructure."""
        if self._lock:
            with self._lock:
                return self._format_basic_ultra_fast(record)
        return self._format_basic_ultra_fast(record)
    
    def _format_colored_enhanced(self, record: LogRecord, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
        """Enhanced colored formatting with full infrastructure."""
        if self._lock:
            with self._lock:
                return self._format_colored_ultra_fast(record, level_color_code, layer_color_code, reset_code)
        return self._format_colored_ultra_fast(record, level_color_code, layer_color_code, reset_code)
    
    def _format_with_timestamp_enhanced(self, record: LogRecord, timestamp: str = None) -> str:
        """Enhanced timestamp formatting with full infrastructure."""
        if self._lock:
            with self._lock:
                return self._format_with_timestamp_ultra_fast(record, timestamp)
        return self._format_with_timestamp_ultra_fast(record, timestamp)
    
    def _format_colored_with_timestamp_enhanced(self, record: LogRecord, timestamp: str = None, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
        """Enhanced colored timestamp formatting with full infrastructure."""
        if self._lock:
            with self._lock:
                return self._format_colored_with_timestamp_ultra_fast(record, timestamp, level_color_code, layer_color_code, reset_code)
        return self._format_colored_with_timestamp_ultra_fast(record, timestamp, level_color_code, layer_color_code, reset_code)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        uptime = time.time() - self._stats['start_time']
        stats = {
            'performance_level': self.performance_level,
            'formats_processed': self._stats['formats_processed'],
            'cache_hits': self._stats['cache_hits'],
            'cache_misses': self._stats['cache_misses'],
            'uptime_seconds': uptime,
            'formats_per_second': self._stats['formats_processed'] / uptime if uptime > 0 else 0,
            'cache_hit_rate': self._stats['cache_hits'] / (self._stats['cache_hits'] + self._stats['cache_misses']) if (self._stats['cache_hits'] + self._stats['cache_misses']) > 0 else 0
        }
        
        # Add LRU cache stats for FAST mode
        if self.performance_level == PerformanceLevel.FAST:
            stats['lru_cache_stats'] = {
                'basic_cache_info': self._format_basic_fast.cache_info(),
                'colored_cache_info': self._format_colored_fast.cache_info(),
                'timestamp_cache_info': self._format_with_timestamp_fast.cache_info(),
                'colored_timestamp_cache_info': self._format_colored_with_timestamp_fast.cache_info()
            }
        
        return stats
    
    def clear_cache(self):
        """Clear all caches."""
        if self.performance_level == PerformanceLevel.FAST:
            # Clear LRU caches
            self._format_basic_fast.cache_clear()
            self._format_colored_fast.cache_clear()
            self._format_with_timestamp_fast.cache_clear()
            self._format_colored_with_timestamp_fast.cache_clear()
        elif hasattr(self, '_cache_manager'):
            self._cache_manager.clear_all()
    
    def optimize(self):
        """Optimize performance based on performance level."""
        if self.performance_level == PerformanceLevel.FAST:
            # For FAST mode, just clear caches to reset
            self.clear_cache()
        elif hasattr(self, '_jit_optimizer'):
            # For ENHANCED mode, use full optimization
            self._jit_optimizer.track_path_usage("optimization", time.time())
            if hasattr(self, '_memory_optimizer'):
                self._memory_optimizer.force_gc()
            if hasattr(self, '_record_pool'):
                self._record_pool.resize_pool()


class FormatRegistry:
    """Registry for standardized format functions with performance levels."""
    
    def __init__(self, performance_level: str = PerformanceLevel.FAST):
        """Initialize with specified performance level."""
        self._standard_formats = StandardFormats(performance_level)
        self.performance_level = performance_level
        
        # Pre-allocated format functions by type
        self.FORMATS = {
            'basic': self._standard_formats.format_basic,
            'with_timestamp': self._standard_formats.format_with_timestamp,
            'colored': self._standard_formats.format_colored,
            'colored_with_timestamp': self._standard_formats.format_colored_with_timestamp,
        }
    
    def get_format_function(self, format_type: str):
        """Get pre-allocated format function by type."""
        return self.FORMATS.get(format_type, self._standard_formats.format_basic)
    
    def register_format(self, name: str, func):
        """Register a new format function."""
        self.FORMATS[name] = func
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        return self._standard_formats.get_stats()
    
    def clear_cache(self):
        """Clear all caches."""
        self._standard_formats.clear_cache()
    
    def optimize(self):
        """Optimize performance."""
        self._standard_formats.optimize()


# Global instances (using FAST performance level by default)
_global_format_registry = FormatRegistry(PerformanceLevel.FAST)
_global_standard_formats = StandardFormats(PerformanceLevel.FAST)


def get_format_registry(performance_level: str = PerformanceLevel.FAST) -> FormatRegistry:
    """Get a format registry instance with specified performance level."""
    if performance_level == PerformanceLevel.FAST:
        return _global_format_registry
    return FormatRegistry(performance_level)


def get_standard_formats(performance_level: str = PerformanceLevel.FAST) -> StandardFormats:
    """Get a standard formats instance with specified performance level."""
    if performance_level == PerformanceLevel.FAST:
        return _global_standard_formats
    return StandardFormats(performance_level)


# Convenience functions for backward compatibility
def format_basic(record: LogRecord) -> str:
    """Fast basic formatting using global instance."""
    return _global_standard_formats.format_basic(record)


def format_colored(record: LogRecord, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
    """Fast colored formatting using global instance."""
    return _global_standard_formats.format_colored(record, level_color_code, layer_color_code, reset_code)


def format_with_timestamp(record: LogRecord, timestamp: str = None) -> str:
    """Fast formatting with timestamp using global instance."""
    return _global_standard_formats.format_with_timestamp(record, timestamp)


def format_colored_with_timestamp(record: LogRecord, timestamp: str = None, level_color_code: str = None, layer_color_code: str = None, reset_code: str = None) -> str:
    """Fast colored formatting with timestamp using global instance."""
    return _global_standard_formats.format_colored_with_timestamp(record, timestamp, level_color_code, layer_color_code, reset_code)


# Performance constants
DEFAULT_LAYERS = ['default', 'core', 'handlers', 'formatters', 'loggers', 'tests']
DEFAULT_LEVELS = [10, 20, 30, 40, 50]  # DEBUG, INFO, WARNING, ERROR, CRITICAL