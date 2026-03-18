# Benchmark Baselines

This directory stores accepted baseline benchmark artifacts used for drift and
regression comparison.

## Policy

- Keep baseline artifacts immutable once accepted.
- Include provenance fields (`profile`, `git_commit_sha`, timestamp) in each
  baseline artifact.
- Prefer one baseline per profile (`ci_smoke`, `pr_gate`, `nightly_truth`).
- Update baselines only through a dedicated PR with audit notes in `docs/audit/`.

## Baseline Acceptance Workflow

1. Select a candidate artifact from `benchmark/results/benchmark_*.json`.
2. Verify candidate metadata:
   - `profile`
   - `git_commit_sha`
   - `python_version`
   - `platform`
   - `machine`
   - `disk_mode`
   - `payload_profile`
3. Confirm reliability guard status and drift context are acceptable.
4. Copy candidate artifact into `benchmark/baselines/` with a versioned name.
5. Add PR notes describing:
   - why baseline is being updated
   - expected performance deltas
   - review/audit evidence references
6. Merge baseline update only after reviewer sign-off.

## Rollback Workflow

1. Identify the last known-good baseline artifact for the same profile.
2. Revert baseline reference update in a dedicated PR.
3. Add rollback rationale and observed regression context in PR notes.
4. Trigger profile benchmark rerun to validate restored baseline behavior.

## Retention and Provenance Guidance

- Retain timestamped benchmark artifacts per profile for trend analysis.
- Avoid comparing cross-profile artifacts for drift decisions.
- Keep baseline history small but meaningful (for example: current and previous stable versions).
- Ensure every accepted baseline has traceable PR context and commit provenance.

## Current seeded baseline

- `ci_smoke_baseline_v1.json`: seeded from `benchmark/results/benchmark_latest.json`
  to bootstrap schema + baseline freeze.
