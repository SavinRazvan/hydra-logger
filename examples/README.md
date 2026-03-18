# Hydra-Logger Examples and Tutorials

This directory now has two onboarding layers:

- **Legacy numbered examples (`01`-`16`)** for feature-by-feature exploration.
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
```

## Full Example Verification

Run the legacy examples runner:

```bash
.hydra_env/bin/python examples/run_all_examples.py
```

This executes all numbered examples, verifies generated logs, and reports pass/fail with diagnostics.

## Legacy Example Catalog

Each example writes output to `logs/examples/`.

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

## Onboarding Guidance

- Use `.hydra_env/bin/python` commands from the repository root.
- Confirm environment health before onboarding rollout:
  - `.hydra_env/bin/python scripts/dev/check_env_health.py --strict`
- Keep layer naming consistent across services (for example `api`, `database`, `auth`, `worker`, `audit`).
- Prefer `json-lines` file output for production ingestion pipelines.
