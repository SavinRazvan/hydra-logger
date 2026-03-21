# Hydra-Logger examples

Canonical onboarding for the **clone / dev** workflow. Published-package users follow the same APIs;
paths below assume the **repository root** as the working directory.

Start here if you want the **big picture**: how we configure logging (file vs code), then **where** to
open notebooks, scripts, and shared helpers.

## Python environment

- **Clone / CI parity:** use **`.hydra_env`** (see `docs/ENVIRONMENT_SETUP.md`) — commands below use
  `.hydra_env/bin/python` so `import hydra_logger` matches how maintainers run gates.
- **Any venv is fine** if `hydra-logger` is installed (e.g. `pip install -e .` or `pip install hydra-logger`).
  Tutorial scripts use `#!/usr/bin/env python3`; they do not hard-require `.hydra_env`.
- **Notebooks:** **`t01_production_quick_start.ipynb`** can install the package in-cell (**§0**). All
  notebooks load YAML/JSON from **`examples/config/`** in a **clone** (set **`HYDRA_LOGGER_REPO`** when
  needed). **T17–T19** read `benchmark/results/` (minimal stubs may be created if files are absent).

## Configuration: YAML files vs Python

We support **both**; onboarding stays simple if you treat one as the **default** and the other as an
**alternative**.

| Style | When we reach for it | Typical API | In this repo |
|-------|----------------------|-------------|--------------|
| **YAML / JSON file** | Production-style contracts, Git review, ops handoff | `create_sync_logger(config_path=...)` (or async variant) | Presets under `examples/config/`; **notebooks** use these heavily. **CLI `t01`** loads a YAML file. |
| **Python `LoggingConfig`** | Quick scripts, tests, or building config at runtime | `create_logger(config, logger_type="sync")` | Most **`cli_tutorials/t*.py`** build config in code so each file is self-contained. |

**Default path we recommend:** learn **file-based** config first (**T01** notebook or CLI
`t01_production_quick_start.py`), then skim any other `t*` CLI script to see the **Python object** style
for the same ideas (layers, destinations, etc.).

**Tiny contrast** (not full tutorials — see T01 / `cli_tutorials` for real usage):

```python
# A) Load from a file (paths relative to process cwd — run from repo root)
from hydra_logger import create_sync_logger

with create_sync_logger(
    config_path="examples/config/tutorial_t01_enterprise_layers.yaml",
    strict_unknown_fields=True,
    name="demo",
) as logger:
    logger.info("ok", layer="app")
```

```python
# B) Build config in Python
from hydra_logger import LogDestination, LoggingConfig, LogLayer, create_logger

cfg = LoggingConfig(
    default_level="INFO",
    layers={
        "app": LogLayer(
            level="INFO",
            destinations=[LogDestination(type="console", format="plain-text")],
        ),
    },
)
with create_logger(cfg, logger_type="sync") as logger:
    logger.info("ok", layer="app")
```

## Explore the tutorials

| Area | Path | What it is |
|------|------|------------|
| **Notebook track** | [`examples/tutorials/notebooks/`](tutorials/notebooks/) | Generated `.ipynb` (`t01`–`t20` where present): §0 pip → §1 clone resolution → imports → YAML/`CONFIG_PATH` → scenario → results. **Requires** `examples/config/` on disk (clone + optional `HYDRA_LOGGER_REPO`). Index: [`notebooks/README.md`](tutorials/notebooks/README.md). |
| **CLI track** | [`examples/tutorials/cli_tutorials/`](tutorials/cli_tutorials/) | Runnable `t01`–`t20` **`.py`** — run from **repo root** so `examples/config` / `examples/logs` paths resolve. **`t01`** uses YAML; most others use in-code `LoggingConfig` (see table above). Listed in [`tutorials/README.md`](tutorials/README.md). |
| **Shared (scripts / reuse)** | [`examples/tutorials/shared/`](tutorials/shared/) | [`path_bootstrap.py`](tutorials/shared/path_bootstrap.py) (`project_root()`, optional `ensure_tutorials_syspath()`), [`cli_tutorial_footer.py`](tutorials/shared/cli_tutorial_footer.py) (end-of-run **Console / Files / Takeaway** for `cli_tutorials/*.py`; each script prepends `examples/tutorials` on `sys.path` **before** importing `shared`). [`tutorial_runtime.py`](tutorials/shared/tutorial_runtime.py), [`artifact_checks.py`](tutorials/shared/artifact_checks.py). |
| **Notebook §1 entry** | [`examples/tutorials/jupyter_workspace.py`](tutorials/jupyter_workspace.py) | `prime_notebook_workspace()` — loaded by generated notebooks via `importlib`, then delegates to `shared.path_bootstrap` → `utility`. |
| **Notebook workspace API** | [`examples/tutorials/utility/`](tutorials/utility/) | `do_notebook_setup()`, `prepare_notebook_workspace()`, `notebook_bootstrap()`, `tutorial_config_path()`, `resolved_cwd()`, etc. |
| **Presets** | [`examples/config/`](config/) | YAML/JSON referenced by notebooks and **`t01`** CLI. See [`config/README.md`](config/README.md). |

