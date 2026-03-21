"""
Role: Create canonical tutorial log output directories under the repo.
Used By:
 - Tutorial scripts writing to `examples/logs/cli-tutorials/`.
Depends On:
 - pathlib
Notes:
 - Matches `.gitignore` entry for `examples/logs/`; run from repo root when possible.
"""

from pathlib import Path


def tutorial_output_dir() -> Path:
    out = Path("examples/logs/cli-tutorials")
    out.mkdir(parents=True, exist_ok=True)
    return out
