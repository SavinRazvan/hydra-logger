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
import os
from pathlib import Path
import shutil
from typing import Any

from benchmark.dev_logging import get_logger


_logger = get_logger(__name__)
_DETAILED_REPORT_ENV = "HYDRA_BENCHMARK_VERBOSE_REPORTS"

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
    write_markdown_reports: bool = True,
) -> Path:
    """Write timestamped and latest benchmark result artifacts."""
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = str(output_payload["metadata"]["timestamp"])
        output_file = results_dir / f"benchmark_{timestamp}.json"
        output_file.write_text(json.dumps(output_payload, indent=2), encoding="utf-8")

        latest_file = results_dir / "benchmark_latest.json"
        shutil.copy2(output_file, latest_file)
        _write_auxiliary_reports(
            output_payload=output_payload,
            results_dir=results_dir,
            timestamp=timestamp,
            write_markdown_reports=write_markdown_reports,
        )
        return output_file
    except KeyError as exc:
        _logger.exception("Benchmark output payload is missing required metadata fields")
        raise ValueError(
            "Invalid benchmark output payload: missing metadata.timestamp"
        ) from exc
    except OSError as exc:
        _logger.exception("Benchmark artifact persistence failed in %s", results_dir)
        raise OSError(f"Failed to persist benchmark artifacts in {results_dir}") from exc


def _write_auxiliary_reports(
    *,
    output_payload: dict[str, Any],
    results_dir: Path,
    timestamp: str,
    write_markdown_reports: bool,
) -> None:
    """Persist benchmark summary and reliability reports beside JSON artifacts."""
    if not write_markdown_reports:
        for prefix in ("summary", "drift", "invariants", "leaks"):
            _conditionally_write_or_clear_report(
                should_write=False,
                results_dir=results_dir,
                timestamp=timestamp,
                prefix=prefix,
                body="",
            )
        return

    results = output_payload.get("results", {})
    metadata = output_payload.get("metadata", {})
    reliability = results.get("reliability_guards", {}) if isinstance(results, dict) else {}
    drift = results.get("drift_policy", {}) if isinstance(results, dict) else {}

    profile = str(metadata.get("profile", "legacy_default"))
    summary_lines = [
        f"# Benchmark Summary ({timestamp})",
        "",
        f"- Profile: {profile}",
        f"- Platform: {metadata.get('platform', 'unknown')}",
        f"- Python: {metadata.get('python_version', 'unknown')}",
        f"- Commit: {metadata.get('git_commit_sha', 'unknown')}",
        f"- Reliability Status: {reliability.get('status', 'unknown') if isinstance(reliability, dict) else 'unknown'}",
        f"- Reliability Strict Mode: {reliability.get('strict_mode', False) if isinstance(reliability, dict) else False}",
        f"- Drift Status: {drift.get('status', 'unknown') if isinstance(drift, dict) else 'unknown'}",
    ]

    invariant_violations = []
    path_violations = []
    leak_violations = []
    if isinstance(reliability, dict):
        invariant_violations = reliability.get("invariant_violations", []) or []
        path_violations = reliability.get("path_violations", []) or []
        leak_violations = reliability.get("leak_violations", []) or []
        file_io_violations = reliability.get("file_io_violations", []) or []
        sample_duration_violations = reliability.get("sample_duration_violations", []) or []
        summary_lines.append(f"- File I/O violations: {len(file_io_violations)}")
        summary_lines.append(f"- Sample duration violations: {len(sample_duration_violations)}")

    _write_report_files(
        results_dir=results_dir,
        timestamp=timestamp,
        prefix="summary",
        body="\n".join(summary_lines) + "\n",
    )
    drift_status = (
        str(drift.get("status", "unknown")) if isinstance(drift, dict) else "unknown"
    )
    drift_items = _flatten_metric_statuses(
        drift.get("metrics", {}) if isinstance(drift, dict) else {}
    )
    invariant_status = "failed" if invariant_violations else "passed"
    invariant_items = [str(item) for item in invariant_violations]
    leak_status = "failed" if leak_violations or path_violations else "passed"
    leak_items = [str(item) for item in [*path_violations, *leak_violations]]

    verbose_reports = str(os.getenv(_DETAILED_REPORT_ENV, "")).strip().lower() in {
        "1",
        "true",
        "yes",
    }
    report_plan = {
        "drift": verbose_reports
        or drift_status not in {"disabled", "passed"}
        or len(drift_items) > 0,
        "invariants": verbose_reports
        or invariant_status != "passed"
        or len(invariant_items) > 0,
        "leaks": verbose_reports or leak_status != "passed" or len(leak_items) > 0,
    }

    _conditionally_write_or_clear_report(
        should_write=report_plan["drift"],
        results_dir=results_dir,
        timestamp=timestamp,
        prefix="drift",
        body=_report_section(
            title="Drift Verdict",
            status=drift_status,
            items=drift_items,
        ),
    )
    _conditionally_write_or_clear_report(
        should_write=report_plan["invariants"],
        results_dir=results_dir,
        timestamp=timestamp,
        prefix="invariants",
        body=_report_section(
            title="Invariant Report",
            status=invariant_status,
            items=invariant_items,
        ),
    )
    _conditionally_write_or_clear_report(
        should_write=report_plan["leaks"],
        results_dir=results_dir,
        timestamp=timestamp,
        prefix="leaks",
        body=_report_section(
            title="Leak Guard Report",
            status=leak_status,
            items=leak_items,
        ),
    )


def _flatten_metric_statuses(metrics: Any) -> list[str]:
    """Return compact metric status lines from drift report payload."""
    if not isinstance(metrics, dict):
        return []
    lines: list[str] = []
    for key, value in metrics.items():
        if isinstance(value, dict):
            status = value.get("status", "unknown")
            lines.append(f"{key}: {status}")
        else:
            lines.append(f"{key}: unknown")
    return lines


def _report_section(*, title: str, status: str, items: list[str]) -> str:
    """Build a simple markdown section for report artifacts."""
    lines = [f"# {title}", "", f"- Status: {status}"]
    if items:
        lines.append("")
        lines.append("## Details")
        lines.extend([f"- {item}" for item in items])
    return "\n".join(lines) + "\n"


def _write_report_files(
    *,
    results_dir: Path,
    timestamp: str,
    prefix: str,
    body: str,
) -> None:
    """Write timestamped and latest markdown report files."""
    try:
        timestamped = results_dir / f"benchmark_{timestamp}_{prefix}.md"
        latest = results_dir / f"benchmark_latest_{prefix}.md"
        timestamped.write_text(body, encoding="utf-8")
        shutil.copy2(timestamped, latest)
    except OSError as exc:
        _logger.exception(
            "Benchmark report persistence failed for prefix=%s timestamp=%s",
            prefix,
            timestamp,
        )
        raise OSError(
            f"Failed to persist benchmark report files for prefix '{prefix}'"
        ) from exc


def _conditionally_write_or_clear_report(
    *,
    should_write: bool,
    results_dir: Path,
    timestamp: str,
    prefix: str,
    body: str,
) -> None:
    """Write report only when useful; clear stale latest otherwise."""
    timestamped = results_dir / f"benchmark_{timestamp}_{prefix}.md"
    latest = results_dir / f"benchmark_latest_{prefix}.md"
    if should_write:
        _write_report_files(
            results_dir=results_dir,
            timestamp=timestamp,
            prefix=prefix,
            body=body,
        )
        return
    try:
        if timestamped.exists():
            timestamped.unlink()
        if latest.exists():
            latest.unlink()
    except OSError:
        _logger.exception("Failed clearing suppressed benchmark report prefix=%s", prefix)
