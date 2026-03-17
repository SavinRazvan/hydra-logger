"""
Role: Benchmark schema and baseline compatibility checks.
Used By:
 - Pytest benchmark schema validation.
Depends On:
 - benchmark
 - json
Notes:
 - Ensures benchmark_latest payload conforms to the schema contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import benchmark.schema_validation as schema_mod
from benchmark.schema_validation import (
    load_result_schema,
    validate_against_schema,
    validate_legacy_compat_payload,
)


def _load_latest_result_payload(project_root: Path) -> dict:
    """Load the newest benchmark result artifact when present."""
    results_dir = project_root / "benchmark" / "results"
    latest_path = results_dir / "benchmark_latest.json"
    if latest_path.exists():
        return json.loads(latest_path.read_text(encoding="utf-8"))

    # Fallback for clean environments where latest symlink/copy may not exist yet.
    timestamped = sorted(
        (
            path
            for path in results_dir.glob("benchmark_*.json")
            if path.name != "benchmark_latest.json"
        ),
        reverse=True,
    )
    if timestamped:
        return json.loads(timestamped[0].read_text(encoding="utf-8"))

    pytest.skip("No benchmark result artifact found under benchmark/results.")


def test_benchmark_latest_matches_result_schema() -> None:
    project_root = Path(__file__).resolve().parents[2]
    payload = _load_latest_result_payload(project_root)
    schema = load_result_schema()

    violations = validate_against_schema(payload, schema)
    assert violations == []


def test_seeded_baseline_artifact_has_required_shape() -> None:
    project_root = Path(__file__).resolve().parents[2]
    baseline_path = project_root / "benchmark" / "baselines" / "ci_smoke_baseline_v1.json"
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))

    assert payload["baseline_name"] == "ci_smoke_baseline_v1"
    assert payload["metadata"]["profile"] == "ci_smoke"
    assert "sync_logger.individual_messages_per_second" in payload["metrics"]


def test_legacy_result_artifact_passes_compat_validation() -> None:
    # Legacy payloads predate newer strict metadata/result requirements but still
    # keep minimum shape needed for compatibility workflows.
    payload = {
        "metadata": {
            "timestamp": "2025-11-23T22:07:27Z",
            "profile": "legacy_ci_smoke",
        },
        "results": {},
    }

    strict_schema = load_result_schema()
    strict_violations = validate_against_schema(payload, strict_schema)
    assert strict_violations  # legacy artifact is expected to miss newer strict fields

    compat_violations = validate_legacy_compat_payload(payload)
    assert compat_violations == []


def test_legacy_compat_validation_reports_invalid_shapes() -> None:
    assert "$: expected object payload" in validate_legacy_compat_payload([])  # type: ignore[arg-type]

    violations = validate_legacy_compat_payload({"metadata": "bad", "results": []})
    assert "$.metadata: expected object" in violations
    assert "$.results: expected object" in violations

    violations = validate_legacy_compat_payload({"metadata": {}, "results": {}})
    assert "$.metadata.timestamp: expected non-empty string" in violations

    violations = validate_legacy_compat_payload(
        {"metadata": {"timestamp": "2026-03-16", "profile": ""}, "results": {}}
    )
    assert "$.metadata.profile: expected non-empty string" in violations


def test_load_result_schema_raises_for_missing_schema(monkeypatch, tmp_path) -> None:
    missing_schema = tmp_path / "missing_schema.json"
    monkeypatch.setattr(schema_mod, "SCHEMA_PATH", missing_schema)

    with pytest.raises(FileNotFoundError):
        load_result_schema()


def test_load_result_schema_raises_for_invalid_json(monkeypatch, tmp_path) -> None:
    bad_schema = tmp_path / "bad_schema.json"
    bad_schema.write_text("{ bad json", encoding="utf-8")
    monkeypatch.setattr(schema_mod, "SCHEMA_PATH", bad_schema)

    with pytest.raises(ValueError, match="Invalid benchmark schema JSON"):
        load_result_schema()
