# Agent Automation

Use script-first workflow commands to reduce prompt tokens and agent drift.

This document is a human-facing command reference.
Agent behavior and policy are authoritative in `AGENTS.md`.
When instructions conflict, follow `AGENTS.md`.
Canonical workflow skill guidance lives in `.agents/skills/PR_WORKFLOW.md`.

## Profile Defaults

Create `.local/agent_profile.json`:

```json
{
  "actor": "Savin I. Razvan",
  "github_user": "@SavinRazvan",
  "agents": "review-pr | prepare-pr | merge-pr"
}
```

This lets workflow scripts infer attribution defaults instead of passing them each time.

## Single-Phase Orchestration

Preflight environment health before any workflow phase:

- `python scripts/dev/check_env_health.py --strict --auto-upgrade-toolchain --json`

Preferred one-command implementation start (clean branch + draft PR):

- `python scripts/pr/start_impl.py --branch "feature/<scope>" --title "<title>" --summary "<item>"`

Bootstrap note:

- If GitHub rejects draft PR creation because there are no unique commits yet on the new branch, `start_impl.py` now prints an explicit defer message and exits successfully.
- In that case, continue implementation, create the first commit via workflow, then run `python scripts/pr/workflow.py --phase create --draft ...`.

Start implementation branch from synced `main`:

- `python scripts/pr/workflow.py --phase start --branch "feature/<scope>"`

Create draft PR immediately after start (before coding):

- `python scripts/pr/workflow.py --phase create --draft --title "<title>" --summary "<item>" --summary "<item>"`

Create/update PR:

- `python scripts/pr/workflow.py --phase create --title "<title>" --summary "<item>" --summary "<item>"`

Create structured commit with required attribution trailers:

- `python scripts/pr/workflow.py --phase commit --commit-all --commit-subject "<type(scope): subject>" --commit-body "<why>" --commit-body "<risk/follow-up>"`

Review phase:

- `python scripts/pr/workflow.py --phase review`

Prepare phase (runs full default gates):

- `python scripts/pr/workflow.py --phase prepare`

Prepare with explicit benchmark gate options:

- `python scripts/pr/workflow.py --phase prepare --benchmark-profile ci_smoke`
- `python scripts/pr/workflow.py --phase prepare --skip-benchmark-gate` (emergency-only)

Merge phase:

- `python scripts/pr/workflow.py --phase merge`

Merge + cleanup in one shot:

- `python scripts/pr/workflow.py --phase merge --auto-finalize`

Finalize phase (post-merge branch cleanup):

- `python scripts/pr/workflow.py --phase finalize --feature-branch "<branch-if-on-main>"`

## Full Pipeline

Run post-implementation flow in one command (feature branch only):

- `python scripts/pr/workflow.py --phase full --title "<title>" --summary "<item>" --summary "<item>"`

`full` runs `create -> review -> prepare -> merge -> finalize`. It does not run `start` or `commit`.

## Required Delivery Order

1. `start` a feature branch from fresh `main`
2. `create --draft` PR immediately from the new branch
3. implement changes + add tests
4. `commit` via workflow commit phase (enforces attribution trailers)
5. `create` update PR title/body as needed
6. `review` — produces `.local/review.md`
7. `prepare` — runs gates, produces `.local/prep.md`
8. `merge` — checks artifacts, merges, produces `.local/merge.md`
9. `finalize` — cleans up local and remote branches

## Required Gates (enforced by `prepare`)

- `python -m pytest -q`
- `python -m pytest --cov=hydra_logger --cov-report=term-missing --cov-fail-under=95 -q`
- `python scripts/dev/check_version_consistency.py`
- `python scripts/pr/check_slim_headers.py --all-python --strict`
- `python benchmark/performance_benchmark.py --profile ci_smoke --no-save-results` (unless `--skip-benchmark-gate`)

## Release Preflight

Use release preflight before tagging or publishing:

- `.hydra_env/bin/python scripts/release/preflight.py`

Fast mode (skip benchmark/build checks when doing iterative local work):

- `.hydra_env/bin/python scripts/release/preflight.py --skip-benchmark --skip-build`

Checklist reference:

- `docs/RELEASE_CHECKLIST.md`

## Machine-Readable Status

Use one command for branch/PR/artifact/check status:

- `python scripts/pr/status.py --json`

This avoids repeated manual checks (`git status`, `gh pr view`, `gh pr checks`, artifact inspection).

## Agent Checkpoint Cadence

Run these checkpoints at minimum:

1. Before implementation starts on a slice branch:
   - `python scripts/pr/status.py --json`
2. After commit, before review:
   - `python scripts/pr/status.py --json`
3. After prepare and before merge:
   - `python scripts/pr/status.py --json`
4. After merge/finalize:
   - `python scripts/pr/status.py --json`

Mandatory evidence for each slice:

- `.local/review.md`
- `.local/prep.md`
- `.local/merge.md`
- latest benchmark artifact set in `benchmark/results/` (JSON + summary/drift/invariants/leaks) when benchmark execution is configured to save artifacts

## Notes

- `create/review/prepare/merge/full` are blocked on `main`; run them from a feature branch.
- `start` is the standard implementation-entry phase from `main`; `finalize` supports `--feature-branch` when run on `main`.
- `workflow.py` runs env preflight by default for `create/review/prepare/merge/full`.
- Direct wrappers (`scripts/pr/create.py`, `scripts/pr/prepare.py`, `scripts/pr/status.py`) also run env preflight by default.
- Emergency-only override: `--skip-env-check`.
- Use `--phase merge --auto-finalize` for one-shot merge + cleanup.
- `--phase commit` blocks commits on `main` unless `--allow-main-commit` is explicitly set.
