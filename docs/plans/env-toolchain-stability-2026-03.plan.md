# Environment Toolchain Stability Plan

- Date: 2026-03-15
- Owner: @SavinRazvan
- Status: complete
- Expected audit results file: `docs/audit/env-toolchain-stability-2026-03-15.results.md`

## Outcome

Deliver a deterministic, self-healing local environment workflow that prevents mixed Conda+venv corruption, provides early failure with actionable guidance, and keeps PR automation stable across machines and shells.

The primary implementation artifact is a guard script:

- `scripts/dev/check_env_health.py`

This script is the single preflight gate for local tooling and workflow wrappers.

## Scope And Source Of Truth

- Target runtime/tooling paths:
  - `.hydra_env/`
  - `environment.yml`
  - `docs/ENVIRONMENT_SETUP.md`
  - `README.md` (environment and contributor command sections)
- Target automation scripts:
  - `scripts/pr/workflow.py`
  - `scripts/pr/status.py`
  - `scripts/pr/review.py`
  - `scripts/pr/prepare.py`
  - `scripts/pr/merge.py`
  - `scripts/pr/finalize.py`
  - `scripts/pr/verify_publish.py`
- New guard script:
  - `scripts/dev/check_env_health.py`
- Out of scope:
  - Replacing dependency manager strategy (Conda vs venv) in this pass
  - Large dependency upgrades unrelated to environment integrity
  - CI container image redesign

## Architecture Intent

- Keep one authoritative environment model active at a time.
- Fail fast before costly commands (lint/type/test/pr workflow).
- Return machine-readable and human-readable diagnostics.
- Keep remediation steps deterministic and copy-paste ready.

## Execution Phases

1. Define health contract and failure taxonomy.
2. Implement environment guard script with strict checks.
3. Integrate guard into local workflows and PR scripts.
4. Document canonical recovery and prevention workflow.
5. Validate with controlled failure scenarios and capture evidence.

## Detailed Implementation Blueprint

### Phase 1 - Health contract

Define health states and checks:

- `healthy`: environment can run subprocess-backed tools (`pip`, `pyright`, `mypy`) from `.hydra_env`.
- `degraded`: environment mostly works but has known non-fatal issues (for example pyright cache path setup required).
- `broken`: environment cannot safely run project workflows.

Define check categories:

- Environment identity checks
  - Detect mixed Conda+venv state (`.hydra_env/conda-meta` and `pyvenv.cfg` both present in incompatible form).
  - Validate interpreter provenance and version consistency.
- Runtime integrity checks
  - Validate import of `_posixsubprocess` and `subprocess`.
  - Validate `pip --version` and `pip check` command execution.
- Toolchain readiness checks
  - Validate `mypy --version`.
  - Validate `pyright --version` with configured cache path.
- Permission and ownership checks
  - Detect non-writable critical paths under `.hydra_env`.
  - Detect permission-denied hotspots for pyright node cache.

### Phase 2 - `scripts/dev/check_env_health.py`

Implement CLI interface:

- `--json` for machine-readable output.
- `--strict` to fail on degraded states.
- `--fix-hints-only` to print remediation commands without mutating state.
- Exit codes:
  - `0` healthy
  - `1` degraded (or broken in non-strict mode)
  - `2` broken / blocking

Expected output model:

- Top-level summary (`status`, `timestamp`, `python`, `env_path`).
- Check results array with:
  - `id`
  - `status` (`pass`/`warn`/`fail`)
  - `evidence`
  - `recommended_fix`

Required guard checks (minimum):

1. `mixed_env_layout`
2. `python_subprocess_import`
3. `pip_health`
4. `mypy_available`
5. `pyright_available`
6. `pyright_cache_permissions`
7. `env_path_writable`

### Phase 3 - Workflow integration

Integrate preflight before expensive commands:

- Add optional `--skip-env-check` to wrappers where needed for emergencies.
- Default behavior: run env guard first and block on `broken`.
- In PR scripts, print a short "how to recover env" message on failure.
- Ensure `scripts/pr/workflow.py` continues using current interpreter (`sys.executable`) for child scripts.

### Phase 4 - Documentation updates

Update:

- `docs/ENVIRONMENT_SETUP.md`
  - Add "Health Check" section with examples.
  - Add deterministic repair sequence.
- `README.md`
  - Link to health check command before lint/type/test commands.
- `docs/AGENT_AUTOMATION.md`
  - Add preflight call for script-first workflows.

Recommended repair sequence to document:

1. Backup/remove corrupted `.hydra_env`.
2. Recreate environment using canonical command set.
3. Reinstall project and dev dependencies.
4. Re-run `check_env_health.py` until status is healthy.

### Phase 5 - Validation matrix

Run and record evidence for:

- Healthy venv path.
- Simulated mixed env (`conda-meta` + mismatched `pyvenv.cfg`) detection.
- Missing `_posixsubprocess` detection.
- pyright cache permission-denied detection.
- Workflow block behavior when status is `broken`.

## Acceptance Criteria

- [x] `scripts/dev/check_env_health.py` exists and implements defined checks.
- [x] Script supports both human-readable and JSON output with stable schema.
- [x] Script exits non-zero for broken state and blocks integrated workflows.
- [x] `scripts/pr/*` wrappers run preflight by default (with explicit override flag).
- [x] Env repair instructions are documented and tested on current platform.
- [x] Results artifact captures evidence for each validation scenario.

## Definition Of Done

- [x] Planned scope completed and merged.
- [x] Environment preflight is the default path for local workflow scripts.
- [x] Known mixed Conda+venv corruption pattern is detected before command execution.
- [x] No contradictory environment instructions remain across docs.
- [x] Evidence captured in `docs/audit/env-toolchain-stability-2026-03-15.results.md`.

## Risks And Mitigations

- Risk: False positives block valid developer environments.
  - Mitigation: Introduce `degraded` state and `--strict` mode; tune checks with real samples.
- Risk: Script itself becomes a maintenance burden.
  - Mitigation: Keep checks modular, pure-function based, and separately unit tested.
- Risk: Platform-specific assumptions break portability.
  - Mitigation: Document Linux-first behavior and isolate platform-specific checks.
- Risk: Devs bypass guard permanently.
  - Mitigation: Require explicit `--skip-env-check` and log when override is used.

## Audit Linkage

- Planned results artifact: `docs/audit/env-toolchain-stability-2026-03-15.results.md`
- Related historical audits:
  - `docs/audit/module-docs-2026-03-15.results.md`
