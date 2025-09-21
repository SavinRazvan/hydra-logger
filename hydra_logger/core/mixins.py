"""
Reusable Behavior Mixins for Hydra-Logger

This module provides a comprehensive set of mixins that can be used to add
specific behaviors and capabilities to any component. Mixins enable
composition-based design and code reuse without multiple inheritance complexity.

MIXIN TYPES:
- PerformanceMixin: Performance monitoring and timing capabilities
- CachingMixin: TTL-based caching with statistics
- EventMixin: Event handling and notification system
- StateMixin: State management with change notifications
- MetricsMixin: Metrics collection and historical tracking

PERFORMANCE FEATURES:
- High-resolution timing with time.perf_counter()
- Performance statistics collection
- Timer management and cleanup
- Error performance tracking
- Configurable measurement retention

CACHING FEATURES:
- TTL-based cache expiration
- Thread-safe cache operations
- Cache statistics and monitoring
- Automatic cleanup of expired entries
- Configurable cache sizes

EVENT SYSTEM:
- Event handler registration and management
- Event emission with error handling
- Thread-safe event operations
- Handler cleanup and management
- Event listing and introspection

STATE MANAGEMENT:
- Thread-safe state operations
- State change notifications
- State validation and cleanup
- State history tracking
- Change handler registration

METRICS COLLECTION:
- Counter and gauge metrics
- Historical metrics tracking
- Metrics aggregation and statistics
- Configurable history retention
- Thread-safe metrics operations

USAGE EXAMPLES:

Performance Monitoring:
    from hydra_logger.core.mixins import PerformanceMixin
    from hydra_logger.core.base import BaseComponent
    
    class MyComponent(PerformanceMixin, BaseComponent):
        def process_data(self):
            self.start_timer("processing")
            # Processing logic...
            duration = self.stop_timer("processing")
            print(f"Processing took {duration:.3f}s")
        
        def get_performance_summary(self):
            return self.get_performance_metrics()

Caching Capabilities:
    from hydra_logger.core.mixins import CachingMixin
    from hydra_logger.core.base import BaseComponent
    
    class MyComponent(CachingMixin, BaseComponent):
        def __init__(self):
            super().__init__(cache_ttl=300)  # 5 minutes
        
        def get_data(self, key):
            cached = self.get_cached(key)
            if cached is not None:
                return cached
            
            # Expensive computation
            result = self.compute_data(key)
            self.set_cached(key, result)
            return result

Event Handling:
    from hydra_logger.core.mixins import EventMixin
    from hydra_logger.core.base import BaseComponent
    
    class MyComponent(EventMixin, BaseComponent):
        def __init__(self):
            super().__init__()
            self.on("data_processed", self.handle_data_processed)
        
        def process_data(self, data):
            # Process data...
            self.emit("data_processed", data, result)
        
        def handle_data_processed(self, data, result):
            print(f"Processed {len(data)} items")

State Management:
    from hydra_logger.core.mixins import StateMixin
    from hydra_logger.core.base import BaseComponent
    
    class MyComponent(StateMixin, BaseComponent):
        def __init__(self):
            super().__init__()
            self.on_state_change(self.handle_state_change)
        
        def update_status(self, status):
            self.set_state("status", status)
        
        def handle_state_change(self, key, old_value, new_value):
            print(f"State changed: {key} = {old_value} → {new_value}")

Metrics Collection:
    from hydra_logger.core.mixins import MetricsMixin
    from hydra_logger.core.base import BaseComponent
    
    class MyComponent(MetricsMixin, BaseComponent):
        def process_item(self, item):
            self.increment_metric("items_processed")
            self.record_metric_history("processing_time", time.time())
        
        def get_metrics_summary(self):
            return self.get_metrics_summary()
"""

from typing import Any, Dict, Optional, Callable
import time
import threading


