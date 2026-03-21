# Tutorial notebooks

Jupyter notebooks for **hands-on onboarding**.

- **Configs:** Every notebook loads YAML/JSON from the **real** `examples/config/` directory inside your
  **hydra-logger clone** (nothing is copied into a temp `examples/config/` tree).
- **Repo resolution:** §1 (usually **collapsed**) uses `importlib` to load
  [`jupyter_workspace.py`](../jupyter_workspace.py), then **`prime_notebook_workspace()`** — which uses
  `__file__` (not Jupyter’s cwd) to anchor the clone and delegates to **`shared.path_bootstrap`** → **`utility.do_notebook_setup()`**.
- **Benchmark tutorials (T17–T19):** If `benchmark/results/*` files are missing, §1 may write **minimal
  stubs** under `benchmark/results/` in the clone so cells still run (replace with real benchmark output
  when available).

**Governance / security context:** [`docs/tutorials/ENTERPRISE_NOTEBOOKS.md`](../../../docs/tutorials/ENTERPRISE_NOTEBOOKS.md).

## Prerequisites

| Topic | Guidance |
|-------|-----------|
| **Python** | **3.11+** (matches `pyrightconfig.json` / package `python_requires`). |
| **Package** | `hydra-logger` importable in the kernel (editable install from clone, or `%pip` in §0). |
| **Repository** | **Clone** with `examples/config/` on disk; set `HYDRA_LOGGER_REPO` if Jupyter’s cwd is not the clone root. |
| **Jupyter** | JupyterLab, VS Code, or classic Notebook — any kernel that can run the repo’s Python. |
| **CI parity** | Recommended: **`.hydra_env`** as the kernel interpreter so behavior matches `pytest` and `examples/run_all_examples.py`. |
| **Network** | Optional for most tutorials; **T12–T14** may attempt outbound HTTP/WebSocket depending on config. |

## T16 vs T20

Both use **`enterprise_onboarding_starter.yaml`**.

| ID | Focus |
|----|--------|
| **T16** | **Enterprise templates at scale** — same preset, framed for broad template / multi-env patterns (pairs with `cli_tutorials/t16_*.py`). |
| **T20** | **Notebook-first onboarding** — same preset, titled for the notebook track and the “strict paths + JSONL check” walkthrough. |

## §1 workspace API

- **Collapsed code cell:** finds `examples/tutorials/jupyter_workspace.py` by walking **`HYDRA_LOGGER_REPO`**
  (if set) and the kernel cwd, then **`repo_root = _mod.prime_notebook_workspace()`**.
- **Implementations:** [`jupyter_workspace.py`](../jupyter_workspace.py), [`shared/path_bootstrap.py`](../shared/path_bootstrap.py)
  (`run_notebook_workspace_setup`), [`utility/__init__.py`](../utility/__init__.py) (`do_notebook_setup`) — not hydra-logger
  library API.
- **`HYDRA_LOGGER_REPO`:** Honored inside `prepare_notebook_workspace` for `chdir` when it points at a valid clone root.

## Typography

Notebook markdown intentionally avoids large headings (`#` / `##`). Titles use `####`; steps use
`**§N — …**` and `<small>` for hints so **code cells** stay the focus.

## What each notebook does

1. **§0** — optional `%pip install hydra-logger` (code cells tagged **`skip-ci`** for automated smoke — CI already uses an editable install).
2. **§1 — Setup** (often **collapsed**): `prime_notebook_workspace()` via `jupyter_workspace.py`. *Notebook plumbing.*
3. **§2 — Imports** / **§3 — Config path** — minimal hydra-logger surface (`CONFIG_PATH` where used).
4. **§5 — Scenario** — the tutorial’s real `create_sync_logger` / logging usage (or benchmark file reads).
5. **§6 — Results** — file tails or a short “what to expect” line.
6. **T01** adds §3 peek, §4 domain code, §5 logger run, §6 file tails (reference layout).

Use **Run All** for the full flow.

## Log and artifact locations

| Artifact | Location |
|----------|-----------|
| **Notebook file logs** | `examples/logs/notebooks/` (presets use `log_dir_name: notebooks`). |
| **Configs** | `examples/config/` in the clone (source of truth). |
| **Benchmark stubs (optional)** | `benchmark/results/` when real benchmark files are absent. |

## Troubleshooting

| Symptom | What to do |
|---------|------------|
| **`FileNotFoundError`** on `getcwd` / `Path.cwd()` during §1 | Kernel cwd pointed at a **deleted temp dir**. **Restart kernel**, **Run All** from the top. |
| **Could not find `jupyter_workspace.py`** | Set **`HYDRA_LOGGER_REPO`** to your clone (or any path inside it), or start Jupyter with cwd inside the clone so the walk can find `examples/tutorials/jupyter_workspace.py`. |
| **Network tutorials** fail offline | T12–T14 may log errors if endpoints are unreachable; the lesson is often **config shape**, not live traffic. |
| **`%pip` / kernel** issues after §0 | Restart the Jupyter kernel after pip upgrades packages. |

## Committed notebook conventions

Committed `.ipynb` files should keep **`execution_count`: null** and **empty `outputs`** on code cells so
git diffs stay small (see `tests/examples/test_tutorial_assets.py`). Clear outputs in Jupyter
(**Clear All Outputs**) before committing edits.

## Notebook files (14)

These `.ipynb` files live in this directory:

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

## Regenerating notebooks

From repository root:

```bash
python3 examples/tutorials/notebooks/temp_nb_factory/generate_notebooks.py
```

Factory sources live under `temp_nb_factory/` (may be gitignored in your checkout).
