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

- Create PR:
  - `python scripts/pr/workflow.py --phase create --title "<title>" --summary "<item>" --summary "<item>"`
- Review phase:
  - `python scripts/pr/workflow.py --phase review`
- Prepare phase:
  - `python scripts/pr/workflow.py --phase prepare`
- Merge phase:
  - `python scripts/pr/workflow.py --phase merge`
  - or merge + cleanup in one shot:
  - `python scripts/pr/workflow.py --phase merge --auto-finalize --feature-branch "<branch-if-running-from-main>"`
- Finalize phase:
  - `python scripts/pr/workflow.py --phase finalize --feature-branch "<branch-if-on-main>"`

## Full Pipeline

Run entire flow in one command:

- `python scripts/pr/workflow.py --phase full --title "<title>" --summary "<item>" --summary "<item>"`

## Machine-Readable Status

Use one command for branch/PR/artifact/check status:

- `python scripts/pr/status.py --json`

This avoids repeated manual checks (`git status`, `gh pr view`, `gh pr checks`, artifact inspection).
