# Benchmark Baselines

This directory stores accepted baseline benchmark artifacts used for drift and
regression comparison.

## Policy

- Keep baseline artifacts immutable once accepted.
- Include provenance fields (`profile`, `git_commit_sha`, timestamp) in each
  baseline artifact.
- Prefer one baseline per profile (`ci_smoke`, `pr_gate`, `nightly_truth`).
- Update baselines only through a dedicated PR with audit notes in `docs/audit/`.

## Current seeded baseline

- `ci_smoke_baseline_v1.json`: seeded from `benchmark/results/benchmark_latest.json`
  to bootstrap schema + baseline freeze.
