# Enterprise Tutorials

Use this directory for enterprise onboarding tutorials.

## Shared utilities (`utility/`)

Package `examples/tutorials/utility` holds **notebook bootstrap** helpers so cells do not repeat
`detect_repo_root` / `chdir` / kernel warnings:

| API | Purpose |
| --- | --- |
| `notebook_bootstrap()` | After `sys.path` is set: `chdir` to repo root, kernel warning, print root. |
| `find_repo_root()` | Locate repo from `Path.cwd()` (or a given start path). |
| `ensure_tutorials_importable()` | `sys.path` insert so `import utility` works. |
| `tutorial_config_path("foo.yaml")` | `examples/config/foo.yaml` under the repo. |
| `tutorial_logs_dir()` | `examples/logs/tutorials/`. |

**Launch Jupyter from the repository root** (the folder that contains `hydra_logger/` and
`examples/`), e.g. `cd path/to/hydra-logger && .hydra_env/bin/jupyter lab`.  
If you cannot do that, set `HYDRA_LOGGER_REPO` to that path before starting Jupyter.

Generated notebooks insert `examples/tutorials` on `sys.path`, then call `notebook_bootstrap()`
(see `temp_nb_factory/generate_notebooks.py`).

## Python Track

Runnable scripts in `examples/tutorials/python/`:

- `t01_production_quick_start.py`
- `t02_configuration_recipes.py`
- `t03_layers_customization.py`
- `t04_extensions_plugins.py`
- `t05_framework_patterns.py`
- `t06_migration_adoption.py`
- `t07_operational_playbook.py`
- `t08_console_configuration_cookbook.py`
- `t09_levels_columns_date_and_destinations.py`
- `t10_enterprise_profile_config.py`
- `t11_enterprise_policy_layers.py`
- `t12_network_http_typed_destination.py`
- `t13_network_ws_resilient_typed_destination.py`
- `t14_network_local_http_simulation.py`
- `t15_enterprise_network_hardening_playbook.py`
- `t16_enterprise_config_templates_at_scale.py`
- `t17_enterprise_benchmark_comparison_workflow.py`
- `t18_enterprise_bring_your_own_config_benchmark.py`
- `t19_enterprise_nightly_drift_snapshot.py`
- `t20_notebook_hydra_config_onboarding.py`

Run example:

```bash
.hydra_env/bin/python examples/tutorials/python/t01_production_quick_start.py
```

## Notebook Track

Guided notebooks in `examples/tutorials/notebooks/`. See
[`notebooks/README.md`](notebooks/README.md) for how they are generated and what each run should print.

Notebooks in `examples/tutorials/notebooks/`:

- `t01_production_quick_start.ipynb` (hybrid companion)
- `t02_configuration_recipes.ipynb`
- `t03_layers_customization.ipynb`
- `t04_extensions_plugins.ipynb` (hybrid companion)
- `t08_console_configuration_cookbook.ipynb`
- `t09_levels_columns_date_and_destinations.ipynb`
- `t12_network_http_typed_destination.ipynb` (hybrid companion)
- `t13_network_ws_resilient_typed_destination.ipynb` (hybrid companion)
- `t14_network_local_http_simulation.ipynb` (hybrid companion)
- `t16_enterprise_config_templates_at_scale.ipynb`
- `t17_enterprise_benchmark_comparison_workflow.ipynb`
- `t18_enterprise_bring_your_own_config_benchmark.ipynb`
- `t19_enterprise_nightly_drift_snapshot.ipynb`
- `t20_notebook_hydra_config_onboarding.ipynb`

Open notebook:

```bash
.hydra_env/bin/python -m jupyter lab examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb
```

## Shared Helpers

Shared utilities are in `examples/tutorials/shared/`.
# Enterprise Tutorials

This directory provides two complementary tracks.

## Python Track

Runnable scripts with deterministic outputs:

