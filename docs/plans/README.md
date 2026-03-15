# Planning Artifacts

This folder stores execution plans for documentation and module-alignment work.

Plans define intent, scope, and acceptance criteria before implementation starts.
Audit evidence and results belong in `docs/audit/`.

## What To Store Here

- Per-initiative plans (for example: `module-docs-2026-03.plan.md`)
- Plan templates used by agents and maintainers
- Optional execution status index

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

1. Create/update plan in `docs/plans/`.
2. Execute scoped work.
3. Record evidence in `docs/audit/<initiative>-<date>.results.md`.
4. Update `docs/plans/INDEX.md` and `docs/audit/INDEX.md`.

## Canonical Companions

- Audit evidence: `docs/audit/`
- Module baseline audit: `docs/MODULE_DOCS_AUDIT.md`
