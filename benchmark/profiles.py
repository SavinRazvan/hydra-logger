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

from benchmark.dev_logging import get_logger


PROFILE_DIR = Path(__file__).resolve().parent / "profiles"
_logger = get_logger(__name__)


def load_profile(profile_name: str | None) -> dict[str, Any]:
    """Load a benchmark profile by name from benchmark/profiles."""
    if not profile_name:
        return {}
    profile_file = PROFILE_DIR / f"{profile_name}.json"
    if not profile_file.exists():
        _logger.error("Unknown benchmark profile requested: %s", profile_name)
        raise ValueError(f"Unknown benchmark profile '{profile_name}' ({profile_file})")
    try:
        payload = json.loads(profile_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _logger.exception("Invalid benchmark profile JSON in %s", profile_file)
        raise ValueError(f"Invalid benchmark profile JSON: {profile_file}") from exc
    except OSError as exc:
        _logger.exception("Could not read benchmark profile file %s", profile_file)
        raise OSError(f"Could not read benchmark profile file: {profile_file}") from exc
    if not isinstance(payload, dict):
        _logger.error("Benchmark profile payload is not an object: %s", profile_file)
        raise ValueError(f"Invalid profile format for {profile_file}")
    return payload
