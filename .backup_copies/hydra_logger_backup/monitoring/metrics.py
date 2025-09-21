"""
Metrics Collection Component for Hydra-Logger

This module provides comprehensive metrics collection with Prometheus-style
metrics including counters, gauges, histograms, and summaries. It supports
both synchronous and background processing for efficient metrics collection.

FEATURES:
- Prometheus-style metrics (counters, gauges, histograms, summaries)
- Background and synchronous processing modes
- Metric history and time-series data
- Prometheus format export
- Configurable batch processing

USAGE:
    from hydra_logger.monitoring import MetricsCollector
    
    # Create metrics collector
    collector = MetricsCollector(
        enabled=True,
        max_metrics=10000,
        use_background_processing=True
    )
    
    # Start monitoring
    collector.start_monitoring()
    
    # Record metrics
    collector.inc_counter("requests_total", value=1, labels={"method": "GET"})
    collector.set_gauge("memory_usage", value=75.5, labels={"type": "heap"})
    collector.observe_histogram("response_time", value=0.25)
    
    # Export Prometheus format
    prometheus_data = collector.export_prometheus()
"""

import time
import threading
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict, deque
from ..interfaces.monitor import MonitorInterface


class MetricsCollector(MonitorInterface):
    """Real metrics collection component with Prometheus-style metrics."""
    
    def __init__(self, enabled: bool = True, max_metrics: int = 10000, 
                 use_background_processing: bool = True, batch_size: int = 100):
        self._enabled = enabled
        self._initialized = True
        self._monitoring = False
        self._max_metrics = max_metrics
        
        # Background processing configuration
        self._use_background_processing = use_background_processing and enabled
        self._batch_size = batch_size
        
        # Metric storage
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(list)
        self._summaries = defaultdict(list)
        
        # Metric metadata
        self._metric_metadata = {}
        self._metric_labels = defaultdict(dict)
        
        # Metric history for time-series data
        self._metric_history = defaultdict(lambda: deque(maxlen=1000))
        
        # Background processing queue
        self._metric_queue = []
        self._queue_lock = threading.Lock()
        
        # Threading
        self._lock = threading.Lock()
        self._collection_thread = None
        self._background_thread = None
        self._stop_event = threading.Event()
        self._collection_interval = 10.0  # seconds
        
        # Statistics
        self._total_metrics = 0
        self._collection_count = 0
        self._last_collection = 0.0
        self._background_metrics_processed = 0
        self._synchronous_metrics_processed = 0
    
    def start_monitoring(self) -> bool:
        """Start metrics collection."""
        if not self._enabled or self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = True
                self._stop_event.clear()
                self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
                self._collection_thread.start()
                
                # Start background processing if enabled
                if self._use_background_processing:
                    self._background_thread = threading.Thread(target=self._background_processor, daemon=True)
                    self._background_thread.start()
                
                return True
        except Exception:
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop metrics collection."""
        if not self._monitoring:
            return False
        
        try:
            with self._lock:
                self._monitoring = False
                self._stop_event.set()
                
                if self._collection_thread and self._collection_thread.is_alive():
                    self._collection_thread.join(timeout=5.0)
                
                if self._background_thread and self._background_thread.is_alive():
                    self._background_thread.join(timeout=5.0)
                
                return True
        except Exception:
            return False
    
    def is_monitoring(self) -> bool:
        """Check if monitoring is active."""
        return self._monitoring
    
    def _collection_loop(self) -> None:
        """Main metrics collection loop."""
        while not self._stop_event.is_set():
            try:
                self._collect_metrics()
                time.sleep(self._collection_interval)
            except Exception:
                # Continue collection even if individual operations fail
                pass
    
    def _background_processor(self) -> None:
        """Background processor for queued metrics."""
        while not self._stop_event.is_set():
            try:
                # Process queued metrics in batches
                self._process_metric_queue()
                time.sleep(0.1)  # Short sleep to prevent busy waiting
            except Exception:
                # Continue processing even if individual operations fail
                pass
    
    def _process_metric_queue(self) -> None:
        """Process queued metrics in batches."""
        with self._queue_lock:
            if not self._metric_queue:
                return
            
            # Process batch of metrics
            batch = self._metric_queue[:self._batch_size]
            self._metric_queue = self._metric_queue[self._batch_size:]
        
        if batch:
            # Process each metric in the batch
            for metric_data in batch:
                try:
                    self._process_queued_metric(metric_data)
                    self._background_metrics_processed += 1
                except Exception:
                    # Skip failed metrics
                    pass
    
    def _process_queued_metric(self, metric_data: Dict[str, Any]) -> None:
        """Process a single queued metric."""
        metric_type = metric_data.get('type')
        name = metric_data.get('name')
        value = metric_data.get('value')
        labels = metric_data.get('labels')
        
        if metric_type == 'counter':
            self._inc_counter_sync(name, value, labels)
        elif metric_type == 'gauge':
            self._set_gauge_sync(name, value, labels)
        elif metric_type == 'histogram':
            self._observe_histogram_sync(name, value, labels)
        elif metric_type == 'summary':
            self._observe_summary_sync(name, value, labels)
    
    def _collect_metrics(self) -> None:
        """Collect and process metrics."""
        if not self._enabled:
            return
        
        current_time = time.time()
        self._collection_count += 1
        
        try:
            # Collect system metrics
            self._collect_system_metrics()
            
            # Process metric history
            self._process_metric_history(current_time)
            
            self._last_collection = current_time
            
        except Exception:
            # Log error but continue
            pass
    
    def _collect_system_metrics(self) -> None:
        """Collect basic system metrics."""
        try:
            import psutil
            
            # CPU metrics
            self.inc_counter("system_cpu_usage", value=psutil.cpu_percent())
            self.set_gauge("system_cpu_count", value=psutil.cpu_count())
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.set_gauge("system_memory_total", value=memory.total)
            self.set_gauge("system_memory_used", value=memory.used)
            self.set_gauge("system_memory_free", value=memory.free)
            self.set_gauge("system_memory_percent", value=memory.percent)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.set_gauge("system_disk_total", value=disk.total)
            self.set_gauge("system_disk_used", value=disk.used)
            self.set_gauge("system_disk_free", value=disk.free)
            self.set_gauge("system_disk_percent", value=disk.percent)
            
        except ImportError:
            # psutil not available, skip system metrics
            pass
    
    def _process_metric_history(self, timestamp: float) -> None:
        """Process and clean up metric history."""
        # Remove old metrics (older than 24 hours)
        cutoff_time = timestamp - (24 * 3600)
        
        for metric_name, history in self._metric_history.items():
            # Remove old entries
            while history and history[0]["timestamp"] < cutoff_time:
                history.popleft()
    
    def inc_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None, 
                   use_background: bool = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Metric labels
            use_background: Whether to use background processing
        """
        if not self._enabled:
            return
        
        # Determine if we should use background processing
        should_use_background = (
            use_background if use_background is not None 
            else self._use_background_processing
        )
        
        if should_use_background:
            self._queue_metric({
                'type': 'counter',
                'name': name,
                'value': value,
                'labels': labels
            })
        else:
            self._inc_counter_sync(name, value, labels)
    
    def _inc_counter_sync(self, name: str, value: int, labels: Optional[Dict[str, str]] = None) -> None:
        """Synchronous counter increment."""
        with self._lock:
            metric_key = self._get_metric_key(name, labels)
            self._counters[metric_key] += value
            self._total_metrics += 1
            self._synchronous_metrics_processed += 1
            
            # Store metric metadata
            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    "type": "counter",
                    "help": f"Counter metric: {name}",
                    "created": time.time()
                }
            
            # Store labels
            if labels:
                self._metric_labels[metric_key] = labels.copy()
    
    def _queue_metric(self, metric_data: Dict[str, Any]) -> None:
        """Queue a metric for background processing."""
        with self._queue_lock:
            self._metric_queue.append(metric_data)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None, 
                 use_background: bool = None) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Metric labels
            use_background: Whether to use background processing
        """
        if not self._enabled:
            return
        
        # Determine if we should use background processing
        should_use_background = (
            use_background if use_background is not None 
            else self._use_background_processing
        )
        
        if should_use_background:
            self._queue_metric({
                'type': 'gauge',
                'name': name,
                'value': value,
                'labels': labels
            })
        else:
            self._set_gauge_sync(name, value, labels)
    
    def _set_gauge_sync(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Synchronous gauge setting."""
        with self._lock:
            metric_key = self._get_metric_key(name, labels)
            self._gauges[metric_key] = value
            self._total_metrics += 1
            self._synchronous_metrics_processed += 1
            
            # Store metric metadata
            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    "type": "gauge",
                    "help": f"Gauge metric: {name}",
                    "created": time.time()
                }
            
            # Store labels
            if labels:
                self._metric_labels[metric_key] = labels.copy()
            
            # Add to history for time-series
            self._metric_history[metric_key].append({
                "timestamp": time.time(),
                "value": value
            })
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Observe a value for histogram metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels
        """
        if not self._enabled:
            return
        
        with self._lock:
            metric_key = self._get_metric_key(name, labels)
            self._histograms[metric_key].append(value)
            self._total_metrics += 1
            
            # Store metric metadata
            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    "type": "histogram",
                    "help": f"Histogram metric: {name}",
                    "created": time.time()
                }
            
            # Store labels
            if labels:
                self._metric_labels[metric_key] = labels.copy()
            
            # Limit histogram size
            if len(self._histograms[metric_key]) > 1000:
                self._histograms[metric_key] = self._histograms[metric_key][-1000:]
    
    def observe_summary(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Observe a value for summary metric.
        
        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels
        """
        if not self._enabled:
            return
        
        with self._lock:
            metric_key = self._get_metric_key(name, labels)
            self._summaries[metric_key].append(value)
            self._total_metrics += 1
            
            # Store metric metadata
            if name not in self._metric_metadata:
                self._metric_metadata[name] = {
                    "type": "summary",
                    "help": f"Summary metric: {name}",
                    "created": time.time()
                }
            
            # Store labels
            if labels:
                self._metric_labels[metric_key] = labels.copy()
            
            # Limit summary size
            if len(self._summaries[metric_key]) > 1000:
                self._summaries[metric_key] = self._summaries[metric_key][-1000:]
    
    def _get_metric_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Generate metric key with labels."""
        if not labels:
            return name
        
        # Sort labels for consistent key generation
        sorted_labels = sorted(labels.items())
        label_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: self._get_histogram_stats(v) for k, v in self._histograms.items()},
                "summaries": {k: self._get_summary_stats(v) for k, v in self._summaries.items()},
                "metadata": dict(self._metric_metadata),
                "labels": dict(self._metric_labels)
            }
    
    def _get_histogram_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate histogram statistics."""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "median": sorted_values[count // 2] if count % 2 == 1 else (sorted_values[count // 2 - 1] + sorted_values[count // 2]) / 2,
            "p50": sorted_values[int(count * 0.5)],
            "p90": sorted_values[int(count * 0.9)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)]
        }
    
    def _get_summary_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate summary statistics."""
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(values)
        
        return {
            "count": count,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "p50": sorted_values[int(count * 0.5)],
            "p90": sorted_values[int(count * 0.9)],
            "p95": sorted_values[int(count * 0.95)],
            "p99": sorted_values[int(count * 0.99)]
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()
            self._metric_history.clear()
            self._total_metrics = 0
            self._collection_count = 0
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        if not self._enabled:
            return ""
        
        lines = []
        
        with self._lock:
            # Export counters
            for key, value in self._counters.items():
                metadata = self._get_metadata_from_key(key)
                if metadata:
                    lines.append(f"# HELP {metadata['name']} {metadata['help']}")
                    lines.append(f"# TYPE {metadata['name']} {metadata['type']}")
                
                labels = self._metric_labels.get(key, {})
                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                    lines.append(f'{metadata["name"] if metadata else key}{{{label_str}}} {value}')
                else:
                    lines.append(f"{metadata['name'] if metadata else key} {value}")
            
            # Export gauges
            for key, value in self._gauges.items():
                metadata = self._get_metadata_from_key(key)
                if metadata:
                    lines.append(f"# HELP {metadata['name']} {metadata['help']}")
                    lines.append(f"# TYPE {metadata['name']} {metadata['type']}")
                
                labels = self._metric_labels.get(key, {})
                if labels:
                    label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                    lines.append(f'{metadata["name"] if metadata else key}{{{label_str}}} {value}')
                else:
                    lines.append(f"{metadata['name'] if metadata else key} {value}")
            
            # Export histograms
            for key, stats in self._histograms.items():
                metadata = self._get_metadata_from_key(key)
                if metadata:
                    lines.append(f"# HELP {metadata['name']} {metadata['help']}")
                    lines.append(f"# TYPE {metadata['name']} {metadata['type']}")
                
                labels = self._metric_labels.get(key, {})
                label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                
                for stat_name, stat_value in stats.items():
                    if isinstance(stat_value, (int, float)):
                        metric_name = f"{metadata['name'] if metadata else key}_{stat_name}"
                        lines.append(f'{metric_name}{{{label_str}}} {stat_value}')
            
            # Export summaries
            for key, stats in self._summaries.items():
                metadata = self._get_metadata_from_key(key)
                if metadata:
                    lines.append(f"# HELP {metadata['name']} {metadata['help']}")
                    lines.append(f"# TYPE {metadata['name']} {metadata['type']}")
                
                labels = self._metric_labels.get(key, {})
                label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                
                for stat_name, stat_value in stats.items():
                    if isinstance(stat_value, (int, float)):
                        metric_name = f"{metadata['name'] if metadata else key}_{stat_name}"
                        lines.append(f'{metric_name}{{{label_str}}} {stat_value}')
        
        return "\n".join(lines)
    
    def _get_metadata_from_key(self, key: str) -> Optional[Dict[str, str]]:
        """Extract metadata from metric key."""
        # Remove labels from key to get base name
        base_name = key.split('{')[0] if '{' in key else key
        
        for name, metadata in self._metric_metadata.items():
            if name == base_name:
                return metadata
        return None
    
    def get_metric_history(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metric history for time-series analysis."""
        if not self._enabled:
            return []
        
        cutoff_time = time.time() - (hours * 3600)
        history = []
        
        with self._lock:
            for key, metric_history in self._metric_history.items():
                if metric_name in key:
                    recent_history = [
                        entry for entry in metric_history
                        if entry["timestamp"] > cutoff_time
                    ]
                    history.extend(recent_history)
        
        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])
        return history
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics collection summary."""
        with self._queue_lock:
            queue_size = len(self._metric_queue)
        
        return {
            "total_metrics": self._total_metrics,
            "collection_count": self._collection_count,
            "last_collection": self._last_collection,
            "monitoring": self._monitoring,
            "enabled": self._enabled,
            "background_processing": self._use_background_processing,
            "synchronous_metrics": self._synchronous_metrics_processed,
            "background_metrics": self._background_metrics_processed,
            "queue_size": queue_size,
            "metric_types": {
                "counters": len(self._counters),
                "gauges": len(self._gauges),
                "histograms": len(self._histograms),
                "summaries": len(self._summaries)
            }
        }
    
    def is_healthy(self) -> bool:
        """Check if the metrics collector is healthy."""
        return self._enabled and self._initialized and not self._stop_event.is_set()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status of the metrics collector."""
        return {
            "healthy": self.is_healthy(),
            "enabled": self._enabled,
            "initialized": self._initialized,
            "monitoring": self._monitoring,
            "collection_thread_alive": self._collection_thread.is_alive() if self._collection_thread else False,
            "total_metrics": self._total_metrics,
            "collection_count": self._collection_count
        }
