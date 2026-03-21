"""
Role: Jupyter §1 entry — prime ``sys.path`` and return ``repo_root`` (importlib-friendly).
Used By:
 - Generated notebooks: ``importlib`` loads this file from disk, then ``prime_notebook_workspace()``.
Depends On:
 - pathlib
 - sys
Notes:
 - Lives at ``examples/tutorials/jupyter_workspace.py`` so :func:`prime_notebook_workspace` can use
   ``__file__`` to locate ``examples/tutorials`` without relying on Jupyter's cwd.
 - Delegates to ``shared.path_bootstrap.run_notebook_workspace_setup`` for ``chdir`` / ``HYDRA_LOGGER_REPO``
   handling and ``utility.do_notebook_setup``.
"""

from __future__ import annotations

import sys
from pathlib import Path


def prime_notebook_workspace(
    *,
    chdir: bool = True,
    warn_if_not_hydra_env: bool = True,
) -> Path:
    """
    Put ``examples/tutorials`` on ``sys.path``, then run the standard notebook workspace setup.

    Intended use: after this module is loaded via ``importlib`` (notebook §1 collapsed cell).
    """
    tutorials = Path(__file__).resolve().parent
    s = str(tutorials)
    if s not in sys.path:
        sys.path.insert(0, s)
    from shared.path_bootstrap import run_notebook_workspace_setup

    return run_notebook_workspace_setup(
        chdir=chdir,
        warn_if_not_hydra_env=warn_if_not_hydra_env,
    )
