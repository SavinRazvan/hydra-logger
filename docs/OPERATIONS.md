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

- run `scripts/release/preflight.py` for integrated release gates
- run targeted module tests for changed logger/handler paths
- attach benchmark JSON evidence for the selected profile tier
- document residual risk and rollback strategy when any advisory signal remains

## References

- `docs/TESTING.md`
- `docs/PERFORMANCE.md`
- `benchmark/README.md`
