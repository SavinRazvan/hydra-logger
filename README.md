# HYDRA-LOGGER

[![CI](https://github.com/SavinRazvan/hydra-logger/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/SavinRazvan/hydra-logger/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://github.com/SavinRazvan/hydra-logger/blob/main/setup.py)
[![Coverage](https://codecov.io/gh/SavinRazvan/hydra-logger/branch/main/graph/badge.svg)](https://codecov.io/gh/SavinRazvan/hydra-logger)
[![License](https://img.shields.io/github/license/SavinRazvan/hydra-logger)](https://github.com/SavinRazvan/hydra-logger/blob/main/LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/hydra-logger?color=blue)](https://pypi.org/project/hydra-logger/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/hydra-logger?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=MAGENTA&left_text=downloads)](https://pepy.tech/projects/hydra-logger)

`hydra-logger` is a modular Python logging library for teams that need configurable logging without coupling application code to fixed transports or formats.

Best fit:
- teams that need structured logging with strict reliability controls
- services that route logs by layer, destination, and policy
- organizations migrating from ad-hoc logging to consistent standards

## Overview

Core capabilities:
- Sync, async, and composite logger types
- Layer-based routing with per-layer destinations and levels
- Console, file, network, and null handlers
- Plain text, colored, JSON lines, and structured formats
- Optional extensions (for example security and performance)

Design principles:
- Keep implementation simple and maintainable
- Favor configuration over hardcoded behavior
- Keep module boundaries explicit and extensible

Quick links:
- [Environment setup](docs/ENVIRONMENT_SETUP.md)
- [Enterprise tutorials](examples/tutorials/README.md)
- [Configuration reference](docs/modules/config.md)
- [Operations diagnostics](docs/OPERATIONS.md)
- [Release policy & API compatibility](docs/RELEASE_POLICY.md)
- [Testing and quality gates](docs/TESTING.md)
- [Performance and benchmarks](docs/PERFORMANCE.md)

## Why Teams Choose Hydra-Logger

Hydra-Logger gives teams production-ready logging with clear defaults, strong
reliability controls, and high throughput.

- Built for real systems: sync, async, and composite logger runtimes
- Policy-driven routing: layers, per-destination levels, and typed network destinations
- Safety-first: strict reliability guards, path controls, and extension-based data protection
- Proven performance: benchmarked profiles with drift and reliability checks (`nightly_truth`)

Latest nightly snapshot (`benchmark/results/benchmark_latest.json`):
- Reliability status: `passed` (strict mode enabled)
- Drift status: `passed`
- Sync throughput: ~`53.7k msg/s`
- Async throughput: ~`44.5k msg/s`
- Concurrent throughput: ~`283.4k msg/s`

Benchmark details:
- [`benchmark/README.md`](benchmark/README.md)
- [`benchmark/results/benchmark_latest_summary.md`](benchmark/results/benchmark_latest_summary.md)

Start quickly:

```bash
pip install hydra-logger
.hydra_env/bin/python examples/tutorials/t01_production_quick_start.py
```

Examples and tutorials:

- Tutorial tracks: [`examples/tutorials/README.md`](examples/tutorials/README.md)
- Full examples catalog: [`examples/README.md`](examples/README.md)
- Run examples individually with `.hydra_env/bin/python <script_path>`.
- Most tutorials write to `logs/examples/...`; network simulation tutorials may also
  emit local result artifacts.

## Install

```bash
pip install hydra-logger
```

Core install includes only required baseline dependencies. Optional extras install
dependency bundles for specific integration scenarios (including custom handlers and
application-side adapters), for example:

```bash
pip install "hydra-logger[network]"
pip install "hydra-logger[perf]"
pip install "hydra-logger[database,cloud,queues]"
pip install "hydra-logger[full]"
```

Notes about extras:
- `network` supports built-in typed network destinations (`network_http`, `network_ws`, `network_socket`, `network_datagram`).
- `database`, `cloud`, `queues`, and `system` provide optional dependency bundles for advanced/custom integrations.

Development environment:

```bash
# Option A (venv)
python3 -m venv .hydra_env
source .hydra_env/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
python -m pip install pyright

# Option B (Conda prefix)
conda env create -p ./.hydra_env -f environment.yml
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$(pwd)/.hydra_env"
```

Environment maintenance and troubleshooting are documented in `docs/ENVIRONMENT_SETUP.md`.

## Quick Start

```python
from hydra_logger import LoggingConfig, LogLayer, LogDestination, create_logger

config = LoggingConfig(
    layers={
        "app": LogLayer(
            destinations=[
                LogDestination(type="console", format="colored", use_colors=True),
                LogDestination(type="file", path="app.log", format="json-lines"),
            ]
        )
    }
)

with create_logger(config, logger_type="sync") as logger:
    logger.info("Application started", layer="app")
    logger.warning("Low memory", layer="app")
    logger.error("Database connection failed", layer="app")
```

Async variant:

```python
import asyncio
from hydra_logger import create_async_logger


async def main():
    async with create_async_logger("MyAsyncApp") as logger:
        await logger.info("Async logging works")
        await logger.warning("Async warning message")


asyncio.run(main())
```

## Configuration

Format configuration:

```python
config = LoggingConfig(
    layers={
        "app": LogLayer(
            destinations=[
                LogDestination(type="console", format="json", use_colors=True),
                LogDestination(type="file", path="app.log", format="plain-text"),
                LogDestination(type="file", path="app_structured.jsonl", format="json-lines"),
            ]
        )
    }
)
```

Destination configuration:

```python
config = LoggingConfig(
    layers={
        "api": LogLayer(
            destinations=[
                LogDestination(type="console", format="colored"),
                LogDestination(type="file", path="api.log", format="json-lines"),
            ]
        )
    }
)
```

Typed network destination configuration (FastAPI-style DX):

```python
config = LoggingConfig(
    layers={
        "webhook": LogLayer(
            destinations=[
                LogDestination(
                    type="network_http",
                    url="https://logs.example.com/ingest",
                    timeout=5.0,
                    retry_count=3,
                    retry_delay=0.5,
                )
            ]
        ),
        "streaming": LogLayer(
            destinations=[
                LogDestination(
                    type="network_ws",
                    url="wss://stream.example.com/events",
                    timeout=10.0,
                    retry_count=5,
                    retry_delay=1.0,
                )
            ]
        ),
    }
)
```

Network migration guidance:

- Prefer explicit typed destinations: `network_http`, `network_ws`, `network_socket`, `network_datagram`.
- Legacy `network` remains transitional and is mapped to `network_http` when `url` is provided.
- Update legacy `network` configs incrementally to typed variants to avoid future deprecation friction.

Network behavior (operational):

- **HTTP probe**: `HTTPHandler` runs a separate connectivity probe before use. Default probe uses **GET**
  (backward compatible). Set `LogDestination.probe_method` to `HEAD`, `OPTIONS`, or `none`, or
  `connection_probe=False`, if your ingest endpoint must not observe GET side effects.
- **WebSocket**: `WebSocketHandler` currently uses a **simulated** transport (records are not sent over
  the wire); a `UserWarning` is emitted once per process on first emit. Treat `network_ws` as
  simulation until a real client integration ships.
- **Unknown / unsupported destinations** resolve to a **no-op** `NullHandler`. With
  `reliability_error_policy="warn"` or strict reliability, the runtime surfaces this instead of failing
  silently.
- **Composite async direct I/O**: `CompositeAsyncLogger` with `use_direct_io=True` flushes file writes
  via a thread pool when an event loop is running, to avoid blocking the loop; sync `close()` still
  flushes on-thread.

Extension configuration:

```python
config = LoggingConfig(
    enable_data_protection=True,
    extensions={
        "data_protection": {
            "enabled": True,
            "type": "security",
            "patterns": ["email", "phone", "api_key"],
        }
    }
)
```

Optional async runtime queue mode (opt-in, default behavior unchanged):

```python
config = LoggingConfig(
    layers={
        "default": LogLayer(destinations=[LogDestination(type="async_file", path="app.jsonl")])
    },
    extensions={
        "async_runtime": {
            "mode": "queue",              # default is task scheduling mode
            "worker_count": 2,            # async queue workers
            "max_queue_size": 20000,      # bounded queue for backpressure
            "overflow_policy": "drop_newest",  # drop_newest | drop_oldest | block_with_timeout
            "put_timeout_seconds": 0.01,  # used when overflow_policy=block_with_timeout
        }
    },
)
```

Enterprise hardening profile (strict reliability is opt-in and does not change default template behavior):

```python
from hydra_logger.config.defaults import get_enterprise_config

config = get_enterprise_config()
# Highlights:
# - strict_reliability_mode=True
# - reliability_error_policy="warn"
# - enforce_log_path_confinement=True
# - allow_absolute_log_paths=False
```

Log file location policy:

- `hydra_logger` does not create log directories on import/install.
- Log directories are created only when file destinations are configured and initialized.
- Default behavior (no `base_log_dir`) writes to `<current working directory>/logs`.
- For strict confinement to project-owned paths, set:

```python
config = LoggingConfig(
    base_log_dir="logs",
    enforce_log_path_confinement=True,
    allow_absolute_log_paths=False,
)
```

## Architecture

System flow (high-level):

```mermaid
flowchart TD
  n_app["Application Code"] --> n_call["logger.info message call"]
  n_call --> n_logger_layer["Logger Layer"]
  n_logger_layer --> n_sync["SyncLogger"]
  n_logger_layer --> n_async["AsyncLogger"]
  n_logger_layer --> n_composite["CompositeLogger"]
  n_logger_layer --> n_composite_async["CompositeAsyncLogger"]
  n_sync --> n_layer_manager["Layer Manager"]
  n_async --> n_layer_manager
  n_composite --> n_layer_manager
  n_composite_async --> n_layer_manager
  n_layer_manager --> n_handlers["Handler System"]
  n_handlers --> n_console["Console"]
  n_handlers --> n_file["File"]
  n_handlers --> n_network["Network"]
```

Detailed architecture and workflow documentation:
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/WORKFLOW_ARCHITECTURE.md`](docs/WORKFLOW_ARCHITECTURE.md)
- [`docs/modules/README.md`](docs/modules/README.md)

## Operations

Quality and validation commands:

```bash
# Environment preflight
.hydra_env/bin/python scripts/dev/check_env_health.py --strict

# Test gate
.hydra_env/bin/python -m pytest -q

# Run all examples
.hydra_env/bin/python examples/run_all_examples.py

# Performance benchmark
.hydra_env/bin/python benchmark/performance_benchmark.py

# Runtime guard (forbid blocking runtime calls in hydra_logger)
.hydra_env/bin/python -m pytest tests/quality/test_runtime_blocking_calls.py -q
```

Enterprise tutorial tracks:

```bash
.hydra_env/bin/python examples/tutorials/t01_production_quick_start.py
.hydra_env/bin/python examples/tutorials/t03_layers_customization.py
.hydra_env/bin/python examples/tutorials/t04_extensions_plugins.py
.hydra_env/bin/python examples/tutorials/t07_operational_playbook.py
.hydra_env/bin/python examples/tutorials/t10_enterprise_profile_config.py
.hydra_env/bin/python examples/tutorials/t11_enterprise_policy_layers.py
.hydra_env/bin/python examples/tutorials/t12_network_http_typed_destination.py
.hydra_env/bin/python examples/tutorials/t13_network_ws_resilient_typed_destination.py
.hydra_env/bin/python examples/tutorials/t14_network_local_http_simulation.py
```

## Documentation

### Start Here (Users)

- [Environment setup and troubleshooting](docs/ENVIRONMENT_SETUP.md)
- [Enterprise tutorials index](examples/tutorials/README.md)
- [Examples catalog](examples/README.md)
- [Configuration reference](docs/modules/config.md)

### Design and Runtime

- [Architecture overview](docs/ARCHITECTURE.md)
- [Runtime workflow architecture](docs/WORKFLOW_ARCHITECTURE.md)
- [Module map and ownership](docs/modules/README.md)

### Operate and Validate

- [Operations diagnostics](docs/OPERATIONS.md)
- [Testing strategy and quality gates](docs/TESTING.md)
- [Performance guidance](docs/PERFORMANCE.md)
- [Benchmark usage guide](benchmark/README.md)

### Troubleshooting

- [Environment health checks](docs/ENVIRONMENT_SETUP.md)
- [Runtime diagnostics and triage](docs/OPERATIONS.md)
- [Performance regression troubleshooting](docs/PERFORMANCE.md)

### Maintainers and Release

- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Agent automation workflow](docs/AGENT_AUTOMATION.md)
- [Changelog](CHANGELOG.md)

Internal planning and audit trackers are maintained under `docs/plans/`,
`docs/audit/`, and `docs/archive/` for repository governance and historical
traceability.

## Contributing

- Keep changes focused and maintain backward compatibility for public APIs
- Add or update tests in `tests/` for behavior changes
- Update docs when behavior or public interfaces change
- Run `pre-commit` and `.hydra_env/bin/python -m pytest -q` before opening a PR
- Run release preflight before tagging/publishing: `.hydra_env/bin/python scripts/release/preflight.py`
- Follow `docs/RELEASE_CHECKLIST.md` for release evidence and final gate order

## License

MIT. See `LICENSE`.
