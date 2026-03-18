# Benchmark Workspace

This directory is the canonical workspace for Hydra Logger benchmark execution,
artifact persistence, drift analysis, and operator review.

## Purpose

- Provide reproducible, profile-based benchmark runs.
- Persist metadata-rich artifacts for audit and comparison.
- Keep benchmark outputs isolated from runtime application logs.

## Layout

- `performance_benchmark.py`: benchmark entrypoint and suite orchestrator.
- `profiles/`: tiered benchmark profile definitions (`ci_smoke`, `pr_gate`, `nightly_truth`).
- `policies/drift_policy.json`: canonical drift thresholds and profile overrides.
- `schema/result_schema.json`: benchmark artifact schema.
- `results/`: persisted benchmark artifacts (timestamped JSON, latest copy, optional reports).
- `baselines/`: accepted baseline snapshots and baseline governance notes.
- `bench_logs/`: transient logs emitted during benchmark execution.

## Prerequisites

- Python 3.11+ (project standard).
- Activated project virtual environment.
- Dependencies installed for the workspace.
- Optional: `psutil` for memory benchmark detail (memory section is skipped when unavailable).

Example setup:

```bash
source /home/razvansavin/Projects/hydra-logger/.hydra_env/bin/activate
python3 --version
```

## Quickstart

Run benchmark profiles from repository root:

```bash
# Fast local smoke signal
python3 benchmark/performance_benchmark.py --profile ci_smoke

# PR-grade benchmark signal
python3 benchmark/performance_benchmark.py --profile pr_gate

# Full nightly-style regression run (heavy workload)
python3 benchmark/performance_benchmark.py --profile nightly_truth
```

Expected behavior:

- `nightly_truth` can appear idle between prints because workloads are large.
- Progress is still active while long sections execute.
- Artifacts are written near run completion (after guard checks and reporting).

## Full CLI Reference

`benchmark/performance_benchmark.py` supports:

- `--profile <name>`: load profile from `benchmark/profiles/`.
  - Valid names currently include `ci_smoke`, `pr_gate`, `nightly_truth`.
- `--results-dir <path>`: custom artifact root (default is `benchmark/results`).
- `--no-save-results`: run benchmark without persisting artifacts.

Examples:

```bash
# Default profile behavior (legacy default config)
python3 benchmark/performance_benchmark.py

# Save to a profile-specific location
python3 benchmark/performance_benchmark.py --profile pr_gate --results-dir benchmark/results/pr_gate

# Run without artifact persistence
python3 benchmark/performance_benchmark.py --profile ci_smoke --no-save-results
```

Report verbosity environment variable:

- `HYDRA_BENCHMARK_VERBOSE_REPORTS=true` enables always-on drift/invariant/leak markdown report output.

## Profile Intent and Selection

- `ci_smoke`:
  - fastest confidence signal
  - drift disabled
  - suitable for quick local verification and CI push checks
- `pr_gate`:
  - pull request performance signal
  - drift enabled with moderate thresholds
  - reliability guards are advisory (reported, not hard-fail)
- `nightly_truth`:
  - deep regression profile
  - drift enabled with stricter thresholds
  - reliability guard violations hard-fail the run (`strict_reliability_guards=true`)

## Expected Runtime by Profile

These are practical planning estimates for a typical developer machine (for example
WSL2 laptop/desktop class hardware). Actual time varies with CPU, disk speed,
machine load, and whether `--results-dir` points to slower storage.

- `ci_smoke`: ~3 to 8 minutes
- `pr_gate`: ~15 to 35 minutes
- `nightly_truth`: ~60 to 150 minutes

Notes:

- `nightly_truth` can have long quiet periods between log lines because sections are large.
- Runtime scales significantly with profile message counts and repetition settings.
- The async suite includes two measured paths (`task_fanout` and `logger_core`), which increases wall-clock time.

