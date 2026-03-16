"""
Role: Reusable benchmark workload generators.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - typing
Notes:
 - Keeps scenario message generation patterns centrally defined.
"""

from __future__ import annotations

from typing import Any


def sync_message(i: int) -> str:
    patterns = [
        f"Processing request {i} for user_id=12345",
        f"Database query completed in {i*0.001:.3f}s, rows={i%100}",
        f"API endpoint /api/v1/users called, response_code=200, duration={i}ms",
    ]
    return patterns[i % len(patterns)]


def async_message(i: int) -> str:
    patterns = [
        f"Async task {i} completed: processed {i*10} items",
        f"WebSocket message received: channel='notifications', size={i*50}B",
        f"Event loop processing: {i} pending tasks, queue_size={i%50}",
    ]
    return patterns[i % len(patterns)]


def composite_message(i: int) -> str:
    patterns = [
        f"Composite logger: Processing transaction {i}, amount=${i*10.50:.2f}",
        f"Multi-handler log: User action 'view_profile' by user_id={i}",
        f"Composite output: API rate limit check, remaining={1000-i}",
    ]
    return patterns[i % len(patterns)]


def build_batch_messages(batch_size: int, message_factory: Any) -> list[tuple[str, str, dict[str, Any]]]:
    return [("INFO", message_factory(i), {}) for i in range(batch_size)]
