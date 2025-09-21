"""
Memory Monitoring Component for Hydra-Logger

This module provides comprehensive memory monitoring with leak detection,
fragmentation analysis, and memory usage tracking. It monitors both
process and system memory to identify potential issues and optimize
memory usage.

FEATURES:
- Process and system memory monitoring
- Memory leak detection and analysis
- Memory fragmentation tracking
- Garbage collection statistics
- Memory trend analysis and alerts

USAGE:
    from hydra_logger.monitoring import MemoryMonitor
    
    # Create memory monitor
    monitor = MemoryMonitor(
        enabled=True,
        check_interval=30.0
    )
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Get memory snapshot
    snapshot = monitor.get_memory_snapshot()
    
    # Get memory trends
    trends = monitor.get_memory_trends()
    
    # Force garbage collection
    gc_results = monitor.force_garbage_collection()
"""

import time
import threading
import gc
import sys
from typing import Any, Dict, List, Optional, Tuple
from collections import deque
from ..interfaces.monitor import MonitorInterface


class MemoryMonitor(MonitorInterface):
    """Real memory monitoring component for memory usage tracking and leak detection."""
    
    def __init__(self, enabled: bool = True, check_interval: float = 30.0):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        self._check_interval = check_interval
        
        # Memory tracking
        self._memory_snapshots = deque(maxlen=1000)
        self._memory_trends = {}
        self._memory_alerts = []
        self._max_alerts = 100
        
        # Memory thresholds
        self._memory_thresholds = {
            "high_usage": 0.8,      # 80% memory usage
            "critical_usage": 0.9,   # 90% memory usage
            "leak_threshold": 0.1,   # 10% growth over time
            "fragmentation_threshold": 0.3  # 30% fragmentation
        }
        
        # Memory analysis
        self._baseline_memory = None
        self._peak_memory = 0
        self._total_allocations = 0
        self._total_deallocations = 0
        
        # Threading
        self._lock = threading.Lock()
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_checks = 0
        self._high_usage_count = 0
        self._critical_usage_count = 0
        self._leak_detections = 0
        self._last_check_time = 0.0
    
    def start_monitoring(self) -> bool:
        """Start memory monitoring."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self._monitor_thread.start()
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop memory monitoring."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                
                if self._monitor_thread and self._monitor_thread.is_alive():
                    self._monitor_thread.join(timeout=5.0)
                
                return True
        except Exception:
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def _monitor_loop(self) -> None:
        """Main memory monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._perform_memory_check()
                time.sleep(self._check_interval)
            except Exception:
                # Continue monitoring even if individual checks fail
                pass
    
    def _perform_memory_check(self) -> None:
        """Perform comprehensive memory check."""
        if not self._enabled:
            return
        
        current_time = time.time()
        self._total_checks += 1
        
        try:
            # Get current memory usage
            memory_info = self._get_memory_info()
            
            # Create memory snapshot
            snapshot = {
                "timestamp": current_time,
                "memory_info": memory_info,
                "gc_stats": self._get_gc_stats(),
                "object_counts": self._get_object_counts()
            }
            
            # Store snapshot
            self._memory_snapshots.append(snapshot)
            
            # Update baseline if not set
            if self._baseline_memory is None:
                self._baseline_memory = memory_info["rss"]
            
            # Update peak memory
            if memory_info["rss"] > self._peak_memory:
                self._peak_memory = memory_info["rss"]
            
            # Check for memory issues
            self._check_memory_usage(memory_info, current_time)
            self._check_memory_leaks(snapshot, current_time)
            self._check_memory_fragmentation(memory_info, current_time)
            
            # Update trends
            self._update_memory_trends(snapshot)
            
            self._last_check_time = current_time
            
        except Exception as e:
            # Log error but continue monitoring
            self._add_memory_alert("error", f"Memory check failed: {str(e)}", current_time)
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get current memory information."""
        try:
            import psutil
            
            process = psutil.Process()
            memory = process.memory_info()
            virtual_memory = psutil.virtual_memory()
            
            return {
                "rss": memory.rss,                    # Resident Set Size
                "vms": memory.vms,                    # Virtual Memory Size
                "percent": memory.percent,            # Memory usage percentage
                "available": virtual_memory.available,
                "total": virtual_memory.total,
                "used": virtual_memory.used,
                "free": virtual_memory.free,
                "swap_total": virtual_memory.swap.total,
                "swap_used": virtual_memory.swap.used,
                "swap_free": virtual_memory.swap.free
            }
        except ImportError:
            # Fallback to basic memory info
            return {
                "rss": 0,
                "vms": 0,
                "percent": 0,
                "available": 0,
                "total": 0,
                "used": 0,
                "free": 0,
                "swap_total": 0,
                "swap_used": 0,
                "swap_free": 0
            }
    
    def _get_gc_stats(self) -> Dict[str, Any]:
        """Get garbage collector statistics."""
        try:
            gc.collect()  # Force collection to get accurate stats
            
            return {
                "collections": gc.get_stats(),
                "counts": gc.get_count(),
                "objects": len(gc.get_objects()),
                "garbage": len(gc.garbage)
            }
        except Exception:
            return {
                "collections": [],
                "counts": (0, 0, 0),
                "objects": 0,
                "garbage": 0
            }
    
    def _get_object_counts(self) -> Dict[str, int]:
        """Get object counts by type."""
        try:
            object_counts = {}
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
            
            # Keep only top object types
            sorted_counts = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)
            return dict(sorted_counts[:20])  # Top 20 object types
            
        except Exception:
            return {}
    
    def _check_memory_usage(self, memory_info: Dict[str, Any], timestamp: float) -> None:
        """Check for high memory usage."""
        if "percent" in memory_info and memory_info["percent"] > 0:
            usage_percent = memory_info["percent"] / 100.0
            
            if usage_percent >= self._memory_thresholds["critical_usage"]:
                self._add_memory_alert(
                    "critical",
                    f"Critical memory usage: {memory_info['percent']:.1f}%",
                    timestamp
                )
                self._critical_usage_count += 1
                
            elif usage_percent >= self._memory_thresholds["high_usage"]:
                self._add_memory_alert(
                    "warning",
                    f"High memory usage: {memory_info['percent']:.1f}%",
                    timestamp
                )
                self._high_usage_count += 1
    
    def _check_memory_leaks(self, snapshot: Dict[str, Any], timestamp: float) -> None:
        """Check for potential memory leaks."""
        if len(self._memory_snapshots) < 10:  # Need enough data points
            return
        
        try:
            # Calculate memory growth over time
            recent_snapshots = list(self._memory_snapshots)[-10:]
            memory_values = [s["memory_info"]["rss"] for s in recent_snapshots]
            
            if len(memory_values) >= 2:
                growth_rate = (memory_values[-1] - memory_values[0]) / memory_values[0]
                
                if growth_rate > self._memory_thresholds["leak_threshold"]:
                    self._add_memory_alert(
                        "warning",
                        f"Potential memory leak detected: {growth_rate:.1%} growth over time",
                        timestamp
                    )
                    self._leak_detections += 1
                    
        except Exception:
            # Skip leak detection if calculation fails
            pass
    
    def _check_memory_fragmentation(self, memory_info: Dict[str, Any], timestamp: float) -> None:
        """Check for memory fragmentation."""
        try:
            if memory_info["total"] > 0 and memory_info["free"] > 0:
                fragmentation = memory_info["free"] / memory_info["total"]
                
                if fragmentation < self._memory_thresholds["fragmentation_threshold"]:
                    self._add_memory_alert(
                        "info",
                        f"Low memory fragmentation: {fragmentation:.1%}",
                        timestamp
                    )
                    
        except Exception:
            # Skip fragmentation check if calculation fails
            pass
    
    def _update_memory_trends(self, snapshot: Dict[str, Any]) -> None:
        """Update memory usage trends."""
        if len(self._memory_snapshots) < 2:
            return
        
        try:
            # Calculate trends over different time periods
            current_time = snapshot["timestamp"]
            
            # 1 hour trend
            hour_ago = current_time - 3600
            hour_snapshots = [s for s in self._memory_snapshots if s["timestamp"] > hour_ago]
            
            if len(hour_snapshots) > 1:
                hour_growth = self._calculate_memory_growth(hour_snapshots)
                self._memory_trends["1hour"] = hour_growth
            
            # 6 hour trend
            six_hours_ago = current_time - (6 * 3600)
            six_hour_snapshots = [s for s in self._memory_snapshots if s["timestamp"] > six_hours_ago]
            
            if len(six_hour_snapshots) > 1:
                six_hour_growth = self._calculate_memory_growth(six_hour_snapshots)
                self._memory_trends["6hours"] = six_hour_growth
            
            # 24 hour trend
            day_ago = current_time - (24 * 3600)
            day_snapshots = [s for s in self._memory_snapshots if s["timestamp"] > day_ago]
            
            if len(day_snapshots) > 1:
                day_growth = self._calculate_memory_growth(day_snapshots)
                self._memory_trends["24hours"] = day_growth
                
        except Exception:
            # Skip trend calculation if it fails
            pass
    
    def _calculate_memory_growth(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate memory growth between snapshots."""
        if len(snapshots) < 2:
            return {"growth_rate": 0, "growth_bytes": 0}
        
        first_rss = snapshots[0]["memory_info"]["rss"]
        last_rss = snapshots[-1]["memory_info"]["rss"]
        
        if first_rss > 0:
            growth_rate = (last_rss - first_rss) / first_rss
            growth_bytes = last_rss - first_rss
        else:
            growth_rate = 0
            growth_bytes = 0
        
        return {
            "growth_rate": growth_rate,
            "growth_bytes": growth_bytes,
            "start_rss": first_rss,
            "end_rss": last_rss,
            "data_points": len(snapshots)
        }
    
    def _add_memory_alert(self, level: str, message: str, timestamp: float) -> None:
        """Add a memory alert."""
        alert = {
            "level": level,
            "message": message,
            "timestamp": timestamp,
            "memory_info": self._get_memory_info() if self._enabled else {}
        }
        
        self._memory_alerts.append(alert)
        
        # Keep only recent alerts
        if len(self._memory_alerts) > self._max_alerts:
            self._memory_alerts = self._memory_alerts[-self._max_alerts:]
    
    def get_memory_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent memory snapshot."""
        if not self._enabled or not self._memory_snapshots:
            return None
        
        return self._memory_snapshots[-1].copy()
    
    def get_memory_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get memory history for specified number of hours."""
        if not self._enabled:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        
        with self._lock:
            recent_snapshots = [
                snapshot for snapshot in self._memory_snapshots
                if snapshot["timestamp"] > cutoff_time
            ]
        
        return recent_snapshots
    
    def get_memory_trends(self) -> Dict[str, Any]:
        """Get memory usage trends."""
        return self._memory_trends.copy()
    
    def get_memory_alerts(self, level: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get memory alerts with optional filtering."""
        if not self._enabled:
            return []
        
        alerts = self._memory_alerts.copy()
        
        if level:
            alerts = [a for a in alerts if a["level"] == level]
        
        return alerts[-limit:] if limit > 0 else alerts
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics."""
        if not self._enabled:
            return {}
        
        current_memory = self._get_memory_info()
        
        return {
            "current_usage": current_memory,
            "baseline_memory": self._baseline_memory,
            "peak_memory": self._peak_memory,
            "memory_trends": self._memory_trends,
            "total_checks": self._total_checks,
            "high_usage_count": self._high_usage_count,
            "critical_usage_count": self._critical_usage_count,
            "leak_detections": self._leak_detections,
            "last_check_time": self._last_check_time,
            "snapshots_count": len(self._memory_snapshots),
            "alerts_count": len(self._memory_alerts),
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
    
    def set_memory_threshold(self, threshold_name: str, value: float) -> bool:
        """Set memory threshold."""
        if threshold_name in self._memory_thresholds:
            self._memory_thresholds[threshold_name] = value
            return True
        return False
    
    def get_memory_thresholds(self) -> Dict[str, float]:
        """Get current memory thresholds."""
        return self._memory_thresholds.copy()
    
    def force_garbage_collection(self) -> Dict[str, Any]:
        """Force garbage collection and return results."""
        if not self._enabled:
            return {}
        
        try:
            # Get pre-collection stats
            pre_stats = self._get_gc_stats()
            pre_memory = self._get_memory_info()
            
            # Force collection
            collected = gc.collect()
            
            # Get post-collection stats
            post_stats = self._get_gc_stats()
            post_memory = self._get_memory_info()
            
            return {
                "objects_collected": collected,
                "memory_freed": pre_memory["rss"] - post_memory["rss"],
                "pre_collection": pre_stats,
                "post_collection": post_stats,
                "pre_memory": pre_memory,
                "post_memory": post_memory
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def reset_memory_stats(self) -> None:
        """Reset memory statistics."""
        with self._lock:
            self._memory_snapshots.clear()
            self._memory_trends.clear()
            self._memory_alerts.clear()
            self._baseline_memory = None
            self._peak_memory = 0
            self._total_checks = 0
            self._high_usage_count = 0
            self._critical_usage_count = 0
            self._leak_detections = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current memory metrics."""
        return self.get_memory_stats()
    
    def reset_metrics(self) -> None:
        """Reset memory metrics."""
        self.reset_memory_stats()
    
    def is_healthy(self) -> bool:
        """Check if memory system is healthy."""
        if not self._enabled:
            return True
        
        current_memory = self._get_memory_info()
        if "percent" in current_memory and current_memory["percent"] > 0:
            usage_percent = current_memory["percent"] / 100.0
            return usage_percent < self._memory_thresholds["critical_usage"]
        
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get memory system health status."""
        return {
            "healthy": self.is_healthy(),
            "current_usage": self._get_memory_info().get("percent", 0),
            "peak_memory": self._peak_memory,
            "leak_detections": self._leak_detections,
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
