# Enterprise tutorials

Deterministic onboarding for `hydra-logger`: **Python scripts** (`t01`–`t20`), **Jupyter notebooks**
(same IDs where present), and shared **config** under `examples/config/`.

**Orientation:** YAML-file vs in-code config, and where notebooks / CLI / `shared` / `utility` live —
[`examples/README.md`](../README.md).

## Validation

| Check | Command |
|-------|---------|
| Pytest (assets, runners, branches, `utility`) | `.hydra_env/bin/python -m pytest tests/examples -q` |
| Smoke all Python tutorials | `.hydra_env/bin/python examples/run_all_examples.py` |

Tutorial **`.ipynb`** files are **committed** under `examples/tutorials/notebooks/`. **CI:** GitHub Actions
runs a **smoke execute** on **T01 + T02** only (`scripts/dev/run_notebook_smoke.py` after
`pip install -e ".[notebook_smoke]"`). The full notebook set is **not** executed in default `pytest`.
Edit notebooks in Jupyter directly; keep outputs cleared for version control (see `notebooks/README.md`).

## Notebook bootstrap (`jupyter_workspace.py` + `utility/`)

**Generated §1 (collapsed):** `importlib` finds `examples/tutorials/jupyter_workspace.py` (from **`HYDRA_LOGGER_REPO`**
or cwd), then **`prime_notebook_workspace()`** → `shared.path_bootstrap` → **`utility.do_notebook_setup()`** /
`prepare_notebook_workspace()`. See `jupyter_workspace.py` and `utility/__init__.py`.

**Configs** always load from **`examples/config/`** in the clone (no temp mirror). **T17–T19** use
`benchmark/results/`; if files are missing, a cell may write minimal stubs there.

**T01** uses **multiple cells**: optional **§0** `%pip install` → §1 setup → imports + `CONFIG_PATH` /
`LOG_DIR` → optional `load_logging_config` → `PaymentService` → `create_sync_logger` → file tails. Scenario
track notebooks follow **§0–§6** with small markdown (`####` / `**§N**` / `<small>`). Use **Run All**
for the full path.

Notebook index: `examples/tutorials/notebooks/README.md` — [open](notebooks/README.md).

**CI:** GitHub Actions runs `scripts/dev/run_notebook_smoke.py` on **T01** + **T02** (see `docs/TESTING.md`).
**Governance:** [`docs/tutorials/ENTERPRISE_NOTEBOOKS.md`](../docs/tutorials/ENTERPRISE_NOTEBOOKS.md).

## CLI tutorial track (runnable scripts)

Scripts live in **`examples/tutorials/cli_tutorials/`** (each name must appear in docs for CI):

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

**Run summary:** Every script prints a short footer from [`shared/cli_tutorial_footer.py`](shared/cli_tutorial_footer.py): **Console** (why Hydra might be quiet), **Files** under `examples/logs/cli-tutorials/`, optional **Details**, a **Takeaway**, and **Notebook** (path when a generated `.ipynb` exists, else a pointer to this README).

**Run all CLI tutorials (streamed output):** from repo root,

```bash
.hydra_env/bin/python examples/tutorials/shared/run_all_cli_tutorials.py
```

(`--dry-run` lists paths; `--fail-fast` stops on first failure.)

Run from repository root:

```bash
.hydra_env/bin/python examples/tutorials/cli_tutorials/t01_production_quick_start.py
```

Run everything:

```bash
.hydra_env/bin/python examples/run_all_examples.py
```

## Notebook track

Committed `.ipynb` files (subset of the Python track — **no** notebooks for `t05`–`t07`, `t10`,
`t11`, `t15`). List and behavior: `notebooks/README.md`.

**Repository required:** run **§0** (`%pip install`) where you need the package; **§1** needs a checkout
with `examples/config/` (set **`HYDRA_LOGGER_REPO`** if Jupyter’s cwd is not the clone root). File logs go
to **`examples/logs/notebooks/`**. **T17–T19** use `benchmark/results/` (optional stub files if missing).

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

`examples/tutorials/shared/` — path bootstrap and artifact checks used by some **CLI** tutorials
(not the same as `utility/`, which targets notebooks).

---

## Track matrix (goals & artifacts)

Each track follows: goal → run → expected artifacts → customization.

### T01 Production quick start

- **Goal:** YAML → `create_sync_logger` → inject logger → `layer` / `context` / `extra`.
- **Logs (CLI):** `examples/logs/cli-tutorials/t01_*` (script overrides `log_dir_name` after loading YAML).
- **Logs (notebook):** `examples/logs/notebooks/t01_*` (preset `tutorial_t01_enterprise_layers.yaml`).
- **Notebook:** multi-cell flow; **CLI script:** `cli_tutorials/t01_production_quick_start.py`.

### T02 Configuration recipes

- **Goal:** overlays / merged YAML (`extends`).
- **Logs:** `examples/logs/cli-tutorials/t02_*` (per script config).

### T03 Layers customization

