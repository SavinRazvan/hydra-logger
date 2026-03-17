"""
Role: Unit tests for benchmark reliability guard enforcement.
Used By:
 - Pytest benchmark reliability validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Covers hard-failure paths for metric and path invariants.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import benchmark.performance_benchmark as perf_mod
from benchmark.guards import (
    detect_new_root_log_leaks,
    validate_file_io_evidence,
    validate_output_matrix_file_evidence,
    validate_result_paths,
)
from benchmark.metrics import validate_result_invariants
from benchmark.performance_benchmark import HydraLoggerBenchmark


def _minimal_valid_results() -> dict:
    return {
        "sync_logger": {
            "total_messages": 100,
            "individual_duration": 2.0,
            "individual_messages_per_second": 50.0,
        },
        "async_logger": {
            "total_messages": 200,
            "individual_duration": 4.0,
            "individual_messages_per_second": 50.0,
        },
        "composite_logger": {
            "total_messages": 100,
            "individual_duration": 2.0,
            "individual_messages_per_second": 50.0,
            "small_batch_total_messages": 250,
            "small_batch_duration": 5.0,
            "small_batch_messages_per_second": 50.0,
            "batch_total_messages": 500,
            "batch_duration": 10.0,
            "batch_messages_per_second": 50.0,
        },
        "composite_async_logger": {
            "total_messages": 100,
            "individual_duration": 2.0,
            "individual_messages_per_second": 50.0,
            "batch_total_messages": 100,
            "batch_duration": 2.0,
            "batch_messages_per_second": 50.0,
        },
        "configurations": {
            "default": {
                "total_messages": 100,
                "duration": 2.0,
                "messages_per_second": 50.0,
            }
        },
        "file_writing": {
            "total_messages": 100,
            "duration": 2.0,
            "measured_duration": 2.0,
            "warmup_duration": 0.1,
            "flush_duration": 0.05,
            "expected_emitted": 100,
            "actual_emitted": 100,
            "written_lines": 100,
            "written_lines_observed": True,
            "messages_per_second": 50.0,
            "bytes_written": 1000,
            "bytes_per_second": 500.0,
            "file_path": "/tmp/benchmark/bench_logs/file.log",
        },
        "async_file_writing": {
            "total_messages": 100,
            "duration": 2.0,
            "measured_duration": 2.0,
            "warmup_duration": 0.1,
            "flush_duration": 0.05,
            "expected_emitted": 100,
            "actual_emitted": 100,
            "written_lines": 100,
            "written_lines_observed": True,
            "messages_per_second": 50.0,
            "bytes_written": 1000,
            "bytes_per_second": 500.0,
            "file_path": "/tmp/benchmark/bench_logs/file2.log",
        },
        "concurrent": {
            "total_messages": 100,
            "total_duration": 2.0,
            "total_messages_per_second": 50.0,
        },
    }


def test_validate_result_invariants_passes_on_matching_formulae() -> None:
    violations = validate_result_invariants(_minimal_valid_results())
    assert violations == []


def test_validate_result_invariants_detects_rate_mismatch() -> None:
    results = _minimal_valid_results()
    results["sync_logger"]["individual_messages_per_second"] = 123.0
    violations = validate_result_invariants(results)
    assert any("sync_logger.individual_messages_per_second" in v for v in violations)


def test_validate_result_invariants_detects_suite_scaling_mismatch() -> None:
    results = _minimal_valid_results()
    results["async_concurrent"] = {
        "scaling": {
            "2": {
                "total_messages": 100,
                "total_duration": 2.0,
                "total_messages_per_second": 999.0,
            }
        }
    }
    violations = validate_result_invariants(results)
    assert any("async_concurrent.scaling.2.total_messages_per_second" in v for v in violations)


def test_validate_result_invariants_detects_counting_and_timing_mismatch() -> None:
    results = _minimal_valid_results()
    results["file_writing"]["actual_emitted"] = 90
    results["file_writing"]["written_lines"] = 80
    results["file_writing"]["written_lines_observed"] = True
    results["file_writing"]["measured_duration"] = 3.0
    violations = validate_result_invariants(results)
    assert any("file_writing.actual_emitted" in v for v in violations)
    assert any("file_writing.written_lines" in v for v in violations)
    assert any("file_writing.measured_duration" in v for v in violations)


def test_validate_result_paths_detects_escape(tmp_path) -> None:
    allowed_logs = tmp_path / "benchmark" / "bench_logs"
    allowed_results = tmp_path / "benchmark" / "results"
    allowed_logs.mkdir(parents=True)
    allowed_results.mkdir(parents=True)

    results = {
        "file_writing": {
            "file_path": str(allowed_logs / "ok.log"),
        },
        "bad": {
            "file_path": str(tmp_path / "logs" / "leak.log"),
        },
    }
    violations = validate_result_paths(results=results, allowed_roots=[allowed_logs, allowed_results])
    assert any("bad.file_path" in v for v in violations)


def test_detect_new_root_log_leaks_finds_suspicious_files(tmp_path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True)
    preexisting = {"existing.log"}
    (logs_dir / "existing.log").write_text("x", encoding="utf-8")
    (logs_dir / "benchmark_composite_async_leak.log").write_text("x", encoding="utf-8")

    violations = detect_new_root_log_leaks(
        project_root=tmp_path,
        preexisting_log_names=preexisting,
    )
    assert len(violations) == 1
    assert "benchmark_composite_async_leak.log" in violations[0]


def test_validate_output_matrix_file_evidence_flags_missing_payload_fields() -> None:
    violations = validate_output_matrix_file_evidence(
        results={
            "output_matrix": {
                "file": {
                    "composite-async:plain-text:baseline:generated": {
                        "total_messages": 100,
                        "file_path": None,
                        "written_lines": None,
                    }
                }
            }
        }
    )
    assert any("file_path: missing concrete output path" in item for item in violations)
    assert any("written_lines: missing integer evidence" in item for item in violations)


def test_validate_output_matrix_file_evidence_passes_for_well_formed_case() -> None:
    violations = validate_output_matrix_file_evidence(
        results={
            "output_matrix": {
                "file": {
                    "sync:plain-text:baseline:generated": {
                        "total_messages": 100,
                        "file_path": "/tmp/benchmark/bench_logs/case.log",
                        "written_lines": 100,
                    }
                }
            }
        }
    )
    assert violations == []


def test_validate_output_matrix_file_evidence_handles_non_dict_sections() -> None:
    assert validate_output_matrix_file_evidence(results={}) == []
    assert validate_output_matrix_file_evidence(results={"output_matrix": []}) == []
    assert validate_output_matrix_file_evidence(results={"output_matrix": {"file": []}}) == []


def test_validate_output_matrix_file_evidence_flags_non_object_payload() -> None:
    violations = validate_output_matrix_file_evidence(
        results={
            "output_matrix": {
                "file": {
                    "sync:plain-text:baseline:generated": "invalid",
                }
            }
        }
    )
    assert any("expected object payload" in item for item in violations)


def test_validate_output_matrix_file_evidence_flags_non_positive_written_lines() -> None:
    violations = validate_output_matrix_file_evidence(
        results={
            "output_matrix": {
                "file": {
                    "sync:plain-text:baseline:generated": {
                        "total_messages": 10,
                        "file_path": "/tmp/benchmark/bench_logs/case.log",
                        "written_lines": 0,
                    }
                }
            }
        }
    )
    assert any("expected > 0, found 0" in item for item in violations)


def test_validate_output_matrix_file_evidence_flags_too_low_written_lines() -> None:
    violations = validate_output_matrix_file_evidence(
        results={
            "output_matrix": {
                "file": {
                    "sync:plain-text:baseline:generated": {
                        "total_messages": 100,
                        "file_path": "/tmp/benchmark/bench_logs/case.log",
                        "written_lines": 99,
                    }
                }
            }
        }
    )
    assert any("too low for 100 emitted messages" in item for item in violations)


def test_validate_file_io_evidence_flags_missing_strict_fields() -> None:
    violations = validate_file_io_evidence(
        results={
            "file_writing": {
                "expected_emitted": 100,
                "actual_emitted": 90,
                "written_lines": 0,
                "written_lines_observed": False,
                "strict_file_evidence": True,
                "file_path": "",
            }
        }
    )
    assert any("file_writing.file_path" in item for item in violations)
    assert any("file_writing.written_lines_observed" in item for item in violations)
    assert any("file_writing.written_lines: expected positive integer evidence" in item for item in violations)
    assert any("file_writing.actual_emitted: expected 100 but found 90" in item for item in violations)


def test_run_benchmark_returns_error_when_reliability_guard_fails(
    tmp_path, monkeypatch
) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    monkeypatch.setattr(bench, "print_header", lambda: None)
    monkeypatch.setattr(bench, "test_sync_logger_performance", lambda: {"ok": True})
    monkeypatch.setattr(
        bench, "test_async_logger_performance", lambda: asyncio.sleep(0, result={"ok": True})
    )
    monkeypatch.setattr(bench, "test_composite_logger_performance", lambda: {"ok": True})
    monkeypatch.setattr(
        bench,
        "test_composite_async_logger_performance",
        lambda: asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(bench, "test_configuration_performance", lambda: {"ok": True})
    monkeypatch.setattr(bench, "test_file_writing_performance", lambda: {"ok": True})
    monkeypatch.setattr(
        bench,
        "test_async_file_writing_performance",
        lambda: asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(bench, "test_memory_usage", lambda: {"ok": True})
    monkeypatch.setattr(
        bench, "test_concurrent_logging", lambda: asyncio.sleep(0, result={"ok": True})
    )
    monkeypatch.setattr(
        bench,
        "test_async_concurrent_suite",
        lambda: asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(bench, "test_parallel_workers_suite", lambda: {"ok": True})
    monkeypatch.setattr(
        bench,
        "test_advanced_concurrent_logging",
        lambda: asyncio.sleep(0, result={"ok": True}),
    )
    monkeypatch.setattr(
        bench, "test_ultra_high_performance", lambda: asyncio.sleep(0, result={"ok": True})
    )
    monkeypatch.setattr(bench, "print_detailed_results", lambda: None)
    monkeypatch.setattr(bench, "_cleanup_logger_cache", lambda: None)
    monkeypatch.setattr(bench, "_final_cleanup", lambda: asyncio.sleep(0))
    monkeypatch.setattr(
        bench,
        "_enforce_reliability_guards",
        lambda: (_ for _ in ()).throw(RuntimeError("guard-failed")),
    )

    exit_code = asyncio.run(bench.run_benchmark())
    assert exit_code == 1


def test_enforce_reliability_guards_fails_on_drift_violations(tmp_path, monkeypatch) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    bench.strict_reliability_guards = True
    bench.results = _minimal_valid_results()

    monkeypatch.setattr(perf_mod, "validate_result_invariants", lambda _results: [])
    monkeypatch.setattr(
        perf_mod,
        "evaluate_drift_policy",
        lambda **_kwargs: (["sync_logger.individual_messages_per_second drift"], {"status": "failed"}),
    )
    monkeypatch.setattr(perf_mod, "validate_result_paths", lambda **_kwargs: [])
    monkeypatch.setattr(perf_mod, "validate_output_matrix_file_evidence", lambda **_kwargs: [])
    monkeypatch.setattr(perf_mod, "detect_new_root_log_leaks", lambda **_kwargs: [])

    try:
        bench._enforce_reliability_guards()
    except RuntimeError as exc:
        assert "drift" in str(exc)
    else:
        raise AssertionError("expected drift violation to raise RuntimeError")

    assert bench.results["drift_policy"]["status"] == "failed"


def test_enforce_reliability_guards_records_pass_report(tmp_path, monkeypatch) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    bench.results = _minimal_valid_results()

    monkeypatch.setattr(perf_mod, "validate_result_invariants", lambda _results: [])
    monkeypatch.setattr(
        perf_mod,
        "evaluate_drift_policy",
        lambda **_kwargs: ([], {"status": "passed"}),
    )
    monkeypatch.setattr(perf_mod, "validate_result_paths", lambda **_kwargs: [])
    monkeypatch.setattr(perf_mod, "validate_output_matrix_file_evidence", lambda **_kwargs: [])
    monkeypatch.setattr(perf_mod, "detect_new_root_log_leaks", lambda **_kwargs: [])

    bench._enforce_reliability_guards()
    guards = bench.results["reliability_guards"]
    assert guards["status"] == "passed"
    assert guards["total_violations"] == 0


def test_enforce_reliability_guards_advisory_mode_does_not_raise(tmp_path, monkeypatch) -> None:
    bench = HydraLoggerBenchmark(save_results=False, results_dir=str(tmp_path / "results"))
    bench.strict_reliability_guards = False
    bench.results = _minimal_valid_results()
    monkeypatch.setattr(
        perf_mod,
        "validate_result_invariants",
        lambda _results: ["sync_logger.individual_messages_per_second mismatch"],
    )
    monkeypatch.setattr(perf_mod, "evaluate_drift_policy", lambda **_kwargs: ([], {"status": "passed"}))
    monkeypatch.setattr(perf_mod, "validate_result_paths", lambda **_kwargs: [])
    monkeypatch.setattr(perf_mod, "validate_output_matrix_file_evidence", lambda **_kwargs: [])
    monkeypatch.setattr(perf_mod, "validate_file_io_evidence", lambda **_kwargs: [])
    monkeypatch.setattr(perf_mod, "detect_new_root_log_leaks", lambda **_kwargs: [])
    bench._enforce_reliability_guards()
    assert bench.results["reliability_guards"]["status"] == "failed"
