"""
Professional AsyncHealthMonitor for system health monitoring and alerting.

This module provides real-time health status with performance metrics,
queue health monitoring, and caching for performance.
"""

import asyncio
import time
from typing import Dict, Any, Optional


class AsyncHealthMonitor:
    """
    Professional health monitoring with comprehensive metrics.
    
    Features:
    - Real-time health status
    - Performance metrics
    - Queue health monitoring
    - Caching for performance
    """
    
    def __init__(self, handler=None):
        """
        Initialize AsyncHealthMonitor.
        
        Args:
            handler: Handler to monitor (optional)
        """
        self._handler = handler
        self._start_time = time.time()
        self._last_check = 0
        self._check_interval = 1.0  # Check every second
        self._cached_status = None
        self._stats = {
            'checks': 0,
            'health_changes': 0,
            'last_health_status': True
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get professional health status with caching.
        
        Returns:
            Dict[str, Any]: Comprehensive health status
        """
        current_time = time.time()
        
        # Cache results to avoid excessive checks
        if current_time - self._last_check < self._check_interval:
            return self._cached_status or self._get_basic_status()
        
        self._stats['checks'] += 1
        self._last_check = current_time
        
        try:
            status = self._get_comprehensive_status()
            
            # Track health changes
            current_health = status.get('is_healthy', True)
            if current_health != self._stats['last_health_status']:
                self._stats['health_changes'] += 1
                self._stats['last_health_status'] = current_health
            
            self._cached_status = status
            return status
            
        except Exception as e:
            # Return basic status if monitoring fails
            status = self._get_basic_status()
            status['error'] = str(e)
            return status
    
    def _get_basic_status(self) -> Dict[str, Any]:
        """Get basic health status."""
        return {
            'uptime': time.time() - self._start_time,
            'is_healthy': True,
            'last_check': self._last_check,
            'monitor_type': self.__class__.__name__
        }
    
    def _get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        status = {
            'uptime': time.time() - self._start_time,
            'last_check': self._last_check,
            'monitor_type': self.__class__.__name__,
            'stats': self._stats.copy()
        }
        
        # Add handler-specific metrics if available
        if self._handler:
            status.update(self._get_handler_metrics())
        
        # Add general system metrics
        status.update(self._get_system_metrics())
        
        # Determine overall health
        status['is_healthy'] = self._determine_health(status)
        
        return status
    
    def _get_handler_metrics(self) -> Dict[str, Any]:
        """Get handler-specific metrics."""
        metrics = {}
        
        try:
            if hasattr(self._handler, 'get_health_status'):
                handler_health = self._handler.get_health_status()
                metrics['handler_health'] = handler_health
            
            if hasattr(self._handler, 'get_error_stats'):
                error_stats = self._handler.get_error_stats()
                metrics['error_stats'] = error_stats
            
            if hasattr(self._handler, '_queue'):
                queue_stats = self._handler._queue.get_stats()
                metrics['queue_stats'] = queue_stats
            
            if hasattr(self._handler, '_memory_monitor'):
                memory_stats = self._handler._memory_monitor.get_memory_stats()
                metrics['memory_stats'] = memory_stats
                
        except Exception as e:
            metrics['handler_metrics_error'] = str(e)
        
        return metrics
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get general system metrics."""
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_mb': memory.available / (1024 * 1024),
                    'process_memory_mb': process_memory.rss / (1024 * 1024),
                    'process_cpu_percent': process.cpu_percent()
                }
            }
            
        except Exception as e:
            return {
                'system': {
                    'error': str(e),
                    'note': 'psutil not available'
                }
            }
    
    def _determine_health(self, status: Dict[str, Any]) -> bool:
        """Determine overall health status."""
        # Check handler health
        if 'handler_health' in status:
            handler_health = status['handler_health']
            if not handler_health.get('is_healthy', True):
                return False
        
        # Check error stats
        if 'error_stats' in status:
            error_stats = status['error_stats']
            if error_stats.get('total_errors', 0) > 50:
                return False
        
        # Check queue health
        if 'queue_stats' in status:
            queue_stats = status['queue_stats']
            if queue_stats.get('is_full', False):
                return False
            if queue_stats.get('dropped_count', 0) > 100:
                return False
        
        # Check memory health
        if 'memory_stats' in status:
            memory_stats = status['memory_stats']
            if memory_stats.get('current_percent', 0) > 90:
                return False
        
        # Check system health
        if 'system' in status:
            system = status['system']
            if system.get('cpu_percent', 0) > 95:
                return False
            if system.get('memory_percent', 0) > 95:
                return False
        
        return True
    
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        status = self.get_health_status()
        return status.get('is_healthy', True)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        status = self.get_health_status()
        return {
            'uptime': status.get('uptime', 0),
            'checks_performed': self._stats['checks'],
            'health_changes': self._stats['health_changes'],
            'current_health': status.get('is_healthy', True),
            'system_metrics': status.get('system', {}),
            'handler_metrics': status.get('handler_health', {})
        }
    
    def set_check_interval(self, interval: float) -> None:
        """Set health check interval."""
        self._check_interval = interval
    
    def reset_stats(self) -> None:
        """Reset health monitor statistics."""
        self._stats = {
            'checks': 0,
            'health_changes': 0,
            'last_health_status': True
        }
        self._start_time = time.time()
        self._cached_status = None
    
    async def shutdown(self) -> None:
        """Shutdown health monitor."""
        self._handler = None
        self._cached_status = None 