- `python/t01_production_quick_start.py`
- `python/t02_configuration_recipes.py`
- `python/t03_layers_customization.py`
- `python/t04_extensions_plugins.py`
- `python/t05_framework_patterns.py`
- `python/t06_migration_adoption.py`
- `python/t07_operational_playbook.py`
- `python/t08_console_configuration_cookbook.py`
- `python/t09_levels_columns_date_and_destinations.py`
- `python/t10_enterprise_profile_config.py`
- `python/t11_enterprise_policy_layers.py`
- `python/t12_network_http_typed_destination.py`
- `python/t13_network_ws_resilient_typed_destination.py`
- `python/t14_network_local_http_simulation.py`
- `python/t15_enterprise_network_hardening_playbook.py`

Run any script:

```bash
.hydra_env/bin/python examples/tutorials/python/t01_production_quick_start.py
```

## Notebook Track

Guided learning notebooks:

- `notebooks/t01_production_quick_start.ipynb` (hybrid companion)
- `notebooks/t02_configuration_recipes.ipynb`
- `notebooks/t03_layers_customization.ipynb`
- `notebooks/t04_extensions_plugins.ipynb` (hybrid companion)
- `notebooks/t08_console_configuration_cookbook.ipynb`
- `notebooks/t09_levels_columns_date_and_destinations.ipynb`
- `notebooks/t12_network_http_typed_destination.ipynb` (hybrid companion)
- `notebooks/t13_network_ws_resilient_typed_destination.ipynb` (hybrid companion)
- `notebooks/t14_network_local_http_simulation.ipynb` (hybrid companion)
- `notebooks/t16_enterprise_config_templates_at_scale.ipynb`
- `notebooks/t17_enterprise_benchmark_comparison_workflow.ipynb`
- `notebooks/t18_enterprise_bring_your_own_config_benchmark.ipynb`
- `notebooks/t19_enterprise_nightly_drift_snapshot.ipynb`
- `notebooks/t20_notebook_hydra_config_onboarding.ipynb`

Open notebooks:

```bash
.hydra_env/bin/python -m jupyter lab examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb
```

## Shared Helpers

`shared/` contains reusable helpers for path bootstrap and output checks.
# Enterprise Onboarding Tutorials

This tutorial suite upgrades the examples folder into a deterministic onboarding path for mixed enterprise audiences:

- backend engineering teams
- platform/SRE teams
- full-stack product teams

## Deterministic Run Commands

Run tutorials with the project environment to avoid import drift:

```bash
.hydra_env/bin/python examples/tutorials/t01_production_quick_start.py
.hydra_env/bin/python examples/tutorials/t02_configuration_recipes.py
.hydra_env/bin/python examples/tutorials/t03_layers_customization.py
.hydra_env/bin/python examples/tutorials/t04_extensions_plugins.py
.hydra_env/bin/python examples/tutorials/t05_framework_patterns.py
.hydra_env/bin/python examples/tutorials/t06_migration_adoption.py
.hydra_env/bin/python examples/tutorials/t07_operational_playbook.py
.hydra_env/bin/python examples/tutorials/t08_console_configuration_cookbook.py
.hydra_env/bin/python examples/tutorials/t09_levels_columns_date_and_destinations.py
.hydra_env/bin/python examples/tutorials/t10_enterprise_profile_config.py
.hydra_env/bin/python examples/tutorials/t11_enterprise_policy_layers.py
.hydra_env/bin/python examples/tutorials/t12_network_http_typed_destination.py
.hydra_env/bin/python examples/tutorials/t13_network_ws_resilient_typed_destination.py
.hydra_env/bin/python examples/tutorials/t14_network_local_http_simulation.py
.hydra_env/bin/python examples/tutorials/t15_enterprise_network_hardening_playbook.py
.hydra_env/bin/python examples/tutorials/t16_enterprise_config_templates_at_scale.py
.hydra_env/bin/python examples/tutorials/t17_enterprise_benchmark_comparison_workflow.py
.hydra_env/bin/python examples/tutorials/t18_enterprise_bring_your_own_config_benchmark.py
.hydra_env/bin/python examples/tutorials/t19_enterprise_nightly_drift_snapshot.py --profile ci_smoke
# Optional heavy run:
# .hydra_env/bin/python examples/tutorials/t19_enterprise_nightly_drift_snapshot.py --profile nightly_truth --run-benchmark
```

