"""
Monitor Interface for Hydra-Logger

This module defines the abstract interface for monitoring components
including performance monitoring, health checks, and metrics collection.
It ensures consistent behavior across all monitoring implementations.

ARCHITECTURE:
- MonitorInterface: Abstract interface for all monitoring implementations
- Defines contract for monitoring operations and metrics collection
- Ensures consistent behavior across different monitoring types
- Supports health monitoring and metrics management

CORE FEATURES:
- Monitoring start/stop operations
- Metrics collection and management
- Health status monitoring
- Metrics reset and cleanup
- Performance tracking and analysis

USAGE EXAMPLES:

Interface Implementation:
    from hydra_logger.interfaces import MonitorInterface
    from typing import Any, Dict
    
    class PerformanceMonitor(MonitorInterface):
        def __init__(self):
            self._monitoring = False
            self._metrics = {
                "messages_processed": 0,
                "errors_count": 0,
                "start_time": None
            }
            self._healthy = True
        
        def start_monitoring(self) -> bool:
            try:
                self._monitoring = True
                self._metrics["start_time"] = time.time()
                return True
            except Exception:
                return False
        
        def stop_monitoring(self) -> bool:
            try:
                self._monitoring = False
                return True
            except Exception:
                return False
        
        def is_monitoring(self) -> bool:
            return self._monitoring
        
        def get_metrics(self) -> Dict[str, Any]:
            return self._metrics.copy()
        
        def reset_metrics(self) -> None:
            self._metrics = {
                "messages_processed": 0,
                "errors_count": 0,
                "start_time": None
            }
        
        def is_healthy(self) -> bool:
            return self._healthy
        
        def get_health_status(self) -> Dict[str, Any]:
            return {
                "healthy": self._healthy,
                "monitoring": self._monitoring,
                "metrics": self._metrics
            }

Monitor Usage:
    from hydra_logger.interfaces import MonitorInterface
    
    def use_monitor(monitor: MonitorInterface):
        \"\"\"Use any monitor that implements MonitorInterface.\"\"\"
        # Start monitoring
        if monitor.start_monitoring():
            print("Monitoring started")
            
            # Check if monitoring
            if monitor.is_monitoring():
                print("Monitor is active")
            
            # Get metrics
            metrics = monitor.get_metrics()
            print(f"Current metrics: {metrics}")
            
            # Check health
            if monitor.is_healthy():
                health = monitor.get_health_status()
                print(f"Monitor health: {health}")
            
            # Stop monitoring
            if monitor.stop_monitoring():
                print("Monitoring stopped")
        else:
            print("Failed to start monitoring")

Polymorphic Usage:
    from hydra_logger.interfaces import MonitorInterface
    
    def use_monitors(monitors: List[MonitorInterface]):
        \"\"\"Use multiple monitors with the same interface.\"\"\"
        # Start all monitors
        for monitor in monitors:
            if monitor.start_monitoring():
                print(f"Monitor started: {monitor.__class__.__name__}")
            else:
                print(f"Failed to start monitor: {monitor.__class__.__name__}")
        
        # Check monitoring status
        for monitor in monitors:
            if monitor.is_monitoring():
                metrics = monitor.get_metrics()
                print(f"Monitor active: {metrics}")
        
        # Stop all monitors
        for monitor in monitors:
            if monitor.stop_monitoring():
                print(f"Monitor stopped: {monitor.__class__.__name__}")

Metrics Management:
    from hydra_logger.interfaces import MonitorInterface
    
    def manage_metrics(monitor: MonitorInterface):
        \"\"\"Manage metrics using the monitor interface.\"\"\"
        # Get current metrics
        metrics = monitor.get_metrics()
        print(f"Current metrics: {metrics}")
        
        # Check health status
        if monitor.is_healthy():
            health = monitor.get_health_status()
            print(f"Monitor health: {health}")
        else:
            print("Monitor is unhealthy")
        
        # Reset metrics if needed
        monitor.reset_metrics()
        print("Metrics reset")

INTERFACE CONTRACTS:
- start_monitoring(): Start monitoring
- stop_monitoring(): Stop monitoring
- is_monitoring(): Check if monitoring is active
- get_metrics(): Get current metrics
- reset_metrics(): Reset all metrics
- is_healthy(): Check if system is healthy
- get_health_status(): Get detailed health status

ERROR HANDLING:
- All methods return boolean success indicators
- Health checks prevent monitoring with unhealthy systems
- Clear error messages and status reporting
- Graceful handling of monitoring failures

BENEFITS:
- Consistent monitoring API across implementations
- Easy testing with mock monitors
- Clear contracts for custom monitoring
- Polymorphic usage without tight coupling
- Better health monitoring and metrics management
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class MonitorInterface(ABC):
    """
    Abstract interface for all monitoring implementations.
    
    This interface defines the contract that all monitors must implement,
    ensuring consistent behavior across different monitoring types.
    """
    
    @abstractmethod
    def start_monitoring(self) -> bool:
        """
        Start monitoring.
        
        Returns:
            True if started successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def stop_monitoring(self) -> bool:
        """
        Stop monitoring.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_monitoring(self) -> bool:
        """
        Check if monitoring is active.
        
        Returns:
            True if monitoring, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.
        
        Returns:
            Metrics dictionary
        """
        raise NotImplementedError
    
    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        raise NotImplementedError
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """
        Check if system is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        raise NotImplementedError
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get detailed health status.
        
        Returns:
            Health status dictionary
        """
        raise NotImplementedError