**Suggested order:** read this file → run **CLI `t01`** or open **notebook `t01`** → pick **notebook** or **CLI** list above for deeper IDs → adjust presets under `examples/config/` and re-run.

**Artifact names:** **CLI** scripts use `tNN_*` stems and write under **`examples/logs/cli-tutorials/`**. **Notebooks** loading YAML/JSON from `examples/config/` write under **`examples/logs/notebooks/`** (shorter preset stems like `dev_app.jsonl`, `prod_app.jsonl`, `enterprise_app.jsonl`).

## Layout (quick reference)

| Path | Purpose |
|------|---------|
| `examples/config/` | YAML/JSON presets (`examples/config/README.md`) |
| `examples/tutorials/cli_tutorials/` | Runnable tutorials `t01`–`t20` |
| `examples/tutorials/notebooks/` | Jupyter tutorials (generated + multi-cell flow) |
| `examples/tutorials/jupyter_workspace.py` | Notebook §1 `prime_notebook_workspace()` (importlib from generated cells) |
| `examples/tutorials/utility/` | Notebook workspace helpers (`do_notebook_setup`, `prepare_notebook_workspace`, paths) |
| `examples/tutorials/shared/` | CLI import path + run footer (`path_bootstrap`, `cli_tutorial_footer`), `run_all_cli_tutorials.py`, `tutorial_runtime`, `artifact_checks` |
| `examples/run_all_examples.py` | Runs all `tutorials/cli_tutorials/*.py` in sequence |
| `examples/logs/` | **Committed samples** under `cli-tutorials/` and `notebooks/` so clones show tutorial-shaped output; other paths under `examples/logs/` stay ignored. |

## Quick start

```bash
.hydra_env/bin/python examples/tutorials/cli_tutorials/t01_production_quick_start.py
.hydra_env/bin/python examples/run_all_examples.py
```

**Notebooks:** start Jupyter from the repo root **or** set `HYDRA_LOGGER_REPO` so `examples/config/` is
found (see [Notebook track](tutorials/notebooks/README.md)).

```bash
.hydra_env/bin/python -m jupyter lab examples/tutorials/notebooks/t01_production_quick_start.ipynb
```

## Indexes

- Tutorials: `examples/tutorials/README.md` — [open](tutorials/README.md)
- Config presets: `examples/config/README.md` — [Presets](config/README.md)
- Audit / migration: `docs/audit/EXAMPLES-AUDIT.md` — [EXAMPLES-AUDIT](../docs/audit/EXAMPLES-AUDIT.md)

## Tests

Tutorial scripts and assets are exercised in CI via `tests/examples/` (run locally with
`python -m pytest tests/examples -q`). This complements `run_all_examples.py` for smoke runs.

## Legacy numbered examples

Older `01_*.py` … `17_*.py` demos are **not** in this tree anymore; canonical material is
`t01`–`t20` under `examples/tutorials/cli_tutorials/` and matching notebooks. Historical copies may
live in a private archive; see [docs/audit/EXAMPLES-AUDIT.md](../docs/audit/EXAMPLES-AUDIT.md).
