#!/usr/bin/env python3
"""
Role: Benchmark harness for measuring logger performance profiles.
Used By:
 - Maintainers validating runtime performance regressions.
Depends On:
 - asyncio
 - datetime
 - gc
 - hydra_logger
 - json
 - os
 - pathlib
 - psutil
 - ...
Notes:
 - Measures throughput/latency scenarios for logger runtime comparisons.
"""

import asyncio
import argparse
import gc
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import platform
from typing import Any, Dict, List, Literal, Optional, Tuple, cast

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os

from hydra_logger import getAsyncLogger, getLogger, getSyncLogger
from hydra_logger.config import (
    get_default_config,
    get_development_config,
    get_production_config,
)
from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer
from hydra_logger.core.logger_management import clearLoggers, listLoggers, removeLogger

from benchmark.guards import (
    detect_new_root_log_leaks,
    disable_direct_io_if_available,
    ensure_composite_file_target,
    rebase_file_destinations_to_benchmark_logs,
    validate_file_io_evidence,
    validate_output_matrix_file_evidence,
    validate_result_paths,
)
from benchmark.drift import evaluate_drift_policy
from benchmark.io_metrics import (
    build_file_io_result,
    count_written_lines,
    extract_handler_bytes_written,
    extract_handler_messages_emitted,
    resolve_written_line_delta,
    resolve_bytes_written,
)
from benchmark.metrics import (
    measure_async_batch_throughput,
    measure_sync_batch_throughput,
    messages_per_second,
    summarize_samples,
    validate_sample_duration,
    validate_result_invariants,
)
from benchmark.profiles import load_profile
from benchmark.reporting import build_output_payload, write_results_artifacts
from benchmark.runners import (
    run_async_concurrent_suite,
    run_parallel_workers_suite,
)
from benchmark.workloads import build_batch_messages

DestinationType = Literal["file", "console", "null", "async_console", "async_file", "async_cloud"]


