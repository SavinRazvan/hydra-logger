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
- Logs: `logs/examples/tutorials/t01_*.jsonl`.
- Customization: logger type, destination formats, default level.

### T02 Configuration Recipes

- Goal: configure destinations, formats, and environment-aware settings.
- Logs: `logs/examples/tutorials/t02_*.jsonl`.
- Customization: layer destinations, format, level thresholds.

### T03 Layers Customization

- Goal: design layer taxonomy and route per-layer traffic.
- Logs: `logs/examples/tutorials/t03_layers_*.jsonl`.
- Customization: layer naming policy, per-layer destination policy, context fields.

### T04 Extensions and Plugins

- Goal: enable/tune built-in extensions and register custom extension types.
- Logs: `logs/examples/tutorials/t04_extensions.jsonl`.
- Customization: extension enablement, processing order, plugin registration.

### T05 Framework Patterns

- Goal: apply logging patterns to API and async worker flows.
- Logs: `logs/examples/tutorials/t05_framework_*.jsonl`.
- Customization: correlation context propagation and layer mapping.

### T06 Migration and Adoption

- Goal: migrate incrementally from legacy app logger to layered hydra logger.
- Logs: `logs/examples/tutorials/t06_migration.jsonl`.
- Customization: side-by-side rollout and rollback switch strategy.

### T07 Operational Playbook

- Goal: run preflight checks and validate onboarding rollout behavior.
- Logs: `logs/examples/tutorials/t07_ops.jsonl`.
- Customization: health checks, release gates, smoke workflow.

### T08 Console Configuration Cookbook

- Goal: configure console output policies for colors, formats, and layer behavior.
- Logs: `logs/examples/tutorials/t08_*.jsonl` and `logs/examples/tutorials/t08_*.log`.
- Customization: `use_colors`, console format, per-layer console strategy.

### T09 Levels, Columns, Date, and Destinations

- Goal: teach level inheritance/overrides and advanced formatter customization.
- Logs: `logs/examples/tutorials/t09_*.jsonl` and `logs/examples/tutorials/t09_*.log`.
- Customization: global/layer/destination levels, formatter columns, timestamp format, multi-destination routing.

## Legacy Example Mapping

- `examples/11_quick_start_basic.py` -> T01
- `examples/12_quick_start_async.py` -> T01
- `examples/01_format_control.py`, `examples/02_destination_control.py`, `examples/05_custom_configurations.py` -> T02
- `examples/07_multi_layer_colored_logging.py`, `examples/16_multi_layer_web_app.py` -> T03/T05
- `examples/03_extension_control.py`, `examples/04_runtime_control.py`, `examples/13_extension_system_example.py` -> T04
- `examples/14_class_based_logging.py`, `examples/15_eda_microservices_patterns.py` -> T05

## Validation Checklist

- Tutorial script exits `0`.
- Expected log file(s) exist in `logs/examples/tutorials/`.
- Output includes a completion marker for each track.
- Track shows at least one customization knob change from default behavior.
