#!/usr/bin/env python3
"""
Role: Execute selected generated tutorial notebooks from the repo root (CI smoke).
Used By:
 - Local maintainers and GitHub Actions ``notebook-smoke`` job.
Depends On:
 - argparse
 - pathlib
 - nbformat
 - nbconvert (optional extra ``notebook_smoke``)
Notes:
 - Drops code cells tagged ``skip-ci`` (§0 ``%pip``) so runners use the pre-installed editable package.
 - **T17–T19** are intentionally excluded here; full runs may use ``benchmark/results/`` (or minimal stubs). See ``docs/TESTING.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / "setup.py").is_file() and (parent / "hydra_logger").is_dir():
            return parent
    raise RuntimeError("Could not locate repository root above scripts/dev/run_notebook_smoke.py")


def _strip_skip_ci_cells(nb: object) -> None:
    """Remove ``%pip`` cells tagged ``skip-ci`` (editable install already on ``PYTHONPATH``)."""
    cells = getattr(nb, "cells", None)
    if cells is None:
        return
    kept = []
    for cell in cells:
        if getattr(cell, "cell_type", None) != "code":
            kept.append(cell)
            continue
        meta = getattr(cell, "metadata", {}) or {}
        tags = meta.get("tags") or []
        if "skip-ci" in tags:
            continue
        kept.append(cell)
    nb.cells = kept  # type: ignore[attr-defined]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute T01+T02 notebooks (smoke).")
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-notebook execute timeout in seconds (default: 600).",
    )
    args = parser.parse_args(argv)

    try:
        import nbformat
        from nbconvert.preprocessors import ExecutePreprocessor
    except ImportError:
        print(
            "Missing nbconvert/nbformat. Install: pip install -e \".[notebook_smoke]\"",
            file=sys.stderr,
        )
        return 2

    root = _repo_root()
    paths = [
        root / "examples" / "tutorials" / "notebooks" / "t01_production_quick_start.ipynb",
        root / "examples" / "tutorials" / "notebooks" / "t02_configuration_recipes.ipynb",
    ]
    for path in paths:
        if not path.is_file():
            print("Missing notebook:", path, file=sys.stderr)
            return 1
        nb = nbformat.read(path, as_version=4)
        _strip_skip_ci_cells(nb)
        ep = ExecutePreprocessor(timeout=args.timeout, kernel_name="python3")
        print("Executing", path.relative_to(root))
        ep.preprocess(nb, {"metadata": {"path": str(root)}})
        print("OK", path.name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
