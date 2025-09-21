"""
Performance Monitoring Component for Hydra-Logger

This module provides comprehensive performance monitoring with operation
timing, throughput tracking, and resource usage monitoring. It helps
identify performance bottlenecks and optimize logging operations.

FEATURES:
- Operation timing and statistics
- Throughput monitoring and analysis
- Performance alerts and thresholds
- Historical performance data
- Resource usage tracking

USAGE:
    from hydra_logger.monitoring import PerformanceMonitor
    
    # Create performance monitor
    monitor = PerformanceMonitor(
        enabled=True,
        max_history=1000
    )
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Record operation performance
    monitor.record_operation("log_write", duration=0.05, success=True)
    
    # Get performance metrics
    metrics = monitor.get_metrics()
    
    # Get operation performance
    op_stats = monitor.get_operation_performance("log_write")
"""

import time
import threading
from typing import Any, Dict, List, Optional, Union
from ..interfaces.monitor import MonitorInterface


class PerformanceMonitor(MonitorInterface):
    """
    Professional performance monitor for logging operations.
    
    Features:
    - Operation timing and statistics
    - Throughput monitoring
    - Performance alerts and thresholds
    - Historical performance data
    - Resource usage tracking
    """
    
    def __init__(self, enabled: bool = True, max_history: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            enabled: Whether monitoring is enabled
            max_history: Maximum number of historical records to keep
        """
        self._enabled = enabled
        self._max_history = max_history
        self._initialized = False
        self._monitoring = False
        
        # Performance metrics
        self._operation_times = {}
        self._operation_counts = {}
        self._throughput_metrics = {}
        self._performance_history = []
        
        # Performance thresholds and alerts
        self._performance_thresholds = {
            'slow_operation': 1.0,  # seconds
            'high_throughput': 10000,  # operations per second
            'memory_pressure': 0.8,  # 80% memory usage
            'error_rate': 0.05,  # 5% error rate
        }
        
        # Performance alerts
        self._performance_alerts = []
        self._alert_history = []
        
        # Threading
        self._lock = threading.Lock()
        self._start_time = time.time()
        
        # Statistics
        self._stats = {
            'total_operations': 0,
            'total_time': 0.0,
            'peak_throughput': 0.0,
            'average_response_time': 0.0,
            'slow_operations': 0,
            'errors': 0,
        }
        
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the performance monitor."""
        try:
            # Validate configuration
            if self._max_history < 100:
                self._max_history = 100
            
            self._initialized = True
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize PerformanceMonitor: {e}")
    
    def start_monitoring(self) -> bool:
        """Start performance monitoring."""
        if not self._initialized:
            return False
        
        with self._lock:
            self._monitoring = True
            self._start_time = time.time()
            return True
    
    def stop_monitoring(self) -> bool:
        """Stop performance monitoring."""
        with self._lock:
            self._monitoring = False
            return True
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring and self._enabled
    
    def record_operation(self, operation: str, duration: float, 
                        success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record an operation's performance metrics.
        
        Args:
            operation: Operation name
            duration: Operation duration in seconds
            success: Whether operation was successful
            metadata: Additional operation metadata
        """
        if not self.is_monitoring():
            return
        
        with self._lock:
            try:
                # Update operation times
                if operation not in self._operation_times:
                    self._operation_times[operation] = []
                
                self._operation_times[operation].append(duration)
                
                # Keep only recent times for performance
                if len(self._operation_times[operation]) > 100:
                    self._operation_times[operation] = self._operation_times[operation][-100:]
                
                # Update operation counts
                if operation not in self._operation_counts:
                    self._operation_counts[operation] = {'total': 0, 'success': 0, 'errors': 0}
                
                self._operation_counts[operation]['total'] += 1
                if success:
                    self._operation_counts[operation]['success'] += 1
                else:
                    self._operation_counts[operation]['errors'] += 1
                
                # Update global statistics
                self._stats['total_operations'] += 1
                self._stats['total_time'] += duration
                self._stats['average_response_time'] = (
                    self._stats['total_time'] / self._stats['total_operations']
                )
                
                # Check for slow operations
                if duration > self._performance_thresholds['slow_operation']:
                    self._stats['slow_operations'] += 1
                    self._create_performance_alert('slow_operation', operation, duration)
                
                # Update throughput metrics
                self._update_throughput_metrics(operation, duration)
                
                # Add to history
                self._add_to_history(operation, duration, success, metadata)
                
                # Check performance thresholds
                self._check_performance_thresholds()
                
            except Exception as e:
                # Don't let monitoring errors break the main application
                pass
    
    def _update_throughput_metrics(self, operation: str, duration: float) -> None:
        """Update throughput metrics for an operation."""
        current_time = time.time()
        
        if operation not in self._throughput_metrics:
            self._throughput_metrics[operation] = {
                'operations': [],
                'last_reset': current_time
            }
        
        # Add operation with timestamp
        self._throughput_metrics[operation]['operations'].append(current_time)
        
        # Remove operations older than 1 second
        cutoff_time = current_time - 1.0
        self._throughput_metrics[operation]['operations'] = [
            t for t in self._throughput_metrics[operation]['operations']
            if t > cutoff_time
        ]
        
        # Calculate current throughput
        current_throughput = len(self._throughput_metrics[operation]['operations'])
        
        # Update peak throughput
        if current_throughput > self._stats['peak_throughput']:
            self._stats['peak_throughput'] = current_throughput
        
        # Check throughput threshold
        if current_throughput > self._performance_thresholds['high_throughput']:
            self._create_performance_alert('high_throughput', operation, current_throughput)
    
    def _add_to_history(self, operation: str, duration: float, 
                        success: bool, metadata: Optional[Dict[str, Any]]) -> None:
        """Add operation to performance history."""
        history_entry = {
            'timestamp': time.time(),
            'operation': operation,
            'duration': duration,
            'success': success,
            'metadata': metadata or {}
        }
        
        self._performance_history.append(history_entry)
        
        # Maintain history size
        if len(self._performance_history) > self._max_history:
            self._performance_history = self._performance_history[-self._max_history:]
    
    def _create_performance_alert(self, alert_type: str, operation: str, value: float) -> None:
        """Create a performance alert."""
        alert = {
            'type': alert_type,
            'operation': operation,
            'value': value,
            'threshold': self._performance_thresholds.get(alert_type, 0),
            'timestamp': time.time(),
            'severity': 'warning' if alert_type in ['slow_operation'] else 'info'
        }
        
        self._performance_alerts.append(alert)
        self._alert_history.append(alert)
        
        # Maintain alert history size
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]
    
    def _check_performance_thresholds(self) -> None:
        """Check all performance thresholds."""
        # This method can be extended to check additional thresholds
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self._lock:
            metrics = {
                'monitoring_active': self.is_monitoring(),
                'uptime': time.time() - self._start_time,
                'global_stats': self._stats.copy(),
                'operation_stats': {},
                'throughput_stats': {},
                'recent_alerts': self._performance_alerts[-10:] if self._performance_alerts else [],
                'alert_count': len(self._performance_alerts),
                'history_size': len(self._performance_history)
            }
            
            # Add operation-specific statistics
            for operation, times in self._operation_times.items():
                if times:
                    metrics['operation_stats'][operation] = {
                        'count': self._operation_counts[operation]['total'],
                        'success_count': self._operation_counts[operation]['success'],
                        'error_count': self._operation_counts[operation]['errors'],
                        'average_time': sum(times) / len(times),
                        'min_time': min(times),
                        'max_time': max(times),
                        'recent_times': times[-10:] if len(times) > 10 else times
                    }
            
            # Add throughput statistics
            for operation, throughput_data in self._throughput_metrics.items():
                current_throughput = len(throughput_data['operations'])
                metrics['throughput_stats'][operation] = {
                    'current_throughput': current_throughput,
                    'peak_throughput': self._stats['peak_throughput']
                }
            
            return metrics
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics."""
        with self._lock:
            self._operation_times.clear()
            self._operation_counts.clear()
            self._throughput_metrics.clear()
            self._performance_history.clear()
            self._performance_alerts.clear()
            self._alert_history.clear()
            
            self._stats = {
                'total_operations': 0,
                'total_time': 0.0,
                'peak_throughput': 0.0,
                'average_response_time': 0.0,
                'slow_operations': 0,
                'errors': 0,
            }
    
    def is_healthy(self) -> bool:
        """Check if performance is healthy."""
        with self._lock:
            # Check if we have too many slow operations
            slow_operation_ratio = (
                self._stats['slow_operations'] / max(self._stats['total_operations'], 1)
            )
            
            # Check if error rate is acceptable
            error_rate = (
                self._stats['errors'] / max(self._stats['total_operations'], 1)
            )
            
            return (slow_operation_ratio < 0.1 and  # Less than 10% slow operations
                    error_rate < 0.05)  # Less than 5% errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status."""
        with self._lock:
            total_ops = max(self._stats['total_operations'], 1)
            
            return {
                'healthy': self.is_healthy(),
                'uptime': time.time() - self._start_time,
                'total_operations': self._stats['total_operations'],
                'average_response_time': self._stats['average_response_time'],
                'peak_throughput': self._stats['peak_throughput'],
                'slow_operation_ratio': self._stats['slow_operations'] / total_ops,
                'error_rate': self._stats['errors'] / total_ops,
                'active_alerts': len(self._performance_alerts),
                'monitoring_active': self.is_monitoring()
            }
    
    def set_threshold(self, threshold_type: str, value: float) -> bool:
        """
        Set a performance threshold.
        
        Args:
            threshold_type: Type of threshold
            value: Threshold value
            
        Returns:
            True if threshold was set successfully
        """
        if threshold_type in self._performance_thresholds:
            self._performance_thresholds[threshold_type] = value
            return True
        return False
    
    def get_threshold(self, threshold_type: str) -> Optional[float]:
        """Get a performance threshold."""
        return self._performance_thresholds.get(threshold_type)
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get all performance alerts."""
        with self._lock:
            return self._performance_alerts.copy()
    
    def clear_performance_alerts(self) -> None:
        """Clear all performance alerts."""
        with self._lock:
            self._performance_alerts.clear()
    
    def get_operation_performance(self, operation: str) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for a specific operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Operation performance metrics or None if not found
        """
        with self._lock:
            if operation not in self._operation_times:
                return None
            
            times = self._operation_times[operation]
            counts = self._operation_counts[operation]
            
            return {
                'operation': operation,
                'total_count': counts['total'],
                'success_count': counts['success'],
                'error_count': counts['errors'],
                'average_time': sum(times) / len(times) if times else 0,
                'min_time': min(times) if times else 0,
                'max_time': max(times) if times else 0,
                'recent_times': times[-10:] if len(times) > 10 else times
            }
