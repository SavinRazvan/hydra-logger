"""Small helper checks for tutorial artifacts."""

from pathlib import Path


def artifact_exists(path: str) -> bool:
    return Path(path).exists()
