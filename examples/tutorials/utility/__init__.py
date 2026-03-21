"""
Role: Shared helpers for tutorial notebooks and scripts (repo root, cwd, paths).
Used By:
 - Generated notebooks under `examples/tutorials/notebooks/`.
 - Optional imports from `examples/tutorials/cli_tutorials/*.py` when not run from repo root.
Depends On:
 - os
 - pathlib
 - sys
 - tempfile
Notes:
 - Repo-mode notebooks add `examples/tutorials` to `sys.path` (clone root = cwd or `HYDRA_LOGGER_REPO`).
 - `notebook_bootstrap()` then `chdir`s to the repo and prints a kernel hint.
 - `prepare_notebook_workspace()` is the **notebook §1 entry** after `sys.path` includes
   ``examples/tutorials``: honors ``HYDRA_LOGGER_REPO`` (``chdir`` when valid), then delegates
   to ``notebook_bootstrap()``. Returns ``(repo_root, True)``.
 - Generated notebooks **require** a checkout that contains ``examples/config/`` (clone + ``HYDRA_LOGGER_REPO``
   or start Jupyter from the repo root). Presets are **not** copied into a temp tree; tutorials read the
   real files under ``examples/config/``.
 - ``resolved_cwd()`` avoids ``Path.cwd()`` crashes when the kernel cwd was a removed temp directory
   (restart + Run All still recommended).
 - ``do_notebook_setup()`` / ``do_nb_setup()`` are the **library-side** notebook entry (after
   ``examples/tutorials`` is on ``sys.path``). Generated notebooks ``importlib``-load ``jupyter_workspace.py``
   and call ``prime_notebook_workspace()`` so users do not paste long bootstrap code.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

__all__ = [
    "resolved_cwd",
    "find_repo_root",
    "setup_notebook",
    "notebook_bootstrap",
    "prepare_notebook_workspace",
    "ensure_tutorials_importable",
    "do_notebook_setup",
    "do_nb_setup",
    "tutorial_config_path",
    "tutorial_logs_dir",
]


def resolved_cwd() -> Path:
    """
    Return ``Path.cwd().resolve()``, recovering if the process cwd no longer exists.

    Jupyter often ``chdir``s into a standalone temp workspace; if that directory is removed
    (cleanup, partial re-run), ``Path.cwd()`` raises ``FileNotFoundError`` — reset to system temp.
    """
    try:
        return Path.cwd().resolve()
    except FileNotFoundError:
        fallback = Path(tempfile.gettempdir()).resolve()
        os.chdir(fallback)
        return fallback


def find_repo_root(start: Path | None = None) -> Path:
    """Return repository root (directory containing `hydra_logger/` and `examples/config/`)."""
    cur = (start or resolved_cwd()).resolve()
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


def _is_hydra_logger_repo_root(path: Path) -> bool:
    """True if ``path`` looks like the hydra-logger clone root."""
    return (
        path.is_dir()
        and (path / "hydra_logger").is_dir()
        and (path / "examples" / "config").is_dir()
    )


def do_notebook_setup(
    *,
    chdir: bool = True,
    warn_if_not_hydra_env: bool = True,
    repo_candidate: Path | None = None,
) -> Path:
    """
    Prepare the notebook workspace and return ``repo_root``.

    Call when ``examples/tutorials`` is already importable **or** pass ``repo_candidate`` (clone root with
    ``hydra_logger/`` and ``examples/config/``). Used by ``shared.path_bootstrap.run_notebook_workspace_setup``.
    """
    ensure_tutorials_importable(repo_candidate)
    root, _ = prepare_notebook_workspace(
        chdir=chdir,
        warn_if_not_hydra_env=warn_if_not_hydra_env,
        repo_candidate=repo_candidate,
    )
    return root


def do_nb_setup(
    *,
    chdir: bool = True,
    warn_if_not_hydra_env: bool = True,
    repo_candidate: Path | None = None,
) -> Path:
    """Alias for :func:`do_notebook_setup` (shorter name for docs / REPL)."""
    return do_notebook_setup(
        chdir=chdir,
        warn_if_not_hydra_env=warn_if_not_hydra_env,
        repo_candidate=repo_candidate,
    )


def prepare_notebook_workspace(
    *,
    chdir: bool = True,
    warn_if_not_hydra_env: bool = True,
    repo_candidate: Path | None = None,
) -> tuple[Path, bool]:
    """
    Repo-mode notebook setup: call only after ``examples/tutorials`` is on ``sys.path``.

    If ``HYDRA_LOGGER_REPO`` points at a valid repo root, ``chdir`` there first so
    ``find_repo_root()`` succeeds even when the kernel cwd is elsewhere (e.g. ``/tmp``).

    If ``repo_candidate`` is set (tests) and the env var is unset/empty, ``chdir`` to
    ``repo_candidate`` when it is a valid repo root.

    Returns ``(repo_root, True)`` (second value reserved for callers/tests; notebooks ignore it).
    """
    raw = os.environ.get("HYDRA_LOGGER_REPO", "").strip()
    if raw:
        cand = Path(raw).expanduser().resolve()
        if _is_hydra_logger_repo_root(cand) and chdir:
            os.chdir(cand)
    elif repo_candidate is not None:
        rc = repo_candidate.expanduser().resolve()
        if _is_hydra_logger_repo_root(rc) and chdir:
            os.chdir(rc)

    root = notebook_bootstrap(chdir=chdir, warn_if_not_hydra_env=warn_if_not_hydra_env)
    return (root, True)


def tutorial_config_path(filename: str, *, repo_root: Path | None = None) -> Path:
    """`examples/config/<filename>` under the repo."""
    root = repo_root or find_repo_root()
    return root / "examples" / "config" / filename


def tutorial_logs_dir(*, repo_root: Path | None = None) -> Path:
    """Canonical **notebook** tutorial log directory: ``examples/logs/notebooks``."""
    root = repo_root or find_repo_root()
    return root / "examples" / "logs" / "notebooks"
