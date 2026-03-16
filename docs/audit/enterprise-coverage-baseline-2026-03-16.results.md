# Enterprise Coverage Baseline (2026-03-16)

## Scope

- Product package coverage: `hydra_logger/**`
- Benchmark package coverage: `benchmark/**`
- Test inventory and obsolete-test candidate scan
- CI/prepare gate threshold baseline

## Commands Executed

- `./.hydra_env/bin/python -m pytest -q`
- `./.hydra_env/bin/python -m pytest --cov=hydra_logger --cov-report=term-missing -q`
- `./.hydra_env/bin/python -m pytest tests/benchmark --cov=benchmark --cov-report=term-missing -q`

## Baseline Coverage Snapshot

- `hydra_logger` total: `62%` (`7620` stmts / `2904` missed)
- `benchmark` total: `100%` (`573` stmts / `0` missed)

## Top Product Hotspots (largest gap first)

- `hydra_logger/handlers/file_handler.py`: `38%`
- `hydra_logger/handlers/console_handler.py`: `37%`
- `hydra_logger/core/exceptions.py`: `42%`
- `hydra_logger/loggers/composite_logger.py`: `45%`
- `hydra_logger/loggers/async_logger.py`: `50%`
- `hydra_logger/utils/file_utility.py`: `52%`
- `hydra_logger/loggers/base.py`: `52%`

## Obsolete Test Candidate Inventory (Quarantine-First)

Initial candidates identified before removal:

1. `tests/test_placeholder.py`
   - Reason: non-functional legacy smoke placeholder with no behavior contract.
   - Replacement target: module-level smoke/integration contracts are already represented in module tests.
   - Action: quarantine in tracker first, then remove in a dedicated cleanup slice.

## CI/Prepare Threshold Baseline

- CI workflow currently enforces `--cov-fail-under=0` for `hydra_logger`.
- `scripts/pr/prepare.py` currently enforces:
  - `pytest -q`
  - `check_slim_headers.py --all-python --strict`
  - benchmark profile gate (default `ci_smoke`)

## Target Ratchet Direction

- Product (`hydra_logger`) staged fail-under ramp:
  - Stage 1: `60`
  - Stage 2: `70`
  - Stage 3: `80`
  - Stage 4: `90`
  - Stage 5: `95`
- Benchmark package remains at `100%` enforcement.

## Residual Risk

- Reaching `>=95%` product coverage requires multiple implementation slices in low-coverage hotspot modules.
- Quarantine-first must be used to prevent accidental loss of safety signals when removing stale tests.

## Uplift Iteration Log (same initiative)

### Iteration A

- Added:
  - `tests/loggers/test_base_logger_contract.py`
  - extended `tests/core/test_exceptions.py`
  - benchmark legacy compatibility checks in `tests/benchmark/test_benchmark_schema_slice_f.py`
- Coverage outcome:
  - `hydra_logger`: `62% -> 64%`
  - `benchmark`: retained `100%`

### Iteration B

- Added:
  - deeper `console_handler` tests in `tests/handlers/test_base_and_console_handlers.py`
  - deeper `file_handler` tests in `tests/handlers/test_file_and_null_handlers.py`
  - deeper `composite_logger` and `async_logger` tests
  - deeper `network_handler` retry/validation/close tests
- Coverage outcome:
  - `hydra_logger`: `64% -> 65.14%`
  - key module deltas:
    - `handlers/console_handler.py`: `37% -> 53%`
    - `handlers/file_handler.py`: `38% -> 39%`
    - `handlers/network_handler.py`: `50% -> 56%`
    - `loggers/composite_logger.py`: `45% -> 48%`
    - `loggers/async_logger.py`: `50% -> 56%`
