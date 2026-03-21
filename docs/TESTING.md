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

Current coverage gate stage (2026-03 baseline):

- CI `hydra_logger` fail-under: `95`
- CI benchmark package fail-under: `95`

Planned enterprise ratchet sequence for `hydra_logger`:

- Stage 1: `60`
- Stage 2: `70`
- Stage 3: `80`
- Stage 4: `90`
- Stage 5: `95` (active)

Historical verification snapshot (2026-03-17, informational only):

- `.hydra_env/bin/python -m pytest --cov=hydra_logger --cov-report=term-missing -q` => `96%` total.
- `.hydra_env/bin/python -m pytest tests/benchmark --cov=benchmark --cov-report=term-missing --cov-fail-under=95 -q` => `100%` total.

## CI/CD Contract

CI pipeline (`.github/workflows/ci.yml`) executes:

- tests with coverage (`pytest tests/ --cov=hydra_logger --cov-fail-under=95 ...`);
- critical module coverage floors (`handlers`, `loggers`, `extensions`) at `>=95` on Python 3.12;
- repository log-isolation guard (`python scripts/dev/check_logs_clean.py`);
- benchmark package coverage (`pytest tests/benchmark --cov=benchmark --cov-fail-under=95`);
- lint and static quality checks;
- build validation and security scans.
- benchmark automation profiles:
  - `ci_smoke` on push/pull request;
  - `pr_gate` on pull request.

Nightly benchmark workflow (`.github/workflows/benchmark-nightly.yml`) executes:

- `nightly_truth` profile on schedule/manual dispatch.

PR preparation (`scripts/pr/prepare.py`) runs these gates via the active Python interpreter:

- `python -m pytest -q`
- `python -m pytest --cov=hydra_logger --cov-report=term-missing --cov-fail-under=95 -q`
- `python scripts/dev/check_version_consistency.py`
- `python scripts/pr/check_slim_headers.py --all-python --strict`
- `python benchmark/performance_benchmark.py --profile ci_smoke --no-save-results` (unless explicitly skipped)

Static/security staged enforcement policy in CI:

- `flake8` runs in three passes: **critical** errors (`E9`, `F63`, `F7`, `F82`), a **blocking** pass aligned with **black** (`max-line-length=88`, `extend-ignore=E203,W503,E501`), and an **advisory** cyclomatic complexity report (`max-complexity=10`, `--exit-zero`). Local config: `.flake8`.
- `mypy` always produces artifact output and enforces blocking mode when `MYPY_ENFORCE=true` (enabled in CI workflow env).
- `bandit` high-severity gate always generates reports and enforces blocking mode when `BANDIT_ENFORCE=true` (enabled in CI workflow env).
- dependency vulnerability scans run through **`pip-audit`**, with blocking mode when `PIP_AUDIT_ENFORCE=true` (enabled in CI workflow env). The optional extra `legacy_safety` installs PyUp `safety` for local use only (pulls transitive `nltk`; not part of default `dev`).

### Deterministic CI stages (lint / security)

Lint and security jobs use **separate** steps for **report capture** (`continue-on-error:
true`, preserves artifacts even when the tool exits non-zero) and **blocking gates**
(explicit `mypy` / `bandit` / `pip-audit` invocations). This avoids shell `|| true`
patterns that can obscure failures while still uploading machine-readable reports.

## Examples and tutorials

- **`tests/examples/`** — tutorial **asset** presence (`test_tutorial_assets.py`), **`run_all_examples.py`**
  behavior (`test_run_all_examples.py`, `test_examples_branch_coverage.py`), **notebook generator**
  contract (`test_examples_and_tutorials_runtime.py` where applicable), and **`examples/tutorials/utility`**
  (`test_tutorial_utility.py`).
- Run: `.hydra_env/bin/python -m pytest tests/examples -q`.
- **`examples/run_all_examples.py`** — optional full smoke of all `examples/tutorials/cli_tutorials/*.py`
  (also exercised by tests).
- **`examples/tutorials/shared/run_all_cli_tutorials.py`** — same scripts in order with **streamed** stdout/stderr
  (human-friendly; not required in CI; `--dry-run` / `--fail-fast` supported).
- **Jupyter notebooks** under `examples/tutorials/notebooks/` are **committed** artifacts; asset tests
  assert clean VCS state (no stored outputs) and notebook content contracts.
- **`test_tutorial_assets.py`** asserts subset preset embedding, `extends` closure for T02, plumbing vs scenario
  cell separation, **clean VCS state** (`execution_count` / `outputs` cleared), and **`skip-ci`** tags on §0 `%pip` cells.
- **Notebook CI smoke** (GitHub Actions job `notebook-smoke`): installs `pip install -e ".[notebook_smoke]"` and runs
  `python scripts/dev/run_notebook_smoke.py`, which executes **T01** and **T02** from the **repository root** after
  stripping cells tagged `skip-ci` (avoids redundant `pip install` during execute). **T17–T19** are **excluded** until
  benchmark artifacts are seeded or fixtures exist under `tests/fixtures/` — see `examples/tutorials/notebooks/README.md`.
- Local smoke (optional): `pip install -e ".[notebook_smoke]"` then `python scripts/dev/run_notebook_smoke.py`.

## Logging Artifact Policy

Runtime logs are destination-controlled:

- production code writes only to explicit configured destinations;
- logger tests run in isolated temporary working directories (`tests/loggers/conftest.py`);
- repository `logs/` is treated as local runtime-only and must remain clean after tests.

Use this local guard before pushing when changing logger behavior:

- `.hydra_env/bin/python scripts/dev/check_logs_clean.py`

## PR Expectations

Before merge:

- changed modules have corresponding tests;
- obsolete tests follow quarantine-first handling and are then removed or updated;
- edge-case coverage is demonstrated;
- remaining risks/gaps are documented.

## References

- `tests/README.md`
- `.agents/skills/test-module-coverage/SKILL.md`
- `docs/RELEASE_CHECKLIST.md`
