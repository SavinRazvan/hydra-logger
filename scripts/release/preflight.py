"""
Role: Release preflight orchestration for enterprise-ready publish checks.
Used By:
 - Local maintainers preparing release candidates.
 - CI jobs validating release readiness signals.
Depends On:
 - argparse
 - dataclasses
 - pathlib
 - subprocess
 - sys
 - time
Notes:
 - Runs fail-fast by default with optional continue-on-failure mode.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PreflightStep:
    step_id: str
    description: str
    command: list[str]


@dataclass(frozen=True)
class PreflightResult:
    step: PreflightStep
    return_code: int
    duration_seconds: float
    output: str

    @property
    def ok(self) -> bool:
        return self.return_code == 0


def _default_steps(
    skip_benchmark: bool, skip_build: bool, pypi_parity: bool = False
) -> list[PreflightStep]:
    python_bin = sys.executable
    steps: list[PreflightStep] = [
        PreflightStep(
            step_id="version_consistency",
            description="Validate governed version consistency",
            command=[python_bin, "scripts/dev/check_version_consistency.py"],
        ),
    ]

    if pypi_parity:
        steps.append(
            PreflightStep(
                step_id="pypi_parity",
                description="Require PyPI index parity with repository (post-publish)",
                command=[
                    python_bin,
                    "scripts/release/check_pypi_parity.py",
                    "--require-match",
                ],
            )
        )

    steps.extend(
        [
            PreflightStep(
                step_id="unit_tests",
                description="Run project unit test suite",
                command=[python_bin, "-m", "pytest", "-q"],
            ),
            PreflightStep(
                step_id="coverage_hydra_logger",
                description="Validate hydra_logger coverage threshold",
                command=[
                    python_bin,
                    "-m",
                    "pytest",
                    "--cov=hydra_logger",
                    "--cov-report=term-missing",
                    "--cov-fail-under=95",
                    "-q",
                ],
            ),
            PreflightStep(
                step_id="slim_headers",
                description="Enforce slim metadata headers",
                command=[
                    python_bin,
                    "scripts/pr/check_slim_headers.py",
                    "--all-python",
                    "--strict",
                ],
            ),
        ]
    )

    if not skip_benchmark:
        steps.append(
            PreflightStep(
                step_id="benchmark_pr_gate",
                description="Run benchmark PR-gate profile sanity check",
                command=[
                    python_bin,
                    "benchmark/performance_benchmark.py",
                    "--profile",
                    "pr_gate",
                    "--no-save-results",
                ],
            )
        )

    if not skip_build:
        steps.extend(
            [
                PreflightStep(
                    step_id="build_dist",
                    description="Build sdist and wheel",
                    command=[python_bin, "-m", "build"],
                ),
                PreflightStep(
                    step_id="twine_check",
                    description="Validate package metadata",
                    command=[python_bin, "-m", "twine", "check", "dist/*"],
                ),
                PreflightStep(
                    step_id="verify_dist_contents",
                    description="Verify distribution archive content policy",
                    command=[python_bin, "scripts/release/verify_dist_contents.py"],
                ),
            ]
        )

    return steps


def _run_step(step: PreflightStep, cwd: Path) -> PreflightResult:
    resolved_command: list[str] = []
    for token in step.command:
        if "*" not in token:
            resolved_command.append(token)
            continue
        matches = sorted(str(path) for path in cwd.glob(token))
        if matches:
            resolved_command.extend(matches)
        else:
            resolved_command.append(token)

    start = time.perf_counter()
    process = subprocess.run(
        resolved_command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        shell=False,
    )
    duration = time.perf_counter() - start
    output = ((process.stdout or "") + (process.stderr or "")).strip()
    return PreflightResult(
        step=step,
        return_code=process.returncode,
        duration_seconds=duration,
        output=output,
    )


def run_preflight(
    *,
    steps: list[PreflightStep],
    cwd: Path,
    continue_on_failure: bool,
) -> int:
    failures: list[PreflightResult] = []
    for step in steps:
        print(f"[RUN ] {step.step_id}: {step.description}")
        result = _run_step(step, cwd)
        if result.ok:
            print(f"[PASS] {step.step_id} ({result.duration_seconds:.2f}s)")
            continue

        failures.append(result)
        print(f"[FAIL] {step.step_id} ({result.duration_seconds:.2f}s)")
        if result.output:
            print(result.output)
        if not continue_on_failure:
            break

    if failures:
        print("\nRelease preflight failed.")
        for item in failures:
            print(f"- {item.step.step_id}: exit_code={item.return_code}")
        return 1

    print("\nRelease preflight passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run release readiness checks for hydra-logger."
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        default=False,
        help="Run all configured checks even after a failure.",
    )
    parser.add_argument(
        "--skip-benchmark",
        action="store_true",
        default=False,
        help="Skip benchmark PR-gate profile sanity check.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        default=False,
        help="Skip build/twine/dist-verification checks.",
    )
    parser.add_argument(
        "--pypi-parity",
        action="store_true",
        default=False,
        help=(
            "After version consistency, require live PyPI metadata to match the "
            "repository (network; use after successful upload)."
        ),
    )
    args = parser.parse_args(argv)

    steps = _default_steps(
        skip_benchmark=args.skip_benchmark,
        skip_build=args.skip_build,
        pypi_parity=args.pypi_parity,
    )
    return run_preflight(
        steps=steps,
        cwd=REPO_ROOT,
        continue_on_failure=args.continue_on_failure,
    )


if __name__ == "__main__":
    raise SystemExit(main())
