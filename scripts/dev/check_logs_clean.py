"""
Role: Fails when repository runtime logs contain test artifacts.
Used By:
 - Local and CI validation workflows.
Depends On:
 - pathlib
 - sys
Notes:
 - Enforces destination-controlled logging by keeping repo `logs/` clean.
"""

from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    """Return non-zero when repository `logs/` has generated files."""
    logs_dir = Path.cwd() / "logs"
    if not logs_dir.exists():
        return 0

    allowed = {".gitkeep"}
    artifacts = [
        p
        for p in logs_dir.iterdir()
        if p.is_file() and p.name not in allowed and p.stat().st_size >= 0
    ]

    if artifacts:
        print("Repository logs directory contains generated artifacts:")
        for artifact in sorted(artifacts):
            print(f"- {artifact}")
        print("Tests must write logs only to temporary test-owned paths.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
