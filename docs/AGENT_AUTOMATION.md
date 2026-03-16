# Agent Automation

Use script-first workflow commands to reduce prompt tokens and agent drift.

This document does not replace `AGENTS.md`. Agent behavior and policy stay authoritative in `AGENTS.md`.
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

- `python scripts/dev/check_env_health.py --strict`

Preferred one-command implementation start (clean branch + draft PR):

- `python scripts/pr/start_impl.py --branch "feature/<scope>" --title "<title>" --summary "<item>"`

Start implementation branch from synced `main`:

- `python scripts/pr/workflow.py --phase start --branch "feature/<scope>"`

Create draft PR immediately after start (before coding):

- `python scripts/pr/workflow.py --phase create --draft --title "<title>" --summary "<item>" --summary "<item>"`

Create/update PR:

- `python scripts/pr/workflow.py --phase create --title "<title>" --summary "<item>" --summary "<item>"`

Review phase:

- `python scripts/pr/workflow.py --phase review`

Prepare phase (runs `pytest -q` + slim header check):

- `python scripts/pr/workflow.py --phase prepare`

Merge phase:

- `python scripts/pr/workflow.py --phase merge`

Merge + cleanup in one shot:

- `python scripts/pr/workflow.py --phase merge --auto-finalize`

Finalize phase (post-merge branch cleanup):

- `python scripts/pr/workflow.py --phase finalize --feature-branch "<branch-if-on-main>"`

## Full Pipeline

Run entire flow in one command:

- `python scripts/pr/workflow.py --phase full --title "<title>" --summary "<item>" --summary "<item>"`

## Required Delivery Order

1. `start` a feature branch from fresh `main`
2. `create --draft` PR immediately from the new branch
3. implement changes + add tests
4. `create` update PR title/body as needed
5. `review` — produces `.local/review.md`
6. `prepare` — runs gates, produces `.local/prep.md`
7. `merge` — checks artifacts, merges, produces `.local/merge.md`
8. `finalize` — cleans up local and remote branches

## Required Gates (enforced by `prepare`)

- `python -m pytest -q`
- `python scripts/pr/check_slim_headers.py --all-python --strict`

## Machine-Readable Status

Use one command for branch/PR/artifact/check status:

- `python scripts/pr/status.py --json`

This avoids repeated manual checks (`git status`, `gh pr view`, `gh pr checks`, artifact inspection).

## Notes

- `create/review/prepare/merge/full` are blocked on `main`; run them from a feature branch.
- `start` is the only phase that begins from `main`.
- `workflow.py` runs env preflight by default for `create/review/prepare/merge/full`.
- Direct wrappers (`scripts/pr/create.py`, `scripts/pr/prepare.py`, `scripts/pr/status.py`) also run env preflight by default.
- Emergency-only override: `--skip-env-check`.
- Use `--phase merge --auto-finalize` for one-shot merge + cleanup.
