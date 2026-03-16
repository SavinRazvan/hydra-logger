# Benchmark Metric Definitions

## Core Throughput Metrics

- `total_messages`: count of emitted benchmark messages in measured window.
- `duration`: measured execution window in seconds (warm-up excluded).
- `messages_per_second`: `total_messages / duration`.

## I/O Metrics

- `bytes_written`: bytes persisted by benchmark scenario.
- `bytes_per_second`: `bytes_written / duration`.
- `written_lines`: line count for line-based outputs, expected to match emitted messages.

## Reliability Counters

- `expected_emitted`: expected number of log events for a scenario.
- `actual_emitted`: observed number of log events emitted by logger path.
- `count_match`: pass/fail invariant where `actual_emitted == expected_emitted`.

## Statistical Aggregates

- `median`: primary central estimate across repetitions.
- `p95`: upper-tail latency/throughput percentile across repetitions.
- Single-run values are diagnostics, not gate decisions.

## Drift Evaluation Signals

- `baseline_median`: comparison reference from accepted benchmark history.
- `baseline_p95`: upper-tail comparison reference from accepted history.
- `drift_pct`: percent difference versus baseline signal.