class HydraLoggerBenchmark:  # pragma: no cover
    """
    Performance benchmark for Hydra-Logger.

    Provides performance testing for all logger types, including individual
    message throughput, batch processing efficiency, memory usage analysis,
    and configuration performance comparison.
    """

    def __init__(
        self,
        save_results: bool = True,
        results_dir: str | None = None,
        profile: str | None = None,
        enabled_sections: List[str] | None = None,
    ):
        self.results = {}
        self.save_results = save_results
        self.profile_name = profile
        self.profile = load_profile(profile)
        self.drift_policy = self.profile.get("drift_policy", {})
        self.strict_reliability_guards = bool(
            self.profile.get("strict_reliability_guards", False)
        )
        self.write_markdown_reports = bool(self.profile.get("write_markdown_reports", True))
        self.disk_mode = str(self.profile.get("disk_mode", "buffered_default"))
        self.payload_profile = str(self.profile.get("payload_profile", "mixed_default"))
        benchmark_root = Path(__file__).resolve().parent
        self._project_root = benchmark_root.parent
        self.results_dir = (
            Path(results_dir)
            if results_dir is not None
            else benchmark_root / "results"
        )
        # Create results directory if saving
        if self.save_results:
            self.results_dir.mkdir(parents=True, exist_ok=True)

        # Track all created loggers for proper cleanup
        self._created_loggers = []

        # Track logger names for cache cleanup
        self._logger_names = []

        # Persist benchmark logs under benchmark/bench_logs
        # so benchmark output never spills into the project root.
        self._benchmark_logs_dir = benchmark_root / "bench_logs"
        self._benchmark_logs_dir.mkdir(parents=True, exist_ok=True)
        self._prune_benchmark_logs()
        logs_dir = self._project_root / "logs"
        self._preexisting_root_log_names = (
            {path.name for path in logs_dir.glob("*") if path.is_file()}
            if logs_dir.exists()
            else set()
        )

        # Clear any existing loggers from global cache to ensure clean state
        # This prevents state pollution from previous benchmark runs
        try:
            existing_loggers = listLoggers()
            if existing_loggers:
                print(
                    f"Cleaning up {len(existing_loggers)} existing loggers from global cache..."
                )
                for logger_name in existing_loggers:
                    try:
                        removeLogger(logger_name)
                    except Exception:
                        pass
        except Exception:
            pass

        # Test configuration parameters
        self.test_config = {
            # Single message logging test parameters
            "typical_single_messages": 100000,
            "small_batch_size": 50,
            "medium_batch_size": 200,
            "large_batch_size": 1000,
            # Concurrent logging test parameters
            "concurrent_workers": 8,
            "messages_per_worker": 100,
            # Message size characteristics
            "message_size_small": 50,
            "message_size_medium": 150,
            "message_size_large": 500,
            # Scenario-based test parameters
            "web_request_logs": 20,
            "database_operation_logs": 10,
            "background_task_logs": 100,
            # Stress test parameters
            "stress_test_messages": 100000,
            "stress_concurrent_workers": 50,
            # Suite split matrix defaults (profile overrides preferred).
            "suite_matrix_workers_tasks": [1, 2, 4, 8, 16, 32],
            "suite_matrix_messages_per_worker": 1000,
            "repetitions": 1,
            "soak_enabled": False,
        }
        overrides = self.profile.get("test_config_overrides", {})
        if isinstance(overrides, dict):
            self.test_config.update(overrides)
        matrix_overrides = self.profile.get("output_matrix_overrides", {})
        self.output_matrix_overrides = (
            matrix_overrides if isinstance(matrix_overrides, dict) else {}
        )
        self.min_sample_duration_seconds = float(
            self.profile.get("min_sample_duration_seconds", 0.001)
        )
        repetition_sections = self.profile.get("repetition_sections", [])
        self.repetition_sections = (
            [str(item) for item in repetition_sections]
            if isinstance(repetition_sections, list)
            else []
        )
        profile_enabled_sections = self.profile.get("enabled_sections", [])
        self.enabled_sections = self._resolve_enabled_sections(
            cli_sections=enabled_sections,
            profile_sections=profile_enabled_sections,
        )
        self._is_partial_section_run = len(self.enabled_sections) < len(
            self._all_section_names()
        )
        if self._is_partial_section_run and self.save_results:
            print(
                "Partial section benchmark requested; disabling result artifact persistence "
                "to preserve full-suite benchmark schema contracts."
            )
            self.save_results = False

    def _section_plan(
        self,
    ) -> List[Tuple[str, Literal["sync", "async"], Any, Optional[int]]]:
        """Ordered benchmark section execution plan."""
        return [
            ("sync_logger", "sync", self.test_sync_logger_performance, None),
            (
                "network_destination",
                "sync",
                self.test_network_destination_performance,
                1,
            ),
            ("async_logger", "async", self.test_async_logger_performance, None),
            ("composite_logger", "sync", self.test_composite_logger_performance, None),
            (
                "composite_async_logger",
                "async",
                self.test_composite_async_logger_performance,
                None,
            ),
            ("configurations", "sync", self.test_configuration_performance, 1),
            ("output_matrix", "async", self.test_output_matrix_performance, 1),
            ("file_writing", "sync", self.test_file_writing_performance, None),
            (
                "async_file_writing",
                "async",
                self.test_async_file_writing_performance,
                None,
            ),
            ("memory", "sync", self.test_memory_usage, 1),
            ("concurrent", "async", self.test_concurrent_logging, None),
            ("async_concurrent", "async", self.test_async_concurrent_suite, None),
            ("parallel_workers", "sync", self.test_parallel_workers_suite, None),
            (
                "advanced_concurrent",
                "async",
                self.test_advanced_concurrent_logging,
                None,
            ),
            (
                "ultra_high_performance",
                "async",
                self.test_ultra_high_performance,
                None,
            ),
        ]

    def _all_section_names(self) -> List[str]:
        """Return all supported benchmark section names in execution order."""
        return [name for name, _kind, _scenario, _repeat in self._section_plan()]

    @staticmethod
    def _normalize_sections(raw: Any) -> List[str]:
        """Normalize section config/CLI payloads into ordered unique names."""
        if raw is None:
            return []
        if isinstance(raw, str):
            items = [item.strip() for item in raw.split(",")]
        elif isinstance(raw, list):
            items = [str(item).strip() for item in raw]
        else:
            raise ValueError("enabled_sections must be a list of section names or CSV string")

        normalized: List[str] = []
        for item in items:
            if not item:
                continue
            if item not in normalized:
                normalized.append(item)
        return normalized

    def _resolve_enabled_sections(
        self, cli_sections: Any, profile_sections: Any
    ) -> List[str]:
        """Resolve active sections with precedence CLI > profile > full suite."""
        supported = self._all_section_names()
        selected = self._normalize_sections(cli_sections) or self._normalize_sections(
            profile_sections
        )
        if not selected:
            return supported

        unknown = [name for name in selected if name not in supported]
        if unknown:
            raise ValueError(
                "Unknown benchmark section(s): "
                + ", ".join(unknown)
                + ". Supported sections: "
                + ", ".join(supported)
            )
        return selected

    def _build_benchmark_log_path(self, prefix: str) -> str:
        """Create a unique benchmark log path under benchmark_logs."""
        safe_prefix = str(prefix).replace(" ", "_")
        filename = f"{safe_prefix}_{id(self)}_{time.time_ns()}.log"
        return str(self._benchmark_logs_dir / filename)

    def _resolve_output_matrix_file_path(
        self, configured_path: str | None, log_format: str
    ) -> str | None:
        """Resolve actual file path used by handlers for output-matrix file cases."""
        if not configured_path:
            return None

        configured = Path(configured_path)
        if configured.exists():
            return str(configured)

        candidates = [configured]
        if log_format == "json-lines":
            candidates.append(configured.with_suffix(".jsonl"))
        elif log_format == "csv":
            candidates.append(configured.with_suffix(".csv"))

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        # Fallback: handlers may derive filename variants from the configured stem.
        stem = configured.with_suffix("").name
        for candidate in sorted(configured.parent.glob(f"{stem}*")):
            if candidate.is_file():
                return str(candidate)
        return None

    def _prune_benchmark_logs(self) -> None:
        """Delete existing benchmark-generated logs before a new run."""
        try:
            for path in self._benchmark_logs_dir.glob("*"):
                if path.is_file():
                    path.unlink()
        except Exception:
            pass

    @staticmethod
    def _count_written_lines(file_path: str) -> int:
        """Best-effort line counter for line-based output files."""
        return count_written_lines(file_path)

    @staticmethod
    def _messages_per_second(total_messages: int, duration: float) -> float:
        """Safely compute throughput from message count and elapsed duration."""
        return messages_per_second(total_messages, duration)

    def _measure_sync_batch_throughput(
        self,
        logger,
        messages: List[Tuple[str, str, Dict[str, Any]]],
        min_duration_seconds: float = 0.25,
        min_iterations: int = 5,
    ) -> Tuple[int, float, float]:
        """Measure sync batch throughput over multiple iterations for stable results."""
        return measure_sync_batch_throughput(
            logger=logger,
            messages=messages,
            flush_sync=self._flush_all_handlers,
            min_duration_seconds=min_duration_seconds,
            min_iterations=min_iterations,
        )

    async def _measure_async_batch_throughput(
        self,
        logger,
        messages: List[Tuple[str, str, Dict[str, Any]]],
        min_duration_seconds: float = 0.25,
        min_iterations: int = 5,
    ) -> Tuple[int, float, float]:
        """Measure async batch throughput over multiple iterations for stable results."""
        return await measure_async_batch_throughput(
            logger=logger,
            messages=messages,
            flush_async=self._flush_all_handlers_async,
            min_duration_seconds=min_duration_seconds,
            min_iterations=min_iterations,
        )

    def _create_performance_config(self, logger_type: str = "sync") -> LoggingConfig:
        """
        Create a performance-optimized configuration without output I/O.

        Core throughput tests should measure logger/runtime overhead and avoid
        generating benchmark output files unless a file-writing benchmark
        explicitly requests them.

        Args:
            logger_type: Type of logger (sync/async) to determine handler type

        Returns:
            LoggingConfig optimized for performance testing
        """
        return LoggingConfig(
            default_level="INFO",
            enable_security=False,  # Disable for performance
            enable_sanitization=False,  # Disable for performance
            enable_plugins=False,  # Disable for performance
            enable_performance_monitoring=False,  # Disable for performance
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="null",
                            format="plain-text",
                        ),
                    ],
                )
            },
        )

    def _create_output_matrix_config(
        self,
        *,
        sink: str,
        logger_type: str,
        log_format: str,
        customization: str,
        config_name: str,
        enable_plugins: bool = False,
        multi_destinations: list[tuple[str, str]] | None = None,
    ) -> LoggingConfig:
        """Create output benchmark configs for console/file matrix scenarios."""
        is_async_logger = logger_type in {"async", "composite-async"}
        destination_type: DestinationType = "console"
        destination_path = None
        if sink in {"file", "async_file"}:
            destination_type = "async_file" if is_async_logger or sink == "async_file" else "file"
            destination_path = self._build_benchmark_log_path(
                f"matrix_{config_name}_{logger_type}_{log_format}_{customization}"
            )
        elif sink in {"async_cloud", "async_cloud_stub"}:
            # Keep cloud benchmarks deterministic by stubbing with local async_file output.
            destination_type = "async_file"
            destination_path = self._build_benchmark_log_path(
                f"matrix_cloud_stub_{config_name}_{logger_type}_{log_format}_{customization}"
            )
        elif sink == "async_console":
            destination_type = "async_console"
        elif sink == "console":
            destination_type = "console"

        enable_security = customization == "hardened"
        enable_sanitization = customization == "hardened"
        destinations = [
            LogDestination(
                type=cast(DestinationType, destination_type),
                path=destination_path,
                format=log_format,
                use_colors=(sink in {"console", "async_console"} and log_format == "colored"),
            )
        ]
        if multi_destinations:
            for extra_sink, extra_format in multi_destinations:
                extra_type: DestinationType = "console"
                extra_path = None
                if extra_sink in {"file", "async_file", "async_cloud", "async_cloud_stub"}:
                    extra_type = "async_file" if is_async_logger else "file"
                    extra_path = self._build_benchmark_log_path(
                        f"matrix_multi_{config_name}_{logger_type}_{extra_sink}_{extra_format}"
                    )
                elif extra_sink == "async_console":
                    extra_type = "async_console"
                else:
                    extra_type = "console"
                destinations.append(
                    LogDestination(
                        type=cast(DestinationType, extra_type),
                        path=extra_path,
                        format=extra_format,
                        use_colors=(extra_sink in {"console", "async_console"} and extra_format == "colored"),
                    )
                )

        return LoggingConfig(
            default_level="INFO",
            enable_security=enable_security,
            enable_sanitization=enable_sanitization,
            enable_plugins=enable_plugins,
            enable_performance_monitoring=False,
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=destinations,
                )
            },
        )

    @staticmethod
    def _force_console_destinations(config: LoggingConfig) -> LoggingConfig:
        """Rewrite all layer destinations to console-only for console matrix tests."""
        for layer in config.layers.values():
            layer.destinations = [
                LogDestination(type="console", format="plain-text", use_colors=False)
            ]
        return config

    @staticmethod
    def _is_sink_compatible(logger_type: str, sink: str) -> bool:
        """Return whether matrix sink is compatible with logger runtime type."""
        console_sinks = {"console", "async_console"}
        file_sinks = {"file", "async_file", "async_cloud_stub", "async_cloud"}
        if sink in console_sinks:
            return True
        if sink in file_sinks and logger_type in {"sync", "composite"}:
            return sink == "file"
        if sink in file_sinks and logger_type in {"async", "composite-async"}:
            return True
        return False

    def _create_logger_for_type(
        self, *, logger_name: str, logger_type: str, config: LoggingConfig
    ):
        """Create logger instance by requested runtime type."""
        if logger_type == "sync":
            return getSyncLogger(logger_name, config=config)
        if logger_type == "async":
            return getAsyncLogger(logger_name, config=config)
        logger = getLogger(
            logger_name, logger_type=logger_type, config=config, use_direct_io=False
        )
        if logger_type == "composite-async":
            self._ensure_composite_file_target(logger, prefix=logger_name)
        return logger

    async def _close_logger_instance(self, logger: Any) -> None:
        """Close logger while supporting sync and async variants."""
        try:
            if hasattr(logger, "aclose") and asyncio.iscoroutinefunction(logger.aclose):
                await logger.aclose()
            elif hasattr(logger, "close_async") and asyncio.iscoroutinefunction(
                logger.close_async
            ):
                await logger.close_async()
            elif hasattr(logger, "close"):
                logger.close()
        except Exception:
            pass

    async def test_output_matrix_performance(self) -> Dict[str, Any]:
        """Benchmark console and file outputs across logger/format/customization matrix."""
        print("\nTesting Output Matrix Performance...")
        print("   Testing console and file outputs across logger variants...")

        overrides = self.output_matrix_overrides
        logger_types = overrides.get(
            "logger_types", ["sync", "async", "composite", "composite-async"]
        )
        console_sinks = overrides.get("console_sinks", ["console", "async_console"])
        file_sinks = overrides.get("file_sinks", ["file", "async_file", "async_cloud_stub"])
        console_formats = overrides.get("console_formats", ["plain-text", "colored", "json-lines"])
        file_formats = overrides.get("file_formats", ["plain-text", "json-lines", "csv"])
        customizations = overrides.get("customizations", ["baseline", "hardened"])
        include_extensions = bool(overrides.get("include_extensions", True))
        max_cases = int(overrides.get("max_cases", 200))
        console_message_count = int(overrides.get("console_message_count", 10))
        file_message_count = int(
            overrides.get(
                "file_message_count",
                max(100, int(self.test_config.get("small_batch_size", 50) * 2)),
            )
        )
        multi_destination_cases = overrides.get(
            "multi_destination_cases",
            [
                {
                    "sink": "console",
                    "format": "plain-text",
                    "extras": [["file", "json-lines"]],
                },
                {
                    "sink": "async_console",
                    "format": "json-lines",
                    "extras": [["async_file", "json-lines"]],
                },
            ],
        )

        results: Dict[str, Any] = {
            "console": {},
            "file": {},
            "multi_destination": {},
            "status": "COMPLETED",
        }
        if include_extensions:
            results["extensions"] = {}
        case_counter = 0

        async def _run_case(
            *,
            sink: str,
            logger_type: str,
            log_format: str,
            customization: str,
            config_name: str,
            config: LoggingConfig,
            extension_mode: str = "disabled",
        ) -> Dict[str, Any]:
            nonlocal case_counter
            case_counter += 1
            if case_counter > max_cases:
                return {"status": "SKIPPED_CASE_CAP"}

            default_layer = config.layers.get("default")
            destinations = default_layer.destinations if default_layer is not None else []
            configured_file_path = None
            for destination in destinations:
                maybe_path = getattr(destination, "path", None)
                if maybe_path:
                    configured_file_path = maybe_path
                    break
            logger_name = (
                f"matrix_{sink}_{logger_type}_{log_format}_{customization}_{extension_mode}_{config_name}_{id(self)}"
            )
            logger = self._create_logger_for_type(
                logger_name=logger_name, logger_type=logger_type, config=config
            )
            if logger_type == "composite-async" and sink in {"file", "async_file", "async_cloud_stub"}:
                # Composite-async file matrix must run with direct I/O enabled,
                # otherwise this logger class routes only to in-memory components.
                try:
                    logger._use_direct_io = True
                except Exception:
                    pass
            else:
                self._disable_direct_io_if_available(logger)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)

            start = time.perf_counter()
            if logger_type in {"async", "composite-async"}:
                target_count = (
                    file_message_count
                    if sink in {"file", "async_file", "async_cloud_stub"}
                    else console_message_count
                )
                for i in range(target_count):
                    await logger.log(
                        "INFO", f"matrix sink={sink} type={logger_type} format={log_format} msg={i}"
                    )
                await self._flush_all_handlers_async(logger)
            else:
                target_count = (
                    file_message_count
                    if sink in {"file", "async_file", "async_cloud_stub"}
                    else console_message_count
                )
                for i in range(target_count):
                    logger.info(
                        f"matrix sink={sink} type={logger_type} format={log_format} msg={i}"
                    )
                self._flush_all_handlers(logger)
            duration = time.perf_counter() - start

            component_file_path = None
            if logger_type == "composite-async":
                for component in getattr(logger, "components", []):
                    maybe_path = getattr(component, "file_path", None)
                    if maybe_path:
                        component_file_path = maybe_path
                        break

            await self._close_logger_instance(logger)
            file_path = self._resolve_output_matrix_file_path(
                configured_file_path, log_format
            )
            if not file_path and component_file_path:
                file_path = self._resolve_output_matrix_file_path(
                    component_file_path, log_format
                )
            written_lines = self._count_written_lines(file_path) if file_path else None
            return {
                "messages_per_second": self._messages_per_second(target_count, duration),
                "duration": duration,
                "total_messages": target_count,
                "format": log_format,
                "customization": customization,
                "config_name": config_name,
                "sink": sink,
                "extension_mode": extension_mode,
                "file_path": file_path,
                "written_lines": written_lines,
            }

        for logger_type in logger_types:
            for sink in console_sinks:
                if not self._is_sink_compatible(logger_type, sink):
                    continue
                for log_format in console_formats:
                    for customization in customizations:
                        extension_modes = ["disabled", "enabled"] if include_extensions else ["disabled"]
                        for extension_mode in extension_modes:
                            config = self._create_output_matrix_config(
                                sink=sink,
                                logger_type=logger_type,
                                log_format=log_format,
                                customization=customization,
                                config_name="generated",
                                enable_plugins=(extension_mode == "enabled"),
                            )
                            key = (
                                f"{logger_type}:{sink}:{log_format}:{customization}:{extension_mode}:generated"
                            )
                            payload = await _run_case(
                                sink=sink,
                                logger_type=logger_type,
                                log_format=log_format,
                                customization=customization,
                                config_name="generated",
                                config=config,
                                extension_mode=extension_mode,
                            )
                            if payload.get("status") == "SKIPPED_CASE_CAP":
                                continue
                            results["console"][key] = payload
                            if include_extensions and extension_mode == "enabled":
                                results["extensions"][key] = payload

        template_configs = {
            "default": get_default_config(),
            "development": get_development_config(),
            "production": get_production_config(),
        }
        for logger_type in logger_types:
            for config_name, base_config in template_configs.items():
                config = self._force_console_destinations(base_config.model_copy(deep=True))
                key = f"{logger_type}:template:{config_name}"
                results["console"][key] = await _run_case(
                    sink="console",
                    logger_type=logger_type,
                    log_format="template",
                    customization="template",
                    config_name=config_name,
                    config=config,
                )

        for logger_type in logger_types:
            for sink in file_sinks:
                if not self._is_sink_compatible(logger_type, sink):
                    continue
                for log_format in file_formats:
                    for customization in customizations:
                        extension_modes = ["disabled", "enabled"] if include_extensions else ["disabled"]
                        for extension_mode in extension_modes:
                            config = self._create_output_matrix_config(
                                sink=sink,
                                logger_type=logger_type,
                                log_format=log_format,
                                customization=customization,
                                config_name="generated",
                                enable_plugins=(extension_mode == "enabled"),
                            )
                            key = (
                                f"{logger_type}:{sink}:{log_format}:{customization}:{extension_mode}:generated"
                            )
                            payload = await _run_case(
                                sink=sink,
                                logger_type=logger_type,
                                log_format=log_format,
                                customization=customization,
                                config_name="generated",
                                config=config,
                                extension_mode=extension_mode,
                            )
                            if payload.get("status") == "SKIPPED_CASE_CAP":
                                continue
                            results["file"][key] = payload
                            if include_extensions and extension_mode == "enabled":
                                results["extensions"][key] = payload

        for case in multi_destination_cases:
            if not isinstance(case, dict):
                continue
            sink = str(case.get("sink", "console"))
            log_format = str(case.get("format", "plain-text"))
            extras_raw = case.get("extras", [])
            extras: list[tuple[str, str]] = []
            if isinstance(extras_raw, list):
                for item in extras_raw:
                    if isinstance(item, list) and len(item) == 2:
                        extras.append((str(item[0]), str(item[1])))
                    elif isinstance(item, tuple) and len(item) == 2:
                        extras.append((str(item[0]), str(item[1])))
            for logger_type in logger_types:
                if not self._is_sink_compatible(logger_type, sink):
                    continue
                for customization in customizations:
                    compatible_extras = [
                        (extra_sink, extra_format)
                        for extra_sink, extra_format in extras
                        if self._is_sink_compatible(logger_type, extra_sink)
                    ]
                    config = self._create_output_matrix_config(
                        sink=sink,
                        logger_type=logger_type,
                        log_format=log_format,
                        customization=customization,
                        config_name="multi",
                        multi_destinations=compatible_extras,
                    )
                    key = f"{logger_type}:{sink}:{log_format}:{customization}:multi"
                    results["multi_destination"][key] = await _run_case(
                        sink=sink,
                        logger_type=logger_type,
                        log_format=log_format,
                        customization=customization,
                        config_name="multi",
                        config=config,
                    )
                    if results["multi_destination"][key].get("status") == "SKIPPED_CASE_CAP":
                        del results["multi_destination"][key]

        print(
            f"   Console matrix cases: {len(results['console'])}, "
            f"file matrix cases: {len(results['file'])}, "
            f"multi-destination cases: {len(results['multi_destination'])}"
        )
        print("   Output Matrix Performance: COMPLETED")
        return results

    def _rebase_file_destinations_to_benchmark_logs(
        self, config: LoggingConfig, config_name: str
    ) -> LoggingConfig:
        """Copy config and redirect file destinations into benchmark/bench_logs."""
        return rebase_file_destinations_to_benchmark_logs(
            config=config,
            config_name=config_name,
            build_log_path=self._build_benchmark_log_path,
        )

    @staticmethod
    def _disable_direct_io_if_available(logger: Any) -> None:
        """Force-disable composite direct-I/O fallback when logger supports it."""
        disable_direct_io_if_available(logger)

    def _ensure_composite_file_target(self, logger: Any, prefix: str) -> None:
        """Attach a file-path component shim so composite fallback writes into bench_logs."""
        ensure_composite_file_target(
            logger=logger,
            prefix=prefix,
            build_log_path=self._build_benchmark_log_path,
        )

    def _flush_all_handlers(self, logger):
        """Flush all synchronous handlers in a logger.

        Async handlers must be flushed separately using _flush_all_handlers_async.
        """
        try:
            handlers = []

            # Collect layer handlers
            if hasattr(logger, "_layer_handlers"):
                for handlers_list in logger._layer_handlers.values():
                    handlers.extend(handlers_list)

            # Collect direct handlers
            if hasattr(logger, "_handlers"):
                direct_handlers = logger._handlers
                if isinstance(direct_handlers, dict):
                    handlers.extend(direct_handlers.values())

            # Flush synchronous handlers only
            for handler in handlers:
                if hasattr(handler, "force_flush"):
                    if asyncio.iscoroutinefunction(handler.force_flush):
                        continue  # Skip async handlers
                    handler.force_flush()
                elif hasattr(handler, "flush"):
                    if asyncio.iscoroutinefunction(handler.flush):
                        continue  # Skip async handlers
                    handler.flush()
        except Exception:
            pass

    async def _flush_all_handlers_async(self, logger):
        """Flush all handlers in a logger, including async handlers."""
        try:
            handlers = []
            direct_handlers = getattr(logger, "_handlers", {})
            if isinstance(direct_handlers, dict):
                handlers.extend(direct_handlers.values())

            layer_handlers = getattr(logger, "_layer_handlers", {})
            for handlers_list in layer_handlers.values():
                handlers.extend(handlers_list)

            # Flush handlers (await async ones)
            flush_tasks = []
            for handler in handlers:
                if hasattr(handler, "flush"):
                    if asyncio.iscoroutinefunction(handler.flush):
                        flush_tasks.append(handler.flush())
                    else:
                        handler.flush()
                elif hasattr(handler, "force_flush"):
                    if asyncio.iscoroutinefunction(handler.force_flush):
                        flush_tasks.append(handler.force_flush())
                    else:
                        handler.force_flush()

            # Await all async flushes in parallel
            if flush_tasks:
                await asyncio.gather(*flush_tasks, return_exceptions=True)
        except Exception:
            pass

    async def _wait_for_async_handlers(self, logger, timeout: float = 2.0) -> None:
        """Wait for async handlers to complete processing.

        Uses queue polling and async synchronization. Waits until all message
        queues are empty and handlers are done.

        Args:
            logger: Logger instance with async handlers
            timeout: Maximum time to wait (default: 2.0 seconds)
        """
        try:
            handlers = []
            # Collect all handlers
            if hasattr(logger, "_handlers"):
                handlers.extend(logger._handlers.values())
            if hasattr(logger, "_layer_handlers"):
                for handlers_list in logger._layer_handlers.values():
                    handlers.extend(handlers_list)

            # Check for async handlers with queues
            async_handlers = []
            for handler in handlers:
                # Check if handler has async queue
                if hasattr(handler, "_message_queue"):
                    async_handlers.append(handler)
                # Also check for worker tasks
                if hasattr(handler, "_worker_tasks") or hasattr(
                    handler, "_worker_task"
                ):
                    async_handlers.append(handler)

            if not async_handlers:
                # No async handlers, just flush sync handlers
                self._flush_all_handlers(logger)
                return

            # Poll queues until empty or timeout
            start_time = time.perf_counter()
            max_iterations = 100  # Prevent infinite loop
            iteration = 0

            while iteration < max_iterations:
                iteration += 1
                elapsed = time.perf_counter() - start_time

                if elapsed >= timeout:
                    break

                # Check all async handler queues
                all_queues_empty = True
                for handler in async_handlers:
                    queue = getattr(handler, "_message_queue", None)
                    if queue is not None:
                        queue_size = queue.qsize()
                        if queue_size > 0:
                            all_queues_empty = False
                            break

                    # Also check message buffers
                    buffer = getattr(handler, "_message_buffer", None)
                    if buffer and len(buffer) > 0:
                        all_queues_empty = False
                        break

                if all_queues_empty:
                    # All queues empty, wait briefly for any final processing
                    await asyncio.sleep(0.01)
                    # Double-check one more time
                    still_empty = True
                    for handler in async_handlers:
                        queue = getattr(handler, "_message_queue", None)
                        if queue and queue.qsize() > 0:
                            still_empty = False
                            break
                    if still_empty:
                        break

                # Brief yield to let handlers process
                await asyncio.sleep(0.01)

            # Flush async handlers after waiting for queues
            await self._flush_all_handlers_async(logger)

        except Exception:
            # Fallback: try to flush if detection fails
            try:
                await self._flush_all_handlers_async(logger)
            except Exception:
                # Last resort: flush sync handlers only
                self._flush_all_handlers(logger)

    def _cleanup_logger_cache(self):
        """Remove all benchmark loggers from global cache to prevent state pollution."""
        try:
            for logger_name in self._logger_names:
                try:
                    removeLogger(logger_name)
                except Exception:
                    pass
            self._logger_names.clear()
        except Exception:
            pass

    async def _final_cleanup(self):
        """Dynamic cleanup: close all loggers, await all handler tasks, and clear cache."""
        try:
            loop = asyncio.get_running_loop()

            # Step 1: Close all tracked loggers properly
            close_tasks = []
            for logger in self._created_loggers:
                try:
                    if hasattr(logger, "aclose") and asyncio.iscoroutinefunction(
                        logger.aclose
                    ):
                        close_tasks.append(logger.aclose())
                    elif hasattr(logger, "close_async") and asyncio.iscoroutinefunction(
                        logger.close_async
                    ):
                        close_tasks.append(logger.close_async())
                    elif hasattr(logger, "close") and callable(logger.close):
                        if not asyncio.iscoroutinefunction(logger.close):
                            logger.close()
                except Exception:
                    pass

            # Wait for all loggers to close
            if close_tasks:
                try:
                    await asyncio.gather(*close_tasks, return_exceptions=True)
                except Exception:
                    pass

            # Step 2: Collect all handler worker tasks from all loggers
            handler_tasks = []
            for logger in self._created_loggers:
                try:
                    # Get all handlers from logger
                    handlers = []
                    if hasattr(logger, "_handlers"):
                        handlers.extend(logger._handlers.values())
                    if hasattr(logger, "_console_handler") and logger._console_handler:
                        handlers.append(logger._console_handler)
                    if hasattr(logger, "components"):
                        for component in logger.components:
                            if hasattr(component, "_handlers"):
                                handlers.extend(component._handlers.values())
                            if (
                                hasattr(component, "_console_handler")
                                and component._console_handler
                            ):
                                handlers.append(component._console_handler)

                    # Collect worker tasks from handlers
                    for handler in handlers:
                        if (
                            hasattr(handler, "_worker_task")
                            and handler._worker_task
                            and not handler._worker_task.done()
                        ):
                            handler_tasks.append(handler._worker_task)
                        if hasattr(handler, "_worker_tasks") and handler._worker_tasks:
                            handler_tasks.extend(
                                [t for t in handler._worker_tasks if not t.done()]
                            )
                except Exception:
                    pass

            # Step 3: Also collect any remaining tasks in the event loop
            all_loop_tasks = [
                t
                for t in asyncio.all_tasks(loop)
                if t != asyncio.current_task() and not t.done()
            ]

            # Combine and deduplicate
            all_tasks = list(set(handler_tasks + all_loop_tasks))

            if not all_tasks:
                return

            # Step 4: Adaptive waiting - check completion status dynamically
            max_wait_time = 2.0
            check_interval = 0.05
            elapsed = 0.0

            while elapsed < max_wait_time:
                done_tasks = [t for t in all_tasks if t.done()]
                if len(done_tasks) == len(all_tasks):
                    break
                await asyncio.sleep(check_interval)
                elapsed += check_interval

            # Step 5: Cancel and await any remaining tasks
            remaining = [t for t in all_tasks if not t.done()]
            if remaining:
                for task in remaining:
                    task.cancel()
                try:
                    await asyncio.wait(
                        remaining, timeout=0.5, return_when=asyncio.ALL_COMPLETED
                    )
                except Exception:
                    pass
                for task in remaining:
                    if not task.done():
                        try:
                            await asyncio.gather(task, return_exceptions=True)
                        except Exception:
                            pass

            # Step 6: Remove all loggers from global cache to prevent state pollution
            self._cleanup_logger_cache()

            # Step 7: Force garbage collection to free memory
            gc.collect()

        except RuntimeError:
            pass
        except Exception:
            pass
        finally:
            # Always cleanup cache, even on error
            self._cleanup_logger_cache()

            # Keep benchmark logs for debugging and comparison between runs.

    def print_header(self):
        """Print benchmark header information."""
        print("=" * 80)
        print("HYDRA-LOGGER PERFORMANCE BENCHMARK")
        print("=" * 80)
        if self.profile_name:
            print(f"Profile: {self.profile_name}")
        print(f"Test Configuration:")
        print(
            f"   Typical Single Messages: {self.test_config['typical_single_messages']:,}"
        )
        print(f"   Small Batch Size: {self.test_config['small_batch_size']:,}")
        print(f"   Medium Batch Size: {self.test_config['medium_batch_size']:,}")
        print(f"   Large Batch Size: {self.test_config['large_batch_size']:,}")
        print(f"   Concurrent Workers: {self.test_config['concurrent_workers']}")
        print(f"   Messages per Worker: {self.test_config['messages_per_worker']:,}")
        print(
            f"   Async/Parallel Matrix: {self.test_config['suite_matrix_workers_tasks']}"
        )
        print(
            f"   Matrix Messages/Worker: {self.test_config['suite_matrix_messages_per_worker']:,}"
        )
        print(f"   Repetitions: {self.test_config.get('repetitions', 1)}")
        print(f"   Scenario Parameters:")
        print(
            f"     - Web Request Logs: {self.test_config['web_request_logs']} msgs/request"
        )
        print(
            f"     - DB Operation Logs: {self.test_config['database_operation_logs']} msgs/op"
        )
        print(
            f"     - Background Task Logs: {self.test_config['background_task_logs']} msgs/task"
        )
        print("=" * 80)

    def _extract_primary_metrics(self, result: Dict[str, Any]) -> dict[str, float]:
        """Extract comparable primary metrics from a scenario payload."""
        if not isinstance(result, dict):
            return {"duration": 0.0}
        if "individual_messages_per_second" in result:
            return {
                "duration": float(result.get("individual_duration", 0.0)),
                "messages_per_second": float(result.get("individual_messages_per_second", 0.0)),
            }
        if "messages_per_second" in result:
            return {
                "duration": float(result.get("duration", 0.0)),
                "messages_per_second": float(result.get("messages_per_second", 0.0)),
            }
        if "total_messages_per_second" in result:
            return {
                "duration": float(result.get("total_duration", 0.0)),
                "messages_per_second": float(result.get("total_messages_per_second", 0.0)),
            }
        return {"duration": float(result.get("duration", 0.0))}

    def _attach_repetition_stats(
        self, *, section: str, result: Dict[str, Any], runs: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Attach repetition summaries and sample-duration checks to scenario payload."""
        duration_samples: list[float] = []
        rate_samples: list[float] = []
        for item in runs:
            metrics = self._extract_primary_metrics(item)
            duration_samples.append(float(metrics.get("duration", 0.0)))
            if "messages_per_second" in metrics:
                rate_samples.append(float(metrics["messages_per_second"]))
        result["repetition_runs"] = len(runs)
        result["repetition_stats"] = {
            "durations": summarize_samples(duration_samples),
            "messages_per_second": summarize_samples(rate_samples),
        }
        if duration_samples and max(duration_samples) > 0:
            duration_now = float(self._extract_primary_metrics(result).get("duration", 0.0))
            result["minimum_sample_duration_seconds"] = self.min_sample_duration_seconds
            result["minimum_sample_duration_passed"] = (
                duration_now >= self.min_sample_duration_seconds
            )
            violation = validate_sample_duration(
                section=section,
                duration=duration_now,
                min_duration_seconds=self.min_sample_duration_seconds,
            )
            if violation:
                result["sample_duration_violation"] = violation
        return result

    def _run_repeated_sync(
        self, *, section: str, scenario: Any, repeat: int | None = None
    ) -> Dict[str, Any]:
        """Run sync scenario multiple times and aggregate repetition statistics."""
        configured_repeat = int(self.test_config.get("repetitions", 1))
        if self.repetition_sections and section not in self.repetition_sections:
            configured_repeat = 1
        total_runs = max(1, int(repeat if repeat is not None else configured_repeat))
        runs: list[Dict[str, Any]] = []
        for _ in range(total_runs):
            payload = scenario()
            runs.append(payload if isinstance(payload, dict) else {"value": payload})
            self._cleanup_logger_cache()
        return self._attach_repetition_stats(section=section, result=runs[-1], runs=runs)

    async def _run_repeated_async(
        self, *, section: str, scenario: Any, repeat: int | None = None
    ) -> Dict[str, Any]:
        """Run async scenario multiple times and aggregate repetition statistics."""
        configured_repeat = int(self.test_config.get("repetitions", 1))
        if self.repetition_sections and section not in self.repetition_sections:
            configured_repeat = 1
        total_runs = max(1, int(repeat if repeat is not None else configured_repeat))
        runs: list[Dict[str, Any]] = []
        for _ in range(total_runs):
            payload = await scenario()
            runs.append(payload if isinstance(payload, dict) else {"value": payload})
            self._cleanup_logger_cache()
        return self._attach_repetition_stats(section=section, result=runs[-1], runs=runs)

    def test_sync_logger_performance(self) -> Dict[str, Any]:
        """
        Test synchronous logger performance.

        Returns:
            Dict containing performance metrics for sync logger
        """
        print("\nTesting Sync Logger Performance...")
        print("   Testing individual message throughput...")

        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_sync_{id(self)}"
        perf_config = self._create_performance_config(logger_type="sync")
        logger = getSyncLogger(logger_name, config=perf_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config["typical_single_messages"]

        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Processing request {i} for user_id=12345",
                f"Database query completed in {i*0.001:.3f}s, rows={i%100}",
                f"API endpoint /api/v1/users called, response_code=200, duration={i}ms",
                f"Cache hit for key 'user:12345:profile', ttl={i*60}s",
                f"Background job 'process_payment' started, job_id={i}",
                f"Error occurred: Connection timeout after {i*10}ms retries",
            ]
            return patterns[i % len(patterns)]

        # Warm-up period to avoid initialization overhead
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        for i in range(warmup_count):
            logger.info(generate_realistic_message(i))

        # Force flush before timing starts
        self._flush_all_handlers(logger)
        time.sleep(0.5)  # Pause for file I/O to complete

        # Test with realistic messages
        start_time = time.perf_counter()
        for i in range(message_count):
            logger.info(generate_realistic_message(i))
        # Force flush after logging to include I/O in timing
        self._flush_all_handlers(logger)
        # Force OS-level sync to ensure all file I/O completes
        import os as os_module

        try:
            for handler in getattr(logger, "_layer_handlers", {}).get("default", []):
                if hasattr(handler, "_file_handle") and handler._file_handle:
                    try:
                        handler._file_handle.flush()
                        os_module.fsync(handler._file_handle.fileno())
                    except (AttributeError, OSError):
                        pass
        except Exception:
            pass
        # End timing BEFORE sleep to measure actual logging performance (not I/O wait time)
        end_time = time.perf_counter()

        duration = end_time - start_time
        messages_per_second = message_count / duration

        # Wait for file I/O to complete (for accurate byte counting, not performance measurement)
        time.sleep(0.5)

        # Cleanup
        composite_health = logger.get_health_status()
        try:
            logger.close()
        except Exception:
            pass

        result = {
            "logger_type": "Sync Logger",
            "individual_messages_per_second": messages_per_second,
            "individual_duration": duration,
            "total_messages": message_count,
            "status": "COMPLETED",
        }

        print(f"   Individual Messages: {messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")
        print("   Sync Logger: COMPLETED")

        return result

    def test_network_destination_performance(self) -> Dict[str, Any]:
        """
        Test typed network destination routing with deterministic local stubbing.

        Returns:
            Dict containing routing throughput and stub dispatch evidence.
        """
        print("\nTesting Network Destination Routing Performance...")
        logger_name = f"benchmark_network_route_{id(self)}"
        message_count = min(5000, int(self.test_config["typical_single_messages"]))
        dispatched = {"count": 0}

        class _StubNetworkHandler:
            def __init__(self) -> None:
                self.formatter = None

            def setFormatter(self, formatter) -> None:  # type: ignore[no-untyped-def]
                self.formatter = formatter

            def emit(self, _record) -> None:  # type: ignore[no-untyped-def]
                dispatched["count"] += 1

            def close(self) -> None:
                return None

        from hydra_logger.handlers.network_handler import NetworkHandlerFactory

        original_create_http = NetworkHandlerFactory.create_http_handler
        NetworkHandlerFactory.create_http_handler = staticmethod(
            lambda **_kwargs: _StubNetworkHandler()
        )
        try:
            config = LoggingConfig(
                default_level="INFO",
                enable_security=False,
                enable_sanitization=False,
                enable_plugins=False,
                enable_performance_monitoring=False,
                layers={
                    "default": LogLayer(
                        level="INFO",
                        destinations=[
                            LogDestination(
                                type="network_http",
                                url="https://localhost/benchmark-ingest",
                                format="plain-text",
                            )
                        ],
                    )
                },
            )
            logger = getSyncLogger(logger_name, config=config)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)

            start_time = time.perf_counter()
            for idx in range(message_count):
                logger.info(f"network benchmark message {idx}")
            self._flush_all_handlers(logger)
            end_time = time.perf_counter()

            try:
                logger.close()
            except Exception:
                pass
        finally:
            NetworkHandlerFactory.create_http_handler = original_create_http

        duration = max(end_time - start_time, 1e-9)
        throughput = message_count / duration
        result = {
            "logger_type": "Network Destination Routing",
            "individual_messages_per_second": throughput,
            "individual_duration": duration,
            "total_messages": message_count,
            "dispatched_messages": dispatched["count"],
            "status": "COMPLETED",
        }
        print(f"   Network destination routed messages: {dispatched['count']}")
        print(f"   Throughput: {throughput:,.0f} msg/s")
        print("   Network Destination Routing: COMPLETED")
        return result

    async def test_async_logger_performance(self) -> Dict[str, Any]:
        """
        Test asynchronous logger performance.

        Returns:
            Dict containing performance metrics for async logger
        """
        print("\nTesting Async Logger Performance...")
        print("   Testing individual message throughput...")

        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_async_{id(self)}"
        perf_config = self._create_performance_config(logger_type="async")
        logger = getAsyncLogger(logger_name, config=perf_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config["typical_single_messages"]

        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Async task {i} completed: processed {i*10} items",
                f"WebSocket message received: channel='notifications', size={i*50}B",
                f"Event loop processing: {i} pending tasks, queue_size={i%50}",
                f"HTTP client request to api.example.com: GET /users/{i}, status=200",
                f"Async cache operation: key='session:{i}', hit={'true' if i%2==0 else 'false'}",
                f"Background worker processing job batch {i}, progress={i}%",
            ]
            return patterns[i % len(patterns)]

        # Warm-up period
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_tasks = []
        for i in range(warmup_count):
            warmup_tasks.append(logger.log("INFO", generate_realistic_message(i)))
        await asyncio.gather(*warmup_tasks)

        # Wait for warm-up handlers to complete
        await self._wait_for_async_handlers(logger, timeout=1.0)

        # Batch task creation for large message counts
        start_time = time.perf_counter()

        # For large batches, create tasks in chunks to reduce overhead
        if message_count > 10000:
            chunk_size = 10000
            for chunk_start in range(0, message_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, message_count)
                tasks = [
                    logger.log("INFO", generate_realistic_message(i))
                    for i in range(chunk_start, chunk_end)
                ]
                await asyncio.gather(*tasks)
        else:
            # Small batches: create all tasks at once
            tasks = [
                logger.log("INFO", generate_realistic_message(i))
                for i in range(message_count)
            ]
            await asyncio.gather(*tasks)

        # End timing BEFORE close to measure actual logging performance (not cleanup)
        end_time = time.perf_counter()

        duration = end_time - start_time
        messages_per_second = message_count / duration

        # Logger-core async path: avoids extra task scheduling in logger.log()
        core_start_time = time.perf_counter()
        if message_count > 10000:
            chunk_size = 10000
            for chunk_start in range(0, message_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, message_count)
                core_tasks = [
                    logger.log_async("INFO", generate_realistic_message(i))
                    for i in range(chunk_start, chunk_end)
                ]
                await asyncio.gather(*core_tasks)
        else:
            core_tasks = [
                logger.log_async("INFO", generate_realistic_message(i))
                for i in range(message_count)
            ]
            await asyncio.gather(*core_tasks)
        core_end_time = time.perf_counter()
        core_duration = core_end_time - core_start_time
        core_messages_per_second = message_count / core_duration

        # Close logger after timing (cleanup doesn't affect performance measurement)
        # Standard: use aclose() first (standard async context manager protocol)
        # Fallback: use close_async() for backward compatibility
        if hasattr(logger, "aclose") and asyncio.iscoroutinefunction(logger.aclose):
            await logger.aclose()
        elif hasattr(logger, "close_async") and asyncio.iscoroutinefunction(
            logger.close_async
        ):
            await logger.close_async()

        result = {
            "logger_type": "Async Logger",
            "individual_messages_per_second": messages_per_second,
            "individual_duration": duration,
            "task_fanout_messages_per_second": messages_per_second,
            "task_fanout_duration": duration,
            "logger_core_messages_per_second": core_messages_per_second,
            "logger_core_duration": core_duration,
            "total_messages": message_count,
            "status": "COMPLETED",
        }

        print(f"   Individual Messages: {messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")
        print(f"   Logger Core Async: {core_messages_per_second:,.0f} msg/s")
        print(f"   Logger Core Duration: {core_duration:.3f}s")
        print("   Async Logger: COMPLETED")

        return result

    def test_composite_logger_performance(self) -> Dict[str, Any]:
        """
        Test composite logger performance.

        Returns:
            Dict containing performance metrics for composite logger
        """
        print("\nTesting Composite Logger Performance...")
        print("   Testing individual message throughput...")

        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_composite_{id(self)}"
        perf_config = self._create_performance_config(logger_type="sync")
        logger = getLogger(
            logger_name,
            logger_type="composite",
            config=perf_config,
            use_direct_io=False,
        )
        self._disable_direct_io_if_available(logger)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config["typical_single_messages"]

        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Composite logger: Processing transaction {i}, amount=${i*10.50:.2f}",
                f"Multi-handler log: User action 'view_profile' by user_id={i}",
                f"Composite output: API rate limit check, remaining={1000-i}",
                f"Multi-destination: Audit log entry {i} for compliance tracking",
                f"Composite sync: Payment processed for order_id={i}, status='completed'",
            ]
            return patterns[i % len(patterns)]

        # Warm-up
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_start = time.perf_counter()
        for i in range(warmup_count):
            logger.info(generate_realistic_message(i))
        warmup_duration = time.perf_counter() - warmup_start

        # Flush before timing
        self._flush_all_handlers(logger)
        time.sleep(0.5)

        # Test with realistic messages
        start_time = time.perf_counter()
        for i in range(message_count):
            logger.info(generate_realistic_message(i))
        # Flush after logging
        self._flush_all_handlers(logger)
        # Force OS-level sync
        import os as os_module

        try:
            for handler in getattr(logger, "_layer_handlers", {}).get("default", []):
                if hasattr(handler, "_file_handle") and handler._file_handle:
                    try:
                        handler._file_handle.flush()
                        os_module.fsync(handler._file_handle.fileno())
                    except (AttributeError, OSError):
                        pass
        except Exception:
            pass
        # End timing BEFORE sleep to measure actual logging performance (not I/O wait time)
        end_time = time.perf_counter()

        duration = end_time - start_time
        individual_messages_per_second = message_count / duration

        # Wait for file I/O to complete (for accurate byte counting, not performance measurement)
        time.sleep(0.5)

        print(f"   Individual Messages: {individual_messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")

        # Test with batch sizes
        print("   Testing small batch...")
        batch_size = self.test_config["small_batch_size"]
        messages = build_batch_messages(batch_size, generate_realistic_message)

        (
            small_batch_total_messages,
            small_batch_duration,
            small_batch_messages_per_second,
        ) = self._measure_sync_batch_throughput(logger, messages)

        print(
            f"   Small Batch ({batch_size} msgs): {small_batch_messages_per_second:,.0f} msg/s"
        )

        # Test medium batch
        print("   Testing medium batch...")
        batch_size = self.test_config["medium_batch_size"]
        messages = build_batch_messages(batch_size, generate_realistic_message)

        (
            medium_batch_total_messages,
            batch_duration,
            batch_messages_per_second,
        ) = self._measure_sync_batch_throughput(logger, messages)
        composite_health = logger.get_health_status()

        # Cleanup
        try:
            logger.close()
        except Exception:
            pass

        result = {
            "logger_type": "Composite Logger",
            "individual_messages_per_second": individual_messages_per_second,
            "small_batch_messages_per_second": small_batch_messages_per_second,
            "batch_messages_per_second": batch_messages_per_second,
            "individual_duration": duration,
            "small_batch_duration": small_batch_duration,
            "batch_duration": batch_duration,
            "total_messages": message_count,
            "small_batch_size": self.test_config["small_batch_size"],
            "small_batch_total_messages": small_batch_total_messages,
            "batch_size": batch_size,
            "batch_total_messages": medium_batch_total_messages,
            "batch_dispatch_errors": composite_health.get("batch_dispatch_errors", 0),
            "status": "COMPLETED",
        }

        print(f"   Medium Batch Messages: {batch_messages_per_second:,.0f} msg/s")
        print(f"   Medium Batch Duration: {batch_duration:.3f}s")
        print("   Composite Logger: COMPLETED")

        return result

    async def test_composite_async_logger_performance(self) -> Dict[str, Any]:
        """
        Test composite async logger performance.

        Returns:
            Dict containing performance metrics for composite async logger
        """
        print("\nTesting Composite Async Logger Performance...")
        print("   Testing individual message throughput...")

        # Use unique logger name to avoid cache conflicts
        # Use file-only config for performance (console I/O is slow)
        logger_name = f"benchmark_composite_async_{id(self)}"
        perf_config = self._create_performance_config(logger_type="async")
        logger = getLogger(
            logger_name,
            logger_type="composite-async",
            config=perf_config,
            use_direct_io=False,
        )
        self._disable_direct_io_if_available(logger)
        self._ensure_composite_file_target(logger, prefix=logger_name)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config["typical_single_messages"]

        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Async composite: WebSocket message broadcast to {i} clients",
                f"Multi-handler async: Background job completed, processed {i*5} items",
                f"Async composite: API request routed to service {i%3}, latency={i}ms",
                f"Composite async: Event stream processing, event_id={i}, size={i*100}B",
                f"Multi-destination async: Audit log entry {i} written to multiple targets",
            ]
            return patterns[i % len(patterns)]

        # Warm-up period
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_tasks = []
        for i in range(warmup_count):
            warmup_tasks.append(logger.log("INFO", generate_realistic_message(i)))
        await asyncio.gather(*warmup_tasks)

        # Wait for warm-up handlers to complete
        await self._wait_for_async_handlers(logger, timeout=1.0)

        # Batch task creation for large message counts
        start_time = time.perf_counter()

        # For large batches, create tasks in chunks to reduce overhead
        if message_count > 10000:
            chunk_size = 10000
            for chunk_start in range(0, message_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, message_count)
                tasks = [
                    logger.log("INFO", generate_realistic_message(i))
                    for i in range(chunk_start, chunk_end)
                ]
                await asyncio.gather(*tasks)
        else:
            # Small batches: create all tasks at once
            tasks = [
                logger.log("INFO", generate_realistic_message(i))
                for i in range(message_count)
            ]
            await asyncio.gather(*tasks)

        # End timing BEFORE close to measure actual logging performance (not cleanup)
        end_time = time.perf_counter()

        duration = end_time - start_time
        individual_messages_per_second = message_count / duration

        print(f"   Individual Messages: {individual_messages_per_second:,.0f} msg/s")
        print(f"   Duration: {duration:.3f}s")

        # Test with batch sizes
        print("   Testing small batch...")
        batch_size = self.test_config["small_batch_size"]
        messages = build_batch_messages(batch_size, generate_realistic_message)

        (
            batch_total_messages,
            batch_duration,
            batch_messages_per_second,
        ) = await self._measure_async_batch_throughput(logger, messages)

        # Close logger after timing (cleanup doesn't affect performance measurement)
        # Standard: use aclose() first (standard async context manager protocol)
        # Fallback: use close_async() for backward compatibility
        if hasattr(logger, "aclose") and asyncio.iscoroutinefunction(logger.aclose):
            await logger.aclose()
        elif hasattr(logger, "close_async") and asyncio.iscoroutinefunction(
            logger.close_async
        ):
            await logger.close_async()

        result = {
            "logger_type": "Composite Async Logger",
            "individual_messages_per_second": individual_messages_per_second,
            "batch_messages_per_second": batch_messages_per_second,
            "individual_duration": duration,
            "batch_duration": batch_duration,
            "total_messages": message_count,
            "batch_size": batch_size,
            "batch_total_messages": batch_total_messages,
            "status": "COMPLETED",
        }

        print(f"   Batch Messages: {batch_messages_per_second:,.0f} msg/s")
        print(f"   Batch Duration: {batch_duration:.3f}s")
        print("   Composite Async Logger: COMPLETED")

        return result

    def test_file_writing_performance(self) -> Dict[str, Any]:
        """
        Test file writing performance (file handlers only).

        Returns:
            Dict containing file writing performance metrics
        """
        print("\nTesting File Writing Performance...")
        print("   Testing file handler I/O performance...")

        import os

        from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer

        benchmark_file = self._build_benchmark_log_path("benchmark_file")
        jsonl_candidate_path = str(Path(benchmark_file).with_suffix(".jsonl"))

        # Create configuration with FILE ONLY (no console)
        file_only_config = LoggingConfig(
            default_level="INFO",
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="file",
                            path=benchmark_file,
                            format="json-lines",
                        ),
                    ],
                )
            },
        )

        # Use unique logger name to avoid cache conflicts
        logger_name = f"benchmark_file_{id(self)}"
        logger = getLogger(logger_name, config=file_only_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config["typical_single_messages"]

        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"File write test: Processing request {i} for user_id=12345",
                f"File I/O: Database query completed in {i*0.001:.3f}s, rows={i%100}",
                f"File log: API endpoint /api/v1/users called, response_code=200, duration={i}ms",
                f"File write: Cache hit for key 'user:12345:profile', ttl={i*60}s",
                f"File handler: Background job 'process_payment' started, job_id={i}",
                f"File output: Error occurred: Connection timeout after {i*10}ms retries",
            ]
            return patterns[i % len(patterns)]

        # Warm-up
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_start = time.perf_counter()
        for i in range(warmup_count):
            logger.info(generate_realistic_message(i))
        warmup_duration = time.perf_counter() - warmup_start

        # Flush before timing
        self._flush_all_handlers(logger)
        time.sleep(0.5)
        baseline_emitted = extract_handler_messages_emitted(logger)
        baseline_line_counts = {
            benchmark_file: self._count_written_lines(benchmark_file),
            jsonl_candidate_path: self._count_written_lines(jsonl_candidate_path),
        }

        # Initialize initial_size to avoid undefined variable
        initial_size = 0
        if os.path.exists(benchmark_file):
            initial_size = os.path.getsize(benchmark_file)
            print(f"   Warm-up wrote {initial_size:,} bytes to file")
        else:
            print("   Warning: File not created during warm-up, will measure from zero")

        # Test file writing performance
        print("   Testing file writing performance...")
        start_time = time.perf_counter()
        for i in range(message_count):
            logger.info(generate_realistic_message(i))

        # Flush after logging to ensure all data is written
        flush_start = time.perf_counter()
        self._flush_all_handlers(logger)
        flush_duration = time.perf_counter() - flush_start

        # Force OS-level sync and wait for I/O to complete
        import os as os_module

        try:
            for handler in getattr(logger, "_layer_handlers", {}).get("default", []):
                if hasattr(handler, "_file_handle") and handler._file_handle:
                    try:
                        handler._file_handle.flush()
                        os_module.fsync(handler._file_handle.fileno())
                    except (AttributeError, OSError):
                        pass
                # Also check handler stats for bytes written
                if hasattr(handler, "get_stats"):
                    stats = handler.get_stats()
                    if "total_bytes_written" in stats:
                        print(
                            f"   Handler reports {stats['total_bytes_written']:,} bytes written"
                        )
        except Exception:
            pass

        # End timing BEFORE sleep to measure actual logging performance (not I/O wait time)
        end_time = time.perf_counter()

        # Wait for file system to sync (for accurate byte counting, not performance measurement)
        time.sleep(0.5)

        # Get bytes written from handler stats (more reliable than file size).
        handler_bytes = extract_handler_bytes_written(logger)
        observed_emitted = extract_handler_messages_emitted(logger)
        actual_emitted = max(0, observed_emitted - baseline_emitted)
        if actual_emitted <= 0:
            actual_emitted = message_count
            actual_emitted_source = "fallback_expected"
        else:
            actual_emitted_source = "handler_counter"
        resolved_file_path = (
            self._resolve_output_matrix_file_path(benchmark_file, "json-lines") or benchmark_file
        )
        baseline_written_lines = baseline_line_counts.get(resolved_file_path, 0)
        byte_summary = resolve_bytes_written(
            file_path=resolved_file_path,
            initial_size=initial_size,
            handler_bytes=handler_bytes,
        )
        bytes_written = int(byte_summary["bytes_written"])
        if bool(byte_summary["file_exists"]):
            final_size = int(byte_summary["final_size"])
            file_bytes = int(byte_summary["file_bytes"])
            print(f"   Initial file size: {initial_size:,} bytes")
            print(f"   Final file size: {final_size:,} bytes")
            print(f"   Handler bytes written: {handler_bytes:,} bytes")
            print(f"   File size increase: {file_bytes:,} bytes")
            print(f"   Total bytes written: {bytes_written:,} bytes")
            if bytes_written <= 0:
                print("   Warning: No bytes written. File I/O may not have completed.")
        else:
            # File doesn't exist, but handler might have stats
            bytes_written = handler_bytes
            if bytes_written > 0:
                print(
                    f"   Handler reports {bytes_written:,} bytes written (file not yet created)"
                )
            else:
                print("   Error: File was not created and handler has no stats")
                bytes_written = 0

        duration = end_time - start_time
        final_written_lines = self._count_written_lines(resolved_file_path)
        observed_written_lines = resolve_written_line_delta(
            baseline_lines=baseline_written_lines,
            final_lines=final_written_lines,
        )
        result = build_file_io_result(
            logger_type="File Handler Only",
            total_messages=message_count,
            duration=duration,
            warmup_duration=warmup_duration,
            flush_duration=flush_duration,
            bytes_written=bytes_written,
            written_lines=observed_written_lines,
            file_path=resolved_file_path,
            actual_emitted=actual_emitted,
            actual_emitted_source=actual_emitted_source,
            strict_file_evidence=True,
        )
        messages_per_second = float(result["messages_per_second"])
        bytes_per_second = float(result["bytes_per_second"])

        # Cleanup
        try:
            logger.close()
        except Exception:
            pass

        print(f"   File Writing: {messages_per_second:,.0f} msg/s")
        print(f"   File I/O Speed: {bytes_per_second:,.0f} bytes/s")
        print(f"   Duration: {duration:.3f}s")
        print("   File Writing: COMPLETED")

        return result

    async def test_async_file_writing_performance(self) -> Dict[str, Any]:
        """
        Test async file writing performance (async file handlers only).

        Returns:
            Dict containing async file writing performance metrics
        """
        print("\nTesting Async File Writing Performance...")
        print("   Testing async file handler I/O performance...")

        import os

        from hydra_logger.config.models import LogDestination, LoggingConfig, LogLayer

        benchmark_file = self._build_benchmark_log_path("benchmark_async_file")
        jsonl_candidate_path = str(Path(benchmark_file).with_suffix(".jsonl"))

        # Create configuration with ASYNC FILE ONLY (no console)
        async_file_only_config = LoggingConfig(
            default_level="INFO",
            layers={
                "default": LogLayer(
                    level="INFO",
                    destinations=[
                        LogDestination(
                            type="async_file",
                            path=benchmark_file,
                            format="json-lines",
                        ),
                    ],
                )
            },
        )

        # Use unique logger name to avoid cache conflicts
        logger_name = f"benchmark_async_file_{id(self)}"
        logger = getAsyncLogger(logger_name, config=async_file_only_config)
        self._created_loggers.append(logger)
        self._logger_names.append(logger_name)
        message_count = self.test_config["typical_single_messages"]

        # Generate test messages
        def generate_realistic_message(i: int) -> str:
            """Generate test log messages."""
            patterns = [
                f"Async file write: Processing async task {i}, processed {i*10} items",
                f"Async file I/O: WebSocket message received, channel='notifications', size={i*50}B",
                f"Async file log: Event loop processing: {i} pending tasks, queue_size={i%50}",
                f"Async file handler: HTTP client request to api.example.com: GET /users/{i}, status=200",
                f"Async file output: Background worker processing job batch {i}, progress={i}%",
            ]
            return patterns[i % len(patterns)]

        # Warm-up
        print("   Warm-up period...")
        warmup_count = min(1000, message_count // 100)
        warmup_start = time.perf_counter()
        warmup_tasks = []
        for i in range(warmup_count):
            warmup_tasks.append(logger.log("INFO", generate_realistic_message(i)))
        await asyncio.gather(*warmup_tasks)
        warmup_duration = time.perf_counter() - warmup_start

        # Wait for warm-up handlers to complete
        await self._wait_for_async_handlers(logger, timeout=1.0)
        baseline_emitted = extract_handler_messages_emitted(logger)
        baseline_line_counts = {
            benchmark_file: self._count_written_lines(benchmark_file),
            jsonl_candidate_path: self._count_written_lines(jsonl_candidate_path),
        }

        # Initialize initial_size to avoid undefined variable
        initial_size = 0
        if os.path.exists(benchmark_file):
            initial_size = os.path.getsize(benchmark_file)
            print(f"   Warm-up wrote {initial_size:,} bytes to file")
        else:
            print("   Warning: File not created during warm-up, will measure from zero")

        # Test async file writing performance
        print("   Testing async file writing performance...")
        start_time = time.perf_counter()

        # Batch task creation for efficiency
        if message_count > 10000:
            chunk_size = 10000
            for chunk_start in range(0, message_count, chunk_size):
                chunk_end = min(chunk_start + chunk_size, message_count)
                tasks = [
                    logger.log("INFO", generate_realistic_message(i))
                    for i in range(chunk_start, chunk_end)
                ]
                await asyncio.gather(*tasks)
        else:
            tasks = [
                logger.log("INFO", generate_realistic_message(i))
                for i in range(message_count)
            ]
            await asyncio.gather(*tasks)

        # End timing BEFORE close/sleep to measure actual logging performance (not cleanup)
        end_time = time.perf_counter()

        # Close logger after timing (cleanup doesn't affect performance measurement)
        print("   Finalizing writes...")
        flush_start = time.perf_counter()
        if hasattr(logger, "close_async"):
            await logger.close_async()
        elif hasattr(logger, "aclose"):
            await logger.aclose()
        else:
            # Fallback: flush handlers manually
            await self._flush_all_handlers_async(logger)
        flush_duration = time.perf_counter() - flush_start

        # Wait for async file operations to complete (for accurate byte counting)
        await asyncio.sleep(0.5)

        # Get bytes written from handler stats (more reliable than file size).
        handler_bytes = extract_handler_bytes_written(logger)
        observed_emitted = extract_handler_messages_emitted(logger)
        actual_emitted = max(0, observed_emitted - baseline_emitted)
        if actual_emitted <= 0:
            actual_emitted = message_count
            actual_emitted_source = "fallback_expected"
        else:
            actual_emitted_source = "handler_counter"
        resolved_file_path = (
            self._resolve_output_matrix_file_path(benchmark_file, "json-lines") or benchmark_file
        )
        baseline_written_lines = baseline_line_counts.get(resolved_file_path, 0)
        byte_summary = resolve_bytes_written(
            file_path=resolved_file_path,
            initial_size=initial_size,
            handler_bytes=handler_bytes,
        )
        bytes_written = int(byte_summary["bytes_written"])
        if bool(byte_summary["file_exists"]):
            final_size = int(byte_summary["final_size"])
            file_bytes = int(byte_summary["file_bytes"])
            print(f"   Initial file size: {initial_size:,} bytes")
            print(f"   Final file size: {final_size:,} bytes")
            print(f"   Handler bytes written: {handler_bytes:,} bytes")
            print(f"   File size increase: {file_bytes:,} bytes")
            print(f"   Total bytes written: {bytes_written:,} bytes")
            if bytes_written <= 0:
                print(
                    "   Warning: No bytes written. Async handlers may not have completed."
                )
        else:
            # File doesn't exist, but handler might have stats
            bytes_written = handler_bytes
            if bytes_written > 0:
                print(
                    f"   Handler reports {bytes_written:,} bytes written (file not yet created)"
                )
            else:
                print("   Error: File was not created and handler has no stats")
                bytes_written = 0

        duration = end_time - start_time
        final_written_lines = self._count_written_lines(resolved_file_path)
        observed_written_lines = resolve_written_line_delta(
            baseline_lines=baseline_written_lines,
            final_lines=final_written_lines,
        )
        result = build_file_io_result(
            logger_type="Async File Handler Only",
            total_messages=message_count,
            duration=duration,
            warmup_duration=warmup_duration,
            flush_duration=flush_duration,
            bytes_written=bytes_written,
            written_lines=observed_written_lines,
            file_path=resolved_file_path,
            actual_emitted=actual_emitted,
            actual_emitted_source=actual_emitted_source,
            strict_file_evidence=True,
        )
        messages_per_second = float(result["messages_per_second"])
        bytes_per_second = float(result["bytes_per_second"])

        print(f"   Async File Writing: {messages_per_second:,.0f} msg/s")
        print(f"   Async File I/O Speed: {bytes_per_second:,.0f} bytes/s")
        print(f"   Duration: {duration:.3f}s")
        print("   Async File Writing: COMPLETED")

        return result

    def test_configuration_performance(self) -> Dict[str, Any]:
        """
        Test performance with different configurations.

        NOTE: These tests use REAL-WORLD configurations that include console handlers.
        Console I/O is inherently slow (10-15K msg/s) because it's synchronous blocking I/O.
        This is expected and represents actual user experience with default configs.

        For comparison, the other performance tests use file-only handlers (30K-400K+ msg/s)
        to measure true logger performance without I/O bottlenecks.

        Returns:
            Dict containing performance metrics for different configurations
        """
        print("\nTesting Configuration Performance...")
        print("   Testing different configuration impacts...")
        print(
            "   NOTE: These use real-world configs with console handlers (slower I/O)"
        )
        print("   For optimized performance, use file-only handlers (see other tests)")

        configs = {
            "default": get_default_config(),
            "development": get_development_config(),
            "production": get_production_config(),
        }

        config_results = {}
        message_count = self.test_config["typical_single_messages"]

        for config_name, base_config in configs.items():
            print(f"   Testing {config_name.title()} configuration...")
            config = self._rebase_file_destinations_to_benchmark_logs(
                base_config, config_name
            )
            # Use unique logger name to avoid cache conflicts
            logger_name = f"benchmark_{config_name}_{id(self)}"
            logger = getLogger(logger_name, config=config)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)

            # Warm-up
            warmup_count = min(1000, message_count // 100)
            for i in range(warmup_count):
                logger.info(f"Warm-up {i}")

            # Flush before timing
            self._flush_all_handlers(logger)
            time.sleep(0.1)  # Brief pause for I/O to settle

            start_time = time.perf_counter()
            for i in range(message_count):
                logger.info(f"{config_name.title()} config benchmark message {i}")
            # Flush after logging
            self._flush_all_handlers(logger)
            # End timing BEFORE sleep to measure actual logging performance
            end_time = time.perf_counter()

            # Brief pause for I/O to complete (for accurate measurement, not performance)
            time.sleep(0.1)

            duration = end_time - start_time
            messages_per_second = message_count / duration

            # Cleanup
            try:
                logger.close()
            except Exception:
                pass

            config_results[config_name] = {
                "messages_per_second": messages_per_second,
                "duration": duration,
                "total_messages": message_count,
                "note": "Real-world config with console handlers (slower I/O)",
            }

            print(
                f"   {config_name.title()} Config: {messages_per_second:,.0f} msg/s (with console I/O)"
            )

        print("   Configuration Performance: COMPLETED")
        print(
            "   Note: Slower speeds are expected due to console handler I/O bottleneck"
        )
        return config_results

    def test_memory_usage(self) -> Dict[str, Any]:
        """
        Test memory usage patterns.

        Uses multiple samples and garbage collection for accurate measurement.
        RSS (Resident Set Size) includes process overhead, so measurements
        represent actual process memory usage including Python overhead.

        Returns:
            Dict containing memory usage metrics
        """
        print("\nTesting Memory Usage...")
        print("   Testing memory efficiency...")

        try:
            import gc
            import os

            import psutil

            process = psutil.Process(os.getpid())

            # Force garbage collection before initial measurement to get clean baseline
            # This ensures we're not measuring leftover objects from previous tests
            gc.collect()
            gc.collect()  # Second pass to handle circular references

            # Take multiple samples and average for more accurate measurement
            # Python's memory allocator works in chunks, so single samples can be noisy
            initial_samples = []
            for _ in range(3):
                initial_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
                time.sleep(0.01)  # Brief pause between samples

            initial_memory = statistics.mean(initial_samples)

            # Test with multiple loggers
            loggers = []
            logger_count = 50

            for i in range(logger_count):
                # Use unique logger name to avoid cache conflicts
                logger_name = f"memory_test_{i}_{id(self)}"
                logger = getLogger(
                    logger_name, config=self._create_performance_config("sync")
                )
                loggers.append(logger)
                self._created_loggers.append(logger)
                self._logger_names.append(logger_name)
                logger.info(f"Memory test message {i}")

            # Flush handlers to ensure all memory allocations are complete
            for logger in loggers:
                try:
                    self._flush_all_handlers(logger)
                except Exception:
                    pass

            # Force garbage collection again to ensure we're measuring actual allocations
            # (not just freed memory that Python's allocator is holding onto)
            gc.collect()

            # Take multiple samples after logger creation for more accurate measurement
            final_samples = []
            for _ in range(3):
                final_samples.append(process.memory_info().rss / 1024 / 1024)  # MB
                time.sleep(0.01)  # Brief pause between samples

            final_memory = statistics.mean(final_samples)
            memory_increase = final_memory - initial_memory

            # Calculate memory per logger (this includes logger overhead + one log message)
            memory_per_logger = (
                memory_increase / logger_count if logger_count > 0 else 0
            )

            result = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "loggers_created": logger_count,
                "memory_per_logger_mb": memory_per_logger,
                "initial_samples": initial_samples,  # For debugging
                "final_samples": final_samples,  # For debugging
                "status": "COMPLETED",
            }

            print(f"   Initial Memory (avg): {initial_memory:.2f} MB")
            print(f"   Final Memory (avg): {final_memory:.2f} MB")
            print(
                f"   Memory Increase: {memory_increase:.2f} MB for {logger_count} loggers"
            )
            print(f"   Memory per Logger: {memory_per_logger:.4f} MB")
            print(
                "   Note: RSS includes Python overhead; actual logger memory may be lower"
            )
            print("   Memory Usage: COMPLETED")

            return result

        except ImportError:
            print("   Warning: psutil not available, skipping memory test")
            return {"status": "SKIPPED", "reason": "psutil not available"}

    async def test_concurrent_logging(self) -> Dict[str, Any]:
        """
        Test concurrent logging performance using async tasks (not threads).

        Using async tasks instead of threads eliminates event loop creation overhead
        and provides better performance for async loggers.

        Returns:
            Dict containing concurrent logging metrics
        """
        print("\nTesting Concurrent Logging...")
        print("   Testing async concurrent logging performance...")

        num_workers = self.test_config["concurrent_workers"]
        messages_per_worker = self.test_config["messages_per_worker"]

        # Use composite-async logger for better performance (like async_concurrent test)
        # Use unique logger name to avoid cache conflicts
        logger_name = f"concurrent_shared_{id(self)}"
        shared_logger = getLogger(
            logger_name,
            logger_type="composite-async",
            config=self._create_performance_config("composite-async"),
            use_direct_io=False,
        )
        self._disable_direct_io_if_available(shared_logger)
        self._ensure_composite_file_target(shared_logger, prefix=logger_name)
        self._created_loggers.append(shared_logger)
        self._logger_names.append(logger_name)

        async def async_worker(worker_id):
            """Async worker that logs messages concurrently."""
            start_time = time.perf_counter()
            # Use batch logging for better performance (much faster than individual tasks)
            if hasattr(shared_logger, "log_batch"):
                messages = [
                    ("INFO", f"Worker {worker_id} message {i}", {})
                    for i in range(messages_per_worker)
                ]
                await shared_logger.log_batch(messages)
            else:
                # Fallback: batch create all tasks at once
                tasks = [
                    shared_logger.log("INFO", f"Worker {worker_id} message {i}")
                    for i in range(messages_per_worker)
                ]
                await asyncio.gather(*tasks)
            end_time = time.perf_counter()
            duration = end_time - start_time
            messages_per_second = messages_per_worker / duration if duration > 0 else 0
            return {
                "worker_id": worker_id,
                "duration": duration,
                "messages_per_second": messages_per_second,
            }

        # Start all workers concurrently using async tasks (much faster than threads)
        start_time = time.perf_counter()
        worker_tasks = [async_worker(i) for i in range(num_workers)]
        worker_results = await asyncio.gather(*worker_tasks)

        # End timing BEFORE flush/cleanup to measure actual logging performance
        end_time = time.perf_counter()
        total_duration = end_time - start_time

        # Flush after timing (cleanup doesn't affect performance measurement)
        await self._flush_all_handlers_async(shared_logger)

        # Calculate total throughput (total messages across all workers / total duration)
        # This is the aggregate throughput, not per-worker
        total_messages = num_workers * messages_per_worker
        total_messages_per_second = total_messages / total_duration

        # Calculate per-worker statistics (for comparison)
        worker_speeds = [
            w["messages_per_second"]
            for w in worker_results
            if "messages_per_second" in w
        ]

        # Cleanup
        try:
            if hasattr(shared_logger, "aclose") and asyncio.iscoroutinefunction(
                shared_logger.aclose
            ):
                await shared_logger.aclose()
            elif hasattr(shared_logger, "close_async") and asyncio.iscoroutinefunction(
                shared_logger.close_async
            ):
                await shared_logger.close_async()
            elif hasattr(shared_logger, "close"):
                shared_logger.close()
        except Exception:
            pass

        # Handle empty results
        if not worker_speeds:
            print("   Warning: No workers completed successfully")
            return {
                "total_duration": total_duration,
                "total_messages_per_second": 0,
                "worker_results": [],
                "num_threads": num_workers,  # Keep for backward compatibility
                "messages_per_thread": messages_per_worker,  # Keep for backward compatibility
                "total_messages": total_messages,
                "avg_thread_speed": 0,
                "min_thread_speed": 0,
                "max_thread_speed": 0,
                "status": "FAILED",
            }

        result = {
            "total_duration": total_duration,
            "total_messages_per_second": total_messages_per_second,
            "thread_results": worker_results,  # Keep key name for backward compatibility
            "num_threads": num_workers,  # Keep for backward compatibility
            "messages_per_thread": messages_per_worker,  # Keep for backward compatibility
            "total_messages": total_messages,
            "avg_thread_speed": statistics.mean(
                worker_speeds
            ),  # Keep for backward compatibility
            "min_thread_speed": min(worker_speeds),
            "max_thread_speed": max(worker_speeds),
            "status": "COMPLETED",
        }

        print(
            f"   Total Throughput: {total_messages_per_second:,.0f} msg/s (total aggregate across {num_workers} workers)"
        )
        print(
            f"   Avg Worker Speed: {result['avg_thread_speed']:,.0f} msg/s (per worker, for reference)"
        )
        print("   Concurrent Logging: COMPLETED")

        return result

    async def test_advanced_concurrent_logging(self) -> Dict[str, Any]:
        """
        Test advanced concurrent logging scenarios.

        Returns:
            Dict containing advanced concurrent logging metrics
        """
        print("\nTesting Advanced Concurrent Logging...")
        print("   Testing multiple concurrent scenarios...")

        import asyncio
        import queue
        import threading

        results = {}

        # Test 1: Shared logger with different thread counts
        print("   Testing shared logger scalability...")
        thread_counts = [1, 2, 5, 10, 20]
        shared_results = {}

        for thread_count in thread_counts:
            # Use unique logger name to avoid cache conflicts
            # Use composite-async for better performance (like async_concurrent test)
            logger_name = f"shared_{thread_count}_{id(self)}"
            shared_logger = getLogger(
                logger_name,
                logger_type="composite-async",
                config=self._create_performance_config("composite-async"),
                use_direct_io=False,
            )
            self._disable_direct_io_if_available(shared_logger)
            self._ensure_composite_file_target(shared_logger, prefix=logger_name)
            self._created_loggers.append(shared_logger)
            self._logger_names.append(logger_name)
            messages_per_worker = 500

            async def async_worker(worker_id):
                """Async worker that logs messages concurrently."""
                start_time = time.perf_counter()
                # Use batch logging for better performance (much faster than individual tasks)
                if hasattr(shared_logger, "log_batch"):
                    messages = [
                        ("INFO", f"Shared Worker {worker_id} message {i}", {})
                        for i in range(messages_per_worker)
                    ]
                    await shared_logger.log_batch(messages)
                else:
                    # Fallback: batch create all tasks at once
                    tasks = [
                        shared_logger.log(
                            "INFO", f"Shared Worker {worker_id} message {i}"
                        )
                        for i in range(messages_per_worker)
                    ]
                    await asyncio.gather(*tasks)
                end_time = time.perf_counter()
                return end_time - start_time

            # Use async tasks instead of threads (much faster - no event loop creation overhead)
            start_time = time.perf_counter()
            worker_tasks = [async_worker(i) for i in range(thread_count)]
            await asyncio.gather(*worker_tasks)

            # End timing BEFORE flush/cleanup to measure actual logging performance
            end_time = time.perf_counter()
            total_duration = end_time - start_time
            # Calculate total throughput (total messages across all workers / total duration)
            total_messages = thread_count * messages_per_worker
            messages_per_second = total_messages / total_duration

            # Flush and close after timing (cleanup doesn't affect performance measurement)
            await self._flush_all_handlers_async(shared_logger)
            if hasattr(shared_logger, "aclose") and asyncio.iscoroutinefunction(
                shared_logger.aclose
            ):
                await shared_logger.aclose()
            elif hasattr(shared_logger, "close_async") and asyncio.iscoroutinefunction(
                shared_logger.close_async
            ):
                await shared_logger.close_async()
            elif hasattr(shared_logger, "close"):
                shared_logger.close()

            shared_results[thread_count] = {
                "messages_per_second": messages_per_second,
                "duration": total_duration,
                "efficiency": messages_per_second / thread_count,
            }

            per_thread = messages_per_second / thread_count
            print(
                f"   {thread_count:2d} threads: {messages_per_second:>8,.0f} msg/s (total aggregate, {per_thread:>6,.0f} msg/s per thread)"
            )

        # Test 2: Async concurrent logging
        print("   Testing async concurrent logging...")

        async def async_concurrent_test():
            # Use unique logger name to avoid cache conflicts
            logger_name = f"async_concurrent_{id(self)}"
            async_logger = getLogger(
                logger_name,
                logger_type="composite-async",
                config=self._create_performance_config("composite-async"),
                use_direct_io=False,
            )
            self._disable_direct_io_if_available(async_logger)
            self._ensure_composite_file_target(async_logger, prefix=logger_name)
            self._created_loggers.append(async_logger)
            self._logger_names.append(logger_name)
            messages_per_task = 1000
            num_tasks = 20

            async def async_worker(task_id):
                start_time = time.perf_counter()
                tasks = []
                for i in range(messages_per_task):
                    tasks.append(
                        async_logger.log("INFO", f"Async Task {task_id} message {i}")
                    )
                await asyncio.gather(*tasks)
                end_time = time.perf_counter()
                return end_time - start_time

            start_time = time.perf_counter()
            worker_tasks = [async_worker(i) for i in range(num_tasks)]
            durations = await asyncio.gather(*worker_tasks)

            # End timing BEFORE close to measure actual logging performance (not cleanup)
            end_time = time.perf_counter()

            total_duration = end_time - start_time
            total_messages = num_tasks * messages_per_task
            messages_per_second = total_messages / total_duration

            # Close logger after timing (cleanup doesn't affect performance measurement)
            if hasattr(async_logger, "close_async"):
                await async_logger.close_async()
            elif hasattr(async_logger, "aclose"):
                await async_logger.aclose()

            return {
                "messages_per_second": messages_per_second,
                "duration": total_duration,
                "num_tasks": num_tasks,
                "messages_per_task": messages_per_task,
            }

        # Run async test
        async_result = await async_concurrent_test()
        print(
            f"   Async {async_result['num_tasks']} tasks: {async_result['messages_per_second']:>8,.0f} msg/s"
        )

        # Test 3: Mixed sync/async concurrent
        print("   Testing mixed sync/async concurrent...")

        def mixed_worker(thread_id, is_async=False):
            # Use unique logger name to avoid cache conflicts
            # Use file-only config for performance (console I/O is slow)
            logger_name = f"mixed_sync_{thread_id}_{id(self)}"
            perf_config = self._create_performance_config(logger_type="sync")
            logger = getLogger(
                logger_name,
                logger_type="composite",
                config=perf_config,
                use_direct_io=False,
            )
            self._disable_direct_io_if_available(logger)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)

            start_time = time.perf_counter()
            # OPTIMIZATION: Use batch logging instead of individual calls (much faster!)
            messages = [
                ("INFO", f"Mixed Thread {thread_id} message {i}", {})
                for i in range(250)
            ]
            # Use batch logging if available (much faster than individual calls)
            if hasattr(logger, "log_batch"):
                logger.log_batch(messages)
            else:
                # Fallback: individual calls (slower but works)
                for level, msg, kwargs in messages:
                    logger.log(level, msg, **kwargs)
            end_time = time.perf_counter()
            return end_time - start_time

        # Create mixed threads
        mixed_threads = []
        start_time = time.perf_counter()

        for i in range(10):
            is_async = i % 2 == 0
            thread = threading.Thread(target=mixed_worker, args=(i, is_async))
            mixed_threads.append(thread)
            thread.start()

        for thread in mixed_threads:
            thread.join()

        # End timing BEFORE cleanup to measure actual logging performance
        end_time = time.perf_counter()
        mixed_duration = end_time - start_time
        mixed_messages = 10 * 250
        mixed_messages_per_second = mixed_messages / mixed_duration

        # Close all mixed loggers after timing (cleanup doesn't affect performance measurement)
        # Note: Loggers are already tracked in _created_loggers and _logger_names
        for logger in self._created_loggers:
            try:
                if hasattr(logger, "_logger_name") and f"mixed_sync_" in str(logger):
                    self._flush_all_handlers(logger)
                    if hasattr(logger, "close"):
                        logger.close()
            except Exception:
                pass

        mixed_per_thread = mixed_messages_per_second / 10
        print(
            f"   Mixed 10 threads: {mixed_messages_per_second:>8,.0f} msg/s (total aggregate, {mixed_per_thread:>6,.0f} msg/s per thread)"
        )

        result = {
            "shared_logger_scalability": shared_results,
            "async_concurrent": async_result,
            "mixed_concurrent": {
                "messages_per_second": mixed_messages_per_second,
                "duration": mixed_duration,
                "num_threads": 10,
            },
            "status": "COMPLETED",
        }

        print("   Advanced Concurrent Logging: COMPLETED")
        return result

    async def test_async_concurrent_suite(self) -> Dict[str, Any]:
        """Explicit async-concurrent suite (event-loop concurrency only)."""
        print("\nTesting Async Concurrent Suite...")
        matrix = list(self.test_config.get("suite_matrix_workers_tasks", [1, 2, 4, 8, 16, 32]))
        messages_per_task = int(self.test_config.get("suite_matrix_messages_per_worker", 1000))
        
        def _create_logger(task_count: int):
            logger_name = f"async_suite_{task_count}_{id(self)}"
            logger = getLogger(
                logger_name,
                logger_type="composite-async",
                config=self._create_performance_config("composite-async"),
                use_direct_io=False,
            )
            self._disable_direct_io_if_available(logger)
            self._ensure_composite_file_target(logger, prefix=logger_name)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)
            return logger

        async def _flush_logger(logger) -> None:
            await self._flush_all_handlers_async(logger)

        async def _close_logger(logger) -> None:
            try:
                if hasattr(logger, "aclose") and asyncio.iscoroutinefunction(logger.aclose):
                    await logger.aclose()
                elif hasattr(logger, "close_async") and asyncio.iscoroutinefunction(
                    logger.close_async
                ):
                    await logger.close_async()
                elif hasattr(logger, "close"):
                    logger.close()
            except Exception:
                pass

        result = await run_async_concurrent_suite(
            matrix=matrix,
            messages_per_task=messages_per_task,
            create_logger=_create_logger,
            flush_async=_flush_logger,
            close_async=_close_logger,
            messages_per_second=self._messages_per_second,
        )
        scaling = result.get("scaling", {})
        for task_count in matrix:
            row = scaling.get(str(task_count), {})
            print(
                f"   {task_count:2d} tasks: {float(row.get('total_messages_per_second', 0.0)):>10,.0f} msg/s (event-loop concurrent)"
            )
        print("   Async Concurrent Suite: COMPLETED")
        return result

    def test_parallel_workers_suite(self) -> Dict[str, Any]:
        """Explicit parallel-workers suite (real process-level parallelism)."""
        print("\nTesting Parallel Workers Suite...")
        matrix = list(self.test_config.get("suite_matrix_workers_tasks", [1, 2, 4, 8, 16, 32]))
        messages_per_worker = int(self.test_config.get("suite_matrix_messages_per_worker", 1000))
        result = run_parallel_workers_suite(
            matrix=matrix,
            messages_per_worker=messages_per_worker,
            bench_logs_dir=self._benchmark_logs_dir,
            messages_per_second=self._messages_per_second,
        )
        scaling = result.get("scaling", {})
        for worker_count in matrix:
            row = scaling.get(str(worker_count), {})
            print(
                f"   {worker_count:2d} workers: {float(row.get('total_messages_per_second', 0.0)):>10,.0f} msg/s (process parallel)"
            )

        print("   Parallel Workers Suite: COMPLETED")
        return result

    async def test_ultra_high_performance(self) -> Dict[str, Any]:
        """
        Test high performance scenarios.

        Returns:
            Dict containing high performance metrics
        """
        print("\nTesting High Performance...")
        print("   Testing composite async logger...")

        import asyncio
        import time

        async def high_performance_test():
            # Use unique logger name to avoid cache conflicts
            logger_name = f"ultra_high_perf_{id(self)}"
            logger = getLogger(
                logger_name,
                logger_type="composite-async",
                config=self._create_performance_config("composite-async"),
                use_direct_io=False,
            )
            self._disable_direct_io_if_available(logger)
            self._created_loggers.append(logger)
            self._logger_names.append(logger_name)

            benchmark_instance = self

            total_messages = 100000
            batch_size = 10000

            # Warm-up
            print("   Warm-up period...")
            warmup_tasks = []
            for i in range(100):
                warmup_tasks.append(logger.log("INFO", f"Warm-up {i}"))
            await asyncio.gather(*warmup_tasks)

            # Wait for warm-up handlers
            await benchmark_instance._wait_for_async_handlers(logger, timeout=0.5)

            # Flush async handlers before timing
            await benchmark_instance._flush_all_handlers_async(logger)

            # Start timing after warm-up and flush
            start_time = time.perf_counter()

            # Track actual messages logged (not total_messages, which is just a target)
            actual_messages_logged = 0

            # Use explicit batch logging path for deterministic measurements.
            # `log_bulk` has implementation-specific behavior across logger variants.
            print("   Testing large-batch logging performance...")
            remaining = total_messages
            batch_messages = [("INFO", f"Bulk message {i}", {}) for i in range(batch_size)]
            await logger.log_batch(batch_messages)
            actual_messages_logged += len(batch_messages)
            remaining = total_messages - len(batch_messages)

            # Test batch logging
            if remaining > 0:
                print("   Testing batch logging performance...")
                batch_messages = []
                batch_count = min(batch_size, remaining)
                for i in range(batch_count):
                    batch_messages.append(("INFO", f"Batch message {i}", {}))
                await logger.log_batch(batch_messages)
                actual_messages_logged += len(batch_messages)
                remaining -= batch_count

            # Test individual async logging
            if remaining > 0:
                individual_count = min(remaining, 10000)
                print(
                    f"   Testing individual async logging performance ({individual_count} messages)..."
                )
                tasks = []
                for i in range(individual_count):
                    tasks.append(logger.log("INFO", f"Individual message {i}"))
                await asyncio.gather(*tasks)
                actual_messages_logged += individual_count

            # End timing BEFORE close to measure actual logging performance (not cleanup)
            end_time = time.perf_counter()
            duration = end_time - start_time
            # Use actual messages logged, not total_messages (which is just a target)
            messages_per_second = (
                actual_messages_logged / duration if duration > 0 else float("inf")
            )

            # Close logger after timing (cleanup doesn't affect performance measurement)
            print("   Finalizing writes...")
            if hasattr(logger, "close_async"):
                await logger.close_async()
            elif hasattr(logger, "aclose"):
                await logger.aclose()
            else:
                # Fallback
                await benchmark_instance._flush_all_handlers_async(logger)

            return {
                "messages_per_second": messages_per_second,
                "duration": duration,
                "total_messages": actual_messages_logged,  # Report actual messages logged
                "status": "COMPLETED",
            }

        # Run high performance test
        result = await high_performance_test()

        print(f"   High Performance: {result['messages_per_second']:>8,.0f} msg/s")
        print(f"   Total Messages: {result['total_messages']:,}")
        print(f"   Duration: {result['duration']:.3f}s")

        if result["messages_per_second"] >= 50000:
            print("   Performance target met: 50K+ msg/s")
        else:
            print("   Performance below 50K msg/s target")

        print("   High Performance: COMPLETED")
        return result

    def print_detailed_results(self):
        """Print comprehensive performance results."""
        print("\n" + "=" * 80)
        print("DETAILED PERFORMANCE RESULTS")
        print("=" * 80)

        # Individual logger performance
        print("\nINDIVIDUAL LOGGER PERFORMANCE")
        print("-" * 60)
        print(
            f"{'Logger Type':<25} | {'Messages/sec':<15} | {'Duration (s)':<12} | {'Status'}"
        )
        print("-" * 60)

        individual_tests = [
            ("sync_logger", "Sync Logger"),
            ("async_logger", "Async Logger"),
            ("composite_logger", "Composite Logger"),
            ("composite_async_logger", "Composite Async Logger"),
        ]

        for test_key, test_name in individual_tests:
            if test_key in self.results:
                result = self.results[test_key]
                print(
                    f"{test_name:<25} | {result['individual_messages_per_second']:>13,.0f} | {result['individual_duration']:>10.3f} | {result['status']}"
                )

        # Batch logging performance
        print("\nBATCH LOGGING PERFORMANCE")
        print("-" * 60)
        print(
            f"{'Logger Type':<25} | {'Messages/sec':<15} | {'Duration (s)':<12} | {'Batch Size'}"
        )
        print("-" * 60)

        batch_tests = [
            ("composite_logger", "Composite Logger"),
            ("composite_async_logger", "Composite Async Logger"),
        ]

        for test_key, test_name in batch_tests:
            if (
                test_key in self.results
                and "batch_messages_per_second" in self.results[test_key]
            ):
                result = self.results[test_key]
                print(
                    f"{test_name:<25} | {result['batch_messages_per_second']:>13,.0f} | {result['batch_duration']:>10.3f} | {result['batch_size']:,}"
                )

        # Configuration performance
        if "configurations" in self.results:
            print("\nCONFIGURATION PERFORMANCE")
            print("-" * 60)
            print(
                f"{'Configuration':<25} | {'Messages/sec':<15} | {'Duration (s)':<12} | {'Messages'}"
            )
            print("-" * 60)

            for config_name, result in self.results["configurations"].items():
                if not isinstance(result, dict):
                    continue
                if not isinstance(result.get("messages_per_second"), (int, float)):
                    continue
                print(
                    f"{config_name.title():<25} | {result['messages_per_second']:>13,.0f} | {result['duration']:>10.3f} | {result['total_messages']:,}"
                )

        # File writing performance
        if (
            "file_writing" in self.results
            and self.results["file_writing"]["status"] == "COMPLETED"
        ):
            print("\nFILE WRITING PERFORMANCE")
            print("-" * 60)
            file_result = self.results["file_writing"]
            print(
                f"Sync File Writing:         {file_result['messages_per_second']:>8,.0f} msg/s"
            )
            print(
                f"File I/O Speed:            {file_result['bytes_per_second']:>8,.0f} bytes/s"
            )
            print(
                f"Total Bytes Written:       {file_result['bytes_written']:>8,} bytes"
            )
            print(f"Duration:                   {file_result['duration']:>8.3f} s")
            print(f"Total Messages:             {file_result['total_messages']:>8,}")

        if (
            "async_file_writing" in self.results
            and self.results["async_file_writing"]["status"] == "COMPLETED"
        ):
            print("\nASYNC FILE WRITING PERFORMANCE")
            print("-" * 60)
            async_file_result = self.results["async_file_writing"]
            print(
                f"Async File Writing:         {async_file_result['messages_per_second']:>8,.0f} msg/s"
            )
            print(
                f"Async File I/O Speed:       {async_file_result['bytes_per_second']:>8,.0f} bytes/s"
            )
            print(
                f"Total Bytes Written:       {async_file_result['bytes_written']:>8,} bytes"
            )
            print(
                f"Duration:                   {async_file_result['duration']:>8.3f} s"
            )
            print(
                f"Total Messages:             {async_file_result['total_messages']:>8,}"
            )

        # Memory usage
        if "memory" in self.results and self.results["memory"]["status"] == "COMPLETED":
            print("\nMEMORY USAGE ANALYSIS")
            print("-" * 60)
            memory = self.results["memory"]
            print(f"Initial Memory:           {memory['initial_memory_mb']:>8.2f} MB")
            print(f"Final Memory:             {memory['final_memory_mb']:>8.2f} MB")
            print(f"Memory Increase:          {memory['memory_increase_mb']:>8.2f} MB")
            print(f"Loggers Created:          {memory['loggers_created']:>8d}")
            print(
                f"Memory per Logger:        {memory['memory_per_logger_mb']:>8.4f} MB"
            )

        # Concurrent performance
        if "concurrent" in self.results:
            print("\nCONCURRENT LOGGING PERFORMANCE")
            print("-" * 60)
            concurrent = self.results["concurrent"]
            print(
                f"Total Throughput:         {concurrent['total_messages_per_second']:>8,.0f} msg/s (total aggregate)"
            )
            print(f"Total Duration:           {concurrent['total_duration']:>8.3f} s")
            print(f"Number of Workers:        {concurrent['num_threads']:>8d}")
            print(f"Messages per Worker:      {concurrent['messages_per_thread']:>8d}")
            print(f"Total Messages:           {concurrent['total_messages']:>8d}")
            print(
                f"Average Worker Speed:     {concurrent['avg_thread_speed']:>8,.0f} msg/s (per worker, for reference)"
            )
            print(
                f"Min Worker Speed:         {concurrent['min_thread_speed']:>8,.0f} msg/s"
            )
            print(
                f"Max Worker Speed:         {concurrent['max_thread_speed']:>8,.0f} msg/s"
            )

        if "async_concurrent" in self.results:
            print("\nASYNC CONCURRENT SUITE")
            print("-" * 60)
            async_suite = self.results["async_concurrent"]
            print(f"Workers/Tasks Matrix:     {async_suite['workers_tasks']}")
            print(
                f"Messages per Task:        {async_suite['messages_per_worker']:>8,}"
            )
            for task_count, row in async_suite.get("scaling", {}).items():
                print(
                    f"Tasks {int(task_count):>2d}:                {row['total_messages_per_second']:>8,.0f} msg/s"
                )

        if "parallel_workers" in self.results:
            print("\nPARALLEL WORKERS SUITE")
            print("-" * 60)
            parallel_suite = self.results["parallel_workers"]
            print(f"Workers Matrix:           {parallel_suite['workers_tasks']}")
            print(
                f"Messages per Worker:      {parallel_suite['messages_per_worker']:>8,}"
            )
            for worker_count, row in parallel_suite.get("scaling", {}).items():
                print(
                    f"Workers {int(worker_count):>2d}:             {row['total_messages_per_second']:>8,.0f} msg/s"
                )

        # Performance summary
        print("\nPERFORMANCE SUMMARY")
        print("-" * 60)

        # Collect all performance metrics
        all_performance_data = []
        performance_threshold = 50000

        for test_key, result in self.results.items():
            if isinstance(result, dict):
                # Individual messages
                if "individual_messages_per_second" in result:
                    all_performance_data.append(
                        {
                            "name": f"{result.get('logger_type', test_key)} (Individual)",
                            "speed": result["individual_messages_per_second"],
                            "type": "individual",
                            "test_key": test_key,
                        }
                    )
                # Batch messages
                if "batch_messages_per_second" in result:
                    all_performance_data.append(
                        {
                            "name": f"{result.get('logger_type', test_key)} (Batch)",
                            "speed": result["batch_messages_per_second"],
                            "type": "batch",
                            "test_key": test_key,
                        }
                    )
                # Total throughput
                if "total_messages_per_second" in result:
                    all_performance_data.append(
                        {
                            "name": f"{test_key.replace('_', ' ').title()} (Total)",
                            "speed": result["total_messages_per_second"],
                            "type": "total",
                            "test_key": test_key,
                        }
                    )
                # Configuration results
                if "configurations" in test_key:
                    for config_name, config_result in result.items():
                        if not isinstance(config_result, dict):
                            continue
                        if not isinstance(config_result.get("messages_per_second"), (int, float)):
                            continue
                        all_performance_data.append(
                            {
                                "name": f"Config: {config_name.title()}",
                                "speed": config_result["messages_per_second"],
                                "type": "config",
                                "test_key": f"{test_key}.{config_name}",
                            }
                        )
                # Advanced concurrent results
                if "advanced_concurrent" in test_key:
                    if "shared_logger_scalability" in result:
                        for thread_count, thread_result in result[
                            "shared_logger_scalability"
                        ].items():
                            all_performance_data.append(
                                {
                                    "name": f"Shared Logger ({thread_count} threads)",
                                    "speed": thread_result["messages_per_second"],
                                    "type": "concurrent",
                                    "test_key": f"{test_key}.shared.{thread_count}",
                                }
                            )
                    if "async_concurrent" in result:
                        all_performance_data.append(
                            {
                                "name": f"Async Concurrent ({result['async_concurrent']['num_tasks']} tasks)",
                                "speed": result["async_concurrent"][
                                    "messages_per_second"
                                ],
                                "type": "async_concurrent",
                                "test_key": f"{test_key}.async",
                            }
                        )
                    if "mixed_concurrent" in result:
                        all_performance_data.append(
                            {
                                "name": "Mixed Sync/Async Concurrent",
                                "speed": result["mixed_concurrent"][
                                    "messages_per_second"
                                ],
                                "type": "mixed",
                                "test_key": f"{test_key}.mixed",
                            }
                        )
                if "async_concurrent" in test_key and "scaling" in result:
                    for task_count, row in result["scaling"].items():
                        all_performance_data.append(
                            {
                                "name": f"Async Concurrent Suite ({task_count} tasks)",
                                "speed": row["total_messages_per_second"],
                                "type": "async_concurrent_suite",
                                "test_key": f"{test_key}.{task_count}",
                            }
                        )
                if "parallel_workers" in test_key and "scaling" in result:
                    for worker_count, row in result["scaling"].items():
                        all_performance_data.append(
                            {
                                "name": f"Parallel Workers Suite ({worker_count} workers)",
                                "speed": row["total_messages_per_second"],
                                "type": "parallel_workers",
                                "test_key": f"{test_key}.{worker_count}",
                            }
                        )
                # High performance
                if "ultra_high_performance" in test_key:
                    all_performance_data.append(
                        {
                            "name": "High Performance",
                            "speed": result["messages_per_second"],
                            "type": "ultra",
                            "test_key": test_key,
                        }
                    )

        if all_performance_data:
            all_speeds = [p["speed"] for p in all_performance_data]

            print(f"Fastest Performance:      {max(all_speeds):>8,.0f} msg/s")
            print(f"Slowest Performance:      {min(all_speeds):>8,.0f} msg/s")
            print(
                f"Average Performance:      {statistics.mean(all_speeds):>8,.0f} msg/s"
            )
            print(
                f"Performance Range:        {max(all_speeds) - min(all_speeds):>8,.0f} msg/s"
            )

            # Identify slow performers (under threshold)
            slow_performers = [
                p for p in all_performance_data if p["speed"] < performance_threshold
            ]

            if slow_performers:
                print("\nLOGGERS BELOW 50K MSG/S THRESHOLD")
                print("-" * 60)
                print(
                    f"{'Logger Name':<40} | {'Speed (msg/s)':<15} | {'Gap to 50K':<15} | {'Type'}"
                )
                print("-" * 60)
                slow_performers.sort(key=lambda x: x["speed"])

                for perf in slow_performers:
                    gap = performance_threshold - perf["speed"]
                    gap_pct = (gap / performance_threshold) * 100
                    print(
                        f"{perf['name']:<40} | {perf['speed']:>13,.0f} | {gap:>13,.0f} ({gap_pct:.1f}%) | {perf['type']}"
                    )

                print(
                    f"\nTotal slow performers: {len(slow_performers)} out of {len(all_performance_data)}"
                )
                print(
                    f"Average speed of slow performers: {statistics.mean([p['speed'] for p in slow_performers]):,.0f} msg/s"
                )
            else:
                print("\nAll loggers meet the 50K msg/s threshold")

            # Show top performers
            print("\nTOP 5 PERFORMERS")
            print("-" * 60)
            print(
                f"{'Rank':<6} | {'Logger Name':<40} | {'Speed (msg/s)':<15} | {'Type'}"
            )
            print("-" * 60)
            top_performers = sorted(
                all_performance_data, key=lambda x: x["speed"], reverse=True
            )[:5]
            for rank, perf in enumerate(top_performers, 1):
                print(
                    f"{rank:<6} | {perf['name']:<40} | {perf['speed']:>13,.0f} | {perf['type']}"
                )

    def save_results_to_file(self):
        """Save benchmark results to JSON file for later analysis.

        Creates timestamped files: benchmark/results/benchmark_YYYY-MM-DD_HH-MM-SS.json
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output = build_output_payload(
                results=self.results,
                profile_name=self.profile_name,
                test_config=self.test_config,
                python_version=sys.version.split()[0],
                platform_name=sys.platform,
                git_commit_sha=self._git_commit_sha(),
                machine=platform.platform(),
                cpu_count=os.cpu_count() or 1,
                disk_mode=self.disk_mode,
                payload_profile=self.payload_profile,
                timestamp=timestamp,
            )
            filename = write_results_artifacts(
                output_payload=output,
                results_dir=self.results_dir,
                write_markdown_reports=self.write_markdown_reports,
            )
            print(f"\nResults saved to: {filename}")
            print(f"   You can review results later or compare with previous runs")

        except Exception as e:
            print(f"\nWarning: Could not save results to file: {e}")
            print(f"   Results are still available in console output above")

    def _git_commit_sha(self) -> str:
        """Return short git SHA for benchmark provenance."""
        try:
            return (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=Path(__file__).resolve().parent.parent,
                    text=True,
                )
                .strip()
            )
        except Exception:
            return "unknown"

    def _enforce_reliability_guards(self) -> None:
        """Hard-fail benchmark on formula or path-confinement violations."""
        violations: list[str] = []
        invariant_violations = validate_result_invariants(self.results)
        violations.extend(invariant_violations)
        drift_violations, drift_report = evaluate_drift_policy(
            current_results=self.results,
            results_dir=self.results_dir,
            profile_name=self.profile_name,
            policy_overrides=self.drift_policy,
        )
        self.results["drift_policy"] = drift_report
        violations.extend(drift_violations)
        path_violations = validate_result_paths(
            results=self.results,
            allowed_roots=[self._benchmark_logs_dir, self.results_dir],
        )
        violations.extend(path_violations)
        matrix_file_violations = validate_output_matrix_file_evidence(results=self.results)
        violations.extend(matrix_file_violations)
        file_io_violations = validate_file_io_evidence(results=self.results)
        violations.extend(file_io_violations)
        sample_duration_violations: list[str] = []
        for section_name, payload in self.results.items():
            if isinstance(payload, dict) and payload.get("sample_duration_violation"):
                sample_duration_violations.append(str(payload["sample_duration_violation"]))
        violations.extend(sample_duration_violations)
        leaked_files = detect_new_root_log_leaks(
            project_root=self._project_root,
            preexisting_log_names=self._preexisting_root_log_names,
        )
        if leaked_files:
            violations.append(
                "new benchmark-related files detected under project logs/: "
                + ", ".join(leaked_files)
            )
        self.results["reliability_guards"] = {
            "status": "failed" if violations else "passed",
            "invariant_violations": invariant_violations,
            "drift_violations": drift_violations,
            "path_violations": path_violations,
            "matrix_file_violations": matrix_file_violations,
            "file_io_violations": file_io_violations,
            "sample_duration_violations": sample_duration_violations,
            "leak_violations": leaked_files,
            "strict_mode": self.strict_reliability_guards,
            "total_violations": len(violations),
        }
        if violations and self.strict_reliability_guards:
            details = "\n - ".join(["Benchmark reliability guard violations:", *violations])
            raise RuntimeError(details)

    async def run_benchmark(self):
        """Run the complete benchmark suite."""
        self.print_header()
        print(f"Active sections: {', '.join(self.enabled_sections)}")

        try:
            for section_name, section_kind, scenario, repeat in self._section_plan():
                if section_name not in self.enabled_sections:
                    continue
                if section_kind == "sync":
                    self.results[section_name] = self._run_repeated_sync(
                        section=section_name,
                        scenario=scenario,
                        repeat=repeat,
                    )
                else:
                    self.results[section_name] = await self._run_repeated_async(
                        section=section_name,
                        scenario=scenario,
                        repeat=repeat,
                    )

            # Enforce hard reliability rules before reporting/saving artifacts.
            self._enforce_reliability_guards()

            # Print detailed results
            self.print_detailed_results()

            # Save results to JSON file
            if self.save_results:
                self.save_results_to_file()

            print("\nBenchmark completed successfully")

            # Final cleanup: ensure all async handlers are properly closed
            await self._final_cleanup()

            return 0

        except Exception as e:
            print(f"\nError during benchmark: {e}")
            import traceback

            traceback.print_exc()
            # Still try to cleanup even on error
            try:
                await self._final_cleanup()
            except Exception:
                pass
            return 1