class PerformanceMixin:
    """Mixin for adding performance monitoring capabilities."""
    
    def __init__(self, **kwargs):
        self._performance_metrics = {}
        self._performance_timers = {}
        self._performance_lock = threading.Lock()
    
    def start_timer(self, name: str) -> None:
        """Start a performance timer."""
        with self._performance_lock:
            self._performance_timers[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """Stop a performance timer and return duration."""
        with self._performance_lock:
            if name not in self._performance_timers:
                return 0.0
            
            start_time = self._performance_timers[name]
            duration = time.time() - start_time
            
            # Store metric
            if name not in self._performance_metrics:
                self._performance_metrics[name] = []
            self._performance_metrics[name].append(duration)
            
            # Keep only last 100 measurements
            if len(self._performance_metrics[name]) > 100:
                self._performance_metrics[name] = self._performance_metrics[name][-100:]
            
            del self._performance_timers[name]
            return duration
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._performance_lock:
            metrics = {}
            for name, measurements in self._performance_metrics.items():
                if measurements:
                    metrics[name] = {
                        'count': len(measurements),
                        'total': sum(measurements),
                        'average': sum(measurements) / len(measurements),
                        'min': min(measurements),
                        'max': max(measurements),
                        'latest': measurements[-1] if measurements else 0.0
                    }
            return metrics
    
    def clear_performance_metrics(self) -> None:
        """Clear all performance metrics."""
        with self._performance_lock:
            self._performance_metrics.clear()
            self._performance_timers.clear()


class CachingMixin:
    """Mixin for adding caching capabilities."""
    
    def __init__(self, **kwargs):
        self._cache = {}
        self._cache_ttl = kwargs.get('cache_ttl', 300)  # 5 minutes default
        self._cache_timestamps = {}
        self._cache_lock = threading.Lock()
    
    def get_cached(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        with self._cache_lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if key in self._cache_timestamps:
                if time.time() - self._cache_timestamps[key] > self._cache_ttl:
                    # Expired, remove from cache
                    del self._cache[key]
                    del self._cache_timestamps[key]
                    return None
            
            return self._cache[key]
    
    def set_cached(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache."""
        with self._cache_lock:
            self._cache[key] = value
            self._cache_timestamps[key] = time.time()
            if ttl is not None:
                # Override default TTL for this key
                self._cache_ttl = ttl
    
    def remove_cached(self, key: str) -> None:
        """Remove a value from cache."""
        with self._cache_lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]
    
    def clear_cache(self) -> None:
        """Clear all cached values."""
        with self._cache_lock:
            self._cache.clear()
            self._cache_timestamps.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._cache_lock:
            return {
                'size': len(self._cache),
                'keys': list(self._cache.keys()),
                'ttl': self._cache_ttl
            }


class EventMixin:
    """Mixin for adding event handling capabilities."""
    
    def __init__(self, **kwargs):
        self._event_handlers = {}
        self._event_lock = threading.Lock()
    
    def on(self, event_name: str, handler: Callable) -> None:
        """Register an event handler."""
        with self._event_lock:
            if event_name not in self._event_handlers:
                self._event_handlers[event_name] = []
            self._event_handlers[event_name].append(handler)
    
    def off(self, event_name: str, handler: Optional[Callable] = None) -> None:
        """Unregister an event handler."""
        with self._event_lock:
            if event_name not in self._event_handlers:
                return
            
            if handler is None:
                # Remove all handlers for this event
                del self._event_handlers[event_name]
            else:
                # Remove specific handler
                if handler in self._event_handlers[event_name]:
                    self._event_handlers[event_name].remove(handler)
                
                # Clean up empty handler lists
                if not self._event_handlers[event_name]:
                    del self._event_handlers[event_name]
    
    def emit(self, event_name: str, *args, **kwargs) -> None:
        """Emit an event to all registered handlers."""
        with self._event_lock:
            if event_name not in self._event_handlers:
                return
            
            # Copy handlers to avoid modification during iteration
            handlers = self._event_handlers[event_name].copy()
        
        # Call handlers outside of lock
        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                # Log error but don't stop other handlers
                print(f"Error in event handler for {event_name}: {e}")
    
    def get_event_handlers(self, event_name: str) -> list[Callable]:
        """Get all handlers for a specific event."""
        with self._event_lock:
            return self._event_handlers.get(event_name, []).copy()
    
    def list_events(self) -> list[str]:
        """List all registered event names."""
        with self._event_lock:
            return list(self._event_handlers.keys())


class StateMixin:
    """Mixin for adding state management capabilities."""
    
    def __init__(self, **kwargs):
        self._state = {}
        self._state_lock = threading.Lock()
        self._state_change_handlers = []
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a state value."""
        with self._state_lock:
            old_value = self._state.get(key)
            self._state[key] = value
            
            # Notify state change handlers
            if old_value != value:
                self._notify_state_change(key, old_value, value)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        with self._state_lock:
            return self._state.get(key, default)
    
    def has_state(self, key: str) -> bool:
        """Check if a state key exists."""
        with self._state_lock:
            return key in self._state
    
    def remove_state(self, key: str) -> None:
        """Remove a state key."""
        with self._state_lock:
            if key in self._state:
                old_value = self._state[key]
                del self._state[key]
                self._notify_state_change(key, old_value, None)
    
    def clear_state(self) -> None:
        """Clear all state."""
        with self._state_lock:
            old_state = self._state.copy()
            self._state.clear()
            
            # Notify for all removed keys
            for key, value in old_state.items():
                self._notify_state_change(key, value, None)
    
    def get_all_state(self) -> Dict[str, Any]:
        """Get all state values."""
        with self._state_lock:
            return self._state.copy()
    
    def on_state_change(self, handler: Callable) -> None:
        """Register a state change handler."""
        with self._state_lock:
            self._state_change_handlers.append(handler)
    
    def _notify_state_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify state change handlers."""
        handlers = self._state_change_handlers.copy()
        for handler in handlers:
            try:
                handler(key, old_value, new_value)
            except Exception as e:
                print(f"Error in state change handler: {e}")


class MetricsMixin:
    """Mixin for adding metrics collection capabilities."""
    
    def __init__(self, **kwargs):
        self._metrics = {}
        self._metrics_lock = threading.Lock()
        self._metrics_history = {}
        self._max_history = kwargs.get('max_history', 1000)
    
    def increment_metric(self, name: str, value: int = 1) -> None:
        """Increment a metric counter."""
        with self._metrics_lock:
            if name not in self._metrics:
                self._metrics[name] = 0
            self._metrics[name] += value
    
    def set_metric(self, name: str, value: Any) -> None:
        """Set a metric value."""
        with self._metrics_lock:
            self._metrics[name] = value
    
    def get_metric(self, name: str, default: Any = None) -> Any:
        """Get a metric value."""
        with self._metrics_lock:
            return self._metrics.get(name, default)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        with self._metrics_lock:
            return self._metrics.copy()
    
    def record_metric_history(self, name: str, value: Any) -> None:
        """Record a metric value in history."""
        with self._metrics_lock:
            if name not in self._metrics_history:
                self._metrics_history[name] = []
            
            self._metrics_history[name].append({
                'value': value,
                'timestamp': time.time()
            })
            
            # Keep only recent history
            if len(self._metrics_history[name]) > self._max_history:
                self._metrics_history[name] = self._metrics_history[name][-self._max_history:]
    
    def get_metric_history(self, name: str) -> list[Dict[str, Any]]:
        """Get metric history."""
        with self._metrics_lock:
            return self._metrics_history.get(name, []).copy()
    
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        with self._metrics_lock:
            self._metrics.clear()
            self._metrics_history.clear()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        with self._metrics_lock:
            summary = {
                'current': self._metrics.copy(),
                'history': {}
            }
            
            for name, history in self._metrics_history.items():
                if history:
                    values = [entry['value'] for entry in history if isinstance(entry['value'], (int, float))]
                    if values:
                        summary['history'][name] = {
                            'count': len(values),
                            'min': min(values),
                            'max': max(values),
                            'average': sum(values) / len(values),
                            'total': sum(values)
                        }
            
            return summary
