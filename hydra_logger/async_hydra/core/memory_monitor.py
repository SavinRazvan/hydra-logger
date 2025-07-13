"""
Professional MemoryMonitor for memory usage monitoring and backpressure.

This module provides real-time memory usage tracking with configurable
thresholds and caching to avoid excessive system calls.
"""

import time
from typing import Dict, Any, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class MemoryMonitor:
    """
    Professional memory monitoring with caching and thresholds.
    
    Features:
    - Real-time memory usage tracking
    - Configurable memory thresholds
    - Caching to avoid excessive system calls
    - Professional warning system
    - Comprehensive memory statistics
    """
    
    def __init__(self, max_percent: float = 70.0, check_interval: float = 5.0):
        """
        Initialize MemoryMonitor.
        
        Args:
            max_percent: Maximum memory usage percentage
            check_interval: Minimum interval between checks in seconds
        """
        self._max_percent = max_percent
        self._check_interval = check_interval
        self._warning_logged = False
        self._last_check = 0
        self._last_result = True  # Default to OK
        self._start_time = time.time()
        self._stats = {
            'checks': 0,
            'warnings': 0,
            'last_memory_percent': 0,
            'peak_memory_percent': 0,
            'total_memory_mb': 0,
            'available_memory_mb': 0
        }
    
    def check_memory(self) -> bool:
        """
        Professional memory check with caching.
        
        Returns:
            bool: True if memory usage is acceptable, False otherwise
        """
        current_time = time.time()
        
        # Cache results to avoid excessive checks
        if current_time - self._last_check < self._check_interval:
            return self._last_result
        
        self._stats['checks'] += 1
        self._last_check = current_time
        
        try:
            if not PSUTIL_AVAILABLE:
                # If psutil is not available, assume memory is OK
                self._last_result = True
                return True
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_mb = memory.available / (1024 * 1024)
            total_mb = memory.total / (1024 * 1024)
            
            # Update statistics
            self._stats['last_memory_percent'] = memory_percent
            self._stats['total_memory_mb'] = total_mb
            self._stats['available_memory_mb'] = available_mb
            
            if memory_percent > self._stats['peak_memory_percent']:
                self._stats['peak_memory_percent'] = memory_percent
            
            if memory_percent > self._max_percent:
                if not self._warning_logged:
                    print(f"WARNING: Memory usage {memory_percent:.1f}% exceeds {self._max_percent}%")
                    self._warning_logged = True
                    self._stats['warnings'] += 1
                self._last_result = False
            else:
                self._warning_logged = False
                self._last_result = True
            
            return self._last_result
            
        except Exception as e:
            # If we can't check memory, assume it's OK
            print(f"Error checking memory usage: {e}")
            self._last_result = True
            return True
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get detailed memory statistics."""
        try:
            if PSUTIL_AVAILABLE:
                memory = psutil.virtual_memory()
                return {
                    'current_percent': memory.percent,
                    'available_mb': memory.available / (1024 * 1024),
                    'total_mb': memory.total / (1024 * 1024),
                    'used_mb': memory.used / (1024 * 1024),
                    'free_mb': memory.free / (1024 * 1024),
                    'max_threshold': self._max_percent,
                    'check_interval': self._check_interval,
                    'stats': self._stats.copy(),
                    'uptime': time.time() - self._start_time,
                    'psutil_available': True
                }
            else:
                return {
                    'current_percent': 0,
                    'available_mb': 0,
                    'total_mb': 0,
                    'used_mb': 0,
                    'free_mb': 0,
                    'max_threshold': self._max_percent,
                    'check_interval': self._check_interval,
                    'stats': self._stats.copy(),
                    'uptime': time.time() - self._start_time,
                    'psutil_available': False,
                    'note': 'psutil not available, memory monitoring disabled'
                }
        except Exception as e:
            return {
                'error': str(e),
                'max_threshold': self._max_percent,
                'check_interval': self._check_interval,
                'stats': self._stats.copy(),
                'uptime': time.time() - self._start_time,
                'psutil_available': PSUTIL_AVAILABLE
            }
    
    def set_threshold(self, percent: float) -> None:
        """Set memory threshold percentage."""
        self._max_percent = percent
    
    def set_check_interval(self, interval: float) -> None:
        """Set check interval in seconds."""
        self._check_interval = interval
    
    def reset_stats(self) -> None:
        """Reset memory statistics."""
        self._stats = {
            'checks': 0,
            'warnings': 0,
            'last_memory_percent': 0,
            'peak_memory_percent': 0,
            'total_memory_mb': 0,
            'available_memory_mb': 0
        }
        self._warning_logged = False
        self._start_time = time.time()
    
    def is_healthy(self) -> bool:
        """Check if memory usage is healthy."""
        return self.check_memory()
    
    def get_warning_count(self) -> int:
        """Get number of memory warnings."""
        return self._stats['warnings']
    
    def get_peak_memory_percent(self) -> float:
        """Get peak memory usage percentage."""
        return self._stats['peak_memory_percent'] 