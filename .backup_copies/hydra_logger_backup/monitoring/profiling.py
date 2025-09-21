"""
Performance Profiling Component for Hydra-Logger

This module provides comprehensive performance profiling with function-level
timing, call analysis, and optimization insights. It helps identify
performance bottlenecks and optimize code execution.

FEATURES:
- Function-level performance profiling
- Call count and timing analysis
- Slow function detection and reporting
- Profile history and analytics
- Context manager support for code blocks

USAGE:
    from hydra_logger.monitoring import Profiler
    
    # Create profiler
    profiler = Profiler(enabled=True, max_profiles=100)
    
    # Start monitoring
    profiler.start_monitoring()
    
    # Profile a function
    @profiler.profile_function(name="my_function")
    def my_function():
        # Function implementation
        pass
    
    # Profile a code block
    with profiler.profile_block("data_processing"):
        # Code block to profile
        pass
    
    # Get profiling results
    stats = profiler.get_function_stats("my_function")
"""

import time
import threading
import cProfile
import pstats
import io
import functools
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict, deque
from ..interfaces.monitor import MonitorInterface


class Profiler(MonitorInterface):
    """Real performance profiling component for code analysis and optimization."""
    
    def __init__(self, enabled: bool = True, max_profiles: int = 100):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        self._max_profiles = max_profiles
        
        # Profile storage
        self._profiles = {}
        self._profile_history = []
        self._active_profiles = {}
        
        # Performance metrics
        self._function_times = defaultdict(list)
        self._function_calls = defaultdict(int)
        self._slow_functions = deque(maxlen=100)
        
        # Profiling configuration
        self._profiling_config = {
            "enable_function_profiling": True,
            "enable_memory_profiling": False,
            "enable_line_profiling": False,
            "min_function_time": 0.001,  # 1ms minimum
            "max_profile_depth": 10
        }
        
        # Threading
        self._lock = threading.Lock()
        self._profiler_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_profiles = 0
        self._total_functions_profiled = 0
        self._last_profile_time = 0.0
    
    def start_monitoring(self) -> bool:
        """Start profiling monitoring."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop profiling monitoring."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                return True
        except Exception:
            return Exception
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def profile_function(self, func: Optional[Callable] = None, name: Optional[str] = None,
                        enabled: bool = True) -> Callable:
        """
        Decorator to profile a function.
        
        Args:
            func: Function to profile (when used as decorator)
            name: Custom name for the function
            enabled: Whether profiling is enabled for this function
            
        Returns:
            Decorated function
        """
        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if not self._enabled or not enabled:
                    return f(*args, **kwargs)
                
                func_name = name or f.__name__
                start_time = time.time()
                
                try:
                    result = f(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Record function timing
                    self._record_function_time(func_name, execution_time)
                    
                    # Check if function is slow
                    if execution_time > self._profiling_config["min_function_time"]:
                        self._record_slow_function(func_name, execution_time, args, kwargs)
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self._record_function_time(func_name, execution_time, error=str(e))
                    raise
                
            return wrapper
        
        if func is None:
            return decorator
        else:
            return decorator(func)
    
    def start_profile(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new profiling session.
        
        Args:
            name: Profile name
            metadata: Additional profile metadata
            
        Returns:
            Profile ID
        """
        if not self._enabled:
            return ""
        
        profile_id = self._generate_profile_id()
        current_time = time.time()
        
        profile = {
            "id": profile_id,
            "name": name,
            "start_time": current_time,
            "end_time": None,
            "duration": None,
            "metadata": metadata or {},
            "status": "active",
            "profiler": cProfile.Profile(),
            "stats": None
        }
        
        with self._lock:
            self._active_profiles[profile_id] = profile
            profile["profiler"].enable()
        
        return profile_id
    
    def stop_profile(self, profile_id: str) -> bool:
        """
        Stop a profiling session.
        
        Args:
            profile_id: Profile ID to stop
            
        Returns:
            True if profile stopped successfully
        """
        if not self._enabled or profile_id not in self._active_profiles:
            return False
        
        try:
            with self._lock:
                profile = self._active_profiles[profile_id]
                profile["profiler"].disable()
                
                # Get profile statistics
                s = io.StringIO()
                stats = pstats.Stats(profile["profiler"], stream=s)
                stats.sort_stats('cumulative')
                stats.print_stats(50)  # Top 50 functions
                
                profile["end_time"] = time.time()
                profile["duration"] = profile["end_time"] - profile["start_time"]
                profile["status"] = "completed"
                profile["stats"] = s.getvalue()
                
                # Move to completed profiles
                self._profiles[profile_id] = profile
                del self._active_profiles[profile_id]
                
                # Add to history
                self._profile_history.append(profile.copy())
                self._total_profiles += 1
                self._last_profile_time = profile["end_time"]
                
                # Keep history size manageable
                if len(self._profile_history) > self._max_profiles:
                    self._profile_history = self._profile_history[-self._max_profiles:]
                
                return True
                
        except Exception:
            return False
    
    def profile_block(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> 'ProfileBlock':
        """
        Context manager for profiling code blocks.
        
        Args:
            name: Block name
            metadata: Additional metadata
            
        Returns:
            ProfileBlock context manager
        """
        return ProfileBlock(self, name, metadata)
    
    def _record_function_time(self, func_name: str, execution_time: float, error: Optional[str] = None) -> None:
        """Record function execution time."""
        if not self._enabled:
            return
        
        with self._lock:
            self._function_times[func_name].append({
                "time": execution_time,
                "timestamp": time.time(),
                "error": error
            })
            
            self._function_calls[func_name] += 1
            self._total_functions_profiled += 1
            
            # Keep only recent timing data
            if len(self._function_times[func_name]) > 1000:
                self._function_times[func_name] = self._function_times[func_name][-1000:]
    
    def _record_slow_function(self, func_name: str, execution_time: float, 
                             args: tuple, kwargs: dict) -> None:
        """Record slow function execution."""
        if not self._enabled:
            return
        
        slow_function_info = {
            "name": func_name,
            "execution_time": execution_time,
            "timestamp": time.time(),
            "args_count": len(args),
            "kwargs_count": len(kwargs),
            "args_preview": str(args)[:100] if args else "",
            "kwargs_preview": str(kwargs)[:100] if kwargs else ""
        }
        
        self._slow_functions.append(slow_function_info)
    
    def _generate_profile_id(self) -> str:
        """Generate a unique profile ID."""
        timestamp = int(time.time() * 1000)
        return f"profile_{timestamp}_{self._total_profiles}"
    
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific profile by ID."""
        return self._profiles.get(profile_id)
    
    def get_active_profiles(self) -> List[Dict[str, Any]]:
        """Get all active profiles."""
        return list(self._active_profiles.values())
    
    def get_profile_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get profile history."""
        return self._profile_history[-limit:] if limit > 0 else self._profile_history.copy()
    
    def get_function_stats(self, func_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get statistics for a specific function.
        
        Args:
            func_name: Function name
            hours: Time period to analyze
            
        Returns:
            Function statistics
        """
        if not self._enabled or func_name not in self._function_times:
            return {}
        
        cutoff_time = time.time() - (hours * 3600)
        recent_times = [
            entry for entry in self._function_times[func_name]
            if entry["timestamp"] > cutoff_time
        ]
        
        if not recent_times:
            return {"function": func_name, "data_points": 0}
        
        execution_times = [entry["time"] for entry in recent_times]
        errors = [entry for entry in recent_times if entry["error"]]
        
        return {
            "function": func_name,
            "data_points": len(recent_times),
            "total_calls": self._function_calls[func_name],
            "execution_times": {
                "min": min(execution_times),
                "max": max(execution_times),
                "mean": sum(execution_times) / len(execution_times),
                "median": sorted(execution_times)[len(execution_times) // 2]
            },
            "errors": len(errors),
            "error_rate": len(errors) / len(recent_times) if recent_times else 0,
            "period_hours": hours
        }
    
    def get_slow_functions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of slow functions."""
        return list(self._slow_functions)[-limit:] if limit > 0 else list(self._slow_functions)
    
    def get_top_functions(self, metric: str = "calls", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top functions by specified metric.
        
        Args:
            metric: Metric to sort by (calls, time, errors)
            limit: Number of functions to return
            
        Returns:
            List of top functions
        """
        if not self._enabled:
            return []
        
        function_stats = []
        
        for func_name in self._function_calls:
            if func_name in self._function_times:
                recent_times = self._function_times[func_name][-100:]  # Last 100 calls
                if recent_times:
                    avg_time = sum(entry["time"] for entry in recent_times) / len(recent_times)
                    errors = sum(1 for entry in recent_times if entry["error"])
                    
                    function_stats.append({
                        "name": func_name,
                        "calls": self._function_calls[func_name],
                        "avg_time": avg_time,
                        "errors": errors,
                        "error_rate": errors / len(recent_times) if recent_times else 0
                    })
        
        # Sort by specified metric
        if metric == "calls":
            function_stats.sort(key=lambda x: x["calls"], reverse=True)
        elif metric == "time":
            function_stats.sort(key=lambda x: x["avg_time"], reverse=True)
        elif metric == "errors":
            function_stats.sort(key=lambda x: x["errors"], reverse=True)
        elif metric == "error_rate":
            function_stats.sort(key=lambda x: x["error_rate"], reverse=True)
        
        return function_stats[:limit] if limit > 0 else function_stats
    
    def clear_profiles(self) -> None:
        """Clear all profiles and history."""
        with self._lock:
            self._profiles.clear()
            self._active_profiles.clear()
            self._profile_history.clear()
            self._function_times.clear()
            self._function_calls.clear()
            self._slow_functions.clear()
            self._total_profiles = 0
            self._total_functions_profiled = 0
    
    def set_profiling_config(self, key: str, value: Any) -> bool:
        """Set profiling configuration."""
        if key in self._profiling_config:
            self._profiling_config[key] = value
            return True
        return False
    
    def get_profiling_config(self) -> Dict[str, Any]:
        """Get current profiling configuration."""
        return self._profiling_config.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get profiling metrics."""
        return {
            "total_profiles": self._total_profiles,
            "active_profiles": len(self._active_profiles),
            "total_functions_profiled": self._total_functions_profiled,
            "unique_functions": len(self._function_calls),
            "slow_functions": len(self._slow_functions),
            "last_profile_time": self._last_profile_time,
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
    
    def reset_metrics(self) -> None:
        """Reset profiling metrics."""
        self.clear_profiles()
    
    def is_healthy(self) -> bool:
        """Check if profiling system is healthy."""
        return len(self._active_profiles) < 50  # Consider healthy if less than 50 active profiles
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get profiling system health status."""
        return {
            "healthy": self.is_healthy(),
            "active_profiles": len(self._active_profiles),
            "total_profiles": self._total_profiles,
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }


class ProfileBlock:
    """Context manager for profiling code blocks."""
    
    def __init__(self, profiler: Profiler, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.profiler = profiler
        self.name = name
        self.metadata = metadata
        self.profile_id = None
    
    def __enter__(self):
        self.profile_id = self.profiler.start_profile(self.name, self.metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.profile_id:
            self.profiler.stop_profile(self.profile_id)
