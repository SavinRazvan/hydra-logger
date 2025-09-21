"""
Handler Types for Hydra-Logger

This module provides comprehensive type definitions for log handlers,
including configuration, state management, performance metrics, and
health monitoring. It supports all aspects of handler lifecycle
and performance tracking.

FEATURES:
- HandlerConfig: Handler configuration and settings
- HandlerState: Current handler state and status
- HandlerMetrics: Performance metrics and statistics
- HandlerHealth: Health monitoring and diagnostics

HANDLER CONFIGURATION:
- Core settings: ID, type, enabled status, log level
- Performance settings: Buffer size, flush interval, queue size
- Error handling: Retry count, retry delay, fail silently
- Security settings: Encryption, compression, validation

HANDLER STATE:
- Status tracking: Initializing, running, paused, stopped, error
- Operational flags: Initialized, running, paused, stopped, error
- Error information: Error messages, counts, timestamps
- Performance state: Queue size, backlog status, memory usage

HANDLER METRICS:
- Processing metrics: Records processed, dropped, failed
- Performance metrics: Processing times, throughput, peak performance
- Queue metrics: Queue size, operations, full count
- Error metrics: Total errors, consecutive errors, max consecutive errors

HANDLER HEALTH:
- Health scoring: 0-100 health score with threshold-based assessment
- Health indicators: Response time, error rate, throughput, memory usage
- Health thresholds: Configurable limits for health assessment
- Health details: Issues and recommendations for improvement

USAGE:
    from hydra_logger.types import (
        HandlerConfig, HandlerState, HandlerMetrics, HandlerHealth
    )
    
    # Create handler configuration
    config = HandlerConfig(
        handler_type="console",
        enabled=True,
        level="INFO",
        buffer_size=8192,
        flush_interval=1.0
    )
    
    # Create handler state
    state = HandlerState(handler_id=config.handler_id)
    state.set_status("running")
    
    # Create handler metrics
    metrics = HandlerMetrics(handler_id=config.handler_id)
    metrics.record_processing(0.001, success=True)
    
    # Create handler health
    health = HandlerHealth(handler_id=config.handler_id)
    health.check_health(metrics, state)
    
    # Get performance summary
    summary = metrics.get_summary()
    print(f"Records processed: {summary['records_processed']}")
    print(f"Success rate: {summary['success_rate']:.2%}")
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
import time


@dataclass
class HandlerConfig:
    """Base configuration for log handlers."""
    
    # Core configuration
    handler_id: str = field(default_factory=lambda: f"handler_{int(time.time() * 1000)}")
    handler_type: str = "unknown"
    enabled: bool = True
    level: str = "INFO"
    
    # Handler-specific settings
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Performance settings
    buffer_size: int = 8192
    flush_interval: float = 1.0
    max_queue_size: int = 10000
    
    # Error handling
    max_retries: int = 3
    retry_delay: float = 1.0
    fail_silently: bool = False
    
    # Security settings
    enable_encryption: bool = False
    enable_compression: bool = False
    enable_validation: bool = True
    
    def __post_init__(self):
        """Initialize handler config after creation."""
        if not self.handler_id:
            self.handler_id = f"handler_{int(time.time() * 1000)}"
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a handler setting."""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a handler setting."""
        self.settings[key] = value
    
    def has_setting(self, key: str) -> bool:
        """Check if a setting exists."""
        return key in self.settings
    
    def remove_setting(self, key: str) -> Any:
        """Remove a setting and return its value."""
        return self.settings.pop(key, None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'handler_id': self.handler_id,
            'handler_type': self.handler_type,
            'enabled': self.enabled,
            'level': self.level,
            'settings': self.settings,
            'buffer_size': self.buffer_size,
            'flush_interval': self.flush_interval,
            'max_queue_size': self.max_queue_size,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'fail_silently': self.fail_silently,
            'enable_encryption': self.enable_encryption,
            'enable_compression': self.enable_compression,
            'enable_validation': self.enable_validation
        }


@dataclass
class HandlerState:
    """Current state of a log handler."""
    
    # State information
    handler_id: str
    status: str = "initializing"  # initializing, running, paused, stopped, error
    last_status_change: float = field(default_factory=time.time)
    
    # Operational state
    is_initialized: bool = False
    is_running: bool = False
    is_paused: bool = False
    is_stopped: bool = False
    has_error: bool = False
    
    # Error information
    error_message: Optional[str] = None
    error_count: int = 0
    last_error_time: Optional[float] = None
    
    # Performance state
    queue_size: int = 0
    is_backlogged: bool = False
    memory_usage: Optional[int] = None
    
    def __post_init__(self):
        """Initialize handler state after creation."""
        self.last_status_change = time.time()
    
    def set_status(self, status: str) -> None:
        """Set the handler status."""
        if status != self.status:
            self.status = status
            self.last_status_change = time.time()
            
            # Update boolean flags
            self.is_running = status == "running"
            self.is_paused = status == "paused"
            self.is_stopped = status == "stopped"
            self.has_error = status == "error"
    
    def set_error(self, error_message: str) -> None:
        """Set an error state."""
        self.set_status("error")
        self.error_message = error_message
        self.error_count += 1
        self.last_error_time = time.time()
    
    def clear_error(self) -> None:
        """Clear error state."""
        self.error_message = None
        self.has_error = False
        if self.status == "error":
            self.set_status("stopped")
    
    def update_queue_size(self, size: int) -> None:
        """Update the current queue size."""
        self.queue_size = size
        self.is_backlogged = size > 0
    
    def update_memory_usage(self, usage: int) -> None:
        """Update memory usage information."""
        self.memory_usage = usage
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            'handler_id': self.handler_id,
            'status': self.status,
            'last_status_change': self.last_status_change,
            'is_initialized': self.is_initialized,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'is_stopped': self.is_stopped,
            'has_error': self.has_error,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'last_error_time': self.last_error_time,
            'queue_size': self.queue_size,
            'is_backlogged': self.is_backlogged,
            'memory_usage': self.memory_usage
        }


@dataclass
class HandlerMetrics:
    """Performance metrics for a log handler."""
    
    # Core metrics
    handler_id: str
    start_time: float = field(default_factory=time.time)
    last_reset: float = field(default_factory=time.time)
    
    # Processing metrics
    records_processed: int = 0
    records_dropped: int = 0
    records_failed: int = 0
    
    # Performance metrics
    total_processing_time: float = 0.0
    min_processing_time: float = float('inf')
    max_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    
    # Queue metrics
    max_queue_size: int = 0
    total_queue_operations: int = 0
    queue_full_count: int = 0
    
    # Error metrics
    total_errors: int = 0
    consecutive_errors: int = 0
    max_consecutive_errors: int = 0
    
    # Throughput metrics
    records_per_second: float = 0.0
    peak_throughput: float = 0.0
    
    def __post_init__(self):
        """Initialize metrics after creation."""
        self.start_time = time.time()
        self.last_reset = self.start_time
    
    def record_processing(self, processing_time: float, success: bool = True) -> None:
        """Record a processing operation."""
        self.records_processed += 1
        self.total_processing_time += processing_time
        
        # Update min/max times
        if processing_time < self.min_processing_time:
            self.min_processing_time = processing_time
        if processing_time > self.max_processing_time:
            self.max_processing_time = processing_time
        
        # Update average
        self.avg_processing_time = self.total_processing_time / self.records_processed
        
        # Update throughput
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            self.records_per_second = self.records_processed / elapsed
            if self.records_per_second > self.peak_throughput:
                self.peak_throughput = self.records_per_second
        
        # Handle errors
        if not success:
            self.records_failed += 1
            self.total_errors += 1
            self.consecutive_errors += 1
            if self.consecutive_errors > self.max_consecutive_errors:
                self.max_consecutive_errors = self.consecutive_errors
        else:
            self.consecutive_errors = 0
    
    def record_dropped(self) -> None:
        """Record a dropped record."""
        self.records_dropped += 1
    
    def record_queue_operation(self, queue_size: int) -> None:
        """Record a queue operation."""
        self.total_queue_operations += 1
        if queue_size > self.max_queue_size:
            self.max_queue_size = queue_size
        if queue_size == 0:
            self.queue_full_count += 1
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.records_processed = 0
        self.records_dropped = 0
        self.records_failed = 0
        self.total_processing_time = 0.0
        self.min_processing_time = float('inf')
        self.max_processing_time = 0.0
        self.avg_processing_time = 0.0
        self.max_queue_size = 0
        self.total_queue_operations = 0
        self.queue_full_count = 0
        self.total_errors = 0
        self.consecutive_errors = 0
        self.max_consecutive_errors = 0
        self.records_per_second = 0.0
        self.peak_throughput = 0.0
        self.last_reset = time.time()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        elapsed = time.time() - self.start_time
        return {
            'handler_id': self.handler_id,
            'uptime_seconds': elapsed,
            'records_processed': self.records_processed,
            'records_dropped': self.records_dropped,
            'records_failed': self.records_failed,
            'success_rate': (self.records_processed - self.records_failed) / max(self.records_processed, 1),
            'avg_processing_time_ms': self.avg_processing_time * 1000,
            'min_processing_time_ms': self.min_processing_time * 1000 if self.min_processing_time != float('inf') else 0,
            'max_processing_time_ms': self.max_processing_time * 1000,
            'records_per_second': self.records_per_second,
            'peak_throughput': self.peak_throughput,
            'total_errors': self.total_errors,
            'max_consecutive_errors': self.max_consecutive_errors,
            'queue_metrics': {
                'max_queue_size': self.max_queue_size,
                'total_operations': self.total_queue_operations,
                'full_count': self.queue_full_count
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'handler_id': self.handler_id,
            'start_time': self.start_time,
            'last_reset': self.last_reset,
            'records_processed': self.records_processed,
            'records_dropped': self.records_dropped,
            'records_failed': self.records_failed,
            'total_processing_time': self.total_processing_time,
            'min_processing_time': self.min_processing_time,
            'max_processing_time': self.max_processing_time,
            'avg_processing_time': self.avg_processing_time,
            'max_queue_size': self.max_queue_size,
            'total_queue_operations': self.total_queue_operations,
            'queue_full_count': self.queue_full_count,
            'total_errors': self.total_errors,
            'consecutive_errors': self.consecutive_errors,
            'max_consecutive_errors': self.max_consecutive_errors,
            'records_per_second': self.records_per_second,
            'peak_throughput': self.peak_throughput
        }


@dataclass
class HandlerHealth:
    """Health status for a log handler."""
    
    handler_id: str
    is_healthy: bool = True
    health_score: float = 100.0  # 0-100 scale
    last_check: float = field(default_factory=time.time)
    
    # Health indicators
    response_time: Optional[float] = None
    error_rate: float = 0.0
    throughput: Optional[float] = None
    memory_usage: Optional[float] = None
    
    # Health thresholds
    max_response_time: float = 1.0  # seconds
    max_error_rate: float = 0.05    # 5%
    max_memory_usage: float = 0.8   # 80%
    min_throughput: float = 100.0   # records/second
    
    # Health details
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize health after creation."""
        self.last_check = time.time()
    
    def check_health(self, metrics: HandlerMetrics, state: HandlerState) -> None:
        """Check handler health based on metrics and state."""
        self.last_check = time.time()
        self.issues.clear()
        self.recommendations.clear()
        
        # Check basic state
        if state.has_error:
            self.issues.append(f"Handler has error: {state.error_message}")
            self.health_score -= 30
        
        if state.is_backlogged:
            self.issues.append("Handler queue is backlogged")
            self.health_score -= 20
        
        # Check response time
        if metrics.avg_processing_time > self.max_response_time:
            self.issues.append(f"Response time too high: {metrics.avg_processing_time:.3f}s")
            self.health_score -= 15
            self.recommendations.append("Consider increasing buffer size or reducing load")
        
        # Check error rate
        if metrics.records_processed > 0:
            error_rate = metrics.records_failed / metrics.records_processed
            self.error_rate = error_rate
            if error_rate > self.max_error_rate:
                self.issues.append(f"Error rate too high: {error_rate:.2%}")
                self.health_score -= 25
                self.recommendations.append("Check handler configuration and error logs")
        
        # Check throughput
        if metrics.records_per_second < self.min_throughput:
            self.issues.append(f"Throughput too low: {metrics.records_per_second:.1f} records/s")
            self.health_score -= 10
            self.recommendations.append("Consider performance optimizations")
        
        # Update response time and throughput
        self.response_time = metrics.avg_processing_time
        self.throughput = metrics.records_per_second
        
        # Ensure health score is within bounds
        self.health_score = max(0.0, min(100.0, self.health_score))
        self.is_healthy = self.health_score >= 70.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health to dictionary."""
        return {
            'handler_id': self.handler_id,
            'is_healthy': self.is_healthy,
            'health_score': self.health_score,
            'last_check': self.last_check,
            'response_time': self.response_time,
            'error_rate': self.error_rate,
            'throughput': self.throughput,
            'memory_usage': self.memory_usage,
            'issues': self.issues,
            'recommendations': self.recommendations
        }


# Convenience functions
def create_handler_config(handler_type: str, **kwargs) -> HandlerConfig:
    """Create a new handler configuration."""
    return HandlerConfig(handler_type=handler_type, **kwargs)


def create_handler_state(handler_id: str) -> HandlerState:
    """Create a new handler state."""
    return HandlerState(handler_id=handler_id)


def create_handler_metrics(handler_id: str) -> HandlerMetrics:
    """Create new handler metrics."""
    return HandlerMetrics(handler_id=handler_id)


def create_handler_health(handler_id: str) -> HandlerHealth:
    """Create new handler health."""
    return HandlerHealth(handler_id=handler_id)


# Export the main classes and functions
__all__ = [
    "HandlerConfig",
    "HandlerState",
    "HandlerMetrics",
    "HandlerHealth",
    "create_handler_config",
    "create_handler_state",
    "create_handler_metrics",
    "create_handler_health"
]
