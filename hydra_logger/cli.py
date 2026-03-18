"""
Role: Command-line entrypoint for hydra-logger package metadata and diagnostics.
Used By:
 - `hydra-logger` console script installed via package entry points.
Depends On:
 - argparse
 - hydra_logger.__version__
Notes:
 - Keeps CLI behavior lightweight and side-effect free for packaging health checks.
"""

from __future__ import annotations

import argparse

from hydra_logger import __version__


def _build_parser() -> argparse.ArgumentParser:
    """Create argument parser for the hydra-logger CLI."""
    parser = argparse.ArgumentParser(
        prog="hydra-logger",
        description="Hydra Logger command-line utilities.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print installed hydra-logger version and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run CLI entrypoint and return process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(f"hydra-logger {__version__}")
        return 0

    print("Hydra Logger CLI is available. Use --version for package version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
