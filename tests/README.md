# Hydra-Logger Test Layout

This directory is the canonical, module-first test layout for `hydra_logger/`.

## Goals

- Keep tests modular and easy to maintain during refactors.
- Make obsolete tests easy to find and remove when features are removed.
- Capture edge cases explicitly for each module.
- Report and improve coverage over time with a ratchet strategy.

## Directory Strategy

Use one folder per production module when tests are added:

```text
tests/
  README.md
  test_placeholder.py
  loggers/
    test_sync_logger_*.py
    test_async_logger_*.py
  handlers/
    test_console_handler_*.py
    test_file_handler_*.py
  formatters/
    test_*.py
  config/
    test_*.py
  factories/
    test_*.py
  core/
    test_*.py
  types/
    test_*.py
  extensions/
    test_*.py
  utils/
    test_*.py
```

Notes:
- Keep one responsibility per test file.
- Prefer behavior-oriented names over implementation details.
- Keep helper fixtures close to the module under test.

## Minimum Test Matrix Per Module

For every changed module, include coverage for:

1. Happy path behavior.
2. Error/failure paths.
3. Edge cases (empty/null/invalid inputs, boundary values).
4. Regression scenarios for previously fixed bugs.
5. Lifecycle behavior where relevant (init/cleanup/shutdown, especially async).

## Obsolete Test Policy

When removing or changing behavior:

- Remove or update matching module test files in the same PR.
- Do not keep dead tests for removed features.
- Document accepted coverage gaps in PR notes when intentionally deferred.

## Execution Commands

Fast local gate:

```bash
python -m pytest -q
```

Coverage view:

```bash
python -m pytest --cov=hydra_logger --cov-report=term-missing -q
```

## CI Expectations

CI runs tests and coverage on pull requests and pushes to `main` via `.github/workflows/ci.yml`.

Current behavior:
- coverage is collected and reported;
- threshold is currently permissive and can be tightened over time.

See `docs/TESTING.md` for policy-level guidance.
