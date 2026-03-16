# Planning Artifacts

This folder stores execution plans and superseded historical plans.

The active architecture execution source of truth is the single master plan in
`.cursor/plans/` ("Hydra Logger Master Architecture + No-Drift Plan").
Historical plans in this folder remain for traceability and must be marked
`superseded` once consolidated.

Audit evidence and results belong in `docs/audit/`.

## What To Store Here

- Historical/superseded initiative plans (for example:
  `module-docs-2026-03.plan.md`)
- Plan templates used by agents and maintainers
- Execution status index and tracker pointers

## File Naming Convention

- Plan: `<initiative>-YYYY-MM.plan.md`
- Keep one initiative per file to preserve traceability.

## Required Sections In Every Plan

1. Outcome
2. Scope and source of truth
3. Execution phases
4. Acceptance criteria
5. Definition of done
6. Links to audit targets/results

## Workflow Contract

1. Keep exactly one active execution plan (master plan).
2. Mark prior plan files as `superseded` and link to the master plan.
3. Execute one scoped slice at a time.
4. Record evidence in `docs/audit/<initiative>-<date>.results.md`.
5. Update `docs/plans/INDEX.md`, `docs/plans/TRACKER.md`, and
   `docs/audit/INDEX.md`.

## Automation

Use the plan scaffold script to create a new plan and update `docs/plans/INDEX.md`:

- `python scripts/plans/create_plan.py --initiative "<initiative title>"`

Optional:

- `--owner "@SavinRazvan"` to override profile defaults
- `--status planned|in_progress|complete`
- `--dry-run` to preview without writing files

## Canonical Companions

- Audit evidence: `docs/audit/`
- Module baseline audit: `docs/MODULE_DOCS_AUDIT.md`
- Active plan status tracking: `docs/plans/INDEX.md` and `docs/plans/TRACKER.md`
