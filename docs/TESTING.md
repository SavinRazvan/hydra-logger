# Testing Strategy

This document defines testing policy for `hydra-logger`.

Implementation conventions and day-to-day layout details are in `tests/README.md`.

## Objectives

- Provide enterprise-grade confidence for runtime behavior.
- Keep test suites scalable as modules evolve.
- Maintain clean traceability between production modules and test modules.
- Prevent drift between implementation changes and test coverage.

## Test Model

Use a module-first structure:

- `hydra_logger/<module>/...` maps to `tests/<module>/...`
- one test file should target one behavior surface
- behavior changes require test changes in the same pull request

This supports safe refactoring and fast removal of obsolete tests.

## Required Coverage Dimensions

Each changed module should include tests for:

1. Happy path behavior
2. Error and failure behavior
3. Edge and boundary inputs
4. Regression scenarios for fixed bugs
5. Lifecycle and cleanup behavior (especially async paths)

## Coverage Policy

Coverage is required as evidence, not vanity:

- run coverage for changed modules in local validation;
- report residual gaps explicitly in PR notes;
- tighten global threshold incrementally (coverage ratchet) rather than one-time jumps.

Current CI/prepare ratchet stage (2026-03 baseline):

- `hydra_logger` fail-under: `60`
- `benchmark` package fail-under: `100`

Planned enterprise ratchet sequence for `hydra_logger`:

- Stage 1: `60` (active)
- Stage 2: `70`
- Stage 3: `80`
- Stage 4: `90`
- Stage 5: `95`

## CI/CD Contract

CI pipeline (`.github/workflows/ci.yml`) executes:

- tests with coverage (`pytest tests/ --cov=hydra_logger --cov-fail-under=60 ...`);
- benchmark package coverage (`pytest tests/benchmark --cov=benchmark --cov-fail-under=100`);
- lint and static quality checks;
- build validation and security scans.
- benchmark automation profiles:
  - `ci_smoke` on push/pull request;
  - `pr_gate` on pull request.

Nightly benchmark workflow (`.github/workflows/benchmark-nightly.yml`) executes:

- `nightly_truth` profile on schedule/manual dispatch.

PR preparation (`scripts/pr/prepare.py`) enforces:

- `python -m pytest -q`
- `python -m pytest --cov=hydra_logger --cov-report=term-missing --cov-fail-under=60 -q`
- `python scripts/pr/check_slim_headers.py --all-python --strict`

## PR Expectations

Before merge:

- changed modules have corresponding tests;
- obsolete tests follow quarantine-first handling and are then removed or updated;
- edge-case coverage is demonstrated;
- remaining risks/gaps are documented.

## References

- `tests/README.md`
- `.agents/skills/test-module-coverage/SKILL.md`
- `.cursor/agents/test-runner.md`
- `.cursor/agents/verifier.md`
