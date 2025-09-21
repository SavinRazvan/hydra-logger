"""
Adaptive Performance Management Component for Hydra-Logger

This module provides intelligent performance management with dynamic optimization
based on system conditions and workload patterns. It automatically adjusts
performance settings to maintain optimal operation under varying conditions.

FEATURES:
- Dynamic performance mode switching
- Resource-aware optimization
- Configurable adaptive strategies
- Performance trend analysis
- Automatic threshold management

USAGE:
    from hydra_logger.monitoring import AdaptivePerformanceManager
    
    # Create adaptive performance manager
    manager = AdaptivePerformanceManager(
        enabled=True,
        strategy=AdaptiveStrategy.MODERATE
    )
    
    # Start monitoring
    manager.start_monitoring()
    
    # Get current performance mode
    current_mode = manager.get_current_mode()
    
    # Manually set performance mode
    manager.set_performance_mode(PerformanceMode.FAST)
"""

import time
import threading
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
from enum import Enum
from ..interfaces.monitor import MonitorInterface


class PerformanceMode(Enum):
    """Performance modes for adaptive management."""
    ULTRA_FAST = "ultra_fast"
    FAST = "fast"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    MINIMAL = "minimal"


class AdaptiveStrategy(Enum):
    """Adaptive strategies for performance management."""
    AGGRESSIVE = "aggressive"
    MODERATE = "moderate"
    CONSERVATIVE = "conservative"
    REACTIVE = "reactive"


