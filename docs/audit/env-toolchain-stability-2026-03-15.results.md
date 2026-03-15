# Environment Toolchain Stability Audit Results

- Date: 2026-03-15
- Owner: @SavinRazvan
- Scope: `scripts/dev/check_env_health.py`, `scripts/pr/workflow.py`, environment docs updates
- Plan: `docs/plans/env-toolchain-stability-2026-03.plan.md`
- Status: in_progress

## Implemented In This Slice

- Added `scripts/dev/check_env_health.py` with deterministic checks:
  - `mixed_env_layout`
  - `python_subprocess_import`
  - `pip_health`
  - `mypy_available`
  - `pyright_available`
  - `env_path_writable`
  - `pyright_cache_permissions`
- Added CLI modes:
  - `--json`
  - `--strict`
  - `--fix-hints-only`
- Integrated preflight into `scripts/pr/workflow.py` for `create/review/prepare/merge/full`.
- Added `--skip-env-check` emergency override to `scripts/pr/workflow.py`.
- Updated:
  - `docs/ENVIRONMENT_SETUP.md` with health-check and repair sequence
  - `docs/AGENT_AUTOMATION.md` with preflight contract
  - `README.md` testing section with preflight recommendation

## Validation Evidence

1. Strict health run on current `.hydra_env`:
   - Command: `python scripts/dev/check_env_health.py --strict --json`
   - Result: `degraded` (exit `2`)
   - Evidence:
     - `pip_health` warning (`python -m pip check` import error)
     - `mypy_available` warning (`librt.internal` import error)
     - Runtime subprocess support check passes.

2. Simulated mixed env detection:
   - Command: `python scripts/dev/check_env_health.py --env-path <temp_mixed_layout> --json`
   - Result: `broken` (exit `2`)
   - Evidence: `mixed_env_layout` failed when both `conda-meta` and `pyvenv.cfg` coexist.

3. Human-friendly hint mode:
   - Command: `python scripts/dev/check_env_health.py --fix-hints-only`
   - Result: non-pass checks are reduced to actionable fix hints.

4. Workflow preflight behavior:
   - Blocking path: `python scripts/pr/workflow.py --phase review ...` -> blocked by env preflight.
   - Override path: `python scripts/pr/workflow.py --phase review ... --skip-env-check` -> workflow proceeds.

## Open Items

- Integrate equivalent preflight defaults into direct wrappers under `scripts/pr/*` that may be called outside `workflow.py`.
- Remove remaining environment inconsistency warnings (`pip_health`, `mypy_available`) in `.hydra_env`.
- Align docs language where needed to avoid Conda/venv ambiguity across all setup references.
