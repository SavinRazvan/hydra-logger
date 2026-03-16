"""
Role: Unit coverage for benchmark harness internals.
Used By:
 - Pytest discovery and benchmark reliability checks.
Depends On:
 - hydra_logger
 - pytest
Notes:
 - Avoids heavy runtime loops by mocking benchmark orchestration methods.
"""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import benchmark.performance_benchmark as perf_mod
from benchmark.performance_benchmark import HydraLoggerBenchmark


def test_init_sets_paths_and_test_config(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(perf_mod, "listLoggers", lambda: ["l1", "l2"])
    removed = []
    monkeypatch.setattr(perf_mod, "removeLogger", lambda name: removed.append(name))

    bench = HydraLoggerBenchmark(save_results=True, results_dir=str(tmp_path / "results"))

    assert bench.results == {}
    assert bench.save_results is True
    assert bench.results_dir.exists()
    assert bench._benchmark_logs_dir.exists()
    assert bench.test_config["typical_single_messages"] == 100000
    assert bench.profile_name is None
    assert bench.drift_policy == {}
    assert removed == ["l1", "l2"]


def test_build_benchmark_log_path_sanitizes_prefix(tmp_path) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    log_path = bench._build_benchmark_log_path("perf async logger")
    path = Path(log_path)

    assert path.parent == bench._benchmark_logs_dir
    assert "perf_async_logger" in path.name
    assert path.suffix == ".log"


def test_create_performance_config_uses_expected_destination_types(tmp_path) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))

    sync_config = bench._create_performance_config("sync")
    sync_dest = sync_config.layers["default"].destinations[0]
    assert sync_dest.type == "file"
    assert sync_dest.path is not None
    assert "perf_sync" in sync_dest.path

    async_config = bench._create_performance_config("async")
    async_dest = async_config.layers["default"].destinations[0]
    assert async_dest.type == "async_file"
    assert async_dest.path is not None
    assert "perf_async" in async_dest.path

    composite_async_config = bench._create_performance_config("composite-async")
    composite_async_dest = composite_async_config.layers["default"].destinations[0]
    assert composite_async_dest.type == "async_file"


def test_git_commit_sha_returns_unknown_on_failure(tmp_path, monkeypatch) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))

    def _raise(*_args, **_kwargs):
        raise RuntimeError("git unavailable")

    monkeypatch.setattr(perf_mod.subprocess, "check_output", _raise)
    assert bench._git_commit_sha() == "unknown"


def test_ensure_composite_file_target_adds_shim_when_missing(tmp_path) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    logger = SimpleNamespace(components=[])

    bench._ensure_composite_file_target(logger, "composite_probe")
    assert len(logger.components) == 1
    assert getattr(logger.components[0], "file_path", None) is not None
    assert str(bench._benchmark_logs_dir) in logger.components[0].file_path


def test_ensure_composite_file_target_keeps_existing_file_component(tmp_path) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    existing = SimpleNamespace(file_path=str(tmp_path / "already.log"))
    logger = SimpleNamespace(components=[existing])

    bench._ensure_composite_file_target(logger, "composite_probe")
    assert logger.components == [existing]


def test_save_results_to_file_writes_metadata_and_latest_copy(
    tmp_path, monkeypatch
) -> None:
    bench = HydraLoggerBenchmark(save_results=True, results_dir=str(tmp_path / "results"))
    bench.results = {"sample": {"messages_per_second": 123.0}}
    monkeypatch.setattr(bench, "_git_commit_sha", lambda: "deadbee")

    bench.save_results_to_file()

    files = sorted(bench.results_dir.glob("benchmark_*.json"))
    assert files, "expected at least one timestamped benchmark artifact"

    latest_path = bench.results_dir / "benchmark_latest.json"
    assert latest_path.exists()

    payload = json.loads(latest_path.read_text())
    assert payload["metadata"]["git_commit_sha"] == "deadbee"
    assert payload["metadata"]["machine"]
    assert payload["metadata"]["cpu_count"] >= 1
    assert payload["metadata"]["disk_mode"]
    assert payload["metadata"]["payload_profile"]
    assert payload["results"]["sample"]["messages_per_second"] == 123.0


def test_run_benchmark_orchestrates_all_steps(tmp_path, monkeypatch) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    order = []

    monkeypatch.setattr(bench, "print_header", lambda: order.append("header"))
    monkeypatch.setattr(
        bench, "test_sync_logger_performance", lambda: order.append("sync") or {"ok": True}
    )
    monkeypatch.setattr(
        bench,
        "test_async_logger_performance",
        lambda: order.append("async") or asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(
        bench,
        "test_composite_logger_performance",
        lambda: order.append("composite") or {"ok": True},
    )
    monkeypatch.setattr(
        bench,
        "test_composite_async_logger_performance",
        lambda: order.append("composite_async") or asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(
        bench,
        "test_configuration_performance",
        lambda: order.append("config") or {"ok": True},
    )
    monkeypatch.setattr(
        bench, "test_file_writing_performance", lambda: order.append("file") or {"ok": True}
    )
    monkeypatch.setattr(
        bench,
        "test_async_file_writing_performance",
        lambda: order.append("async_file") or asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(bench, "test_memory_usage", lambda: order.append("memory") or {"ok": True})
    monkeypatch.setattr(
        bench,
        "test_concurrent_logging",
        lambda: order.append("concurrent") or asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(
        bench,
        "test_advanced_concurrent_logging",
        lambda: order.append("advanced") or asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(
        bench,
        "test_async_concurrent_suite",
        lambda: order.append("async_suite") or asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(
        bench,
        "test_parallel_workers_suite",
        lambda: order.append("parallel_suite") or {"ok": True},
    )
    monkeypatch.setattr(
        bench,
        "test_ultra_high_performance",
        lambda: order.append("ultra") or asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(bench, "print_detailed_results", lambda: order.append("details"))
    monkeypatch.setattr(bench, "_cleanup_logger_cache", lambda: order.append("cleanup"))
    monkeypatch.setattr(
        bench, "_final_cleanup", lambda: order.append("final_cleanup") or asyncio.sleep(0)
    )

    exit_code = asyncio.run(bench.run_benchmark())
    assert exit_code == 0
    assert "sync_logger" in bench.results
    assert "async_concurrent" in bench.results
    assert "parallel_workers" in bench.results
    assert "ultra_high_performance" in bench.results
    assert order.count("cleanup") == 13
    assert order[-1] == "final_cleanup"


def test_run_benchmark_returns_error_and_still_cleans_up(tmp_path, monkeypatch) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    calls = []

    monkeypatch.setattr(bench, "print_header", lambda: None)

    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr(bench, "test_sync_logger_performance", _explode)
    monkeypatch.setattr(
        bench, "_final_cleanup", lambda: calls.append("final_cleanup") or asyncio.sleep(0)
    )

    exit_code = asyncio.run(bench.run_benchmark())
    assert exit_code == 1
    assert calls == ["final_cleanup"]


def test_main_returns_run_benchmark_code(monkeypatch) -> None:
    class DummyBenchmark:
        def __init__(self, save_results=True, results_dir=None, profile=None):
            assert save_results is True
            assert results_dir is None
            assert profile is None

        async def run_benchmark(self):
            return 7

    monkeypatch.setattr(perf_mod, "HydraLoggerBenchmark", DummyBenchmark)
    assert asyncio.run(perf_mod.main()) == 7
