# Tutorial notebook factory

Generated `.ipynb` files under `../` are built from Python (valid cells). Notebooks resolve the clone and
read presets from `examples/config/` — they do **not** embed or mirror config files.

## Layout

| File | Purpose |
|------|---------|
| `factory_import_setup.py` | Ensures this directory is on `sys.path` (IDE / debugger / `runpy` safe). |
| `nb_factory_core.py` | Specs, `bootstrap_snippet` (importlib → `jupyter_workspace.prime_notebook_workspace`), cell builders, `build_tutorial_notebook`, `write_notebook_json`. |
| `scenarios.py` | `scenario_imports` / `scenario_main` / `scenario_results_code`, `SCENARIO_INSPECT`, `build_scenario_code` (legacy concat). |
| `generate_<stem>.py` | Regenerate **one** notebook (low friction while editing). |
| `generate_notebooks.py` | Regenerate **all** notebooks (kept until explicitly retired). |

## Regenerate one notebook

From repository root:

```bash
python3 examples/tutorials/notebooks/temp_nb_factory/generate_t03_layers_customization.py
```

## Regenerate everything

```bash
python3 examples/tutorials/notebooks/temp_nb_factory/generate_notebooks.py
```

**Note:** Run these from a checkout that contains `examples/config/` and `examples/tutorials/jupyter_workspace.py` — notebooks load both at runtime.

- **Committed `.ipynb`:** `write_notebook_json` clears `execution_count` and `outputs` for small git diffs.
- **Repo log dir:** presets use `examples/logs/notebooks/`; `scenarios._log_root_expr()` must stay aligned.
- **§0 `%pip` cells** carry metadata tag `skip-ci` for `scripts/dev/run_notebook_smoke.py` (CI uses editable install).

Parent docs: [`../README.md`](../README.md), [`../../README.md`](../../README.md).
