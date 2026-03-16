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
from pathlib import Path
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


def validate_result_paths(
    *, results: dict[str, Any], allowed_roots: list[Path]
) -> list[str]:
    """Validate that result paths remain confined to allowed benchmark roots."""
    violations: list[str] = []
    normalized_roots = [root.resolve() for root in allowed_roots]

    def _walk(node: Any, trail: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                next_trail = f"{trail}.{key}" if trail else key
                if isinstance(value, str) and (key.endswith("_path") or key == "path"):
                    try:
                        resolved = Path(value).resolve()
                    except Exception:
                        violations.append(f"{next_trail}: invalid path value {value!r}")
                        continue
                    if not any(resolved.is_relative_to(root) for root in normalized_roots):
                        violations.append(
                            f"{next_trail}: path escapes benchmark roots ({resolved})"
                        )
                _walk(value, next_trail)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                _walk(value, f"{trail}[{index}]")

    _walk(results, "")
    return violations


def detect_new_root_log_leaks(
    *,
    project_root: Path,
    preexisting_log_names: set[str],
) -> list[str]:
    """Detect newly created benchmark-like files under project root logs/."""
    logs_dir = project_root / "logs"
    if not logs_dir.exists():
        return []

    suspicious_tokens = (
        "benchmark",
        "perf_",
        "composite_logger_benchmark",
        "benchmark_async_file",
    )
    violations: list[str] = []
    for path in logs_dir.glob("*"):
        if not path.is_file():
            continue
        name = path.name
        if name in preexisting_log_names:
            continue
        if any(token in name for token in suspicious_tokens):
            violations.append(str(path.resolve()))
    return violations
