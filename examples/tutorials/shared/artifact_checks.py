"""
Role: Lightweight existence checks for tutorial-generated artifacts.
Used By:
 - Tutorial scripts validating outputs under `examples/logs/tutorials/`.
Depends On:
 - pathlib
Notes:
 - Keep checks side-effect free aside from filesystem stat.
"""

from pathlib import Path


def artifact_exists(path: str) -> bool:
    return Path(path).exists()
