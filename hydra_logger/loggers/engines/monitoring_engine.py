"""
Monitoring Engine for Hydra-Logger Loggers

This module provides comprehensive monitoring features including performance monitoring,
health monitoring, memory monitoring, and metrics collection. It serves as the central
monitoring system for all logger implementations.

ARCHITECTURE:
- MonitoringEngine: Central monitoring and metrics engine
- PerformanceMonitor: Performance monitoring and metrics collection
- HealthMonitor: Health status monitoring and reporting
- MemoryMonitor: Memory usage tracking and analysis
- MetricsCollector: Metrics collection and management

CORE FEATURES:
- Performance monitoring and metrics collection
- Health status monitoring and reporting
- Memory usage tracking and analysis
- System metrics collection and management
- Alert threshold management and notification
- Metrics export and reporting

USAGE EXAMPLES:

Basic Monitoring:
    from hydra_logger.loggers.engines import MonitoringEngine
    
    # Create monitoring engine
    monitoring = MonitoringEngine()
    
    # Start monitoring
    monitoring.start_monitoring()
    
    # Get health status
    health = monitoring.get_health_status()
    print(f"Health status: {health}")
    
    # Stop monitoring
    monitoring.stop_monitoring()

Performance Monitoring:
    from hydra_logger.loggers.engines import MonitoringEngine
    
    # Create monitoring engine
    monitoring = MonitoringEngine()
    
    # Start monitoring
    monitoring.start_monitoring()
    
    # Record custom metrics
    monitoring.record_metric("log_duration_ms", 15.5)
    monitoring.record_metric("log_throughput", 1000.0)
    monitoring.record_metric("error_count", 5)
    
    # Get performance metrics
    perf_metrics = monitoring.get_performance_metrics()
    print(f"Performance metrics: {perf_metrics}")
    
    # Get all metrics
    all_metrics = monitoring.get_all_metrics()
    print(f"All metrics: {all_metrics}")

Health Monitoring:
    from hydra_logger.loggers.engines import MonitoringEngine
    
    # Create monitoring engine
    monitoring = MonitoringEngine()
    
    # Start monitoring
    monitoring.start_monitoring()
    
    # Get health status
    health = monitoring.get_health_status()
    print(f"Overall health: {health['status']}")
    print(f"Uptime: {health['uptime']}")
    print(f"Health details: {health['health']}")
    print(f"Memory status: {health['memory']}")
    print(f"Performance status: {health['performance']}")

Memory Monitoring:
    from hydra_logger.loggers.engines import MonitoringEngine
    
    # Create monitoring engine
    monitoring = MonitoringEngine()
    
    # Start monitoring
    monitoring.start_monitoring()
    
    # Get memory metrics
    memory_metrics = monitoring.get_memory_metrics()
    print(f"Memory metrics: {memory_metrics}")
    
    # Get all metrics including memory
    all_metrics = monitoring.get_all_metrics()
    print(f"Memory details: {all_metrics['memory']}")

Alert Management:
    from hydra_logger.loggers.engines import MonitoringEngine
    
    # Create monitoring engine
    monitoring = MonitoringEngine()
    
    # Set alert thresholds
    monitoring.set_alert_threshold("log_duration_ms", 100.0, ">")
    monitoring.set_alert_threshold("error_count", 10, ">")
    monitoring.set_alert_threshold("memory_usage", 80.0, ">")
    
    # Get current alerts
    alerts = monitoring.get_alerts()
    print(f"Current alerts: {alerts}")
    
    # Clear alerts
    monitoring.clear_alerts()

Metrics Export:
    from hydra_logger.loggers.engines import MonitoringEngine
    
    # Create monitoring engine
    monitoring = MonitoringEngine()
    
    # Start monitoring
    monitoring.start_monitoring()
    
    # Export metrics in different formats
    json_metrics = monitoring.export_metrics("json")
    print(f"JSON metrics: {json_metrics}")
    
    # Get monitoring system metrics
    system_metrics = monitoring.get_monitoring_metrics()
    print(f"System metrics: {system_metrics}")

Engine Management:
    from hydra_logger.loggers.engines import MonitoringEngine
    
    # Create monitoring engine
    monitoring = MonitoringEngine()
    
    # Enable/disable monitoring
    monitoring.set_monitoring_enabled(True)
    
    # Start monitoring
    monitoring.start_monitoring()
    
    # Get individual monitors
    perf_monitor = monitoring.get_performance_monitor()
    health_monitor = monitoring.get_health_monitor()
    memory_monitor = monitoring.get_memory_monitor()
    metrics_collector = monitoring.get_metrics_collector()
    
    # Reset metrics
    monitoring.reset_metrics()
    
    # Stop monitoring
    monitoring.stop_monitoring()

PERFORMANCE MONITORING:
- Real-time performance metrics collection
- Throughput and latency measurements
- Resource usage tracking
- Performance trend analysis
- Custom metric recording

HEALTH MONITORING:
- System health status reporting
- Component health checking
- Uptime and availability tracking
- Health trend analysis
- Automated health checks

MEMORY MONITORING:
- Memory usage tracking and analysis
- Memory leak detection
- Memory trend analysis
- Memory optimization recommendations
- Memory alert management

METRICS COLLECTION:
- Custom metrics recording
- Metrics aggregation and analysis
- Metrics export in multiple formats
- Metrics storage and retrieval
- Metrics visualization support

ALERT MANAGEMENT:
- Configurable alert thresholds
- Alert condition evaluation
- Alert notification system
- Alert history and tracking
- Alert suppression and management

ERROR HANDLING:
- Graceful error handling with fallback mechanisms
- Error isolation between monitoring components
- Comprehensive error reporting
- Automatic resource cleanup
- Silent error handling for maximum performance

BENEFITS:
- Comprehensive monitoring and metrics collection
- Real-time performance and health monitoring
- Easy integration with logger implementations
- Configurable alerting and notification
- Production-ready monitoring solution
"""

