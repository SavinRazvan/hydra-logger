#!/usr/bin/env python3
"""
Role: Run every `cli_tutorials/t*.py` in order; stream stdout/stderr for inspection.
Used By:
 - Developers validating the CLI tutorial track locally (`python .../run_all_cli_tutorials.py`).
Depends On:
 - argparse
 - os
 - subprocess
 - sys
 - pathlib
Notes:
 - Always `chdir`s to repo root so `examples/config` and `examples/logs/cli-tutorials` resolve.
 - Prefer `.hydra_env/bin/python` when following project docs; any interpreter with `hydra_logger` works.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Ordered list (t01 → t20) — keep in sync with `examples/tutorials/README.md`.
CLI_TUTORIAL_FILENAMES: tuple[str, ...] = (
    "t01_production_quick_start.py",
    "t02_configuration_recipes.py",
    "t03_layers_customization.py",
    "t04_extensions_plugins.py",
    "t05_framework_patterns.py",
    "t06_migration_adoption.py",
    "t07_operational_playbook.py",
    "t08_console_configuration_cookbook.py",
    "t09_levels_columns_date_and_destinations.py",
    "t10_enterprise_profile_config.py",
    "t11_enterprise_policy_layers.py",
    "t12_network_http_typed_destination.py",
    "t13_network_ws_resilient_typed_destination.py",
    "t14_network_local_http_simulation.py",
    "t15_enterprise_network_hardening_playbook.py",
    "t16_enterprise_config_templates_at_scale.py",
    "t17_enterprise_benchmark_comparison_workflow.py",
    "t18_enterprise_bring_your_own_config_benchmark.py",
    "t19_enterprise_nightly_drift_snapshot.py",
    "t20_notebook_hydra_config_onboarding.py",
)


def repo_root_from_here() -> Path:
    """This file: examples/tutorials/shared/run_all_cli_tutorials.py → repo root."""
    return Path(__file__).resolve().parents[3]


def cli_tutorials_dir(root: Path | None = None) -> Path:
    r = root or repo_root_from_here()
    return r / "examples" / "tutorials" / "cli_tutorials"


def iter_cli_script_paths(root: Path | None = None) -> list[Path]:
    base = cli_tutorials_dir(root)
    return [base / name for name in CLI_TUTORIAL_FILENAMES]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run all hydra-logger CLI tutorials in sequence (stream output).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print script paths only; do not execute.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first non-zero exit code.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        metavar="SEC",
        help="Per-script timeout in seconds (default: 120). Use 0 for no limit.",
    )
    args = parser.parse_args(argv)

    root = repo_root_from_here()
    os.chdir(root)

    scripts = iter_cli_script_paths(root)
    missing = [p for p in scripts if not p.is_file()]
    if missing:
        for p in missing:
            print(f"Missing: {p}", file=sys.stderr)
        return 2

    if args.dry_run:
        for p in scripts:
            print(p.relative_to(root))
        return 0

    sep = "=" * 72
    exit_code = 0
    for i, script in enumerate(scripts, start=1):
        rel = script.relative_to(root)
        print(f"\n{sep}\n[{i}/{len(scripts)}] {rel}\n{sep}\n", flush=True)
        timeout = None if args.timeout <= 0 else args.timeout
        try:
            proc = subprocess.run(
                [sys.executable, str(script)],
                cwd=root,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT after {timeout}s: {rel}", file=sys.stderr, flush=True)
            exit_code = 124
            if args.fail_fast:
                return exit_code
            continue
        if proc.returncode != 0:
            exit_code = proc.returncode
            print(
                f"FAILED ({proc.returncode}): {rel}",
                file=sys.stderr,
                flush=True,
            )
            if args.fail_fast:
                return exit_code

    print(f"\n{sep}\nAll {len(scripts)} CLI tutorials finished (last exit: {exit_code}).\n{sep}\n")
    return exit_code if exit_code != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
