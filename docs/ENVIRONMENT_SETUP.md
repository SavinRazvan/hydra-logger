# Development Environment Setup

This repository uses a project-local Conda environment at `.hydra_env`.

## Dependency Source of Truth

- Package/runtime/development dependency versions: `setup.py`
- Environment bootstrap and Python version: `environment.yml`

`requirements.txt` and `requirements-dev.txt` are intentionally removed to avoid duplicate dependency definitions.

## Standard Setup (Conda Prefix)

Create the environment in the project directory:

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
