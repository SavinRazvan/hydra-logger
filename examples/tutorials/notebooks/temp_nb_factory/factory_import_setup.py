"""
Role: Put ``temp_nb_factory`` on ``sys.path`` so sibling modules resolve reliably.
Used By:
 - ``generate_notebooks.py`` and ``generate_*.py`` (import this before ``nb_factory_core``).
Depends On:
 - pathlib
 - sys
Notes:
 - Covers debuggers, ``runpy``, and runners that do not set ``sys.path[0]`` to this directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

_FACTORY_DIR = Path(__file__).resolve().parent
_FACTORY_DIR_STR = str(_FACTORY_DIR)
if _FACTORY_DIR_STR not in sys.path:
    sys.path.insert(0, _FACTORY_DIR_STR)
