"""
Role: Benchmark result serialization and persistence helpers.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - json
 - pathlib
 - shutil
 - typing
Notes:
 - Centralizes output payload shaping for compatibility and reuse.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import shutil
from typing import Any


def make_serializable(obj: Any) -> Any:
    """Recursively convert values to JSON-serializable forms."""
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    if hasattr(obj, "__dict__"):
        return str(obj)
    return str(obj)


def build_output_payload(
    *,
    results: dict[str, Any],
    profile_name: str | None,
    test_config: dict[str, Any],
    python_version: str,
    platform_name: str,
    git_commit_sha: str,
    machine: str,
    cpu_count: int,
    disk_mode: str,
    payload_profile: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Build a benchmark artifact payload with metadata and serialized results."""
    resolved_timestamp = timestamp or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return {
        "metadata": {
            "timestamp": resolved_timestamp,
            "profile": profile_name or "legacy_default",
            "test_config": test_config,
            "python_version": python_version,
            "platform": platform_name,
            "git_commit_sha": git_commit_sha,
            "machine": machine,
            "cpu_count": cpu_count,
            "disk_mode": disk_mode,
            "payload_profile": payload_profile,
        },
        "results": make_serializable(results),
    }


def write_results_artifacts(
    *,
    output_payload: dict[str, Any],
    results_dir: Path,
) -> Path:
    """Write timestamped and latest benchmark result artifacts."""
    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = str(output_payload["metadata"]["timestamp"])
    output_file = results_dir / f"benchmark_{timestamp}.json"
    output_file.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")

    latest_file = results_dir / "benchmark_latest.json"
    shutil.copy2(output_file, latest_file)
    return output_file
