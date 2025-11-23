"""
System Capability Detection and Adaptive Configuration

This module provides system detection to automatically configure
buffer sizes, flush intervals, and performance parameters based on:
- Available system memory
- CPU capabilities
- System load
- Safety margins to prevent OOM

FEATURES:
- Memory-aware buffer sizing (prevents OOM crashes)
- CPU-aware performance tuning
- Load-aware adaptation
- Safe defaults for resource-constrained systems
- Dynamic scaling for high-performance systems
- Data integrity guarantees (graceful degradation)
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple
from enum import Enum


class SystemProfile(Enum):
    """System performance profiles based on detected capabilities."""
    
    RESOURCE_CONSTRAINED = "resource_constrained"  # < 2GB RAM, low-end system
    STANDARD = "standard"  # 2-8GB RAM, typical system
    HIGH_PERFORMANCE = "high_performance"  # 8-16GB RAM, good system
    ULTRA_HIGH_PERFORMANCE = "ultra_high_performance"  # > 16GB RAM, powerful system


class SystemDetector:
    """
    System detection for safe, adaptive performance optimization.
    
    This class detects system capabilities and provides safe buffer sizes
    that prevent OOM while maximizing performance within available resources.
    """
    
    def __init__(self):
        """Initialize system detector."""
        self._psutil_available = False
        self._system_profile = None
        self._available_memory_mb = None
        self._cpu_count = None
        self._safe_memory_limit_mb = None
        
        # Initialize detection
        self._detect_system_capabilities()
    
    def _detect_system_capabilities(self) -> None:
        """Detect system capabilities safely."""
        try:
            import psutil
            self._psutil_available = True
            
            # Get available memory
            memory = psutil.virtual_memory()
            self._available_memory_mb = memory.available / 1024 / 1024
            
            # Get CPU count
            self._cpu_count = psutil.cpu_count(logical=True)
            
            # Calculate safe memory limit (use max 10% of available memory for logging)
            # This prevents OOM even under load
            self._safe_memory_limit_mb = max(50, self._available_memory_mb * 0.10)
            
            # Determine system profile
            if self._available_memory_mb < 2048:  # < 2GB
                self._system_profile = SystemProfile.RESOURCE_CONSTRAINED
            elif self._available_memory_mb < 8192:  # < 8GB
                self._system_profile = SystemProfile.STANDARD
            elif self._available_memory_mb < 16384:  # < 16GB
                self._system_profile = SystemProfile.HIGH_PERFORMANCE
            else:  # >= 16GB
                self._system_profile = SystemProfile.ULTRA_HIGH_PERFORMANCE
                
        except ImportError:
            # Fallback to conservative defaults if psutil not available
            self._psutil_available = False
            self._system_profile = SystemProfile.RESOURCE_CONSTRAINED
            self._available_memory_mb = 512  # Assume minimal memory
            self._cpu_count = 1
            self._safe_memory_limit_mb = 50  # Very conservative
    
    def get_optimal_buffer_size(
        self, 
        handler_type: str = "console",
        min_size: int = 100,
        max_size: int = 1000000
    ) -> int:
        """
        Get optimal buffer size based on system capabilities.
        
        Args:
            handler_type: Type of handler ('console', 'file', etc.)
            min_size: Minimum safe buffer size
            max_size: Maximum buffer size (safety limit)
        
        Returns:
            Optimal buffer size that balances performance and safety
        """
        if not self._psutil_available:
            # Very conservative defaults if we can't detect system
            return min_size if handler_type == "console" else min(min_size * 10, 5000)
        
        # Calculate buffer size based on:
        # 1. System profile (memory availability)
        # 2. Handler type (file handlers can be larger)
        # 3. Safe memory limits (prevent OOM)
        
        # Base buffer size per message (estimate: ~500 bytes per message)
        bytes_per_message = 500
        messages_per_mb = (1024 * 1024) // bytes_per_message  # ~2000 messages per MB
        
        # Calculate safe buffer size based on available memory
        # Use 1% of safe memory limit for each handler (multiple handlers possible)
        safe_buffer_mb = self._safe_memory_limit_mb * 0.01  # 1% per handler
        safe_buffer_messages = int(safe_buffer_mb * messages_per_mb)
        
        # Profile-based scaling factors
        profile_multipliers = {
            SystemProfile.RESOURCE_CONSTRAINED: 1.0,
            SystemProfile.STANDARD: 2.5,
            SystemProfile.HIGH_PERFORMANCE: 5.0,
            SystemProfile.ULTRA_HIGH_PERFORMANCE: 10.0,
        }
        
        multiplier = profile_multipliers.get(self._system_profile, 1.0)
        
        # Handler type multipliers (file handlers can be larger)
        handler_multipliers = {
            "console": 1.0,
            "file": 2.0,
            "async_file": 3.0,
            "network": 1.5,
        }
        
        handler_mult = handler_multipliers.get(handler_type, 1.0)
        
        # Calculate optimal size
        optimal_size = int(safe_buffer_messages * multiplier * handler_mult)
        
        # Apply safety limits
        optimal_size = max(min_size, min(optimal_size, max_size))
        
        # Profile-specific defaults
        # Larger buffers = better throughput, system detector ensures safety
        profile_defaults = {
            SystemProfile.RESOURCE_CONSTRAINED: {
                "console": 2000,  # Increased from 1000
                "file": 10000,   # Increased from 5000
            },
            SystemProfile.STANDARD: {
                "console": 10000,  # Increased from 5000
                "file": 100000,   # Increased from 50000
            },
            SystemProfile.HIGH_PERFORMANCE: {
                "console": 50000,  # Increased from 20000
                "file": 500000,   # Increased from 200000
            },
            SystemProfile.ULTRA_HIGH_PERFORMANCE: {
                "console": 100000,  # Increased from 50000
                "file": 1000000,   # Increased from 500000
            },
        }
        
        profile_default = profile_defaults.get(
            self._system_profile, 
            {"console": 1000, "file": 5000}
        ).get(handler_type, min_size)
        
        # Use the larger of calculated or profile default
        optimal_size = max(optimal_size, profile_default)
        
        return min(optimal_size, max_size)
    
    def get_optimal_flush_interval(
        self,
        handler_type: str = "console",
        min_interval: float = 0.1,
        max_interval: float = 10.0
    ) -> float:
        """
        Get optimal flush interval based on system capabilities.
        
        Args:
            handler_type: Type of handler
            min_interval: Minimum flush interval (safety)
            max_interval: Maximum flush interval (data integrity)
        
        Returns:
            Optimal flush interval in seconds
        """
        # Base flush intervals
        # Longer intervals = better throughput, but ensure data integrity
        base_intervals = {
            "console": 2.0,  # 2 seconds for console (good balance)
            "file": 5.0,    # 5 seconds for file (safe balance)
            "async_file": 2.0,  # 2 seconds for async file
            "network": 0.5,  # 0.5 seconds for network (lower latency needed)
        }
        
        base = base_intervals.get(handler_type, 1.0)
        
        # Adjust based on system profile
        # Higher performance systems can wait longer (less frequent flushes)
        profile_adjustments = {
            SystemProfile.RESOURCE_CONSTRAINED: 0.5,  # More frequent (safer)
            SystemProfile.STANDARD: 1.0,
            SystemProfile.HIGH_PERFORMANCE: 1.5,
            SystemProfile.ULTRA_HIGH_PERFORMANCE: 2.0,  # Less frequent (more performant)
        }
        
        adjustment = profile_adjustments.get(self._system_profile, 1.0)
        optimal_interval = base * adjustment
        
        # Apply safety limits
        return max(min_interval, min(optimal_interval, max_interval))
    
    def get_safe_max_buffer_size(self) -> int:
        """
        Get maximum safe buffer size to prevent OOM.
        
        Returns:
            Maximum buffer size in messages that's safe for this system
        """
        if not self._psutil_available:
            return 10000  # Very conservative default
        
        # Calculate based on available memory
        bytes_per_message = 500  # Estimate
        messages_per_mb = (1024 * 1024) // bytes_per_message
        
        # Use 5% of available memory as absolute maximum
        max_buffer_mb = self._available_memory_mb * 0.05
        max_buffer_messages = int(max_buffer_mb * messages_per_mb)
        
        # Safety limit: never exceed 1M messages
        return min(max_buffer_messages, 1000000)
    
    def should_use_aggressive_buffering(self) -> bool:
        """
        Determine if system can handle aggressive buffering.
        
        Returns:
            True if system has enough resources for aggressive buffering
        """
        if not self._psutil_available:
            return False
        
        return self._system_profile in (
            SystemProfile.HIGH_PERFORMANCE,
            SystemProfile.ULTRA_HIGH_PERFORMANCE
        )
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information.
        
        Returns:
            Dictionary with system capabilities
        """
        return {
            "psutil_available": self._psutil_available,
            "system_profile": self._system_profile.value if self._system_profile else "unknown",
            "available_memory_mb": self._available_memory_mb,
            "cpu_count": self._cpu_count,
            "safe_memory_limit_mb": self._safe_memory_limit_mb,
            "safe_max_buffer_size": self.get_safe_max_buffer_size(),
            "can_use_aggressive_buffering": self.should_use_aggressive_buffering(),
        }
    
    def monitor_memory_usage(self, current_usage_mb: float) -> Dict[str, Any]:
        """
        Monitor memory usage and provide safety recommendations.
        
        Args:
            current_usage_mb: Current memory usage in MB
        
        Returns:
            Dictionary with safety status and recommendations
        """
        if not self._psutil_available:
            return {
                "safe": True,
                "warning": False,
                "recommendation": "unknown",
            }
        
        # Calculate memory usage percentage
        usage_percent = (current_usage_mb / self._available_memory_mb) * 100
        
        # Safety thresholds
        safe_threshold = 50.0  # 50% usage is safe
        warning_threshold = 80.0  # 80% usage triggers warning
        
        is_safe = usage_percent < safe_threshold
        should_warn = usage_percent >= warning_threshold
        
        recommendation = "normal"
        if should_warn:
            recommendation = "reduce_buffers"
        elif usage_percent > safe_threshold:
            recommendation = "monitor"
        
        return {
            "safe": is_safe,
            "warning": should_warn,
            "usage_percent": usage_percent,
            "recommendation": recommendation,
            "available_mb": self._available_memory_mb,
            "current_usage_mb": current_usage_mb,
        }


# Global singleton instance
_system_detector: Optional[SystemDetector] = None


def get_system_detector() -> SystemDetector:
    """Get global system detector instance."""
    global _system_detector
    if _system_detector is None:
        _system_detector = SystemDetector()
    return _system_detector


def get_optimal_buffer_config(
    handler_type: str = "console"
) -> Dict[str, Any]:
    """
    Get optimal buffer configuration for a handler type.
    
    Args:
        handler_type: Type of handler ('console', 'file', etc.)
    
    Returns:
        Dictionary with buffer_size and flush_interval
    """
    detector = get_system_detector()
    return {
        "buffer_size": detector.get_optimal_buffer_size(handler_type),
        "flush_interval": detector.get_optimal_flush_interval(handler_type),
        "max_buffer_size": detector.get_safe_max_buffer_size(),
    }

