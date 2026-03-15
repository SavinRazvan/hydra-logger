# PR Workflow For Hydra-Logger

This file is the maintainer source of truth for PR handling in this repository.

## Script-First Principle

Prefer workflow scripts over manual command chains to reduce token usage and drift:

- `python scripts/pr/workflow.py --phase <create|review|prepare|merge|finalize|full>`
- `python scripts/pr/status.py --json`

## Required Skill Order

Use these skills in sequence:

1. `review-pr` (review only, no code changes)
2. `prepare-pr` (apply fixes, run required checks)
3. `merge-pr` (merge only after checks and artifacts are complete)

Do not skip steps.

## Required PR Creation (After Commit/Push)

Create PRs with the project wrapper script so attribution is always present:

1. `git push -u origin HEAD`
2. `python scripts/pr/workflow.py --phase create --title "<title>" --summary "<bullet-1>" --summary "<bullet-2>" [--test-plan "<cmd>"]`

The generated PR body must include this attribution block:

- `Author: <name>`
- `GitHub-User: <@handle>`
- `Agent/s: <agent-pipeline>`
- `Made-with: Cursor`

## Required Publish Checkpoint (After PR Create, Before Merge)

After `commit -> push -> PR create`, verify publication and linkage:

1. `python scripts/pr/status.py --json`
2. `python scripts/pr/verify_publish.py --branch "$(git branch --show-current)"`
3. `gh pr view --json number,url,headRefName,state,mergeStateStatus`
4. `gh pr checks --watch` (or `gh pr checks` for non-blocking view)

If upstream tracking is missing:

- `git branch --set-upstream-to=origin/<branch> <branch>`

Do not proceed to merge until publication and linkage checks pass.

For one-shot merge + cleanup, use:

- `python scripts/pr/workflow.py --phase merge --auto-finalize [--feature-branch "<branch-if-on-main>"]`

## Required Verification Before Merge

Run at minimum:

- `python -m pytest -q`
- `python scripts/pr/check_slim_headers.py --all-python --strict`

## Required PR Artifacts

The flow should produce these local artifacts:

- `.local/review.md`
- `.local/prep.md`
- `.local/merge.md`

Each file should include:

- scope
- decisions/findings
- verification evidence
- remaining risks or follow-ups
- action attribution:
  - `Action-By: <name>`
  - `GitHub-User: <@handle>` (when provided)
  - `Agent/s: <agent-name-or-pipeline>`

## Required Finalization Step (After Merge)

After merge, close the workflow with repository cleanup:

1. `git checkout main`
2. `python scripts/pr/finalize.py --branch <feature-branch>`
3. optional cleanup pass:
   - `python scripts/pr/finalize.py --branch <feature-branch> --delete-merged-local`
4. confirm remote feature branch deletion:
   - `git ls-remote --heads origin <feature-branch>` (expect no output)
5. verify final state:
   - `git status --short --branch`
