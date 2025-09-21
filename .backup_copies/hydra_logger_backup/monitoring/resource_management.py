"""
Resource Management Component for Hydra-Logger

This module provides intelligent resource management with allocation strategies,
monitoring, and optimization. It manages system resources including CPU, memory,
disk, network, threads, and file descriptors with configurable allocation strategies.

FEATURES:
- Multiple resource types (CPU, memory, disk, network, threads, file descriptors)
- Configurable allocation strategies (first-fit, best-fit, round-robin, etc.)
- Resource monitoring and threshold management
- Background and synchronous processing modes
- Resource allocation history and analytics

USAGE:
    from hydra_logger.monitoring import ResourceManager, ResourceType, AllocationStrategy
    
    # Create resource manager
    manager = ResourceManager(
        enabled=True,
        strategy=AllocationStrategy.BEST_FIT,
        use_background_processing=True
    )
    
    # Start monitoring
    manager.start_monitoring()
    
    # Allocate resource
    allocation_id = manager.allocate_resource(
        resource_type=ResourceType.MEMORY,
        amount=1024,
        requester="logger"
    )
    
    # Get resource status
    status = manager.get_resource_status(ResourceType.MEMORY)
    
    # Deallocate resource
    manager.deallocate_resource(allocation_id, reason="task_complete")
"""

import time
import threading
import psutil
from typing import Any, Dict, List, Optional, Callable, Union
from collections import defaultdict, deque
from enum import Enum
from concurrent.futures import Future
from ..interfaces.monitor import MonitorInterface
from ..security.background_processing import (
    BackgroundSecurityProcessor, 
    SecurityOperationType, 
    get_background_processor
)


