# Release Checklist

Use this checklist before tagging and publishing a release artifact.

## Required Order

1. Confirm branch and release scope are correct.
2. Validate version consistency from canonical source.
3. Run quality and coverage gates.
4. Validate benchmark profile health.
5. Build and verify distribution artifacts.
6. Confirm security scan status.
7. Capture release evidence in PR/release notes.

## Commands

Preferred single-command preflight:

```bash
.hydra_env/bin/python scripts/release/preflight.py
```

Optional fast mode (skip heavy benchmark/build checks):

```bash
.hydra_env/bin/python scripts/release/preflight.py --skip-benchmark --skip-build
```

If you need persisted benchmark evidence for release notes, run a saved benchmark explicitly:

```bash
.hydra_env/bin/python benchmark/performance_benchmark.py --profile pr_gate
```

## Gate Details

- **Version consistency**: `scripts/dev/check_version_consistency.py` must pass.
- **Tests**: full unit suite and `hydra_logger` coverage gate (`>=95%`) must pass.
- **Header policy**: slim metadata header validation must pass.
- **Benchmark sanity**: `benchmark/performance_benchmark.py --profile pr_gate` should complete with valid guard evidence.
- **Package quality**: `python -m build`, `twine check`, and dist-content verification must pass.
- **Security posture**: lint/security workflow outputs must be reviewed before publish.

## Release Evidence

Capture at minimum:

- commit SHA and tag candidate
- full preflight output
- CI run URL for green release candidate build
- benchmark JSON artifact used for release decision (from an explicit saved benchmark run)
- any accepted residual risks with owner + follow-up date