If you want machine-specific estimates, run once with shell timing and keep the
result in your team runbook:

```bash
time python3 benchmark/performance_benchmark.py --profile ci_smoke
time python3 benchmark/performance_benchmark.py --profile pr_gate
time python3 benchmark/performance_benchmark.py --profile nightly_truth
```

## How Throughput and Duration Are Calculated

Core formulas:

- `messages_per_second = total_messages / duration`
- `bytes_per_second = bytes_written / duration`

Duration notes:

- Warm-up time is excluded from measured throughput windows.
- Some suites include separate flush/finalization durations as additional fields.
- Printed durations are rounded for console readability; calculations use full precision.

Async logger throughput includes two distinct paths:

- `task_fanout_*`: measured from `logger.log(...)`.
- `logger_core_*`: measured from `logger.log_async(...)`.

Do not merge these into one number; they represent different execution paths.

## Artifact Lifecycle

When `save_results` is enabled (default):

- A timestamped JSON artifact is written:
  - `benchmark/results/benchmark_YYYY-MM-DD_HH-MM-SS.json`
- A convenience latest copy is updated:
  - `benchmark/results/benchmark_latest.json`
- Optional markdown report artifacts may be written:
  - `benchmark_latest_summary.md`
  - `benchmark_latest_drift.md`
  - `benchmark_latest_invariants.md`
  - `benchmark_latest_leaks.md`

Important:

- `benchmark_latest.json` is a convenience pointer copy, not historical storage.
- Drift history uses timestamped `benchmark_*.json` files for the same profile.
- If a run fails before save, new artifacts are not persisted.

## Result Organization and Comparison Policy

For enterprise comparability, isolate results by profile and run batch:

```bash
python3 benchmark/performance_benchmark.py --profile ci_smoke --results-dir benchmark/results/ci_smoke
python3 benchmark/performance_benchmark.py --profile pr_gate --results-dir benchmark/results/pr_gate
python3 benchmark/performance_benchmark.py --profile nightly_truth --results-dir benchmark/results/nightly_truth/2026-03-17
```

Comparison rules:

- Compare same profile only (`ci_smoke` vs `ci_smoke`, not cross-profile).
- Validate metadata compatibility before analysis:
  - `profile`
  - `python_version`
  - `platform`
  - `machine`
  - `disk_mode`
  - `payload_profile`
  - `git_commit_sha`

## Drift Policy and Reliability Guards

- Drift policy source: `benchmark/policies/drift_policy.json`.
- Profile-level drift overrides can be defined in `benchmark/profiles/*.json`.
- If baseline history count is below minimum, drift marks metric as `skipped_insufficient_baseline` (not failed).
- Guard checks include:
  - formula invariants
  - output path confinement
  - output-matrix file evidence
  - file I/O evidence
  - sample duration checks
  - root log leak detection

Severity by profile:

- `ci_smoke`: advisory
- `pr_gate`: advisory
- `nightly_truth`: hard-fail on violations

## Enterprise Operator Runbook

1. Select profile by decision tier (`ci_smoke`, `pr_gate`, `nightly_truth`).
2. Use profile-specific `--results-dir` to avoid mixed histories.
3. Run benchmark and wait for completion artifact write.
4. Inspect metadata and guard statuses before throughput comparison.
5. Compare only same-profile, metadata-compatible runs.
6. Capture benchmark evidence in PR/operations notes.

## CI and Nightly Automation

- CI workflow (`.github/workflows/ci.yml`) runs:
  - `ci_smoke` on push and pull request
  - `pr_gate` on pull request
- Nightly workflow (`.github/workflows/benchmark-nightly.yml`) runs:
  - `nightly_truth` on schedule and manual dispatch
- Automation artifacts are uploaded from `benchmark/results/`.

## Related Documentation

- `docs/benchmarks/CONTRACT.md`
- `docs/benchmarks/MIGRATION.md`
- `docs/PERFORMANCE.md`
