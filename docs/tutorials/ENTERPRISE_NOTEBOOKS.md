# Enterprise notes — tutorial notebooks

Short governance context for [`examples/tutorials/notebooks/`](../../examples/tutorials/notebooks/README.md). The notebooks teach **API usage**; org policy stays with your team.

## Configuration ownership

- Treat YAML/JSON under `examples/config/` as **samples** (notebooks load these paths in **repo** mode). File logs from notebooks land under **`examples/logs/notebooks/`** (see preset `log_dir_name`).
- Promote changes through the same review process as application config (versioning, environment promotion, rollback).
- Prefer **separate** dev/stage/prod presets; do not copy production secrets into tutorial trees.

## Sensitive data

- Do not log passwords, tokens, or raw PII in structured fields. Use **extensions** (e.g. security redaction) and narrow `context` / `extra` payloads — see tutorial **T04** and [`SECURITY.md`](../../SECURITY.md) if published.
- **Network tutorials (T12–T14):** Notebook YAML may call public echo/httpbin endpoints (optional `hydra-logger[network]`); **CLI** tutorials often use **in-process stubs**. Treat any change to “real endpoint” configs as policy-sensitive.

## Operations

- **Benchmark notebooks (T17–T19)** read `benchmark/results/`; use real artifacts when you have them. If files are missing, a notebook cell may write **minimal stubs** under `benchmark/results/` in the clone so cells still run. They are **not** part of the default `run_notebook_smoke.py` set (see [`docs/TESTING.md`](../TESTING.md)).
- For reproducible runs, use the repo **virtualenv** (e.g. `.hydra_env`) as the Jupyter kernel when developing against a clone.

## Further reading

- [`examples/tutorials/notebooks/README.md`](../../examples/tutorials/notebooks/README.md) — prerequisites, §1 (`jupyter_workspace` / `prime_notebook_workspace`), troubleshooting.
- [`examples/config/README.md`](../../examples/config/README.md) — preset catalog.
- [`examples/tutorials/README.md`](../../examples/tutorials/README.md) — CLI track, `run_all_cli_tutorials.py`, artifact matrix.
