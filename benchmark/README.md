# Benchmark Workspace

This folder is the canonical workspace for Hydra Logger performance benchmarking.

## Layout

- `performance_benchmark.py`: benchmark entrypoint.
- `schema/result_schema.json`: canonical benchmark result schema.
- `baselines/`: accepted baseline snapshots used for drift comparison.
- `results/`: benchmark snapshots and latest result symlink/copy targets.
- `bench_logs/`: transient run logs and generated logger output during benchmark runs.

## Run

```bash
python3 benchmark/performance_benchmark.py

# Tiered profiles
python3 benchmark/performance_benchmark.py --profile ci_smoke
python3 benchmark/performance_benchmark.py --profile pr_gate
python3 benchmark/performance_benchmark.py --profile nightly_truth
```

## Tracking Policy

- Keep reproducible benchmark snapshots in `results/`.
- Treat `bench_logs/` as transient diagnostics.
- Include benchmark metadata with every results artifact:
  - commit SHA
  - Python version
  - platform
  - benchmark configuration
  - selected profile (`legacy_default`, `ci_smoke`, `pr_gate`, `nightly_truth`)

## Drift policy gates

- `pr_gate` and `nightly_truth` profiles enable throughput drift checks.
- Drift checks compare current run metrics with same-profile history in
  `benchmark/results/` using median and p95 references.
- Canonical policy source: `benchmark/policies/drift_policy.json`.
- Profile-level `drift_policy` values act as overrides on top of canonical policy.
- When historical sample count is below policy minimum, checks are reported as
  skipped (not failed) to avoid bootstrapping false negatives.

## Reliability contract

- File benchmarks (`file_writing`, `async_file_writing`) publish observed
  `actual_emitted` counters from handlers and strict line-evidence fields.
- Output-matrix file cases must expose concrete `file_path` and `written_lines`
  evidence at emitted-message parity.
- Repetition metadata (`repetition_runs`, `repetition_stats`) and
  `minimum_sample_duration_*` markers are persisted per scenario payload.
- Reliability guard failures are **hard-fail only** for `nightly_truth`
  (`strict_reliability_guards=true`); CI/PR profiles remain advisory.

## CI and nightly automation

- CI workflow (`.github/workflows/ci.yml`) runs:
  - `ci_smoke` profile on push + pull request
  - `pr_gate` profile on pull request
- Nightly workflow (`.github/workflows/benchmark-nightly.yml`) runs:
  - `nightly_truth` profile on schedule and manual dispatch
- Artifacts are uploaded from `benchmark/results/` for each automation tier.