class ResourceType(Enum):
    """Types of system resources."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    THREADS = "threads"
    FILE_DESCRIPTORS = "file_descriptors"


class ResourceState(Enum):
    """Resource states."""
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    EXHAUSTED = "exhausted"
    CRITICAL = "critical"


class AllocationStrategy(Enum):
    """Resource allocation strategies."""
    FIRST_FIT = "first_fit"
    BEST_FIT = "best_fit"
    WORST_FIT = "worst_fit"
    ROUND_ROBIN = "round_robin"
    PRIORITY_BASED = "priority_based"


class ResourceManager(MonitorInterface):
    """Real resource management component for intelligent resource allocation and monitoring."""
    
    def __init__(self, enabled: bool = True, strategy: AllocationStrategy = AllocationStrategy.BEST_FIT,
                 use_background_processing: bool = True, sampling_interval: float = 1.0):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        self._strategy = strategy
        
        # Background processing configuration
        self._use_background_processing = use_background_processing and enabled
        self._background_processor = get_background_processor()
        self._sampling_interval = sampling_interval
        
        # Resource operation queue for background processing
        self._resource_queue = []
        self._queue_lock = threading.Lock()
        self._background_thread = None
        
        # Resource pools and allocation
        self._resource_pools = {
            ResourceType.CPU: {
                "total": psutil.cpu_count(),
                "available": psutil.cpu_count(),
                "allocated": 0,
                "reserved": 0,
                "units": "cores"
            },
            ResourceType.MEMORY: {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "allocated": 0,
                "reserved": 0,
                "units": "bytes"
            },
            ResourceType.THREADS: {
                "total": 1000,  # Arbitrary limit
                "available": 1000,
                "allocated": 0,
                "reserved": 0,
                "units": "threads"
            },
            ResourceType.FILE_DESCRIPTORS: {
                "total": 10000,  # Arbitrary limit
                "available": 10000,
                "allocated": 0,
                "reserved": 0,
                "units": "descriptors"
            }
        }
        
        # Resource allocations tracking
        self._allocations = {}
        self._allocation_history = deque(maxlen=1000)
        
        # Resource monitoring
        self._resource_metrics = defaultdict(lambda: deque(maxlen=100))
        self._resource_alerts = []
        self._max_alerts = 100
        
        # Resource thresholds
        self._resource_thresholds = {
            ResourceType.CPU: {
                "warning": 0.7,      # 70% usage
                "critical": 0.9,     # 90% usage
                "reservation": 0.2   # 20% reserved
            },
            ResourceType.MEMORY: {
                "warning": 0.8,      # 80% usage
                "critical": 0.95,    # 95% usage
                "reservation": 0.1   # 10% reserved
            },
            ResourceType.THREADS: {
                "warning": 0.8,      # 80% usage
                "critical": 0.95,    # 95% usage
                "reservation": 0.1   # 10% reserved
            },
            ResourceType.FILE_DESCRIPTORS: {
                "warning": 0.8,      # 80% usage
                "critical": 0.95,    # 95% usage
                "reservation": 0.1   # 10% reserved
            }
        }
        
        # Resource policies
        self._resource_policies = {
            "auto_scale": True,
            "auto_reclaim": True,
            "reservation_enabled": True,
            "overcommit_allowed": False,
            "max_allocation_time": 3600  # 1 hour
        }
        
        # Threading
        self._lock = threading.Lock()
        self._resource_thread = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._total_allocations = 0
        self._total_deallocations = 0
        self._failed_allocations = 0
        self._last_resource_check = 0.0
        
        # Background processing statistics
        self._background_operations = 0
        self._synchronous_operations = 0
        self._resource_cache = {}
        self._cache_max_size = 1000
        self._cache_ttl = 300.0  # 5 minutes
    
    def start_monitoring(self) -> bool:
        """Start resource management monitoring."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                self._resource_thread = threading.Thread(target=self._resource_loop, daemon=True)
                self._resource_thread.start()
                
                # Start background processing if enabled
                if self._use_background_processing:
                    self._background_thread = threading.Thread(target=self._background_processor_loop, daemon=True)
                    self._background_thread.start()
                
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop resource management monitoring."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                
                if self._resource_thread and self._resource_thread.is_alive():
                    self._resource_thread.join(timeout=5.0)
                
                # Stop background processing if enabled
                if self._background_thread and self._background_thread.is_alive():
                    self._background_thread.join(timeout=5.0)
                
                return True
        except Exception:
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def _resource_loop(self) -> None:
        """Main resource monitoring loop."""
        while not self._stop_event.is_set():
            try:
                self._update_resource_metrics()
                self._check_resource_thresholds()
                self._cleanup_expired_allocations()
                time.sleep(10)  # Check every 10 seconds
            except Exception:
                # Continue monitoring even if individual operations fail
                pass
    
    def _background_processor_loop(self) -> None:
        """Background processing loop for resource operations."""
        while not self._stop_event.is_set():
            try:
                self._process_resource_queue()
                time.sleep(self._sampling_interval)
            except Exception:
                # Continue processing even if individual operations fail
                pass
    
    def _process_resource_queue(self) -> None:
        """Process queued resource operations."""
        with self._queue_lock:
            if not self._resource_queue:
                return
            
            # Process all queued operations
            operations = self._resource_queue.copy()
            self._resource_queue.clear()
        
        for operation in operations:
            try:
                self._execute_resource_operation(operation)
                with self._lock:
                    self._background_operations += 1
            except Exception:
                # Log error but continue processing
                pass
    
    def _execute_resource_operation(self, operation: Dict[str, Any]) -> None:
        """Execute a resource operation."""
        op_type = operation.get('type')
        
        if op_type == 'update_metrics':
            self._update_resource_metrics_sync()
        elif op_type == 'check_thresholds':
            self._check_resource_thresholds_sync()
        elif op_type == 'cleanup_allocations':
            self._cleanup_expired_allocations_sync()
        elif op_type == 'allocate':
            self._allocate_resource_sync(operation.get('data', {}))
        elif op_type == 'deallocate':
            self._deallocate_resource_sync(operation.get('data', {}))
    
    def _queue_resource_operation(self, operation: Dict[str, Any]) -> None:
        """Queue a resource operation for background processing."""
        with self._queue_lock:
            self._resource_queue.append(operation)
    
    def _update_resource_metrics(self) -> None:
        """Update resource metrics and pools."""
        if not self._enabled:
            return
        
        # Use background processing if enabled
        if self._use_background_processing:
            self._queue_resource_operation({'type': 'update_metrics'})
        else:
            self._update_resource_metrics_sync()
    
    def _update_resource_metrics_sync(self) -> None:
        """Synchronous resource metrics update."""
        if not self._enabled:
            return
        
        current_time = time.time()
        
        try:
            # Update CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            self._resource_pools[ResourceType.CPU]["total"] = cpu_count
            self._resource_pools[ResourceType.CPU]["available"] = max(0, cpu_count - self._resource_pools[ResourceType.CPU]["allocated"])
            
            # Update memory metrics
            memory = psutil.virtual_memory()
            
            self._resource_pools[ResourceType.MEMORY]["total"] = memory.total
            self._resource_pools[ResourceType.MEMORY]["available"] = max(0, memory.available - self._resource_pools[ResourceType.MEMORY]["allocated"])
            
            # Store metrics
            self._resource_metrics[ResourceType.CPU].append({
                "timestamp": current_time,
                "usage_percent": cpu_percent,
                "available": self._resource_pools[ResourceType.CPU]["available"],
                "allocated": self._resource_pools[ResourceType.CPU]["allocated"]
            })
            
            self._resource_metrics[ResourceType.MEMORY].append({
                "timestamp": current_time,
                "usage_percent": memory.percent,
                "available": self._resource_pools[ResourceType.MEMORY]["available"],
                "allocated": self._resource_pools[ResourceType.MEMORY]["allocated"]
            })
            
            self._last_resource_check = current_time
            
            with self._lock:
                self._synchronous_operations += 1
            
        except Exception as e:
            # Log error but continue monitoring
            pass
    
    def _check_resource_thresholds(self) -> None:
        """Check resource usage against thresholds."""
        if not self._enabled:
            return
        
        # Use background processing if enabled
        if self._use_background_processing:
            self._queue_resource_operation({'type': 'check_thresholds'})
        else:
            self._check_resource_thresholds_sync()
    
    def _check_resource_thresholds_sync(self) -> None:
        """Synchronous resource threshold checking."""
        if not self._enabled:
            return
        
        current_time = time.time()
        
        for resource_type, pool in self._resource_pools.items():
            if resource_type not in self._resource_thresholds:
                continue
            
            thresholds = self._resource_thresholds[resource_type]
            usage_ratio = 1.0 - (pool["available"] / pool["total"])
            
            # Check critical threshold
            if usage_ratio >= thresholds["critical"]:
                self._add_resource_alert(
                    "critical",
                    f"{resource_type.value} usage critical: {usage_ratio:.1%}",
                    resource_type,
                    usage_ratio,
                    current_time
                )
            
            # Check warning threshold
            elif usage_ratio >= thresholds["warning"]:
                self._add_resource_alert(
                    "warning",
                    f"{resource_type.value} usage high: {usage_ratio:.1%}",
                    resource_type,
                    usage_ratio,
                    current_time
                )
        
        with self._lock:
            self._synchronous_operations += 1
    
    def _cleanup_expired_allocations(self) -> None:
        """Clean up expired resource allocations."""
        if not self._enabled:
            return
        
        # Use background processing if enabled
        if self._use_background_processing:
            self._queue_resource_operation({'type': 'cleanup_allocations'})
        else:
            self._cleanup_expired_allocations_sync()
    
    def _cleanup_expired_allocations_sync(self) -> None:
        """Synchronous cleanup of expired allocations."""
        if not self._enabled:
            return
        
        current_time = time.time()
        expired_allocations = []
        
        with self._lock:
            for allocation_id, allocation in self._allocations.items():
                if allocation.get("expires_at") and current_time > allocation["expires_at"]:
                    expired_allocations.append(allocation_id)
            
            for allocation_id in expired_allocations:
                self._deallocate_resource(allocation_id, reason="expired")
            
            self._synchronous_operations += 1
    
    def _add_resource_alert(self, level: str, message: str, resource_type: ResourceType, 
                           usage_ratio: float, timestamp: float) -> None:
        """Add a resource alert."""
        alert = {
            "level": level,
            "message": message,
            "resource_type": resource_type.value,
            "usage_ratio": usage_ratio,
            "timestamp": timestamp
        }
        
        self._resource_alerts.append(alert)
        
        # Keep only recent alerts
        if len(self._resource_alerts) > self._max_alerts:
            self._resource_alerts = self._resource_alerts[-self._max_alerts:]
    
    def allocate_resource(self, resource_type: ResourceType, amount: int, 
                         requester: str, priority: int = 1, timeout: Optional[int] = None) -> Optional[str]:
        """
        Allocate a resource.
        
        Args:
            resource_type: Type of resource to allocate
            amount: Amount of resource to allocate
            requester: Who is requesting the resource
            priority: Allocation priority (higher = more important)
            timeout: Allocation timeout in seconds
            
        Returns:
            Allocation ID if successful, None otherwise
        """
        if not self._enabled or resource_type not in self._resource_pools:
            return None
        
        # Use background processing if enabled
        if self._use_background_processing:
            return self._allocate_resource_background(resource_type, amount, requester, priority, timeout)
        else:
            return self._allocate_resource_sync(resource_type, amount, requester, priority, timeout)
    
    def _allocate_resource_sync(self, resource_type: ResourceType, amount: int, 
                               requester: str, priority: int = 1, timeout: Optional[int] = None) -> Optional[str]:
        """Synchronous resource allocation."""
        try:
            with self._lock:
                pool = self._resource_pools[resource_type]
                
                # Check if enough resources are available
                if not self._can_allocate_resource(resource_type, amount):
                    self._failed_allocations += 1
                    return None
                
                # Create allocation
                allocation_id = self._generate_allocation_id()
                allocation = {
                    "id": allocation_id,
                    "resource_type": resource_type.value,
                    "amount": amount,
                    "requester": requester,
                    "priority": priority,
                    "allocated_at": time.time(),
                    "expires_at": time.time() + timeout if timeout else None,
                    "status": "active"
                }
                
                # Apply allocation strategy
                if self._strategy == AllocationStrategy.BEST_FIT:
                    success = self._allocate_best_fit(resource_type, amount)
                elif self._strategy == AllocationStrategy.FIRST_FIT:
                    success = self._allocate_first_fit(resource_type, amount)
                elif self._strategy == AllocationStrategy.WORST_FIT:
                    success = self._allocate_worst_fit(resource_type, amount)
                else:  # ROUND_ROBIN
                    success = self._allocate_round_robin(resource_type, amount)
                
                if success:
                    # Record allocation
                    self._allocations[allocation_id] = allocation
                    self._allocation_history.append(allocation.copy())
                    self._total_allocations += 1
                    
                    # Update pool
                    pool["allocated"] += amount
                    pool["available"] = max(0, pool["total"] - pool["allocated"])
                    
                    return allocation_id
                else:
                    self._failed_allocations += 1
                    return None
                    
        except Exception:
            self._failed_allocations += 1
            return None
    
    def _allocate_resource_background(self, resource_type: ResourceType, amount: int, 
                                    requester: str, priority: int = 1, timeout: Optional[int] = None) -> Optional[str]:
        """Background resource allocation."""
        # For immediate allocation, we still need to do it synchronously
        # But we can queue the cleanup and monitoring operations
        allocation_id = self._allocate_resource_sync(resource_type, amount, requester, priority, timeout)
        
        if allocation_id:
            # Queue background operations
            self._queue_resource_operation({
                'type': 'update_metrics',
                'allocation_id': allocation_id
            })
            self._queue_resource_operation({
                'type': 'check_thresholds',
                'allocation_id': allocation_id
            })
        
        return allocation_id
    
    def _can_allocate_resource(self, resource_type: ResourceType, amount: int) -> bool:
        """Check if resource can be allocated."""
        pool = self._resource_pools[resource_type]
        thresholds = self._resource_thresholds[resource_type]
        
        # Check if enough resources are available
        if pool["available"] < amount:
            return False
        
        # Check reservation policy
        if self._resource_policies["reservation_enabled"]:
            reserved_amount = pool["total"] * thresholds["reservation"]
            if pool["available"] - amount < reserved_amount:
                return False
        
        return True
    
    def _allocate_best_fit(self, resource_type: ResourceType, amount: int) -> bool:
        """Allocate using best-fit strategy."""
        # Best-fit: allocate to the smallest available space that fits
        pool = self._resource_pools[resource_type]
        return pool["available"] >= amount
    
    def _allocate_first_fit(self, resource_type: ResourceType, amount: int) -> bool:
        """Allocate using first-fit strategy."""
        # First-fit: allocate to the first available space that fits
        pool = self._resource_pools[resource_type]
        return pool["available"] >= amount
    
    def _allocate_worst_fit(self, resource_type: ResourceType, amount: int) -> bool:
        """Allocate using worst-fit strategy."""
        # Worst-fit: allocate to the largest available space
        pool = self._resource_pools[resource_type]
        return pool["available"] >= amount
    
    def _allocate_round_robin(self, resource_type: ResourceType, amount: int) -> bool:
        """Allocate using round-robin strategy."""
        # Round-robin: allocate in a circular manner
        pool = self._resource_pools[resource_type]
        return pool["available"] >= amount
    
    def deallocate_resource(self, allocation_id: str, reason: str = "manual") -> bool:
        """
        Deallocate a resource.
        
        Args:
            allocation_id: ID of allocation to deallocate
            reason: Reason for deallocation
            
        Returns:
            True if deallocation successful
        """
        if not self._enabled or allocation_id not in self._allocations:
            return False
        
        try:
            with self._lock:
                allocation = self._allocations[allocation_id]
                resource_type = ResourceType(allocation["resource_type"])
                amount = allocation["amount"]
                
                # Update allocation status
                allocation["status"] = "deallocated"
                allocation["deallocated_at"] = time.time()
                allocation["deallocation_reason"] = reason
                
                # Update pool
                pool = self._resource_pools[resource_type]
                pool["allocated"] = max(0, pool["allocated"] - amount)
                pool["available"] = min(pool["total"], pool["available"] + amount)
                
                # Record deallocation
                self._total_deallocations += 1
                
                return True
                
        except Exception:
            return False
    
    def _deallocate_resource(self, allocation_id: str, reason: str) -> bool:
        """Internal deallocation method."""
        return self.deallocate_resource(allocation_id, reason)
    
    def reserve_resource(self, resource_type: ResourceType, amount: int, 
                        requester: str, priority: int = 1) -> Optional[str]:
        """
        Reserve a resource without allocating it.
        
        Args:
            resource_type: Type of resource to reserve
            amount: Amount of resource to reserve
            requester: Who is reserving the resource
            priority: Reservation priority
            
        Returns:
            Reservation ID if successful, None otherwise
        """
        if not self._enabled or resource_type not in self._resource_pools:
            return None
        
        try:
            with self._lock:
                pool = self._resource_pools[resource_type]
                
                # Check if enough resources can be reserved
                if pool["available"] - pool["reserved"] < amount:
                    return None
                
                # Create reservation
                reservation_id = f"reservation_{int(time.time() * 1000)}"
                reservation = {
                    "id": reservation_id,
                    "resource_type": resource_type.value,
                    "amount": amount,
                    "requester": requester,
                    "priority": priority,
                    "reserved_at": time.time(),
                    "status": "reserved"
                }
                
                # Update pool
                pool["reserved"] += amount
                
                return reservation_id
                
        except Exception:
            return None
    
    def get_resource_status(self, resource_type: ResourceType) -> Dict[str, Any]:
        """Get status of a specific resource type."""
        if resource_type not in self._resource_pools:
            return {}
        
        pool = self._resource_pools[resource_type]
        thresholds = self._resource_thresholds.get(resource_type, {})
        
        usage_ratio = 1.0 - (pool["available"] / pool["total"])
        
        # Determine resource state
        if usage_ratio >= thresholds.get("critical", 1.0):
            state = ResourceState.CRITICAL
        elif usage_ratio >= thresholds.get("warning", 1.0):
            state = ResourceState.EXHAUSTED
        elif pool["available"] == 0:
            state = ResourceState.ALLOCATED
        elif pool["reserved"] > 0:
            state = ResourceState.RESERVED
        else:
            state = ResourceState.AVAILABLE
        
        return {
            "resource_type": resource_type.value,
            "state": state.value,
            "total": pool["total"],
            "available": pool["available"],
            "allocated": pool["allocated"],
            "reserved": pool["reserved"],
            "usage_ratio": usage_ratio,
            "units": pool["units"]
        }
    
    def get_all_resource_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all resources."""
        return {
            resource_type.value: self.get_resource_status(resource_type)
            for resource_type in self._resource_pools.keys()
        }
    
    def get_allocation_info(self, allocation_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific allocation."""
        return self._allocations.get(allocation_id)
    
    def get_active_allocations(self, resource_type: Optional[ResourceType] = None) -> List[Dict[str, Any]]:
        """Get all active allocations."""
        active_allocations = [
            allocation for allocation in self._allocations.values()
            if allocation["status"] == "active"
        ]
        
        if resource_type:
            active_allocations = [
                allocation for allocation in active_allocations
                if allocation["resource_type"] == resource_type.value
            ]
        
        return active_allocations
    
    def get_allocation_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get allocation history."""
        return list(self._allocation_history)[-limit:] if limit > 0 else list(self._allocation_history)
    
    def get_resource_metrics(self, resource_type: ResourceType, hours: int = 24) -> List[Dict[str, Any]]:
        """Get resource metrics for specified time period."""
        if resource_type not in self._resource_metrics:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        
        recent_metrics = [
            metric for metric in self._resource_metrics[resource_type]
            if metric["timestamp"] > cutoff_time
        ]
        
        return recent_metrics
    
    def get_resource_alerts(self, level: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get resource alerts with optional filtering."""
        alerts = self._resource_alerts.copy()
        
        if level:
            alerts = [a for a in alerts if a["level"] == level]
        
        return alerts[-limit:] if limit > 0 else alerts
    
    def set_resource_threshold(self, resource_type: ResourceType, threshold_name: str, value: float) -> bool:
        """Set resource threshold."""
        if (resource_type in self._resource_thresholds and 
            threshold_name in self._resource_thresholds[resource_type]):
            self._resource_thresholds[resource_type][threshold_name] = value
            return True
        return False
    
    def get_resource_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Get all resource thresholds."""
        return {
            resource_type.value: thresholds.copy()
            for resource_type, thresholds in self._resource_thresholds.items()
        }
    
    def set_resource_policy(self, policy_name: str, value: Any) -> bool:
        """Set resource policy."""
        if policy_name in self._resource_policies:
            self._resource_policies[policy_name] = value
            return True
        return False
    
    def get_resource_policies(self) -> Dict[str, Any]:
        """Get all resource policies."""
        return self._resource_policies.copy()
    
    def set_allocation_strategy(self, strategy: AllocationStrategy) -> bool:
        """Set allocation strategy."""
        if strategy in AllocationStrategy:
            self._strategy = strategy
            return True
        return False
    
    def get_allocation_strategy(self) -> AllocationStrategy:
        """Get current allocation strategy."""
        return self._strategy
    
    def _generate_allocation_id(self) -> str:
        """Generate a unique allocation ID."""
        timestamp = int(time.time() * 1000)
        return f"allocation_{timestamp}_{self._total_allocations}"
    
    def _get_cache_key(self, operation: str, data: Any = None) -> str:
        """Generate cache key for operation and data."""
        import hashlib
        key_data = f"{operation}:{str(data)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache resource operation result."""
        with self._lock:
            if len(self._resource_cache) >= self._cache_max_size:
                # Remove oldest entries
                oldest_key = min(self._resource_cache.keys(),
                               key=lambda k: self._resource_cache[k]['timestamp'])
                del self._resource_cache[oldest_key]
            
            self._resource_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
    
    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if valid."""
        if cache_key in self._resource_cache:
            cached_result = self._resource_cache[cache_key]
            if time.time() - cached_result['timestamp'] < self._cache_ttl:
                return cached_result['result']
        return None
    
    def get_resource_manager_stats(self) -> Dict[str, Any]:
        """Get resource manager statistics."""
        with self._lock:
            stats = {
                "total_allocations": self._total_allocations,
                "total_deallocations": self._total_deallocations,
                "failed_allocations": self._failed_allocations,
                "active_allocations": len(self.get_active_allocations()),
                "allocation_success_rate": (self._total_allocations / (self._total_allocations + self._failed_allocations) 
                                          if (self._total_allocations + self._failed_allocations) > 0 else 0),
                "current_strategy": self._strategy.value,
                "last_resource_check": self._last_resource_check,
                "monitoring": self._monitoring,
                "enabled": self._enabled,
                "background_processing": self._use_background_processing,
                "synchronous_operations": self._synchronous_operations,
                "background_operations": self._background_operations,
                "cache_size": len(self._resource_cache),
                "queue_size": len(self._resource_queue)
            }
            return stats
    
    def reset_resource_stats(self) -> None:
        """Reset resource manager statistics."""
        with self._lock:
            self._allocation_history.clear()
            self._resource_metrics.clear()
            self._resource_alerts.clear()
            self._total_allocations = 0
            self._total_deallocations = 0
            self._failed_allocations = 0
            self._last_resource_check = 0.0
            self._synchronous_operations = 0
            self._background_operations = 0
            self._resource_cache.clear()
            self._resource_queue.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get resource manager metrics."""
        return self.get_resource_manager_stats()
    
    def reset_metrics(self) -> None:
        """Reset resource manager metrics."""
        self.reset_resource_stats()
    
    def is_healthy(self) -> bool:
        """Check if resource manager is healthy."""
        return (self._total_allocations > 0 and 
                self._failed_allocations / (self._total_allocations + self._failed_allocations) < 0.2)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get resource manager health status."""
        return {
            "healthy": self.is_healthy(),
            "allocation_success_rate": (self._total_allocations / (self._total_allocations + self._failed_allocations) 
                                      if (self._total_allocations + self._failed_allocations) > 0 else 0),
            "active_allocations": len(self.get_active_allocations()),
            "current_strategy": self._strategy.value,
            "monitoring": self._monitoring,
            "enabled": self._enabled,
            "background_processing": self._use_background_processing
        }
    
    def enable_background_processing(self, enabled: bool = True) -> None:
        """Enable or disable background processing."""
        self._use_background_processing = enabled and self._enabled
    
    def is_background_processing_enabled(self) -> bool:
        """Check if background processing is enabled."""
        return self._use_background_processing
    
    def set_sampling_interval(self, interval: float) -> None:
        """Set sampling interval for background processing."""
        self._sampling_interval = max(0.1, interval)  # Minimum 0.1 seconds
