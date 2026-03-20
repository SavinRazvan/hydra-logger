# Hydra-Logger examples

Canonical onboarding for the **clone / dev** workflow. Published-package users follow the same APIs;
paths below assume the **repository root** as the working directory.

## Layout

| Path | Purpose |
|------|---------|
| `examples/config/` | YAML/JSON presets (`examples/config/README.md`) |
| `examples/tutorials/python/` | Runnable tutorials `t01`–`t20` |
| `examples/tutorials/notebooks/` | Jupyter tutorials (generated + multi-cell flow) |
| `examples/tutorials/utility/` | Notebook bootstrap (`notebook_bootstrap`, paths) |
| `examples/tutorials/shared/` | Helpers for scripts (`path_bootstrap`, artifacts) |
| `examples/tutorials/notebooks/temp_nb_factory/` | Regenerate `.ipynb` from `generate_notebooks.py` + `scenarios.py` |
| `examples/run_all_examples.py` | Runs all `tutorials/python/*.py` in sequence |
| `examples/logs/` | **Gitignored** — tutorial runtime output (e.g. `tutorials/t01_*.jsonl`) |

## Quick start

```bash
.hydra_env/bin/python examples/tutorials/python/t01_production_quick_start.py
.hydra_env/bin/python examples/run_all_examples.py
```

**Notebooks:** start Jupyter from the repo root (or set `HYDRA_LOGGER_REPO`). See
`examples/tutorials/notebooks/README.md` — [Notebook track](tutorials/notebooks/README.md).

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
`t01`–`t20` under `examples/tutorials/python/` and matching notebooks. Historical copies may
live in a private archive; see [docs/audit/EXAMPLES-AUDIT.md](../docs/audit/EXAMPLES-AUDIT.md).
