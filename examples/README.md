# Hydra-Logger Examples

This folder contains the canonical onboarding structure for `hydra-logger`.

## Structure

- `examples/config/` - standardized configuration presets
- `examples/tutorials/python/` - runnable tutorial scripts
- `examples/tutorials/notebooks/` - guided notebook tutorials
- `examples/tutorials/shared/` - shared tutorial helpers
- `examples/run_all_examples.py` - runner for canonical Python tutorials

## Start Here

- Tutorial index: [`examples/tutorials/README.md`](tutorials/README.md)
- Config preset guide: [`examples/config/README.md`](config/README.md)

## Deterministic Commands

Run tutorial scripts:

```bash
.hydra_env/bin/python examples/tutorials/python/t01_production_quick_start.py
.hydra_env/bin/python examples/tutorials/python/t05_framework_patterns.py
.hydra_env/bin/python examples/tutorials/python/t15_enterprise_network_hardening_playbook.py
```

Run all canonical Python tutorials:

```bash
.hydra_env/bin/python examples/run_all_examples.py
```

Open notebooks:

```bash
.hydra_env/bin/python -m jupyter lab examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb
```
# Hydra-Logger Examples

This folder is the canonical onboarding surface for `hydra-logger`.

## Structure

- `examples/config/` - reusable configuration presets
- `examples/tutorials/python/` - runnable tutorial scripts
- `examples/tutorials/notebooks/` - guided notebook tutorials
- `examples/tutorials/shared/` - shared helper utilities

## Start Here

- Tutorial index: [`examples/tutorials/README.md`](tutorials/README.md)
- Config preset guide: [`examples/config/README.md`](config/README.md)

## Deterministic Runs

Run tutorial scripts from repository root:

```bash
.hydra_env/bin/python examples/tutorials/python/t01_production_quick_start.py
.hydra_env/bin/python examples/tutorials/python/t05_framework_patterns.py
.hydra_env/bin/python examples/tutorials/python/t15_enterprise_network_hardening_playbook.py
```

Run all canonical Python tutorials:

```bash
.hydra_env/bin/python examples/run_all_examples.py
```

Open notebook tutorials:

```bash
.hydra_env/bin/python -m jupyter lab examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb
```
# Hydra-Logger Examples and Tutorials

This directory now has two onboarding layers:

- **Legacy numbered examples (`01`-`17`)** for feature-by-feature exploration.
- **Enterprise tutorial tracks (`tutorials/`)** for production onboarding.

## Enterprise Onboarding First

For enterprise onboarding, start here:

- [`examples/tutorials/README.md`](tutorials/README.md)

Run each tutorial with deterministic environment commands:

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
.hydra_env/bin/python -m jupyter lab examples/tutorials/t20_notebook_hydra_config_onboarding.ipynb
```

## Full Example Verification

Run the legacy examples runner:

```bash
.hydra_env/bin/python examples/run_all_examples.py
```

This executes all numbered examples, verifies generated logs, and reports pass/fail with diagnostics.

## Legacy Example Catalog

Most examples write output to `examples/logs/`; network-focused examples can produce JSON artifacts instead.

1. `01_format_control.py` - format control
2. `02_destination_control.py` - destination control
3. `03_extension_control.py` - extension toggles
4. `04_runtime_control.py` - runtime extension management
5. `05_custom_configurations.py` - custom config composition
6. `06_basic_colored_logging.py` - basic colored output
7. `07_multi_layer_colored_logging.py` - per-layer coloring
8. `08_mixed_console_file_output.py` - console + file output split
9. `09_all_logger_types_colors.py` - sync/async/composite types
10. `10_disable_colors.py` - non-colored output policy
11. `11_quick_start_basic.py` - synchronous quick start
12. `12_quick_start_async.py` - async quick start
13. `13_extension_system_example.py` - extension configuration
14. `14_class_based_logging.py` - class-based integration
15. `15_eda_microservices_patterns.py` - EDA and microservices pattern
16. `16_multi_layer_web_app.py` - multi-layer web app simulation
17. `17_network_typed_destinations.py` - typed HTTP/WS network destination routing

## Config Presets

Reusable onboarding config packs live in `examples/config/`.

- Start guide: `examples/config/README.md`
- Includes minimal/base overlays, strict production preset, multi-layer service preset,
  and typed network destination presets (HTTP/WS/socket/datagram).

## Onboarding Guidance

- Use `.hydra_env/bin/python` commands from the repository root.
- Confirm environment health before onboarding rollout:
  - `.hydra_env/bin/python scripts/dev/check_env_health.py --strict`
- Keep layer naming consistent across services (for example `api`, `database`, `auth`, `worker`, `audit`).
- Prefer `json-lines` file output for production ingestion pipelines.
