# Benchmark Migration Guide

This guide documents migration from ad-hoc benchmark runs to the tiered
benchmark contract.

## Tier mapping

- `ci_smoke`:
  - Purpose: fast confidence on every push/PR.
  - Trigger: CI workflow (`.github/workflows/ci.yml`).
- `pr_gate`:
  - Purpose: PR decision signal with stronger workload.
  - Trigger: pull request in CI workflow.
- `nightly_truth`:
  - Purpose: scheduled regression monitoring with drift policy checks.
  - Trigger: nightly workflow (`.github/workflows/benchmark-nightly.yml`) or
    manual dispatch.

## Path and artifact policy

- Runtime benchmark output must remain inside:
  - `benchmark/results/`
  - `benchmark/bench_logs/`
- Root `logs/` writes during benchmark runs are contract violations.
- CI uploads benchmark artifacts from `benchmark/results/`.

## Drift policy migration notes

- Drift policy is profile-scoped:
  - `ci_smoke`: drift disabled.
  - `pr_gate`: drift enabled with moderate thresholds and lower baseline minimum.
  - `nightly_truth`: drift enabled with stricter thresholds.
- If baseline history is below `min_baseline_runs`, drift checks report
  `skipped_insufficient_baseline` and do not fail the run.

## Operational checklist

1. Use profile-based runs only:
   - `python benchmark/performance_benchmark.py --profile ci_smoke`
   - `python benchmark/performance_benchmark.py --profile pr_gate`
   - `python benchmark/performance_benchmark.py --profile nightly_truth`
2. Review `benchmark/results/benchmark_latest.json` metadata:
   - `profile`
   - `git_commit_sha`
   - `python_version`
   - `platform`
3. Treat any guard failure as a hard stop until fixed:
   - formula invariants
   - path confinement
   - root log leak detection
   - drift policy violations (when enabled)
