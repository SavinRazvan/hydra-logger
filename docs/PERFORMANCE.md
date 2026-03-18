# Hydra-Logger Performance

This document describes how to evaluate and reason about `hydra-logger`
performance using benchmark artifacts and profile-based interpretation.

---

## Benchmark Source of Truth

Performance truth comes from benchmark artifacts under `benchmark/results/`,
not from static numbers in documentation.

Primary references:

- `benchmark/README.md`
- `docs/benchmarks/CONTRACT.md`
- `docs/benchmarks/MIGRATION.md`

---

## Benchmark Tiers

- `ci_smoke`:
  - fast confidence signal for push/PR
  - drift disabled
- `pr_gate`:
  - pull request performance signal
  - drift enabled with moderate thresholds
  - reliability guards remain advisory
- `nightly_truth`:
  - deep regression profile
  - stricter drift thresholds
  - reliability guards are hard-fail

---

## Run Commands

```bash
# Tiered benchmark profiles
python3 benchmark/performance_benchmark.py --profile ci_smoke
python3 benchmark/performance_benchmark.py --profile pr_gate
python3 benchmark/performance_benchmark.py --profile nightly_truth
```

Use profile-specific artifact roots for cleaner comparison history:

```bash
python3 benchmark/performance_benchmark.py --profile ci_smoke --results-dir benchmark/results/ci_smoke
python3 benchmark/performance_benchmark.py --profile pr_gate --results-dir benchmark/results/pr_gate
python3 benchmark/performance_benchmark.py --profile nightly_truth --results-dir benchmark/results/nightly_truth
```

---

## How to Interpret Metrics

Core formulas:

- `messages_per_second = total_messages / duration`
- `bytes_per_second = bytes_written / duration`

Interpretation notes:

- Warm-up is excluded from measured throughput windows.
- Console output rounds durations; calculations use full precision.
- Async logger reports two paths:
  - `task_fanout_*` for `logger.log(...)`
  - `logger_core_*` for `logger.log_async(...)`

Compare these async paths separately; they are not equivalent measurements.

---

## Safe Comparison Rules

Only compare benchmark runs that are both:

- same profile (`ci_smoke` vs `ci_smoke`, etc.)
- metadata-compatible on:
  - `python_version`
  - `platform`
  - `machine`
  - `disk_mode`
  - `payload_profile`
  - `git_commit_sha` (for change attribution)

Do not compare cross-profile throughput directly. Workload size, repetitions,
and suite coverage differ by profile design.

---

## Artifact and Provenance Checklist

Expected persisted artifacts:

- `benchmark_YYYY-MM-DD_HH-MM-SS.json` (timestamped historical run)
- `benchmark_latest.json` (convenience latest copy)
- optional report files (`summary`, `drift`, `invariants`, `leaks`)

Capture provenance in performance reviews:

```bash
git rev-parse --short HEAD
python3 --version
uname -srmo
```

---

## Troubleshooting Slow or "Stuck" Runs

- Long `nightly_truth` runs can appear idle while still progressing.
- Artifacts are persisted near run completion, not continuously during execution.
- If a run exits before save, new timestamped artifacts are not created.
- For quick validation, rerun with `ci_smoke` before deep nightly investigation.

---

## Related Documentation

- [WORKFLOW_ARCHITECTURE.md](WORKFLOW_ARCHITECTURE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [README.md](../README.md)
