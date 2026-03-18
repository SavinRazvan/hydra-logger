# Development Environment Setup

This repository uses a project-local Python environment at `.hydra_env`.
Use one environment model at a time (venv or Conda prefix) and avoid mixing layouts.

## Dependency Source of Truth

- Package/runtime/development dependency versions: `setup.py`
- Conda bootstrap model: `environment.yml`
- venv bootstrap model: system Python + `pip install -e .[dev]`

`requirements.txt` and `requirements-dev.txt` are intentionally removed to avoid duplicate dependency definitions.

## Core vs Optional Dependencies

- `pip install hydra-logger` installs the core runtime dependencies only.
- Optional integrations are enabled through extras in `setup.py`, such as:
  - `network` (websocket/network integrations)
  - `perf` (performance introspection)
  - `database`, `cloud`, `queues`, `system`
  - `full` / `all` (aggregate extras)

Examples:

```bash
python -m pip install "hydra-logger[network]"
python -m pip install "hydra-logger[perf]"
python -m pip install "hydra-logger[database,cloud,queues]"
```

## Standard Setup (venv)

Create and activate a local venv:

```bash
python3 -m venv .hydra_env
source .hydra_env/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
python -m pip install pyright
```

## Alternative Setup (Conda Prefix)

Create the Conda environment in the project directory:

```bash
conda env create -p ./.hydra_env -f environment.yml
```

If it already exists, update it:

```bash
conda env update -p ./.hydra_env -f environment.yml --prune
```

Activate it:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$(pwd)/.hydra_env"
```

Editable package install is already defined in `environment.yml` (`-e .[dev]`).

## Environment Health Check

Run a deterministic preflight before lint/type/test/PR automation:

```bash
.hydra_env/bin/python scripts/dev/check_env_health.py --strict
```

Machine-readable output:

```bash
.hydra_env/bin/python scripts/dev/check_env_health.py --strict --json
```

If the check reports a degraded/broken state and you only want remediation hints:

```bash
.hydra_env/bin/python scripts/dev/check_env_health.py --fix-hints-only
```

## Conda-Lock Workflow (Recommended for Reproducibility)

Install `conda-lock` (once, typically in base):

```bash
conda install -n base -c conda-forge conda-lock
```

Generate lockfile(s):

```bash
conda-lock -f environment.yml -p linux-64 -p osx-64 -p osx-arm64 -p win-64
```

Install from lockfile:

```bash
conda-lock install --prefix ./.hydra_env conda-lock.yml
```

Regenerate lockfile whenever dependencies change in `setup.py` or `environment.yml`.

## Troubleshooting

If Conda plugins/solver behave badly in your environment:

```bash
CONDA_NO_PLUGINS=true CONDA_SOLVER=classic conda --no-plugins env create -p ./.hydra_env -f environment.yml
```

Deterministic repair sequence when health checks fail:

1. Remove the corrupted `.hydra_env`.
2. Recreate `.hydra_env` using your chosen model (venv or Conda prefix).
3. Reinstall project dependencies (`-e .[dev]`) and `pyright` if using venv.
4. Re-run `.hydra_env/bin/python scripts/dev/check_env_health.py --strict` until healthy.
