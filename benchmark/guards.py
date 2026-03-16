"""
Role: Benchmark isolation and fallback guard helpers.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - copy
 - types
 - typing
Notes:
 - Redirects benchmark writes into benchmark workspace paths.
"""

from __future__ import annotations

import copy
from types import SimpleNamespace
from typing import Any

from hydra_logger.config.models import LoggingConfig


def rebase_file_destinations_to_benchmark_logs(
    *,
    config: LoggingConfig,
    config_name: str,
    build_log_path: Any,
) -> LoggingConfig:
    """Copy config and redirect file destinations into benchmark/bench_logs."""
    rebased = copy.deepcopy(config)
    for layer_name, layer in rebased.layers.items():
        for index, destination in enumerate(layer.destinations):
            destination_type = str(getattr(destination, "type", "")).lower()
            if "file" not in destination_type and "jsonl" not in destination_type:
                continue
            destination.path = build_log_path(f"config_{config_name}_{layer_name}_{index}")
    return rebased


def disable_direct_io_if_available(logger: Any) -> None:
    """Force-disable composite direct-I/O fallback when logger supports it."""
    if hasattr(logger, "_use_direct_io"):
        try:
            logger._use_direct_io = False
        except Exception:
            pass


def ensure_composite_file_target(*, logger: Any, prefix: str, build_log_path: Any) -> None:
    """Attach a file-path shim so composite fallback writes into benchmark logs."""
    components = getattr(logger, "components", None)
    if not isinstance(components, list):
        return

    for component in components:
        if getattr(component, "file_path", None):
            return

    components.append(SimpleNamespace(file_path=build_log_path(prefix)))
