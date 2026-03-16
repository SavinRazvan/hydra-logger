# Benchmark Contract

This document defines the canonical benchmark contract for `hydra-logger`.

## Goals

- Produce reproducible, comparable performance artifacts.
- Prevent benchmark-induced side effects outside benchmark workspaces.
- Make concurrency and parallelism conclusions explicit and non-mixed.

## Artifact and Path Contract

- Allowed benchmark output roots:
  - `benchmark/results/`
  - `benchmark/bench_logs/`
- Any benchmark write outside these roots is a contract violation.
- Artifacts must include metadata:
  - timestamp
  - git commit SHA
  - python version
  - platform
  - benchmark configuration/profile

## Metric Contract

- Required formulas:
  - `messages_per_second = total_messages / duration`
  - `bytes_per_second = bytes_written / duration`
- Warm-up durations are excluded from measured duration.
- Flush/cleanup durations should be reported separately where available.

## Suite Separation Contract

- `async_concurrent` evaluates event-loop concurrency (single-process interleaving).
- `parallel_workers` evaluates real parallel throughput (multi-worker execution).
- These suites must be reported independently.

## Validation Contract

- Every benchmark run must be invariant-checked before accepted.
- Every suspicious regression must trigger:
  - rerun
  - targeted code-path review
  - test-path mirror check
