---
name: prepare-pr
description: Prepares a pull request for merge by applying approved fixes and running required checks. Use after review-pr recommends proceeding.
disable-model-invocation: true
---

# Prepare PR

## Goal

Make the PR merge-ready with validated fixes and explicit evidence.

## Instructions

1. Confirm `.local/review.md` exists and resolve BLOCKER/IMPORTANT findings first.
2. Apply focused fixes only within PR scope.
3. Run checks and create the prep artifact in one step:
   - `python scripts/pr/prepare.py --pr <pr-number-or-url> --actor "<name>" --agents "review-pr | prepare-pr" [--github-user "<@handle>"]`
   - The script runs required checks and writes `.local/prep.md` with results.
   - It enforces strict slim-header validation repository-wide (`--all-python --strict`).
   - If the script exits non-zero, fix the failing gate before proceeding.
   - If gates were already run and verified independently (e.g. as part of a prior step), pass `--skip-gates` to record them as externally verified without re-running.
4. Enrich `.local/prep.md` with:
   - resolved findings
   - residual risks/follow-ups
   (the script already wrote attribution, branch/HEAD stamp, and gate results)

## Exit Criteria

Status should be: `PR is ready for /merge-pr`.
