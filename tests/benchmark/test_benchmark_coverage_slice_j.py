"""
Role: Coverage-focused unit tests for benchmark helper modules.
Used By:
 - Pytest benchmark slice J validation.
Depends On:
 - benchmark
 - pytest
Notes:
 - Targets edge/error branches to improve deterministic module coverage.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

import benchmark.drift as drift_mod
import benchmark.guards as guards_mod
import benchmark.metrics as metrics_mod
import benchmark.profiles as profiles_mod
import benchmark.reporting as reporting_mod
import benchmark.runners as runners_mod
import benchmark.schema_validation as schema_mod
from benchmark.io_metrics import extract_handler_bytes_written


def test_parallel_sync_worker_handles_close_exception(monkeypatch, tmp_path) -> None:
    class _FakeLogger:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def info(self, message: str) -> None:
            self.messages.append(message)

        def close(self) -> None:
            raise RuntimeError("close-failed")

    fake_logger = _FakeLogger()
    monkeypatch.setattr(runners_mod, "getLogger", lambda *args, **kwargs: fake_logger)

    completed = runners_mod.parallel_sync_worker(
        bench_logs_dir=str(tmp_path),
        worker_count=2,
        worker_id=1,
        messages_per_worker=3,
    )

    assert completed == 3
    assert len(fake_logger.messages) == 3


def test_make_serializable_handles_tuple_and_custom_objects() -> None:
    class _WithDict:
        def __init__(self) -> None:
            self.value = 1

    class _NoDict:
        __slots__ = ("value",)

        def __init__(self) -> None:
            self.value = 1

    payload = {"tuple": (1, 2), "a": _WithDict(), "b": _NoDict()}
    result = reporting_mod.make_serializable(payload)

    assert result["tuple"] == [1, 2]
    assert isinstance(result["a"], str)
    assert isinstance(result["b"], str)


def test_build_output_payload_generates_timestamp_when_missing(monkeypatch) -> None:
    class _Now:
        @staticmethod
        def strftime(_fmt: str) -> str:
            return "2026-03-16_17-00-00"

    class _DateTime:
        @staticmethod
        def now() -> _Now:
            return _Now()

    monkeypatch.setattr(reporting_mod, "datetime", _DateTime)
    payload = reporting_mod.build_output_payload(
        results={"ok": True},
        profile_name=None,
        test_config={},
        python_version="3.12.3",
        platform_name="linux",
        git_commit_sha="abc",
        machine="x86",
        cpu_count=1,
        disk_mode="buffered",
        payload_profile="small",
        timestamp=None,
    )
    assert payload["metadata"]["timestamp"] == "2026-03-16_17-00-00"
    assert payload["metadata"]["profile"] == "legacy_default"


def test_schema_validation_reports_multiple_error_kinds() -> None:
    payload = {"metadata": {"timestamp": "", "cpu_count": -1}, "results": []}
    schema = {
        "type": "object",
        "required": ["metadata", "results", "missing"],
        "properties": {
            "metadata": {
                "type": "object",
                "required": ["timestamp", "cpu_count"],
                "properties": {
                    "timestamp": {"type": "string", "minLength": 1},
                    "cpu_count": {"type": "integer", "minimum": 0},
                },
            },
            "results": {"type": "object"},
        },
    }
    violations = schema_mod.validate_against_schema(payload, schema)

    assert any("missing required key 'missing'" in item for item in violations)
    assert any(
        "$.metadata.timestamp: string length 0 < minLength 1" in item
        for item in violations
    )
    assert any(
        "$.metadata.cpu_count: value -1 < minimum 0" in item for item in violations
    )
    assert any("$.results: expected type 'object'" in item for item in violations)


def test_schema_validation_skips_absent_optional_properties() -> None:
    payload = {"root": {}}
    schema = {
        "type": "object",
        "properties": {
            "root": {
                "type": "object",
                "properties": {"optional_child": {"type": "string"}},
            }
        },
    }
    violations = schema_mod.validate_against_schema(payload, schema)
    assert violations == []


def test_schema_is_type_handles_union_and_unknown() -> None:
    assert schema_mod._is_type(1, ["string", "integer"]) is True
    assert schema_mod._is_type(True, "integer") is False
    assert schema_mod._is_type("x", "custom-unknown-type") is True


def test_disable_direct_io_if_available_swallows_setter_errors() -> None:
    class _BrokenSetter:
        @property
        def _use_direct_io(
            self,
        ) -> bool:  # pragma: no cover - getter value not relevant
            return True

        @_use_direct_io.setter
        def _use_direct_io(self, _value: bool) -> None:
            raise RuntimeError("cannot-set")

    guards_mod.disable_direct_io_if_available(_BrokenSetter())


def test_ensure_composite_file_target_handles_non_list_and_existing_path() -> None:
    logger_non_list = types.SimpleNamespace(components=None)
    guards_mod.ensure_composite_file_target(
        logger=logger_non_list,
        prefix="x",
        build_log_path=lambda _prefix: "/tmp/bench/non-list.log",
    )

    existing = [types.SimpleNamespace(file_path="/tmp/bench/already.log")]
    logger_existing = types.SimpleNamespace(components=existing)
    guards_mod.ensure_composite_file_target(
        logger=logger_existing,
        prefix="y",
        build_log_path=lambda _prefix: "/tmp/bench/new.log",
    )
    assert len(existing) == 1


def test_validate_result_paths_invalid_path_and_nested_list(tmp_path) -> None:
    allowed_root = tmp_path / "benchmark" / "bench_logs"
    allowed_root.mkdir(parents=True)

    results = {
        "items": [{"path": "\x00bad"}],
        "ok": {"file_path": str(allowed_root / "safe.log")},
    }
    violations = guards_mod.validate_result_paths(
        results=results,
        allowed_roots=[allowed_root],
    )
    assert any("invalid path value" in item for item in violations)


def test_detect_new_root_log_leaks_handles_missing_logs_dir_and_subdirs(
    tmp_path,
) -> None:
    assert (
        guards_mod.detect_new_root_log_leaks(
            project_root=tmp_path,
            preexisting_log_names=set(),
        )
        == []
    )

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "subdir").mkdir()
    leaks = guards_mod.detect_new_root_log_leaks(
        project_root=tmp_path,
        preexisting_log_names=set(),
    )
    assert leaks == []


def test_validate_result_invariants_reports_non_finite_and_negative_timing() -> None:
    results = {
        "sync_logger": {
            "total_messages": 10,
            "individual_duration": 1.0,
            "individual_messages_per_second": float("inf"),
        },
        "file_writing": {
            "total_messages": 10,
            "duration": 2.0,
            "measured_duration": 2.0,
            "warmup_duration": -0.1,
            "flush_duration": -0.2,
            "expected_emitted": 10,
            "actual_emitted": 9,
            "written_lines": 0,
            "written_lines_observed": False,
            "strict_file_evidence": False,
            "messages_per_second": 5.0,
            "bytes_written": 100.0,
            "bytes_per_second": 50.0,
        },
        "async_concurrent": {"scaling": {"2": "invalid"}},
        "parallel_workers": {"scaling": {"2": "invalid"}},
        "configurations": {"dev": "invalid"},
    }
    violations = metrics_mod.validate_result_invariants(results)
    assert any("reported rate is not finite" in item for item in violations)
    assert any("warmup_duration: negative value" in item for item in violations)
    assert any("flush_duration: negative value" in item for item in violations)
    assert any("actual_emitted: expected 10 but found 9" in item for item in violations)
    assert not any("written_lines" in item for item in violations)


def test_validate_result_invariants_covers_non_dict_sections_and_parallel_scaling() -> (
    None
):
    results = {
        "sync_logger": "skip-non-dict",
        "file_writing": "skip-non-dict",
        "parallel_workers": {
            "scaling": {
                "2": {
                    "total_messages": 10,
                    "total_duration": 2.0,
                    "total_messages_per_second": 5.0,
                }
            }
        },
    }
    violations = metrics_mod.validate_result_invariants(results)
    assert violations == []


def test_validate_result_invariants_async_split_rates_and_dispatch_errors() -> None:
    results = {
        "async_logger": {
            "total_messages": 100,
            "individual_duration": 2.0,
            "individual_messages_per_second": 50.0,
            "task_fanout_duration": 2.0,
            "task_fanout_messages_per_second": 999.0,
            "logger_core_duration": 2.0,
            "logger_core_messages_per_second": 999.0,
        },
        "composite_logger": {
            "total_messages": 100,
            "individual_duration": 2.0,
            "individual_messages_per_second": 50.0,
            "small_batch_total_messages": 50,
            "small_batch_duration": 1.0,
            "small_batch_messages_per_second": 50.0,
            "batch_total_messages": 50,
            "batch_duration": 1.0,
            "batch_messages_per_second": 50.0,
            "batch_dispatch_errors": 1,
        },
    }
    violations = metrics_mod.validate_result_invariants(results)
    assert any(
        "async_logger.task_fanout_messages_per_second" in item for item in violations
    )
    assert any(
        "async_logger.logger_core_messages_per_second" in item for item in violations
    )
    assert any("composite_logger.batch_dispatch_errors" in item for item in violations)


def test_drift_percentile_and_extract_metric_edge_paths() -> None:
    assert drift_mod._percentile([], 95.0) == 0.0
    assert drift_mod._percentile([5.0], 95.0) == 5.0
    assert drift_mod._percentile([1.0, 2.0], 0.0) == 1.0
    assert drift_mod._percentile([1.0, 2.0], 100.0) == 2.0
    assert drift_mod._extract_metric({"a": {"b": 1.0}}, "a.b") == 1.0
    assert drift_mod._extract_metric({"a": {"b": "x"}}, "a.b") is None
    assert drift_mod._extract_metric({"a": 1.0}, "a.b") is None


def test_merge_policy_applies_overrides() -> None:
    policy = drift_mod._merge_policy({"enabled": True, "history_window": 9})
    assert policy["enabled"] is True
    assert policy["history_window"] == 9
    assert "metrics" in policy


def test_load_policy_for_profile_handles_invalid_policy_json(
    monkeypatch, tmp_path
) -> None:
    invalid_policy = tmp_path / "drift_policy_bad.json"
    invalid_policy.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(drift_mod, "POLICY_FILE", invalid_policy)
    policy = drift_mod.load_policy_for_profile(
        profile_name="pr_gate",
        policy_overrides={"enabled": True},
    )
    assert policy["enabled"] is True


def test_load_history_payloads_filters_bad_artifacts(tmp_path) -> None:
    (tmp_path / "benchmark_latest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "benchmark_2026-01-01_00-00-00.json").write_text(
        "{bad", encoding="utf-8"
    )
    (tmp_path / "benchmark_2026-01-01_00-00-01.json").write_text(
        json.dumps({"metadata": "bad", "results": {}}), encoding="utf-8"
    )
    (tmp_path / "benchmark_2026-01-01_00-00-02.json").write_text(
        json.dumps({"metadata": {"profile": "other"}, "results": {}}), encoding="utf-8"
    )
    (tmp_path / "benchmark_2026-01-01_00-00-03.json").write_text(
        json.dumps({"metadata": {"profile": "ci_smoke"}, "results": {}}),
        encoding="utf-8",
    )

    history = drift_mod._load_history_payloads(
        results_dir=tmp_path,
        profile_name="ci_smoke",
        history_window=5,
    )
    assert len(history) == 1


def test_load_history_payloads_stops_on_zero_history_window(tmp_path) -> None:
    (tmp_path / "benchmark_2026-01-01_00-00-01.json").write_text(
        json.dumps({"metadata": {"profile": "ci_smoke"}, "results": {}}),
        encoding="utf-8",
    )
    history = drift_mod._load_history_payloads(
        results_dir=tmp_path,
        profile_name="ci_smoke",
        history_window=0,
    )
    assert history == [{"metadata": {"profile": "ci_smoke"}, "results": {}}]


def test_evaluate_drift_policy_handles_non_list_metrics_and_missing_current(
    tmp_path,
) -> None:
    (tmp_path / "benchmark_2026-01-01_00-00-00.json").write_text(
        json.dumps(
            {
                "metadata": {"profile": "ci_smoke"},
                "results": {"sync_logger": {"individual_messages_per_second": 10.0}},
            }
        ),
        encoding="utf-8",
    )

    violations, report = drift_mod.evaluate_drift_policy(
        current_results={"sync_logger": {"other_metric": 1.0}},
        results_dir=tmp_path,
        profile_name="ci_smoke",
        policy_overrides={
            "enabled": True,
            "metrics": "not-a-list",
            "min_baseline_runs": 1,
        },
    )
    assert violations == []
    assert report["status"] == "passed"


def test_evaluate_drift_policy_skips_non_string_metric_and_non_dict_history(
    tmp_path,
) -> None:
    (tmp_path / "benchmark_2026-01-01_00-00-00.json").write_text(
        json.dumps(
            {
                "metadata": {"profile": "ci_smoke"},
                "results": {"sync_logger": {"individual_messages_per_second": 10.0}},
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "benchmark_2026-01-01_00-00-01.json").write_text(
        json.dumps({"metadata": {"profile": "ci_smoke"}, "results": "bad-node"}),
        encoding="utf-8",
    )
    violations, report = drift_mod.evaluate_drift_policy(
        current_results={"sync_logger": {"individual_messages_per_second": 9.0}},
        results_dir=tmp_path,
        profile_name="ci_smoke",
        policy_overrides={
            "enabled": True,
            "metrics": [42, "missing.path"],
            "min_baseline_runs": 1,
            "history_window": 10,
        },
    )
    assert violations == []
    assert report["metrics"]["missing.path"]["status"] == "skipped_no_current_metric"


def test_extract_handler_bytes_written_skips_handlers_without_stats() -> None:
    handler_without_stats = object()
    logger = types.SimpleNamespace(_layer_handlers={"default": [handler_without_stats]})

    assert extract_handler_bytes_written(logger) == 0


def test_load_profile_rejects_non_dict_payload(monkeypatch, tmp_path) -> None:
    bad_profile = tmp_path / "broken.json"
    bad_profile.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(profiles_mod, "PROFILE_DIR", tmp_path)
    try:
        profiles_mod.load_profile("broken")
    except ValueError as exc:
        assert "Invalid profile format" in str(exc)
    else:
        raise AssertionError("expected invalid profile payload to raise ValueError")
