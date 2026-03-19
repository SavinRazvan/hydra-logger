"""
Role: Lightweight SLI counters for SLO dashboards and release gates.
Used By:
 - Handlers and loggers that need cheap operational counters.
Depends On:
 - threading
 - time
 - typing
Notes:
 - Counters are process-local; wire exporters in application code as needed.
"""

import threading
import time
from dataclasses import dataclass
from typing import Dict, List

_lock = threading.Lock()


@dataclass
class _HistogramSample:
    """Single latency observation."""

    name: str
    value_seconds: float
    timestamp: float


_dropped_logs = 0
_handler_errors = 0
_queue_saturation_events = 0
_flush_latency_samples: List[_HistogramSample] = []


def reset_metrics() -> None:
    """Reset all counters (intended for tests)."""
    global _dropped_logs, _handler_errors, _queue_saturation_events
    with _lock:
        _dropped_logs = 0
        _handler_errors = 0
        _queue_saturation_events = 0
        _flush_latency_samples.clear()


def record_dropped_log(reason: str = "unspecified") -> None:
    """Increment dropped-log SLI (reason reserved for structured export)."""
    global _dropped_logs
    with _lock:
        _dropped_logs += 1
    _ = reason


def record_handler_error(handler_name: str = "unspecified") -> None:
    """Increment handler failure SLI."""
    global _handler_errors
    with _lock:
        _handler_errors += 1
    _ = handler_name


def record_queue_saturation(component: str = "unspecified") -> None:
    """Increment queue saturation / overflow SLI."""
    global _queue_saturation_events
    with _lock:
        _queue_saturation_events += 1
    _ = component


def record_flush_latency(name: str, seconds: float) -> None:
    """Append a flush latency observation (trimmed in snapshot)."""
    with _lock:
        _flush_latency_samples.append(
            _HistogramSample(
                name=name,
                value_seconds=seconds,
                timestamp=time.time(),
            )
        )
        if len(_flush_latency_samples) > 10_000:
            del _flush_latency_samples[:-5000]


def snapshot() -> Dict[str, object]:
    """Return a point-in-time copy of all SLI counters."""
    with _lock:
        return {
            "dropped_logs": _dropped_logs,
            "handler_errors": _handler_errors,
            "queue_saturation_events": _queue_saturation_events,
            "flush_latency_recent": [
                {"name": s.name, "value_seconds": s.value_seconds, "ts": s.timestamp}
                for s in _flush_latency_samples[-200:]
            ],
        }


def percentile(sorted_values: List[float], p: float) -> float:
    """Simple percentile helper for offline SLO evaluation."""
    if not sorted_values:
        return 0.0
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def flush_latency_percentiles() -> Dict[str, float]:
    """Compute p95/p99 for recent flush samples (per process)."""
    with _lock:
        values = sorted(s.value_seconds for s in _flush_latency_samples)
    if not values:
        return {"p95": 0.0, "p99": 0.0, "count": 0.0}
    return {
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
        "count": float(len(values)),
    }