async def main(
    profile: str | None = None,
    save_results: bool = True,
    results_dir: str | None = None,
    enabled_sections: List[str] | None = None,
):
    """Main entry point for the benchmark suite."""
    benchmark = HydraLoggerBenchmark(
        save_results=save_results,
        results_dir=results_dir,
        profile=profile,
        enabled_sections=enabled_sections,
    )
    return await benchmark.run_benchmark()


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Hydra benchmark runner")
    parser.add_argument(
        "--profile",
        default=None,
        help="Benchmark profile name under benchmark/profiles (ci_smoke, pr_gate, nightly_truth).",
    )
    parser.add_argument(
        "--no-save-results",
        action="store_true",
        default=False,
        help="Do not persist benchmark result artifacts.",
    )
    parser.add_argument(
        "--results-dir",
        default=None,
        help="Custom directory for benchmark result artifacts.",
    )
    parser.add_argument(
        "--sections",
        default=None,
        help=(
            "Comma-separated benchmark section names to run. "
            "Overrides profile enabled_sections."
        ),
    )
    args = parser.parse_args()
    section_list = (
        [item.strip() for item in args.sections.split(",")] if args.sections else None
    )
    exit_code = asyncio.run(
        main(
            profile=args.profile,
            save_results=not args.no_save_results,
            results_dir=args.results_dir,
            enabled_sections=section_list,
        )
    )
    sys.exit(exit_code)