- **Goal:** layer taxonomy and routing.
- **Logs (CLI):** `t03_layers_api.jsonl`, `t03_layers_database.jsonl`, `t03_layers_auth.jsonl` under `examples/logs/cli-tutorials/`.
- **Notebook:** YAML `CONFIG_PATH` + optional **§3b** JSON peek (`dev_console_file.json`); **§Results** tails under `examples/logs/notebooks/` (repo).

### T04 Extensions and plugins

- **Goal:** extensions (`model_copy`, security redaction, etc.).
- **Logs:** `examples/logs/cli-tutorials/` per preset.

### T05 Framework patterns

- **Goal:** API + worker style flows.
- **Logs:** `examples/logs/cli-tutorials/t05_framework_*.jsonl`.

### T06 Migration and adoption

- **Goal:** incremental adoption from stdlib logging.
- **Logs:** `examples/logs/cli-tutorials/t06_migration.jsonl`.

### T07 Operational playbook

- **Goal:** preflight / rollout checks.
- **Logs:** `examples/logs/cli-tutorials/t07_ops.jsonl`.

### T08 Console configuration cookbook

- **Goal:** console format / colors + file mirror.
- **Logs (CLI):** `t08_colored_plaintext.jsonl`, `t08_no_color.log`, `t08_layer_api.jsonl`, `t08_layer_audit.log`.
- **Logs (notebook):** YAML preset `dev_console_file` → mainly `dev_app.jsonl` under `examples/logs/notebooks/` (see §6 tail in the notebook).

### T09 Levels, columns, date, destinations

- **Goal:** destination-level levels, columns/date formatter sample, multi-sink routing.
- **Logs (CLI):** `t09_api.jsonl`, `t09_api_audit.log`, `t09_security.jsonl`.
- **Logs (notebook):** strict preset → `prod_app.jsonl` (plus any extra sinks defined in the embedded YAML).

### T10 Enterprise profile configuration

- **Goal:** enterprise defaults / profile wiring (with tutorial path shim + console sink).
- **Logs:** `t10_default_enterprise.jsonl`, `t10_warning_warning.jsonl`, `t10_error_error.jsonl` (dynamic names from resolved layers).

### T11 Enterprise policy layers

- **Goal:** policy-oriented routing.
- **Logs:** `examples/logs/cli-tutorials/t11_*`.

### T12 Typed network HTTP destination

- **Goal:** `network_http` config shape (stub transport + visible Hydra sinks).
- **Artifacts:** `t12_network_http_layer.jsonl` (Hydra file sink) + `t12_network_http_stub_results.json` (captured stub payloads).

### T13 Typed network WebSocket destination

- **Goal:** `network_ws` config shape (stub transport + visible Hydra sinks).
- **Artifacts:** `t13_network_ws_layer.jsonl` + `t13_network_ws_stub_results.json`.

### T14 Local HTTP simulation

- **Goal:** batched / local ingest patterns (in-process server + Hydra sinks).
- **Artifacts:** `t14_network_http_layer.jsonl` + `t14_network_ingest_payloads.json`.

### T15 Enterprise network hardening playbook

- **Goal:** hardened network posture across transports.
- **Artifacts:** `t15_network_hardening_results.jsonl`.

### T16 Enterprise config templates at scale

- **Goal:** templates / `extends` at scale.
- **Artifacts (CLI):** `t16_enterprise_config_templates_at_scale.jsonl`.
- **Artifacts (notebook):** enterprise starter preset → `enterprise_app.jsonl` (and console output).

### T17 Benchmark comparison workflow

- **Goal:** benchmark artifacts and comparison.
- **Artifacts:** `benchmark/results/...`, tutorial summaries under `examples/logs/cli-tutorials/`.

### T18 Bring-your-own-config benchmark

- **Goal:** user YAML + benchmark persistence.
- **Artifacts:** `benchmark/results/tutorials/t18_byoc/`, tutorial configs under `examples/logs/cli-tutorials/`.

### T19 Nightly drift snapshot

- **Goal:** drift-style signals from benchmarks.
- **Artifacts:** `t19_enterprise_nightly_drift_snapshot.jsonl` (CLI); notebooks may also reference `benchmark/results/` when present.

### T20 Notebook / config onboarding

- **Goal:** strict enterprise preset in notebook + script twin.
- **Notebook:** `examples/tutorials/notebooks/t20_notebook_hydra_config_onboarding.ipynb`.
- **Outputs (CLI):** `t20_notebook_hydra_config_onboarding.jsonl`.
- **Outputs (notebook):** same preset stem as T16 enterprise flow → `enterprise_app.jsonl` in `examples/logs/notebooks/`.

## Legacy mapping (historical)

Older numbered examples (`examples/01_*.py` …) map conceptually to these tutorials; they are not
shipped in-tree. See [`docs/audit/EXAMPLES-AUDIT.md`](../../docs/audit/EXAMPLES-AUDIT.md).

## Checklist (manual)

- Tutorial script exits `0`.
- **CLI:** `examples/logs/cli-tutorials/`. **Notebooks (repo):** `examples/logs/notebooks/`. Benchmark paths where applicable.
- After changing notebooks: clear outputs, re-read `notebooks/README.md`, run `pytest tests/examples -q`.
