# Agent Automation

Use script-first workflow commands to reduce prompt tokens and agent drift.

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

Preflight environment health before script-first workflow commands:

- `python scripts/dev/check_env_health.py --strict`

- Start implementation branch from synced `main`:
  - `python scripts/pr/workflow.py --phase start --branch "feature/<scope>"`
- Create PR:
  - `python scripts/pr/workflow.py --phase create --title "<title>" --summary "<item>" --summary "<item>"`
- Review phase:
  - `python scripts/pr/workflow.py --phase review`
- Prepare phase:
  - `python scripts/pr/workflow.py --phase prepare`
- Merge phase:
  - `python scripts/pr/workflow.py --phase merge`
  - or merge + cleanup in one shot:
  - `python scripts/pr/workflow.py --phase merge --auto-finalize`
- Finalize phase:
  - `python scripts/pr/workflow.py --phase finalize --feature-branch "<branch-if-on-main>"`

## Full Pipeline

Run entire flow in one command:

- `python scripts/pr/workflow.py --phase full --title "<title>" --summary "<item>" --summary "<item>"`

## Required Delivery Order

1. `start` a feature branch from fresh `main`
2. implement changes + add tests
3. `prepare` gates must pass (pytest + slim header checks)
4. merge via workflow
5. finalize cleanup

Notes:

- `create/review/prepare/merge/full` are blocked on `main`; run them from a feature branch.
- Use `--phase merge --auto-finalize` for one-shot merge + cleanup.
- `scripts/pr/workflow.py` now runs env preflight by default for `create/review/prepare/merge/full`.
- Direct tracked wrappers (`scripts/pr/create.py`, `scripts/pr/prepare.py`, `scripts/pr/status.py`) also run env preflight by default.
- Emergency-only override: `--skip-env-check`.

## Machine-Readable Status

Use one command for branch/PR/artifact/check status:

- `python scripts/pr/status.py --json`

This avoids repeated manual checks (`git status`, `gh pr view`, `gh pr checks`, artifact inspection).
