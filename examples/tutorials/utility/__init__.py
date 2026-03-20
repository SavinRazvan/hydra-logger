"""
Role: Shared helpers for tutorial notebooks and scripts (repo root, cwd, paths).
Used By:
 - Generated notebooks under `examples/tutorials/notebooks/`.
 - Optional imports from `examples/tutorials/python/*.py` when not run from repo root.
Depends On:
 - os
 - pathlib
 - sys
Notes:
 - Notebooks add `examples/tutorials` to `sys.path` (repo root = process cwd, or `HYDRA_LOGGER_REPO`).
 - `notebook_bootstrap()` then `chdir`s to the repo and prints a kernel hint.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = [
    "find_repo_root",
    "setup_notebook",
    "notebook_bootstrap",
    "ensure_tutorials_importable",
    "tutorial_config_path",
    "tutorial_logs_dir",
]


def find_repo_root(start: Path | None = None) -> Path:
    """Return repository root (directory containing `hydra_logger/` and `examples/config/`)."""
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "hydra_logger").is_dir() and (candidate / "examples" / "config").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find hydra-logger repo root (expected hydra_logger/ and examples/config/)."
    )


def ensure_tutorials_importable(repo_root: Path | None = None) -> Path:
    """Put `examples/tutorials` on sys.path so `import utility` works."""
    root = repo_root or find_repo_root()
    tutorials = root / "examples" / "tutorials"
    if not tutorials.is_dir():
        raise FileNotFoundError(f"Missing tutorials directory: {tutorials}")
    s = str(tutorials)
    if s not in sys.path:
        sys.path.insert(0, s)
    return root


def setup_notebook(
    *,
    chdir: bool = True,
    warn_if_not_hydra_env: bool = True,
) -> Path:
    """
    Standard notebook entry: locate repo, optional chdir, optional kernel warning.

    Call after ``ensure_tutorials_importable`` (or use ``notebook_bootstrap`` in one shot).
    """
    root = find_repo_root()
    if chdir:
        os.chdir(root)
    if warn_if_not_hydra_env and ".hydra_env" not in sys.executable:
        print(f"Warning: expected .hydra_env kernel, current interpreter is: {sys.executable}")
    print(f"Repo root (cwd): {root}")
    return root


def notebook_bootstrap(
    *,
    chdir: bool = True,
    warn_if_not_hydra_env: bool = True,
) -> Path:
    """One-shot: add tutorials to path, chdir to repo root, return root."""
    root = ensure_tutorials_importable()
    return setup_notebook(chdir=chdir, warn_if_not_hydra_env=warn_if_not_hydra_env)


def tutorial_config_path(filename: str, *, repo_root: Path | None = None) -> Path:
    """`examples/config/<filename>` under the repo."""
    root = repo_root or find_repo_root()
    return root / "examples" / "config" / filename


def tutorial_logs_dir(*, repo_root: Path | None = None) -> Path:
    """Canonical tutorial log output directory."""
    root = repo_root or find_repo_root()
    return root / "examples" / "logs" / "tutorials"
