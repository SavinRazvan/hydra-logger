"""
Role: Resolve repository root for tutorials run from varied working directories.
Used By:
 - Tutorial scripts and notebooks that need stable paths to `examples/config/`.
 - ``jupyter_workspace.prime_notebook_workspace()`` (notebook §1 after ``sys.path`` includes ``examples/tutorials``).
Depends On:
 - pathlib
 - sys (optional, for `ensure_tutorials_syspath`)
Notes:
 - Assumes this file lives at `examples/tutorials/shared/path_bootstrap.py`.
 - ``run_notebook_workspace_setup`` uses this file's location (not the process cwd) to find the clone root.
"""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_notebook_workspace_setup(
    *,
    chdir: bool = True,
    warn_if_not_hydra_env: bool = True,
) -> Path:
    """
    Single entry for **notebook §1** after this module has been loaded (e.g. via ``importlib``).

    Puts ``examples/tutorials`` on ``sys.path``, then delegates to ``utility.do_notebook_setup`` with an
    explicit ``repo_candidate`` derived from this file's path so setup works even when Jupyter's cwd is
    outside the clone (as long as the loaded ``path_bootstrap.py`` belongs to the intended checkout).
    """
    ensure_tutorials_syspath()
    from utility import do_notebook_setup

    return do_notebook_setup(
        chdir=chdir,
        warn_if_not_hydra_env=warn_if_not_hydra_env,
        repo_candidate=project_root(),
    )


def ensure_tutorials_syspath() -> None:
    """
    Insert ``examples/tutorials`` on ``sys.path`` so ``import shared.*`` works from
    ``cli_tutorials/*.py`` when run as ``python examples/tutorials/cli_tutorials/tXX_*.py``.
    """
    tutorials_dir = Path(__file__).resolve().parents[1]
    s = str(tutorials_dir)
    if s not in sys.path:
        sys.path.insert(0, s)
