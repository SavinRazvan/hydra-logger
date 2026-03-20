# Enterprise tutorials

Deterministic onboarding for `hydra-logger`: **Python scripts** (`t01`–`t20`), **Jupyter notebooks**
(same IDs where present), and shared **config** under `examples/config/`.

## Validation

| Check | Command |
|-------|---------|
| Pytest (assets, runners, branches, `utility`) | `.hydra_env/bin/python -m pytest tests/examples -q` |
| Smoke all Python tutorials | `.hydra_env/bin/python examples/run_all_examples.py` |

Notebooks are **generated** from `notebooks/temp_nb_factory/`; they are not executed in default CI
(dependency on Jupyter). Regenerate after changing factory or scenarios:

```bash
python3 examples/tutorials/notebooks/temp_nb_factory/generate_notebooks.py
```

## Notebook bootstrap (`utility/`)

`examples/tutorials/utility` provides **`notebook_bootstrap()`** and path helpers so notebook cells
stay short. Notebooks expect **Jupyter started from the repo root** or **`HYDRA_LOGGER_REPO`**
set to it. See the API table in the source docstring of `utility/__init__.py`.

Generated cells: `sys.path` + `import utility` + `repo_root = notebook_bootstrap()`.

**T01** uses **multiple cells**: setup → imports / `CONFIG_PATH` → optional `load_logging_config` →
`PaymentService` → `create_sync_logger` + scenarios → file tails. Use **Run All** for the full path.

Notebook index: `examples/tutorials/notebooks/README.md` — [open](notebooks/README.md).

## Python track

Scripts live in **`examples/tutorials/python/`** (each name must appear in docs for CI):

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

Run from repository root:

```bash
.hydra_env/bin/python examples/tutorials/python/t01_production_quick_start.py
```

Run everything:

```bash
.hydra_env/bin/python examples/run_all_examples.py
```

## Notebook track

Generated `.ipynb` files (subset of the Python track — **no** notebooks for `t05`–`t07`, `t10`,
`t11`, `t15`). Source of truth: `notebooks/temp_nb_factory/generate_notebooks.py` → `TUTORIAL_SPECS`.

| Notebook |
|----------|
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

Details: [`notebooks/README.md`](notebooks/README.md).

```bash
.hydra_env/bin/python -m jupyter lab examples/tutorials/notebooks/t01_production_quick_start.ipynb
```

## Shared script helpers (`shared/`)

`examples/tutorials/shared/` — path bootstrap and artifact checks used by some **Python** tutorials
(not the same as `utility/`, which targets notebooks).

---

## Track matrix (goals & artifacts)

Each track follows: goal → run → expected artifacts → customization.

### T01 Production quick start

- **Goal:** YAML → `create_sync_logger` → inject logger → `layer` / `context` / `extra`.
- **Logs:** `examples/logs/tutorials/t01_app.jsonl`, `t01_audit.log`, `t01_error.jsonl`.
- **Notebook:** multi-cell flow; **Python:** `python/t01_production_quick_start.py`.

### T02 Configuration recipes

- **Goal:** overlays / merged YAML (`extends`).
- **Logs:** `examples/logs/tutorials/t02_*` (per script config).

### T03 Layers customization

- **Goal:** layer taxonomy and routing.
- **Logs:** `examples/logs/tutorials/t03_layers_*.jsonl` (script) / `api.jsonl` + `worker.jsonl` (preset notebooks).

### T04 Extensions and plugins

- **Goal:** extensions (`model_copy`, security redaction, etc.).
- **Logs:** `examples/logs/tutorials/` per preset.

### T05 Framework patterns

- **Goal:** API + worker style flows.
- **Logs:** `examples/logs/tutorials/t05_framework_*.jsonl`.

### T06 Migration and adoption

- **Goal:** incremental adoption from stdlib logging.
- **Logs:** `examples/logs/tutorials/t06_migration.jsonl`.

### T07 Operational playbook

- **Goal:** preflight / rollout checks.
- **Logs:** `examples/logs/tutorials/t07_ops.jsonl`.

### T08 Console configuration cookbook

- **Goal:** console format / colors + file mirror.
- **Logs:** `examples/logs/tutorials/dev_app.jsonl` (preset).

### T09 Levels, columns, date, destinations

- **Goal:** strict file-only preset behavior.
- **Logs:** `examples/logs/tutorials/prod_app.jsonl`.

### T10 Enterprise profile configuration

- **Goal:** enterprise defaults / profile wiring.
- **Logs:** `examples/logs/tutorials/t10_*`.

### T11 Enterprise policy layers

- **Goal:** policy-oriented routing.
- **Logs:** `examples/logs/tutorials/t11_*`.

### T12 Typed network HTTP destination

- **Goal:** `network_http` config shape.
- **Artifacts:** `examples/logs/tutorials/t12_network_http_stub_results.json` (when script generates).

### T13 Typed network WebSocket destination

- **Goal:** `network_ws` config shape.
- **Artifacts:** `examples/logs/tutorials/t13_network_ws_stub_results.json`.

### T14 Local HTTP simulation

- **Goal:** batched / local ingest patterns.
- **Artifacts:** `examples/logs/tutorials/t14_network_ingest_payloads.json`.

### T15 Enterprise network hardening playbook

- **Goal:** hardened network posture across transports.
- **Artifacts:** `examples/logs/tutorials/t15_network_hardening_results.json`.

### T16 Enterprise config templates at scale

- **Goal:** templates / `extends` at scale.
- **Artifacts:** summaries under `examples/logs/tutorials/` + `t16_configs/` as applicable.

### T17 Benchmark comparison workflow

- **Goal:** benchmark artifacts and comparison.
- **Artifacts:** `benchmark/results/...`, tutorial summaries under `examples/logs/tutorials/`.

### T18 Bring-your-own-config benchmark

- **Goal:** user YAML + benchmark persistence.
- **Artifacts:** `benchmark/results/tutorials/t18_byoc/`, tutorial configs under `examples/logs/tutorials/`.

### T19 Nightly drift snapshot

- **Goal:** drift-style signals from benchmarks.
- **Artifacts:** `examples/logs/tutorials/t19_nightly_drift_snapshot.json` (script); benchmark MD/JSON for notebooks.

### T20 Notebook / config onboarding

- **Goal:** strict enterprise preset in notebook + script twin.
- **Notebook:** `examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb`.
- **Outputs:** `examples/logs/tutorials/enterprise_app.jsonl` (preset).

## Legacy mapping (historical)

Older numbered examples (`examples/01_*.py` …) map conceptually to these tutorials; they are not
shipped in-tree. See [`docs/audit/EXAMPLES-AUDIT.md`](../../docs/audit/EXAMPLES-AUDIT.md).

## Checklist (manual)

- Tutorial script exits `0`.
- Expected artifacts under `examples/logs/tutorials/` (and benchmark paths where applicable).
- After changing notebooks: run `generate_notebooks.py` and re-read `notebooks/README.md`.
