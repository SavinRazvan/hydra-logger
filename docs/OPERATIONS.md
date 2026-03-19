# Operations Diagnostics Guide

This guide defines runtime diagnostics to keep `hydra-logger` stable in production.

## Scope

Use these checks when validating operational health:

- queue pressure and backlog growth
- dropped message counters
- async worker failures and restart behavior
- handler emit/write failure rates
- shutdown cleanup completion (queues and tasks drained)

## Core Runtime Signals

Monitor and alert on these classes of signals:

- **Queue pressure**
  - sustained queue growth without recovery windows
  - queue depth above agreed threshold for more than N intervals
- **Drop behavior**
  - non-zero dropped message counters
  - rising drop rate under normal load
- **Worker health**
  - uncaught worker exceptions
  - worker task exits not paired with graceful close
- **Handler reliability**
  - repeated emit failures (file/network/console)
  - fallback path usage spikes compared to baseline
- **Lifecycle cleanup**
  - non-drained queues after close
  - leaked async tasks after logger teardown

## Operational Triage Flow

1. Identify failing signal class (queue, drops, worker, handler, cleanup).
2. Confirm load profile and destination configuration for the failing path.
3. Reproduce with benchmark profile closest to production conditions.
4. Inspect latest benchmark JSON guard sections before throughput metrics.
5. Decide severity:
   - blocking: data-loss risk, persistent worker failure, unbounded queue growth
   - advisory: transient spikes with automatic recovery
6. Record evidence and mitigation in incident or PR notes.

## Release and PR Expectations

Before merge for runtime-sensitive changes:

- run `.hydra_env/bin/python scripts/release/preflight.py` for integrated release gates
- run targeted module tests for changed logger/handler paths
- attach benchmark JSON evidence for the selected profile tier
- document residual risk and rollback strategy when any advisory signal remains

## Ownership and review gates

Critical paths (require maintainer review for functional changes):

| Area | Modules / workflows |
| --- | --- |
| Handlers / transports | `hydra_logger/handlers/` |
| Logger runtimes | `hydra_logger/loggers/` |
| Configuration | `hydra_logger/config/` |
| Release & CI | `.github/workflows/`, `scripts/release/` |

## Rollout and rollback

Staged delivery for behavior-affecting changes:

1. **dev** → **staging** → **canary** → **prod**
2. **Rollout gates**: no sustained increase in dropped-log rate vs baseline; async
   flush latency within agreed p95/p99 budget; no new critical security findings.
3. **Rollback triggers**: sustained handler error rate or queue saturation over
   agreed windows; failed benchmark guard tiers; user-visible data loss.

## SLIs / SLOs (library hooks)

Process-local counters and latency samples live in `hydra_logger.utils.slo_metrics`
(`record_dropped_log`, `record_handler_error`, `record_queue_saturation`,
`record_flush_latency`, `snapshot()`, `flush_latency_percentiles()`). Applications
should export these to their metrics stack; initial **SLO targets** are owned by
the deploying team (suggested starting points: dropped logs ≈ 0 in steady state;
flush p99 within service budget; handler errors not trending up release-over-release).

## References

- `docs/TESTING.md`
- `docs/PERFORMANCE.md`
- `docs/RELEASE_POLICY.md`
- `benchmark/README.md`
