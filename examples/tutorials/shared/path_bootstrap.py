"""
Role: Resolve repository root for tutorials run from varied working directories.
Used By:
 - Tutorial scripts and notebooks that need stable paths to `examples/config/`.
Depends On:
 - pathlib
Notes:
 - Assumes this file lives at `examples/tutorials/shared/path_bootstrap.py`.
"""

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]
