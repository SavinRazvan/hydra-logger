# Benchmark Workspace

This folder is the canonical workspace for Hydra Logger performance benchmarking.

## Layout

- `performance_benchmark.py`: benchmark entrypoint.
- `results/`: benchmark snapshots and latest result symlink/copy targets.
- `bench_logs/`: transient run logs and generated logger output during benchmark runs.

## Run

```bash
python3 benchmark/performance_benchmark.py
```

## Tracking Policy

- Keep reproducible benchmark snapshots in `results/`.
- Treat `bench_logs/` as transient diagnostics.
- Include benchmark metadata with every results artifact:
  - commit SHA
  - Python version
  - platform
  - benchmark configuration
