"""
Role: Lightweight benchmark schema compatibility checks.
Used By:
 - tests.benchmark
Depends On:
 - json
 - pathlib
 - typing
Notes:
 - Validates required keys and primitive types without external dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark.dev_logging import get_logger


SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "result_schema.json"
_logger = get_logger(__name__)


def load_result_schema() -> dict[str, Any]:
    """Load benchmark result JSON schema payload."""
    try:
        raw_schema = SCHEMA_PATH.read_text(encoding="utf-8")
        return json.loads(raw_schema)
    except FileNotFoundError as exc:
        _logger.exception("Benchmark schema file not found at %s", SCHEMA_PATH)
        raise FileNotFoundError(f"Benchmark schema file is missing: {SCHEMA_PATH}") from exc
    except json.JSONDecodeError as exc:
        _logger.exception("Benchmark schema file is invalid JSON: %s", SCHEMA_PATH)
        raise ValueError(f"Invalid benchmark schema JSON at {SCHEMA_PATH}") from exc
    except OSError as exc:
        _logger.exception("Benchmark schema file read failed at %s", SCHEMA_PATH)
        raise OSError(f"Could not read benchmark schema file: {SCHEMA_PATH}") from exc


def validate_against_schema(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """
    Validate payload against a subset of JSON-schema rules used in this project.

    Supported checks:
    - type
    - required
    - minimum (integer)
    - minLength (string)
    """
    violations: list[str] = []
    _validate_node(path="$", value=payload, schema=schema, violations=violations)
    return violations


def validate_legacy_compat_payload(payload: dict[str, Any]) -> list[str]:
    """
    Validate minimum compatibility shape for legacy benchmark artifacts.

    This keeps older historical benchmark result files useful for trend/drift
    analysis even when the strict schema adds new metadata requirements.
    """
    violations: list[str] = []
    if not isinstance(payload, dict):
        return ["$: expected object payload"]

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        violations.append("$.metadata: expected object")
    else:
        timestamp = metadata.get("timestamp")
        if not isinstance(timestamp, str) or not timestamp:
            violations.append("$.metadata.timestamp: expected non-empty string")
        profile = metadata.get("profile", "legacy_default")
        if not isinstance(profile, str) or not profile:
            violations.append("$.metadata.profile: expected non-empty string")

    results = payload.get("results")
    if not isinstance(results, dict):
        violations.append("$.results: expected object")
    return violations


def _validate_node(*, path: str, value: Any, schema: dict[str, Any], violations: list[str]) -> None:
    expected_type = schema.get("type")
    if expected_type is not None and not _is_type(value, expected_type):
        violations.append(f"{path}: expected type {expected_type!r}, got {type(value).__name__}")
        return

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            violations.append(f"{path}: string length {len(value)} < minLength {min_length}")

    if isinstance(value, int):
        minimum = schema.get("minimum")
        if isinstance(minimum, int) and value < minimum:
            violations.append(f"{path}: value {value} < minimum {minimum}")

    required = schema.get("required", [])
    if isinstance(required, list) and isinstance(value, dict):
        for key in required:
            if key not in value:
                violations.append(f"{path}: missing required key {key!r}")

    properties = schema.get("properties", {})
    if isinstance(properties, dict) and isinstance(value, dict):
        for key, prop_schema in properties.items():
            if key not in value:
                continue
            if isinstance(prop_schema, dict):
                _validate_node(
                    path=f"{path}.{key}",
                    value=value[key],
                    schema=prop_schema,
                    violations=violations,
                )


def _is_type(value: Any, schema_type: Any) -> bool:
    if isinstance(schema_type, list):
        return any(_is_type(value, item) for item in schema_type)
    mapping = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }
    python_type = mapping.get(schema_type)
    if python_type is None:
        return True
    # bool is a subclass of int; keep JSON integer semantics strict.
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, python_type)
