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

from benchmark.schema_validation import load_result_schema, validate_against_schema


def test_benchmark_latest_matches_result_schema() -> None:
    project_root = Path(__file__).resolve().parents[2]
    latest_path = project_root / "benchmark" / "results" / "benchmark_latest.json"
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
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