Notebook variant:

```bash
.hydra_env/bin/python -m jupyter lab examples/tutorials/t20_notebook_hydra_config_onboarding.ipynb
```

## Track Matrix

Each track follows this recommended structure:

1. Goal
2. Prerequisites
3. Run
4. Expected output
5. Customization knobs
6. Failure modes
7. Production notes

### T01 Production Quick Start

- Goal: choose sync/async/composite logger patterns with safe defaults.
- Logs: `examples/logs/tutorials/t01_app.jsonl`, `t01_audit.log`, `t01_error.jsonl` (layered demo).
- Customization: logger type, destination formats, default level.

### T02 Configuration Recipes

- Goal: configure destinations, formats, and environment-aware settings.
- Logs: `examples/logs/tutorials/t02_*.jsonl`.
- Customization: layer destinations, format, level thresholds.

### T03 Layers Customization

- Goal: design layer taxonomy and route per-layer traffic.
- Logs: `examples/logs/tutorials/t03_layers_*.jsonl`.
- Customization: layer naming policy, per-layer destination policy, context fields.

### T04 Extensions and Plugins

- Goal: enable/tune built-in extensions and register custom extension types.
- Logs: `examples/logs/tutorials/t04_extensions.jsonl`.
- Customization: extension enablement, processing order, plugin registration.

### T05 Framework Patterns

- Goal: apply logging patterns to API and async worker flows.
- Logs: `examples/logs/tutorials/t05_framework_*.jsonl`.
- Customization: correlation context propagation and layer mapping.

### T06 Migration and Adoption

- Goal: migrate incrementally from legacy app logger to layered hydra logger.
- Logs: `examples/logs/tutorials/t06_migration.jsonl`.
- Customization: side-by-side rollout and rollback switch strategy.

### T07 Operational Playbook

- Goal: run preflight checks and validate onboarding rollout behavior.
- Logs: `examples/logs/tutorials/t07_ops.jsonl`.
- Customization: health checks, release gates, smoke workflow.

### T08 Console Configuration Cookbook

- Goal: configure console output policies for colors, formats, and layer behavior.
- Logs: `examples/logs/tutorials/t08_*.jsonl` and `examples/logs/tutorials/t08_*.log`.
- Customization: `use_colors`, console format, per-layer console strategy.

### T09 Levels, Columns, Date, and Destinations

- Goal: teach level inheritance/overrides and advanced formatter customization.
- Logs: `examples/logs/tutorials/t09_*.jsonl` and `examples/logs/tutorials/t09_*.log`.
- Customization: global/layer/destination levels, formatter columns, timestamp format, multi-destination routing.

### T10 Enterprise Profile Configuration

- Goal: validate enterprise-ready defaults from `get_enterprise_config`.
- Logs: `examples/logs/tutorials/t10_*.log` and `examples/logs/tutorials/t10_*.jsonl` (tutorial-normalized outputs).
- Customization: reliability and path-confinement controls on enterprise profile.
- Runtime note: tutorial applies compatibility shims (`async_runtime` removal and temporary absolute-path allowance) so execution remains deterministic with current runtime constraints.

### T11 Enterprise Policy Layers and Routing

- Goal: apply enterprise policy controls to multi-layer routing and destination overrides.
- Logs: `examples/logs/tutorials/t11_*.jsonl` and `examples/logs/tutorials/t11_audit.log`.
- Customization: layer-level policy, destination-level filtering, and context propagation.

### T12 Typed Network HTTP Destination

- Goal: onboard typed `network_http` destination configuration with strict validation.
- Logs/artifacts: `examples/logs/tutorials/t12_network_http_stub_results.json`.
- Customization: `url`, `timeout`, `retry_count`, `retry_delay`, and header credentials.

