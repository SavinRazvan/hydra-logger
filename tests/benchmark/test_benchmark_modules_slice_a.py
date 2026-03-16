"""
Role: Unit coverage for extracted benchmark helper modules.
Used By:
 - Pytest benchmark module validation.
Depends On:
 - benchmark
 - hydra_logger
 - pytest
Notes:
 - Validates Slice A extraction behavior remains deterministic.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from benchmark.guards import (
    disable_direct_io_if_available,
    ensure_composite_file_target,
    rebase_file_destinations_to_benchmark_logs,
)
from benchmark.metrics import (
    measure_async_batch_throughput,
    measure_sync_batch_throughput,
    messages_per_second,
)
from benchmark.workloads import (
    async_message,
    build_batch_messages,
    composite_message,
    sync_message,
)
from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer


def test_messages_per_second_handles_zero_duration() -> None:
    assert messages_per_second(10, 0.0) == 0.0
    assert messages_per_second(10, 2.0) == 5.0


def test_measure_sync_batch_throughput_runs_and_flushes() -> None:
    class FakeLogger:
        def __init__(self) -> None:
            self.calls = 0

        def log_batch(self, _messages) -> None:
            self.calls += 1

    logger = FakeLogger()
    flushed = {"count": 0}

    def _flush(_logger) -> None:
        flushed["count"] += 1

    total_messages, duration, rate = measure_sync_batch_throughput(
        logger=logger,
        messages=[("INFO", "m1", {})],
        flush_sync=_flush,
        min_duration_seconds=0.0,
        min_iterations=3,
    )

    assert logger.calls == 3
    assert flushed["count"] == 1
    assert total_messages == 3
    assert duration >= 0.0
    assert rate >= 0.0


def test_measure_async_batch_throughput_runs_and_flushes() -> None:
    class FakeAsyncLogger:
        def __init__(self) -> None:
            self.calls = 0

        async def log_batch(self, _messages) -> None:
            self.calls += 1

    logger = FakeAsyncLogger()
    flushed = {"count": 0}

    async def _flush(_logger) -> None:
        flushed["count"] += 1

    total_messages, duration, rate = asyncio.run(
        measure_async_batch_throughput(
            logger=logger,
            messages=[("INFO", "m1", {})],
            flush_async=_flush,
            min_duration_seconds=0.0,
            min_iterations=4,
        )
    )

    assert logger.calls == 4
    assert flushed["count"] == 1
    assert total_messages == 4
    assert duration >= 0.0
    assert rate >= 0.0


def test_rebase_file_destinations_to_benchmark_logs_rewrites_paths() -> None:
    config = LoggingConfig(
        layers={
            "default": LogLayer(
                destinations=[
                    LogDestination(type="file", path="root.log", format="json-lines"),
                    LogDestination(type="console", format="plain-text"),
                ]
            )
        }
    )

    rebased = rebase_file_destinations_to_benchmark_logs(
        config=config,
        config_name="default",
        build_log_path=lambda prefix: f"/tmp/bench/{prefix}.log",
    )

    assert rebased is not config
    assert rebased.layers["default"].destinations[0].path is not None
    assert "/tmp/bench/config_default_default_0.log" in rebased.layers["default"].destinations[
        0
    ].path
    assert rebased.layers["default"].destinations[1].type == "console"


def test_disable_direct_io_if_available_updates_flag() -> None:
    logger = SimpleNamespace(_use_direct_io=True)
    disable_direct_io_if_available(logger)
    assert logger._use_direct_io is False


def test_ensure_composite_file_target_adds_once() -> None:
    logger = SimpleNamespace(components=[])
    ensure_composite_file_target(
        logger=logger,
        prefix="composite_probe",
        build_log_path=lambda p: f"/tmp/bench/{p}.log",
    )
    ensure_composite_file_target(
        logger=logger,
        prefix="composite_probe",
        build_log_path=lambda p: f"/tmp/bench/{p}.log",
    )

    assert len(logger.components) == 1
    assert logger.components[0].file_path.endswith("composite_probe.log")


def test_workload_message_generators_are_deterministic() -> None:
    assert "Processing request" in sync_message(0)
    assert "Async task" in async_message(0)
    assert "Composite logger" in composite_message(0)


def test_build_batch_messages_uses_factory() -> None:
    result = build_batch_messages(3, lambda i: f"m{i}")
    assert result == [
        ("INFO", "m0", {}),
        ("INFO", "m1", {}),
        ("INFO", "m2", {}),
    ]


def test_build_batch_messages_validates_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be >= 0"):
        build_batch_messages(-1, lambda i: f"m{i}")


def test_build_batch_messages_validates_message_factory() -> None:
    with pytest.raises(TypeError, match="message_factory must be callable"):
        build_batch_messages(1, "not-callable")


def test_build_batch_messages_bubbles_factory_errors() -> None:
    def _broken_factory(_index: int) -> str:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        build_batch_messages(2, _broken_factory)
