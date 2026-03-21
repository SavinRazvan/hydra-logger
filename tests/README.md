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
  examples/
    test_tutorial_assets.py
    test_tutorial_utility.py
    test_run_all_examples.py
    test_run_all_cli_tutorials.py
    test_cli_tutorial_footer.py
    test_examples_and_tutorials_runtime.py
    test_examples_branch_coverage.py
    ...
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
  benchmark/
    test_*.py
  scripts/
    test_*.py
```

Notes:
- Keep one responsibility per test file.
- Prefer behavior-oriented names over implementation details.
- Keep helper fixtures close to the module under test.
- Logger/factory/core tests are isolated from repository runtime logs via module `conftest.py` fixtures that run each test in a per-test temporary working directory.

## Minimum Test Matrix Per Module

For every changed module, include coverage for:

1. Happy path behavior.
2. Error/failure paths.
3. Edge cases (empty/null/invalid inputs, boundary values).
4. Regression scenarios for previously fixed bugs.
5. Lifecycle behavior where relevant (init/cleanup/shutdown, especially async).

## Obsolete Test Policy (Quarantine-First)

When removing or changing behavior:

- First quarantine outdated tests with explicit tracker mapping and replacement target.
- Then remove or update matching module test files in the same PR/slice once replacement coverage is in place.
- Do not keep dead tests for removed features.
- Document accepted coverage gaps in PR notes when intentionally deferred.

## Execution Commands

Fast local gate:

```bash
.hydra_env/bin/python -m pytest -q
```

Coverage view:

```bash
.hydra_env/bin/python -m pytest --cov=hydra_logger --cov-report=term-missing -q
```

## CI Expectations

CI runs tests and coverage on pull requests and pushes to `main` via `.github/workflows/ci.yml`.

Current behavior:
- coverage is collected and reported;
- threshold is currently permissive and can be tightened over time;
- repository `logs/` must remain clean after tests (`python scripts/dev/check_logs_clean.py`).

See `docs/TESTING.md` for policy-level guidance.