### T13 Resilient Typed Network WebSocket Destination

- Goal: onboard typed `network_ws` destination with resilient retry semantics.
- Logs/artifacts: `examples/logs/tutorials/t13_network_ws_stub_results.json`.
- Customization: `url`, retry controls, and resilient stream-layer routing policy.

### T14 Local HTTP Route Simulation

- Goal: validate typed `network_http` end-to-end against a local `/ingest` simulation route.
- Logs/artifacts: `examples/logs/tutorials/t14_network_ingest_payloads.json`.
- Customization: local route path/port, retry policy, payload assertions.

### T15 Enterprise Network Hardening Playbook

- Goal: combine typed HTTP/WS destinations with strict reliability-oriented runtime posture.
- Logs/artifacts: `examples/logs/tutorials/t15_network_hardening_results.json`.
- Customization: retry policy, credentials headers, reliability mode, and network layer split.

### T16 Enterprise Config Templates at Scale

- Goal: use YAML template composition (`extends`) and JSON runtime configs in one rollout track.
- Logs/artifacts: `examples/logs/tutorials/t16_config_templates_summary.json` and generated config files under `examples/logs/tutorials/t16_configs/`.
- Customization: YAML overlay policy, strict unknown fields, JSON destination maps.

### T17 Enterprise Benchmark Comparison Workflow

- Goal: persist benchmark runs and compare latest vs previous signals using saved artifacts.
- Logs/artifacts: benchmark runs under `benchmark/results/tutorials/t17_enterprise/<date>/` and summary at `examples/logs/tutorials/t17_benchmark_comparison_summary.json`.
- Customization: profile choice, results directory strategy, nightly command scheduling.

### T18 Enterprise Bring-Your-Own-Config Benchmark

- Goal: validate user-owned YAML config files with `config_path` and run persisted benchmark artifacts in the same onboarding flow.
- Logs/artifacts: `examples/logs/tutorials/t18_configs/enterprise_user_config.yaml`, summary at `examples/logs/tutorials/t18_byoc_benchmark_summary.json`, and benchmark artifacts under `benchmark/results/tutorials/t18_byoc/<date>/`.
- Customization: user config schema, strict unknown field validation, benchmark profile/results retention strategy.

### T19 Enterprise Nightly Drift Snapshot

- Goal: generate a compact performance drift snapshot (latest vs previous) for a benchmark profile.
- Logs/artifacts: `examples/logs/tutorials/t19_nightly_drift_snapshot.json`.
- Customization: profile selection (`ci_smoke`, `pr_gate`, `nightly_truth`) and optional fresh benchmark execution with `--run-benchmark`.

### T20 Notebook: Config File -> Runtime Logging

- Goal: interactive, end-to-end onboarding in Jupyter (write YAML, load `config_path`, emit logs, inspect artifacts).
- Notebook: `examples/tutorials/t20_notebook_hydra_config_onboarding.ipynb`.
- Outputs: `examples/logs/tutorials/t20_*.jsonl` and `examples/logs/tutorials/t20_audit.log`.

## Legacy Example Mapping

- `examples/11_quick_start_basic.py` -> T01
- `examples/12_quick_start_async.py` -> T01
- `examples/01_format_control.py`, `examples/02_destination_control.py`, `examples/05_custom_configurations.py` -> T02
- `examples/07_multi_layer_colored_logging.py`, `examples/16_multi_layer_web_app.py` -> T03/T05
- `examples/03_extension_control.py`, `examples/04_runtime_control.py`, `examples/13_extension_system_example.py` -> T04
- `examples/14_class_based_logging.py`, `examples/15_eda_microservices_patterns.py` -> T05

## Validation Checklist

- Tutorial script exits `0`.
- Expected tutorial artifact(s) exist (`examples/logs/tutorials/` logs and network result JSON where applicable).
- Output includes a completion marker for each track.
- Track shows at least one customization knob change from default behavior.
