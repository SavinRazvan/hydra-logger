"""
Role: Unit tests for extracted benchmark runners and reporting modules.
Used By:
 - Pytest benchmark modularization validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Covers non-CLI execution and artifact serialization paths.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import benchmark.runners as runners_mod
from benchmark.reporting import build_output_payload, write_results_artifacts
from benchmark.runners import run_async_concurrent_suite, run_parallel_workers_suite


def test_run_async_concurrent_suite_returns_expected_shape() -> None:
    class _FakeLogger:
        async def log_batch(self, _messages) -> None:
            return None

    async def _run() -> dict:
        return await run_async_concurrent_suite(
            matrix=[1, 2],
            messages_per_task=3,
            create_logger=lambda _count: _FakeLogger(),
            flush_async=lambda _logger: asyncio.sleep(0),
            close_async=lambda _logger: asyncio.sleep(0),
            messages_per_second=lambda total, duration: total / duration if duration > 0 else 0.0,
        )

    result = asyncio.run(_run())
    assert result["suite"] == "async_concurrent"
    assert result["workers_tasks"] == [1, 2]
    assert "1" in result["scaling"]
    assert "2" in result["scaling"]


def test_run_parallel_workers_suite_uses_worker_results(monkeypatch, tmp_path) -> None:
    class _FakeFuture:
        def __init__(self, value: int) -> None:
            self._value = value

        def result(self) -> int:
            return self._value

    class _FakeExecutor:
        def __init__(self, max_workers: int) -> None:
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb) -> None:
            return None

        def submit(self, _fn, *_args, **_kwargs):
            return _FakeFuture(5)

    monkeypatch.setattr(runners_mod, "ProcessPoolExecutor", _FakeExecutor)
    result = run_parallel_workers_suite(
        matrix=[1, 2],
        messages_per_worker=5,
        bench_logs_dir=tmp_path,
        messages_per_second=lambda total, duration: total / duration if duration > 0 else 0.0,
    )

    assert result["suite"] == "parallel_workers"
    assert result["scaling"]["1"]["total_messages"] == 5
    assert result["scaling"]["2"]["total_messages"] == 10


def test_reporting_build_and_write_outputs(tmp_path) -> None:
    payload = build_output_payload(
        results={"sync_logger": {"messages_per_second": 1.0}},
        profile_name="ci_smoke",
        test_config={"typical_single_messages": 10000},
        python_version="3.12.3",
        platform_name="linux",
        git_commit_sha="abc1234",
        machine="linux-x86_64",
        cpu_count=8,
        disk_mode="buffered",
        payload_profile="mixed_default",
        timestamp="2026-03-16_16-00-00",
    )
    out_path = write_results_artifacts(output_payload=payload, results_dir=tmp_path)

    assert out_path.name == "benchmark_2026-03-16_16-00-00.json"
    latest_path = tmp_path / "benchmark_latest.json"
    assert latest_path.exists()
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_payload["metadata"]["profile"] == "ci_smoke"
