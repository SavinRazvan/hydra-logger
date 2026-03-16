"""
Role: Benchmark profile loading and defaults.
Used By:
 - benchmark.performance_benchmark
Depends On:
 - json
 - pathlib
Notes:
 - Keeps tier profile selection explicit and reproducible.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROFILE_DIR = Path(__file__).resolve().parent / "profiles"


def load_profile(profile_name: str | None) -> dict[str, Any]:
    """Load a benchmark profile by name from benchmark/profiles."""
    if not profile_name:
        return {}
    profile_file = PROFILE_DIR / f"{profile_name}.json"
    if not profile_file.exists():
        raise ValueError(f"Unknown benchmark profile '{profile_name}' ({profile_file})")
    payload = json.loads(profile_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid profile format for {profile_file}")
    return payload
