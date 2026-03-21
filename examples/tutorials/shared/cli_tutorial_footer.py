"""
Role: Consistent end-of-run summary for `cli_tutorials/*.py` (artifacts + takeaway).
Used By:
 - Runnable scripts under `examples/tutorials/cli_tutorials/`.
Depends On:
 - pathlib (optional normalization)
Notes:
 - Call after logging so users see where output went when sinks are file-only.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


def print_cli_tutorial_footer(
    *,
    code: str,
    title: str,
    console: str,
    artifacts: Sequence[str | Path] = (),
    extra_lines: Sequence[str] = (),
    takeaway: str,
    notebook_rel: str | None = None,
) -> None:
    """
    Print a short, copy-friendly summary: what appeared on console vs disk, and what to inspect.

    Args:
        code: Tutorial id, e.g. ``T05``.
        title: Human title for the script.
        console: One line: what the user should have seen on stdout (or why Hydra was quiet).
        artifacts: Paths (repo-relative strings preferred) written or updated.
        extra_lines: Optional bullets (e.g. dynamic counts, stub URLs) printed under **Details**.
        takeaway: Single learning outcome / next step.
        notebook_rel: If set, relative path from repo root to the paired notebook; else CLI-only hint.
    """
    sep = "=" * 62
    print(sep)
    print(f"{code} — {title}")
    print(sep)
    print(f"Console: {console}")
    if artifacts:
        print("Files:")
        for p in artifacts:
            print(f"  {p}")
    if extra_lines:
        print("Details:")
        for line in extra_lines:
            print(f"  {line}")
    print(f"Takeaway: {takeaway}")
    if notebook_rel:
        print(f"Notebook: {notebook_rel}")
    else:
        print("Notebook: (no generated notebook for this ID — see examples/tutorials/README.md)")
    print(sep)
