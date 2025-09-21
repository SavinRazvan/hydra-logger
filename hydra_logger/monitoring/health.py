"""
Health Monitoring Component for Hydra-Logger

This module provides comprehensive health monitoring with system metrics
collection, health score calculation, and trend analysis. It monitors
CPU, memory, disk, network, and process health to provide overall
system health assessment.

FEATURES:
- System resource monitoring (CPU, memory, disk, network)
- Process-level health tracking
- Health score calculation and trend analysis
- Configurable health thresholds
- Health history and reporting

USAGE:
    from hydra_logger.monitoring import HealthMonitor
    
    # Create health monitor
    monitor = HealthMonitor(
        enabled=True,
        check_interval=30.0
    )
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Get health status
    status = monitor.get_health_status()
    
    # Get health metrics
    metrics = monitor.get_metrics()
    
    # Add custom metric
    monitor.add_custom_metric("custom_metric", 42.0)
"""

import time
import threading
import psutil
from typing import Any, Dict, List, Optional
from ..interfaces.monitor import MonitorInterface


class HealthMonitor(MonitorInterface):
    """Real health monitoring component for system health tracking."""
    
    def __init__(self, enabled: bool = True, check_interval: float = 30.0):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        self._check_interval = check_interval
        self._last_check = 0.0
        
        # Health metrics
        self._health_metrics = {
            "system": {},
            "process": {},
            "memory": {},
            "disk": {},
            "network": {},
            "custom": {}
        }
        
        # Health thresholds
        self._health_thresholds = {
            "cpu_usage": 80.0,  # 80% CPU usage
            "memory_usage": 85.0,  # 85% memory usage
            "disk_usage": 90.0,  # 90% disk usage
            "response_time": 1.0,  # 1 second response time
            "error_rate": 5.0,  # 5% error rate
        }
        
        # Health status
        self._health_status = "unknown"
        self._health_score = 100.0
        self._health_history = []
        self._max_history = 100
        
        # Threading
        self._lock = threading.Lock()
        self._monitor_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_checks = 0
        self._failed_checks = 0
        self._last_failure_time = 0.0
    
    def start_monitoring(self) -> bool:
        """Start health monitoring."""
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
        """Stop health monitoring."""
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
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._perform_health_check()
                time.sleep(self._check_interval)
            except Exception:
                # Continue monitoring even if individual checks fail
                pass
    
    def _perform_health_check(self) -> None:
        """Perform comprehensive health check."""
        if not self._enabled:
            return
        
        current_time = time.time()
        self._total_checks += 1
        
        try:
            # System health checks
            self._check_system_health()
            self._check_process_health()
            self._check_memory_health()
            self._check_disk_health()
            self._check_network_health()
            
            # Calculate overall health score
            self._calculate_health_score()
            
            # Update health status
            self._update_health_status()
            
            # Record health history
            self._record_health_history(current_time)
            
            self._last_check = current_time
            
        except Exception as e:
            self._failed_checks += 1
            self._last_failure_time = current_time
            self._health_status = "error"
            self._health_score = 0.0
    
    def _check_system_health(self) -> None:
        """Check system-level health metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()
            
            self._health_metrics["system"] = {
                "cpu_usage": cpu_percent,
                "load_average": {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                },
                "cpu_count": psutil.cpu_count(),
                "boot_time": psutil.boot_time(),
                "uptime": time.time() - psutil.boot_time()
            }
        except Exception:
            self._health_metrics["system"] = {"error": "Failed to get system metrics"}
    
    def _check_process_health(self) -> None:
        """Check process-level health metrics."""
        try:
            process = psutil.Process()
            
            self._health_metrics["process"] = {
                "pid": process.pid,
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_info": {
                    "rss": process.memory_info().rss,
                    "vms": process.memory_info().vms
                },
                "num_threads": process.num_threads(),
                "status": process.status(),
                "create_time": process.create_time()
            }
        except Exception:
            self._health_metrics["process"] = {"error": "Failed to get process metrics"}
    
    def _check_memory_health(self) -> None:
        """Check memory health metrics."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            self._health_metrics["memory"] = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free,
                "percent": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_free": swap.free,
                "swap_percent": swap.percent
            }
        except Exception:
            self._health_metrics["memory"] = {"error": "Failed to get memory metrics"}
    
    def _check_disk_health(self) -> None:
        """Check disk health metrics."""
        try:
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            self._health_metrics["disk"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
                "read_count": disk_io.read_count if disk_io else 0,
                "write_count": disk_io.write_count if disk_io else 0
            }
        except Exception:
            self._health_metrics["disk"] = {"error": "Failed to get disk metrics"}
    
    def _check_network_health(self) -> None:
        """Check network health metrics."""
        try:
            network_io = psutil.net_io_counters()
            
            self._health_metrics["network"] = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
                "errin": network_io.errin,
                "errout": network_io.errout,
                "dropin": network_io.dropin,
                "dropout": network_io.dropout
            }
        except Exception:
            self._health_metrics["network"] = {"error": "Failed to get network metrics"}
    
    def _calculate_health_score(self) -> None:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        try:
            # CPU usage penalty
            if "cpu_usage" in self._health_metrics["system"]:
                cpu_usage = self._health_metrics["system"]["cpu_usage"]
                if cpu_usage > self._health_thresholds["cpu_usage"]:
                    penalty = (cpu_usage - self._health_thresholds["cpu_usage"]) * 0.5
                    score -= penalty
            
            # Memory usage penalty
            if "percent" in self._health_metrics["memory"]:
                memory_usage = self._health_metrics["memory"]["percent"]
                if memory_usage > self._health_thresholds["memory_usage"]:
                    penalty = (memory_usage - self._health_thresholds["memory_usage"]) * 0.5
                    score -= penalty
            
            # Disk usage penalty
            if "percent" in self._health_metrics["disk"]:
                disk_usage = self._health_metrics["disk"]["percent"]
                if disk_usage > self._health_thresholds["disk_usage"]:
                    penalty = (disk_usage - self._health_thresholds["disk_usage"]) * 0.5
                    score -= penalty
            
            # Ensure score is within bounds
            score = max(0.0, min(100.0, score))
            
        except Exception:
            score = 0.0
        
        self._health_score = score
    
    def _update_health_status(self) -> None:
        """Update overall health status."""
        if self._health_score >= 90:
            self._health_status = "excellent"
        elif self._health_score >= 75:
            self._health_status = "good"
        elif self._health_score >= 50:
            self._health_status = "fair"
        elif self._health_score >= 25:
            self._health_status = "poor"
        else:
            self._health_status = "critical"
    
    def _record_health_history(self, timestamp: float) -> None:
        """Record health metrics in history."""
        history_entry = {
            "timestamp": timestamp,
            "health_score": self._health_score,
            "health_status": self._health_status,
            "cpu_usage": self._health_metrics["system"].get("cpu_usage", 0),
            "memory_usage": self._health_metrics["memory"].get("percent", 0),
            "disk_usage": self._health_metrics["disk"].get("percent", 0)
        }
        
        self._health_history.append(history_entry)
        
        # Keep only recent history
        if len(self._health_history) > self._max_history:
            self._health_history = self._health_history[-self._max_history:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current health metrics."""
        return self._health_metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset health metrics."""
        with self._lock:
            self._health_metrics = {
                "system": {},
                "process": {},
                "memory": {},
                "disk": {},
                "network": {},
                "custom": {}
            }
            self._health_history = []
            self._total_checks = 0
            self._failed_checks = 0
    
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self._health_score >= 50.0
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            "status": self._health_status,
            "score": self._health_score,
            "is_healthy": self.is_healthy(),
            "last_check": self._last_check,
            "total_checks": self._total_checks,
            "failed_checks": self._failed_checks,
            "last_failure": self._last_failure_time,
            "monitoring": self._monitoring,
            "check_interval": self._check_interval
        }
    
    def add_custom_metric(self, name: str, value: Any) -> None:
        """Add custom health metric."""
        self._health_metrics["custom"][name] = value
    
    def set_threshold(self, metric: str, threshold: float) -> bool:
        """Set health threshold for a metric."""
        if metric in self._health_thresholds:
            self._health_thresholds[metric] = threshold
            return True
        return False
    
    def get_health_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get health history."""
        return self._health_history[-limit:] if limit > 0 else self._health_history.copy()
    
    def get_health_trend(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trend over specified hours."""
        cutoff_time = time.time() - (hours * 3600)
        recent_history = [
            entry for entry in self._health_history
            if entry["timestamp"] > cutoff_time
        ]
        
        if not recent_history:
            return {"trend": "insufficient_data"}
        
        scores = [entry["health_score"] for entry in recent_history]
        avg_score = sum(scores) / len(scores)
        
        if len(scores) > 1:
            trend = "improving" if scores[-1] > scores[0] else "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "average_score": avg_score,
            "min_score": min(scores),
            "max_score": max(scores),
            "data_points": len(scores),
            "period_hours": hours
        }
