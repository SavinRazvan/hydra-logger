# Tutorial notebooks

Jupyter notebooks for **hands-on onboarding**. Paths are **repository-relative**; the first code
cells set **`cwd`** to the repo root (or use `HYDRA_LOGGER_REPO`).

## What each notebook does

1. Adds `examples/tutorials` to `sys.path`, then **`utility.notebook_bootstrap()`** (repo root + kernel hint).
2. **Multiple cells** (especially **T01**): setup → imports → config peek → domain code →
   `create_sync_logger` + logs → optional **file tails**. Use **Run All** for the full flow.
3. Intro cells list **what to check** (console and/or `examples/logs/tutorials/`).

## Generated files (14)

Regenerated from `temp_nb_factory/` — keep this list aligned with `generate_notebooks.py` →
`TUTORIAL_SPECS`:

| File |
|------|
| `t01_production_quick_start.ipynb` |
| `t02_configuration_recipes.ipynb` |
| `t03_layers_customization.ipynb` |
| `t04_extensions_plugins.ipynb` |
| `t08_console_configuration_cookbook.ipynb` |
| `t09_levels_columns_date_and_destinations.ipynb` |
| `t12_network_http_typed_destination.ipynb` |
| `t13_network_ws_resilient_typed_destination.ipynb` |
| `t14_network_local_http_simulation.ipynb` |
| `t16_enterprise_config_templates_at_scale.ipynb` |
| `t17_enterprise_benchmark_comparison_workflow.ipynb` |
| `t18_enterprise_bring_your_own_config_benchmark.ipynb` |
| `t19_enterprise_nightly_drift_snapshot.ipynb` |
| `t20_notebook_hydra_config_onboarding.ipynb` |

Scripts without a matching notebook today: `t05`, `t06`, `t07`, `t10`, `t11`, `t15` (Python only).

## Regenerate

From repository root:

```bash
python3 examples/tutorials/notebooks/temp_nb_factory/generate_notebooks.py
```

- Scenario bodies: `temp_nb_factory/scenarios.py`
- Layout + T01 cells: `temp_nb_factory/generate_notebooks.py`

## Kernel

Use **`.hydra_env`** as the Jupyter kernel so `import hydra_logger` matches CI and
`examples/run_all_examples.py` (Python tutorials).

## Parent index

- [`examples/tutorials/README.md`](../README.md) — full tutorial index + validation commands
- [`examples/README.md`](../../README.md) — examples tree
