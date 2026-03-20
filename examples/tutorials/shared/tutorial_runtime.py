"""Shared runtime helpers for tutorial scripts."""

from pathlib import Path


def tutorial_output_dir() -> Path:
    out = Path("examples/logs/tutorials")
    out.mkdir(parents=True, exist_ok=True)
    return out
