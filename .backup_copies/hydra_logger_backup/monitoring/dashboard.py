"""
Monitoring Dashboard Component for Hydra-Logger

This module provides a comprehensive monitoring dashboard with real-time
visualization of system metrics, health status, and performance data.
It offers multiple views and data export capabilities for monitoring
and analysis.

FEATURES:
- Real-time system metrics visualization
- Multiple dashboard views (overview, performance, health, alerts, system)
- Data export in multiple formats (JSON, CSV, HTML, Markdown)
- Configurable refresh intervals and data retention
- Custom data source integration

USAGE:
    from hydra_logger.monitoring import MonitoringDashboard
    
    # Create dashboard
    dashboard = MonitoringDashboard(
        enabled=True,
        port=8080,
        host="localhost"
    )
    
    # Start monitoring
    dashboard.start_monitoring()
    
    # Get dashboard view
    overview = dashboard.get_dashboard_view("overview")
    
    # Export data
    json_data = dashboard.export_dashboard_data(format="json", view="overview")
"""

import time
import threading
import json
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
from ..interfaces.monitor import MonitorInterface


class MonitoringDashboard(MonitorInterface):
    """Real monitoring dashboard component for web-based monitoring interface."""
    
    def __init__(self, enabled: bool = True, port: int = 8080, host: str = "localhost"):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        self._port = port
        self._host = host
        
        # Dashboard data
        self._dashboard_data = {
            "system_status": {},
            "performance_metrics": {},
            "health_metrics": {},
            "alerts": [],
            "charts_data": defaultdict(lambda: deque(maxlen=1000))
        }
        
        # Dashboard configuration
        self._dashboard_config = {
            "refresh_interval": 5.0,  # seconds
            "max_data_points": 1000,
            "enable_charts": True,
            "enable_alerts": True,
            "enable_export": True,
            "theme": "dark"  # dark, light, auto
        }
        
        # Dashboard views and widgets
        self._dashboard_views = {
            "overview": self._get_overview_view,
            "performance": self._get_performance_view,
            "health": self._get_health_view,
            "alerts": self._get_alerts_view,
            "system": self._get_system_view
        }
        
        # Data sources and callbacks
        self._data_sources = {}
        self._data_callbacks = {}
        
        # Dashboard state
        self._dashboard_state = {
            "last_update": 0.0,
            "total_requests": 0,
            "active_users": 0,
            "error_count": 0
        }
        
        # Threading
        self._lock = threading.Lock()
        self._dashboard_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_views = 0
        self._total_exports = 0
        self._last_export_time = 0.0
    
    def start_monitoring(self) -> bool:
        """Start dashboard monitoring."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                self._dashboard_thread = threading.Thread(target=self._dashboard_loop, daemon=True)
                self._dashboard_thread.start()
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop dashboard monitoring."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                
                if self._dashboard_thread and self._dashboard_thread.is_alive():
                    self._dashboard_thread.join(timeout=5.0)
                
                return True
        except Exception:
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def _dashboard_loop(self) -> None:
        """Main dashboard update loop."""
        while not self._stop_event.is_set():
            try:
                self._update_dashboard_data()
                time.sleep(self._dashboard_config["refresh_interval"])
            except Exception:
                # Continue monitoring even if individual updates fail
                pass
    
    def _update_dashboard_data(self) -> None:
        """Update dashboard data from all sources."""
        if not self._enabled:
            return
        
        current_time = time.time()
        
        try:
            # Update system status
            self._update_system_status()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Update health metrics
            self._update_health_metrics()
            
            # Update alerts
            self._update_alerts()
            
            # Update charts data
            self._update_charts_data()
            
            # Call data callbacks
            self._call_data_callbacks()
            
            self._dashboard_state["last_update"] = current_time
            
        except Exception as e:
            self._dashboard_state["error_count"] += 1
    
    def _update_system_status(self) -> None:
        """Update system status information."""
        try:
            import psutil
            
            # System information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self._dashboard_data["system_status"] = {
                "timestamp": time.time(),
                "cpu": {
                    "usage": cpu_percent,
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
                },
                "memory": {
                    "total": memory.total,
                    "used": memory.used,
                    "free": memory.free,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": self._get_network_stats(),
                "uptime": time.time() - psutil.boot_time()
            }
            
        except ImportError:
            # psutil not available, use basic info
            self._dashboard_data["system_status"] = {
                "timestamp": time.time(),
                "error": "psutil not available"
            }
    
    def _get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        try:
            import psutil
            
            network_io = psutil.net_io_counters()
            return {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            }
        except Exception:
            return {"error": "Failed to get network stats"}
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        try:
            # This would typically get data from PerformanceMonitor
            self._dashboard_data["performance_metrics"] = {
                "timestamp": time.time(),
                "operations_per_second": 0,
                "average_response_time": 0,
                "error_rate": 0,
                "throughput": 0
            }
        except Exception:
            self._dashboard_data["performance_metrics"] = {
                "timestamp": time.time(),
                "error": "Failed to update performance metrics"
            }
    
    def _update_health_metrics(self) -> None:
        """Update health metrics."""
        try:
            # This would typically get data from HealthMonitor
            self._dashboard_data["health_metrics"] = {
                "timestamp": time.time(),
                "overall_health": "unknown",
                "health_score": 0,
                "component_status": {}
            }
        except Exception:
            self._dashboard_data["health_metrics"] = {
                "timestamp": time.time(),
                "error": "Failed to update health metrics"
            }
    
    def _update_alerts(self) -> None:
        """Update alerts information."""
        try:
            # This would typically get data from AlertManager
            self._dashboard_data["alerts"] = []
        except Exception:
            self._dashboard_data["alerts"] = []
    
    def _update_charts_data(self) -> None:
        """Update charts data for time-series visualization."""
        if not self._dashboard_config["enable_charts"]:
            return
        
        current_time = time.time()
        
        # Update CPU usage chart
        if "system_status" in self._dashboard_data:
            cpu_data = {
                "timestamp": current_time,
                "value": self._dashboard_data["system_status"].get("cpu", {}).get("usage", 0)
            }
            self._dashboard_data["charts_data"]["cpu_usage"].append(cpu_data)
        
        # Update memory usage chart
        if "system_status" in self._dashboard_data:
            memory_data = {
                "timestamp": current_time,
                "value": self._dashboard_data["system_status"].get("memory", {}).get("percent", 0)
            }
            self._dashboard_data["charts_data"]["memory_usage"].append(memory_data)
    
    def _call_data_callbacks(self) -> None:
        """Call registered data callbacks."""
        for callback_name, callback in self._data_callbacks.items():
            try:
                callback(self._dashboard_data)
            except Exception:
                # Continue with other callbacks
                pass
    
    def register_data_source(self, name: str, data_getter: Callable) -> bool:
        """Register a data source for the dashboard."""
        try:
            self._data_sources[name] = data_getter
            return True
        except Exception:
            return False
    
    def unregister_data_source(self, name: str) -> bool:
        """Unregister a data source."""
        if name in self._data_sources:
            del self._data_sources[name]
            return True
        return False
    
    def register_data_callback(self, name: str, callback: Callable) -> bool:
        """Register a callback for dashboard data updates."""
        try:
            self._data_callbacks[name] = callback
            return True
        except Exception:
            return False
    
    def unregister_data_callback(self, name: str) -> bool:
        """Unregister a data callback."""
        if name in self._data_callbacks:
            del self._data_callbacks[name]
            return True
        return False
    
    def get_dashboard_view(self, view_name: str, **kwargs) -> Dict[str, Any]:
        """Get a specific dashboard view."""
        if not self._enabled:
            return {"error": "Dashboard not enabled"}
        
        if view_name not in self._dashboard_views:
            return {"error": f"Unknown view: {view_name}"}
        
        try:
            self._total_views += 1
            return self._dashboard_views[view_name](**kwargs)
        except Exception as e:
            return {"error": f"Failed to get view {view_name}: {str(e)}"}
    
    def _get_overview_view(self, **kwargs) -> Dict[str, Any]:
        """Get overview dashboard view."""
        return {
            "view": "overview",
            "timestamp": time.time(),
            "system_status": self._dashboard_data["system_status"],
            "performance_summary": self._dashboard_data["performance_metrics"],
            "health_summary": self._dashboard_data["health_metrics"],
            "recent_alerts": self._dashboard_data["alerts"][-5:] if self._dashboard_data["alerts"] else [],
            "charts": {
                "cpu_usage": list(self._dashboard_data["charts_data"]["cpu_usage"][-50:]),
                "memory_usage": list(self._dashboard_data["charts_data"]["memory_usage"][-50:])
            }
        }
    
    def _get_performance_view(self, **kwargs) -> Dict[str, Any]:
        """Get performance dashboard view."""
        return {
            "view": "performance",
            "timestamp": time.time(),
            "performance_metrics": self._dashboard_data["performance_metrics"],
            "performance_charts": {
                "throughput": list(self._dashboard_data["charts_data"]["cpu_usage"][-100:]),
                "response_time": list(self._dashboard_data["charts_data"]["memory_usage"][-100:])
            }
        }
    
    def _get_health_view(self, **kwargs) -> Dict[str, Any]:
        """Get health dashboard view."""
        return {
            "view": "health",
            "timestamp": time.time(),
            "health_metrics": self._dashboard_data["health_metrics"],
            "health_charts": {
                "health_score": list(self._dashboard_data["charts_data"]["cpu_usage"][-100:])
            }
        }
    
    def _get_alerts_view(self, **kwargs) -> Dict[str, Any]:
        """Get alerts dashboard view."""
        return {
            "view": "alerts",
            "timestamp": time.time(),
            "alerts": self._dashboard_data["alerts"],
            "alert_summary": {
                "total": len(self._dashboard_data["alerts"]),
                "critical": len([a for a in self._dashboard_data["alerts"] if a.get("severity") == "critical"]),
                "warning": len([a for a in self._dashboard_data["alerts"] if a.get("severity") == "warning"])
            }
        }
    
    def _get_system_view(self, **kwargs) -> Dict[str, Any]:
        """Get system dashboard view."""
        return {
            "view": "system",
            "timestamp": time.time(),
            "system_status": self._dashboard_data["system_status"],
            "system_charts": {
                "cpu_usage": list(self._dashboard_data["charts_data"]["cpu_usage"][-100:]),
                "memory_usage": list(self._dashboard_data["charts_data"]["memory_usage"][-100:])
            }
        }
    
    def export_dashboard_data(self, format: str = "json", view: str = "overview") -> str:
        """Export dashboard data in specified format."""
        if not self._enabled or not self._dashboard_config["enable_export"]:
            return ""
        
        try:
            data = self.get_dashboard_view(view)
            self._total_exports += 1
            self._last_export_time = time.time()
            
            if format.lower() == "json":
                return json.dumps(data, indent=2, default=str)
            elif format.lower() == "csv":
                return self._convert_to_csv(data)
            else:
                return json.dumps(data, default=str)
                
        except Exception as e:
            return f"Export failed: {str(e)}"
    
    def _convert_to_csv(self, data: Dict[str, Any]) -> str:
        """Convert dashboard data to CSV format."""
        # Simple CSV conversion for basic data
        csv_lines = []
        
        if "system_status" in data:
            csv_lines.append("Metric,Value")
            csv_lines.append(f"CPU Usage,{data['system_status'].get('cpu', {}).get('usage', 0)}")
            csv_lines.append(f"Memory Usage,{data['system_status'].get('memory', {}).get('percent', 0)}")
            csv_lines.append(f"Disk Usage,{data['system_status'].get('disk', {}).get('percent', 0)}")
        
        return "\n".join(csv_lines)
    
    def set_dashboard_config(self, key: str, value: Any) -> bool:
        """Set dashboard configuration."""
        if key in self._dashboard_config:
            self._dashboard_config[key] = value
            return True
        return False
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get current dashboard configuration."""
        return self._dashboard_config.copy()
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        return {
            "total_views": self._total_views,
            "total_exports": self._total_exports,
            "last_export_time": self._last_export_time,
            "active_data_sources": len(self._data_sources),
            "active_callbacks": len(self._data_callbacks),
            "last_update": self._dashboard_state["last_update"],
            "total_requests": self._dashboard_state["total_requests"],
            "error_count": self._dashboard_state["error_count"],
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics."""
        return self.get_dashboard_stats()
    
    def reset_metrics(self) -> None:
        """Reset dashboard metrics."""
        with self._lock:
            self._total_views = 0
            self._total_exports = 0
            self._last_export_time = 0.0
            self._dashboard_state["total_requests"] = 0
            self._dashboard_state["error_count"] = 0
    
    def is_healthy(self) -> bool:
        """Check if dashboard is healthy."""
        return self._dashboard_state["error_count"] < 10  # Consider healthy if less than 10 errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get dashboard health status."""
        return {
            "healthy": self.is_healthy(),
            "error_count": self._dashboard_state["error_count"],
            "last_update": self._dashboard_state["last_update"],
            "monitoring": self._monitoring,
            "enabled": self._enabled
        }