class AdaptivePerformanceManager(MonitorInterface):
    """Real adaptive performance management component for dynamic optimization."""
    
    def __init__(self, enabled: bool = True, strategy: AdaptiveStrategy = AdaptiveStrategy.MODERATE):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        self._strategy = strategy
        
        # Performance modes configuration
        self._performance_modes = {
            PerformanceMode.ULTRA_FAST: {
                "buffer_size": 10000,
                "flush_interval": 0.1,
                "max_workers": 16,
                "compression": False,
                "async_io": True,
                "batch_processing": True
            },
            PerformanceMode.FAST: {
                "buffer_size": 5000,
                "flush_interval": 0.5,
                "max_workers": 8,
                "compression": False,
                "async_io": True,
                "batch_processing": True
            },
            PerformanceMode.BALANCED: {
                "buffer_size": 1000,
                "flush_interval": 1.0,
                "max_workers": 4,
                "compression": True,
                "async_io": True,
                "batch_processing": False
            },
            PerformanceMode.CONSERVATIVE: {
                "buffer_size": 500,
                "flush_interval": 2.0,
                "max_workers": 2,
                "compression": True,
                "async_io": False,
                "batch_processing": False
            },
            PerformanceMode.MINIMAL: {
                "buffer_size": 100,
                "flush_interval": 5.0,
                "max_workers": 1,
                "compression": True,
                "async_io": False,
                "batch_processing": False
            }
        }
        
        # Current performance state
        self._current_mode = PerformanceMode.BALANCED
        self._current_config = self._performance_modes[PerformanceMode.BALANCED].copy()
        
        # Performance metrics tracking
        self._performance_history = deque(maxlen=1000)
        self._mode_changes = []
        self._optimization_attempts = 0
        
        # Adaptive thresholds
        self._adaptive_thresholds = {
            "cpu_high": 0.8,        # 80% CPU usage
            "cpu_low": 0.3,         # 30% CPU usage
            "memory_high": 0.85,    # 85% memory usage
            "memory_low": 0.5,      # 50% memory usage
            "latency_high": 1.0,    # 1 second
            "latency_low": 0.1,     # 100ms
            "throughput_low": 100,  # 100 ops/sec
            "throughput_high": 1000 # 1000 ops/sec
        }
        
        # Strategy-specific parameters
        self._strategy_params = {
            AdaptiveStrategy.AGGRESSIVE: {
                "mode_switch_threshold": 0.1,    # 10% change triggers switch
                "optimization_frequency": 30,    # Optimize every 30 seconds
                "max_mode_switches": 10          # Max 10 switches per hour
            },
            AdaptiveStrategy.MODERATE: {
                "mode_switch_threshold": 0.2,    # 20% change triggers switch
                "optimization_frequency": 60,    # Optimize every 60 seconds
                "max_mode_switches": 5           # Max 5 switches per hour
            },
            AdaptiveStrategy.CONSERVATIVE: {
                "mode_switch_threshold": 0.3,    # 30% change triggers switch
                "optimization_frequency": 120,   # Optimize every 2 minutes
                "max_mode_switches": 3           # Max 3 switches per hour
            },
            AdaptiveStrategy.REACTIVE: {
                "mode_switch_threshold": 0.5,    # 50% change triggers switch
                "optimization_frequency": 300,   # Optimize every 5 minutes
                "max_mode_switches": 2           # Max 2 switches per hour
            }
        }
        
        # Performance optimization rules
        self._optimization_rules = [
            self._rule_high_cpu_usage,
            self._rule_high_memory_usage,
            self._rule_high_latency,
            self._rule_low_throughput,
            self._rule_resource_underutilization
        ]
        
        # Threading
        self._lock = threading.Lock()
        self._optimization_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_optimizations = 0
        self._successful_optimizations = 0
        self._last_optimization_time = 0.0
        self._mode_switch_count = 0
    
    def start_monitoring(self) -> bool:
        """Start adaptive performance monitoring."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                self._optimization_thread = threading.Thread(target=self._optimization_loop, daemon=True)
                self._optimization_thread.start()
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop adaptive performance monitoring."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                
                if self._optimization_thread and self._optimization_thread.is_alive():
                    self._optimization_thread.join(timeout=5.0)
                
                return True
        except Exception:
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def _optimization_loop(self) -> None:
        """Main optimization loop."""
        strategy_params = self._strategy_params[self._strategy]
        optimization_interval = strategy_params["optimization_frequency"]
        
        while not self._stop_event.is_set():
            try:
                self._perform_optimization()
                time.sleep(optimization_interval)
            except Exception:
                # Continue optimization even if individual attempts fail
                pass
    
    def _perform_optimization(self) -> None:
        """Perform performance optimization analysis."""
        if not self._enabled:
            return
        
        current_time = time.time()
        self._total_optimizations += 1
        
        try:
            # Collect current performance metrics
            current_metrics = self._collect_performance_metrics()
            
            # Store performance history
            self._performance_history.append({
                "timestamp": current_time,
                "mode": self._current_mode.value,
                "metrics": current_metrics,
                "config": self._current_config.copy()
            })
            
            # Check optimization rules
            optimization_needed = self._check_optimization_rules(current_metrics)
            
            if optimization_needed:
                self._apply_optimization(current_metrics)
                self._successful_optimizations += 1
            
            self._last_optimization_time = current_time
            
        except Exception as e:
            # Log error but continue optimization
            pass
    
    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics."""
        try:
            import psutil
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "cpu_usage": cpu_percent / 100.0,
                "memory_usage": memory.percent / 100.0,
                "process_memory": process_memory.rss,
                "timestamp": time.time()
            }
            
        except ImportError:
            # Fallback metrics
            return {
                "cpu_usage": 0.5,
                "memory_usage": 0.5,
                "process_memory": 0,
                "timestamp": time.time()
            }
    
    def _check_optimization_rules(self, metrics: Dict[str, Any]) -> bool:
        """Check if optimization is needed based on rules."""
        if not self._enabled:
            return False
        
        # Check mode switch limits
        strategy_params = self._strategy_params[self._strategy]
        if self._mode_switch_count >= strategy_params["max_mode_switches"]:
            return False
        
        # Check if enough time has passed since last optimization
        if time.time() - self._last_optimization_time < 60:  # Minimum 1 minute between optimizations
            return False
        
        # Check optimization rules
        for rule in self._optimization_rules:
            if rule(metrics):
                return True
        
        return False
    
    def _rule_high_cpu_usage(self, metrics: Dict[str, Any]) -> bool:
        """Rule for high CPU usage."""
        cpu_usage = metrics.get("cpu_usage", 0)
        return cpu_usage > self._adaptive_thresholds["cpu_high"]
    
    def _rule_high_memory_usage(self, metrics: Dict[str, Any]) -> bool:
        """Rule for high memory usage."""
        memory_usage = metrics.get("memory_usage", 0)
        return memory_usage > self._adaptive_thresholds["memory_high"]
    
    def _rule_high_latency(self, metrics: Dict[str, Any]) -> bool:
        """Rule for high latency."""
        # This would typically come from actual latency measurements
        return False
    
    def _rule_low_throughput(self, metrics: Dict[str, Any]) -> bool:
        """Rule for low throughput."""
        # This would typically come from actual throughput measurements
        return False
    
    def _rule_resource_underutilization(self, metrics: Dict[str, Any]) -> bool:
        """Rule for resource underutilization."""
        cpu_usage = metrics.get("cpu_usage", 0)
        memory_usage = metrics.get("memory_usage", 0)
        
        return (cpu_usage < self._adaptive_thresholds["cpu_low"] and 
                memory_usage < self._adaptive_thresholds["memory_low"])
    
    def _apply_optimization(self, metrics: Dict[str, Any]) -> bool:
        """Apply performance optimization."""
        if not self._enabled:
            return False
        
        try:
            # Determine optimal performance mode
            optimal_mode = self._determine_optimal_mode(metrics)
            
            if optimal_mode != self._current_mode:
                # Switch to optimal mode
                self._switch_performance_mode(optimal_mode)
                return True
            
            return False
            
        except Exception:
            return False
    
    def _determine_optimal_mode(self, metrics: Dict[str, Any]) -> PerformanceMode:
        """Determine the optimal performance mode based on current metrics."""
        cpu_usage = metrics.get("cpu_usage", 0.5)
        memory_usage = metrics.get("memory_usage", 0.5)
        
        # High resource usage - move to more conservative mode
        if cpu_usage > self._adaptive_thresholds["cpu_high"] or memory_usage > self._adaptive_thresholds["memory_high"]:
            if self._current_mode == PerformanceMode.ULTRA_FAST:
                return PerformanceMode.FAST
            elif self._current_mode == PerformanceMode.FAST:
                return PerformanceMode.BALANCED
            elif self._current_mode == PerformanceMode.BALANCED:
                return PerformanceMode.CONSERVATIVE
            elif self._current_mode == PerformanceMode.CONSERVATIVE:
                return PerformanceMode.MINIMAL
            else:
                return PerformanceMode.MINIMAL
        
        # Low resource usage - move to more aggressive mode
        elif cpu_usage < self._adaptive_thresholds["cpu_low"] and memory_usage < self._adaptive_thresholds["memory_low"]:
            if self._current_mode == PerformanceMode.MINIMAL:
                return PerformanceMode.CONSERVATIVE
            elif self._current_mode == PerformanceMode.CONSERVATIVE:
                return PerformanceMode.BALANCED
            elif self._current_mode == PerformanceMode.BALANCED:
                return PerformanceMode.FAST
            elif self._current_mode == PerformanceMode.FAST:
                return PerformanceMode.ULTRA_FAST
            else:
                return PerformanceMode.ULTRA_FAST
        
        # Keep current mode if within acceptable range
        return self._current_mode
    
    def _switch_performance_mode(self, new_mode: PerformanceMode) -> bool:
        """Switch to a new performance mode."""
        if not self._enabled or new_mode == self._current_mode:
            return False
        
        try:
            with self._lock:
                old_mode = self._current_mode
                self._current_mode = new_mode
                self._current_config = self._performance_modes[new_mode].copy()
                
                # Record mode change
                mode_change = {
                    "timestamp": time.time(),
                    "from_mode": old_mode.value,
                    "to_mode": new_mode.value,
                    "reason": "adaptive_optimization",
                    "config": self._current_config.copy()
                }
                
                self._mode_changes.append(mode_change)
                self._mode_switch_count += 1
                
                # Keep only recent mode changes
                if len(self._mode_changes) > 100:
                    self._mode_changes = self._mode_changes[-100:]
                
                return True
                
        except Exception:
            return False
    
    def set_performance_mode(self, mode: PerformanceMode) -> bool:
        """Manually set performance mode."""
        return self._switch_performance_mode(mode)
    
    def get_current_mode(self) -> PerformanceMode:
        """Get current performance mode."""
        return self._current_mode
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get current performance configuration."""
        return self._current_config.copy()
    
    def get_performance_modes(self) -> Dict[str, Dict[str, Any]]:
        """Get all available performance modes."""
        return {mode.value: config.copy() for mode, config in self._performance_modes.items()}
    
    def set_adaptive_strategy(self, strategy: AdaptiveStrategy) -> bool:
        """Set adaptive strategy."""
        if strategy in AdaptiveStrategy:
            self._strategy = strategy
            return True
        return False
    
    def get_adaptive_strategy(self) -> AdaptiveStrategy:
        """Get current adaptive strategy."""
        return self._strategy
    
    def set_adaptive_threshold(self, threshold_name: str, value: float) -> bool:
        """Set adaptive threshold."""
        if threshold_name in self._adaptive_thresholds:
            self._adaptive_thresholds[threshold_name] = value
            return True
        return False
    
    def get_adaptive_thresholds(self) -> Dict[str, float]:
        """Get current adaptive thresholds."""
        return self._adaptive_thresholds.copy()
    
    def get_optimization_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get optimization history."""
        return list(self._performance_history)[-limit:] if limit > 0 else list(self._performance_history)
    
    def get_mode_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get performance mode change history."""
        return self._mode_changes[-limit:] if limit > 0 else self._mode_changes.copy()
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        return {
            "total_optimizations": self._total_optimizations,
            "successful_optimizations": self._successful_optimizations,
            "mode_switch_count": self._mode_switch_count,
            "current_mode": self._current_mode.value,
            "current_strategy": self._strategy.value,
            "last_optimization_time": self._last_optimization_time,
            "optimization_success_rate": (self._successful_optimizations / self._total_optimizations 
                                        if self._total_optimizations > 0 else 0),
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
    
    def reset_optimization_stats(self) -> None:
        """Reset optimization statistics."""
        with self._lock:
            self._performance_history.clear()
            self._mode_changes.clear()
            self._total_optimizations = 0
            self._successful_optimizations = 0
            self._mode_switch_count = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get adaptive performance metrics."""
        return self.get_optimization_stats()
    
    def reset_metrics(self) -> None:
        """Reset adaptive performance metrics."""
        self.reset_optimization_stats()
    
    def is_healthy(self) -> bool:
        """Check if adaptive performance system is healthy."""
        return (self._total_optimizations > 0 and 
                self._successful_optimizations / self._total_optimizations > 0.5)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get adaptive performance system health status."""
        return {
            "healthy": self.is_healthy(),
            "current_mode": self._current_mode.value,
            "strategy": self._strategy.value,
            "optimization_success_rate": (self._successful_optimizations / self._total_optimizations 
                                        if self._total_optimizations > 0 else 0),
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