import time
from typing import Any, Dict, Optional, Union, List
from ...monitoring.performance import PerformanceMonitor
from ...monitoring.health import HealthMonitor
from ...monitoring.memory import MemoryMonitor
from ...monitoring.metrics import MetricsCollector


class MonitoringEngine:
    """Monitoring and metrics engine for loggers."""
    
    def __init__(self):
        """Initialize the monitoring engine."""
        self._performance_monitor = PerformanceMonitor()
        self._health_monitor = HealthMonitor()
        self._memory_monitor = MemoryMonitor()
        self._metrics_collector = MetricsCollector()
        self._monitoring_enabled = True
        
        # Monitoring statistics
        self._start_time = time.time()
        self._health_checks = 0
        self._performance_measurements = 0
        self._memory_checks = 0
    
    def set_monitoring_enabled(self, enabled: bool) -> None:
        """Enable or disable monitoring."""
        self._monitoring_enabled = enabled
    
    def start_monitoring(self) -> None:
        """Start all monitoring systems."""
        if not self._monitoring_enabled:
            return
        
        try:
            self._performance_monitor.start()
            self._health_monitor.start()
            self._memory_monitor.start()
            self._metrics_collector.start()
        except Exception:
            pass  # Silently fail if monitoring components are not available
    
    def stop_monitoring(self) -> None:
        """Stop all monitoring systems."""
        if not self._monitoring_enabled:
            return
        
        try:
            self._performance_monitor.stop()
            self._health_monitor.stop()
            self._memory_monitor.stop()
            self._metrics_collector.stop()
        except Exception:
            pass
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        if not self._monitoring_enabled:
            return {'status': 'unknown', 'reason': 'Monitoring disabled'}
        
        self._health_checks += 1
        
        try:
            health_status = self._health_monitor.get_status()
            memory_status = self._memory_monitor.get_status()
            performance_status = self._performance_monitor.get_status()
            
            # Determine overall health
            overall_status = 'healthy'
            if health_status.get('status') == 'unhealthy':
                overall_status = 'unhealthy'
            elif memory_status.get('status') == 'warning':
                overall_status = 'warning'
            
            return {
                'status': overall_status,
                'timestamp': time.time(),
                'uptime': time.time() - self._start_time,
                'health': health_status,
                'memory': memory_status,
                'performance': performance_status
            }
        except Exception as e:
            return {
                'status': 'error',
                'reason': f'Health check failed: {e}',
                'timestamp': time.time()
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self._monitoring_enabled:
            return {}
        
        self._performance_measurements += 1
        
        try:
            return self._performance_monitor.get_metrics()
        except Exception:
            return {}
    
    def get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory metrics."""
        if not self._monitoring_enabled:
            return {}
        
        self._memory_checks += 1
        
        try:
            return self._memory_monitor.get_metrics()
        except Exception:
            return {}
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all available metrics."""
        if not self._monitoring_enabled:
            return {}
        
        try:
            return {
                'performance': self.get_performance_metrics(),
                'memory': self.get_memory_metrics(),
                'health': self.get_health_status(),
                'system': self._metrics_collector.get_system_metrics()
            }
        except Exception:
            return {}
    
    def record_metric(self, metric_name: str, value: Any, **kwargs) -> None:
        """Record a custom metric."""
        if not self._monitoring_enabled:
            return
        
        try:
            self._metrics_collector.record(metric_name, value, **kwargs)
        except Exception:
            pass
    
    def set_alert_threshold(self, metric_name: str, threshold: float, operator: str = '>') -> None:
        """Set an alert threshold for a metric."""
        if not self._monitoring_enabled:
            return
        
        try:
            self._metrics_collector.set_threshold(metric_name, threshold, operator)
        except Exception:
            pass
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get current alerts."""
        if not self._monitoring_enabled:
            return []
        
        try:
            return self._metrics_collector.get_alerts()
        except Exception:
            return []
    
    def clear_alerts(self) -> None:
        """Clear all current alerts."""
        if not self._monitoring_enabled:
            return
        
        try:
            self._metrics_collector.clear_alerts()
        except Exception:
            pass
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in the specified format."""
        if not self._monitoring_enabled:
            return ''
        
        try:
            return self._metrics_collector.export(format)
        except Exception:
            return ''
    
    def get_monitoring_metrics(self) -> Dict[str, Any]:
        """Get monitoring system metrics."""
        return {
            'monitoring_enabled': self._monitoring_enabled,
            'health_checks': self._health_checks,
            'performance_measurements': self._performance_measurements,
            'memory_checks': self._memory_checks,
            'uptime': time.time() - self._start_time,
            'start_time': self._start_time
        }
    
    def reset_metrics(self) -> None:
        """Reset monitoring metrics."""
        self._health_checks = 0
        self._performance_measurements = 0
        self._memory_checks = 0
        self._start_time = time.time()
    
    def get_performance_monitor(self) -> PerformanceMonitor:
        """Get the performance monitor."""
        return self._performance_monitor
    
    def get_health_monitor(self) -> HealthMonitor:
        """Get the health monitor."""
        return self._health_monitor
    
    def get_memory_monitor(self) -> MemoryMonitor:
        """Get the memory monitor."""
        return self._memory_monitor
    
    def get_metrics_collector(self) -> MetricsCollector:
        """Get the metrics collector."""
        return self._metrics_collector
